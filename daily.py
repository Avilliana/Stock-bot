"""
Slow lane: daily-bar ETF strategies aimed at compounding, judged against simply
holding SPY (the same index as VOO).

Timing (no look-ahead): the target weights for day t are computed from closes up
to day t-1, and the trade happens at day t's close. Returns are close-to-close on
dividend-adjusted prices, so the T-bill ETF (BIL) earns its interest.

Every evening this script:
  * refreshes ~10 years of daily bars (data/daily_<SYM>.csv.gz),
  * backtests each strategy: base, costs x2, +-20% parameter nudges, each half
    of history, the trailing 3 years,
  * records the forward record: the days since each strategy's version started
    (`since` in config.json) are true out-of-sample, because the settings were
    fixed before those days happened,
  * writes reports/daily_<strategy>.json, DAILY.md and logs/daily_summary.json
    (including what each strategy holds right now).

    python daily.py                 refresh data + everything above
    python daily.py --no-fetch      use cached data
    python daily.py --synthetic     fake prices, just to prove it runs
"""
import argparse
import json
import math
import os
from datetime import datetime, timezone

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, "data")
REPORTS = os.path.join(HERE, "reports")


def load_config():
    with open(os.path.join(HERE, "config.json"), encoding="utf-8") as f:
        return json.load(f)


# -- data --------------------------------------------------------------------

def _path(sym):
    return os.path.join(CACHE, f"daily_{sym}.csv.gz")


def fetch(api, dcfg, log=print):
    """Full re-download each time (daily bars are small, and dividend adjustments
    change past prices whenever a new dividend is paid)."""
    from alpaca import AlpacaError
    os.makedirs(CACHE, exist_ok=True)
    end = datetime.now(timezone.utc).strftime("%Y-%m-%dT00:00:00Z")
    start = dcfg["start"] + "T00:00:00Z"
    feed = dcfg["feed"]
    try:
        got = api.bars(dcfg["symbols"], start, end, timeframe="1Day", feed=feed, adjustment="all")
    except AlpacaError as e:
        if feed == "iex" or e.status not in (401, 403, 422):
            raise
        log(f"feed '{feed}' refused ({e.status}); falling back to iex (shorter history)")
        got = api.bars(dcfg["symbols"], start, end, timeframe="1Day", feed="iex", adjustment="all")
    for sym, bars in got.items():
        df = pd.DataFrame(bars)[["t", "c"]]
        df["t"] = pd.to_datetime(df["t"], utc=True).dt.tz_convert("America/New_York").dt.date.astype(str)
        df.rename(columns={"t": "date", "c": "close"}).to_csv(_path(sym), index=False, compression="gzip")
        log(f"{sym}: {len(df)} daily bars, {df['t'].iloc[0]} to {df['t'].iloc[-1]}")


def load_closes(symbols):
    cols = {}
    for s in symbols:
        if not os.path.exists(_path(s)):
            raise SystemExit(f"no cached daily data for {s} - run without --no-fetch first")
        d = pd.read_csv(_path(s))
        cols[s] = d.set_index("date")["close"]
    df = pd.DataFrame(cols).dropna()           # only days every symbol traded
    df.index = pd.to_datetime(df.index)
    return df.sort_index()


