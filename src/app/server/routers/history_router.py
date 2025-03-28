from bson import ObjectId
from fastapi import APIRouter
from mm_mongo import MongoDeleteResult

from app.server.deps import CoreDep

router = APIRouter(prefix="/api/history", tags=["history"])


@router.post("/")
async def create_history(core: CoreDep, group_id: ObjectId) -> None:
    await core.history_service.create(group_id)


@router.delete("/{id}")
async def delete_history(core: CoreDep, id: ObjectId) -> MongoDeleteResult:
    return await core.db.history.delete(id)
