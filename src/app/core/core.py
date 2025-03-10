from mm_base5 import BaseCore, CoreConfig

from app.core.db import Db
from app.core.services.balance_service import BalanceService
from app.core.services.bot_service import BotService
from app.core.services.coin_service import CoinService
from app.core.services.group_service import GroupService
from app.core.services.naming_service import NamingService
from app.core.services.network_service import NetworkService
from app.settings import DConfigSettings, DValueSettings


class Core(BaseCore[DConfigSettings, DValueSettings, Db]):
    def __init__(self, core_config: CoreConfig) -> None:
        super().__init__(core_config, DConfigSettings, DValueSettings, Db)
        self.bot_service: BotService = BotService(self.base_service_params)
        self.network_service: NetworkService = NetworkService(self.base_service_params)
        self.coin_service: CoinService = CoinService(self.base_service_params)
        self.group_service: GroupService = GroupService(self.base_service_params, self.network_service, self.coin_service)
        self.balance_service: BalanceService = BalanceService(self.base_service_params, self.network_service, self.coin_service)
        self.naming_service: NamingService = NamingService(self.base_service_params, self.network_service)

        self.scheduler.add_job(self.balance_service.check_next, interval=5)
        self.scheduler.add_job(self.naming_service.check_next, interval=5)

    def start(self) -> None:
        pass

    def stop(self) -> None:
        pass
