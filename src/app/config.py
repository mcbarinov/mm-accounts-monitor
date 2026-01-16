import logging
from datetime import datetime
from typing import Annotated

from mm_base6 import BaseSettings, BaseState, Config, setting_field, state_field

config = Config(
    openapi_tags=["bot", "network", "coin", "group"], ui_menu={"/bot": "bot", "/groups": "groups", "/history": "history"}
)


class Settings(BaseSettings):
    mm_node_checker: Annotated[str, setting_field("", "mm node checker url")]
    proxies_url: Annotated[str, setting_field("http://localhost:8000", "proxies url, each proxy on new line")]
    round_ndigits: Annotated[int, setting_field(5, "round ndigits")]
    limit_network_workers: Annotated[int, setting_field(20, "How many requests to one network in parallel")]
    limit_naming_workers: Annotated[int, setting_field(20, "How many requests to one naming in parallel")]
    check_balance_interval: Annotated[int, setting_field(15, "Check balance interval in minutes")]
    check_name_interval: Annotated[int, setting_field(15, "Check name interval in minutes")]


class State(BaseState):
    check_balances: Annotated[bool, state_field(True)]
    check_namings: Annotated[bool, state_field(True)]
    proxies: Annotated[list[str], state_field([], "list of proxies")]
    proxies_updated_at: Annotated[datetime | None, state_field(None, "timestamp of last proxies update")]
    mm_node_checker: Annotated[dict[str, list[str]] | None, state_field(None, "mm_node_checker data")]
    mm_node_checker_updated_at: Annotated[datetime | None, state_field(None, "timestamp of last mm_node_checker update")]


for lib in ["httpcore", "httpx", "web3"]:
    logging.getLogger(lib).setLevel(logging.WARNING)
