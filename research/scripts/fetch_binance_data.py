"""从 data.binance.vision 下载 BTC/ETH 历史数据（现货 K 线、U 本位永续 K 线、资金费率）。

用法:
    python research/scripts/fetch_binance_data.py                 # 默认 BTCUSDT ETHUSDT, 1d 4h 8h
    python research/scripts/fetch_binance_data.py --out data --symbols BTCUSDT --intervals 1d

输出 (CSV, UTC 时间索引):
    {out}/spot_{SYMBOL}_{interval}.csv      open,high,low,close,volume,quote_volume
    {out}/perp_{SYMBOL}_{interval}.csv      同上（U 本位永续）
    {out}/funding_{SYMBOL}.csv              funding_rate, funding_interval_hours

说明:
- 月度归档覆盖到上个月；当月用日度 K 线归档补齐。资金费率没有日度归档，
  当月部分尝试用 fapi.binance.com 补，失败就跳过（会打印提示）。
- 现货 K 线从 2025-01 起时间戳是微秒，这里统一转成毫秒。
- 部分永续 K 线 CSV 带表头、部分不带，统一处理。
"""
import argparse
import datetime as dt
import io
import sys
import zipfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd
import requests

BASE = "https://data.binance.vision/data"
KLINE_COLS = ["open_time", "open", "high", "low", "close", "volume", "close_time",
              "quote_volume", "count", "taker_buy_volume", "taker_buy_quote_volume", "ignore"]
SESSION = requests.Session()


def months(start: str, end: dt.date):
    y, m = map(int, start.split("-"))
    while (y, m) < (end.year, end.month):
        yield f"{y:04d}-{m:02d}"
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)


def days_of_current_month(today: dt.date):
    d = today.replace(day=1)
    while d < today:
        yield d.isoformat()
        d += dt.timedelta(days=1)


def get_zip_csv(url: str, header_marker: str):
    r = SESSION.get(url, timeout=60)
    if r.status_code == 404:
        return None
    r.raise_for_status()
    with zipfile.ZipFile(io.BytesIO(r.content)) as z:
        raw = z.read(z.namelist()[0]).decode()
    has_header = raw.split("\n", 1)[0].startswith(header_marker)
    return pd.read_csv(io.StringIO(raw), header=0 if has_header else None)


def to_ms(s: pd.Series) -> pd.Series:
    s = s.astype("int64")
    return s.where(s < 10**14, s // 1000)  # 微秒 -> 毫秒


def fetch_klines(market: str, symbol: str, interval: str, start: str, today: dt.date):
    prefix = f"{BASE}/spot" if market == "spot" else f"{BASE}/futures/um"
    urls = [f"{prefix}/monthly/klines/{symbol}/{interval}/{symbol}-{interval}-{m}.zip" for m in months(start, today)]
    urls += [f"{prefix}/daily/klines/{symbol}/{interval}/{symbol}-{interval}-{d}.zip" for d in days_of_current_month(today)]
    with ThreadPoolExecutor(8) as ex:
        frames = [f for f in ex.map(lambda u: get_zip_csv(u, "open_time"), urls) if f is not None]
    if not frames:
        return None
    df = pd.concat([f.set_axis(KLINE_COLS, axis=1) for f in frames], ignore_index=True)
    df["open_time"] = to_ms(df["open_time"])
    df = df.drop_duplicates("open_time").sort_values("open_time")
    df.index = pd.to_datetime(df["open_time"], unit="ms", utc=True)
    df.index.name = "time"
    return df[["open", "high", "low", "close", "volume", "quote_volume"]].astype(float)


def fetch_funding(symbol: str, start: str, today: dt.date):
    urls = [f"{BASE}/futures/um/monthly/fundingRate/{symbol}/{symbol}-fundingRate-{m}.zip" for m in months(start, today)]
    with ThreadPoolExecutor(8) as ex:
        frames = [f for f in ex.map(lambda u: get_zip_csv(u, "calc_time"), urls) if f is not None]
    df = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame(
        columns=["calc_time", "funding_interval_hours", "last_funding_rate"])
    df.columns = ["calc_time", "funding_interval_hours", "last_funding_rate"]
    # 当月部分：尝试 REST
    month_start_ms = int(dt.datetime(today.year, today.month, 1, tzinfo=dt.timezone.utc).timestamp() * 1000)
    try:
        r = SESSION.get("https://fapi.binance.com/fapi/v1/fundingRate",
                        params={"symbol": symbol, "startTime": month_start_ms, "limit": 1000}, timeout=30)
        r.raise_for_status()
        rest = pd.DataFrame(r.json())
        if not rest.empty:
            rest = pd.DataFrame({"calc_time": rest["fundingTime"].astype("int64"),
                                 "funding_interval_hours": pd.NA,
                                 "last_funding_rate": rest["fundingRate"].astype(float)})
            df = pd.concat([df, rest], ignore_index=True)
    except Exception as e:  # 地区限制(451)或未放行时跳过
        print(f"  [warn] {symbol} 当月资金费率 REST 补齐失败，跳过: {e}", file=sys.stderr)
    df["calc_time"] = to_ms(df["calc_time"])
    # calc_time 可能有毫秒级抖动，按整秒去重
    df["calc_time"] = (df["calc_time"] // 1000) * 1000
    df = df.drop_duplicates("calc_time").sort_values("calc_time")
    df.index = pd.to_datetime(df["calc_time"], unit="ms", utc=True)
    df.index.name = "time"
    return df.rename(columns={"last_funding_rate": "funding_rate"})[["funding_rate", "funding_interval_hours"]]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="data")
    ap.add_argument("--symbols", nargs="+", default=["BTCUSDT", "ETHUSDT"])
    ap.add_argument("--intervals", nargs="+", default=["1d", "4h", "8h"])
    ap.add_argument("--spot-start", default="2017-08")
    ap.add_argument("--perp-start", default="2019-09")
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    today = dt.datetime.now(dt.timezone.utc).date()

    for sym in args.symbols:
        for iv in args.intervals:
            for market, start in (("spot", args.spot_start), ("perp", args.perp_start)):
                df = fetch_klines(market, sym, iv, start, today)
                if df is None:
                    print(f"  [skip] {market} {sym} {iv}: 无数据")
                    continue
                path = out / f"{market}_{sym}_{iv}.csv"
                df.to_csv(path)
                print(f"{path}: {len(df)} rows {df.index[0]:%Y-%m-%d} .. {df.index[-1]:%Y-%m-%d %H:%M}")
        fr = fetch_funding(sym, args.perp_start, today)
        path = out / f"funding_{sym}.csv"
        fr.to_csv(path)
        print(f"{path}: {len(fr)} rows {fr.index[0]:%Y-%m-%d} .. {fr.index[-1]:%Y-%m-%d %H:%M}")


if __name__ == "__main__":
    main()
