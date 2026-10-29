from __future__ import annotations

import shutil
from pathlib import Path

from ..i18n import Msg
from .models import ConversionError, ConversionOptions, ConversionResult

SUPPORTED_EXTENSIONS = {".pdf", ".docx"}


def convert_file(path: Path, opts: ConversionOptions, workdir: Path) -> ConversionResult:
    """Convert a file inside `workdir`; images are written to `workdir/<name>_assets/`."""
    path = Path(path)
    ext = path.suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise ConversionError(Msg("err.unsupported", ext=path.suffix))
    workdir.mkdir(parents=True, exist_ok=True)
    if ext == ".docx":
        from .docx_converter import convert_docx

        return convert_docx(path, opts, workdir)
    from .pdf_converter import convert_pdf

    return convert_pdf(path, opts, workdir)


def save_result(result: ConversionResult, markdown: str, md_path: Path) -> Path:
    """Write the Markdown as UTF-8 (no BOM) and copy the image folder next to it."""
    md_path = Path(md_path)
    md_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text(markdown, encoding="utf-8", newline="\n")
    if result.images:
        target = md_path.parent / result.assets_dir.name
        if target.resolve() != result.assets_dir.resolve():
            shutil.copytree(result.assets_dir, target, dirs_exist_ok=True)
    return md_path


def default_output_path(source: Path, output_dir: str = "") -> Path:
    base = Path(output_dir) if output_dir else source.parent
    return base / f"{source.stem}.md"
