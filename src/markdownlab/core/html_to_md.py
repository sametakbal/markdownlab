"""Convert the semantic HTML produced by mammoth to Markdown without losing information."""
from __future__ import annotations

import re

from bs4 import BeautifulSoup, NavigableString, Tag
from markdownify import ATX, BACKSLASH, MarkdownConverter

# Characters in text that could be interpreted as Markdown syntax.
# markdownify's escape_misc escapes every &, =, + etc., which makes the output
# unreadable; here only characters that actually change meaning are escaped.
_ESCAPE_CHARS_RE = re.compile(r"([`\[\]])")
_TAG_LIKE_RE = re.compile(r"<(?=[A-Za-z/!?])")
_STRIKE_RE = re.compile(r"~~")
_LINE_START_RE = re.compile(r"^(\s*)(#{1,6}(?=\s|$)|>|[-+](?=\s)|\d{1,9}(?=[.)](\s|$)))", re.M)

_FOOTNOTE_ID_RE = re.compile(r"^(footnote|endnote)-(\d+)$")
_FOOTNOTE_REF_RE = re.compile(r"^#(footnote|endnote)-(\d+)$")


class FidelityConverter(MarkdownConverter):
    def __init__(self, **options):
        defaults = dict(
            heading_style=ATX,
            bullets="-",
            strong_em_symbol="*",
            newline_style=BACKSLASH,
            sup_symbol="<sup>",
            sub_symbol="<sub>",
            table_infer_header=True,
            escape_misc=False,
        )
        defaults.update(options)
        super().__init__(**defaults)

    def escape(self, text, parent_tags):
        if not text:
            return text
        text = text.replace("\\", "\\\\")  # backslashes first
        text = super().escape(text, parent_tags)  # * and _
        text = _ESCAPE_CHARS_RE.sub(r"\\\1", text)
        text = _TAG_LIKE_RE.sub(r"\\<", text)
        text = _STRIKE_RE.sub(r"\\~\\~", text)
        text = _LINE_START_RE.sub(_escape_line_start, text)
        if parent_tags and {"td", "th"} & set(parent_tags):
            text = text.replace("|", r"\|")
        return text

    # --- tables -------------------------------------------------------------
    def convert_table(self, el, text, parent_tags):
        if is_complex_table(el):
            # GFM tables cannot represent merged cells / multi-paragraph
            # cells; keep the table as HTML so nothing is lost.
            return "\n\n" + table_to_html(el) + "\n\n"
        return super().convert_table(el, text, parent_tags)

    # --- inline formatting --------------------------------------------------
    def convert_u(self, el, text, parent_tags):
        # Markdown has no underline; keep the HTML tag so the formatting survives
        if not text.strip():
            return text
        return f"<u>{text}</u>"

    def convert_s(self, el, text, parent_tags):
        return self.convert_del(el, text, parent_tags)


def _escape_line_start(m: re.Match) -> str:
    lead, token = m.group(1), m.group(2)
    if token[0].isdigit():
        return f"{lead}{token}\\"  # "1." -> "1\." (the dot follows)
    return f"{lead}\\{token}"


def is_complex_table(table: Tag) -> bool:
    for cell in table.find_all(["td", "th"]):
        if _own(cell, table) is False:
            continue
        if int(cell.get("colspan", 1) or 1) > 1 or int(cell.get("rowspan", 1) or 1) > 1:
            return True
        if cell.find(["ul", "ol", "table", "pre", "blockquote", "h1", "h2", "h3", "h4", "h5", "h6"]):
            return True
        if len(cell.find_all("p", recursive=False)) > 1:
            return True
    return False


def _own(cell: Tag, table: Tag) -> bool:
    return cell.find_parent("table") is table


def table_to_html(table: Tag) -> str:
    """Write the table as plain HTML, keeping the cell formatting."""
    rows = []
    for tr in table.find_all("tr"):
        if tr.find_parent("table") is not table:
            continue
        cells = []
        for cell in tr.find_all(["td", "th"], recursive=False):
            attrs = ""
            for a in ("colspan", "rowspan"):
                v = cell.get(a)
                if v and str(v) != "1":
                    attrs += f' {a}="{v}"'
            inner = _cell_html(cell)
            cells.append(f"<{cell.name}{attrs}>{inner}</{cell.name}>")
        rows.append("<tr>" + "".join(cells) + "</tr>")
    return "<table>\n" + "\n".join(rows) + "\n</table>"


_KEEP_TAGS = {"strong", "b", "em", "i", "u", "s", "del", "sup", "sub", "br", "a", "img",
              "ul", "ol", "li", "p", "table", "tr", "td", "th", "code", "pre"}


def _cell_html(cell: Tag) -> str:
    # Markdown is not processed inside HTML blocks, so keep the cell as clean HTML
    clone = BeautifulSoup(str(cell), "html.parser").find(cell.name)
    for tag in clone.find_all(True):
        if tag.name not in _KEEP_TAGS:
            tag.unwrap()
            continue
        allowed = {"href", "src", "alt", "colspan", "rowspan"}
        for attr in list(tag.attrs):
            if attr not in allowed:
                del tag[attr]
    return clone.decode_contents().strip()


def prepare_footnotes(soup: BeautifulSoup) -> list[tuple[str, BeautifulSoup]]:
    """Turn mammoth footnotes into [^n] references and detach their bodies."""
    notes = []
    for li in soup.find_all("li", id=_FOOTNOTE_ID_RE):
        kind, num = _FOOTNOTE_ID_RE.match(li["id"]).groups()
        label = num if kind == "footnote" else f"e{num}"
        for back in li.find_all("a", href=re.compile(r"^#(footnote|endnote)-ref-")):
            back.decompose()
        notes.append((label, li))
    for a in soup.find_all("a", href=_FOOTNOTE_REF_RE):
        kind, num = _FOOTNOTE_REF_RE.match(a["href"]).groups()
        label = num if kind == "footnote" else f"e{num}"
        target = a.parent if a.parent and a.parent.name == "sup" else a
        target.replace_with(NavigableString(f"\x00FN{label}\x00"))
    for label, li in notes:
        li.extract()
    for ol in soup.find_all("ol"):
        if not ol.find("li"):
            ol.decompose()
    return notes


def html_to_markdown(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    notes = prepare_footnotes(soup)
    conv = FidelityConverter()
    md = conv.convert_soup(soup)
    md = re.sub(r"\x00FN([^\x00]+)\x00", r"[^\1]", md)
    if notes:
        lines = ["", ""]
        for label, li in notes:
            body = conv.convert_soup(BeautifulSoup(li.decode_contents(), "html.parser")).strip()
            body = body.replace("\n", "\n    ")
            lines.append(f"[^{label}]: {body}")
        md = md.rstrip() + "\n".join(lines) + "\n"
    return md
