"""
Options lane: sell monthly options on one stock whose 100 shares fit in $1,000.

Real option prices before Feb 2024 aren't available for free, so option prices
are MODELED: Black-Scholes from the stock price at the time, using the stock's
own trailing volatility scaled by how expensive its real options have been.
That scale ("IV ratio" = implied vol / realized vol) is measured from Alpaca's
real option bars since Feb 2024 (calibrate step). The edge of selling options
lives almost entirely in that ratio, so the gauntlet also re-runs everything with
ratio 1.0 (options priced exactly fairly) and double spreads, to see whether a
result only exists because of the assumption.

Prices: split-adjusted for P&L (no dividends - same for the stock benchmark),
raw prices for "does 100 shares cost <= $1,000?" and for strike increments.
Cash and put collateral earn T-bill (BIL) returns. SPY benchmark is total return.

    python options.py              fetch data, calibrate, backtest, score
    python options.py --no-fetch   cached data and calibration
    python options.py --synthetic  fake prices, just to prove it runs
"""
import argparse
import json
import math
import os
from datetime import date, datetime, timedelta, timezone

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, "data")
REPORTS = os.path.join(HERE, "reports")
CAL_PATH = os.path.join(REPORTS, "options_calibration.json")


def load_config():
    with open(os.path.join(HERE, "config.json"), encoding="utf-8") as f:
        return json.load(f)


# -- Black-Scholes -------------------------------------------------------------

def _N(x):
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def bs(kind, S, K, T, r, sigma, q=0.0):
    """Black-Scholes with a continuous dividend yield q (dividends make puts dearer)."""
    if T <= 0 or sigma <= 0:
        return max(0.0, S - K) if kind == "call" else max(0.0, K - S)
    sq = sigma * math.sqrt(T)
    d1 = (math.log(S / K) + (r - q + 0.5 * sigma * sigma) * T) / sq
    d2 = d1 - sq
    if kind == "call":
        return S * math.exp(-q * T) * _N(d1) - K * math.exp(-r * T) * _N(d2)
    return K * math.exp(-r * T) * _N(-d2) - S * math.exp(-q * T) * _N(-d1)


def implied_vol(kind, price, S, K, T, r, q=0.0):
    intrinsic = max(0.0, S - K) if kind == "call" else max(0.0, K * math.exp(-r * T) - S)
    if T <= 0 or price <= intrinsic + 1e-4:
        return None
    lo, hi = 0.01, 5.0
    for _ in range(60):
        mid = (lo + hi) / 2
        if bs(kind, S, K, T, r, mid, q) > price:
            hi = mid
        else:
            lo = mid
    return (lo + hi) / 2


# -- calendar ---------------------------------------------------------------------

def third_friday(y, m):
    d = date(y, m, 15)
    return d + timedelta(days=(4 - d.weekday()) % 7)


def monthly_expiries(index):
    """Standard monthly expiration for each month, moved to the prior trading day
    when the third Friday is a holiday."""
    days = set(index.date)
    out = []
    y, m = index[0].year, index[0].month
    last = index[-1].date() + timedelta(days=70)
    while date(y, m, 1) <= last:
        d = third_friday(y, m)
        while d not in days and d > index[0].date() and d <= index[-1].date():
            d -= timedelta(days=1)
        out.append(d)
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    return out


def next_expiry(t, expiries, min_dte):
    for e in expiries:
        if (e - t).days >= min_dte:
            return e
    return None


def occ(root, exp, kind, strike):
    return f"{root}{exp:%y%m%d}{'C' if kind == 'call' else 'P'}{int(round(strike * 1000)):08d}"


def floor_half(x):
    return math.floor(x * 2) / 2


def ceil_half(x):
    return math.ceil(x * 2) / 2


# -- data ---------------------------------------------------------------------------

def _path(sym):
    return os.path.join(CACHE, f"opt_{sym}.csv.gz")


