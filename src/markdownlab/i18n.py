"""Simple translation layer (Turkish / English).

Strings are stored by key; `t()` formats them for the current language.
Conversion warnings are kept as `Msg` objects so they can be re-translated
when the language changes.
"""
from __future__ import annotations

import locale
import os

LANGUAGES = {"tr": "Türkçe", "en": "English"}
DEFAULT_LANGUAGE = "en"

_current = DEFAULT_LANGUAGE

STRINGS: dict[str, dict[str, str]] = {
    # --- main window --------------------------------------------------------
    "app.title": {"tr": "MarkdownLab — PDF / DOCX → Markdown", "en": "MarkdownLab — PDF / DOCX → Markdown"},
    "toolbar": {"tr": "Araçlar", "en": "Tools"},
    "act.add": {"tr": "Dosya Ekle…", "en": "Add Files…"},
    "act.remove": {"tr": "Kaldır", "en": "Remove"},
    "act.convert": {"tr": "Tümünü Dönüştür", "en": "Convert All"},
    "act.cancel": {"tr": "İptal", "en": "Cancel"},
    "act.save": {"tr": "Kaydet", "en": "Save"},
    "act.save_as": {"tr": "Farklı Kaydet…", "en": "Save As…"},
    "act.save_all": {"tr": "Tümünü Kaydet", "en": "Save All"},
    "act.settings": {"tr": "Ayarlar…", "en": "Settings…"},
    "act.about": {"tr": "Hakkında", "en": "About"},
    "about.title": {"tr": "MarkdownLab Hakkında", "en": "About MarkdownLab"},
    "about.body": {
        "tr": "<h3>MarkdownLab {version}</h3>"
              "<p>PDF ve DOCX dosyalarını karakterleri ve biçimi koruyarak Markdown'a çevirir.</p>"
              "<p>{copyright}</p>"
              "<p>Bu program özgür yazılımdır: Free Software Foundation tarafından yayımlanan "
              "GNU Affero Genel Kamu Lisansı'nın 3. sürümü ya da (tercihinize bağlı olarak) "
              "daha sonraki herhangi bir sürümünün koşulları altında yeniden dağıtabilir "
              "ve/veya değiştirebilirsiniz.</p>"
              "<p>Bu program yararlı olması umuduyla, ancak <b>HİÇBİR GARANTİ OLMADAN</b>; "
              "SATILABİLİRLİK veya BELİRLİ BİR AMACA UYGUNLUK zımni garantisi bile olmaksızın "
              'dağıtılmaktadır. Ayrıntılar için <a href="https://www.gnu.org/licenses/agpl-3.0.html">'
              "GNU AGPL</a> metnine bakın.</p>"
              "<p>Kullanılan üçüncü taraf bileşenler ve lisansları program klasöründeki "
              "LICENSE ve THIRD_PARTY_NOTICES.md dosyalarında listelenmiştir.</p>",
        "en": "<h3>MarkdownLab {version}</h3>"
              "<p>Converts PDF and DOCX files to Markdown while preserving characters and formatting.</p>"
              "<p>{copyright}</p>"
              "<p>This program is free software: you can redistribute it and/or modify it under "
              "the terms of the GNU Affero General Public License as published by the Free "
              "Software Foundation, either version 3 of the License, or (at your option) any "
              "later version.</p>"
              "<p>This program is distributed in the hope that it will be useful, but "
              "<b>WITHOUT ANY WARRANTY</b>; without even the implied warranty of MERCHANTABILITY "
              'or FITNESS FOR A PARTICULAR PURPOSE. See the <a href="https://www.gnu.org/licenses/agpl-3.0.html">'
              "GNU AGPL</a> for more details.</p>"
              "<p>Third-party components and their licenses are listed in the LICENSE and "
              "THIRD_PARTY_NOTICES.md files in the program folder.</p>",
    },
    "language": {"tr": "Dil:", "en": "Language:"},
    "col.file": {"tr": "Dosya", "en": "File"},
    "col.status": {"tr": "Durum", "en": "Status"},
    "drop_hint": {
        "tr": "PDF veya DOCX dosyalarını (ya da klasörleri) buraya sürükleyip bırakın.",
        "en": "Drag and drop PDF or DOCX files (or folders) here.",
    },
    "editor.placeholder": {"tr": "Dönüştürülen Markdown burada görünecek.", "en": "The converted Markdown will appear here."},
    "tab.markdown": {"tr": "Markdown", "en": "Markdown"},
    "tab.preview": {"tr": "Önizleme", "en": "Preview"},
    "status.pending": {"tr": "Bekliyor", "en": "Pending"},
    "status.queued": {"tr": "Sırada", "en": "Queued"},
    "status.running": {"tr": "Dönüştürülüyor…", "en": "Converting…"},
    "status.done": {"tr": "Tamam", "en": "Done"},
    "status.done_warnings": {"tr": "Tamam ({n} uyarı)", "en": "Done (warnings: {n})"},
    "status.failed": {"tr": "Hata", "en": "Error"},
    "status.cancelled": {"tr": "İptal edildi", "en": "Cancelled"},
    "msg.cancelling": {"tr": "Sıradaki dönüşümler iptal ediliyor…", "en": "Cancelling queued conversions…"},
    "msg.converting": {"tr": "Dönüştürülüyor: {name}", "en": "Converting: {name}"},
    "msg.batch_done": {"tr": "Dönüşüm tamamlandı: {ok}/{total} dosya hazır.", "en": "Conversion finished: {ok}/{total} files ready."},
    "msg.saved": {"tr": "Kaydedildi: {path}", "en": "Saved: {path}"},
    "msg.saved_n": {"tr": "{n} dosya kaydedildi.", "en": "Files saved: {n}."},
    "msg.settings_saved": {
        "tr": "Ayarlar kaydedildi; yeni dönüşümlerde geçerli olacak.",
        "en": "Settings saved; they apply to new conversions.",
    },
    "dlg.open": {"tr": "Dosya seç", "en": "Select files"},
    "dlg.open_filter": {
        "tr": "Belgeler (*.pdf *.docx);;PDF (*.pdf);;Word (*.docx)",
        "en": "Documents (*.pdf *.docx);;PDF (*.pdf);;Word (*.docx)",
    },
    "dlg.save_as": {"tr": "Markdown olarak kaydet", "en": "Save as Markdown"},
    "dlg.save_failed": {"tr": "Kaydedilemedi", "en": "Could not save"},
    "dlg.overwrite.title": {"tr": "Üzerine yazılsın mı?", "en": "Overwrite?"},
    "dlg.overwrite.body": {
        "tr": "Şu dosyalar zaten var:\n\n{names}{more}\n\nÜzerine yazılsın mı?",
        "en": "These files already exist:\n\n{names}{more}\n\nOverwrite them?",
    },
    "dlg.overwrite.more": {"tr": "\n… ve {n} dosya daha", "en": "\n… and {n} more file(s)"},
    "dlg.unsaved.title": {"tr": "Kaydedilmemiş dönüşümler", "en": "Unsaved conversions"},
    "dlg.unsaved.body": {
        "tr": "{n} dönüşüm henüz kaydedilmedi. Yine de çıkılsın mı?",
        "en": "Unsaved conversions: {n}. Quit anyway?",
    },
    # --- settings -----------------------------------------------------------
    "set.title": {"tr": "Ayarlar", "en": "Settings"},
    "set.general": {"tr": "Genel", "en": "General"},
    "set.language": {"tr": "Arayüz dili:", "en": "Interface language:"},
    "set.output_dir": {"tr": "Çıktı klasörü:", "en": "Output folder:"},
    "set.output_dir.placeholder": {"tr": "Boş: kaynak dosyanın bulunduğu klasör", "en": "Empty: the source file's folder"},
    "set.extract_images": {"tr": "Görselleri çıkar (<ad>_assets klasörüne)", "en": "Extract images (into a <name>_assets folder)"},
    "set.image_dpi": {"tr": "Görsel çözünürlüğü (DPI):", "en": "Image resolution (DPI):"},
    "set.remove_hf": {
        "tr": "PDF üst/alt bilgilerini ve sayfa numaralarını kaldır",
        "en": "Remove PDF page headers, footers and page numbers",
    },
    "set.tables_html": {
        "tr": "PDF tablolarını HTML olarak yaz (birleşik hücreler korunur)",
        "en": "Write PDF tables as HTML (keeps merged cells)",
    },
    "set.nbsp": {"tr": "Bölünmez boşlukları normal boşluğa çevir", "en": "Convert non-breaking spaces to normal spaces"},
    "set.ocr_box": {"tr": "OCR (Tesseract)", "en": "OCR (Tesseract)"},
    "set.ocr_enabled": {
        "tr": "Gerektiğinde OCR uygula (taranmış / bozuk kodlamalı sayfalar)",
        "en": "Apply OCR when needed (scanned / badly encoded pages)",
    },
    "set.force_ocr": {"tr": "Tüm sayfalarda OCR'ı zorla", "en": "Force OCR on all pages"},
    "set.ocr_lang": {"tr": "Diller:", "en": "Languages:"},
    "set.ocr_dpi": {"tr": "OCR çözünürlüğü (DPI):", "en": "OCR resolution (DPI):"},
    "set.tessdata": {"tr": "tessdata klasörü:", "en": "tessdata folder:"},
    "set.tessdata.placeholder": {"tr": "Boş: otomatik bul", "en": "Empty: detect automatically"},
    "set.browse": {"tr": "Gözat…", "en": "Browse…"},
    "set.pick_output": {"tr": "Çıktı klasörü", "en": "Output folder"},
    "set.pick_tessdata": {"tr": "tessdata veya Tesseract-OCR klasörü", "en": "tessdata or Tesseract-OCR folder"},
    "set.ocr_missing": {
        "tr": "⚠ Tesseract dil dosyaları bulunamadı; taranmış PDF'ler metne çevrilemez. "
              '<a href="{url}">Tesseract\'ı indirin</a> (kurulumda Türkçe dil paketini seçin).',
        "en": "⚠ Tesseract language files not found; scanned PDFs cannot be converted to text. "
              '<a href="{url}">Download Tesseract</a> (select the language packs you need during setup).',
    },
    "set.ocr_found": {"tr": "✓ {path}<br>Yüklü diller: {langs}", "en": "✓ {path}<br>Installed languages: {langs}"},
    # --- conversion warnings / errors ---------------------------------------
    "raw": {"tr": "{text}", "en": "{text}"},
    "err.unsupported": {"tr": "Desteklenmeyen dosya türü: {ext}", "en": "Unsupported file type: {ext}"},
    "err.docx_read": {"tr": "DOCX okunamadı: {exc}", "en": "Could not read DOCX: {exc}"},
    "err.pdf_open": {"tr": "PDF açılamadı: {exc}", "en": "Could not open PDF: {exc}"},
    "err.pdf_password": {"tr": "PDF parola korumalı; dönüştürülemez.", "en": "The PDF is password protected and cannot be converted."},
    "err.pdf_convert": {"tr": "PDF dönüştürülemedi: {exc}", "en": "PDF conversion failed: {exc}"},
    "warn.non_web_image": {
        "tr": "Görsel {n} {ext} biçiminde; çoğu Markdown görüntüleyicisi bunu gösteremez.",
        "en": "Image {n} is in {ext} format; most Markdown viewers cannot display it.",
    },
    "warn.unmapped_styles": {
        "tr": "Şu Word stilleri için özel eşleme yok, metin düz paragraf olarak aktarıldı: {styles}",
        "en": "No mapping for these Word styles; their text was kept as plain paragraphs: {styles}",
    },
    "warn.no_text": {
        "tr": "Belgeden metin çıkarılamadı. Taranmış bir PDF ise OCR için Tesseract ve Türkçe dil dosyasını kurun.",
        "en": "No text could be extracted. If this is a scanned PDF, install Tesseract and the needed language files for OCR.",
    },
    "warn.fffd": {
        "tr": "{n} adet okunamayan karakter (U+FFFD) bulundu; kaynak fontun Unicode eşlemesi bozuk olabilir. OCR'ı zorlamayı deneyin.",
        "en": "Unreadable characters (U+FFFD) found: {n}; the source font's Unicode mapping may be broken. Try forcing OCR.",
    },
    "warn.pua": {
        "tr": "{n} adet özel kullanım alanı (PUA) karakteri bulundu; sembol fontları veya bozuk font eşlemesi olabilir.",
        "en": "Private use area (PUA) characters found: {n}; these may be symbol fonts or a broken font mapping.",
    },
    "warn.ocr_lang_missing": {
        "tr": "OCR dil dosyası eksik: {langs} ({path}). Türkçe için 'tur.traineddata' gereklidir.",
        "en": "Missing OCR language file: {langs} ({path}). Turkish requires 'tur.traineddata'.",
    },
    "warn.ocr_unavailable": {
        "tr": "OCR devre dışı: Tesseract dil dosyaları bulunamadı. Taranmış sayfalar metne çevrilemez. Kurulum: {url}",
        "en": "OCR disabled: Tesseract language files not found. Scanned pages cannot be converted to text. Install: {url}",
    },
    "warn.ocr_no_lang": {
        "tr": "OCR devre dışı: istenen dillerin hiçbiri yüklü değil.",
        "en": "OCR disabled: none of the requested languages are installed.",
    },
    # --- command line -------------------------------------------------------
    "cli.description": {
        "tr": "PDF/DOCX dosyalarını Markdown'a çevirir. Argümansız çalıştırılırsa arayüz açılır.",
        "en": "Converts PDF/DOCX files to Markdown. Opens the GUI when run without arguments.",
    },
    "cli.files": {"tr": "dönüştürülecek .pdf/.docx dosyaları", "en": ".pdf/.docx files to convert"},
    "cli.output_dir": {"tr": "çıktı klasörü (varsayılan: kaynağın yanı)", "en": "output folder (default: next to the source)"},
    "cli.no_ocr": {"tr": "OCR'ı devre dışı bırak", "en": "disable OCR"},
    "cli.lang": {"tr": "arayüz / mesaj dili", "en": "interface / message language"},
    "cli.ok": {"tr": "OK    {src} -> {out}", "en": "OK    {src} -> {out}"},
    "cli.error": {"tr": "HATA  {src}: {exc}", "en": "ERROR {src}: {exc}"},
    "cli.warning": {"tr": "  uyarı: {msg}", "en": "  warning: {msg}"},
}


