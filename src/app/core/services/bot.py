from app.core.types_ import AppService, AppServiceParams


class BotService(AppService):
    def __init__(self, base_params: AppServiceParams) -> None:
        super().__init__(base_params)

    def toggle_check_balances(self) -> None:
        self.dynamic_values.check_balances = not self.dynamic_values.check_balances

    def toggle_check_namings(self) -> None:
        self.dynamic_values.check_namings = not self.dynamic_values.check_namings
