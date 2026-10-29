from __future__ import annotations

from pathlib import Path

import mammoth

from ..i18n import Msg
from . import text_fidelity
from .html_to_md import html_to_markdown
from .images import CONTENT_TYPE_EXT, NON_WEB_EXT, assets_dir_name, relink_images
from .models import ConversionError, ConversionOptions, ConversionResult

# Word stores built-in style names in English in styles.xml; Turkish names are
# also mapped for custom styles created in a Turkish-language Word.
STYLE_MAP = """
p[style-name='Title'] => h1:fresh
p[style-name='Konu Başlığı'] => h1:fresh
p[style-name='Subtitle'] => h2:fresh
p[style-name='Alt Konu Başlığı'] => h2:fresh
p[style-name='Başlık 1'] => h1:fresh
p[style-name='Başlık 2'] => h2:fresh
p[style-name='Başlık 3'] => h3:fresh
p[style-name='Başlık 4'] => h4:fresh
p[style-name='Başlık 5'] => h5:fresh
p[style-name='Başlık 6'] => h6:fresh
p[style-name='Quote'] => blockquote > p:fresh
p[style-name='Intense Quote'] => blockquote > p:fresh
p[style-name='Alıntı'] => blockquote > p:fresh
p[style-name='Code'] => pre:separator('\\n')
p[style-name='HTML Preformatted'] => pre:separator('\\n')
r[style-name='Code Char'] => code
r[style-name='HTML Code'] => code
u => u
strike => s
"""


def convert_docx(path: Path, opts: ConversionOptions, workdir: Path) -> ConversionResult:
    assets = workdir / assets_dir_name(path.stem)
    warnings: list[Msg] = []
    counter = 0

    def save_image(image):
        nonlocal counter
        counter += 1
        ext = CONTENT_TYPE_EXT.get((image.content_type or "").lower(), "bin")
        if ext in NON_WEB_EXT:
            warnings.append(Msg("warn.non_web_image", n=counter, ext=ext.upper()))
        name = f"image_{counter:03d}.{ext}"
        assets.mkdir(parents=True, exist_ok=True)
        with image.open() as src:
            (assets / name).write_bytes(src.read())
        return {"src": f"{assets.name}/{name}"}

    convert_image = mammoth.images.img_element(save_image) if opts.extract_images else _drop_image

    try:
        with path.open("rb") as f:
            result = mammoth.convert_to_html(f, style_map=STYLE_MAP, convert_image=convert_image)
    except Exception as exc:  # corrupt / encrypted file
        raise ConversionError(Msg("err.docx_read", exc=exc)) from exc

    for msg in result.messages:
        if msg.type == "warning" and "Unrecognised" not in msg.message:
            warnings.append(Msg("raw", text=msg.message))
    unknown_styles = sorted({
        m.message.split(": ", 1)[-1].split(" (Style ID")[0]
        for m in result.messages
        if "Unrecognised" in m.message and "List" not in m.message
    })
    if unknown_styles:
        warnings.append(Msg("warn.unmapped_styles", styles=", ".join(unknown_styles)))

    markdown = relink_images(html_to_markdown(result.value), assets)
    markdown = text_fidelity.finalize(markdown, nbsp_to_space=opts.nbsp_to_space)
    warnings += text_fidelity.suspicious_char_report(markdown)
    return ConversionResult(path, markdown, workdir, assets, warnings)


def _drop_image(image):
    return []
