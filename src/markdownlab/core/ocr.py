"""Locate Tesseract language data (tessdata) and prepare the OCR function.

MuPDF embeds the Tesseract engine; it only needs the folder containing the
`*.traineddata` language files.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

from ..i18n import Msg

TESSERACT_DOWNLOAD_URL = "https://github.com/UB-Mannheim/tesseract/wiki"


def _as_tessdata(candidate: str | os.PathLike | None) -> Path | None:
    if not candidate:
        return None
    p = Path(candidate)
    if p.is_file():  # tesseract.exe may have been selected
        p = p.parent
    for d in (p, p / "tessdata"):
        if d.is_dir() and any(d.glob("*.traineddata")):
            return d
    return None


def _default_candidates() -> list[Path]:
    out = []
    base = Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
    out.append(base / "tessdata")  # bundled with the application
    for env in ("ProgramFiles", "ProgramFiles(x86)", "LOCALAPPDATA"):
        root = os.environ.get(env)
        if root:
            out.append(Path(root) / "Tesseract-OCR")
            out.append(Path(root) / "Programs" / "Tesseract-OCR")
    return out


def find_tessdata(custom: str = "") -> Path | None:
    for cand in (custom, os.environ.get("TESSDATA_PREFIX"), *_default_candidates()):
        found = _as_tessdata(cand)
        if found:
            return found
    try:  # tesseract installation on PATH
        import pymupdf

        return _as_tessdata(pymupdf.get_tessdata())
    except Exception:
        return None


def available_languages(tessdata: Path) -> set[str]:
    return {p.stem for p in tessdata.glob("*.traineddata")}


def resolve_language(requested: str, tessdata: Path) -> tuple[str | None, list[Msg]]:
    have = available_languages(tessdata)
    wanted = [lang for lang in requested.split("+") if lang]
    ok = [lang for lang in wanted if lang in have]
    missing = [lang for lang in wanted if lang not in have]
    warnings = []
    if missing:
        warnings.append(Msg("warn.ocr_lang_missing", langs=", ".join(missing), path=str(tessdata)))
    return ("+".join(ok) or None), warnings


def get_ocr_function(tessdata_dir: str, language: str):
    """Return (ocr_function | None, language, warnings)."""
    tessdata = find_tessdata(tessdata_dir)
    if tessdata is None:
        return None, None, [Msg("warn.ocr_unavailable", url=TESSERACT_DOWNLOAD_URL)]
    lang, warnings = resolve_language(language, tessdata)
    if lang is None:
        return None, None, warnings + [Msg("warn.ocr_no_lang")]

    os.environ["TESSDATA_PREFIX"] = str(tessdata)
    from pymupdf4llm.ocr import tesseract_api

    tesseract_api.TESSDATA = str(tessdata)  # the module reads this value at import time
    return tesseract_api.exec_ocr, lang, warnings
