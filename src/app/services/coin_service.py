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
                self.db.coin.set(
                    f"{c.network}__{c.symbol}", {"decimals": c.decimals, "token": c.token, "notes": c.notes}, upsert=True
                )
            return Ok(len(coins))
        except Exception as e:
            return Err(e)

    def export_as_toml(self) -> str:
        coins = []
        for c in self.db.coin.find({}, "_id"):
            coin = remove_empty_keys(
                {"network": c.network, "symbol": c.symbol, "decimals": c.decimals, "token": c.token, "notes": c.notes}
            )
            coins.append(coin)
        return toml.dumps({"coins": coins})


def remove_empty_keys(d: dict[str, object]) -> dict[str, object]:
    return {k: v for k, v in d.items() if v}
