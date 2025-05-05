from enum import Enum, unique

from mm_crypto_utils import NetworkType


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

    @property
    def network_type(self) -> NetworkType:
        match self:
            case Naming.ENS:
                return NetworkType.EVM
            case Naming.ANS:
                return NetworkType.APTOS
            case Naming.STARKNET_ID:
                return NetworkType.STARKNET
        raise ValueError("no network type found")

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
