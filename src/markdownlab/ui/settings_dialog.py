from __future__ import annotations

from dataclasses import asdict, fields

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from .. import i18n
from ..core import ocr
from ..core.models import ConversionOptions
from ..i18n import t


def load_settings() -> tuple[ConversionOptions, str]:
    """Return (conversion options, output folder)."""
    s = QSettings()
    opts = ConversionOptions()
    for f in fields(ConversionOptions):
        default = getattr(opts, f.name)
        value = s.value(f"options/{f.name}", default)
        if isinstance(default, bool):
            value = value in (True, "true", "1", 1)
        elif isinstance(default, int):
            value = int(value)
        setattr(opts, f.name, value)
    return opts, str(s.value("output_dir", ""))


def store_settings(opts: ConversionOptions, output_dir: str) -> None:
    s = QSettings()
    for k, v in asdict(opts).items():
        s.setValue(f"options/{k}", v)
    s.setValue("output_dir", output_dir)


def load_language() -> str:
    """Saved language; the system language on first launch."""
    lang = str(QSettings().value("language", ""))
    return lang if lang in i18n.LANGUAGES else i18n.detect_system_language()


def store_language(lang: str) -> None:
    QSettings().setValue("language", lang)


def language_combo(current: str) -> QComboBox:
    combo = QComboBox()
    for code, name in i18n.LANGUAGES.items():
        combo.addItem(name, code)
    combo.setCurrentIndex(combo.findData(current))
    return combo


class SettingsDialog(QDialog):
    def __init__(self, opts: ConversionOptions, output_dir: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle(t("set.title"))
        self.setMinimumWidth(520)

        self.language = language_combo(i18n.language())

        self.output_dir = QLineEdit(output_dir)
        self.output_dir.setPlaceholderText(t("set.output_dir.placeholder"))
        out_row = _with_browse(self.output_dir, self._pick_output_dir)

        self.extract_images = QCheckBox(t("set.extract_images"))
        self.extract_images.setChecked(opts.extract_images)
        self.image_dpi = _spin(72, 600, opts.image_dpi)
        self.remove_hf = QCheckBox(t("set.remove_hf"))
        self.remove_hf.setChecked(opts.remove_headers_footers)
        self.tables_html = QCheckBox(t("set.tables_html"))
        self.tables_html.setChecked(opts.pdf_tables_as_html)
        self.nbsp = QCheckBox(t("set.nbsp"))
        self.nbsp.setChecked(opts.nbsp_to_space)

        general = QGroupBox(t("set.general"))
        gl = QFormLayout(general)
        gl.addRow(t("set.language"), self.language)
        gl.addRow(t("set.output_dir"), out_row)
        gl.addRow(self.extract_images)
        gl.addRow(t("set.image_dpi"), self.image_dpi)
        gl.addRow(self.remove_hf)
        gl.addRow(self.tables_html)
        gl.addRow(self.nbsp)

        self.ocr_enabled = QCheckBox(t("set.ocr_enabled"))
        self.ocr_enabled.setChecked(opts.ocr_enabled)
        self.force_ocr = QCheckBox(t("set.force_ocr"))
        self.force_ocr.setChecked(opts.force_ocr)
        self.ocr_lang = QLineEdit(opts.ocr_language)
        self.ocr_dpi = _spin(150, 600, opts.ocr_dpi)
        self.tessdata = QLineEdit(opts.tessdata_dir)
        self.tessdata.setPlaceholderText(t("set.tessdata.placeholder"))
        self.tessdata.textChanged.connect(self._update_ocr_status)
        self.ocr_lang.textChanged.connect(self._update_ocr_status)
        tess_row = _with_browse(self.tessdata, self._pick_tessdata)
        self.ocr_status = QLabel()
        self.ocr_status.setWordWrap(True)
        self.ocr_status.setOpenExternalLinks(True)

        ocr_box = QGroupBox(t("set.ocr_box"))
        ol = QFormLayout(ocr_box)
        ol.addRow(self.ocr_enabled)
        ol.addRow(self.force_ocr)
        ol.addRow(t("set.ocr_lang"), self.ocr_lang)
        ol.addRow(t("set.ocr_dpi"), self.ocr_dpi)
        ol.addRow(t("set.tessdata"), tess_row)
        ol.addRow(self.ocr_status)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(general)
        layout.addWidget(ocr_box)
        layout.addWidget(buttons)
        self._update_ocr_status()

    def values(self) -> tuple[ConversionOptions, str]:
        opts = ConversionOptions(
            extract_images=self.extract_images.isChecked(),
            image_dpi=self.image_dpi.value(),
            remove_headers_footers=self.remove_hf.isChecked(),
            pdf_tables_as_html=self.tables_html.isChecked(),
            ocr_enabled=self.ocr_enabled.isChecked(),
            force_ocr=self.force_ocr.isChecked(),
            ocr_language=self.ocr_lang.text().strip() or "tur+eng",
            ocr_dpi=self.ocr_dpi.value(),
            tessdata_dir=self.tessdata.text().strip(),
            nbsp_to_space=self.nbsp.isChecked(),
        )
        return opts, self.output_dir.text().strip()

    def selected_language(self) -> str:
        return self.language.currentData()

    def _update_ocr_status(self):
        tessdata = ocr.find_tessdata(self.tessdata.text().strip())
        if tessdata is None:
            self.ocr_status.setText(t("set.ocr_missing", url=ocr.TESSERACT_DOWNLOAD_URL))
            return
        _, warnings = ocr.resolve_language(self.ocr_lang.text().strip(), tessdata)
        langs = ", ".join(sorted(ocr.available_languages(tessdata)))
        msg = t("set.ocr_found", path=tessdata, langs=langs)
        if warnings:
            msg += "<br>⚠ " + "<br>⚠ ".join(str(w) for w in warnings)
        self.ocr_status.setText(msg)

    def _pick_output_dir(self):
        d = QFileDialog.getExistingDirectory(self, t("set.pick_output"), self.output_dir.text())
        if d:
            self.output_dir.setText(d)

    def _pick_tessdata(self):
        d = QFileDialog.getExistingDirectory(self, t("set.pick_tessdata"))
        if d:
            self.tessdata.setText(d)


def _spin(lo: int, hi: int, value: int) -> QSpinBox:
    sb = QSpinBox()
    sb.setRange(lo, hi)
    sb.setValue(value)
    return sb


def _with_browse(edit: QLineEdit, handler) -> QWidget:
    w = QWidget()
    row = QHBoxLayout(w)
    row.setContentsMargins(0, 0, 0, 0)
    row.addWidget(edit)
    btn = QPushButton(t("set.browse"))
    btn.clicked.connect(handler)
    row.addWidget(btn)
    return w
