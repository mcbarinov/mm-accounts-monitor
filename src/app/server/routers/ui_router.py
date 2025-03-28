from collections.abc import Callable
from typing import Annotated

import pydash
from bson import ObjectId
from fastapi import APIRouter, Depends, Form, HTTPException, Query
from mm_base6 import RenderDep, redirect
from mm_std import Err, str_to_list
from pydantic import BaseModel, Field
from starlette.responses import HTMLResponse, PlainTextResponse, RedirectResponse

from app.core.constants import Naming, NetworkType
from app.core.db import Network
from app.server.deps import CoreDep

router = APIRouter(include_in_schema=False)


@router.get("/")
async def index_page(render: RenderDep) -> HTMLResponse:
    return await render.html("index.j2")


@router.get("/bot")
async def bot_page(render: RenderDep) -> HTMLResponse:
    return await render.html("bot.j2")


@router.get("/networks")
async def networks_page(render: RenderDep, core: CoreDep) -> HTMLResponse:
    networks = await core.network_service.get_networks()
    return await render.html("networks.j2", networks=networks, network_types=[t.value for t in NetworkType])


@router.get("/networks/oldest-checked-time")
async def get_networks_oldest_checked_time_page(render: RenderDep, core: CoreDep) -> HTMLResponse:
    stats = await core.network_service.calc_oldest_checked_time()
    return await render.html("networks_oldest_checked_time.j2", stats=stats)


@router.get("/namings")
async def namings_page(render: RenderDep, core: CoreDep) -> HTMLResponse:
    oldest_checked_time = await core.naming_service.calc_oldest_checked_time()
    return await render.html("namings.j2", namings=list(Naming), oldest_checked_time=oldest_checked_time)


@router.get("/coins")
async def coins_page(render: RenderDep, core: CoreDep) -> HTMLResponse:
    explorer_token_map = await core.coin_service.explorer_token_map()
    return await render.html("coins.j2", coins=await core.coin_service.get_coins(), explorer_token_map=explorer_token_map)


@router.get("/coins/oldest-checked-time")
async def get_coins_oldest_checked_time_page(render: RenderDep, core: CoreDep) -> HTMLResponse:
    stats = await core.coin_service.calc_oldest_checked_time()
    return await render.html("coins_oldest_checked_time.j2", stats=stats)


@router.get("/groups")
async def groups_page(render: RenderDep, core: CoreDep) -> HTMLResponse:
    groups = await core.db.group.find({}, "name")
    coins = await core.coin_service.get_coins()
    coins_by_network_type = await core.coin_service.get_coins_by_network_type()
    return await render.html(
        "groups.j2",
        groups=groups,
        coins=coins,
        network_types=list(NetworkType),
        namings=list(Naming),
        coins_by_network_type=coins_by_network_type,
    )


@router.get("/accounts/{group_id}")
async def accounts(render: RenderDep, core: CoreDep, group_id: ObjectId) -> HTMLResponse:
    group = await core.db.group.get(group_id)
    info = await core.group_service.get_group_accounts_info(group_id)
    return await render.html("accounts.j2", group=group, info=info)


@router.get("/accounts/{group_id}/balances")
async def account_balances_page(render: RenderDep, core: CoreDep, group_id: ObjectId) -> HTMLResponse:
    group = await core.db.group.get(ObjectId(group_id))
    account_balances = await core.db.account_balance.find({"group_id": ObjectId(group_id)}, "account,coin")
    return await render.html("account_balances.j2", group=group, account_balances=account_balances)


@router.get("/accounts/{group_id}/namings")
async def account_namings_page(render: RenderDep, core: CoreDep, group_id: ObjectId) -> HTMLResponse:
    group = await core.db.group.get(ObjectId(group_id))
    account_namings = await core.db.account_naming.find({"group_id": ObjectId(group_id)}, "account,naming")
    return await render.html("account_namings.j2", group=group, account_namings=account_namings)


@router.get("/naming-problems")
async def naming_problems_page(render: RenderDep, core: CoreDep) -> HTMLResponse:
    problems = await core.db.naming_problem.find({}, "-created_at", 1000)
    return await render.html("naming_problems.j2", problems=problems)


def optional_bool(param_name: str) -> Callable[[str | None], bool | None]:
    def func(value: str | None = Query(None, alias=param_name)) -> bool | None:
        # Treat empty string as None
        if value == "" or value is None:
            return None
        # Convert common representations of booleans
        if value.lower() in ("true", "1", "yes"):
            return True
        if value.lower() in ("false", "0", "no"):
            return False
        raise HTTPException(status_code=400, detail="Invalid boolean value")

    return func


