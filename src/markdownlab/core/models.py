from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from ..i18n import Msg


@dataclass
class ConversionOptions:
    extract_images: bool = True
    image_dpi: int = 150

    # PDF
    remove_headers_footers: bool = True
    pdf_tables_as_html: bool = False

    # OCR (scanned / badly encoded PDF pages)
    ocr_enabled: bool = True
    force_ocr: bool = False
    ocr_language: str = "tur+eng"
    ocr_dpi: int = 300
    tessdata_dir: str = ""  # detected automatically when empty

    # Text
    nbsp_to_space: bool = False


@dataclass
class ConversionResult:
    source: Path
    markdown: str
    workdir: Path  # folder the .md file's relative image links resolve against
    assets_dir: Path
    warnings: list[Msg] = field(default_factory=list)  # str(msg) yields text in the current language

    @property
    def images(self) -> list[Path]:
        if not self.assets_dir.is_dir():
            return []
        return sorted(p for p in self.assets_dir.iterdir() if p.is_file())


class ConversionError(Exception):
    pass
