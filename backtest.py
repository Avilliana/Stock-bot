"""
Backtest every enabled strategy with honest settings, then attack it:
  * base run           - venue costs on, slippage per config
  * stress             - same run with costs x2
  * plateau            - every numeric parameter nudged up and down 20%
  * recent             - the trailing ~year on its own
  * benchmark / beta   - vs buy-and-hold SPY over the same days

Writes reports/<strategy>.json (+ _trades.csv) and BACKTEST.md. gate.py turns
those into pass/fail.

    python backtest.py                 download/refresh data, test all strategies
    python backtest.py --no-fetch      use the cached data in data/
    python backtest.py --synthetic     fake market, just to prove the pipeline runs
    python backtest.py --strategy orb  one strategy only
"""
import argparse
import json
import math
import os
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime, timezone

import numpy as np
import pandas as pd

import data as D
from strategies import simulate_day

HERE = os.path.dirname(os.path.abspath(__file__))
REPORTS = os.path.join(HERE, "reports")

_DAYS = None   # {symbol: [day, ...]}, shared with worker processes
_CFG = None


def load_config():
    with open(os.path.join(HERE, "config.json"), encoding="utf-8") as f:
        return json.load(f)


def _init(days, cfg):
    global _DAYS, _CFG
    _DAYS, _CFG = days, cfg


def run_strategy(args):
    name, params, cost_mult = args
    trades = []
    for sym, days in _DAYS.items():
        for day in days:
            if day["prev_close"] is None:
                continue
            trades.extend(simulate_day(sym, day, name, params, _CFG, cost_mult))
    return trades


# -- metrics -----------------------------------------------------------------

def metrics(trades, all_dates, cfg, spy_ret=None):
    alloc = cfg["risk"]["strategy_allocation_usd"]
    df = pd.DataFrame(trades)
    out = {"trades": len(df)}
    if df.empty:
        out.update({"win_rate": 0, "profit_factor": 0, "total_pnl": 0, "sharpe": 0,
                    "max_dd_pct": 0, "avg_r": 0, "beta": None})
        return out
    gains = df.loc[df.pnl_usd > 0, "pnl_usd"].sum()
    losses = -df.loc[df.pnl_usd < 0, "pnl_usd"].sum()
    daily = df.groupby("date")["pnl_usd"].sum().reindex(all_dates, fill_value=0.0)
    ret = daily / alloc
    sd = ret.std(ddof=1)
    eq = alloc + daily.cumsum()
    peak = eq.cummax()
    dd = ((peak - eq) / peak).max() * 100
    by_sym = df.groupby("symbol")["pnl_usd"].sum()
    top5 = df["pnl_usd"].nlargest(5).sum()
    total = df["pnl_usd"].sum()
    out.update({
        "win_rate": round((df.pnl_usd > 0).mean() * 100, 1),
        "profit_factor": round(gains / losses, 3) if losses > 0 else (99.0 if gains > 0 else 0.0),
        "total_pnl": round(total, 2),
        "avg_pnl": round(df.pnl_usd.mean(), 2),
        "avg_r": round(df.r.mean(), 3),
        "std_r": round(df.r.std(ddof=1), 3) if len(df) > 1 else 0.0,
        "sharpe": round(ret.mean() / sd * math.sqrt(252), 3) if sd > 0 else 0.0,
        "max_dd_pct": round(dd, 2),
        "return_on_alloc_pct": round(total / alloc * 100, 2),
        "trades_per_year": round(len(df) / max(1, len(all_dates)) * 252, 1),
        "long": _side(df, "long"), "short": _side(df, "short"),
        "best_symbol_share": round(by_sym.max() / total, 2) if total > 0 else None,
        "top5_trades_share": round(top5 / total, 2) if total > 0 else None,
        "exit_reasons": df["reason"].value_counts().to_dict(),
    })
    if spy_ret is not None:
        s = spy_ret.reindex(all_dates).fillna(0.0)
        var = s.var(ddof=1)
        out["beta"] = round(float(np.cov(ret, s, ddof=1)[0, 1] / var), 3) if var > 0 else None
    return out


def _side(df, side):
    d = df[df.side == side]
    if d.empty:
        return {"trades": 0}
    g, lo = d.loc[d.pnl_usd > 0, "pnl_usd"].sum(), -d.loc[d.pnl_usd < 0, "pnl_usd"].sum()
    return {"trades": len(d), "pnl": round(d.pnl_usd.sum(), 2),
            "profit_factor": round(g / lo, 3) if lo > 0 else None}


def nudges(params, frac):
    """Every numeric parameter moved up and down by frac (ints move at least 1)."""
    out = []
    for k, v in params.items():
        if isinstance(v, bool) or not isinstance(v, (int, float)):
            continue
        for sgn in (-1, 1):
            p = dict(params)
            if isinstance(v, int):
                nv = int(round(v * (1 + sgn * frac)))
                if nv == v:
                    nv = v + sgn
                if nv < 1:
                    continue
            else:
                nv = round(v * (1 + sgn * frac), 6)
            p[k] = nv
            out.append((f"{k} {v} -> {nv}", p))
    return out


