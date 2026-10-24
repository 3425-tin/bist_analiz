"""yfinance ile toplu fiyat çekme."""
import logging
import time

import pandas as pd
import yfinance as yf

from .store import PRICE_COLUMNS

log = logging.getLogger(__name__)

YF_RENAME = {
    "Open": "open", "High": "high", "Low": "low",
    "Close": "close", "Adj Close": "adj_close", "Volume": "volume",
}


def _normalize(raw: pd.DataFrame) -> pd.DataFrame:
    df = raw.rename(columns=YF_RENAME)
    if "adj_close" not in df:
        df["adj_close"] = df["close"]
    df = df[PRICE_COLUMNS].dropna(how="all")
    idx = pd.DatetimeIndex(df.index)
    if idx.tz is not None:
        idx = idx.tz_localize(None)
    df.index = idx.normalize().rename("date")
    return df[~df.index.duplicated(keep="last")].sort_index()


def _download_batch(symbols: list[str], start: str, end: str | None,
                    auto_adjust: bool) -> dict[str, pd.DataFrame]:
    raw = yf.download(
        symbols, start=start, end=end, interval="1d",
        auto_adjust=auto_adjust, group_by="ticker",
        threads=True, progress=False,
    )
    out: dict[str, pd.DataFrame] = {}
    if raw is None or raw.empty:
        return out
    for sym in symbols:
        if isinstance(raw.columns, pd.MultiIndex):
            if sym not in raw.columns.get_level_values(0):
                continue
            part = raw[sym]
        else:
            part = raw
        df = _normalize(part)
        if not df.empty:
            out[sym] = df
    return out


def fetch_daily(symbols: list[str], start: str, end: str | None, fetch_cfg: dict,
                auto_adjust: bool = False) -> tuple[dict[str, pd.DataFrame], list[str]]:
    """Sembolleri parti parti çeker, boş dönenleri tekrar dener.

    Dönüş: ({sembol: günlük df}, başarısız semboller)
    """
    results: dict[str, pd.DataFrame] = {}
    batch_size = fetch_cfg["batch_size"]
    batches = [symbols[i:i + batch_size] for i in range(0, len(symbols), batch_size)]

    for n, batch in enumerate(batches, 1):
        pending = list(batch)
        for attempt in range(fetch_cfg["max_retries"] + 1):
            if not pending:
                break
            if attempt:
                wait = fetch_cfg["retry_wait_seconds"] * 2 ** (attempt - 1)
                log.info("Tekrar deneme %d (%d sembol), %ss bekleniyor", attempt, len(pending), wait)
                time.sleep(wait)
            try:
                got = _download_batch(pending, start, end, auto_adjust)
            except Exception as exc:  # ağ hataları: tekrar dene
                log.warning("Parti %d hata: %s", n, exc)
                got = {}
            results.update(got)
            pending = [s for s in pending if s not in got]
        log.info("Parti %d/%d tamam (%d başarılı)", n, len(batches), len(batch) - len(pending))
        time.sleep(fetch_cfg["pause_between_batches_seconds"])

    failed = [s for s in symbols if s not in results]
    return results, failed
