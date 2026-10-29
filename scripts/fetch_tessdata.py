"""Download pinned Tesseract language data into ./tessdata.

build.spec bundles this folder, so the packaged app can OCR scanned PDFs
without a separate Tesseract installation. Files are verified by SHA-256.

    python scripts/fetch_tessdata.py [dest]
"""
from __future__ import annotations

import hashlib
import sys
import urllib.request
from pathlib import Path

# tessdata_best (LSTM, most accurate) at the 4.1.0 tag
BASE_URL = "https://github.com/tesseract-ocr/tessdata_best/raw/4.1.0/{lang}.traineddata"
FILES = {
    "tur": "e0c3338dc17503dc7d335a507c9ae01b2b46cfd07561171e1e1ac55d85e8e438",
    "eng": "8280aed0782fe27257a68ea10fe7ef324ca0f8d85bd2fd145d1c2b560bcb66ba",
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main(dest: str = "tessdata") -> int:
    out = Path(dest)
    out.mkdir(parents=True, exist_ok=True)
    for lang, expected in FILES.items():
        target = out / f"{lang}.traineddata"
        if target.is_file() and sha256(target) == expected:
            print(f"{target}: up to date")
            continue
        tmp = target.with_suffix(".part")
        print(f"Downloading {lang}.traineddata ...")
        urllib.request.urlretrieve(BASE_URL.format(lang=lang), tmp)
        actual = sha256(tmp)
        if actual != expected:
            tmp.unlink()
            print(f"SHA-256 mismatch for {lang}: {actual}", file=sys.stderr)
            return 1
        tmp.replace(target)
        print(f"{target}: ok")
    return 0


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:2]))
