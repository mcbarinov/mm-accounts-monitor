from datetime import datetime

from mm_base3 import DC, DV, BaseAppConfig, DConfigDict, DValueDict
from pydantic import Field


class AppConfig(BaseAppConfig):
    tags: list[str] = Field(["bot", "network", "coin"])
    main_menu: dict[str, str] = Field({"/networks": "networks", "/coins": "coins", "/groups": "groups"})


class DConfigSettings(DConfigDict):
    proxies_url = DC("http://localhost:8000", "proxies url, each proxy on new line")
    round_ndigits = DC(5, "round ndigits")
    max_workers_networks = DC(10, "How many networks process in parallel")
    max_workers_coins = DC(5, "How many coins process in parallel in one network")


class DValueSettings(DValueDict):
    proxies: DV[list[str]] = DV([])
    proxies_updated_at: DV[datetime | None] = DV(None)
