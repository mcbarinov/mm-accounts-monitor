from markupsafe import Markup
from mm_base6 import CustomJinja

from app.core.core import Core


async def header_info(_core: Core) -> Markup:
    info = ""
    return Markup(info)  # noqa: S704 # nosec


async def footer_info(_core: Core) -> Markup:
    info = ""
    return Markup(info)  # noqa: S704 # nosec


custom_jinja = CustomJinja(
    header_info=header_info,
    header_info_new_line=False,
    footer_info=footer_info,
)
