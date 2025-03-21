import time
from decimal import Decimal

from bson import ObjectId
from mm_crypto_utils import random_node, random_proxy
from mm_std import ConcurrentTasks, Err, Result, utc_delta, utc_now

from app.core.blockchains import aptos, evm, solana, starknet
from app.core.constants import NetworkType
from app.core.db import Coin, Network, RpcMonitoring
from app.core.services.coin_service import CoinService
from app.core.services.network_service import NetworkService
from app.core.types_ import AppService, AppServiceParams


class BalanceService(AppService):
    def __init__(self, base_params: AppServiceParams, network_service: NetworkService, coin_service: CoinService) -> None:
        super().__init__(base_params)
        self.network_service = network_service
        self.coin_service = coin_service

    # @synchronized
    def check_next(self) -> None:
        if not self.dvalue.check_balances:
            return
        self.logger.debug("Checking balances...")
        tasks = ConcurrentTasks(max_workers=self.dconfig.max_workers_networks, thread_name_prefix="check_next_balances")
        for network in self.network_service.get_networks():
            tasks.add_task(f"check_next_network_balances_{network.id}", self.check_next_network_balances, args=(network.id,))
        tasks.execute()

    def check_next_network_balances(self, network: str) -> int:
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
            return 0

        tasks = ConcurrentTasks(max_workers=self.dconfig.max_workers_coins, thread_name_prefix="check_balances__" + network)
        for ab in need_to_check:
            tasks.add_task(f"check_account_balance_{ab.id}", self.check_account_balance, args=(ab.id,))
        tasks.execute()

        return len(need_to_check)

    def _request_balance(self, network: Network, coin: Coin, account: str) -> Result[int]:
        res: Result[int] = Err("not started yet")

        for _ in range(5):
            start_at = time.perf_counter()
            rpc_url = random_node(network.rpc_urls)
            proxy = random_proxy(self.dvalue.proxies)

            match network.type:
                case NetworkType.EVM:
                    res = evm.get_balance(rpc_url, account, coin.token, proxy)
                case NetworkType.SOLANA:
                    res = solana.get_balance(rpc_url, account, coin.token, proxy)
                case NetworkType.APTOS:
                    res = aptos.get_balance(rpc_url, account, coin.token, proxy)
                case NetworkType.STARKNET:
                    if coin.token is None:
                        raise ValueError("can't get balance for coin on StarkNet without token address")
                    res = starknet.get_balance(rpc_url, account, coin.token, proxy)
                case _:
                    return Err("check_balance: unknown network")

            rpc_monitoring = RpcMonitoring(
                id=ObjectId(),
                network=network.id,
                coin=coin.id,
                account=account,
                rpc_url=rpc_url,
                proxy=proxy,
                success=res.is_ok(),
                response_time=round(time.perf_counter() - start_at, ndigits=2),
                error=res.err,
                data=res.data,
            )
            self.db.rpc_monitoring.insert_one(rpc_monitoring)

            if res.is_ok():
                return res

        return res

    def check_account_balance(self, id: ObjectId) -> Result[int]:
        account_balance = self.db.account_balance.get(id)
        coin = self.coin_service.get_coin(account_balance.coin)
        network = self.network_service.get_network(coin.network)

        # self.logger.debug("check_account_balance: %s / %s / %s", network.id, coin.symbol, account_balance.account)

        res = self._request_balance(network, coin, account_balance.account)
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
