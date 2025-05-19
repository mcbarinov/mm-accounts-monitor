from __future__ import annotations

import logging
from typing import Self

from mm_base6 import BaseCore, CoreConfig
from mm_crypto_utils import Network

from app.core.constants import Naming
from app.core.db import Db
from app.core.services.balance import BalanceService
from app.core.services.bot import BotService
from app.core.services.coin import CoinService
from app.core.services.group import GroupService
from app.core.services.history import HistoryService
from app.core.services.name import NameService
from app.core.services.network import NetworkService
from app.settings import DynamicConfigs, DynamicValues


class ServiceRegistry:
    bot: BotService
    network: NetworkService
    coin: CoinService
    name: NameService
    group: GroupService
    balance: BalanceService
    history: HistoryService


class Core(BaseCore[DynamicConfigs, DynamicValues, Db, ServiceRegistry]):
    @classmethod
    async def init(cls, core_config: CoreConfig) -> Self:
        res = await super().base_init(core_config, DynamicConfigs, DynamicValues, Db, ServiceRegistry)

        # service registry

        bot_service = BotService(res.base_service_params)
        network_service = NetworkService(res.base_service_params)
        coin_service = CoinService(res.base_service_params, network_service)
        name_service = NameService(res.base_service_params, network_service)
        group_service = GroupService(res.base_service_params, network_service, coin_service)
        balance_service = BalanceService(res.base_service_params, network_service, coin_service)
        history_service = HistoryService(res.base_service_params, network_service, coin_service)

        res.services.bot = bot_service
        res.services.network = network_service
        res.services.coin = coin_service
        res.services.name = name_service
        res.services.group = group_service
        res.services.balance = balance_service
        res.services.history = history_service

        return res

    async def configure_scheduler(self) -> None:
        # check balances
        for network in Network:
            task_id = "balances_on_" + network.value
            self.scheduler.add_task(task_id, 2, self.services.balance.check_next_network, args=(network,))

        # check namings
        for naming in list(Naming):
            task_id = "names_on_" + naming
            self.scheduler.add_task(task_id, 2, self.services.name.check_next_naming, args=(naming,))

        # mm-node-checker
        self.scheduler.add_task("mm-node-checker", 30, self.services.network.update_mm_node_checker)

    async def start(self) -> None:
        libraries = ["httpcore", "httpx", "web3"]
        for lib in libraries:
            logging.getLogger(lib).setLevel(logging.WARNING)

        await self.services.network.load_rpc_urls_from_db()
        await self.services.coin.load_coins_from_db()

    async def stop(self) -> None:
        pass
