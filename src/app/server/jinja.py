from typing import Any, override

from mm_base6 import BaseJinjaConfig
from mm_web3 import Network, NetworkType

from app.core.types import AppCore


class JinjaConfig(BaseJinjaConfig[AppCore]):
    @override
    def get_globals(self) -> dict[str, Any]:
        return {"networks": list(Network), "network_types": list(NetworkType)}
