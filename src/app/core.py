from mm_base3 import BaseCore

from app.config import AppConfig, DConfigSettings, DValueSettings
from app.db import Db
from app.services.balance_service import BalanceService
from app.services.bot_service import BotService
from app.services.coin_service import CoinService
from app.services.group_service import GroupService
from app.services.network_service import NetworkService


class Core(BaseCore[AppConfig, DConfigSettings, DValueSettings, Db]):
    def __init__(self) -> None:
        super().__init__(AppConfig, DConfigSettings, DValueSettings, Db)
        self.bot_service: BotService = BotService(self.base_service_params)
        self.network_service: NetworkService = NetworkService(self.base_service_params)
        self.coin_service: CoinService = CoinService(self.base_service_params)
        self.group_service: GroupService = GroupService(self.base_service_params, self.network_service, self.coin_service)
        self.balance_service: BalanceService = BalanceService(self.base_service_params, self.network_service, self.coin_service)

        self.scheduler.add_job(self.bot_service.update_proxies, interval=60)
        self.scheduler.add_job(self.balance_service.check_next_balances, interval=5)

    def start(self) -> None:
        pass

    def stop(self) -> None:
        pass
