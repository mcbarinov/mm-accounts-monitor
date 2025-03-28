from bson import ObjectId
from fastapi import APIRouter
from mm_std import Result

from app.core.db import AccountName
from app.server.deps import CoreDep

router = APIRouter(prefix="/api/account-namings", tags=["account-naming"])


@router.get("/{id}")
async def get_account_name(core: CoreDep, id: ObjectId) -> AccountName:
    return await core.db.account_name.get(id)


@router.post("/{id}/check")
async def check_account_name(core: CoreDep, id: ObjectId) -> Result[str | None]:
    return await core.name_service.check_account_name(id)
