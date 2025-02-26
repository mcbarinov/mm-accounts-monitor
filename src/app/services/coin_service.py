import pydash
import toml
import tomlkit
from mm_base3 import BaseService
from mm_base3.base_service import BaseServiceParams
from mm_std import Err, Ok, Result
from pydantic import BaseModel

from app.config import AppConfig, DConfigSettings, DValueSettings
from app.db import Db


class ImportCoinItem(BaseModel):
    network: str
    symbol: str
    decimals: int
    token: str | None = None
    notes: str = ""


class CoinService(BaseService[AppConfig, DConfigSettings, DValueSettings, Db]):
    def __init__(self, base_params: BaseServiceParams[AppConfig, DConfigSettings, DValueSettings, Db]) -> None:
        super().__init__(base_params)

    def import_from_toml(self, toml_str: str) -> Result[int]:
        try:
            coins = [ImportCoinItem(**n) for n in tomlkit.loads(toml_str)["coins"]]  # type:ignore[arg-type,union-attr]
            for c in coins:
                self.db.coin.update_one(
                    {"network": c.network, "symbol": c.symbol},
                    {"$set": {"decimals": c.decimals, "token": c.token, "notes": c.notes}},
                    upsert=True,
                )
            return Ok(len(coins))
        except Exception as e:
            return Err(e)

    def export_as_toml(self) -> str:
        coins = [pydash.omit(c.model_dump(), "_id") for c in self.db.coin.find({}, "network,symbol")]
        return toml.dumps({"coins": coins})
