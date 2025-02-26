from mm_base3 import BaseCore

from app.config import AppConfig, DConfigSettings, DValueSettings
from app.db import Db
from app.services.bot_service import BotService
from app.services.network_service import NetworkService


class Core(BaseCore[AppConfig, DConfigSettings, DValueSettings, Db]):
    def __init__(self) -> None:
        super().__init__(AppConfig, DConfigSettings, DValueSettings, Db)
        self.bot_service = BotService(self.base_service_params)
        self.network_service = NetworkService(self.base_service_params)

        self.scheduler.add_job(self.bot_service.update_proxies, interval=60)

    def start(self) -> None:
        pass

    def stop(self) -> None:
        pass