def fetch(api, ocfg, log=print):
    from alpaca import AlpacaError
    os.makedirs(CACHE, exist_ok=True)
    end = datetime.now(timezone.utc).strftime("%Y-%m-%dT00:00:00Z")
    start = ocfg["start"] + "T00:00:00Z"
    syms = ocfg["candidates"]
    tr = [ocfg["benchmark"], ocfg["cash"]]

    def get(symbols, adj):
        try:
            return api.bars(symbols, start, end, timeframe="1Day", feed="sip", adjustment=adj)
        except AlpacaError as e:
            if e.status not in (401, 403, 422):
                raise
            return api.bars(symbols, start, end, timeframe="1Day", feed="iex", adjustment=adj)

    raw, spl, tot = get(syms, "raw"), get(syms, "split"), get(tr, "all")

    def series(bars):
        if not bars:
            return pd.Series(dtype=float)
        d = pd.DataFrame(bars)
        idx = pd.to_datetime(d["t"], utc=True).dt.tz_convert("America/New_York").dt.date.astype(str)
        return pd.Series(d["c"].to_numpy(float), index=idx)

    for s in syms:
        df = pd.DataFrame({"raw": series(raw.get(s, [])), "adj": series(spl.get(s, []))}).dropna()
        df.index.name = "date"
        df.reset_index().to_csv(_path(s), index=False, compression="gzip")
        log(f"{s}: {len(df)} days" + (f" from {df.index[0]}" if len(df) else ""))
    for s in tr:
        sr = series(tot.get(s, []))
        df = pd.DataFrame({"raw": sr, "adj": sr})
        df.index.name = "date"
        df.reset_index().to_csv(_path(s), index=False, compression="gzip")


def load(sym):
    p = _path(sym)
    if not os.path.exists(p):
        return None
    df = pd.read_csv(p, index_col="date")
    df.index = pd.to_datetime(df.index)
    return df.sort_index()


def synthetic(ocfg, n=2600, seed=3):
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range("2016-01-04", periods=n)
    out = {}
    for j, s in enumerate(ocfg["candidates"][:6] + [ocfg["benchmark"], ocfg["cash"]]):
        if s == ocfg["cash"]:
            p = 100 * np.cumprod(1 + np.full(n, 0.02 / 252))
        else:
            vol = 0.01 if s == ocfg["benchmark"] else rng.uniform(0.02, 0.04)
            drift = 0.0004 if s == ocfg["benchmark"] else rng.normal(0.0, 0.0006)
            p = rng.uniform(4, 14) * np.cumprod(1 + drift + rng.normal(0, vol, n))
        out[s] = pd.DataFrame({"raw": p, "adj": p}, index=idx)
    return out


# -- calibration: how expensive were real options vs realized volatility? ----------

def rv_series(adj, days):
    return np.log(adj).diff().rolling(days).std() * math.sqrt(252)


def rate_series(bil):
    return (bil.pct_change(21) * 252 / 21).clip(lower=0).fillna(0.0)


def calibrate(api, frames, ocfg, log=print):
    vcfg = ocfg["vol"]
    bil = frames[ocfg["cash"]]["adj"]
    rate = rate_series(bil)
    obs = {s: [] for s in ocfg["candidates"]}
    idx = bil.index
    starts = [d for d in pd.date_range("2024-02-01", idx[-1] - pd.Timedelta(days=40), freq="MS")]
    expiries = monthly_expiries(idx)
    for m in starts:
        tds = idx[idx >= m]
        if not len(tds):
            continue
        t = tds[0]
        exp = next_expiry(t.date(), expiries, 20)
        want, meta = [], {}
        for s in ocfg["candidates"]:
            df = frames.get(s)
            if df is None or t not in df.index:
                continue
            R = float(df.loc[t, "raw"])
            if not 1 <= R <= 60:
                continue
            K = round(R * 2) / 2 if R < 25 else float(round(R))
            for kind in ("call", "put"):
                sym = occ(s, exp, kind, K)
                want.append(sym)
                meta[sym] = (s, kind, R, K)
        if not want:
            continue
        got = {}
        for i in range(0, len(want), 100):
            try:
                got.update(api.option_bars(want[i:i + 100], t.strftime("%Y-%m-%d"), t.strftime("%Y-%m-%d")))
            except Exception as e:                       # noqa: BLE001
                log(f"option bars unavailable for {t.date()}: {str(e)[:120]}")
                break
        T = (exp - t.date()).days / 365
        per = {}
        for sym, bars in got.items():
            if not bars or sym not in meta:
                continue
            s, kind, R, K = meta[sym]
            iv = implied_vol(kind, float(bars[-1]["c"]), R, K, T, float(rate.loc[t]))
            if iv:
                per.setdefault(s, []).append(iv)
        for s, ivs in per.items():
            rv = float(rv_series(frames[s]["adj"], vcfg["rv_days"]).loc[t])
            if rv > 0:
                ratio = float(np.median(ivs)) / rv
                if 0.3 <= ratio <= 3.0:
                    obs[s].append(round(ratio, 3))
    allr = [x for v in obs.values() for x in v]
    cal = {"updated": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
           "method": "median of (ATM implied vol from real ~monthly option closes) / (60-day realized vol), "
                     "first trading day of each month since Feb 2024",
           "pooled": round(float(np.median(allr)), 3) if allr else None,
           "pooled_n": len(allr),
           "per_symbol": {s: {"ratio": round(float(np.median(v)), 3), "n": len(v)} for s, v in obs.items() if v}}
    os.makedirs(REPORTS, exist_ok=True)
    with open(CAL_PATH, "w", encoding="utf-8") as f:
        json.dump(cal, f, indent=2)
    log(f"calibration: pooled IV/RV {cal['pooled']} from {len(allr)} observations")
    return cal


