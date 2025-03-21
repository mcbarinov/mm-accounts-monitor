from bson import ObjectId
from fastapi import APIRouter

from app.core.db import Group
from app.core.services.group_service import ProcessAccountBalancesResult, ProcessAccountNamingsResult
from app.server.deps import CoreDep

router = APIRouter(prefix="/api/groups", tags=["group"])


@router.get("/")
async def get_all_groups(core: CoreDep) -> list[Group]:
    return await core.db.group.find({}, "_id")


@router.get("/{id}")
async def get_group(core: CoreDep, id: ObjectId) -> Group:
    return await core.db.group.get(id)


@router.delete("/{id}")
async def delete_group(core: CoreDep, id: ObjectId) -> None:
    await core.group_service.delete_group(ObjectId(id))


@router.post("/{id}/process-account-balances")
async def process_account_balances(core: CoreDep, id: ObjectId) -> ProcessAccountBalancesResult:
    return await core.group_service.process_account_balances(ObjectId(id))


@router.post("/{id}/process-account-namings")
async def process_account_namings(core: CoreDep, id: ObjectId) -> ProcessAccountNamingsResult:
    return await core.group_service.process_account_namings(ObjectId(id))
