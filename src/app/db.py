from bson import ObjectId
from mm_base3.base_db import BaseDb
from mm_mongo import MongoCollection, MongoModel
from pydantic import Field


class Network(MongoModel[str]):
    rpc_urls: list[str] = Field(default_factory=list)
    explorer_url: str

    __collection__: str = "network"


class Coin(MongoModel[ObjectId]):
    network: str  # Network.id
    symbol: str
    token: str | None = None  # if None, then it's a native coin
    decimals: int
    notes: str = ""

    __collection__: str = "coin"
    __indexes__ = ["network", "!network,symbol"]


class Db(BaseDb):
    network: MongoCollection[str, Network]
    coin: MongoCollection[ObjectId, Coin]
