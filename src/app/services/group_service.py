from dataclasses import dataclass
from decimal import Decimal
from typing import cast

from bson import ObjectId
from mm_base3.errors import UserError
from mm_std import synchronized
from pydantic import BaseModel

from app.db import AccountBalance, Group, GroupBalances, NetworkType
from app.services.coin_service import CoinService
from app.services.network_service import NetworkService
from app.types_ import AppBaseService, AppBaseServiceParams


@dataclass
class ProcessAccountBalancesResult:
    inserted: int
    deleted_by_coin: int
    deleted_by_account: int


class GroupAccountsInfo(BaseModel):
    coins_sum: dict[str, Decimal]  # coin -> sum(balance)
    balances: dict[str, dict[str, Decimal]]  # coin -> account -> balance

    def get_balance(self, coin: str, account: str) -> Decimal | None:
        return self.balances.get(coin, {}).get(account, None)


class GroupService(AppBaseService):
    def __init__(self, base_params: AppBaseServiceParams, network_service: NetworkService, coin_service: CoinService) -> None:
        super().__init__(base_params)
        self.network_service = network_service
        self.coin_service = coin_service

    def get_group_accounts_info(self, group_id: ObjectId) -> GroupAccountsInfo:
        balances: dict[str, dict[str, Decimal]] = {}
        for gb in self.db.group_balances.find({"group_id": group_id}):
            balances[gb.coin] = gb.balances

        coins_sum: dict[str, Decimal] = {}
        for coin, coin_balances in balances.items():
            if coin_balances:
                coins_sum[coin] = cast(Decimal, sum(coin_balances.values()))

        return GroupAccountsInfo(coins_sum=coins_sum, balances=balances)

    def create_group(self, name: str, network_type: NetworkType, notes: str, coin_ids: list[str]) -> Group:
        # check coins are correlated with the network type
        for coin_id in coin_ids:
            coin = self.coin_service.get_coin(coin_id)
            network = self.network_service.get_network(coin.network)
            if network.type != network_type:
                raise UserError(f"Coin {coin_id} is not from the network {network_type.value}")
        return Group(id=ObjectId(), name=name, network_type=network_type, notes=notes, coins=coin_ids)

    def update_accounts(self, id: ObjectId, accounts: list[str]) -> None:
        self.db.group.set(id, {"accounts": accounts})
        self.process_account_balances(id)

    def update_coins(self, id: ObjectId, coin_ids: list[str]) -> None:
        group = self.db.group.get(id)
        # check coins are correlated with the network type
        for coin_id in coin_ids:
            coin = self.coin_service.get_coin(coin_id)
            network = self.network_service.get_network(coin.network)
            if network.type != group.network_type:
                raise UserError(f"Coin {coin_id} is not from the network {group.network_type.value}")
        self.db.group.set(id, {"coins": coin_ids})
        self.process_account_balances(id)

    @synchronized
    def process_account_balances(self, id: ObjectId) -> ProcessAccountBalancesResult:
        """Create account balances for all coins and accounts in the group.
        And delete balances for coins and accounts that are not in the group."""
        group = self.db.group.get(id)
        inserted = 0
        for coin in group.coins:
            if not self.db.group_balances.exists({"group_id": id, "coin": coin}):
                self.db.group_balances.insert_one(GroupBalances(id=ObjectId(), group_id=id, coin=coin))
            for account in group.accounts:
                if self.db.account_balance.exists({"group_id": id, "coin": coin, "account": account}):
                    continue
                network = coin.split("__")[0]
                self.db.account_balance.insert_one(
                    AccountBalance(id=ObjectId(), group_id=id, network=network, coin=coin, account=account)
                )
                inserted += 1

        deleted_by_coin = self.db.account_balance.delete_many({"group_id": id, "coin": {"$nin": group.coins}}).deleted_count
        deleted_by_account = self.db.account_balance.delete_many(
            {"group_id": id, "account": {"$nin": group.accounts}}
        ).deleted_count

        return ProcessAccountBalancesResult(
            inserted=inserted, deleted_by_coin=deleted_by_coin, deleted_by_account=deleted_by_account
        )
