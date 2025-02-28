from mm_base3 import BaseService
from mm_base3.base_service import BaseServiceParams

from app.config import AppConfig, DConfigSettings, DValueSettings
from app.db import Db

AppBaseService = BaseService[AppConfig, DConfigSettings, DValueSettings, Db]
AppBaseServiceParams = BaseServiceParams[AppConfig, DConfigSettings, DValueSettings, Db]
