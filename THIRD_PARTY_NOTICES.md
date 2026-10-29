# Third-party notices / Üçüncü taraf bildirimleri

MarkdownLab is licensed under the GNU Affero General Public License v3.0 or later
(see [LICENSE](LICENSE)). The Windows package distributed on the Releases page
bundles the following third-party components, each under its own license.

MarkdownLab, GNU Affero Genel Kamu Lisansı v3.0 veya sonraki bir sürümü ile
lisanslanmıştır ([LICENSE](LICENSE)). Releases sayfasındaki Windows paketi,
her biri kendi lisansına tabi olan aşağıdaki üçüncü taraf bileşenleri içerir.

| Component | License | Source |
| --- | --- | --- |
| PyMuPDF / MuPDF (incl. pymupdf4llm and layout code) | AGPL-3.0 (or Artifex commercial license) | <https://github.com/pymupdf/PyMuPDF> |
| Tesseract OCR engine (embedded in MuPDF) | Apache-2.0 | <https://github.com/tesseract-ocr/tesseract> |
| Tesseract language data `tur`, `eng` (tessdata_best 4.1.0) | Apache-2.0 | <https://github.com/tesseract-ocr/tessdata_best> |
| Qt 6 / PySide6 / Shiboken6 | LGPL-3.0 | <https://www.qt.io/> · <https://code.qt.io/cgit/pyside/pyside-setup.git> |
| mammoth | BSD-2-Clause | <https://github.com/mwilliamson/python-mammoth> |
| cobble | BSD-2-Clause | <https://github.com/mwilliamson/python-cobble> |
| markdownify | MIT | <https://github.com/matthewwithanm/python-markdownify> |
| Beautiful Soup 4 | MIT | <https://www.crummy.com/software/BeautifulSoup/> |
| soupsieve | MIT | <https://github.com/facelessuser/soupsieve> |
| markdown-it-py | MIT | <https://github.com/executablebooks/markdown-it-py> |
| mdit-py-plugins | MIT | <https://github.com/executablebooks/mdit-py-plugins> |
| mdurl | MIT | <https://github.com/executablebooks/mdurl> |
| lxml | BSD-3-Clause | <https://lxml.de/> |
| ONNX Runtime | MIT | <https://github.com/microsoft/onnxruntime> |
| NumPy | BSD-3-Clause (and bundled permissive licenses) | <https://numpy.org/> |
| Python | PSF License | <https://www.python.org/> |
| PyInstaller bootloader | GPL-2.0-or-later with bootloader exception | <https://pyinstaller.org/> |

## Qt / PySide6 (LGPL-3.0)

The Qt and PySide6 libraries are included as separate, unmodified dynamic
libraries in the `_internal` folder of the package. Under the LGPL you may
replace them with your own compatible build. Their source code is available
from the links above.

Qt ve PySide6 kütüphaneleri paketin `_internal` klasöründe ayrı ve
değiştirilmemiş dinamik kütüphaneler olarak bulunur. LGPL kapsamında bunları
kendi uyumlu derlemenizle değiştirebilirsiniz.

The full license texts of the bundled Python packages are included in their
`*.dist-info` folders inside `_internal`.

Paketlenen Python bileşenlerinin tam lisans metinleri `_internal` içindeki
`*.dist-info` klasörlerinde yer alır.
