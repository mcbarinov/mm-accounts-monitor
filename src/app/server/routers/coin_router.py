from fastapi import APIRouter
from mm_base6 import cbv
from mm_mongo import MongoDeleteResult

from app.core.db import Coin
from app.server.deps import View

router = APIRouter(prefix="/api/coins", tags=["coin"])


@cbv(router)
class CBV(View):
    @router.get("/{id}")
    async def get_coin(self, id: str) -> Coin:
        return self.core.coin_service.get_coin(id)

    @router.delete("/{id}")
    async def delete_coin(self, id: str) -> MongoDeleteResult:
        return await self.core.coin_service.delete(id)
