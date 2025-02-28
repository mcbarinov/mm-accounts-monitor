from enum import Enum, unique


@unique
class Naming(str, Enum):
    ENS = "ens"
    ANS = "ans"
    STARKNET_ID = "starknet_id"