def synthetic_closes(symbols, n=2700, seed=1):
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range("2016-01-04", periods=n)
    out = {}
    for k, s in enumerate(symbols):
        if s == "BIL":
            out[s] = 100 * np.cumprod(1 + np.full(n, 0.02 / 252))
            continue
        regime = np.repeat(rng.normal(0.0004, 0.0008, n // 120 + 1), 120)[:n]
        vol = np.repeat(rng.uniform(0.006, 0.02, n // 60 + 1), 60)[:n]
        out[s] = 100 * np.cumprod(1 + regime + rng.normal(0, 1, n) * vol)
    return pd.DataFrame(out, index=idx)


# -- strategies: target weights for each day from data up to the day before ------

def w_trend(px, p, cash):
    assets = p["assets"]
    w = pd.DataFrame(0.0, index=px.index, columns=px.columns)
    sleeve = 1.0 / len(assets)
    for a in assets:
        sma = px[a].rolling(int(p["sma_days"])).mean()
        band = p["band_pct"] / 100
        state, held = [], False
        for c, m in zip(px[a].to_numpy(), sma.to_numpy()):
            if np.isnan(m):
                held = False
            elif c > m * (1 + band):
                held = True
            elif c < m * (1 - band):
                held = False
            state.append(held)
        on = pd.Series(state, index=px.index).shift(1, fill_value=False)   # decided yesterday
        w[a] += np.where(on, sleeve, 0.0)
        w[cash] += np.where(on, 0.0, sleeve)
    return w


def w_momentum(px, p, cash):
    lb = int(p["lookback_days"])
    risky = p["risky"]
    mom = px / px.shift(lb) - 1
    # last trading day of each month; for the newest row, judge by the next business day
    nxt = px.index.to_series().shift(-1)
    nxt.iloc[-1] = px.index[-1] + pd.offsets.BDay(1)
    month_end = px.index.to_series().dt.to_period("M") != nxt.dt.to_period("M")
    w = pd.DataFrame(np.nan, index=px.index, columns=px.columns)
    dates = px.index
    for i in range(1, len(dates)):
        if not month_end.iloc[i]:               # trade at the month's last close
            continue
        m = mom.iloc[i - 1]                    # using data through the day before
        if m[risky].isna().any():
            continue
        row = pd.Series(0.0, index=px.columns)
        top = m[risky].sort_values(ascending=False).index[: int(p["top_n"])]
        for a in top:
            row[a if m[a] > m[cash] else cash] += 1.0 / int(p["top_n"])
        w.iloc[i] = row.values
    w = w.ffill()
    w[cash] = w[cash].fillna(1.0)
    return w.fillna(0.0)


def w_voltarget(px, p, cash):
    a = p["asset"]
    r = px[a].pct_change()
    vol = r.rolling(int(p["vol_days"])).std() * math.sqrt(252) * 100
    raw = (p["target_vol_pct"] / vol).clip(upper=p["max_weight"]).shift(1)   # yesterday's vol
    held, out = 0.0, []
    for x in raw.to_numpy():
        if not np.isnan(x) and abs(x - held) >= p["min_change"]:
            held = float(x)
        out.append(held)
    w = pd.DataFrame(0.0, index=px.index, columns=px.columns)
    w[a] = out
    w[cash] = 1.0 - w[a]
    return w


DAILY = {"trend": w_trend, "momentum": w_momentum, "voltarget": w_voltarget}


# -- simulation and metrics ---------------------------------------------------

def simulate(px, w, slip_bps):
    """w.loc[t] is held from the close of t to the close of t+1."""
    r = px.pct_change().fillna(0.0)
    gross = (w.shift(1).fillna(0.0) * r).sum(axis=1)
    turnover = w.diff().abs().sum(axis=1).fillna(w.abs().sum(axis=1))
    cost = turnover * slip_bps / 1e4
    ret = gross - cost
    ret.iloc[0] = 0.0
    return ret, turnover


def stats(ret, turnover=None):
    ret = ret.dropna()
    n = len(ret)
    if n < 2:
        return {"days": n}
    eq = (1 + ret).cumprod()
    yrs = n / 252
    sd = ret.std(ddof=1)
    dd = (1 - eq / eq.cummax()).max() * 100
    out = {"days": n, "years": round(yrs, 2),
           "cagr_pct": round((eq.iloc[-1] ** (1 / yrs) - 1) * 100, 2),
           "vol_pct": round(sd * math.sqrt(252) * 100, 2),
           "sharpe": round(ret.mean() / sd * math.sqrt(252), 3) if sd > 0 else 0.0,
           "max_dd_pct": round(dd, 2),
           "total_return_pct": round((eq.iloc[-1] - 1) * 100, 2)}
    if turnover is not None:
        t = turnover.loc[ret.index]
        out["switches"] = int((t > 0.001).sum())
        out["turnover_per_year"] = round(t.sum() / yrs, 2)
    return out


def nudges(params, frac):
    out = []
    for k, v in params.items():
        if isinstance(v, bool) or not isinstance(v, (int, float)):
            continue
        for sgn in (-1, 1):
            q = dict(params)
            if isinstance(v, int):
                nv = int(round(v * (1 + sgn * frac)))
                nv = nv if nv != v else v + sgn
                if nv < 1:
                    continue
            else:
                nv = round(v * (1 + sgn * frac), 6)
            q[k] = nv
            out.append((f"{k} {v} -> {nv}", q))
    return out


def run_all(px, cfg, synthetic=False):
    d = cfg["daily"]
    cash, bench = d["cash"], d["benchmark"]
    slip = d["slippage_bps"]
    frac = cfg["backtest"]["nudge_frac"]
    stress = cfg["backtest"]["stress_cost_mult"]
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    bh = px[bench].pct_change().fillna(0.0)
    bh_q = px["QQQ"].pct_change().fillna(0.0) if "QQQ" in px else None
    warm = 260                                   # first year of history is indicator warm-up
    idx = px.index[warm:]
    half = idx[len(idx) // 2]
    recent_start = idx[-252 * d["scorecard"]["recent_years"]] if len(idx) > 252 * d["scorecard"]["recent_years"] else idx[0]

    def window(s, a=None, b=None):
        s = s.loc[idx]
        if a is not None:
            s = s[s.index >= a]
        if b is not None:
            s = s[s.index < b]
        return s

    bench_full = stats(window(bh))
    summary = {"updated": stamp, "synthetic": synthetic, "last_date": str(px.index[-1].date()),
               "period": [str(idx[0].date()), str(idx[-1].date())],
               "benchmark": {"symbol": bench, **bench_full},
               "qqq": stats(window(bh_q)) if bh_q is not None else None,
               "strategies": {}}
    md = [f"# Slow lane (daily) results\n\nUpdated {stamp} UTC · {str(idx[0].date())} to {str(idx[-1].date())}"
          f" ({bench_full['years']} years){' · **SYNTHETIC DATA**' if synthetic else ''}\n",
          "| | CAGR | Sharpe | max drawdown | switches/yr |\n|---|---|---|---|---|",
          f"| buy-and-hold {bench} | {bench_full['cagr_pct']}% | {bench_full['sharpe']} | {bench_full['max_dd_pct']}% | - |"]
    if summary["qqq"]:
        q = summary["qqq"]
        md.append(f"| buy-and-hold QQQ | {q['cagr_pct']}% | {q['sharpe']} | {q['max_dd_pct']}% | - |")

    os.makedirs(REPORTS, exist_ok=True)
    for name, s in d["strategies"].items():
        if not s["enabled"]:
            continue
        f = DAILY[name]
        p = s["params"]
        # Judge each strategy against holding what it could hold: trend owns half
        # QQQ, so comparing it with SPY alone would flatter it.
        bmix = s.get("benchmark", {bench: 1.0})
        sb = sum(px[k].pct_change().fillna(0.0) * v for k, v in bmix.items())
        blabel = " + ".join(f"{int(v * 100)}% {k}" for k, v in bmix.items()) if len(bmix) > 1 else bench
        w = f(px, p, cash)
        ret, to = simulate(px, w, slip)
        ret2, _ = simulate(px, w, slip * stress)
        base = stats(window(ret), window(to))
        since = pd.Timestamp(s["since"])
        fwd_ret = ret[ret.index > since]
        fwd = stats(fwd_ret) if len(fwd_ret) >= 2 else {"days": len(fwd_ret)}
        if len(fwd_ret) >= 2:
            fwd["benchmark"] = stats(sb[sb.index > since])
        rep = {
            "strategy": name, "version": s["version"], "params": p, "since": s["since"],
            "updated": stamp, "synthetic": synthetic, "slippage_bps": slip,
            "base": base,
            "stress": stats(window(ret2), window(to)),
            "halves": [stats(window(ret, b=half)), stats(window(ret, a=half))],
            "bench_halves": [stats(window(sb, b=half)), stats(window(sb, a=half))],
            "recent": stats(window(ret, a=recent_start)),
            "bench_recent": stats(window(sb, a=recent_start)),
            "benchmark": {"label": blabel, **stats(window(sb))},
            "plateau": [],
            "forward": fwd,
            "holding": {k: round(v, 3) for k, v in w.iloc[-1].items() if v > 0.001},
        }
        for lab, q in nudges(p, frac):
            r_, t_ = simulate(px, f(px, q, cash), slip)
            st = stats(window(r_), window(t_))
            rep["plateau"].append({"change": lab, "cagr_pct": st["cagr_pct"], "sharpe": st["sharpe"],
                                   "max_dd_pct": st["max_dd_pct"]})
        eq = (1 + window(ret)).cumprod()
        rep["equity_monthly"] = [[str(i.date()), round(float(v), 4)] for i, v in eq.resample("ME").last().items()]
        with open(os.path.join(REPORTS, f"daily_{name}.json"), "w", encoding="utf-8") as fh:
            json.dump(rep, fh, indent=2)
        summary["strategies"][name] = {"version": s["version"], "about": s["about"],
                                       "base": base, "forward": fwd, "holding": rep["holding"],
                                       "benchmark": rep["benchmark"]}
        md.append(f"| {name} {s['version']} | {base['cagr_pct']}% | {base['sharpe']} | {base['max_dd_pct']}% | "
                  f"{round(base['switches'] / base['years'], 1)} |")
        if blabel != bench:
            bs = rep["benchmark"]
            md.append(f"| ↳ its benchmark: {blabel} | {bs['cagr_pct']}% | {bs['sharpe']} | {bs['max_dd_pct']}% | - |")
        print(f"{name}: CAGR {base['cagr_pct']}%, Sharpe {base['sharpe']}, max DD {base['max_dd_pct']}% "
              f"(vs {blabel}: {rep['benchmark']['cagr_pct']}%, {rep['benchmark']['sharpe']}, {rep['benchmark']['max_dd_pct']}%) · holds {rep['holding']}")
    be = (1 + window(bh)).cumprod()
    summary["benchmark"]["equity_monthly"] = [[str(i.date()), round(float(v), 4)] for i, v in be.resample("ME").last().items()]
    md.append("\nCosts: %.1f bps per unit of turnover. Decisions use data through the previous close; "
              "trades at the close. Forward record starts at each version's `since` date." % slip)
    with open(os.path.join(HERE, "DAILY.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(md) + "\n")
    os.makedirs(os.path.join(HERE, "logs"), exist_ok=True)
    with open(os.path.join(HERE, "logs", "daily_summary.json"), "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2)
    return summary


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-fetch", action="store_true")
    ap.add_argument("--synthetic", action="store_true")
    a = ap.parse_args()
    cfg = load_config()
    syms = cfg["daily"]["symbols"]
    if a.synthetic:
        px = synthetic_closes(syms)
    else:
        if not a.no_fetch:
            from alpaca import Alpaca
            fetch(Alpaca(), cfg["daily"])
        px = load_closes(syms)
    run_all(px, cfg, synthetic=a.synthetic)


if __name__ == "__main__":
    main()
