from markupsafe import Markup
from mm_base3 import CustomJinja

from app.core import Core


def header_info(_core: Core) -> Markup:
    info = "<span style='color: red'></span>"
    return Markup(info)  # nosec: B704


def footer_info(_core: Core) -> Markup:
    info = ""
    return Markup(info)  # nosec: B704


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
