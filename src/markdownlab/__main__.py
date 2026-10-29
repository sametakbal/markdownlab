from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from . import __copyright__, __license__, __version__, i18n
from .i18n import t


def _ensure_streams():
    # In a windowed (console-less) .exe sys.stdout is None; keep library prints from crashing
    for name in ("stdout", "stderr"):
        stream = getattr(sys, name)
        if stream is None:
            setattr(sys, name, open(os.devnull, "w", encoding="utf-8"))
        elif hasattr(stream, "reconfigure"):
            # The Windows console may be cp1252; don't crash when printing Turkish characters
            stream.reconfigure(encoding="utf-8", errors="replace")


def run_cli(files: list[str], output_dir: str, no_ocr: bool) -> int:
    import tempfile

    from .core.dispatcher import convert_file, default_output_path, save_result
    from .core.models import ConversionError, ConversionOptions

    opts = ConversionOptions(ocr_enabled=not no_ocr)
    status = 0
    with tempfile.TemporaryDirectory(prefix="markdownlab_") as tmp:
        for i, f in enumerate(files):
            src = Path(f)
            try:
                result = convert_file(src, opts, Path(tmp) / str(i))
            except ConversionError as exc:
                print(t("cli.error", src=src, exc=exc), file=sys.stderr)
                status = 1
                continue
            out = save_result(result, result.markdown, default_output_path(src, output_dir))
            print(t("cli.ok", src=src, out=out))
            for w in result.warnings:
                print(t("cli.warning", msg=w))
    return status


def main() -> int:
    _ensure_streams()
    # --lang is parsed first so that the help text is in the selected language
    pre = argparse.ArgumentParser(add_help=False)
    pre.add_argument("--lang", choices=sorted(i18n.LANGUAGES))
    lang = pre.parse_known_args()[0].lang
    i18n.set_language(lang or i18n.detect_system_language())

    parser = argparse.ArgumentParser(
        prog="markdownlab", description=t("cli.description"),
        formatter_class=argparse.RawDescriptionHelpFormatter,  # keep line breaks in --version
    )
    parser.add_argument("files", nargs="*", help=t("cli.files"))
    parser.add_argument("-o", "--output-dir", default="", help=t("cli.output_dir"))
    parser.add_argument("--no-ocr", action="store_true", help=t("cli.no_ocr"))
    parser.add_argument("--lang", choices=sorted(i18n.LANGUAGES), help=t("cli.lang"))
    version_text = (
        f"MarkdownLab {__version__}\n{__copyright__}\n"
        f"License: {__license__} <https://www.gnu.org/licenses/agpl-3.0.html>\n"
        "This program comes with ABSOLUTELY NO WARRANTY."
    )
    parser.add_argument("--version", action="version", version=version_text)
    args = parser.parse_args()

    if args.files:
        return run_cli(args.files, args.output_dir, args.no_ocr)

    from PySide6.QtWidgets import QApplication

    from .ui.main_window import MainWindow, apply_qt_translation
    from .ui.settings_dialog import load_language

    app = QApplication(sys.argv)
    app.setOrganizationName("MarkdownLab")
    app.setApplicationName("MarkdownLab")
    app.setStyle("Fusion")
    i18n.set_language(args.lang or load_language())
    apply_qt_translation(i18n.language())
    win = MainWindow()
    win.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
