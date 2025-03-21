from markupsafe import Markup
from mm_base6 import CustomJinja

from app.core.core import Core


async def header_info(_core: Core) -> Markup:
    info = ""
    return Markup(info)  # noqa: S704 # nosec


async def footer_info(_core: Core) -> Markup:
    info = ""
    return Markup(info)  # noqa: S704 # nosec


def network_from_coin_id(coin: str) -> str:
    return coin.split("__")[0]


def symbol_from_coin_id(coin: str) -> str:
    return coin.split("__")[1]


custom_jinja = CustomJinja(
    header_info=header_info,
    header_info_new_line=False,
    footer_info=footer_info,
    filters={"network_from_coin_id": network_from_coin_id, "symbol_from_coin_id": symbol_from_coin_id},
)
