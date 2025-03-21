from datetime import datetime

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

    def to_db(self) -> Coin:
        return Coin(id=f"{self.network}__{self.symbol}", decimals=self.decimals, token=self.token, notes=self.notes)


class OldestCheckedTimeStats(BaseModel):
    class Stats(BaseModel):
        oldest_checked_time: datetime | None
        never_checked_count: int  # how many accounts have never been checked

    coins: dict[str, Stats]  # coin_id -> Stats


class CoinService(AppService):
    def __init__(self, base_params: AppServiceParams, network_service: NetworkService) -> None:
        super().__init__(base_params)
        self.network_service = network_service

    def import_from_toml(self, toml_str: str) -> Result[int]:
        try:
            count = 0
            coins = [ImportCoinItem(**n) for n in tomlkit.loads(toml_str)["coins"]]  # type:ignore[arg-type,union-attr]
            for c in coins:
                if not self.db.coin.exists({"_id": f"{c.network}__{c.symbol}"}):
                    self.db.coin.insert_one(c.to_db())
                    count += 1
            return Ok(count)
        except Exception as e:
            return Err(e)

    def export_as_toml(self) -> str:
        coins = []
        for c in self.db.coin.find({}, "_id"):
            coin = replace_empty_dict_values(
                {"network": c.network, "symbol": c.symbol, "decimals": c.decimals, "token": c.token, "notes": c.notes}
            )
            coins.append(coin)
        return toml_dumps({"coins": coins})

    def get_coins(self) -> list[Coin]:
        # TODO: cache it
        return self.db.coin.find({}, "_id")

    def get_coins_by_network_type(self) -> dict[NetworkType, list[Coin]]:
        coins = self.get_coins()
        coins_by_network_type: dict[NetworkType, list[Coin]] = {n: [] for n in NetworkType}
        for c in coins:
            network_type = self.network_service.get_network(c.network).type
            coins_by_network_type[network_type].append(c)
        return coins_by_network_type

    def get_coin(self, id: str) -> Coin:
        # TODO: cache it
        return self.db.coin.get(id)

    def delete(self, id: str) -> MongoDeleteResult:
        self.db.group_balances.delete_many({"coin": id})
        self.db.account_balance.delete_many({"coin": id})
        self.db.group.update_many({"coins": id}, {"$pull": {"coins": id}})
        # TODO: remove from cache
        return self.db.coin.delete(id)

    def calc_oldest_checked_time(self) -> OldestCheckedTimeStats:
        result = OldestCheckedTimeStats(coins={})
        for coin in self.get_coins():
            oldest_checked_time = None
            never_checked_count = self.db.account_balance.count({"coin": coin.id, "checked_at": None})
            if never_checked_count == 0:
                balance = self.db.account_balance.find_one({"coin": coin.id}, "checked_at")
                if balance:
                    oldest_checked_time = balance.checked_at
            result.coins[coin.id] = OldestCheckedTimeStats.Stats(
                oldest_checked_time=oldest_checked_time, never_checked_count=never_checked_count
            )

        return result
