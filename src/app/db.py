from datetime import datetime
from decimal import Decimal

import pydash
from bson import ObjectId
from mm_base3.base_db import BaseDb
from mm_mongo import MongoCollection, MongoModel
from pydantic import Field

from app.constants import Naming, NetworkType


class Network(MongoModel[str]):
    type: NetworkType
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
    names: list[str] | None = None  # domains, ids, etc..
    checked_at: datetime | None = None

    __collection__: str = "account_naming"
    __indexes__ = ["group_id", "account", "network", "naming", "checked_at"]


class GroupBalances(MongoModel[ObjectId]):
    group_id: ObjectId
    coin: str
    balances: dict[str, Decimal] = Field(default_factory=dict)  # account -> balance

    __collection__: str = "group_balances"
    __indexes__ = ["!group_id,coin", "group_id"]


class GroupNamings(MongoModel[ObjectId]):
    group_id: ObjectId
    naming: Naming
    names: dict[str, list[str]] = Field(default_factory=dict)  # account -> [values]

    __collection__: str = "group_namings"
    __indexes__ = ["!group_id,naming", "group_id"]


class Db(BaseDb):
    network: MongoCollection[str, Network]
    coin: MongoCollection[str, Coin]
    group: MongoCollection[ObjectId, Group]
    account_balance: MongoCollection[ObjectId, AccountBalance]
    account_naming: MongoCollection[ObjectId, AccountNaming]
    group_balances: MongoCollection[ObjectId, GroupBalances]
    group_namings: MongoCollection[ObjectId, GroupNamings]
