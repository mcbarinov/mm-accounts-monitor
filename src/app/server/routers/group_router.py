from bson import ObjectId
from fastapi import APIRouter

from app.core.db import Group
from app.core.services.group_service import ProcessAccountBalancesResult, ProcessAccountNamingsResult
from app.server.deps import CoreDep

router = APIRouter(prefix="/api/groups", tags=["group"])


@router.get("/")
def get_all_groups(core: CoreDep) -> list[Group]:
    return core.db.group.find({}, "_id")


@router.get("/{id}")
def get_group(core: CoreDep, id: ObjectId) -> Group:
    return core.db.group.get(id)


@router.delete("/{id}")
def delete_group(core: CoreDep, id: ObjectId) -> None:
    core.group_service.delete_group(ObjectId(id))


@router.post("/{id}/process-account-balances")
def process_account_balances(core: CoreDep, id: ObjectId) -> ProcessAccountBalancesResult:
    return core.group_service.process_account_balances(ObjectId(id))


@router.post("/{id}/process-account-namings")
def process_account_namings(core: CoreDep, id: ObjectId) -> ProcessAccountNamingsResult:
    return core.group_service.process_account_namings(ObjectId(id))