def ratio_for(sym, cal, ocfg):
    if cal:
        p = cal.get("per_symbol", {}).get(sym)
        if p and p["n"] >= 8:
            return p["ratio"]
        if cal.get("pooled") and cal.get("pooled_n", 0) >= 20:
            return cal["pooled"]
    return ocfg["vol"]["default_iv_ratio"]


# -- simulation ---------------------------------------------------------------------

def simulate(kind, df, bil_ret, rate, p, ocfg, iv_ratio, spread_mult=1.0):
    """One stock, one strategy, $capital. Returns (daily equity Series, stats dict)."""
    c = ocfg["costs"]
    cap, max_k = ocfg["capital"], ocfg["max_strike"]
    S = df["adj"].to_numpy(float)
    R = df["raw"].to_numpy(float)
    k = R / S
    idx = df.index
    sig = np.maximum(ocfg["vol"]["min_iv"], iv_ratio * rv_series(df["adj"], ocfg["vol"]["rv_days"]).to_numpy())
    br = bil_ret.reindex(idx).fillna(0.0).to_numpy()
    rr = rate.reindex(idx).ffill().fillna(0.0).to_numpy()
    expiries = monthly_expiries(idx)
    slip = c["stock_slippage_bps"] / 1e4

    cash, sh, basis, opt = float(cap), 0.0, None, None
    eq = np.full(len(idx), np.nan)
    cycles = assigned = called = 0
    premium_total = 0.0

    def sell(kind_, K_raw, i):
        nonlocal cash, opt, cycles, premium_total
        t = idx[i].date()
        exp = next_expiry(t, expiries, p.get("min_dte", 20))
        if exp is None or np.isnan(sig[i]):
            return
        K_adj = K_raw / k[i]
        T = (exp - t).days / 365
        prem_raw = bs(kind_, S[i], K_adj, T, rr[i], sig[i]) * k[i]
        if prem_raw < c["min_premium"]:
            return
        half = max(c["min_half_spread"], c["half_spread_frac"] * prem_raw) * spread_mult
        credit = 100 * (prem_raw - half) - c["commission_per_contract"]
        if credit <= 0:
            return
        cash += credit
        premium_total += credit
        cycles += 1
        opt = {"kind": kind_, "K": K_adj, "exp": exp, "n": 100 * k[i]}

    for i in range(len(idx)):
        t = idx[i].date()
        if i > 0 and cash > 0:
            cash *= 1 + br[i]
        # expiration at today's close
        if opt is not None and t >= opt["exp"]:
            if opt["kind"] == "put" and S[i] < opt["K"]:
                cash -= opt["K"] * opt["n"]
                sh += opt["n"]
                basis = opt["K"]
                assigned += 1
            elif opt["kind"] == "call" and S[i] > opt["K"]:
                cash += opt["K"] * opt["n"]
                sh -= opt["n"]
                called += 1
                if sh <= 1e-9:
                    sh, basis = 0.0, None
            opt = None
        # open the next position
        if opt is None and not np.isnan(sig[i]):
            if kind == "wheel":
                if sh > 0:
                    target = R[i] * (1 + p["call_otm_pct"] / 100)
                    if p.get("call_above_basis") and basis is not None:
                        target = max(target, basis * k[i])
                    sell("call", ceil_half(target), i)
                else:
                    K = floor_half(R[i] * (1 - p["put_otm_pct"] / 100))
                    if 0.5 <= K <= max_k and cash >= K * 100:
                        sell("put", K, i)
            elif kind == "covered_call":
                if sh == 0 and R[i] <= max_k and cash >= R[i] * 100 * (1 + slip):
                    cash -= R[i] * 100 * (1 + slip)
                    sh, basis = 100 * k[i], S[i]
                if sh > 0:
                    sell("call", ceil_half(R[i] * (1 + p["call_otm_pct"] / 100)), i)
            elif kind == "csp":
                if sh > 0:
                    cash += sh * S[i] * (1 - slip)
                    sh, basis = 0.0, None
                K = floor_half(R[i] * (1 - p["put_otm_pct"] / 100))
                if 0.5 <= K <= max_k and cash >= K * 100:
                    sell("put", K, i)
        val = cash + sh * S[i]
        if opt is not None:
            T = max(0.0, (opt["exp"] - t).days / 365)
            val -= opt["n"] * bs(opt["kind"], S[i], opt["K"], T, rr[i], sig[i] if not np.isnan(sig[i]) else 0.3)
        eq[i] = val
    return pd.Series(eq, index=idx), {"cycles": cycles, "assigned": assigned, "called_away": called,
                                      "premium_usd": round(premium_total, 2)}


