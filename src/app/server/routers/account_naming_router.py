from bson import ObjectId
from fastapi import APIRouter
from mm_std import Result

from app.core.db import AccountNaming
from app.server.deps import CoreDep

router = APIRouter(prefix="/api/account-namings", tags=["account-naming"])


@router.get("/{id}")
async def get_account_naming(core: CoreDep, id: ObjectId) -> AccountNaming:
    return await core.db.account_naming.get(id)


@router.post("/{id}/check")
async def check_account_naming(core: CoreDep, id: ObjectId) -> Result[str | None]:
    return await core.naming_service.check_account_naming(id)
