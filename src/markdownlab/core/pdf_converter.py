from __future__ import annotations

from pathlib import Path

import pymupdf
import pymupdf4llm
from pymupdf4llm.ocr import OCRMode

from ..i18n import Msg
from . import ocr, text_fidelity
from .images import assets_dir_name, relink_images
from .models import ConversionError, ConversionOptions, ConversionResult


def convert_pdf(path: Path, opts: ConversionOptions, workdir: Path) -> ConversionResult:
    assets = workdir / assets_dir_name(path.stem)
    warnings: list[Msg] = []

    ocr_fn, ocr_lang = None, None
    if opts.ocr_enabled or opts.force_ocr:
        ocr_fn, ocr_lang, ocr_warnings = ocr.get_ocr_function(opts.tessdata_dir, opts.ocr_language)
        warnings += ocr_warnings

    try:
        doc = pymupdf.open(path)
    except Exception as exc:
        raise ConversionError(Msg("err.pdf_open", exc=exc)) from exc
    if doc.needs_pass:
        doc.close()
        raise ConversionError(Msg("err.pdf_password"))

    kwargs = dict(
        write_images=opts.extract_images,
        image_path=str(assets),
        dpi=opts.image_dpi,
        header=not opts.remove_headers_footers,
        footer=not opts.remove_headers_footers,
        use_ocr=OCRMode.SELECT_KEEP_OLD if ocr_fn else OCRMode.NEVER,
        force_ocr=bool(opts.force_ocr and ocr_fn),
        ocr_dpi=opts.ocr_dpi,
        show_progress=False,
    )
    if ocr_fn:
        kwargs.update(ocr_function=ocr_fn, ocr_language=ocr_lang)
    if opts.pdf_tables_as_html:
        kwargs["table_output"] = "html"

    try:
        markdown = pymupdf4llm.to_markdown(doc, **kwargs)
    except Exception as exc:
        raise ConversionError(Msg("err.pdf_convert", exc=exc)) from exc
    finally:
        doc.close()

    markdown = text_fidelity.tidy_pdf_markdown(relink_images(markdown, assets))
    markdown = text_fidelity.finalize(
        markdown, nbsp_to_space=opts.nbsp_to_space, dehyphenate=True
    )
    if not markdown.strip():
        warnings.append(Msg("warn.no_text"))
    warnings += text_fidelity.suspicious_char_report(markdown)
    return ConversionResult(path, markdown, workdir, assets, warnings)
