"""BTC 月线趋势过滤 sanity check（粗糙验证，不是可交易策略）。

数据: backtesting.py 自带的 BTC/USD 月线 (2012-2024)。
用法:
    pip install backtesting
    python research/scripts/tsmom_monthly.py            # 用 backtesting.test.BTCUSD
    python research/scripts/tsmom_monthly.py my.csv     # 自备 CSV: index=日期, 含 Close 列

规则: 在第 t 个月收盘计算信号，持有第 t+1 个月（shift(1)，无未来函数）；
每次进出场按单边 0.1% 扣费；信号为 0 时持有现金、收益为 0。
"""
import sys

import numpy as np
import pandas as pd

FEE = 0.001  # 单边手续费+滑点


def load_close(path=None):
    if path:
        return pd.read_csv(path, index_col=0, parse_dates=True)["Close"]
    from backtesting.test import BTCUSD
    return BTCUSD["Close"]


def stats(r, name):
    r = r.dropna()
    eq = (1 + r).cumprod()
    yrs = len(r) / 12
    return dict(
        strategy=name,
        CAGR=f"{eq.iloc[-1] ** (1 / yrs) - 1:.1%}",
        vol=f"{r.std() * np.sqrt(12):.1%}",
        sharpe=round(r.mean() / r.std() * np.sqrt(12), 2),
        maxDD=f"{(eq / eq.cummax() - 1).min():.1%}",
    )


def with_costs(pos, ret):
    pos = pos.shift(1)  # t 收盘出信号，t+1 持有
    cost = pos.diff().abs().fillna(0) * FEE
    return pos * ret - cost, pos


def run(px, start):
    ret = px.pct_change()
    rows = [stats(ret[start:], "buy&hold")]
    for n in (3, 6, 12):
        r, pos = with_costs((px.pct_change(n) > 0).astype(float), ret)
        rows.append(stats(r[start:], f"TSMOM {n}m") | {"in_mkt": f"{pos[start:].mean():.0%}"})
    r, pos = with_costs((px > px.rolling(10).mean()).astype(float), ret)
    rows.append(stats(r[start:], "close>SMA10m") | {"in_mkt": f"{pos[start:].mean():.0%}"})
    return pd.DataFrame(rows).set_index("strategy")


if __name__ == "__main__":
    px = load_close(sys.argv[1] if len(sys.argv) > 1 else None)
    for start in ("2013-01", "2018-01"):
        print(f"\n=== BTC monthly, {start} .. {px.index[-1]:%Y-%m} ===")
        print(run(px, start).to_string())
