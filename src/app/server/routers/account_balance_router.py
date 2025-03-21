from bson import ObjectId
from fastapi import APIRouter
from mm_std import Result

from app.core.db import AccountBalance
from app.server.deps import CoreDep

router = APIRouter(prefix="/api/account-balances", tags=["account-balance"])


@router.get("/{id}")
async def get_account_balance(core: CoreDep, id: ObjectId) -> AccountBalance:
    return await core.db.account_balance.get(id)


@router.post("/{id}/check")
async def check_account_balance(core: CoreDep, id: ObjectId) -> Result[int]:
    return await core.balance_service.check_account_balance(id)
