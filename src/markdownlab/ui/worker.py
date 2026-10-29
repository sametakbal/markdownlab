from __future__ import annotations

import threading
import traceback
from pathlib import Path

from PySide6.QtCore import QObject, QRunnable, Signal

from ..core.dispatcher import convert_file
from ..core.models import ConversionError, ConversionOptions


class WorkerSignals(QObject):
    started = Signal(int)
    finished = Signal(int, object)  # job_id, ConversionResult
    failed = Signal(int, object)  # job_id, Msg | str
    cancelled = Signal(int)


class ConversionTask(QRunnable):
    def __init__(self, job_id: int, path: Path, opts: ConversionOptions, workdir: Path,
                 cancel_event: threading.Event):
        super().__init__()
        self.job_id = job_id
        self.path = path
        self.opts = opts
        self.workdir = workdir
        self.cancel_event = cancel_event
        self.signals = WorkerSignals()

    def run(self):
        if self.cancel_event.is_set():
            self.signals.cancelled.emit(self.job_id)
            return
        self.signals.started.emit(self.job_id)
        try:
            result = convert_file(self.path, self.opts, self.workdir)
        except ConversionError as exc:
            self.signals.failed.emit(self.job_id, exc.args[0] if exc.args else str(exc))
        except Exception:
            self.signals.failed.emit(self.job_id, traceback.format_exc(limit=3))
        else:
            self.signals.finished.emit(self.job_id, result)
