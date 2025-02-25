from litestar import Router, get


@get()
def test() -> dict[str, str]:
    return {"test": "test"}


api_router = Router(path="/api", route_handlers=[test])