# -- main ---------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-fetch", action="store_true")
    ap.add_argument("--synthetic", action="store_true")
    ap.add_argument("--strategy")
    ap.add_argument("--no-plateau", action="store_true")
    ap.add_argument("--workers", type=int, default=os.cpu_count() or 2)
    a = ap.parse_args()
    cfg = load_config()
    syms = list(dict.fromkeys(cfg["universe"] + [cfg["benchmark"]]))

    if a.synthetic:
        frames = {s: D.synthetic_frame(s) for s in syms}
    else:
        if not a.no_fetch:
            from alpaca import Alpaca
            D.refresh_cache(Alpaca(), syms, cfg["backtest"]["years"], cfg["data_feed"])
        frames = {s: D.load_cached(s) for s in syms}
        cutoff = pd.Timestamp.now(tz=D.NY) - pd.Timedelta(days=int(365.25 * cfg["backtest"]["years"]))
        frames = {s: f[f.index >= cutoff] for s, f in frames.items()}

    days = {s: D.frame_to_days(f) for s, f in frames.items() if s in cfg["universe"]}
    bench = D.regular_session(frames[cfg["benchmark"]])
    if bench.empty:
        raise SystemExit("No benchmark data - run without --no-fetch first.")
    closes = bench["c"].groupby(bench.index.date).last()
    closes.index = [str(d) for d in closes.index]
    spy_ret = closes.pct_change().dropna()
    all_dates = list(closes.index[1:])
    recent_dates = all_dates[-252:]

    bh_sd = spy_ret.std(ddof=1)
    bench_m = {"sharpe": round(spy_ret.mean() / bh_sd * math.sqrt(252), 3) if bh_sd > 0 else 0,
               "return_pct": round((closes.iloc[-1] / closes.iloc[0] - 1) * 100, 2)}

    names = [n for n, s in cfg["strategies"].items() if s["enabled"]]
    if a.strategy:
        names = [a.strategy]
    os.makedirs(REPORTS, exist_ok=True)
    frac = cfg["backtest"]["nudge_frac"]
    stress_mult = cfg["backtest"]["stress_cost_mult"]

    jobs, labels = [], []
    for n in names:
        p = cfg["strategies"][n]["params"]
        jobs += [(n, p, 1.0), (n, p, stress_mult)]
        labels += [(n, "base", None), (n, "stress", None)]
        if not a.no_plateau:
            for lab, q in nudges(p, frac):
                jobs.append((n, q, 1.0))
                labels.append((n, "nudge", lab))

    print(f"{len(days)} symbols, {len(all_dates)} trading days, {len(jobs)} backtest runs")
    with ProcessPoolExecutor(max_workers=a.workers, initializer=_init,
                             initargs=(days, cfg)) as ex:
        results = list(ex.map(run_strategy, jobs))

    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    md = [f"# Backtest results\n\nUpdated {stamp} UTC · {len(all_dates)} trading days "
          f"({all_dates[0]} to {all_dates[-1]}) · data feed `{cfg['data_feed']}`"
          f"{' · **SYNTHETIC DATA**' if a.synthetic else ''}\n",
          f"Buy-and-hold {cfg['benchmark']}: Sharpe {bench_m['sharpe']}, "
          f"return {bench_m['return_pct']}%\n"]
    for n in names:
        base = next(r for (nn, kind, _), r in zip(labels, results) if nn == n and kind == "base")
        stress = next(r for (nn, kind, _), r in zip(labels, results) if nn == n and kind == "stress")
        nudge_res = [(lab, r) for (nn, kind, lab), r in zip(labels, results) if nn == n and kind == "nudge"]
        m = metrics(base, all_dates, cfg, spy_ret)
        recent_set = set(recent_dates)
        rec_tr = [t for t in base if t["date"] in recent_set]
        report = {
            "strategy": n, "version": cfg["strategies"][n]["version"],
            "params": cfg["strategies"][n]["params"], "updated": stamp,
            "synthetic": a.synthetic, "data_feed": cfg["data_feed"],
            "period": [all_dates[0], all_dates[-1]], "days": len(all_dates),
            "costs": cfg["costs"], "honest_slippage_mult": cfg["backtest"].get("honest_slippage_mult", 1.0),
            "base": m,
            "stress": metrics(stress, all_dates, cfg),
            "recent": metrics(rec_tr, recent_dates, cfg),
            "benchmark": bench_m,
            "plateau": [{"change": lab, **{k: v for k, v in metrics(r, all_dates, cfg).items()
                                           if k in ("trades", "profit_factor", "total_pnl", "sharpe")}}
                        for lab, r in nudge_res],
        }
        with open(os.path.join(REPORTS, f"{n}.json"), "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
        pd.DataFrame(base).to_csv(os.path.join(REPORTS, f"{n}_trades.csv"), index=False)
        print(f"{n}: {m['trades']} trades, PF {m['profit_factor']}, Sharpe {m['sharpe']}, "
              f"P&L ${m['total_pnl']}, max DD {m['max_dd_pct']}%")
        md.append(f"## {n} ({report['version']})\n\n"
                  f"| | trades | win % | PF | Sharpe | P&L | max DD |\n|---|---|---|---|---|---|---|\n"
                  + "".join(f"| {k} | {x['trades']} | {x['win_rate']} | {x['profit_factor']} | "
                            f"{x['sharpe']} | ${x['total_pnl']} | {x['max_dd_pct']}% |\n"
                            for k, x in (("base", m), ("costs x2", report["stress"]),
                                         ("last year", report["recent"]))))
    with open(os.path.join(HERE, "BACKTEST.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(md))


if __name__ == "__main__":
    main()
