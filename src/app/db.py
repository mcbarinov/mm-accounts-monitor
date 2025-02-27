from datetime import datetime
from decimal import Decimal
from enum import Enum, unique

import pydash
from bson import ObjectId
from mm_base3.base_db import BaseDb
from mm_mongo import MongoCollection, MongoModel
from pydantic import Field


@unique
class NetworkType(str, Enum):
    EVM = "evm"
    SOLANA = "solana"
    APTOS = "aptos"


class Network(MongoModel[str]):
    __collection__: str = "network"
    type: NetworkType
    rpc_urls: list[str] = Field(default_factory=list)
    explorer_url: str


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


# class GroupBalances(MongoModel[ObjectId]):
#     group_id: ObjectId
#     balances: dict[str, dict[str, Decimal]] = Field(default_factory=dict)  # account-> symbol -> balance
#
#     __collection__: str = "group_balances"


class AccountBalance(MongoModel[ObjectId]):
    group_id: ObjectId
    account: str
    coin: str
    balance: Decimal | None = None
    balance_raw: int | None = None
    checked_at: datetime | None = None

    __collection__: str = "account_balance"
    __indexes__ = ["group_id", "account", "coin", "checked_at"]


class Db(BaseDb):
    network: MongoCollection[str, Network]
    coin: MongoCollection[str, Coin]
    group: MongoCollection[ObjectId, Group]
    account_balance: MongoCollection[ObjectId, AccountBalance]
    # group_balances: MongoCollection[ObjectId, GroupBalances]
