"""BIST Analiz - ana sayfa. Çalıştırma: streamlit run app.py"""
import streamlit as st

from src.config import db_path, load_config
from src.data.pipeline import update
from src.data.store import PriceStore

st.set_page_config(page_title="BIST Analiz", layout="wide")
st.title("BIST Analiz")

cfg = load_config()
store = PriceStore(db_path(cfg))

st.subheader("Veri durumu")
summary = store.summary()
if summary.empty:
    st.warning("Veritabanı boş. Aşağıdaki butonla ilk yüklemeyi yapın "
               "(ya da terminalde: `python -m src.data.pipeline --full`).")
else:
    c1, c2, c3 = st.columns(3)
    c1.metric("Sembol", len(summary))
    c2.metric("Son tarih", summary["last_date"].max())
    c3.metric("Günlük satır", f"{summary['daily_rows'].sum():,}")
    st.dataframe(summary, use_container_width=True, hide_index=True)

if st.button("Veriyi güncelle"):
    with st.spinner("yfinance'tan veri çekiliyor..."):
        report = update(store=store)
    st.success(f"{len(report.updated)} sembol güncellendi, {len(report.failed)} başarısız.")
    if report.failed:
        st.error("Başarısız: " + ", ".join(report.failed))
    for sym, issues in report.warnings.items():
        st.caption(f"⚠️ {sym}: {'; '.join(issues)}")
