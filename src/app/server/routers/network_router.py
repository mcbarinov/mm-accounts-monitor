from fastapi import APIRouter
from mm_base6 import cbv

from app.core.db import Network
from app.server.deps import View

router = APIRouter(prefix="/api/networks", tags=["network"])


@cbv(router)
class CBV(View):
    @router.get("/")
    async def get_all_networks(self) -> list[Network]:
        return self.core.network_service.get_networks()

    @router.get("/{id}")
    async def get_network(self, id: str) -> Network:
        return self.core.network_service.get_network(id)

    @router.delete("/{id}")
    async def delete_network(self, id: str) -> None:
        return await self.core.network_service.delete_network(id)

    @router.post("/{id}/check-next-network-balances")
    async def check_next_network_balances(self, id: str) -> int | None:
        return await self.core.balance_service.check_next_network(id)
