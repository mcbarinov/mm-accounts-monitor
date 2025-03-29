from bson import ObjectId
from fastapi import APIRouter
from mm_base6 import cbv
from mm_mongo import MongoDeleteResult

from app.core.db import RpcMonitoring
from app.server.deps import View

router = APIRouter(prefix="/api/rpc-monitoring", tags=["rpc_monitoring"])


@cbv(router)
class CBV(View):
    @router.get("/{id}")
    async def get_rpc_monitoring(self, id: ObjectId) -> RpcMonitoring:
        return await self.core.db.rpc_monitoring.get(id)

    @router.delete("/")
    async def delete_all(self) -> MongoDeleteResult:
        return await self.core.db.rpc_monitoring.delete_many({})
