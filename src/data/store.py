"""SQLite veritabanı katmanı: günlük ve haftalık fiyat tabloları."""
import sqlite3
from pathlib import Path

import pandas as pd

PRICE_COLUMNS = ["open", "high", "low", "close", "adj_close", "volume"]
TABLES = ("daily_prices", "weekly_prices")

SCHEMA = """
CREATE TABLE IF NOT EXISTS {table} (
    ticker    TEXT NOT NULL,
    date      TEXT NOT NULL,   -- ISO tarih (YYYY-MM-DD)
    open      REAL,
    high      REAL,
    low       REAL,
    close     REAL,
    adj_close REAL,
    volume    REAL,
    PRIMARY KEY (ticker, date)
);
"""

FETCH_LOG_SCHEMA = """
CREATE TABLE IF NOT EXISTS fetch_log (
    ticker     TEXT PRIMARY KEY,
    last_fetch TEXT NOT NULL,
    status     TEXT NOT NULL,   -- ok / empty / error
    rows       INTEGER,
    message    TEXT
);
"""


class PriceStore:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.path)

    def _init_schema(self) -> None:
        with self._connect() as con:
            for table in TABLES:
                con.execute(SCHEMA.format(table=table))
            con.execute(FETCH_LOG_SCHEMA)

    def upsert(self, table: str, ticker: str, df: pd.DataFrame) -> int:
        """df: DatetimeIndex + PRICE_COLUMNS. Aynı (ticker, date) varsa üzerine yazar."""
        if table not in TABLES:
            raise ValueError(f"Bilinmeyen tablo: {table}")
        if df.empty:
            return 0
        rows = [
            (ticker, idx.strftime("%Y-%m-%d"),
             *(None if pd.isna(row[c]) else float(row[c]) for c in PRICE_COLUMNS))
            for idx, row in df[PRICE_COLUMNS].iterrows()
        ]
        with self._connect() as con:
            con.executemany(
                f"INSERT OR REPLACE INTO {table} (ticker, date, {', '.join(PRICE_COLUMNS)}) "
                f"VALUES (?, ?, {', '.join('?' * len(PRICE_COLUMNS))})",
                rows,
            )
        return len(rows)

    def load(self, table: str, ticker: str,
             start: str | None = None, end: str | None = None) -> pd.DataFrame:
        if table not in TABLES:
            raise ValueError(f"Bilinmeyen tablo: {table}")
        sql = f"SELECT date, {', '.join(PRICE_COLUMNS)} FROM {table} WHERE ticker = ?"
        params: list = [ticker]
        if start:
            sql += " AND date >= ?"
            params.append(start)
        if end:
            sql += " AND date <= ?"
            params.append(end)
        sql += " ORDER BY date"
        with self._connect() as con:
            df = pd.read_sql_query(sql, con, params=params, parse_dates=["date"])
        return df.set_index("date")

    def last_date(self, table: str, ticker: str) -> pd.Timestamp | None:
        with self._connect() as con:
            (val,) = con.execute(
                f"SELECT MAX(date) FROM {table} WHERE ticker = ?", (ticker,)
            ).fetchone()
        return pd.Timestamp(val) if val else None

    def tickers(self, table: str = "daily_prices") -> list[str]:
        with self._connect() as con:
            return [r[0] for r in con.execute(
                f"SELECT DISTINCT ticker FROM {table} ORDER BY ticker")]

    def log_fetch(self, ticker: str, status: str, rows: int = 0, message: str = "") -> None:
        with self._connect() as con:
            con.execute(
                "INSERT OR REPLACE INTO fetch_log VALUES (?, datetime('now'), ?, ?, ?)",
                (ticker, status, rows, message),
            )

    def summary(self) -> pd.DataFrame:
        """Sembol başına satır sayısı ve tarih aralığı (arayüzde durum göstermek için)."""
        sql = """
        SELECT d.ticker,
               COUNT(*)    AS daily_rows,
               MIN(d.date) AS first_date,
               MAX(d.date) AS last_date,
               (SELECT COUNT(*) FROM weekly_prices w WHERE w.ticker = d.ticker) AS weekly_rows,
               f.status, f.last_fetch
        FROM daily_prices d
        LEFT JOIN fetch_log f ON f.ticker = d.ticker
        GROUP BY d.ticker ORDER BY d.ticker
        """
        with self._connect() as con:
            return pd.read_sql_query(sql, con)
