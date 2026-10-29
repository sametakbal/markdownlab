import string

import pytest

from markdownlab import i18n
from markdownlab.i18n import Msg, t


def _fields(text):
    return {f for _, f, _, _ in string.Formatter().parse(text) if f}


@pytest.mark.parametrize("key", sorted(i18n.STRINGS))
def test_every_key_translated_with_same_placeholders(key):
    entry = i18n.STRINGS[key]
    assert set(entry) == set(i18n.LANGUAGES), key
    assert all(entry.values()), key
    assert _fields(entry["tr"]) == _fields(entry["en"]), key


def test_switching_language():
    i18n.set_language("en")
    assert t("act.save") == "Save"
    i18n.set_language("tr")
    assert t("act.save") == "Kaydet"
    i18n.set_language("xx")  # unknown language -> default
    assert i18n.language() == i18n.DEFAULT_LANGUAGE


def test_msg_follows_current_language():
    m = Msg("warn.fffd", n=3)
    i18n.set_language("tr")
    assert str(m).startswith("3 adet okunamayan")
    i18n.set_language("en")
    assert str(m).startswith("Unreadable characters (U+FFFD) found: 3")


def test_conversion_warnings_are_translatable(tmp_path):
    from markdownlab.core.dispatcher import convert_file
    from markdownlab.core.models import ConversionError, ConversionOptions

    f = tmp_path / "a.txt"
    f.write_text("x")
    with pytest.raises(ConversionError) as info:
        convert_file(f, ConversionOptions(), tmp_path)
    i18n.set_language("en")
    assert str(info.value) == "Unsupported file type: .txt"
    i18n.set_language("tr")
    assert str(info.value) == "Desteklenmeyen dosya türü: .txt"
