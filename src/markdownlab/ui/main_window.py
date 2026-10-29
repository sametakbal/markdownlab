from __future__ import annotations

import itertools
import shutil
import tempfile
import threading
from dataclasses import dataclass, field
from pathlib import Path

from PySide6.QtCore import QLibraryInfo, QThreadPool, QTimer, QTranslator, QUrl, Qt
from PySide6.QtGui import QAction, QFont, QKeySequence
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QFileDialog,
    QHeaderView,
    QLabel,
    QListWidget,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QProgressBar,
    QSizePolicy,
    QSplitter,
    QTabWidget,
    QTextBrowser,
    QToolBar,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from .. import __copyright__, __version__, i18n
from ..core.dispatcher import SUPPORTED_EXTENSIONS, default_output_path, save_result
from ..core.models import ConversionResult
from ..i18n import Msg, t
from .preview import render_html
from .settings_dialog import (
    SettingsDialog,
    language_combo,
    load_settings,
    store_language,
    store_settings,
)
from .worker import ConversionTask

# Job states; their on-screen labels come from the "status.<state>" i18n keys
PENDING, QUEUED, RUNNING, DONE, FAILED, CANCELLED = (
    "pending", "queued", "running", "done", "failed", "cancelled",
)
CONVERTIBLE = (PENDING, FAILED, CANCELLED)

_qt_translator: QTranslator | None = None


def apply_qt_translation(lang: str) -> None:
    """Translate Qt's built-in texts (OK/Cancel, Yes/No…) to the selected language."""
    global _qt_translator
    app = QApplication.instance()
    if _qt_translator is not None:
        app.removeTranslator(_qt_translator)
        _qt_translator = None
    translator = QTranslator(app)
    if translator.load(f"qtbase_{lang}", QLibraryInfo.path(QLibraryInfo.TranslationsPath)):
        app.installTranslator(translator)
        _qt_translator = translator


