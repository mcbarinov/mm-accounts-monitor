from __future__ import annotations

from datetime import datetime

import pydash
import tomlkit
from mm_std import Err, Ok, Result, async_synchronized
from pydantic import BaseModel

from app.core.constants import NetworkType
from app.core.db import Network
from app.core.types_ import AppService, AppServiceParams


class ImportNetworkItem(BaseModel):
    id: str
    type: NetworkType
    rpc_urls: str
    explorer_address: str
    explorer_token: str

    @property
    def rpc_urls_list(self) -> list[str]:
        return [u.strip() for u in self.rpc_urls.splitlines() if u.strip()]

    def to_db(self) -> Network:
        return Network(
            id=self.id,
            type=self.type,
            rpc_urls=self.rpc_urls_list,
            explorer_address=self.explorer_address,
            explorer_token=self.explorer_token,
        )


class OldestCheckedTimeStats(BaseModel):
    class Stats(BaseModel):
        oldest_checked_time: datetime | None
        never_checked_count: int  # how many accounts have never been checked

    networks: dict[str, Stats]  # network_id -> Stats


class NetworkService(AppService):
    def __init__(self, base_params: AppServiceParams) -> None:
        super().__init__(base_params)
        self.networks: list[Network] = []  # load on core.start

    def export_as_toml(self) -> str:
        doc = tomlkit.document()
        networks = tomlkit.aot()
        for n in self.networks:
            network = tomlkit.table()
            network.add("id", n.id)
            network.add("type", n.type)
            network.add("rpc_urls", tomlkit.string("\n".join(n.rpc_urls), multiline=True))
            network.add("explorer_address", n.explorer_address)
            network.add("explorer_token", n.explorer_token)
            networks.append(network)

        doc.add("networks", networks)
        return tomlkit.dumps(doc)

    async def import_from_toml(self, toml_str: str) -> Result[int]:
        try:
            networks = [ImportNetworkItem(**n) for n in tomlkit.loads(toml_str)["networks"]]  # type:ignore[arg-type,union-attr]
            for n in networks:
                await self.db.network.set(n.id, n.to_db().model_dump(), upsert=True)
            await self.load_networks_from_db()
            return Ok(len(networks))
        except Exception as e:
            await self.load_networks_from_db()
            return Err(e)

    async def load_networks_from_db(self) -> None:
        self.networks = await self.db.network.find({}, "_id")

    def get_networks(self) -> list[Network]:
        return self.networks

    async def delete_network(self, id: str) -> None:
        # TODO: delete all coins associated with this network
        raise NotImplementedError

    @async_synchronized
    async def add_network(self, network: Network) -> None:
        await self.db.network.insert_one(network)
        await self.load_networks_from_db()

    def get_network(self, id: str) -> Network:
        res = pydash.find(self.networks, lambda n: n.id == id)
        if res is None:
            raise ValueError(f"Network {id} not found")
        return res

    async def calc_oldest_checked_time(self) -> OldestCheckedTimeStats:
        result = OldestCheckedTimeStats(networks={})
        for network in self.get_networks():
            oldest_checked_time = None
            never_checked_count = await self.db.account_balance.count({"network": network.id, "checked_at": None})
            if never_checked_count == 0:
                account_balance = await self.db.account_balance.find_one({"network": network.id}, "checked_at")
                if account_balance:
                    oldest_checked_time = account_balance.checked_at
            result.networks[network.id] = OldestCheckedTimeStats.Stats(
                oldest_checked_time=oldest_checked_time, never_checked_count=never_checked_count
            )
        return result
