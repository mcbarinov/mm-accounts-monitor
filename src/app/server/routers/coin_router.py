from fastapi import APIRouter
from mm_mongo import MongoDeleteResult

from app.core.db import Coin
from app.server.deps import CoreDep

router = APIRouter(prefix="/api/coins", tags=["coin"])


@router.get("/{id}")
def get_coin(core: CoreDep, id: str) -> Coin:
    return core.coin_service.get_coin(id)


@router.delete("/{id}")
def delete_coin(core: CoreDep, id: str) -> MongoDeleteResult:
    return core.coin_service.delete(id)
