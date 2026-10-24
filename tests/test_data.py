import pandas as pd
import pytest

from src.data.pipeline import quality_issues
from src.data.resample import daily_to_weekly
from src.data.store import PriceStore


def _daily(dates, closes):
    idx = pd.DatetimeIndex(pd.to_datetime(dates), name="date")
    c = pd.Series(closes, index=idx, dtype=float)
    return pd.DataFrame({"open": c - 1, "high": c + 2, "low": c - 2,
                         "close": c, "adj_close": c, "volume": 100.0})


def test_weekly_aggregation_and_holiday_label():
    # 2024-01-01 Pazartesi ... 2024-01-11 Perşembe (12 Cuma tatil varsayımı)
    dates = ["2024-01-01", "2024-01-02", "2024-01-03", "2024-01-04", "2024-01-05",
             "2024-01-08", "2024-01-09", "2024-01-10", "2024-01-11"]
    w = daily_to_weekly(_daily(dates, [10, 11, 12, 13, 14, 20, 21, 22, 23]))
    assert list(w.index.strftime("%Y-%m-%d")) == ["2024-01-05", "2024-01-11"]
    first = w.iloc[0]
    assert (first.open, first.high, first.low, first.close, first.volume) == (9, 16, 8, 14, 500)
    assert w.iloc[1].close == 23


def test_weekly_skips_empty_weeks():
    w = daily_to_weekly(_daily(["2024-01-02", "2024-01-16"], [1, 2]))
    assert len(w) == 2


def test_store_upsert_roundtrip(tmp_path):
    store = PriceStore(tmp_path / "t.db")
    df = _daily(["2024-01-02", "2024-01-03"], [10, 11])
    assert store.upsert("daily_prices", "THYAO.IS", df) == 2
    # Aynı tarihe yeniden yazınca güncellenmeli, çoğalmamalı
    store.upsert("daily_prices", "THYAO.IS", _daily(["2024-01-03"], [99]))
    out = store.load("daily_prices", "THYAO.IS")
    assert len(out) == 2 and out["close"].iloc[-1] == 99
    assert store.last_date("daily_prices", "THYAO.IS") == pd.Timestamp("2024-01-03")
    with pytest.raises(ValueError):
        store.load("bad_table", "X")


def test_quality_flags_jump():
    q = {"min_daily_rows": 1, "max_missing_close_ratio": 0.05, "max_daily_abs_return": 0.5}
    issues = quality_issues(_daily(["2024-01-02", "2024-01-03"], [10, 30]), q)
    assert any("sıçrama" in i for i in issues)