def buy_and_hold(df, bil_ret, ocfg):
    """$capital: buy 100 shares the first day they cost <= $capital, hold; rest in T-bills."""
    cap = ocfg["capital"]
    S, R = df["adj"].to_numpy(float), df["raw"].to_numpy(float)
    br = bil_ret.reindex(df.index).fillna(0.0).to_numpy()
    cash, sh = float(cap), 0.0
    eq = []
    for i in range(len(S)):
        if i > 0 and cash > 0:
            cash *= 1 + br[i]
        if sh == 0 and R[i] * 100 <= cash and R[i] <= ocfg["max_strike"]:
            cash -= R[i] * 100
            sh = 100 * R[i] / S[i]
        eq.append(cash + sh * S[i])
    return pd.Series(eq, index=df.index)


def stats(ret):
    ret = ret.dropna()
    n = len(ret)
    if n < 20:
        return {"days": n, "cagr_pct": 0.0, "sharpe": 0.0, "max_dd_pct": 0.0, "years": round(n / 252, 2)}
    eq = (1 + ret).cumprod()
    yrs = n / 252
    sd = ret.std(ddof=1)
    return {"days": n, "years": round(yrs, 2),
            "cagr_pct": round((max(eq.iloc[-1], 1e-9) ** (1 / yrs) - 1) * 100, 2),
            "vol_pct": round(sd * math.sqrt(252) * 100, 2),
            "sharpe": round(ret.mean() / sd * math.sqrt(252), 3) if sd > 0 else 0.0,
            "max_dd_pct": round((1 - eq / eq.cummax()).max() * 100, 2),
            "total_return_pct": round((eq.iloc[-1] - 1) * 100, 2)}


