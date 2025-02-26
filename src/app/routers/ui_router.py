from typing import Annotated, Any

import pydash
from litestar import Controller, Request, Router, get, post
from litestar.plugins.flash import flash
from litestar.response import Redirect, Template
from mm_base3 import FormBody, FormData, render_html
from mm_std import Err
from pydantic import BaseModel

from app.core import Core
from app.db import Network


class PagesController(Controller):
    path = "/"

    @get()
    def index(self) -> Template:
        return render_html("index.j2")

    @get("networks")
    def networks_page(self, core: Core) -> Template:
        networks = core.db.network.find({}, "_id")
        return render_html("networks.j2", networks=networks)


class ActionsController(Controller):
    path = "/"

    class AddNetworkForm(BaseModel):
        id: str
        rpc_urls: str
        explorer_url: str

        def db_model(self) -> Network:
            rpc_urls = [line.strip() for line in self.rpc_urls.split("\n") if line.strip()]
            return Network(id=self.id, rpc_urls=pydash.uniq(rpc_urls), explorer_url=self.explorer_url)

    @post("add-network")
    def add_network(self, core: Core, data: Annotated[AddNetworkForm, FormBody], request: Request[Any, Any, Any]) -> Redirect:
        core.db.network.insert_one(data.db_model())
        flash(request, "network added successfully", "success")
        return Redirect("/networks")

    @post("update-explorer-url/{id:str}")
    def update_explorer_url(self, core: Core, id: str, data: FormData, request: Request[Any, Any, Any]) -> Redirect:
        core.db.network.update_one({"_id": id}, {"$set": {"explorer_url": data["value"]}})
        flash(request, "explorer url updated successfully", "success")
        return Redirect("/networks")

    @post("add-rpc-url/{id:str}")
    def add_rpc_url(self, core: Core, id: str, data: FormData, request: Request[Any, Any, Any]) -> Redirect:
        core.db.network.update_one({"_id": id}, {"$push": {"rpc_urls": data["value"]}})
        flash(request, "rpc url added successfully", "success")
        return Redirect("/networks")

    @get("delete-rpc-url/{id:str}")
    def delete_rpc_url(self, core: Core, id: str, value: str, request: Request[Any, Any, Any]) -> Redirect:
        core.db.network.update_one({"_id": id}, {"$pull": {"rpc_urls": value}})
        flash(request, "rpc url deleted successfully", "success")
        return Redirect("/networks")

    @get("export-networks")
    def export_networks(self, core: Core) -> str:
        return core.network_service.export_as_toml()

    @post("import-networks")
    def import_networks(self, core: Core, data: FormData, request: Request[Any, Any, Any]) -> Redirect:
        res = core.network_service.import_from_toml(data["value"])
        if isinstance(res, Err):
            flash(request, f"can't import networks: {res.err}", "error")
        else:
            flash(request, f"{res.ok} networks imported successfully", "success")
        return Redirect("/networks")


ui_router = Router(path="/", route_handlers=[PagesController, ActionsController], include_in_schema=False)
