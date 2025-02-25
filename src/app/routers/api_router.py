from litestar import Controller, Router, post

from app.core import Core


class BotController(Controller):
    path = "bot"
    tags = ["bot"]

    @post("update-proxies")
    def update_proxies(self, core: Core) -> int:
        return core.bot_service.update_proxies()


api_router = Router(path="/api", route_handlers=[BotController])
