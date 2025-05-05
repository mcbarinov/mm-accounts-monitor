from typing import Annotated

from bson import ObjectId
from fastapi import APIRouter, Body
from mm_base6 import cbv
from starlette.responses import PlainTextResponse

from app.core.constants import Naming
from app.core.db import Group
from app.core.services.group_service import ProcessAccountBalancesResult, ProcessAccountNamingsResult
from app.server.deps import View

router = APIRouter(prefix="/api/groups", tags=["group"])


@cbv(router)
class CBV(View):
    @router.get("/")
    async def get_all_groups(self) -> list[Group]:
        return await self.core.db.group.find({}, "_id")

    @router.delete("/")
    async def delete_all_groups(self) -> None:
        for group in await self.core.db.group.find({}, "_id"):
            await self.core.group_service.delete_group(group.id)

    @router.get("/export", response_class=PlainTextResponse)
    async def export_groups(self) -> str:
        return await self.core.group_service.export_as_toml()

    @router.get("/{id}")
    async def get_group(self, id: ObjectId) -> Group:
        return await self.core.db.group.get(id)

    @router.delete("/{id}")
    async def delete_group(self, id: ObjectId) -> None:
        await self.core.group_service.delete_group(ObjectId(id))

    @router.post("/{id}/coins")
    async def add_coin_to_group(self, id: ObjectId, coin_id: Annotated[str, Body(..., embed=True)]) -> None:
        return await self.core.group_service.add_coin(id, coin_id)

    @router.post("/{id}/namings")
    async def add_namings_to_group(self, id: ObjectId) -> None:
        pass

    @router.delete("/{id}/coins/{coin_id}")
    async def remove_coin_from_group(self, id: ObjectId, coin_id: str) -> None:
        pass

    @router.delete("/{id}/namings/{naming}")
    async def remove_naming_from_group(self, id: ObjectId, naming: Naming) -> None:
        pass

    @router.post("/{id}/process-account-balances")
    async def process_account_balances(self, id: ObjectId) -> ProcessAccountBalancesResult:
        return await self.core.group_service.process_account_balances(ObjectId(id))

    @router.post("/{id}/process-account-names")
    async def process_account_names(self, id: ObjectId) -> ProcessAccountNamingsResult:
        return await self.core.group_service.process_account_names(ObjectId(id))

    @router.post("/{id}/reset-group-balances")
    async def reset_group_balances(self, id: ObjectId) -> None:
        await self.core.group_service.reset_group_balances(ObjectId(id))
