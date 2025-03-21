from dataclasses import dataclass
from decimal import Decimal
from typing import cast

from bson import ObjectId
from mm_base6 import UserError
from mm_mongo import MongoDeleteResult
from mm_std import async_synchronized
from pydantic import BaseModel

from app.core.constants import Naming, NetworkType
from app.core.db import AccountBalance, AccountNaming, Group, GroupBalance, GroupNaming
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


class GroupAccountsInfo(BaseModel):
    coins_sum: dict[str, Decimal]  # coin -> sum(balance)
    balances: dict[str, dict[str, Decimal]]  # coin -> account -> balance
    namings: dict[Naming, dict[str, str]]  # naming -> account -> name

    def get_balance(self, coin: str, account: str) -> Decimal | None:
        return self.balances.get(coin, {}).get(account, None)

    def get_name(self, naming: Naming, account: str) -> str | None:
        return self.namings.get(naming, {}).get(account, None)


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

        return GroupAccountsInfo(coins_sum=coins_sum, balances=balances, namings=namings)

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

    async def delete_group(self, id: ObjectId) -> MongoDeleteResult:
        await self.db.account_balance.delete_many({"group_id": id})
        await self.db.account_naming.delete_many({"group_id": id})
        await self.db.group_naming.delete_many({"group_id": id})
        await self.db.group_balance.delete_many({"group_id": id})
        return await self.db.group.delete(id)

    async def update_accounts(self, id: ObjectId, accounts: list[str]) -> None:
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
            for account in group.accounts:
                if await self.db.account_naming.exists({"group_id": id, "naming": naming, "account": account}):
                    continue
                network = naming.network
                await self.db.account_naming.insert_one(
                    AccountNaming(id=ObjectId(), group_id=id, network=network, naming=naming, account=account)
                )
                inserted += 1

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
            for account in group.accounts:
                if await self.db.account_balance.exists({"group_id": id, "coin": coin, "account": account}):
                    continue
                network = coin.split("__")[0]
                await self.db.account_balance.insert_one(
                    AccountBalance(id=ObjectId(), group_id=id, network=network, coin=coin, account=account)
                )
                inserted += 1

        deleted_by_coin = (
            await self.db.account_balance.delete_many({"group_id": id, "coin": {"$nin": group.coins}})
        ).deleted_count
        deleted_by_account = (
            await self.db.account_balance.delete_many({"group_id": id, "account": {"$nin": group.accounts}})
        ).deleted_count

        return ProcessAccountBalancesResult(
            inserted=inserted, deleted_by_coin=deleted_by_coin, deleted_by_account=deleted_by_account
        )
