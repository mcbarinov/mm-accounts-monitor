from dataclasses import dataclass
from decimal import Decimal
from typing import cast

import pydash
import tomlkit
from bson import ObjectId
from mm_base6 import UserError
from mm_mongo import MongoDeleteResult
from mm_std import async_synchronized, toml_dumps, toml_loads
from pydantic import BaseModel

from app.core.constants import Naming, NetworkType
from app.core.db import AccountBalance, AccountNaming, Coin, Group, GroupBalance, GroupNaming, Network
from app.core.services.coin_service import CoinService
from app.core.services.network_service import NetworkService
from app.core.types_ import AppService, AppServiceParams


@dataclass
class ProcessAccountBalancesResult:
    inserted: int
    deleted_by_coin: int
    deleted_by_account: int


@dataclass
class ProcessAccountNamingsResult:
    inserted: int
    deleted_by_coin: int
    deleted_by_account: int


class ImportGroupItem(BaseModel):
    name: str
    network_type: NetworkType
    notes: str
    coins: str
    namings: str
    accounts: str


class GroupAccountsInfo(BaseModel):
    networks: list[Network]
    coins_map: dict[str, Coin]  # coin_id -> Coin
    coins_sum: dict[str, Decimal]  # coin -> sum(balance)
    balances: dict[str, dict[str, Decimal]]  # coin -> account -> balance
    namings: dict[Naming, dict[str, str]]  # naming -> account -> name

    def get_balance(self, coin: str, account: str) -> Decimal | None:
        return self.balances.get(coin, {}).get(account, None)

    def get_name(self, naming: Naming, account: str) -> str | None:
        return self.namings.get(naming, {}).get(account, None)

    def explorer_address(self, coin: str, account: str) -> str:
        network_id = coin.split("__")[0]
        network = next(n for n in self.networks if n.id == network_id)
        if not network:
            return "__network_not_found__"
        return network.explorer_address + account


