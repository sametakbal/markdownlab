import unicodedata

from markdownlab.core import text_fidelity as tf
from markdownlab.core.html_to_md import html_to_markdown


def test_nfc_normalization_merges_combining_dot():
    decomposed = unicodedata.normalize("NFD", "İstanbul ğ ş")
    assert tf.normalize_chars(decomposed) == "İstanbul ğ ş"


def test_ligatures_and_invisible_chars():
    assert tf.normalize_chars("\ufb01nal \ufb02uent e\ufb00ect") == "final fluent effect"
    assert tf.normalize_chars("ke\u00adli\u200bme\ufeff") == "kelime"
    assert tf.normalize_chars("keli\u00ad\nme") == "kelime"


def test_nbsp_kept_unless_requested():
    assert tf.normalize_chars("a\u00a0b") == "a\u00a0b"
    assert tf.normalize_chars("a\u00a0b", nbsp_to_space=True) == "a b"


def test_turkish_case_untouched():
    s = "Iı İi ÇçĞğÖöŞşÜü"
    assert tf.finalize(s) == s + "\n"


def test_dehyphenation_only_for_lowercase_continuation():
    assert tf.join_hyphenated_lines("çalış-\nmalar") == "çalışmalar"
    assert tf.join_hyphenated_lines("Ankara-\nİstanbul") == "Ankara-\nİstanbul"


def test_collapse_blank_lines_keeps_code_blocks():
    src = "a\n\n\n\nb\n```\nx\n\n\n\ny\n```\n"
    assert tf.collapse_blank_lines(src) == "a\n\nb\n```\nx\n\n\n\ny\n```\n"


def test_suspicious_chars_reported():
    assert tf.suspicious_char_report("temiz metin") == []
    assert len(tf.suspicious_char_report("bozuk \ufffd \ue001")) == 2


def test_tidy_pdf_markdown():
    src = "# **Başlık**  \n\n- a\n\n- b\n\nmetin "
    assert tf.tidy_pdf_markdown(src) == "# Başlık\n\n- a\n- b\n\nmetin"


def test_html_escaping_is_minimal_but_safe():
    md = html_to_markdown("<p>5 * 3, a_b, [x], &lt;tag&gt;, C:\\yol, a &amp; b = c + d</p>")
    assert md.strip() == r"5 \* 3, a\_b, \[x\], \<tag>, C:\\yol, a & b = c + d"


def test_line_start_markers_escaped():
    md = html_to_markdown("<p># değil başlık</p><p>1. değil liste</p><p>- değil madde</p>")
    assert "\\# değil başlık" in md
    assert "1\\. değil liste" in md
    assert "\\- değil madde" in md


def test_nested_lists():
    md = html_to_markdown("<ul><li>bir<ul><li>iç öğe</li></ul></li><li>iki</li></ul>")
    lines = [line for line in md.splitlines() if line.strip()]
    assert lines[0] == "- bir"
    assert lines[1].startswith("  ") and lines[1].strip() == "- iç öğe"
    assert lines[2] == "- iki"


def test_footnotes():
    html = (
        '<p>Metin<sup><a href="#footnote-1" id="footnote-ref-1">[1]</a></sup> devam.</p>'
        '<ol><li id="footnote-1"><p>Dipnot açıklaması ğüş <a href="#footnote-ref-1">↑</a></p></li></ol>'
    )
    md = html_to_markdown(html)
    assert "Metin[^1] devam." in md
    assert "[^1]: Dipnot açıklaması ğüş" in md
    assert "↑" not in md


def test_pipe_escaped_in_table_cells():
    md = html_to_markdown("<table><tr><td>a|b</td><td>c</td></tr></table>")
    assert r"a\|b" in md
