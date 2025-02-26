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


class Db(BaseDb):
    network: MongoCollection[str, Network]
    coin: MongoCollection[str, Coin]
