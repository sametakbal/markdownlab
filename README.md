# MarkdownLab

**[Türkçe](#türkçe) · [English](#english)**

---

## Türkçe

PDF ve DOCX dosyalarını **karakterleri ve biçimi bozmadan** Markdown'a çeviren masaüstü uygulaması. Arayüz **Türkçe ve İngilizce** kullanılabilir.

### İndirme

En son sürümü **[Releases](../../releases/latest)** sayfasından indirin:

1. `MarkdownLab-<sürüm>-windows-x64.zip` dosyasını indirin.
2. Zip'e sağ tıklayıp **Tümünü ayıkla** ile bir klasöre çıkarın.
3. Çıkan klasördeki `MarkdownLab\MarkdownLab.exe` dosyasını çalıştırın.

**Gereksinimler:** Windows 10 veya 11, 64-bit.

> **Önemli:** `MarkdownLab.exe`, yanındaki `_internal` klasörü olmadan çalışmaz. Exe'yi zip'in içinden çift tıklayarak açmayın ve tek başına başka bir yere taşımayın; klasörü bütün olarak kullanın. Masaüstünden açmak isterseniz exe'ye sağ tıklayıp kısayol oluşturun.

Kurulum veya Python gerekmez; Python ve gereken tüm kütüphaneler pakete dahildir. Türkçe ve İngilizce OCR dil dosyaları pakete dahildir; taranmış PDF'ler için Tesseract kurmanız gerekmez. İsterseniz indirdiğiniz dosyayı `.sha256` dosyasındaki özetle doğrulayabilirsiniz: `Get-FileHash MarkdownLab-*.zip`.

Not: Paket imzasız olduğu için Windows SmartScreen ilk açılışta uyarı gösterebilir; **Ek bilgi → Yine de çalıştır** ile açabilirsiniz.

### Özellikler

- Başlıklar, kalın / italik / altı çizili / üstü çizili, iç içe listeler, dipnotlar
- Tablolar (birleşik hücreli tablolar bilgi kaybı olmasın diye HTML olarak korunur)
- Görseller `<ad>_assets/` klasörüne çıkarılır
- Taranmış veya bozuk font kodlamalı PDF sayfalarında otomatik OCR (Tesseract, `tur+eng`)
- UTF-8 (BOM'suz), Unicode NFC, ligatür (ﬁ→fi) ve yumuşak tire düzeltmeleri; büyük/küçük harf dönüşümü yapılmaz (İ/ı güvenli)
- Toplu dönüşüm, sürükle-bırak, düzenlenebilir Markdown kaynağı ve canlı önizleme

### Kaynaktan kurulum

```bat
python -m venv .venv
.venv\Scripts\pip install -e .[dev]
```

### Kullanım

- **Arayüz:** `.venv\Scripts\python -m markdownlab` — dosyaları sürükleyip bırakın, **Tümünü Dönüştür** (F5), sonucu düzenleyin / önizleyin, **Kaydet**.
- **Komut satırı:** `python -m markdownlab belge.pdf rapor.docx -o cikti\`

### Dil seçimi

- İlk açılışta uygulama sistem dilini kullanır (Türkçe sistemde Türkçe, diğerlerinde İngilizce).
- Dili araç çubuğunun sağındaki **Dil** kutusundan veya **Ayarlar → Arayüz dili**'nden değiştirebilirsiniz. Değişiklik yeniden başlatmadan uygulanır ve hatırlanır; mevcut dönüşümlerin uyarıları da yeni dile çevrilir.
- Komut satırında: `python -m markdownlab --lang tr ...` veya `--lang en`. `--lang` arayüzü açarken de kullanılabilir (kayıtlı tercihi değiştirmez).

Not: dil seçimi yalnızca uygulamanın kendi metinlerini etkiler; dönüştürülen belgenin içeriği olduğu gibi korunur.

### OCR (taranmış PDF'ler)

Releases sayfasındaki paket Türkçe ve İngilizce dil dosyalarını içerir, ek bir şey gerekmez. Kaynaktan çalıştırırken `python scripts/fetch_tessdata.py` ile dil dosyalarını `tessdata\` klasörüne indirip `TESSDATA_PREFIX` değişkenini bu klasöre ayarlayın, ya da [Tesseract](https://github.com/UB-Mannheim/tesseract/wiki) kurun ve kurulumda **Turkish** dil paketini seçin. Uygulama `tessdata` klasörünü otomatik bulur; bulamazsa **Ayarlar**'dan gösterin. Yalnızca `tur.traineddata` / `eng.traineddata` dosyaları yeterlidir. OCR dilleri Ayarlar'daki **Diller** alanından değiştirilebilir (ör. `tur+eng`, `eng`).

### Paketleme

```bat
.venv\Scripts\pyinstaller --noconfirm build.spec   # dist\MarkdownLab\MarkdownLab.exe
```

Proje kökünde bir `tessdata\` klasörü varsa (`python scripts/fetch_tessdata.py` ile oluşturulur) OCR dil dosyaları pakete dahil edilir. Paketi denemek için: `python scripts/smoke_test.py dist\MarkdownLab\MarkdownLab.exe`.

### Sürüm yayınlama

Yayınlar GitHub Actions ile otomatik oluşturulur ([.github/workflows/release.yml](.github/workflows/release.yml)):

1. `src/markdownlab/__init__.py` içindeki `__version__` değerini artırın (ör. `0.2.0`) ve commit'leyin.
2. Aynı sürümle bir etiket oluşturup gönderin:

   ```bat
   git tag v0.2.0
   git push origin v0.2.0
   ```

3. İş akışı testleri (OCR dahil) çalıştırır, `.exe`'yi derler, paketi dener ve `MarkdownLab-0.2.0-windows-x64.zip` ile `.sha256` dosyasını yeni bir GitHub Release'e ekler. Sürüm notları commit'lerden otomatik üretilir.

Etiket `__version__` ile eşleşmezse iş akışı durur. **Actions → Release → Run workflow** ile elle çalıştırıldığında yayın oluşturmaz, yalnızca paketi iş akışı çıktısı (artifact) olarak yükler. Her push ve pull request'te testler ayrıca [ci.yml](.github/workflows/ci.yml) ile çalışır.

### Geliştirme

- Test: `.venv\Scripts\python -m pytest`
- Yeni bir metin eklerken `src/markdownlab/i18n.py` içindeki `STRINGS` sözlüğüne hem `tr` hem `en` karşılığını ekleyin ve kodda `t("anahtar")` kullanın. Testler her anahtarın iki dilde de bulunduğunu ve `{yer_tutucu}`ların eşleştiğini denetler.

### Lisans

MarkdownLab, [GNU Affero Genel Kamu Lisansı v3.0 veya sonraki bir sürümü](LICENSE) (AGPL-3.0-or-later) ile lisanslanmış özgür yazılımdır. Kullandığı PyMuPDF/MuPDF kütüphanesi de AGPL-3.0 lisanslıdır. Programı değiştirip dağıtırsanız (ağ üzerinden hizmet olarak sunmak dahil), değiştirdiğiniz kaynak kodunu da aynı lisansla paylaşmanız gerekir. Pakete dahil üçüncü taraf bileşenler ve lisansları [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) dosyasında listelenmiştir.

---

## English

A desktop application that converts PDF and DOCX files to Markdown **without breaking characters or formatting**. The interface is available in **English and Turkish**.

### Download

Get the latest version from the **[Releases](../../releases/latest)** page:

1. Download `MarkdownLab-<version>-windows-x64.zip`.
2. Right-click the zip and choose **Extract All** to extract it to a folder.
3. Run `MarkdownLab\MarkdownLab.exe` from the extracted folder.

**Requirements:** Windows 10 or 11, 64-bit.

> **Important:** `MarkdownLab.exe` does not work without the `_internal` folder next to it. Don't open the exe by double-clicking it inside the zip, and don't move it elsewhere on its own; keep the folder together. To start it from the desktop, right-click the exe and create a shortcut.

No installation or Python required; Python and all needed libraries are bundled. Turkish and English OCR language data are bundled, so scanned PDFs work without installing Tesseract. You can verify the download against the `.sha256` file: `Get-FileHash MarkdownLab-*.zip`.

Note: the package is unsigned, so Windows SmartScreen may warn on first launch; choose **More info → Run anyway**.

### Features

- Headings, bold / italic / underline / strikethrough, nested lists, footnotes
- Tables (tables with merged cells are kept as HTML so no information is lost)
- Images are extracted into a `<name>_assets/` folder
- Automatic OCR for scanned or badly encoded PDF pages (Tesseract, `tur+eng`)
- UTF-8 (no BOM), Unicode NFC, ligature (ﬁ→fi) and soft-hyphen fixes; no case conversion is ever applied (safe for Turkish İ/ı)
- Batch conversion, drag and drop, editable Markdown source and live preview

### Install from source

```bat
python -m venv .venv
.venv\Scripts\pip install -e .[dev]
```

### Usage

- **GUI:** `.venv\Scripts\python -m markdownlab` — drag files in, **Convert All** (F5), edit / preview the result, **Save**.
- **Command line:** `python -m markdownlab document.pdf report.docx -o output\`

### Language

- On first launch the app follows the system language (Turkish on a Turkish system, English otherwise).
- Change it from the **Language** box on the right of the toolbar or in **Settings → Interface language**. The change applies immediately without a restart and is remembered; warnings of existing conversions are translated too.
- On the command line: `python -m markdownlab --lang en ...` or `--lang tr`. `--lang` also works when opening the GUI (it does not change the saved preference).

Note: the language setting only affects the application's own text; the content of converted documents is preserved as is.

### OCR (scanned PDFs)

The package on the Releases page includes Turkish and English language data; nothing else is needed. When running from source, either download the language files into `tessdata\` with `python scripts/fetch_tessdata.py` and point `TESSDATA_PREFIX` at that folder, or install [Tesseract](https://github.com/UB-Mannheim/tesseract/wiki) and select the language packs you need (e.g. **Turkish**) during setup. The app finds the `tessdata` folder automatically; if it cannot, point to it in **Settings**. Only the `*.traineddata` files (e.g. `tur.traineddata`, `eng.traineddata`) are required. OCR languages can be changed in the **Languages** field in Settings (e.g. `tur+eng`, `eng`).

### Packaging

```bat
.venv\Scripts\pyinstaller --noconfirm build.spec   # dist\MarkdownLab\MarkdownLab.exe
```

If a `tessdata\` folder exists in the project root (created by `python scripts/fetch_tessdata.py`), the OCR language files are bundled. To try the package: `python scripts/smoke_test.py dist\MarkdownLab\MarkdownLab.exe`.

### Releasing

Releases are built automatically by GitHub Actions ([.github/workflows/release.yml](.github/workflows/release.yml)):

1. Bump `__version__` in `src/markdownlab/__init__.py` (e.g. `0.2.0`) and commit.
2. Create and push a tag with the same version:

   ```bat
   git tag v0.2.0
   git push origin v0.2.0
   ```

3. The workflow runs the tests (including OCR), builds the `.exe`, smoke-tests it, and attaches `MarkdownLab-0.2.0-windows-x64.zip` and its `.sha256` to a new GitHub Release. Release notes are generated from the commits.

The workflow stops if the tag does not match `__version__`. Running it manually via **Actions → Release → Run workflow** does not publish a release; it only uploads the package as a workflow artifact. Tests also run on every push and pull request via [ci.yml](.github/workflows/ci.yml).

### Development

- Tests: `.venv\Scripts\python -m pytest`
- When adding new text, add both `tr` and `en` entries to the `STRINGS` dictionary in `src/markdownlab/i18n.py` and use `t("key")` in code. The tests check that every key exists in both languages and that `{placeholders}` match.

### License

MarkdownLab is free software licensed under the [GNU Affero General Public License v3.0 or later](LICENSE) (AGPL-3.0-or-later). The PyMuPDF/MuPDF library it uses is also AGPL-3.0 licensed. If you modify and distribute the program (including offering it as a network service), you must share your modified source code under the same license. Bundled third-party components and their licenses are listed in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
