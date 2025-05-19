from fastapi import APIRouter
from mm_base6 import cbv

from app.server.deps import View

router = APIRouter(prefix="/api/bot", tags=["bot"])


@cbv(router)
class CBV(View):
    @router.post("/toggle-check-balances")
    async def toggle_check_balances(self) -> None:
        self.core.services.bot.toggle_check_balances()

    @router.post("/toggle-check-namings")
    async def toggle_check_namings(self) -> None:
        self.core.services.bot.toggle_check_namings()
