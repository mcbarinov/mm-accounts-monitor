from markupsafe import Markup
from mm_base3 import CustomJinja

from app.core import Core


def header_info(_core: Core) -> Markup:
    info = "<span style='color: red'></span>"
    return Markup(info)  # nosec: B704


def footer_info(_core: Core) -> Markup:
    info = ""
    return Markup(info)  # nosec: B704


custom_jinja = CustomJinja(
    header_info=header_info,
    header_info_new_line=False,
    footer_info=footer_info,
)
