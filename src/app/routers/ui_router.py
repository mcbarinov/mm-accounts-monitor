from litestar import Controller, Router, get
from litestar.response import Template
from mm_base3 import render_html


class UIController(Controller):
    path = "/"

    @get()
    def index(self) -> Template:
        return render_html("index.j2")


ui_router = Router(path="/", route_handlers=[UIController])
