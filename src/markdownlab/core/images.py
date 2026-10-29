from __future__ import annotations

import re
from pathlib import Path

CONTENT_TYPE_EXT = {
    "image/png": "png",
    "image/jpeg": "jpg",
    "image/jpg": "jpg",
    "image/gif": "gif",
    "image/bmp": "bmp",
    "image/tiff": "tiff",
    "image/svg+xml": "svg",
    "image/webp": "webp",
    "image/x-emf": "emf",
    "image/x-wmf": "wmf",
}

# Formats that browsers / Markdown viewers cannot display
NON_WEB_EXT = {"emf", "wmf", "tiff"}


def assets_dir_name(stem: str) -> str:
    return f"{stem}_assets"


def md_link_target(rel_path: str) -> str:
    """Wrap paths containing spaces or parentheses in CommonMark's <...> form."""
    rel_path = rel_path.replace("\\", "/")
    if re.search(r"[\s()<>]", rel_path):
        return f"<{rel_path}>"
    return rel_path


_IMG_LINK_RE = re.compile(r"!\[([^\]]*)\]\((<[^>]+>|[^)\n]+?)\)")


def relink_images(markdown: str, assets_dir: Path) -> str:
    """Rewrite image links to `<stem>_assets/<name>`, matching by file name."""
    names = {p.name for p in assets_dir.iterdir()} if assets_dir.is_dir() else set()
    if not names:
        return markdown

    def repl(m: re.Match) -> str:
        alt, target = m.group(1), m.group(2).strip("<>")
        name = target.replace("\\", "/").rsplit("/", 1)[-1]
        if name in names:
            return f"![{alt}]({md_link_target(f'{assets_dir.name}/{name}')})"
        return m.group(0)

    return _IMG_LINK_RE.sub(repl, markdown)
