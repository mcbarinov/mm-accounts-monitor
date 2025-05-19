from datetime import datetime

from fastapi import APIRouter
from mm_base6 import DC, DV, CoreConfig, DynamicConfigsModel, DynamicValuesModel, ServerConfig

core_config = CoreConfig()

server_config = ServerConfig()
server_config.tags = ["bot", "network", "coin", "group"]
server_config.main_menu = {"/bot": "bot", "/groups": "groups", "/history": "history"}


class DynamicConfigs(DynamicConfigsModel):
    mm_node_checker = DC("", "mm node checker url")
    proxies_url = DC("http://localhost:8000", "proxies url, each proxy on new line")
    round_ndigits = DC(5, "round ndigits")
    limit_network_workers = DC(20, "How many requests to one network in parallel")
    limit_naming_workers = DC(20, "How many requests to one naming in parallel")
    check_balance_interval = DC(15, "Check balance interval in minutes")
    check_name_interval = DC(15, "Check name interval in minutes")


class DynamicValues(DynamicValuesModel):
    check_balances: DV[bool] = DV(True)
    check_namings: DV[bool] = DV(True)
    proxies: DV[list[str]] = DV([])
    proxies_updated_at: DV[datetime | None] = DV(None)
    mm_node_checker: DV[dict[str, list[str]] | None] = DV(None)
    mm_node_checker_updated_at: DV[datetime | None] = DV(None)


def get_router() -> APIRouter:
    from app.server import routers

    router = APIRouter()

    router.include_router(routers.ui.router)
    router.include_router(routers.bot.router)
    router.include_router(routers.network.router)
    router.include_router(routers.coin.router)
    router.include_router(routers.group.router)
    router.include_router(routers.account_name.router)
    router.include_router(routers.account_balance.router)
    router.include_router(routers.rpc_monitoring.router)
    router.include_router(routers.history.router)

    return router
