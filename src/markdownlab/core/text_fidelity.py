"""Character-preserving post-processing.

No function here performs case conversion (to avoid the Turkish dotted /
dotless I problem); text is only touched to repair encoding-related damage.
"""
from __future__ import annotations

import re
import unicodedata

from ..i18n import Msg

LIGATURES = {
    "ﬀ": "ff",
    "ﬁ": "fi",
    "ﬂ": "fl",
    "ﬃ": "ffi",
    "ﬄ": "ffl",
    "ﬅ": "st",
    "ﬆ": "st",
}

# Zero-width / invisible characters (ZWJ/ZWNJ are deliberately kept)
INVISIBLE = {
    "​": "",  # zero width space
    "⁠": "",  # word joiner
    "﻿": "",  # BOM / zero width no-break space
    "­": "",  # soft hyphen
}

REPLACEMENT_CHAR = "�"

_FENCE_RE = re.compile(r"^(```|~~~)")
# end-of-line hyphenation: "keli-\nme" -> "kelime" (only if the next letter is lowercase)
_HYPHEN_BREAK_RE = re.compile(r"(\w)-\n(?=[a-zçğıöşüâîû])")


def normalize_chars(text: str, *, nbsp_to_space: bool = False) -> str:
    text = unicodedata.normalize("NFC", text)
    # a soft hyphen at the end of a line split the word: join it
    text = text.replace("­\n", "")
    table = {**LIGATURES, **INVISIBLE}
    if nbsp_to_space:
        table[" "] = " "
        table[" "] = " "
    return text.translate(str.maketrans(table))


def normalize_newlines(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")


def collapse_blank_lines(text: str) -> str:
    """Collapse runs of blank lines to one, outside code blocks."""
    out: list[str] = []
    in_fence = False
    blank_run = 0
    for line in text.split("\n"):
        if _FENCE_RE.match(line.lstrip()):
            in_fence = not in_fence
        if not in_fence and line.strip() == "":
            blank_run += 1
            if blank_run > 1:
                continue
        else:
            blank_run = 0
        out.append(line)
    return "\n".join(out).strip("\n") + "\n"


def join_hyphenated_lines(text: str) -> str:
    """Join end-of-line hyphenation from PDFs (except inside code blocks)."""
    parts = re.split(r"(^```.*?^```[^\n]*$)", text, flags=re.M | re.S)
    for i in range(0, len(parts), 2):
        parts[i] = _HYPHEN_BREAK_RE.sub(r"\1", parts[i])
    return "".join(parts)


_BOLD_HEADING_RE = re.compile(r"^(#{1,6}) +\*\*(.+?)\*\* *$", re.M)
_LIST_ITEM_RE = re.compile(r"^\s*(?:[-*+]|\d{1,9}[.)]) ")


def tidy_pdf_markdown(text: str) -> str:
    """Simplify redundant markup in pymupdf4llm output."""
    text = re.sub(r"[ \t]+$", "", text, flags=re.M)
    # headings already render bold: "# **Title**" -> "# Title"
    text = _BOLD_HEADING_RE.sub(r"\1 \2", text)
    # remove blank lines between consecutive list items (tight list)
    lines = text.split("\n")
    out: list[str] = []
    for i, line in enumerate(lines):
        if (
            line == ""
            and out
            and i + 1 < len(lines)
            and _LIST_ITEM_RE.match(out[-1])
            and _LIST_ITEM_RE.match(lines[i + 1])
        ):
            continue
        out.append(line)
    return "\n".join(out)


def suspicious_char_report(text: str) -> list[Msg]:
    """Return warnings if the output contains characters that indicate encoding problems."""
    warnings = []
    fffd = text.count(REPLACEMENT_CHAR)
    if fffd:
        warnings.append(Msg("warn.fffd", n=fffd))
    pua = sum(1 for ch in text if 0xE000 <= ord(ch) <= 0xF8FF)
    if pua:
        warnings.append(Msg("warn.pua", n=pua))
    return warnings


def finalize(text: str, *, nbsp_to_space: bool = False, dehyphenate: bool = False) -> str:
    text = normalize_newlines(text)
    text = normalize_chars(text, nbsp_to_space=nbsp_to_space)
    if dehyphenate:
        text = join_hyphenated_lines(text)
    return collapse_blank_lines(text)
