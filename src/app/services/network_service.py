from __future__ import annotations

import tomlkit
from mm_std import Err, Ok, Result
from pydantic import BaseModel
from tomlkit.items import Table

from app.constants import NetworkType
from app.db import Network
from app.types_ import AppBaseService, AppBaseServiceParams


class ImportNetworkItem(BaseModel):
    id: str
    type: NetworkType
    rpc_urls: str
    explorer_url: str

    @property
    def rpc_urls_list(self) -> list[str]:
        return [u.strip() for u in self.rpc_urls.splitlines() if u.strip()]


class NetworkService(AppBaseService):
    def __init__(self, base_params: AppBaseServiceParams) -> None:
        super().__init__(base_params)

    def export_as_toml(self) -> str:
        doc = tomlkit.document()
        networks: list[Table] = []
        for n in self.db.network.find({}, "_id"):
            network = tomlkit.table()
            network.add("id", n.id)
            network.add("type", n.type)
            network.add("rpc_urls", tomlkit.string("\n".join(n.rpc_urls), multiline=True))
            network.add("explorer_url", n.explorer_url)
            networks.append(network)

        doc.add("networks", *networks)
        return tomlkit.dumps(doc)

    def import_from_toml(self, toml_str: str) -> Result[int]:
        try:
            networks = [ImportNetworkItem(**n) for n in tomlkit.loads(toml_str)["networks"]]  # type:ignore[arg-type,union-attr]
            for n in networks:
                self.db.network.set(
                    n.id, {"type": n.type, "rpc_urls": n.rpc_urls_list, "explorer_url": n.explorer_url}, upsert=True
                )
            return Ok(len(networks))
        except Exception as e:
            return Err(e)

    def get_networks(self) -> list[Network]:
        # TODO: cache it
        return self.db.network.find({}, "_id")

    def get_network(self, id: str) -> Network:
        # TODO: cache it
        return self.db.network.get(id)
