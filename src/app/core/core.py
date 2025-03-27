from __future__ import annotations

from typing import Self

from mm_base6 import BaseCore, CoreConfig

from app.core.constants import Naming
from app.core.db import Db
from app.core.services.balance_service import BalanceService
from app.core.services.bot_service import BotService
from app.core.services.coin_service import CoinService
from app.core.services.group_service import GroupService
from app.core.services.naming_service import NamingService
from app.core.services.network_service import NetworkService
from app.settings import DConfigSettings, DValueSettings


class Core(BaseCore[DConfigSettings, DValueSettings, Db]):
    bot_service: BotService
    network_service: NetworkService
    coin_service: CoinService
    naming_service: NamingService
    group_service: GroupService
    balance_service: BalanceService

    @classmethod
    async def init(cls, core_config: CoreConfig) -> Self:
        res = await super().base_init(core_config, DConfigSettings, DValueSettings, Db)
        res.bot_service = BotService(res.base_service_params)
        res.network_service = NetworkService(res.base_service_params)
        res.coin_service = CoinService(res.base_service_params, res.network_service)
        res.naming_service = NamingService(res.base_service_params, res.network_service)
        res.group_service = GroupService(res.base_service_params, res.network_service, res.coin_service)
        res.balance_service = BalanceService(res.base_service_params, res.network_service, res.coin_service)
        return res

    async def configure_scheduler(self) -> None:
        # check balances
        for network in await self.network_service.get_networks():
            task_id = "balances_on_" + network.id
            self.scheduler.add_task(task_id, 2, self.balance_service.check_next_network, args=(network.id,))

        # check namings
        for naming in list(Naming):
            task_id = "naming_on_" + naming
            self.scheduler.add_task(task_id, 2, self.naming_service.check_next_naming, args=(naming,))

    async def start(self) -> None:
        pass

    async def stop(self) -> None:
        pass
