from typing import Annotated, Any

import pydash
from bson import ObjectId
from litestar import Controller, Request, Router, get, post
from litestar.plugins.flash import flash
from litestar.response import Redirect, Template
from mm_base3 import FormBody, FormData, render_html
from mm_std import Err
from pydantic import BaseModel

from app.constants import Naming, NetworkType
from app.core import Core
from app.db import Network
from app.utils import multilines


class PagesController(Controller):
    path = "/"

    @get(sync_to_thread=False)
    def index(self) -> Template:
        return render_html("index.j2")

    @get("bot", sync_to_thread=True)
    def bot(self) -> Template:
        return render_html("bot.j2")

    @get("networks", sync_to_thread=False)
    def networks_page(self, core: Core) -> Template:
        networks = core.network_service.get_networks()
        return render_html("networks.j2", networks=networks, network_types=[t.value for t in NetworkType])

    @get("namings", sync_to_thread=True)
    def namings(self) -> Template:
        return render_html("namings.j2", namings=list(Naming))

    @get("coins", sync_to_thread=True)
    def coins(self, core: Core) -> Template:
        coins = core.db.coin.find({}, "network,symbol")
        return render_html("coins.j2", coins=coins)

    @get("groups", sync_to_thread=True)
    def groups(self, core: Core) -> Template:
        groups = core.db.group.find({}, "name")
        return render_html("groups.j2", groups=groups)

    @get("add-group", sync_to_thread=True)
    def add_group(self, core: Core) -> Template:
        coins = core.coin_service.get_coins()
        return render_html("add_group.j2", network_types=list(NetworkType), coins=coins, namings=list(Naming))

    @get("accounts/{group_id:str}", sync_to_thread=True)
    def accounts(self, core: Core, group_id: str) -> Template:
        group = core.db.group.get(ObjectId(group_id))
        info = core.group_service.get_group_accounts_info(ObjectId(group_id))
        return render_html("accounts.j2", group=group, info=info)

    @get("account-balances/{group_id:str}", sync_to_thread=True)
    def account_balances(self, core: Core, group_id: str) -> Template:
        group = core.db.group.get(ObjectId(group_id))
        account_balances = core.db.account_balance.find({"group_id": ObjectId(group_id)}, "account,coin")
        return render_html("account_balances.j2", group=group, account_balances=account_balances)

    @get("account-namings/{group_id:str}", sync_to_thread=True)
    def account_namings(self, core: Core, group_id: str) -> Template:
        group = core.db.group.get(ObjectId(group_id))
        account_namings = core.db.account_naming.find({"group_id": ObjectId(group_id)}, "account,naming")
        return render_html("account_namings.j2", group=group, account_namings=account_namings)


class ActionsController(Controller):
    path = "/"

    class AddNetworkForm(BaseModel):
        id: str
        type: NetworkType
        rpc_urls: str
        explorer_url: str

        def to_db(self) -> Network:
            rpc_urls = [line.strip() for line in self.rpc_urls.split("\n") if line.strip()]
            return Network(id=self.id, type=self.type, rpc_urls=pydash.uniq(rpc_urls), explorer_url=self.explorer_url)

    class AddGroupForm(BaseModel):
        name: str
        network_type: NetworkType
        notes: str
        coins: list[str] | str
        namings: list[str] | str

        @property
        def coins_list(self) -> list[str]:
            if isinstance(self.coins, str):
                return [self.coins]
            return self.coins

        @property
        def namings_list(self) -> list[Naming]:
            if isinstance(self.namings, str):
                return [Naming(self.namings)]
            return [Naming(n) for n in self.namings]

    class UpdateCoins(BaseModel):
        value: list[str]

    @post("add-network", sync_to_thread=True)
    def add_network(self, core: Core, data: Annotated[AddNetworkForm, FormBody], request: Request[Any, Any, Any]) -> Redirect:
        core.db.network.insert_one(data.to_db())
        flash(request, "network added successfully", "success")
        return Redirect("/networks")

    @post("add-group", sync_to_thread=True)
    def add_group(self, core: Core, data: Annotated[AddGroupForm, FormBody], request: Request[Any, Any, Any]) -> Redirect:
        core.group_service.create_group(data.name, data.network_type, data.notes, data.namings_list, data.coins_list)
        flash(request, "group added successfully", "success")
        return Redirect("/groups")

    @post("update-explorer-url/{id:str}", sync_to_thread=True)
    def update_explorer_url(self, core: Core, id: str, data: FormData, request: Request[Any, Any, Any]) -> Redirect:
        core.db.network.update_one({"_id": id}, {"$set": {"explorer_url": data["value"]}})
        flash(request, "explorer url updated successfully", "success")
        return Redirect("/networks")

    @post("add-rpc-url/{id:str}", sync_to_thread=True)
    def add_rpc_url(self, core: Core, id: str, data: FormData, request: Request[Any, Any, Any]) -> Redirect:
        core.db.network.update_one({"_id": id}, {"$push": {"rpc_urls": data["value"]}})
        flash(request, "rpc url added successfully", "success")
        return Redirect("/networks")

    @get("delete-rpc-url/{id:str}", sync_to_thread=True)
    def delete_rpc_url(self, core: Core, id: str, value: str, request: Request[Any, Any, Any]) -> Redirect:
        core.db.network.update_one({"_id": id}, {"$pull": {"rpc_urls": value}})
        flash(request, "rpc url deleted successfully", "success")
        return Redirect("/networks")

    @get("export-networks", sync_to_thread=True)
    def export_networks(self, core: Core) -> str:
        return core.network_service.export_as_toml()

    @post("import-networks", sync_to_thread=True)
    def import_networks(self, core: Core, data: FormData, request: Request[Any, Any, Any]) -> Redirect:
        res = core.network_service.import_from_toml(data["value"])
        if isinstance(res, Err):
            flash(request, f"can't import networks: {res.err}", "error")
        else:
            flash(request, f"{res.ok} networks imported successfully", "success")
        return Redirect("/networks")

    @get("export-coins", sync_to_thread=True)
    def export_coins(self, core: Core) -> str:
        return core.coin_service.export_as_toml()

    @post("import-coins", sync_to_thread=True)
    def import_coins(self, core: Core, data: FormData, request: Request[Any, Any, Any]) -> Redirect:
        res = core.coin_service.import_from_toml(data["value"])
        if isinstance(res, Err):
            flash(request, f"can't import coins: {res.err}", "error")
        else:
            flash(request, f"{res.ok} coins imported successfully", "success")
        return Redirect("/coins")

    @post("update-accounts/{group_id:str}", sync_to_thread=True)
    def update_accounts(self, core: Core, group_id: str, data: FormData, request: Request[Any, Any, Any]) -> Redirect:
        core.group_service.update_accounts(ObjectId(group_id), multilines(data["value"]))
        flash(request, "accounts updated successfully", "success")
        return Redirect("/groups")

    @post("update-coins/{group_id:str}", sync_to_thread=True)
    def update_coins(
        self, core: Core, group_id: str, data: Annotated[UpdateCoins, FormBody], request: Request[Any, Any, Any]
    ) -> Redirect:
        core.group_service.update_coins(ObjectId(group_id), data.value)
        flash(request, "coins updated successfully", "success")
        return Redirect("/groups")


ui_router = Router(path="/", route_handlers=[PagesController, ActionsController], include_in_schema=False)
