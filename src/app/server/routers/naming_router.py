from datetime import datetime

from fastapi import APIRouter

from app.core.constants import Naming
from app.server.deps import CoreDep

router = APIRouter(prefix="/api/namings", tags=["namings"])


@router.get("/oldest-checked-time")
def get_oldest_checked_time(core: CoreDep) -> dict[Naming, datetime | None]:
    return core.naming_service.calc_oldest_checked_time()