@dataclass
class Job:
    id: int
    path: Path
    status: str = PENDING
    result: ConversionResult | None = None
    markdown: str = ""
    error: Msg | str = ""
    saved_to: Path | None = None
    item: QTreeWidgetItem | None = field(default=None, repr=False)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.resize(1280, 800)
        self.setAcceptDrops(True)

        self.opts, self.output_dir = load_settings()
        self.jobs: dict[int, Job] = {}
        self._ids = itertools.count(1)
        self._tmp = tempfile.TemporaryDirectory(prefix="markdownlab_")
        # PyMuPDF is not thread-safe: conversions run one at a time in the background
        self.pool = QThreadPool(self)
        self.pool.setMaxThreadCount(1)
        self._cancel = threading.Event()
        self._batch_total = 0
        self._batch_done = 0

        self._build_ui()
        self.retranslate()
        self._update_actions()

    # --- ui -----------------------------------------------------------------
    def _build_ui(self):
        self.toolbar = QToolBar()
        self.toolbar.setMovable(False)
        self.toolbar.setToolButtonStyle(Qt.ToolButtonTextOnly)
        self.addToolBar(self.toolbar)

        def act(slot, shortcut=None):
            a = QAction(self)
            a.triggered.connect(slot)
            if shortcut:
                a.setShortcut(shortcut)
            self.toolbar.addAction(a)
            return a

        self.act_add = act(self.add_files_dialog, QKeySequence.Open)
        self.act_remove = act(self.remove_selected, QKeySequence.Delete)
        self.toolbar.addSeparator()
        self.act_convert = act(self.convert_all, "F5")
        self.act_cancel = act(self.cancel)
        self.toolbar.addSeparator()
        self.act_save = act(self.save_current, QKeySequence.Save)
        self.act_save_as = act(self.save_current_as, QKeySequence.SaveAs)
        self.act_save_all = act(self.save_all, "Ctrl+Shift+A")
        self.toolbar.addSeparator()
        self.act_settings = act(self.open_settings)
        self.act_about = act(self.show_about)

        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.toolbar.addWidget(spacer)
        self.language_label = QLabel()
        self.language_label.setContentsMargins(0, 0, 6, 0)
        self.toolbar.addWidget(self.language_label)
        self.language_box = language_combo(i18n.language())
        self.language_box.currentIndexChanged.connect(
            lambda _: self.set_language(self.language_box.currentData())
        )
        self.toolbar.addWidget(self.language_box)

        self.files = QTreeWidget()
        self.files.setRootIsDecorated(False)
        self.files.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.files.setColumnCount(2)
        self.files.header().setSectionResizeMode(0, QHeaderView.Stretch)
        self.files.header().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.files.currentItemChanged.connect(lambda *_: self._show_current())
        self.files.itemSelectionChanged.connect(self._update_actions)

        self.hint = QLabel()
        self.hint.setWordWrap(True)
        self.hint.setStyleSheet("color: gray; padding: 4px;")
        left = QWidget()
        ll = QVBoxLayout(left)
        ll.setContentsMargins(0, 0, 0, 0)
        ll.addWidget(self.files)
        ll.addWidget(self.hint)

        self.editor = QPlainTextEdit()
        mono = QFont("Consolas")
        mono.setStyleHint(QFont.Monospace)
        mono.setPointSize(10)
        self.editor.setFont(mono)
        self.editor.setLineWrapMode(QPlainTextEdit.WidgetWidth)
        self.editor.textChanged.connect(self._on_edit)

        self.preview = QTextBrowser()
        self.preview.setOpenExternalLinks(True)

        self.tabs = QTabWidget()
        self.tabs.addTab(self.editor, "")
        self.tabs.addTab(self.preview, "")
        self.tabs.currentChanged.connect(lambda _: self._refresh_preview())

        self.warnings = QListWidget()
        self.warnings.setWordWrap(True)
        self.warnings.setMaximumHeight(110)

        right = QSplitter(Qt.Vertical)
        right.addWidget(self.tabs)
        right.addWidget(self.warnings)
        right.setStretchFactor(0, 1)

        split = QSplitter(Qt.Horizontal)
        split.addWidget(left)
        split.addWidget(right)
        split.setSizes([330, 950])
        self.setCentralWidget(split)

        self.progress = QProgressBar()
        self.progress.setMaximumWidth(240)
        self.progress.setVisible(False)
        self.statusBar().addPermanentWidget(self.progress)

        self._preview_timer = QTimer(self, singleShot=True, interval=300)
        self._preview_timer.timeout.connect(self._refresh_preview)
        self._loading_editor = False

    # --- language -----------------------------------------------------------
    def set_language(self, lang: str):
        if lang == i18n.language():
            return
        i18n.set_language(lang)
        store_language(lang)
        apply_qt_translation(lang)
        self.statusBar().clearMessage()  # drop transient messages in the previous language
        self.retranslate()

    def retranslate(self):
        self.setWindowTitle(f"{t('app.title')}  v{__version__}")
        self.toolbar.setWindowTitle(t("toolbar"))
        for action, key in (
            (self.act_add, "act.add"), (self.act_remove, "act.remove"),
            (self.act_convert, "act.convert"), (self.act_cancel, "act.cancel"),
            (self.act_save, "act.save"), (self.act_save_as, "act.save_as"),
            (self.act_save_all, "act.save_all"), (self.act_settings, "act.settings"),
            (self.act_about, "act.about"),
        ):
            action.setText(t(key))
        self.language_label.setText(t("language"))
        self.language_box.blockSignals(True)
        self.language_box.setCurrentIndex(self.language_box.findData(i18n.language()))
        self.language_box.blockSignals(False)
        self.files.setHeaderLabels([t("col.file"), t("col.status")])
        self.hint.setText(t("drop_hint"))
        self.editor.setPlaceholderText(t("editor.placeholder"))
        self.tabs.setTabText(0, t("tab.markdown"))
        self.tabs.setTabText(1, t("tab.preview"))
        for job in self.jobs.values():
            self._set_status(job, job.status)
        self._show_messages(self._current_job())

    # --- adding files -------------------------------------------------------
    def dragEnterEvent(self, event):
        if any(self._expand(Path(u.toLocalFile())) for u in event.mimeData().urls()):
            event.acceptProposedAction()

    def dropEvent(self, event):
        paths = [p for u in event.mimeData().urls() for p in self._expand(Path(u.toLocalFile()))]
        self.add_files(paths)

    @staticmethod
    def _expand(path: Path) -> list[Path]:
        if path.is_dir():
            return sorted(p for p in path.rglob("*")
                          if p.suffix.lower() in SUPPORTED_EXTENSIONS and not p.name.startswith("~$"))
        if path.suffix.lower() in SUPPORTED_EXTENSIONS:
            return [path]
        return []

    def add_files_dialog(self):
        files, _ = QFileDialog.getOpenFileNames(self, t("dlg.open"), "", t("dlg.open_filter"))
        self.add_files([Path(f) for f in files])

    def add_files(self, paths: list[Path]):
        known = {j.path.resolve() for j in self.jobs.values()}
        first_new = None
        for p in paths:
            if p.resolve() in known:
                continue
            job = Job(next(self._ids), p)
            job.item = QTreeWidgetItem([p.name, ""])
            job.item.setToolTip(0, str(p))
            job.item.setData(0, Qt.UserRole, job.id)
            self._set_status(job, PENDING)
            self.files.addTopLevelItem(job.item)
            self.jobs[job.id] = job
            known.add(p.resolve())
            first_new = first_new or job
        if first_new and self.files.currentItem() is None:
            self.files.setCurrentItem(first_new.item)
        self._update_actions()

    def remove_selected(self):
        for item in self.files.selectedItems():
            job = self.jobs[item.data(0, Qt.UserRole)]
            if job.status in (QUEUED, RUNNING):
                continue
            self.files.takeTopLevelItem(self.files.indexOfTopLevelItem(item))
            del self.jobs[job.id]
        self._show_current()
        self._update_actions()

    # --- conversion ---------------------------------------------------------
    def convert_all(self):
        todo = [j for j in self.jobs.values() if j.status in CONVERTIBLE]
        selected = [self.jobs[i.data(0, Qt.UserRole)] for i in self.files.selectedItems()]
        # allow re-converting finished files that are selected
        todo += [j for j in selected if j.status == DONE and j not in todo]
        if not todo:
            return
        self._cancel = threading.Event()
        self._batch_total += len(todo)
        self.progress.setRange(0, self._batch_total)
        self.progress.setValue(self._batch_done)
        self.progress.setVisible(True)
        for job in todo:
            workdir = Path(self._tmp.name) / str(job.id)
            shutil.rmtree(workdir, ignore_errors=True)
            job.error = ""
            self._set_status(job, QUEUED)
            task = ConversionTask(job.id, job.path, self.opts, workdir, self._cancel)
            task.signals.started.connect(self._on_started)
            task.signals.finished.connect(self._on_finished)
            task.signals.failed.connect(self._on_failed)
            task.signals.cancelled.connect(self._on_cancelled)
            self.pool.start(task)
        self._show_current()

    def cancel(self):
        self._cancel.set()
        self.statusBar().showMessage(t("msg.cancelling"), 3000)

    def _on_started(self, job_id: int):
        job = self.jobs.get(job_id)
        if job:
            self._set_status(job, RUNNING)
            self.statusBar().showMessage(t("msg.converting", name=job.path.name))
        self._update_actions()

    def _on_finished(self, job_id: int, result: ConversionResult):
        job = self.jobs.get(job_id)
        if job:
            job.result, job.markdown, job.saved_to = result, result.markdown, None
            self._set_status(job, DONE)
            self._refresh_if_current(job)
        self._step()

    def _on_failed(self, job_id: int, message):
        job = self.jobs.get(job_id)
        if job:
            job.error = message
            self._set_status(job, FAILED)
            self._refresh_if_current(job)
        self._step()

    def _on_cancelled(self, job_id: int):
        job = self.jobs.get(job_id)
        if job:
            self._set_status(job, CANCELLED)
            self._refresh_if_current(job)
        self._step()

    def _refresh_if_current(self, job: Job):
        if self.files.currentItem() is job.item:
            self._show_current()

    def _step(self):
        self._batch_done += 1
        self.progress.setValue(self._batch_done)
        if self._batch_done >= self._batch_total:
            self.progress.setVisible(False)
            self._batch_done = self._batch_total = 0
            ok = sum(j.status == DONE for j in self.jobs.values())
            self.statusBar().showMessage(t("msg.batch_done", ok=ok, total=len(self.jobs)), 6000)
        self._update_actions()

    def _set_status(self, job: Job, status: str):
        job.status = status
        if status == DONE and job.result and job.result.warnings:
            label = t("status.done_warnings", n=len(job.result.warnings))
        else:
            label = t(f"status.{status}")
        job.item.setText(1, label)
        job.item.setToolTip(1, str(job.error) if status == FAILED else "")
        color = {DONE: Qt.darkGreen, FAILED: Qt.red}.get(status)
        if color is None:
            job.item.setData(1, Qt.ForegroundRole, None)  # the theme's default color
        else:
            job.item.setForeground(1, color)

    # --- viewing / editing --------------------------------------------------
    def _current_job(self) -> Job | None:
        item = self.files.currentItem()
        return self.jobs.get(item.data(0, Qt.UserRole)) if item else None

    def _show_current(self):
        job = self._current_job()
        self._loading_editor = True
        if job is not None and job.status == DONE:
            self.editor.setPlainText(job.markdown)
        else:
            self.editor.clear()
        self.editor.setReadOnly(job is None or job.status != DONE)
        self._loading_editor = False
        self._show_messages(job)
        self._refresh_preview()
        self._update_actions()

    def _show_messages(self, job: Job | None):
        self.warnings.clear()
        if job is None:
            return
        if job.status == DONE:
            for w in job.result.warnings:
                self.warnings.addItem("⚠ " + str(w))
            if job.saved_to:
                self.warnings.addItem(t("msg.saved", path=job.saved_to))
        elif job.status == FAILED:
            self.warnings.addItem("✖ " + str(job.error))

    def _on_edit(self):
        if self._loading_editor:
            return
        job = self._current_job()
        if job and job.status == DONE:
            job.markdown = self.editor.toPlainText()
            self._preview_timer.start()

    def _refresh_preview(self):
        if self.tabs.currentWidget() is not self.preview:
            return
        job = self._current_job()
        if not job or job.status != DONE:
            self.preview.clear()
            return
        workdir = str(job.result.workdir)
        self.preview.setSearchPaths([workdir])
        self.preview.document().setBaseUrl(QUrl.fromLocalFile(workdir + "/"))
        scroll = self.preview.verticalScrollBar().value()
        self.preview.setHtml(render_html(job.markdown))
        self.preview.verticalScrollBar().setValue(scroll)

    # --- saving -------------------------------------------------------------
    def save_current(self):
        job = self._current_job()
        if job and job.status == DONE:
            target = job.saved_to or default_output_path(job.path, self.output_dir)
            if self._confirm_overwrite([target]):
                self._save(job, target)

    def save_current_as(self):
        job = self._current_job()
        if not (job and job.status == DONE):
            return
        suggested = str(job.saved_to or default_output_path(job.path, self.output_dir))
        target, _ = QFileDialog.getSaveFileName(self, t("dlg.save_as"), suggested, "Markdown (*.md)")
        if target:  # the file dialog already asks before overwriting
            self._save(job, Path(target))

    def save_all(self):
        done = [j for j in self.jobs.values() if j.status == DONE]
        targets = [j.saved_to or default_output_path(j.path, self.output_dir) for j in done]
        if not done or not self._confirm_overwrite(targets):
            return
        for job, target in zip(done, targets):
            self._save(job, target)
        self.statusBar().showMessage(t("msg.saved_n", n=len(done)), 6000)

    def _save(self, job: Job, target: Path):
        try:
            job.saved_to = save_result(job.result, job.markdown, target)
        except OSError as exc:
            QMessageBox.critical(self, t("dlg.save_failed"), f"{target}\n\n{exc}")
            return
        job.item.setToolTip(0, f"{job.path}\n→ {job.saved_to}")
        self.statusBar().showMessage(t("msg.saved", path=job.saved_to), 6000)
        if job is self._current_job():
            self._show_messages(job)

    def _confirm_overwrite(self, targets: list[Path]) -> bool:
        existing = [p for p in targets if p.exists()]
        if not existing:
            return True
        names = "\n".join(str(p) for p in existing[:10])
        more = t("dlg.overwrite.more", n=len(existing) - 10) if len(existing) > 10 else ""
        answer = QMessageBox.question(
            self, t("dlg.overwrite.title"), t("dlg.overwrite.body", names=names, more=more)
        )
        return answer == QMessageBox.Yes

    # --- settings -----------------------------------------------------------
    def open_settings(self):
        dlg = SettingsDialog(self.opts, self.output_dir, self)
        if dlg.exec():
            self.opts, self.output_dir = dlg.values()
            store_settings(self.opts, self.output_dir)
            self.set_language(dlg.selected_language())
            self.statusBar().showMessage(t("msg.settings_saved"), 5000)

    def show_about(self):
        # AGPL §5(d): interactive UIs must show the license and warranty notice
        box = QMessageBox(self)
        box.setWindowTitle(t("about.title"))
        box.setTextFormat(Qt.RichText)
        box.setText(t("about.body", version=__version__, copyright=__copyright__))
        label = box.findChild(QLabel, "qt_msgbox_label")
        if label is not None:
            label.setOpenExternalLinks(True)
        box.exec()

    def _update_actions(self):
        job = self._current_job()
        busy = self._batch_total > 0
        has_pending = any(j.status in CONVERTIBLE for j in self.jobs.values())
        selected_done = any(self.jobs[i.data(0, Qt.UserRole)].status == DONE for i in self.files.selectedItems())
        self.act_convert.setEnabled(has_pending or selected_done)
        self.act_cancel.setEnabled(busy)
        self.act_remove.setEnabled(bool(self.files.selectedItems()))
        can_save = bool(job and job.status == DONE)
        self.act_save.setEnabled(can_save)
        self.act_save_as.setEnabled(can_save)
        self.act_save_all.setEnabled(any(j.status == DONE for j in self.jobs.values()))

    def closeEvent(self, event):
        unsaved = [j for j in self.jobs.values() if j.status == DONE and j.saved_to is None]
        if unsaved:
            answer = QMessageBox.question(
                self, t("dlg.unsaved.title"), t("dlg.unsaved.body", n=len(unsaved))
            )
            if answer != QMessageBox.Yes:
                event.ignore()
                return
        self._cancel.set()
        self.pool.waitForDone(5000)
        self._tmp.cleanup()
        super().closeEvent(event)
