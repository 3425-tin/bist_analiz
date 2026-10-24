"""Veri güncelleme akışı: çek -> kalite kontrol -> günlük kaydet -> haftalık üret.

Kullanım:
    python -m src.data.pipeline            # artımlı güncelleme
    python -m src.data.pipeline --full     # 10 yılı baştan çek
    python -m src.data.pipeline --tickers THYAO GARAN
"""
import argparse
import logging
from dataclasses import dataclass, field

import pandas as pd

from src.config import db_path, load_config

from .fetcher import fetch_daily
from .resample import daily_to_weekly
from .store import PriceStore

log = logging.getLogger(__name__)


@dataclass
class UpdateReport:
    updated: dict[str, int] = field(default_factory=dict)  # sembol -> yeni/güncel günlük satır
    failed: list[str] = field(default_factory=list)
    warnings: dict[str, list[str]] = field(default_factory=dict)


def all_symbols(cfg: dict) -> list[str]:
    suffix = cfg["data"]["ticker_suffix"]
    return [cfg["data"]["index_ticker"]] + [t + suffix for t in cfg["bist100_tickers"]]


def quality_issues(df: pd.DataFrame, q: dict) -> list[str]:
    issues = []
    if len(df) < q["min_daily_rows"]:
        issues.append(f"az satır ({len(df)} < {q['min_daily_rows']})")
    missing = df["close"].isna().mean() if len(df) else 0.0
    if missing > q["max_missing_close_ratio"]:
        issues.append(f"kapanış eksik oranı %{missing:.1%}")
    ret = df["adj_close"].pct_change().abs()
    jumps = ret[ret > q["max_daily_abs_return"]]
    if not jumps.empty:
        days = ", ".join(d.strftime("%Y-%m-%d") for d in jumps.index[:5])
        issues.append(f"{len(jumps)} şüpheli sıçrama (> %{q['max_daily_abs_return']:.0%}): {days}")
    return issues


def update(full: bool = False, tickers: list[str] | None = None,
           cfg: dict | None = None, store: PriceStore | None = None) -> UpdateReport:
    cfg = cfg or load_config()
    store = store or PriceStore(db_path(cfg))
    d, f = cfg["data"], cfg["fetch"]
    symbols = ([t if t.endswith(d["ticker_suffix"]) or t.startswith("^") else t + d["ticker_suffix"]
                for t in tickers] if tickers else all_symbols(cfg))

    default_start = pd.Timestamp.today().normalize() - pd.DateOffset(years=d["history_years"])
    # Başlangıç tarihine göre grupla ki aynı aralıktaki semboller tek istekte gitsin.
    groups: dict[str, list[str]] = {}
    for sym in symbols:
        last = None if full else store.last_date("daily_prices", sym)
        start = default_start if last is None else last - pd.Timedelta(days=f["incremental_overlap_days"])
        groups.setdefault(start.strftime("%Y-%m-%d"), []).append(sym)

    report = UpdateReport()
    for start, syms in groups.items():
        log.info("%d sembol, başlangıç %s", len(syms), start)
        data, failed = fetch_daily(syms, start, None, f, auto_adjust=d["auto_adjust"])
        for sym in failed:
            store.log_fetch(sym, "empty", 0, "yfinance veri döndürmedi")
        report.failed.extend(failed)

        for sym, new in data.items():
            n = store.upsert("daily_prices", sym, new)
            daily = store.load("daily_prices", sym)
            # Haftalık tabloyu tamamen yeniden üret (ucuz ve tutarlı).
            store.upsert("weekly_prices", sym, daily_to_weekly(daily, d["weekly_rule"]))
            issues = quality_issues(daily, cfg["quality"])
            if issues:
                report.warnings[sym] = issues
            store.log_fetch(sym, "ok", n, "; ".join(issues))
            report.updated[sym] = n
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="BIST 100 veri güncelleme")
    parser.add_argument("--full", action="store_true", help="Tüm geçmişi baştan çek")
    parser.add_argument("--tickers", nargs="*", help="Sadece bu semboller (ör. THYAO GARAN)")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    r = update(full=args.full, tickers=args.tickers)
    print(f"\nGüncellenen: {len(r.updated)} sembol, başarısız: {len(r.failed)}")
    if r.failed:
        print("Başarısız:", ", ".join(r.failed))
    for sym, issues in r.warnings.items():
        print(f"Uyarı {sym}: {'; '.join(issues)}")


if __name__ == "__main__":
    main()
