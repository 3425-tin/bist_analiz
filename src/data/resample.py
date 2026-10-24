"""Günlük OHLCV verisinden haftalık mum üretimi."""
import pandas as pd

from .store import PRICE_COLUMNS

AGG = {
    "open": "first",
    "high": "max",
    "low": "min",
    "close": "last",
    "adj_close": "last",
    "volume": "sum",
}


def daily_to_weekly(daily: pd.DataFrame, rule: str = "W-FRI") -> pd.DataFrame:
    """Haftalık mumlar; tarih etiketi haftanın son *işlem* günüdür.

    Tatil yüzünden Cuma işlem yoksa etiket Perşembe vb. olur. İşlem günü
    olmayan haftalar atılır.
    """
    if daily.empty:
        return daily.reindex(columns=PRICE_COLUMNS)
    df = daily[PRICE_COLUMNS].dropna(subset=["close"]).sort_index()
    grouped = df.groupby(pd.Grouper(freq=rule))
    weekly = grouped.agg(AGG)
    weekly["_last_day"] = grouped.apply(lambda g: g.index.max() if len(g) else pd.NaT)
    weekly = weekly.dropna(subset=["_last_day"])
    weekly.index = pd.DatetimeIndex(weekly.pop("_last_day"), name="date")
    return weekly[PRICE_COLUMNS]
