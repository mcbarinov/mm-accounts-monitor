from __future__ import annotations

from enum import Enum, unique


@unique
class NetworkType(str, Enum):
    EVM = "evm"
    SOLANA = "solana"
    APTOS = "aptos"
    STARKNET = "starknet"


@unique
class Naming(str, Enum):
    ENS = "ens"
    ANS = "ans"
    STARKNET_ID = "starknet_id"

    @property
    def network(self) -> str:
        match self:
            case Naming.ENS:
                return "ethereum"
            case Naming.ANS:
                return "aptos"
            case Naming.STARKNET_ID:
                return "starknet"
        raise ValueError("no network found")

    def is_consistent(self, network_type: NetworkType) -> bool:
        match self:
            case Naming.ENS:
                return network_type == NetworkType.EVM
            case Naming.ANS:
                return network_type == NetworkType.APTOS
            case Naming.STARKNET_ID:
                return network_type == NetworkType.STARKNET
            case _:
                return False
