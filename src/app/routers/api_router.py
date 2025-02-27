from bson import ObjectId
from litestar import Controller, Router, delete, get, post
from mm_std import Result

from app.core import Core
from app.db import AccountBalance, Group, Network
from app.services.group_service import ProcessAccountBalancesResult


class BotController(Controller):
    path = "bot"
    tags = ["bot"]

    @post("update-proxies")
    def update_proxies(self, core: Core) -> int:
        return core.bot_service.update_proxies()


class NetworkController(Controller):
    path = "networks"
    tags = ["network"]

    @get()
    def get_all_networks(self, core: Core) -> list[Network]:
        return core.db.network.find({}, "_id")

    @get("{id:str}")
    def get_network(self, core: Core, id: str) -> Network:
        return core.db.network.get(id)

    @delete("{id:str}")
    def delete_network(self, core: Core, id: str) -> None:
        # TODO: delete all coins associated with this network
        core.db.network.delete(id)


class GroupController(Controller):
    path = "groups"
    tags = ["group"]

    @get()
    def get_all_groups(self, core: Core) -> list[Group]:
        return core.db.group.find({}, "_id")

    @get("{id:str}")
    def get_group(self, core: Core, id: str) -> Group:
        return core.db.group.get(ObjectId(id))

    @delete("{id:str}")
    def delete_group(self, core: Core, id: str) -> None:
        core.db.group.delete(ObjectId(id))

    @post("{id:str}/process-account-balances")
    def process_account_balances(self, core: Core, id: str) -> ProcessAccountBalancesResult:
        return core.group_service.process_account_balances(ObjectId(id))


class AccountBalanceController(Controller):
    path = "account-balances"

    @get("/{id:str}")
    def get_account_balance(self, core: Core, id: str) -> AccountBalance:
        return core.db.account_balance.get(ObjectId(id))

    @post("/{id:str}/check")
    def check_account_balance(self, core: Core, id: str) -> Result[int]:
        return core.balance_service.check_account_balance(ObjectId(id))


api_router = Router(path="/api", route_handlers=[BotController, NetworkController, GroupController, AccountBalanceController])