def set_language(lang: str) -> None:
    global _current
    _current = lang if lang in LANGUAGES else DEFAULT_LANGUAGE


def language() -> str:
    return _current


def t(key: str, **kwargs) -> str:
    entry = STRINGS[key]
    text = entry.get(_current) or entry[DEFAULT_LANGUAGE]
    return text.format(**kwargs) if kwargs else text


def detect_system_language() -> str:
    """Return 'tr' if the system language is Turkish, otherwise 'en'."""
    candidates = [os.environ.get(v, "") for v in ("LC_ALL", "LC_MESSAGES", "LANG")]
    try:
        candidates.append(locale.getlocale()[0] or "")
    except ValueError:
        pass
    try:
        from PySide6.QtCore import QLocale

        candidates.append(QLocale.system().name())
    except ImportError:
        pass
    for c in candidates:
        if c.lower().startswith(("tr", "turkish")):
            return "tr"
    return "en"


class Msg:
    """Translatable message; `str()` renders it in the current language on every call."""

    __slots__ = ("key", "kwargs")

    def __init__(self, key: str, **kwargs):
        self.key = key
        self.kwargs = kwargs

    def __str__(self) -> str:
        return t(self.key, **self.kwargs)

    def __repr__(self) -> str:
        return f"Msg({self.key!r}, {self.kwargs!r})"
