import pydash
from bson import ObjectId
from mm_base3.base_db import BaseDb
from mm_mongo import MongoCollection, MongoModel
from pydantic import Field


class Network(MongoModel[str]):
    rpc_urls: list[str] = Field(default_factory=list)
    explorer_url: str

    __collection__: str = "network"


class Coin(MongoModel[str]):  # id = {network}__{symbol}
    token: str | None = None  # if None, then it's a native coin
    decimals: int
    notes: str = ""

    @property
    def network(self) -> str:
        return self.id.split("__")[0]

    @property
    def symbol(self) -> str:
        return self.id.split("__")[1]

    __collection__: str = "coin"


class Group(MongoModel[ObjectId]):
    name: str
    notes: str
    coins: list[str]  # Coin.id
    accounts: list[str] = Field(default_factory=list)

    __collection__: str = "group"

    def get_networks(self) -> list[str]:
        networks = [c.split("__")[0] for c in self.coins]
        return pydash.sort(pydash.uniq(networks))

    def get_symbols(self, network: str) -> list[str]:
        symbols = [c.split("__")[1] for c in self.coins if c.startswith(f"{network}__")]
        return pydash.sort(pydash.uniq(symbols))


class Db(BaseDb):
    network: MongoCollection[str, Network]
    coin: MongoCollection[str, Coin]
    group: MongoCollection[ObjectId, Group]
