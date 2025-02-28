from decimal import Decimal

from bson import ObjectId
from mm_std import ConcurrentTasks, Err, Result, synchronized, utc_delta, utc_now

from app.blockchains import evm, solana
from app.db import NetworkType
from app.services.coin_service import CoinService
from app.services.network_service import NetworkService
from app.types_ import AppBaseService, AppBaseServiceParams


class BalanceService(AppBaseService):
    def __init__(self, base_params: AppBaseServiceParams, network_service: NetworkService, coin_service: CoinService) -> None:
        super().__init__(base_params)
        self.network_service = network_service
        self.coin_service = coin_service

    @synchronized
    def check_next_balances(self) -> None:
        self.dvalue.check_balances = False
        if not self.dvalue.check_balances:
            return
        tasks = ConcurrentTasks(max_workers=self.dconfig.max_workers_networks)
        for network in self.network_service.get_networks():
            tasks.add_task(f"check_next_network_balances_{network.id}", self.check_next_network_balances, args=(network.id,))
        tasks.execute()

    def check_next_network_balances(self, network: str) -> None:
        self.logger.debug("check_next_network_balances called: %s", network)

        need_to_check = self.db.account_balance.find(
            {"network": network, "$or": [{"checked_at": None}, {"checked_at": {"$lt": utc_delta(minutes=-5)}}]}, "checked_at", 10
        )
        if not need_to_check:
            return

        tasks = ConcurrentTasks(max_workers=self.dconfig.max_workers_coins)
        for ab in need_to_check:
            tasks.add_task(f"check_account_balance_{ab.id}", self.check_account_balance, args=(ab.id,))
        tasks.execute()

    def check_account_balance(self, id: ObjectId) -> Result[int]:
        account_balance = self.db.account_balance.get(id)
        coin = self.coin_service.get_coin(account_balance.coin)
        network = self.network_service.get_network(coin.network)

        self.logger.debug("check_account_balance: %s / %s / %s", network.id, coin.symbol, account_balance.account)

        match network.type:
            case NetworkType.EVM:
                res = evm.get_balance(network.rpc_urls, account_balance.account, coin.token, proxies=self.dvalue.proxies)
            case NetworkType.SOLANA:
                res = solana.get_balance(network.rpc_urls, account_balance.account, coin.token, proxies=self.dvalue.proxies)
            case _:
                raise NotImplementedError

        if isinstance(res, Err):
            self.logger.debug("check_account_balance: %s", res.err)
            return res

        balance_raw = res.ok
        balance = (
            Decimal(0)
            if balance_raw == 0
            else round(Decimal(balance_raw) / 10**coin.decimals, ndigits=self.dconfig.round_ndigits)
        )
        self.db.group_balances.update_one(
            {"group_id": account_balance.group_id, "coin": account_balance.coin},
            {"$set": {f"balances.{account_balance.account}": balance}},
        )
        self.db.account_balance.set(id, {"balance_raw": balance_raw, "balance": balance, "checked_at": utc_now()})

        return res
