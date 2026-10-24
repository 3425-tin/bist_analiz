# BIST Analiz

BIST 100 endeksi ve hisseleri için Streamlit arayüzlü analiz uygulaması.

## Kurulum ve çalıştırma

Gereken: **Python 3.11 veya üstü** (python.org). Windows'ta kurarken "Add Python to PATH" kutusunu işaretleyin.

- **Windows:** `baslat.bat` dosyasına çift tıklayın.
- **macOS / Linux:** terminalde `./baslat.sh` komutunu çalıştırın.

İlk açılışta sanal ortam (`.venv`) kurulur ve paketler yüklenir. Sonra tarayıcıda
`http://localhost:8501` açılır. Kapatmak için terminal penceresinde Ctrl+C'ye basın.

## İlk veri yüklemesi

Ana sayfadaki **"Veriyi güncelle"** butonuna basın ya da terminalden çalıştırın:

    .venv/bin/python -m src.data.pipeline --full       # macOS/Linux
    .venv\Scripts\python -m src.data.pipeline --full   # Windows

91 sembolün 10 yıllık verisi birkaç dakikada iner. Sonraki güncellemeler
artımlıdır, yani sadece son günleri çeker. Veriler `data/bist.db` (SQLite) dosyasında tutulur.

## Yapı

    app.py               Ana sayfa: veri durumu ve güncelleme
    pages/               5 portal (şimdilik boş)
    config.yaml          Tüm ayarlar, eşikler ve BIST 100 sembol listesi
    src/data/fetcher.py  yfinance ile toplu çekme ve tekrar deneme
    src/data/store.py    SQLite: daily_prices, weekly_prices, fetch_log
    src/data/resample.py Günlükten haftalığa dönüşüm (W-FRI)
    src/data/pipeline.py Güncelleme akışı ve kalite kontrolleri
    tests/               Birim testleri (pytest)
