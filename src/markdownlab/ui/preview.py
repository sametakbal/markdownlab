from __future__ import annotations

import re

from markdown_it import MarkdownIt
from mdit_py_plugins.footnote import footnote_plugin

_md = (
    MarkdownIt("commonmark", {"html": True, "breaks": False})
    .enable(["table", "strikethrough"])
    .use(footnote_plugin)
)

# QTextBrowser only supports HTML4-level CSS; table borders are set via attributes
_TABLE_RE = re.compile(r"<table(\s[^>]*)?>")

CSS = """
body { font-family: 'Segoe UI', sans-serif; font-size: 11pt; }
h1 { font-size: 20pt; } h2 { font-size: 16pt; } h3 { font-size: 13pt; }
code, pre { font-family: Consolas, monospace; background: #f3f3f3; }
th { background: #eeeeee; }
blockquote { color: #555555; margin-left: 12px; }
"""


def render_html(markdown: str) -> str:
    body = _md.render(markdown)
    body = _TABLE_RE.sub('<table border="1" cellspacing="0" cellpadding="4">', body)
    return f"<html><head><style>{CSS}</style></head><body>{body}</body></html>"
