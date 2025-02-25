from mm_base3 import DC, DV, BaseAppConfig, DConfigDict, DValueDict
from pydantic import Field


class AppConfig(BaseAppConfig):
    tags: list[str] = Field(["bot"])
    main_menu: dict[str, str] = Field({"/data": "data"})
    telegram_bot_help: str = """
/first_command - bla bla1
/second_command - bla bla2
"""


class DConfigSettings(DConfigDict):
    proxies_url = DC("http://localhost:8000", "proxies url, each proxy on new line")


class DValueSettings(DValueDict):
    proxies = DV([])
    proxies_updated_at = DV(None)
