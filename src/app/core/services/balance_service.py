from decimal import Decimal

from bson import ObjectId
from mm_std import ConcurrentTasks, Err, Result, synchronized, utc_delta, utc_now

from app.core.blockchains import aptos, evm, solana, starknet
from app.core.constants import NetworkType
from app.core.db import BalanceProblem
from app.core.services.coin_service import CoinService
from app.core.services.network_service import NetworkService
from app.core.types_ import AppService, AppServiceParams


class BalanceService(AppService):
    def __init__(self, base_params: AppServiceParams, network_service: NetworkService, coin_service: CoinService) -> None:
        super().__init__(base_params)
        self.network_service = network_service
        self.coin_service = coin_service

    @synchronized
    def check_next(self) -> None:
        if not self.dvalue.check_balances:
            return
        tasks = ConcurrentTasks(max_workers=self.dconfig.max_workers_networks, thread_name_prefix="check_next_balances")
        for network in self.network_service.get_networks():
            tasks.add_task(f"check_next_network_balances_{network.id}", self.check_next_network_balances, args=(network.id,))
        tasks.execute()

    def check_next_network_balances(self, network: str) -> None:
        # self.logger.debug("check_next_network_balances called: %s", network)

        # first check accounts that were never checked
        need_to_check = self.db.account_balance.find(
            {"network": network, "checked_at": None}, limit=self.dconfig.max_workers_coins
        )
        # next check accounts that were checked more than 5 minutes ago
        if len(need_to_check) < self.dconfig.max_workers_coins:
            need_to_check += self.db.account_balance.find(
                {"network": network, "checked_at": {"$lt": utc_delta(minutes=-1 * self.dconfig.check_balance_interval)}},
                limit=self.dconfig.max_workers_coins - len(need_to_check),
            )
        if not need_to_check:
            return

        tasks = ConcurrentTasks(max_workers=self.dconfig.max_workers_coins, thread_name_prefix="check_balances__" + network)
        for ab in need_to_check:
            tasks.add_task(f"check_account_balance_{ab.id}", self.check_account_balance, args=(ab.id,))
        tasks.execute()

    def check_account_balance(self, id: ObjectId) -> Result[int]:
        account_balance = self.db.account_balance.get(id)
        coin = self.coin_service.get_coin(account_balance.coin)
        network = self.network_service.get_network(coin.network)

        # self.logger.debug("check_account_balance: %s / %s / %s", network.id, coin.symbol, account_balance.account)

        match network.type:
            case NetworkType.EVM:
                res = evm.get_balance(network.rpc_urls, account_balance.account, coin.token, proxies=self.dvalue.proxies)
            case NetworkType.SOLANA:
                res = solana.get_balance(network.rpc_urls, account_balance.account, coin.token, proxies=self.dvalue.proxies)
            case NetworkType.APTOS:
                res = aptos.get_balance(network.rpc_urls, account_balance.account, coin.token, proxies=self.dvalue.proxies)
            case NetworkType.STARKNET:
                if coin.token is None:
                    raise ValueError("can't get balance for coin on StarkNet without token address")
                res = starknet.get_balance(network.rpc_urls, account_balance.account, coin.token, proxies=self.dvalue.proxies)
            case _:
                raise NotImplementedError

        if isinstance(res, Err):
            self.logger.debug("check_account_balance: %s", res.err)
            self.db.balance_problem.insert_one(
                BalanceProblem(id=ObjectId(), network=network.id, coin=coin.id, account=account_balance.account, message=res.err)
            )
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