@router.get("/rpc-monitoring")
async def rpc_monitoring_page(
    render: RenderDep,
    core: CoreDep,
    network: str | None = None,
    success: Annotated[bool | None, Depends(optional_bool("success"))] = None,
    limit: int = 1000,
) -> HTMLResponse:
    form = {"network": network, "success": success, "limit": limit}
    query: dict[str, object] = {}
    if network:
        query["network"] = network
    if success is not None:
        query["success"] = success
    monitoring = await core.db.rpc_monitoring.find(query, "-created_at", limit)
    networks = [n.id for n in await core.network_service.get_networks()]
    return await render.html("rpc_monitoring.j2", monitoring=monitoring, networks=networks, form=form)


@router.get("/history")
async def history_page(render: RenderDep, core: CoreDep) -> HTMLResponse:
    history = await core.db.history.find({}, "-created_at", 100)
    return await render.html("history.j2", history=history)


@router.get("/history/{id}")
async def history_accounts(render: RenderDep, core: CoreDep, id: ObjectId) -> HTMLResponse:
    history = await core.db.history.get(id)
    info = await core.history_service.get_history_group_accounts_info(id)
    return await render.html("history_accounts.j2", history=history, info=info)


# actions


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
async def add_network(render: RenderDep, core: CoreDep, data: Annotated[AddNetworkForm, Form()]) -> RedirectResponse:
    await core.db.network.insert_one(data.to_db())
    render.flash("network added successfully")
    return redirect("/networks")


@router.post("/networks/import")
async def import_networks(render: RenderDep, core: CoreDep, value: Annotated[str, Form()]) -> RedirectResponse:
    res = await core.network_service.import_from_toml(value)
    if isinstance(res, Err):
        render.flash(f"can't import networks: {res.err}", is_error=True)
    else:
        render.flash(f"{res.ok} networks imported successfully")
    return redirect("/networks")


@router.get("/networks/export", response_class=PlainTextResponse)
async def export_networks(core: CoreDep) -> str:
    return await core.network_service.export_as_toml()


@router.post("/networks/{id}/explorer")
async def update_explorer_url(render: RenderDep, core: CoreDep, id: str, value: Annotated[str, Form()]) -> RedirectResponse:
    await core.db.network.update_one({"_id": id}, {"$set": {"explorer_url": value}})
    render.flash("explorer url updated successfully")
    return redirect("/networks")


@router.post("/networks/{id}/add-rpc")
async def add_rpc_url(render: RenderDep, core: CoreDep, id: str, value: Annotated[str, Form()]) -> RedirectResponse:
    await core.db.network.update_one({"_id": id}, {"$push": {"rpc_urls": value}})
    render.flash("rpc url added successfully")
    return redirect("/networks")


@router.get("/networks/{id}/delete-rpc")
async def delete_rpc_url(render: RenderDep, core: CoreDep, id: str, value: str) -> RedirectResponse:
    await core.db.network.update_one({"_id": id}, {"$pull": {"rpc_urls": value}})
    render.flash("rpc url deleted successfully")
    return redirect("/networks")


@router.get("/coins/export", response_class=PlainTextResponse)
async def export_coins(core: CoreDep) -> str:
    return await core.coin_service.export_as_toml()


@router.post("/coins/import")
async def import_coins(render: RenderDep, core: CoreDep, value: Annotated[str, Form()]) -> RedirectResponse:
    res = await core.coin_service.import_from_toml(value)
    if isinstance(res, Err):
        render.flash(f"can't import coins: {res.err}", is_error=True)
    else:
        render.flash(f"{res.ok} coins imported successfully")
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
async def create_group(render: RenderDep, core: CoreDep, data: Annotated[CreateGroupForm, Form()]) -> RedirectResponse:
    await core.group_service.create_group(data.name, data.network_type, data.notes, data.namings_list, data.coins_list)
    render.flash("group added successfully")
    return redirect("/groups")


@router.post("/groups/import")
async def import_groups(render: RenderDep, core: CoreDep, toml: Annotated[str, Form()]) -> RedirectResponse:
    count = await core.group_service.import_from_toml(toml)
    render.flash(f"groups imported successfully: {count}")
    return redirect("/groups")


@router.post("/groups/{id}/accounts")
async def update_accounts(render: RenderDep, core: CoreDep, id: ObjectId, value: Annotated[str, Form()]) -> RedirectResponse:
    await core.group_service.update_accounts(id, str_to_list(value, unique=True))
    render.flash("accounts updated successfully")
    return redirect("/groups")


@router.post("/groups/{id}/coins")
async def update_coins(render: RenderDep, core: CoreDep, id: ObjectId, value: Annotated[list[str], Form()]) -> RedirectResponse:
    await core.group_service.update_coins(id, value)
    render.flash("coins updated successfully")
    return redirect("/groups")
