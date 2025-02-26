from __future__ import annotations

import tomlkit
from mm_base3 import BaseService
from mm_base3.base_service import BaseServiceParams

from app.config import AppConfig, DConfigSettings, DValueSettings
from app.db import Db


class NetworkService(BaseService[AppConfig, DConfigSettings, DValueSettings, Db]):
    def __init__(self, base_params: BaseServiceParams[AppConfig, DConfigSettings, DValueSettings, Db]) -> None:
        super().__init__(base_params)

    def export_as_toml(self) -> str:
        doc = tomlkit.document()
        networks = []
        for n in self.db.network.find({}, "_id"):
            network = tomlkit.table()
            network.add("id", n.id)
            network.add("rpc_urls", tomlkit.string("\n".join(n.rpc_urls), multiline=True))
            network.add("explorer_url", n.explorer_url)
            networks.append(network)

        doc.add("networks", networks)
        return tomlkit.dumps(doc)

    def import_from_toml(self, toml_str: str) -> None:
        pass
