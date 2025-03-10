from fastapi import APIRouter

from app.server.deps import CoreDep

router = APIRouter(prefix="/api/bot", tags=["bot"])


@router.post("/toggle-check-balances")
def toggle_check_balances(core: CoreDep) -> None:
    core.bot_service.toggle_check_balances()


@router.post("/toggle-check-namings")
def toggle_check_namings(core: CoreDep) -> None:
    core.bot_service.toggle_check_namings()
