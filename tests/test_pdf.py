import pytest
from conftest import TR_TEXT, TR_UPPER

from markdownlab.core import ocr
from markdownlab.core.dispatcher import convert_file
from markdownlab.core.models import ConversionError, ConversionOptions


def test_pdf_formatting_and_characters(sample_pdf, tmp_path):
    md = convert_file(sample_pdf, ConversionOptions(), tmp_path).markdown

    assert "# PDF Başlığı Ğüşİ" in md
    assert "## Alt Bölüm Çalışması" in md
    assert TR_TEXT in md
    assert TR_UPPER in md
    assert "**kalın şekil**" in md
    assert "eğik yazı" in md
    assert "- birinci öğe\n- ikinci öğe" in md


def test_pdf_table(sample_pdf, tmp_path):
    md = convert_file(sample_pdf, ConversionOptions(), tmp_path).markdown
    rows = [line.replace(" ", "") for line in md.splitlines() if line.startswith("|")]
    assert any("Ayşe|Iğdır" in r for r in rows)
    assert any("Çağrı|İzmir" in r for r in rows)


def test_pdf_images(sample_pdf, tmp_path):
    r = convert_file(sample_pdf, ConversionOptions(), tmp_path)
    assert len(r.images) == 1
    assert f"]({r.assets_dir.name}/{r.images[0].name})" in r.markdown


def test_pdf_tables_as_html(sample_pdf, tmp_path):
    md = convert_file(sample_pdf, ConversionOptions(pdf_tables_as_html=True), tmp_path).markdown
    assert "<table" in md and "Iğdır" in md


def test_unsupported_extension(tmp_path):
    f = tmp_path / "a.txt"
    f.write_text("x")
    with pytest.raises(ConversionError):
        convert_file(f, ConversionOptions(), tmp_path)


def test_scanned_pdf_ocr(scanned_pdf, tmp_path):
    tessdata = ocr.find_tessdata()
    if tessdata is None or "tur" not in ocr.available_languages(tessdata):
        pytest.skip("Tesseract + Türkçe dil dosyası kurulu değil")
    md = convert_file(scanned_pdf, ConversionOptions(), tmp_path).markdown
    for word in ("Iğdır'da", "şişeler", "İSTANBUL", "Çağrı", "Öğütücü"):
        assert word in md


def test_scanned_pdf_without_ocr_warns(scanned_pdf, tmp_path):
    r = convert_file(scanned_pdf, ConversionOptions(ocr_enabled=False), tmp_path)
    assert any(w.key == "warn.no_text" for w in r.warnings) or "Iğdır" not in r.markdown
