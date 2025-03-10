from app.core.types_ import AppService, AppServiceParams


class BotService(AppService):
    def __init__(self, base_params: AppServiceParams) -> None:
        super().__init__(base_params)

    def toggle_check_balances(self) -> None:
        self.dvalue.check_balances = not self.dvalue.check_balances

    def toggle_check_namings(self) -> None:
        self.dvalue.check_namings = not self.dvalue.check_namings