class GroupService(AppService):
    def __init__(self, base_params: AppServiceParams, network_service: NetworkService, coin_service: CoinService) -> None:
        super().__init__(base_params)
        self.network_service = network_service
        self.coin_service = coin_service

    async def get_group_accounts_info(self, group_id: ObjectId) -> GroupAccountsInfo:
        balances: dict[str, dict[str, Decimal]] = {}
        for gb in await self.db.group_balance.find({"group_id": group_id}):
            balances[gb.coin] = gb.balances

        coins_sum: dict[str, Decimal] = {}
        for coin, coin_balances in balances.items():
            if coin_balances:
                coins_sum[coin] = cast(Decimal, sum(coin_balances.values()))

        namings: dict[Naming, dict[str, str]] = {}
        for gn in await self.db.group_naming.find({"group_id": group_id}):
            namings[gn.naming] = gn.names

        return GroupAccountsInfo(
            coins_sum=coins_sum,
            balances=balances,
            namings=namings,
            coins_map=await self.coin_service.get_coins_map(),
            networks=await self.network_service.get_networks(),
        )

    async def create_group(
        self, name: str, network_type: NetworkType, notes: str, namings: list[Naming], coin_ids: list[str]
    ) -> Group:
        # Check if the namings are consistent with the network type
        for naming in namings:
            if not naming.is_consistent(network_type):
                raise UserError(f"Naming {naming.name} is not consistent with the network type {network_type.value}")
        # Check if the coins are consistent with the network type
        for coin_id in coin_ids:
            coin = await self.coin_service.get_coin(coin_id)
            network = await self.network_service.get_network(coin.network)
            if network.type != network_type:
                raise UserError(f"Coin {coin_id} is not consistent with the network type {network_type.value}")
        new_group = Group(id=ObjectId(), name=name, network_type=network_type, notes=notes, coins=coin_ids, namings=namings)
        await self.db.group.insert_one(new_group)
        await self.process_account_namings(new_group.id)
        await self.process_account_balances(new_group.id)
        return new_group

    async def export_as_toml(self) -> str:
        groups = []
        for group in await self.db.group.find({}):
            obj = group.model_dump()
            obj = pydash.omit(obj, "_id")
            obj["coins"] = tomlkit.string("\n".join(obj["coins"]), multiline=True)
            obj["namings"] = tomlkit.string("\n".join(obj["namings"]), multiline=True)
            obj["accounts"] = tomlkit.string("\n".join(obj["accounts"]), multiline=True)
            groups.append(obj)

        return toml_dumps({"groups": groups})

    @async_synchronized
    async def import_from_toml(self, toml: str) -> int:
        known_coins = [c.id for c in await self.coin_service.get_coins()]
        count = 0
        for data in toml_loads(toml)["groups"]:  # type:ignore[union-attr]
            group = ImportGroupItem(**cast(dict[str, object], data))
            if not await self.db.group.exists({"name": group.name}):
                coin_ids = [c.strip() for c in group.coins.split("\n") if c.strip()]
                unknown_coins = [c for c in coin_ids if c not in known_coins]
                if unknown_coins:
                    raise ValueError(f"unknown coins: {unknown_coins}")
                namings = [Naming(n.strip()) for n in group.namings.split("\n") if n.strip()]
                accounts = [a.strip() for a in group.accounts.split("\n") if a.strip()]
                if group.network_type.lowercase_address():
                    accounts = [a.lower() for a in accounts]
                new_group = Group(
                    id=ObjectId(),
                    name=group.name,
                    network_type=group.network_type,
                    notes=group.notes,
                    coins=coin_ids,
                    namings=namings,
                    accounts=accounts,
                )
                await self.db.group.insert_one(new_group)
                await self.process_account_namings(new_group.id)
                await self.process_account_balances(new_group.id)
                count += 1
        return count

    async def delete_group(self, id: ObjectId) -> MongoDeleteResult:
        await self.db.account_balance.delete_many({"group_id": id})
        await self.db.account_naming.delete_many({"group_id": id})
        await self.db.group_naming.delete_many({"group_id": id})
        await self.db.group_balance.delete_many({"group_id": id})
        return await self.db.group.delete(id)

    async def update_accounts(self, id: ObjectId, accounts: list[str]) -> None:
        group = await self.db.group.get(id)
        if group.network_type.lowercase_address():
            accounts = [a.lower() for a in accounts]
        await self.db.group.set(id, {"accounts": accounts})
        await self.process_account_balances(id)
        await self.process_account_namings(id)

    async def update_coins(self, id: ObjectId, coin_ids: list[str]) -> None:
        group = await self.db.group.get(id)
        # Check if the coins are consistent with the network type
        for coin_id in coin_ids:
            coin = await self.coin_service.get_coin(coin_id)
            network = await self.network_service.get_network(coin.network)
            if network.type != group.network_type:
                raise UserError(f"Coin {coin_id} is not from the network {group.network_type.value}")
        await self.db.group.set(id, {"coins": coin_ids})
        await self.process_account_balances(id)

    @async_synchronized
    async def process_account_namings(self, id: ObjectId) -> ProcessAccountNamingsResult:
        """Create account namings for all namings and accounts in the group.
        And delete docs for namings and accounts that are not in the group."""
        group = await self.db.group.get(id)
        inserted = 0
        for naming in group.namings:
            if not await self.db.group_naming.exists({"group_id": id, "naming": naming}):
                await self.db.group_naming.insert_one(GroupNaming(id=ObjectId(), group_id=id, naming=naming))

            known_accounts = [
                a["account"]
                async for a in self.db.account_naming.collection.find(
                    {"group_id": id, "naming": naming}, {"_id": False, "account": True}
                )
            ]
            new_accounts = [account for account in group.accounts if account not in known_accounts]
            if len(new_accounts) > 0:
                insert_many = [
                    AccountNaming(id=ObjectId(), group_id=id, network=naming.network, naming=naming, account=account)
                    for account in new_accounts
                ]
                await self.db.account_naming.insert_many(insert_many)
                inserted += len(new_accounts)
        deleted_by_naming = (
            await self.db.account_naming.delete_many({"group_id": id, "naming": {"$nin": group.namings}})
        ).deleted_count
        deleted_by_account = (
            await self.db.account_naming.delete_many({"group_id": id, "account": {"$nin": group.accounts}})
        ).deleted_count
        return ProcessAccountNamingsResult(inserted, deleted_by_naming, deleted_by_account)

    @async_synchronized
    async def process_account_balances(self, id: ObjectId) -> ProcessAccountBalancesResult:
        """Create account balances for all coins and accounts in the group.
        And delete balances for coins and accounts that are not in the group."""
        group = await self.db.group.get(id)
        inserted = 0
        for coin in group.coins:
            if not await self.db.group_balance.exists({"group_id": id, "coin": coin}):
                await self.db.group_balance.insert_one(GroupBalance(id=ObjectId(), group_id=id, coin=coin))
            known_accounts = [
                a["account"]
                async for a in self.db.account_balance.collection.find(
                    {"group_id": id, "coin": coin}, {"_id": False, "account": True}
                )
            ]
            new_accounts = [account for account in group.accounts if account not in known_accounts]
            if len(new_accounts) > 0:
                insert_many = [
                    AccountBalance(id=ObjectId(), group_id=id, network=coin.split("__")[0], coin=coin, account=account)
                    for account in new_accounts
                ]
                await self.db.account_balance.insert_many(insert_many)
                inserted += len(new_accounts)
        deleted_by_coin = (
            await self.db.account_balance.delete_many({"group_id": id, "coin": {"$nin": group.coins}})
        ).deleted_count
        deleted_by_account = (
            await self.db.account_balance.delete_many({"group_id": id, "account": {"$nin": group.accounts}})
        ).deleted_count

        return ProcessAccountBalancesResult(
            inserted=inserted, deleted_by_coin=deleted_by_coin, deleted_by_account=deleted_by_account
        )
