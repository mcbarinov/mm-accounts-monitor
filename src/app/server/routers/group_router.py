from bson import ObjectId
from fastapi import APIRouter
from starlette.responses import PlainTextResponse

from app.core.db import Group
from app.core.services.group_service import ProcessAccountBalancesResult, ProcessAccountNamingsResult
from app.server.deps import CoreDep

router = APIRouter(prefix="/api/groups", tags=["group"])


@router.get("/")
async def get_all_groups(core: CoreDep) -> list[Group]:
    return await core.db.group.find({}, "_id")


@router.delete("/")
async def delete_all_groups(core: CoreDep) -> None:
    for group in await core.db.group.find({}, "_id"):
        await core.group_service.delete_group(group.id)


@router.get("/export", response_class=PlainTextResponse)
async def export_groups(core: CoreDep) -> str:
    return await core.group_service.export_as_toml()


@router.get("/{id}")
async def get_group(core: CoreDep, id: ObjectId) -> Group:
    return await core.db.group.get(id)


@router.delete("/{id}")
async def delete_group(core: CoreDep, id: ObjectId) -> None:
    await core.group_service.delete_group(ObjectId(id))


@router.post("/{id}/process-account-balances")
async def process_account_balances(core: CoreDep, id: ObjectId) -> ProcessAccountBalancesResult:
    return await core.group_service.process_account_balances(ObjectId(id))


@router.post("/{id}/process-account-names")
async def process_account_names(core: CoreDep, id: ObjectId) -> ProcessAccountNamingsResult:
    return await core.group_service.process_account_names(ObjectId(id))
