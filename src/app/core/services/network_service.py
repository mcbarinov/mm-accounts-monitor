from __future__ import annotations

from datetime import datetime

import pydash
from mm_crypto_utils import Network
from mm_std import async_synchronized, http_request, utc_now
from pydantic import BaseModel

from app.core.db import RpcUrl
from app.core.types_ import AppService, AppServiceParams


class NetworkCheckStats(BaseModel):
    class Stats(BaseModel):
        oldest_checked_time: datetime | None
        never_checked_count: int  # how many accounts have never been checked
        all_count: int  # how many accounts in this network

    networks: dict[Network, Stats]  # network_id -> Stats


class NetworkService(AppService):
    def __init__(self, base_params: AppServiceParams) -> None:
        super().__init__(base_params)
        self.rpc_urls: dict[Network, list[str]] = {}

    @async_synchronized
    async def update_mm_node_checker(self) -> dict[str, list[str]] | None:
        if not self.dynamic_configs.mm_node_checker:
            return None

        res = await http_request(self.dynamic_configs.mm_node_checker)
        json_body = res.parse_json_body()
        if res.status_code == 200 and not res.is_err() and json_body:
            for key in json_body:
                if not isinstance(json_body[key], list):
                    return None
            self.dynamic_values.mm_node_checker = json_body
            self.dynamic_values.mm_node_checker_updated_at = utc_now()
            return json_body  # type:ignore[no-any-return]

    async def calc_network_check_stats(self) -> NetworkCheckStats:
        result = NetworkCheckStats(networks={})
        for network in Network:
            oldest_checked_time = None
            never_checked_count = await self.db.account_balance.count({"network": network, "checked_at": None})
            if never_checked_count == 0:
                account_balance = await self.db.account_balance.find_one({"network": network}, "checked_at")
                if account_balance:
                    oldest_checked_time = account_balance.checked_at
            result.networks[network] = NetworkCheckStats.Stats(
                oldest_checked_time=oldest_checked_time,
                never_checked_count=never_checked_count,
                all_count=await self.db.account_balance.count({"network": network}),
            )
        return result

    def get_rpc_urls(self, network: Network) -> list[str]:
        if self.dynamic_values.mm_node_checker:
            return self.dynamic_values.mm_node_checker.get(network.value) or []
        return []

    @async_synchronized
    async def add_rpc_url(self, network: Network, url: str) -> None:
        if not await self.db.rpc_url.exists({"_id": network.value}):
            await self.db.rpc_url.insert_one(RpcUrl(id=network.value, urls=[]))
        rpc_url = await self.db.rpc_url.get(network.value)
        urls = pydash.uniq([*rpc_url.urls, url.strip()])
        await self.db.rpc_url.set(network.value, {"urls": urls})
        await self.load_rpc_urls_from_db()

    @async_synchronized
    async def delete_rpc_url(self, network: Network, url: str) -> None:
        if not await self.db.rpc_url.exists({"_id": network.value}):
            return
        rpc_url = await self.db.rpc_url.get(network.value)
        urls = pydash.uniq([u for u in rpc_url.urls if u != url.strip()])
        await self.db.rpc_url.set(network.value, {"urls": urls})
        await self.load_rpc_urls_from_db()

    @async_synchronized
    async def load_rpc_urls_from_db(self) -> dict[Network, list[str]]:
        self.rpc_urls = {}
        for rpc_url in await self.db.rpc_url.find({}, "id,urls"):
            self.rpc_urls[Network(rpc_url.id)] = rpc_url.urls
        return self.rpc_urls
