from mm_base3 import BaseService
from mm_base3.base_service import BaseServiceParams
from mm_std import hr, synchronized, utc_now

from app.config import AppConfig, DConfigSettings, DValueSettings
from app.db import Db


class BotService(BaseService[AppConfig, DConfigSettings, DValueSettings, Db]):
    def __init__(self, base_params: BaseServiceParams[AppConfig, DConfigSettings, DValueSettings, Db]) -> None:
        super().__init__(base_params)

    @synchronized
    def update_proxies(self) -> int:
        self.logger.debug("update_proxies called")
        res = hr(self.dconfig.proxies_url)
        if res.is_error():
            self.dlog("update_proxies", {"error": res.error})
            return -1
        proxies = res.body.strip().splitlines()
        proxies = [p.strip() for p in proxies if p.strip()]
        self.dvalue.proxies = proxies
        self.dvalue.proxies_updated_at = utc_now()
        return len(proxies)
