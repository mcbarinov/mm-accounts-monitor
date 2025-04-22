from bson import ObjectId
from fastapi import APIRouter
from mm_base6 import cbv
from mm_std import Result

from app.core.db import AccountBalance
from app.server.deps import View

router = APIRouter(prefix="/api/account-balances", tags=["account-balance"])


@cbv(router)
class CBV(View):
    @router.get("/{id}")
    async def get_account_balance(self, id: ObjectId) -> AccountBalance:
        return await self.core.db.account_balance.get(id)

    @router.post("/{id}/check")
    async def check_account_balance(self, id: ObjectId) -> Result[int]:
        return await self.core.balance_service.check_account_balance(id)
