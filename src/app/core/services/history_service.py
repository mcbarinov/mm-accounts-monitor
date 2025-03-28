from decimal import Decimal
from typing import cast

from bson import ObjectId
from mm_mongo import MongoInsertOneResult
from pydantic import BaseModel

from app.core.db import History
from app.core.services.coin_service import CoinService
from app.core.services.group_service import GroupAccountsInfo
from app.core.services.network_service import NetworkService
from app.core.types_ import AppService, AppServiceParams


class HistoryAccountsInfo(BaseModel):
    pass


class HistoryService(AppService):
    def __init__(self, base_params: AppServiceParams, network_service: NetworkService, coin_service: CoinService) -> None:
        super().__init__(base_params)
        self.network_service = network_service
        self.coin_service = coin_service

    async def create(self, group_id: ObjectId) -> MongoInsertOneResult:
        group = await self.db.group.get(group_id)
        group_balances = await self.db.group_balance.find({"group_id": group_id})
        balances = {b.coin: b.balances for b in group_balances}
        group_namings = await self.db.group_naming.find({"group_id": group_id})
        names = {n.naming: n.names for n in group_namings}
        return await self.db.history.insert_one(History(id=ObjectId(), group=group, balances=balances, names=names))

    async def get_history_group_accounts_info(self, history_id: ObjectId) -> GroupAccountsInfo:
        history = await self.db.history.get(history_id)

        balances = history.balances

        coins_sum: dict[str, Decimal] = {}
        for coin, coin_balances in balances.items():
            if coin_balances:
                coins_sum[coin] = cast(Decimal, sum(coin_balances.values()))

        return GroupAccountsInfo(
            coins_sum=coins_sum,
            balances=balances,
            namings=history.names,
            coins_map=await self.coin_service.get_coins_map(),
            networks=await self.network_service.get_networks(),
        )
