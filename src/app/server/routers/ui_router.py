from typing import Annotated

import pydash
from bson import ObjectId
from fastapi import APIRouter, Depends, Form
from mm_base6 import cbv, redirect
from mm_std import Err, str_to_list
from pydantic import BaseModel, Field
from starlette.responses import HTMLResponse, PlainTextResponse, RedirectResponse

from app.core.constants import Naming, NetworkType
from app.core.db import Network
from app.server import utils
from app.server.deps import View

router = APIRouter(include_in_schema=False)


@cbv(router)
class CBV(View):
    @router.get("/")
    async def index(self) -> HTMLResponse:
        return await self.render.html("index.j2")

    @router.get("/bot")
    async def bot(self) -> HTMLResponse:
        return await self.render.html("bot.j2")

    @router.get("/networks")
    async def networks(self) -> HTMLResponse:
        networks = await self.core.network_service.get_networks()
        return await self.render.html("networks.j2", networks=networks, network_types=[t.value for t in NetworkType])

    @router.get("/networks/oldest-checked-time")
    async def networks_oldest_checked_time(self) -> HTMLResponse:
        stats = await self.core.network_service.calc_oldest_checked_time()
        return await self.render.html("networks_oldest_checked_time.j2", stats=stats)

    @router.get("/namings")
    async def namings(self) -> HTMLResponse:
        oldest_checked_time = await self.core.name_service.calc_oldest_checked_time()
        return await self.render.html("namings.j2", namings=list(Naming), oldest_checked_time=oldest_checked_time)

    @router.get("/coins")
    async def coins(self) -> HTMLResponse:
        explorer_token_map = await self.core.coin_service.explorer_token_map()
        return await self.render.html(
            "coins.j2", coins=await self.core.coin_service.get_coins(), explorer_token_map=explorer_token_map
        )

    @router.get("/coins/oldest-checked-time")
    async def coins_oldest_checked_time(self) -> HTMLResponse:
        stats = await self.core.coin_service.calc_oldest_checked_time()
        return await self.render.html("coins_oldest_checked_time.j2", stats=stats)

    @router.get("/groups")
    async def groups(self) -> HTMLResponse:
        groups = await self.core.db.group.find({}, "name")
        coins = await self.core.coin_service.get_coins()
        coins_by_network_type = await self.core.coin_service.get_coins_by_network_type()
        return await self.render.html(
            "groups.j2",
            groups=groups,
            coins=coins,
            network_types=list(NetworkType),
            namings=list(Naming),
            coins_by_network_type=coins_by_network_type,
        )

    @router.get("/groups/{group_id}")
    async def group(self, group_id: ObjectId) -> HTMLResponse:
        group = await self.core.db.group.get(group_id)
        info = await self.core.group_service.get_group_accounts_info(group_id)
        return await self.render.html("group.j2", group=group, info=info)

    @router.get("/accounts/{group_id}/balances")
    async def account_balances_page(self, group_id: ObjectId) -> HTMLResponse:
        group = await self.core.db.group.get(ObjectId(group_id))
        account_balances = await self.core.db.account_balance.find({"group_id": ObjectId(group_id)}, "account,coin")
        return await self.render.html("account_balances.j2", group=group, account_balances=account_balances)

    @router.get("/accounts/{group_id}/names")
    async def account_names_page(self, group_id: ObjectId) -> HTMLResponse:
        group = await self.core.db.group.get(ObjectId(group_id))
        account_names = await self.core.db.account_name.find({"group_id": ObjectId(group_id)}, "account,naming")
        return await self.render.html("account_names.j2", group=group, account_names=account_names)

    @router.get("/naming-problems")
    async def naming_problems_page(self) -> HTMLResponse:
        problems = await self.core.db.naming_problem.find({}, "-created_at", 1000)
        return await self.render.html("naming_problems.j2", problems=problems)

    @router.get("/rpc-monitoring")
    async def rpc_monitoring_page(
        self,
        network: str | None = None,
        success: Annotated[bool | None, Depends(utils.optional_bool("success"))] = None,
        limit: int = 1000,
    ) -> HTMLResponse:
        form = {"network": network, "success": success, "limit": limit}
        query: dict[str, object] = {}
        if network:
            query["network"] = network
        if success is not None:
            query["success"] = success
        monitoring = await self.core.db.rpc_monitoring.find(query, "-created_at", limit)
        networks = [n.id for n in await self.core.network_service.get_networks()]
        return await self.render.html("rpc_monitoring.j2", monitoring=monitoring, networks=networks, form=form)

    @router.get("/history")
    async def history_page(self) -> HTMLResponse:
        history = await self.core.db.history.find({}, "-created_at", 100)
        return await self.render.html("history.j2", history=history)

    @router.get("/history/{id}")
    async def history_accounts_page(self, id: ObjectId) -> HTMLResponse:
        history = await self.core.db.history.get(id)
        info = await self.core.history_service.get_history_group_accounts_info(id)
        return await self.render.html("history_accounts.j2", history=history, info=info)

    @router.get("/history/{id}/diff")
    async def get_history_diff_page(self, id: ObjectId) -> HTMLResponse:
        history = await self.core.db.history.get(id)
        coins_map = await self.core.coin_service.get_coins_map()
        diff = await self.core.history_service.get_balances_diff(id)
        return await self.render.html("history_diff.j2", history=history, diff=diff, coins_map=coins_map)


