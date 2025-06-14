from mm_base6 import BaseService

from app.core.types import AppCore


class BotService(BaseService):
    core: AppCore

    def toggle_check_balances(self) -> None:
        self.core.dynamic_values.check_balances = not self.core.dynamic_values.check_balances

    def toggle_check_namings(self) -> None:
        self.core.dynamic_values.check_namings = not self.core.dynamic_values.check_namings
