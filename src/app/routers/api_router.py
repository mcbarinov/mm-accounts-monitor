from bson import ObjectId
from litestar import Controller, Router, delete, get, post
from mm_std import Result

from app.core import Core
from app.db import AccountBalance, AccountNaming, Group, Network
from app.services.group_service import ProcessAccountBalancesResult, ProcessAccountNamingsResult


class BotController(Controller):
    path = "bot"
    tags = ["bot"]

    @post("update-proxies", sync_to_thread=True)
    def update_proxies(self, core: Core) -> int:
        return core.bot_service.update_proxies()

    @post("toggle-check-balances", sync_to_thread=True)
    def toggle_check_balances(self, core: Core) -> None:
        core.bot_service.toggle_check_balances()

    @post("toggle-check-namings", sync_to_thread=True)
    def toggle_check_namings(self, core: Core) -> None:
        core.bot_service.toggle_check_namings()


class NetworkController(Controller):
    path = "networks"
    tags = ["network"]

    @get(sync_to_thread=False)
    def get_all_networks(self, core: Core) -> list[Network]:
        return core.network_service.get_networks()

    @get("{id:str}", sync_to_thread=False)
    def get_network(self, core: Core, id: str) -> Network:
        return core.network_service.get_network(id)

    @delete("{id:str}", sync_to_thread=True)
    def delete_network(self, core: Core, id: str) -> None:
        # TODO: delete all coins associated with this network
        core.db.network.delete(id)


class GroupController(Controller):
    path = "groups"
    tags = ["group"]

    @get(sync_to_thread=True)
    def get_all_groups(self, core: Core) -> list[Group]:
        return core.db.group.find({}, "_id")

    @get("{id:str}", sync_to_thread=True)
    def get_group(self, core: Core, id: str) -> Group:
        return core.db.group.get(ObjectId(id))

    @delete("{id:str}", sync_to_thread=True)
    def delete_group(self, core: Core, id: str) -> None:
        core.group_service.delete_group(ObjectId(id))

    @post("{id:str}/process-account-balances", sync_to_thread=True)
    def process_account_balances(self, core: Core, id: str) -> ProcessAccountBalancesResult:
        return core.group_service.process_account_balances(ObjectId(id))

    @post("{id:str}/process-account-namings", sync_to_thread=True)
    def process_account_namings(self, core: Core, id: str) -> ProcessAccountNamingsResult:
        return core.group_service.process_account_namings(ObjectId(id))


class AccountBalanceController(Controller):
    path = "account-balances"
    tags = ["balance"]

    @get("/{id:str}", sync_to_thread=True)
    def get_account_balance(self, core: Core, id: str) -> AccountBalance:
        return core.db.account_balance.get(ObjectId(id))

    @post("/{id:str}/check", sync_to_thread=True)
    def check_account_balance(self, core: Core, id: str) -> Result[int]:
        return core.balance_service.check_account_balance(ObjectId(id))


class AccountNamingController(Controller):
    path = "account-namings"
    tags = ["naming"]

    @get("/{id:str}", sync_to_thread=True)
    def get_account_naming(self, core: Core, id: str) -> AccountNaming:
        return core.db.account_naming.get(ObjectId(id))

    @post("/{id:str}/check", sync_to_thread=True)
    def check_account_naming(self, core: Core, id: str) -> Result[str | None]:
        core.logger.debug("check_account_naming called: %s", id)
        return core.naming_service.check_account_naming(ObjectId(id))


api_router = Router(
    path="/api",
    route_handlers=[BotController, NetworkController, GroupController, AccountBalanceController, AccountNamingController],
)
