from markupsafe import Markup
from mm_base6 import JinjaConfig
from mm_cryptocurrency import Network, NetworkType

from app.core.types import AppCore


async def header_info(_core: AppCore) -> Markup:
    info = ""
    return Markup(info)  # noqa: S704 # nosec


async def footer_info(_core: AppCore) -> Markup:
    info = ""
    return Markup(info)  # noqa: S704 # nosec


jinja_config = JinjaConfig(
    header_info=header_info,
    header_info_new_line=False,
    footer_info=footer_info,
    globals={"networks": list(Network), "network_types": list(NetworkType)},
)
