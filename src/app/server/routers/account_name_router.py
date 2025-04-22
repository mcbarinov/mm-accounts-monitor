from bson import ObjectId
from fastapi import APIRouter
from mm_base6 import cbv
from mm_std import Result

from app.core.db import AccountName
from app.server.deps import View

router = APIRouter(prefix="/api/account-namings", tags=["account-naming"])


@cbv(router)
class CBV(View):
    @router.get("/{id}")
    async def get_account_name(self, id: ObjectId) -> AccountName:
        return await self.core.db.account_name.get(id)

    @router.post("/{id}/check")
    async def check_account_name(self, id: ObjectId) -> Result[str | None]:
        return await self.core.name_service.check_account_name(id)