def run_kind(kind, frames, ocfg, cal, p, ratio_override=None, spread_mult=1.0, warm=70):
    bil = frames[ocfg["cash"]]["adj"]
    bil_ret, rate = bil.pct_change().fillna(0.0), rate_series(bil)
    rets, per = {}, {}
    for s in ocfg["candidates"]:
        df = frames.get(s)
        if df is None or len(df) < warm + 60:
            continue
        ratio = ratio_override if ratio_override is not None else ratio_for(s, cal, ocfg)
        eq, info = simulate(kind, df, bil_ret, rate, p, ocfg, ratio, spread_mult)
        eq = eq.iloc[warm:]
        r = eq.pct_change().dropna()
        rets[s] = r
        per[s] = {**stats(r), **info, "iv_ratio": ratio}
    agg = pd.DataFrame(rets).mean(axis=1, skipna=True) if rets else pd.Series(dtype=float)
    return agg, per, rets


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-fetch", action="store_true")
    ap.add_argument("--synthetic", action="store_true")
    a = ap.parse_args()
    cfg = load_config()
    o = cfg["options"]
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    if a.synthetic:
        frames = synthetic(o)
        o = dict(o, candidates=[s for s in frames if s not in (o["benchmark"], o["cash"])])
        cal = None
    else:
        api = None
        if not a.no_fetch:
            from alpaca import Alpaca
            api = Alpaca()
            fetch(api, o)
        frames = {s: load(s) for s in o["candidates"] + [o["benchmark"], o["cash"]]}
        frames = {s: f for s, f in frames.items() if f is not None and len(f)}
        cal = None
        if api is not None:
            try:
                cal = calibrate(api, frames, o)
            except Exception as e:                        # noqa: BLE001
                print(f"calibration failed: {e}")
        if cal is None and os.path.exists(CAL_PATH):
            cal = json.load(open(CAL_PATH, encoding="utf-8"))

    bil = frames[o["cash"]]["adj"]
    bil_ret = bil.pct_change().fillna(0.0)
    # benchmarks: buy-and-hold the same stocks with the same $1k rule, and $1k in SPY
    bh = {}
    for s in o["candidates"]:
        if s in frames and len(frames[s]) > 130:
            bh[s] = buy_and_hold(frames[s], bil_ret, o).iloc[70:].pct_change().dropna()
    bh_agg = pd.DataFrame(bh).mean(axis=1, skipna=True)
    spy = frames[o["benchmark"]]["adj"].pct_change().reindex(bh_agg.index).fillna(0.0)
    idx = bh_agg.index
    half = idx[len(idx) // 2]
    rec_start = idx[-252 * o["scorecard"]["recent_years"]] if len(idx) > 252 * o["scorecard"]["recent_years"] else idx[0]

    summary = {"updated": stamp, "synthetic": a.synthetic, "capital": o["capital"],
               "period": [str(idx[0].date()), str(idx[-1].date())],
               "calibration": {"pooled": (cal or {}).get("pooled"), "n": (cal or {}).get("pooled_n", 0)},
               "bh_stocks": stats(bh_agg), "spy": stats(spy), "strategies": {}}
    md = [f"# Options lane results\n\nUpdated {stamp} UTC · {summary['period'][0]} to {summary['period'][1]}"
          f" · $"f"{o['capital']} per stock, one contract{' · **SYNTHETIC DATA**' if a.synthetic else ''}\n",
          "Each strategy runs on every candidate stock separately ($1,000 each), then results are averaged. "
          "Option prices are modeled (Black-Scholes); the IV/RV ratio is measured from real option data since Feb 2024"
          f" (pooled {summary['calibration']['pooled']}, n={summary['calibration']['n']}).\n",
          "| | CAGR | Sharpe | worst drop |\n|---|---|---|---|",
          f"| hold the same stocks | {summary['bh_stocks']['cagr_pct']}% | {summary['bh_stocks']['sharpe']} | {summary['bh_stocks']['max_dd_pct']}% |",
          f"| $1k in SPY instead | {summary['spy']['cagr_pct']}% | {summary['spy']['sharpe']} | {summary['spy']['max_dd_pct']}% |"]
    os.makedirs(REPORTS, exist_ok=True)
    for name, scfg in o["strategies"].items():
        if not scfg["enabled"]:
            continue
        p = scfg["params"]
        agg, per, rets = run_kind(name, frames, o, cal, p)
        agg = agg.reindex(idx).fillna(0.0)
        base = stats(agg)
        base["cycles"] = int(sum(x["cycles"] for x in per.values()))
        base["assigned"] = int(sum(x["assigned"] for x in per.values()))
        a1, _, _ = run_kind(name, frames, o, cal, p, ratio_override=1.0, spread_mult=2.0)
        sweep = {}
        for rt in (0.9, 1.0, 1.1, 1.2, 1.3):
            ag, _, _ = run_kind(name, frames, o, cal, p, ratio_override=rt)
            sweep[str(rt)] = stats(ag.reindex(idx).fillna(0.0))
        plateau = []
        for key, v in p.items():
            if isinstance(v, bool) or not isinstance(v, (int, float)):
                continue
            for sgn in (-1, 1):
                q = dict(p)
                q[key] = round(v * (1 + sgn * 0.2), 4) if isinstance(v, float) else max(1, int(round(v * (1 + sgn * 0.2))))
                ag, _, _ = run_kind(name, frames, o, cal, q)
                st = stats(ag.reindex(idx).fillna(0.0))
                plateau.append({"change": f"{key} {v} -> {q[key]}", "cagr_pct": st["cagr_pct"],
                                "sharpe": st["sharpe"], "max_dd_pct": st["max_dd_pct"]})
        breadth = {s: bool(per[s]["sharpe"] > stats(bh[s])["sharpe"]) for s in per if s in bh}
        rep = {"strategy": name, "version": scfg["version"], "params": p, "since": scfg["since"],
               "updated": stamp, "synthetic": a.synthetic, "costs": o["costs"],
               "calibrated": bool(cal and cal.get("pooled")),
               "base": base, "bh_stocks": summary["bh_stocks"], "spy": summary["spy"],
               "no_edge_stress": stats(a1.reindex(idx).fillna(0.0)),
               "iv_ratio_sweep": sweep, "plateau": plateau,
               "halves": [stats(agg[agg.index < half]), stats(agg[agg.index >= half])],
               "bh_halves": [stats(bh_agg[bh_agg.index < half]), stats(bh_agg[bh_agg.index >= half])],
               "recent": stats(agg[agg.index >= rec_start]), "bh_recent": stats(bh_agg[bh_agg.index >= rec_start]),
               "per_stock": {s: {**per[s], "bh": stats(bh[s]) if s in bh else None,
                                 "beats_holding": breadth.get(s)} for s in per},
               "breadth_share": round(sum(breadth.values()) / len(breadth), 2) if breadth else 0}
        with open(os.path.join(REPORTS, f"options_{name}.json"), "w", encoding="utf-8") as f:
            json.dump(rep, f, indent=2)
        summary["strategies"][name] = {"version": scfg["version"], "about": scfg["about"], "base": base,
                                       "breadth_share": rep["breadth_share"],
                                       "no_edge": rep["no_edge_stress"]}
        md.append(f"| **{name}** {scfg['version']} | {base['cagr_pct']}% | {base['sharpe']} | {base['max_dd_pct']}% |")
        md.append(f"| ↳ if options were priced fairly + 2x spreads | {rep['no_edge_stress']['cagr_pct']}% | "
                  f"{rep['no_edge_stress']['sharpe']} | {rep['no_edge_stress']['max_dd_pct']}% |")
        print(f"{name}: CAGR {base['cagr_pct']}% Sharpe {base['sharpe']} DD {base['max_dd_pct']}% cycles {base['cycles']} "
              f"| hold stocks {summary['bh_stocks']['cagr_pct']}% {summary['bh_stocks']['sharpe']} | SPY {summary['spy']['cagr_pct']}% "
              f"| fair-priced {rep['no_edge_stress']['cagr_pct']}% | beats holding in {rep['breadth_share']:.0%} of stocks")
    md.append("\nPer-stock detail is in `reports/options_<strategy>.json`. Costs: $"
              f"{o['costs']['commission_per_contract']} per contract, half-spread max(${o['costs']['min_half_spread']}, "
              f"{int(o['costs']['half_spread_frac'] * 100)}% of premium) on every sale.")
    with open(os.path.join(HERE, "OPTIONS.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(md) + "\n")
    os.makedirs(os.path.join(HERE, "logs"), exist_ok=True)
    live = {}
    lp = os.path.join(HERE, "logs", "wheel_state.json")
    if os.path.exists(lp):
        live = json.load(open(lp, encoding="utf-8"))
    summary["live"] = {k: live.get(k) for k in ("symbol", "phase", "equity", "cycles_done", "started", "open")}
    with open(os.path.join(HERE, "logs", "options_summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)


if __name__ == "__main__":
    main()
