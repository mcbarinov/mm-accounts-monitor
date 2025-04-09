from datetime import datetime

from fastapi import APIRouter
from mm_base6 import DC, DV, CoreConfig, DConfigModel, DValueModel, ServerConfig

core_config = CoreConfig()

server_config = ServerConfig()
server_config.tags = ["bot", "network", "coin", "group"]
server_config.main_menu = {"/bot": "bot", "/groups": "groups", "/history": "history"}


class DConfigSettings(DConfigModel):
    mm_node_checker = DC("", "mm node checker url")
    proxies_url = DC("http://localhost:8000", "proxies url, each proxy on new line")
    round_ndigits = DC(5, "round ndigits")
    limit_network_workers = DC(20, "How many requests to one network in parallel")
    limit_naming_workers = DC(20, "How many requests to one naming in parallel")
    check_balance_interval = DC(15, "Check balance interval in minutes")
    check_name_interval = DC(15, "Check name interval in minutes")


class DValueSettings(DValueModel):
    check_balances: DV[bool] = DV(True)
    check_namings: DV[bool] = DV(True)
    proxies: DV[list[str]] = DV([])
    proxies_updated_at: DV[datetime | None] = DV(None)
    mm_node_checker: DV[dict[str, list[str]] | None] = DV(None)
    mm_node_checker_updated_at: DV[datetime | None] = DV(None)


def get_router() -> APIRouter:
    from app.server.routers import (
        account_balance_router,
        account_name_router,
        bot_router,
        coin_router,
        group_router,
        history_router,
        network_router,
        rpc_monitoring_router,
        ui_router,
    )

    router = APIRouter()
    router.include_router(ui_router.router)
    router.include_router(bot_router.router)
    router.include_router(network_router.router)
    router.include_router(coin_router.router)
    router.include_router(group_router.router)
    router.include_router(account_name_router.router)
    router.include_router(account_balance_router.router)
    router.include_router(rpc_monitoring_router.router)
    router.include_router(history_router.router)

    return router
