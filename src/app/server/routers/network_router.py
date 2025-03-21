from fastapi import APIRouter

from app.core.db import Network
from app.server.deps import CoreDep

router = APIRouter(prefix="/api/networks", tags=["network"])


@router.get("/")
def get_all_networks(core: CoreDep) -> list[Network]:
    return core.network_service.get_networks()


@router.get("/{id}")
def get_network(core: CoreDep, id: str) -> Network:
    return core.network_service.get_network(id)


@router.delete("/{id}")
def delete_network(core: CoreDep, id: str) -> None:
    # TODO: delete all coins associated with this network
    core.db.network.delete(id)


@router.post("/{id}/check-next-network-balances")
def check_next_network_balances(core: CoreDep, id: str) -> int:
    return core.balance_service.check_next_network_balances(id)
