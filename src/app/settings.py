import logging
from datetime import datetime

from fastapi import APIRouter
from mm_base6 import DC, DV, CoreConfig, DynamicConfigsModel, DynamicValuesModel, ServerConfig
from mm_web3 import Network

from app.core.constants import Naming
from app.core.types import AppCore

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


async def configure_scheduler(core: AppCore) -> None:
    """Configure background scheduler tasks."""
    # check balances
    for network in Network:
        task_id = "balances_on_" + network.value
        core.scheduler.add_task(task_id, 2, core.services.balance.check_next_network, args=(network,))

    # check namings
    for naming in list(Naming):
        task_id = "names_on_" + naming
        core.scheduler.add_task(task_id, 2, core.services.name.check_next_naming, args=(naming,))

    # mm-node-checker
    core.scheduler.add_task("mm-node-checker", 30, core.services.network.update_mm_node_checker)


async def start_core(core: AppCore) -> None:
    """Startup logic for the application."""
    libraries = ["httpcore", "httpx", "web3"]
    for lib in libraries:
        logging.getLogger(lib).setLevel(logging.WARNING)

    await core.services.network.load_rpc_urls_from_db()
    await core.services.coin.load_coins_from_db()


async def stop_core(core: AppCore) -> None:
    """Cleanup logic for the application."""


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
