from conftest import TR_TEXT, TR_UPPER

from markdownlab.core.dispatcher import convert_file, save_result
from markdownlab.core.models import ConversionOptions


def test_docx_formatting_and_characters(sample_docx, tmp_path):
    r = convert_file(sample_docx, ConversionOptions(), tmp_path)
    md = r.markdown

    assert "# Ana Başlık Şeması" in md
    assert "## İkinci Düzey Başlık" in md
    assert TR_TEXT in md
    assert TR_UPPER in md
    assert "**kalın ğüş**" in md
    assert "*italik İıÖ*" in md
    assert "<u>altı çizili</u>" in md
    assert "~~üstü çizili~~" in md
    assert "- Birinci madde çay" in md
    assert "- İkinci madde şeker" in md
    assert "1. Numaralı öğe" in md
    assert r"5 \* 3 = 15, a\_b\_c, \[köşeli\], \<etiket>, x|y" in md


def test_docx_tables(sample_docx, tmp_path):
    md = convert_file(sample_docx, ConversionOptions(), tmp_path).markdown
    assert "| Ad | Şehir | Not |" in md
    assert r"| Ayşe | Iğdır | A\|B |" in md
    # the merged-cell table is kept as HTML
    assert '<td colspan="2"><p>Birleşik başlık</p></td>' in md


def test_docx_images_and_save(sample_docx, tmp_path):
    r = convert_file(sample_docx, ConversionOptions(), tmp_path / "work")
    assert [p.name for p in r.images] == ["image_001.png"]
    assert "![](<örnek belge_assets/image_001.png>)" in r.markdown

    out = save_result(r, r.markdown, tmp_path / "çıktı" / "sonuç.md")
    assert out.read_bytes().decode("utf-8") == r.markdown
    assert not out.read_bytes().startswith(b"\xef\xbb\xbf")  # no BOM
    assert (out.parent / "örnek belge_assets" / "image_001.png").is_file()


def test_docx_without_images(sample_docx, tmp_path):
    r = convert_file(sample_docx, ConversionOptions(extract_images=False), tmp_path)
    assert "![" not in r.markdown
    assert r.images == []
