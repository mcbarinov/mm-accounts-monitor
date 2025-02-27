from bson import ObjectId
from mm_base3 import BaseService
from mm_base3.base_service import BaseServiceParams

from app.config import AppConfig, DConfigSettings, DValueSettings
from app.db import Db


class GroupService(BaseService[AppConfig, DConfigSettings, DValueSettings, Db]):
    def __init__(self, base_params: BaseServiceParams[AppConfig, DConfigSettings, DValueSettings, Db]) -> None:
        super().__init__(base_params)

    def update_accounts(self, id: ObjectId, accounts: list[str]) -> None:
        # TODO: process balances, etc...
        self.db.group.set(id, {"accounts": accounts})

    def update_coins(self, id: ObjectId, coins: list[str]) -> None:
        # TODO: process balances, etc...
        self.db.group.set(id, {"coins": coins})
