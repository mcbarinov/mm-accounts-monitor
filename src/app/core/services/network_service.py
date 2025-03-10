from __future__ import annotations

import tomlkit
from mm_std import Err, Ok, Result
from pydantic import BaseModel

from app.core.constants import NetworkType
from app.core.db import Network
from app.core.types_ import AppService, AppServiceParams


class ImportNetworkItem(BaseModel):
    id: str
    type: NetworkType
    rpc_urls: str
    explorer_url: str

    @property
    def rpc_urls_list(self) -> list[str]:
        return [u.strip() for u in self.rpc_urls.splitlines() if u.strip()]

    def to_db(self) -> Network:
        return Network(id=self.id, type=self.type, rpc_urls=self.rpc_urls_list, explorer_url=self.explorer_url)


class NetworkService(AppService):
    def __init__(self, base_params: AppServiceParams) -> None:
        super().__init__(base_params)

    def export_as_toml(self) -> str:
        doc = tomlkit.document()
        networks = tomlkit.aot()
        for n in self.db.network.find({}, "_id"):
            network = tomlkit.table()
            network.add("id", n.id)
            network.add("type", n.type)
            network.add("rpc_urls", tomlkit.string("\n".join(n.rpc_urls), multiline=True))
            network.add("explorer_url", n.explorer_url)
            networks.append(network)

        doc.add("networks", networks)
        return tomlkit.dumps(doc)

    def import_from_toml(self, toml_str: str) -> Result[int]:
        try:
            networks = [ImportNetworkItem(**n) for n in tomlkit.loads(toml_str)["networks"]]  # type:ignore[arg-type,union-attr]
            count = 0
            for n in networks:
                if not self.db.network.exists({"_id": n.id}):
                    self.db.network.insert_one(n.to_db())
                    count += 1
            return Ok(count)
        except Exception as e:
            return Err(e)

    def get_networks(self) -> list[Network]:
        # TODO: cache it
        return self.db.network.find({}, "_id")

    def get_network(self, id: str) -> Network:
        # TODO: cache it
        return self.db.network.get(id)
