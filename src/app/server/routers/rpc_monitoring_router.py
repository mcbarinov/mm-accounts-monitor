from bson import ObjectId
from fastapi import APIRouter
from mm_mongo import MongoDeleteResult

from app.core.db import RpcMonitoring
from app.server.deps import CoreDep

router = APIRouter(prefix="/api/rpc-monitoring", tags=["rpc_monitoring"])


@router.get("/{id}")
def get_rpc_monitoring(core: CoreDep, id: ObjectId) -> RpcMonitoring:
    return core.db.rpc_monitoring.get(id)


@router.delete("/")
def delete_all(core: CoreDep) -> MongoDeleteResult:
    return core.db.rpc_monitoring.delete_many({})
