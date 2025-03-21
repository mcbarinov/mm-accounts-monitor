from __future__ import annotations

from typing import cast

from mm_base6 import BaseCore, CoreConfig

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
    async def init(cls, core_config: CoreConfig) -> Core:
        res = cast(Core, await super().base_init(core_config, DConfigSettings, DValueSettings, Db))
        res.bot_service = BotService(res.base_service_params)
        res.network_service = NetworkService(res.base_service_params)
        res.coin_service = CoinService(res.base_service_params, res.network_service)
        res.naming_service = NamingService(res.base_service_params, res.network_service)
        res.group_service = GroupService(res.base_service_params, res.network_service, res.coin_service)
        res.balance_service = BalanceService(res.base_service_params, res.network_service, res.coin_service)

        # res.scheduler.add_task("data_service:generate_one", 60, res.data_service.generate_one)
        res.scheduler.add_task("naming:check_next", 2, res.naming_service.check_next)
        res.scheduler.add_task("balance:check_next", 2, res.balance_service.check_next)

        return res
