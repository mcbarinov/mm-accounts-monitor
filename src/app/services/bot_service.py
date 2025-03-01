from mm_std import hr, synchronized, utc_now

from app.types_ import AppBaseService, AppBaseServiceParams


class BotService(AppBaseService):
    def __init__(self, base_params: AppBaseServiceParams) -> None:
        super().__init__(base_params)

    @synchronized
    def update_proxies(self) -> int:
        res = hr(self.dconfig.proxies_url)
        if res.is_error():
            self.dlog("update_proxies", {"error": res.error})
            return -1
        proxies = res.body.strip().splitlines()
        proxies = [p.strip() for p in proxies if p.strip()]
        self.dvalue.proxies = proxies
        self.dvalue.proxies_updated_at = utc_now()
        return len(proxies)

    def toggle_check_balances(self) -> None:
        self.dvalue.check_balances = not self.dvalue.check_balances

    def toggle_check_namings(self) -> None:
        self.dvalue.check_namings = not self.dvalue.check_namings