@cbv(router)
class ActionCBV(View):
    class AddNetworkForm(BaseModel):
        id: str
        type: NetworkType
        rpc_urls: str
        explorer_address: str
        explorer_token: str

        def to_db(self) -> Network:
            rpc_urls = [line.strip() for line in self.rpc_urls.split("\n") if line.strip()]
            return Network(
                id=self.id,
                type=self.type,
                rpc_urls=pydash.uniq(rpc_urls),
                explorer_address=self.explorer_address,
                explorer_token=self.explorer_token,
            )

    @router.post("/networks")
    async def add_network(self, data: Annotated[AddNetworkForm, Form()]) -> RedirectResponse:
        await self.core.db.network.insert_one(data.to_db())
        self.render.flash("network added successfully")
        return redirect("/networks")

    @router.post("/networks/import")
    async def import_networks(self, value: Annotated[str, Form()]) -> RedirectResponse:
        res = await self.core.network_service.import_from_toml(value)
        if isinstance(res, Err):
            self.render.flash(f"can't import networks: {res.err}", is_error=True)
        else:
            self.render.flash(f"{res.ok} networks imported successfully")
        return redirect("/networks")

    @router.get("/networks/export", response_class=PlainTextResponse)
    async def export_networks(self) -> str:
        return await self.core.network_service.export_as_toml()

    @router.post("/networks/{id}/explorer")
    async def update_explorer_url(self, id: str, value: Annotated[str, Form()]) -> RedirectResponse:
        await self.core.db.network.update_one({"_id": id}, {"$set": {"explorer_url": value}})
        self.render.flash("explorer url updated successfully")
        return redirect("/networks")

    @router.post("/networks/{id}/add-rpc")
    async def add_rpc_url(self, id: str, value: Annotated[str, Form()]) -> RedirectResponse:
        await self.core.db.network.update_one({"_id": id}, {"$push": {"rpc_urls": value}})
        self.render.flash("rpc url added successfully")
        return redirect("/networks")

    @router.get("/networks/{id}/delete-rpc")
    async def delete_rpc_url(self, id: str, value: str) -> RedirectResponse:
        await self.core.db.network.update_one({"_id": id}, {"$pull": {"rpc_urls": value}})
        self.render.flash("rpc url deleted successfully")
        return redirect("/networks")

    @router.get("/coins/export", response_class=PlainTextResponse)
    async def export_coins(self) -> str:
        return await self.core.coin_service.export_as_toml()

    @router.post("/coins/import")
    async def import_coins(self, value: Annotated[str, Form()]) -> RedirectResponse:
        res = await self.core.coin_service.import_from_toml(value)
        if isinstance(res, Err):
            self.render.flash(f"can't import coins: {res.err}", is_error=True)
        else:
            self.render.flash(f"{res.ok} coins imported successfully")
        return redirect("/coins")

    class CreateGroupForm(BaseModel):
        name: str
        network_type: NetworkType
        notes: str
        coins: list[str] | str = Field(default_factory=list)  # type: ignore[arg-type]
        namings: list[str] | str = Field(default_factory=list)  # type: ignore[arg-type]

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

    @router.post("/groups")
    async def create_group(self, data: Annotated[CreateGroupForm, Form()]) -> RedirectResponse:
        await self.core.group_service.create_group(data.name, data.network_type, data.notes, data.namings_list, data.coins_list)
        self.render.flash("group added successfully")
        return redirect("/groups")

    @router.post("/groups/import")
    async def import_groups(self, toml: Annotated[str, Form()]) -> RedirectResponse:
        count = await self.core.group_service.import_from_toml(toml)
        self.render.flash(f"groups imported successfully: {count}")
        return redirect("/groups")

    @router.post("/groups/{id}/accounts")
    async def update_accounts(self, id: ObjectId, value: Annotated[str, Form()]) -> RedirectResponse:
        await self.core.group_service.update_accounts(id, str_to_list(value, unique=True))
        self.render.flash("accounts updated successfully")
        return redirect("/groups")

    @router.post("/groups/{id}/coins")
    async def update_coins(self, id: ObjectId, value: Annotated[list[str], Form()]) -> RedirectResponse:
        await self.core.group_service.update_coins(id, value)
        self.render.flash("coins updated successfully")
        return redirect("/groups")

    @router.post("/groups/{id}/update-account-notes")
    async def update_account_notes(
        self, id: ObjectId, account: Annotated[str, Form()], notes: Annotated[str, Form()]
    ) -> RedirectResponse:
        await self.core.db.group.set(id, {f"account_notes.{account}": notes})
        self.render.flash("account notes updated successfully")
        return redirect("/groups/" + str(id))
