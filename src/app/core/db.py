from datetime import datetime
from decimal import Decimal

import pydash
from bson import ObjectId
from mm_base6 import BaseDb
from mm_mongo import AsyncMongoCollection, MongoModel
from mm_std import utc_now
from pydantic import Field, field_validator

from app.core.constants import Naming, NetworkType


class Network(MongoModel[str]):
    type: NetworkType
    rpc_urls: list[str] = Field(default_factory=list)
    explorer_address: str
    explorer_token: str

    __collection__: str = "network"

    @field_validator("id", mode="before")
    def ensure_lowercase_id(cls, v: str) -> str:
        if isinstance(v, str):
            return v.lower()
        return v


class Coin(MongoModel[str]):  # id = {network}__{symbol}, lowercased
    network: str  # network.id
    symbol: str  # symbol is not lowercase
    token: str | None = None  # if None, then it's a native coin
    decimals: int
    notes: str = ""

    __collection__: str = "coin"

    @field_validator("id", mode="before")
    def ensure_lowercase_id(cls, v: str) -> str:
        if isinstance(v, str):
            return v.lower()
        return v


class Group(MongoModel[ObjectId]):
    name: str
    network_type: NetworkType
    notes: str
    coins: list[str]  # Coin.id
    namings: list[Naming] = Field(default_factory=list)
    accounts: list[str] = Field(default_factory=list)

    __collection__: str = "group"

    def get_coin_networks(self) -> list[str]:
        networks = [c.split("__")[0] for c in self.coins]
        return pydash.sort(pydash.uniq(networks))

    def get_coin_symbols(self, network: str) -> list[str]:
        symbols = [c.split("__")[1] for c in self.coins if c.startswith(f"{network}__")]
        return pydash.sort(pydash.uniq(symbols))


class AccountBalance(MongoModel[ObjectId]):
    group_id: ObjectId
    account: str
    network: str  # network_id
    coin: str
    balance: Decimal | None = None
    balance_raw: int | None = None
    checked_at: datetime | None = None

    __collection__: str = "account_balance"
    __indexes__ = ["group_id", "account", "coin", "network", "checked_at"]


class AccountNaming(MongoModel[ObjectId]):
    group_id: ObjectId
    account: str
    network: str  # network_id
    naming: Naming
    name: str | None = None  # domains, ids, etc..
    checked_at: datetime | None = None

    __collection__: str = "account_naming"
    __indexes__ = ["group_id", "account", "network", "naming", "checked_at"]


class GroupBalance(MongoModel[ObjectId]):
    group_id: ObjectId
    coin: str
    balances: dict[str, Decimal] = Field(default_factory=dict)  # account -> balance

    __collection__: str = "group_balance"
    __indexes__ = ["!group_id,coin", "group_id"]


class GroupNaming(MongoModel[ObjectId]):
    group_id: ObjectId
    naming: Naming
    names: dict[str, str] = Field(default_factory=dict)  # account -> name, name can be empty string

    __collection__: str = "group_naming"
    __indexes__ = ["!group_id,naming", "group_id"]


class NamingProblem(MongoModel[ObjectId]):
    network: str
    naming: Naming
    account: str
    message: str
    created_at: datetime = Field(default_factory=utc_now)

    __collection__: str = "naming_problem"
    __indexes__ = ["network", "naming", "account", "created_at"]


class RpcMonitoring(MongoModel[ObjectId]):
    network: str
    rpc_url: str
    success: bool
    account: str
    response_time: float
    coin: str | None = None
    proxy: str | None = None
    error: str | None = None
    data: object | None = None
    created_at: datetime = Field(default_factory=utc_now)

    __collection__: str = "rpc_monitoring"
    __indexes__ = ["network", "rpc_url", "account", "coin", "proxy", "success", "created_at"]


class Db(BaseDb):
    network: AsyncMongoCollection[str, Network]
    coin: AsyncMongoCollection[str, Coin]
    group: AsyncMongoCollection[ObjectId, Group]
    account_balance: AsyncMongoCollection[ObjectId, AccountBalance]
    account_naming: AsyncMongoCollection[ObjectId, AccountNaming]
    group_balance: AsyncMongoCollection[ObjectId, GroupBalance]
    group_naming: AsyncMongoCollection[ObjectId, GroupNaming]
    naming_problem: AsyncMongoCollection[ObjectId, NamingProblem]
    rpc_monitoring: AsyncMongoCollection[ObjectId, RpcMonitoring]
