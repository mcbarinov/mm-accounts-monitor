import tomlkit
from mm_std import Err, Ok, Result, toml_dumps
from pydantic import BaseModel

from app.core.db import Coin
from app.core.types_ import AppService, AppServiceParams


class ImportCoinItem(BaseModel):
    network: str
    symbol: str
    decimals: int
    token: str | None = None
    notes: str = ""

    def to_db(self) -> Coin:
        return Coin(id=f"{self.network}__{self.symbol}", decimals=self.decimals, token=self.token, notes=self.notes)


class CoinService(AppService):
    def __init__(self, base_params: AppServiceParams) -> None:
        super().__init__(base_params)

    def import_from_toml(self, toml_str: str) -> Result[int]:
        try:
            count = 0
            coins = [ImportCoinItem(**n) for n in tomlkit.loads(toml_str)["coins"]]  # type:ignore[arg-type,union-attr]
            for c in coins:
                if not self.db.coin.exists({"_id": f"{c.network}__{c.symbol}"}):
                    self.db.coin.insert_one(c.to_db())
                    count += 1
            return Ok(count)
        except Exception as e:
            return Err(e)

    def export_as_toml(self) -> str:
        coins = []
        for c in self.db.coin.find({}, "_id"):
            coin = remove_empty_keys(
                {"network": c.network, "symbol": c.symbol, "decimals": c.decimals, "token": c.token, "notes": c.notes}
            )
            coins.append(coin)
        return toml_dumps({"coins": coins})

    def get_coins(self) -> list[Coin]:
        # TODO: cache it
        return self.db.coin.find({}, "_id")

    def get_coin(self, id: str) -> Coin:
        # TODO: cache it
        return self.db.coin.get(id)


def remove_empty_keys(d: dict[str, object]) -> dict[str, object]:
    return {k: v for k, v in d.items() if v}
