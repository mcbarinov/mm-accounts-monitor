import logging
import time
from decimal import Decimal

from bson import ObjectId
from mm_crypto_utils import random_node, random_proxy
from mm_std import AsyncTaskRunner, Err, Result, async_synchronized_parameter, utc_delta, utc_now

from app.core.blockchains import aptos, evm, solana, starknet
from app.core.constants import NetworkType
from app.core.db import Coin, Network, RpcMonitoring
from app.core.services.coin_service import CoinService
from app.core.services.network_service import NetworkService
from app.core.types_ import AppService, AppServiceParams

logger = logging.getLogger(__name__)


class BalanceService(AppService):
    def __init__(self, base_params: AppServiceParams, network_service: NetworkService, coin_service: CoinService) -> None:
        super().__init__(base_params)
        self.network_service = network_service
        self.coin_service = coin_service

    @async_synchronized_parameter(arg_index=1)
    async def check_next_network(self, network: str) -> int:
        # first check accounts that were never checked
        need_to_check = await self.db.account_balance.find(
            {"network": network, "checked_at": None}, limit=self.dconfig.limit_network_workers
        )
        # next check accounts that were checked more than 5 minutes ago
        if len(need_to_check) < self.dconfig.limit_network_workers:
            need_to_check += await self.db.account_balance.find(
                {"network": network, "checked_at": {"$lt": utc_delta(minutes=-1 * self.dconfig.check_balance_interval)}},
                limit=self.dconfig.limit_network_workers - len(need_to_check),
            )
        if not need_to_check:
            return 0

        runner = AsyncTaskRunner(self.dconfig.limit_network_workers, name="check_balances")
        for ab in need_to_check:
            runner.add_task(str(ab.id), self.check_account_balance(ab.id))
        await runner.run()
        return len(need_to_check)

    async def _request_balance(self, network: Network, coin: Coin, account: str) -> Result[int]:
        res: Result[int] = Err("not started yet")

        for _ in range(5):
            start_at = time.perf_counter()
            rpc_url = random_node(network.rpc_urls)
            proxy = random_proxy(self.dvalue.proxies)

            match network.type:
                case NetworkType.EVM:
                    res = await evm.get_balance(rpc_url, account, coin.token, proxy)
                case NetworkType.SOLANA:
                    res = await solana.get_balance(rpc_url, account, coin.token, proxy)
                case NetworkType.APTOS:
                    res = await aptos.get_balance(rpc_url, account, coin.token, proxy)
                case NetworkType.STARKNET:
                    if coin.token is None:
                        raise ValueError("can't get balance for coin on StarkNet without token address")
                    res = await starknet.get_balance(rpc_url, account, coin.token, proxy)
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
            await self.db.rpc_monitoring.insert_one(rpc_monitoring)

            if res.is_ok():
                return res

        return res

    async def check_account_balance(self, id: ObjectId) -> Result[int]:
        account_balance = await self.db.account_balance.get(id)
        coin = self.coin_service.get_coin(account_balance.coin)
        network = self.network_service.get_network(coin.network)

        # self.logger.debug("check_account_balance: %s / %s / %s", network.id, coin.symbol, account_balance.account)

        res = await self._request_balance(network, coin, account_balance.account)
        if isinstance(res, Err):
            # logger.debug("check_account_balance: %s", res.err)
            return res

        balance_raw = res.ok
        balance = (
            Decimal(0)
            if balance_raw == 0
            else round(Decimal(balance_raw) / 10**coin.decimals, ndigits=self.dconfig.round_ndigits)
        )
        await self.db.group_balance.update_one(
            {"group_id": account_balance.group_id, "coin": account_balance.coin},
            {"$set": {f"balances.{account_balance.account}": balance, f"checked_at.{account_balance.account}": utc_now()}},
        )
        await self.db.account_balance.set(id, {"balance_raw": str(balance_raw), "balance": balance, "checked_at": utc_now()})

        return res
