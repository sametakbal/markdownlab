# PyInstaller: pyinstaller build.spec  ->  dist/MarkdownLab/MarkdownLab.exe
# Optional, for scanned PDFs: put tur/eng .traineddata files into ./tessdata
# and they will be bundled with the application.
import shutil
from pathlib import Path
from PyInstaller.utils.hooks import collect_all, copy_metadata

datas, binaries, hiddenimports = [], [], []
for pkg in ("pymupdf", "pymupdf4llm", "pymupdf_layout", "mammoth", "mdit_py_plugins"):
    d, b, h = collect_all(pkg)
    datas += d; binaries += b; hiddenimports += h

# Ship the dist-info folders (with their license files) of every bundled
# third-party distribution, see THIRD_PARTY_NOTICES.md
for dist in ("PySide6", "PySide6_Essentials", "shiboken6", "pymupdf", "mammoth", "cobble",
             "markdownify", "beautifulsoup4", "soupsieve", "markdown-it-py", "mdit-py-plugins",
             "mdurl", "onnxruntime", "numpy", "lxml"):
    try:
        datas += copy_metadata(dist)
    except Exception as exc:
        print(f"WARNING: no metadata for {dist}: {exc}")

if Path("tessdata").is_dir():
    datas.append(("tessdata", "tessdata"))

a = Analysis(
    ["launcher.py"],
    pathex=["src"],
    datas=datas,
    binaries=binaries,
    hiddenimports=hiddenimports,
    excludes=["PySide6.QtWebEngineCore", "PySide6.QtWebEngineWidgets", "PySide6.QtPdf", "tkinter"],
)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name="MarkdownLab", console=False)
coll = COLLECT(exe, a.binaries, a.datas, name="MarkdownLab")

# License texts next to the exe, where users will see them
for notice in ("LICENSE", "THIRD_PARTY_NOTICES.md"):
    shutil.copy2(notice, Path(DISTPATH) / "MarkdownLab" / notice)
