from dataclasses import dataclass

from bson import ObjectId
from mm_base3 import BaseService
from mm_base3.base_service import BaseServiceParams
from mm_std import synchronized

from app.config import AppConfig, DConfigSettings, DValueSettings
from app.db import AccountBalance, Db, GroupBalances


@dataclass
class ProcessAccountBalancesResult:
    inserted: int
    deleted_by_coin: int
    deleted_by_account: int


class GroupService(BaseService[AppConfig, DConfigSettings, DValueSettings, Db]):
    def __init__(self, base_params: BaseServiceParams[AppConfig, DConfigSettings, DValueSettings, Db]) -> None:
        super().__init__(base_params)

    def update_accounts(self, id: ObjectId, accounts: list[str]) -> None:
        # TODO: process balances, etc...
        self.db.group.set(id, {"accounts": accounts})

    def update_coins(self, id: ObjectId, coins: list[str]) -> None:
        # TODO: process balances, etc...
        self.db.group.set(id, {"coins": coins})

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
                self.db.account_balance.insert_one(AccountBalance(id=ObjectId(), group_id=id, coin=coin, account=account))
                inserted += 1

        deleted_by_coin = self.db.account_balance.delete_many({"group_id": id, "coin": {"$nin": group.coins}}).deleted_count
        deleted_by_account = self.db.account_balance.delete_many(
            {"group_id": id, "account": {"$nin": group.accounts}}
        ).deleted_count

        return ProcessAccountBalancesResult(
            inserted=inserted, deleted_by_coin=deleted_by_coin, deleted_by_account=deleted_by_account
        )
