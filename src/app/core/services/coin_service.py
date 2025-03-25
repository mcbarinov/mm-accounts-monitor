from datetime import datetime

import pydash
import tomlkit
from mm_mongo import MongoDeleteResult
from mm_std import Err, Ok, Result, replace_empty_dict_values, toml_dumps
from pydantic import BaseModel

from app.core.constants import NetworkType
from app.core.db import Coin
from app.core.services.network_service import NetworkService
from app.core.types_ import AppService, AppServiceParams


class ImportCoinItem(BaseModel):
    network: str
    symbol: str
    decimals: int
    token: str | None = None
    notes: str = ""

    @property
    def id(self) -> str:
        return f"{self.network}__{self.symbol}".lower()

    def to_db(self) -> Coin:
        return Coin(
            id=self.id, network=self.network, symbol=self.symbol, decimals=self.decimals, token=self.token, notes=self.notes
        )


class OldestCheckedTimeStats(BaseModel):
    class Stats(BaseModel):
        oldest_checked_time: datetime | None
        never_checked_count: int  # how many accounts have never been checked

    coins: dict[str, Stats]  # coin_id -> Stats


class CoinService(AppService):
    def __init__(self, base_params: AppServiceParams, network_service: NetworkService) -> None:
        super().__init__(base_params)
        self.network_service = network_service

    async def import_from_toml(self, toml_str: str) -> Result[int]:
        try:
            count = 0
            coins = [ImportCoinItem(**n) for n in tomlkit.loads(toml_str)["coins"]]  # type:ignore[arg-type,union-attr]
            for c in coins:
                if not await self.db.coin.exists({"_id": c.id}):
                    await self.db.coin.insert_one(c.to_db())
                    count += 1
            return Ok(count)
        except Exception as e:
            return Err(e)

    async def export_as_toml(self) -> str:
        coins = []
        for c in await self.db.coin.find({}, "_id"):
            coin = replace_empty_dict_values(
                {"network": c.network, "symbol": c.symbol, "decimals": c.decimals, "token": c.token, "notes": c.notes}
            )
            coins.append(coin)
        return toml_dumps({"coins": coins})

    async def get_coins(self) -> list[Coin]:
        # TODO: cache it
        return await self.db.coin.find({}, "_id")

    async def get_coins_map(self) -> dict[str, Coin]:
        # TODO: cache it
        coins = await self.get_coins()
        return {c.id: c for c in coins}

    async def explorer_token_map(self) -> dict[str, str]:  # coin_id -> explorer_token
        result: dict[str, str] = {}
        networks = await self.network_service.get_networks()
        for coin in await self.get_coins():
            network = pydash.find(networks, lambda n: n.id == coin.network)  # noqa: B023
            if network is None:
                raise RuntimeError(f"Network not found for coin {coin.id}")
            explorer_token = network.explorer_token
            if coin.token is not None:
                explorer_token += coin.token
            else:
                explorer_token = explorer_token.removesuffix("token/")
            result[coin.id] = explorer_token

        return result

    async def get_coins_by_network_type(self) -> dict[NetworkType, list[Coin]]:
        coins = await self.get_coins()
        coins_by_network_type: dict[NetworkType, list[Coin]] = {n: [] for n in NetworkType}
        for c in coins:
            network_type = (await self.network_service.get_network(c.network)).type
            coins_by_network_type[network_type].append(c)
        return coins_by_network_type

    async def get_coin(self, id: str) -> Coin:
        # TODO: cache it
        return await self.db.coin.get(id)

    async def delete(self, id: str) -> MongoDeleteResult:
        await self.db.group_balance.delete_many({"coin": id})
        await self.db.account_balance.delete_many({"coin": id})
        await self.db.group.update_many({"coins": id}, {"$pull": {"coins": id}})
        # TODO: remove from cache
        return await self.db.coin.delete(id)

    async def calc_oldest_checked_time(self) -> OldestCheckedTimeStats:
        result = OldestCheckedTimeStats(coins={})
        for coin in await self.get_coins():
            oldest_checked_time = None
            never_checked_count = await self.db.account_balance.count({"coin": coin.id, "checked_at": None})
            if never_checked_count == 0:
                balance = await self.db.account_balance.find_one({"coin": coin.id}, "checked_at")
                if balance:
                    oldest_checked_time = balance.checked_at
            result.coins[coin.id] = OldestCheckedTimeStats.Stats(
                oldest_checked_time=oldest_checked_time, never_checked_count=never_checked_count
            )

        return result
