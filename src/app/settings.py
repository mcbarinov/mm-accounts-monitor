from datetime import datetime

from fastapi import APIRouter
from mm_base6 import DC, DV, CoreConfig, DConfigModel, DValueModel, ServerConfig

core_config = CoreConfig()

server_config = ServerConfig()
server_config.tags = ["bot", "network", "coin"]
server_config.main_menu = {"/bot": "bot", "/groups": "groups"}


class DConfigSettings(DConfigModel):
    proxies_url = DC("http://localhost:8000", "proxies url, each proxy on new line")
    round_ndigits = DC(5, "round ndigits")
    max_workers_networks = DC(10, "How many networks process in parallel")
    max_workers_coins = DC(5, "How many coins process in parallel in one network")
    max_workers_namings = DC(5, "How many namings process in parallel in one network")
    check_balance_interval = DC(15, "Check balance interval in minutes")
    check_naming_interval = DC(15, "Check naming interval in minutes")


class DValueSettings(DValueModel):
    check_balances: DV[bool] = DV(True)
    check_namings: DV[bool] = DV(True)
    proxies: DV[list[str]] = DV([])
    proxies_updated_at: DV[datetime | None] = DV(None)


def get_router() -> APIRouter:
    from app.server.routers import (
        account_balance_router,
        account_naming_router,
        bot_router,
        coin_router,
        group_router,
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
    router.include_router(account_naming_router.router)
    router.include_router(account_balance_router.router)
    router.include_router(rpc_monitoring_router.router)

    return router
