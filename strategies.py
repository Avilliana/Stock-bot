"""
The three strategies, written once and shared by the backtester and the live bot.

Rules that keep the backtest honest:
  * prepare() builds per-bar arrays where the value at bar i uses ONLY bars 0..i
    (cumulative max/min, cumulative VWAP, trailing std). tests/test_no_lookahead.py
    proves this by recomputing on truncated data.
  * scan(i) decides using completed bar i. The order goes in at the NEXT bar's open.
  * The live bot calls the exact same prepare()/scan() on today's bars so far, so
    "what the backtest would have done" and "what the bot does" are the same code.

A day is a dict:
  date (YYYY-MM-DD), prev_close (float),
  mins  - minute of day in New York time (570 = 9:30)
  o, h, l, c, v - numpy arrays, regular session only
"""
from dataclasses import dataclass
from typing import Optional

import numpy as np
import pandas as pd

OPEN_MIN = 9 * 60 + 30


def hm(s: str) -> int:
    h, m = s.split(":")
    return int(h) * 60 + int(m)


def fmt_min(m: int) -> str:
    return f"{m // 60:02d}:{m % 60:02d}"


@dataclass
class Signal:
    side: int          # +1 long, -1 short
    ref: float         # close of the decision bar
    stop: float
    target: float
    time_stop: int     # minute of day; exit at market at/after this minute
    note: str = ""


@dataclass
class State:
    taken: int = 0     # entries already made today (this strategy, this symbol)
    in_pos: bool = False


# ---------------------------------------------------------------------------
# Opening-range breakout
# ---------------------------------------------------------------------------

def orb_prepare(day, p):
    mins, h, l = day["mins"], day["h"], day["l"]
    or_end = OPEN_MIN + int(p["or_minutes"])
    in_or = mins < or_end
    orh = np.maximum.accumulate(np.where(in_or, h, -np.inf))
    orl = np.minimum.accumulate(np.where(in_or, l, np.inf))
    n_or = np.cumsum(in_or)
    return {"orh": orh, "orl": orl, "n_or": n_or, "or_end": or_end}


def orb_scan(day, prep, i, st: State, p) -> Optional[Signal]:
    if st.taken >= 1 or st.in_pos or i < 1:
        return None
    m = day["mins"][i]
    if m < prep["or_end"] or m > hm(p["last_entry"]):
        return None
    if prep["n_or"][i] < 0.6 * p["or_minutes"]:      # too many missing bars in the range
        return None
    orh, orl = prep["orh"][i], prep["orl"][i]
    rng = orh - orl
    if not np.isfinite(rng) or orl <= 0:
        return None
    rng_pct = rng / orl * 100
    if rng_pct < p["min_range_pct"] or rng_pct > p["max_range_pct"]:
        return None
    c, c1 = day["c"][i], day["c"][i - 1]
    ts = hm(p["time_stop"])
    if c > orh and c1 <= orh:
        stop = orh - p["stop_frac"] * rng
        risk = c - stop
        return Signal(+1, c, stop, c + p["reward_risk"] * risk, ts, f"break above {orh:.2f}")
    if c < orl and c1 >= orl:
        stop = orl + p["stop_frac"] * rng
        risk = stop - c
        return Signal(-1, c, stop, c - p["reward_risk"] * risk, ts, f"break below {orl:.2f}")
    return None


# ---------------------------------------------------------------------------
# VWAP mean reversion
# ---------------------------------------------------------------------------

def _trailing_std(x, n):
    """Std of x over the last n values ending at each i (uses only <= i)."""
    return pd.Series(x).rolling(n, min_periods=max(5, n // 2)).std(ddof=1).to_numpy()


def vwap_prepare(day, p):
    h, l, c, v = day["h"], day["l"], day["c"], day["v"]
    tp = (h + l + c) / 3.0
    cv = np.cumsum(v)
    vw = np.where(cv > 0, np.cumsum(tp * v) / np.where(cv > 0, cv, 1), tp)
    dev = c - vw
    sd = _trailing_std(dev, int(p["lookback"]))
    with np.errstate(divide="ignore", invalid="ignore"):
        z = np.where(sd > 0, dev / sd, np.nan)
    return {"vwap": vw, "sd": sd, "z": z}


def vwap_scan(day, prep, i, st: State, p) -> Optional[Signal]:
    if st.in_pos or st.taken >= int(p["max_trades_per_day"]):
        return None
    m = day["mins"][i]
    if m < hm(p["start"]) or m > hm(p["last_entry"]):
        return None
    z, sd, vw, c = prep["z"][i], prep["sd"][i], prep["vwap"][i], day["c"][i]
    if not np.isfinite(z) or not sd > 0:
        return None
    if abs(c - vw) / c * 100 < p["min_dev_pct"]:
        return None
    ts = min(m + 1 + int(p["max_hold_min"]), hm(p["time_stop"]))
    if -p["z_stop"] < z <= -p["z_entry"]:
        return Signal(+1, c, vw - p["z_stop"] * sd, vw, ts, f"z={z:.2f}")
    if p["z_entry"] <= z < p["z_stop"]:
        return Signal(-1, c, vw + p["z_stop"] * sd, vw, ts, f"z={z:.2f}")
    return None


# ---------------------------------------------------------------------------
# Gap fade
# ---------------------------------------------------------------------------

def gapfade_prepare(day, p):
    mins = day["mins"]
    confirm_end = OPEN_MIN + int(p["confirm_minutes"]) - 1
    idx = np.nonzero(mins >= confirm_end)[0]
    return {
        "decision_idx": int(idx[0]) if len(idx) else -1,
        "hi": np.maximum.accumulate(day["h"]),
        "lo": np.minimum.accumulate(day["l"]),
    }


def gapfade_scan(day, prep, i, st: State, p) -> Optional[Signal]:
    if st.taken >= 1 or st.in_pos or i != prep["decision_idx"]:
        return None
    if day["mins"][0] > OPEN_MIN + 1:            # no real opening print
        return None
    pc, o0, c = day["prev_close"], day["o"][0], day["c"][i]
    if not pc or pc <= 0:
        return None
    gap = (o0 / pc - 1) * 100
    if not (p["min_gap_pct"] <= abs(gap) <= p["max_gap_pct"]):
        return None
    target = pc + (o0 - pc) * (1 - p["fill_frac"])
    ts = hm(p["time_stop"])
    buf = p["stop_buffer_pct"] / 100
    if gap > 0 and c < o0 and target < c:
        return Signal(-1, c, prep["hi"][i] * (1 + buf), target, ts, f"gap +{gap:.2f}%")
    if gap < 0 and c > o0 and target > c:
        return Signal(+1, c, prep["lo"][i] * (1 - buf), target, ts, f"gap {gap:.2f}%")
    return None


def too_tight(sig: Signal) -> bool:
    """Stop or target too close to the price to be a real trade (and a live bracket
    would be rejected after rounding to cents). Same rule in backtest and live."""
    gap = max(0.03, sig.ref * 0.0005)          # 3 cents or 5 bps
    return abs(sig.ref - sig.stop) < gap or abs(sig.target - sig.ref) < gap


STRATEGIES = {
    "orb": (orb_prepare, orb_scan),
    "vwap": (vwap_prepare, vwap_scan),
    "gapfade": (gapfade_prepare, gapfade_scan),
}


# ---------------------------------------------------------------------------
# Costs and the fill model (backtest)
# ---------------------------------------------------------------------------

def slippage_bps(symbol, cfg, mult=1.0):
    c = cfg["costs"]
    base = c["slippage_bps_etf"] if symbol in cfg["etfs"] else c["slippage_bps_stock"]
    return base * mult * cfg["backtest"].get("honest_slippage_mult", 1.0)


def fees(side_sold_qty, sold_notional, cfg, mult=1.0):
    c = cfg["costs"]
    sec = sold_notional * c["sec_fee_per_million_sold"] / 1e6
    taf = min(side_sold_qty * c["finra_taf_per_share_sold"], c["finra_taf_max"])
    return (sec + taf) * mult


def simulate_day(symbol, day, name, p, cfg, cost_mult=1.0):
    """Run one strategy over one symbol-day. Returns a list of closed trades."""
    prepare, scan = STRATEGIES[name]
    prep = prepare(day, p)
    mins, o, h, l, c = day["mins"], day["o"], day["h"], day["l"], day["c"]
    n = len(mins)
    flat = hm(cfg["risk"]["flatten_time"])
    slip = slippage_bps(symbol, cfg, cost_mult) / 1e4
    risk_usd = cfg["risk"]["risk_per_trade_usd"]
    max_notional = cfg["risk"]["max_notional_per_trade_usd"]
    allow_short = cfg["risk"]["allow_shorts"]
    st = State()
    trades = []
    i = 0
    while i < n - 1:
        sig = scan(day, prep, i, st, p)
        if sig is None or (sig.side < 0 and not allow_short):
            i += 1
            continue
        j = i + 1
        if mins[j] >= flat or mins[j] >= sig.time_stop:
            i += 1
            continue
        side = sig.side
        # Size off the decision bar's close, exactly like the live bot (it can't
        # know the next open). If the next open has already jumped past the stop or
        # target, the trade still happens and exits on that bar - same as a live
        # bracket would.
        rps = abs(sig.ref - sig.stop)
        if too_tight(sig):
            i += 1
            continue
        qty = int(min(risk_usd / rps, max_notional / sig.ref))
        if qty < 1:
            i += 1
            continue
        entry = o[j] * (1 + side * slip)
        st.taken += 1
        st.in_pos = True
        exit_px, reason, k_exit = None, None, n - 1
        for k in range(j, n):
            if k > j and (mins[k] >= sig.time_stop or mins[k] >= flat):
                exit_px, reason, k_exit = o[k] * (1 - side * slip), "time", k
                break
            if side > 0:
                hit_stop = l[k] <= sig.stop
                hit_tgt = h[k] >= sig.target
                if hit_stop:
                    exit_px, reason, k_exit = min(o[k], sig.stop) * (1 - slip), "stop", k
                    break
                if hit_tgt:
                    exit_px, reason, k_exit = max(o[k], sig.target), "target", k
                    break
            else:
                hit_stop = h[k] >= sig.stop
                hit_tgt = l[k] <= sig.target
                if hit_stop:
                    exit_px, reason, k_exit = max(o[k], sig.stop) * (1 + slip), "stop", k
                    break
                if hit_tgt:
                    exit_px, reason, k_exit = min(o[k], sig.target), "target", k
                    break
        if exit_px is None:
            exit_px, reason, k_exit = c[-1] * (1 - side * slip), "eod", n - 1
        sold_notional = (exit_px if side > 0 else entry) * qty
        fee = fees(qty, sold_notional, cfg, cost_mult)
        pnl = side * (exit_px - entry) * qty - fee
        trades.append({
            "date": day["date"], "strategy": name, "symbol": symbol,
            "side": "long" if side > 0 else "short", "qty": qty,
            "entry_time": fmt_min(mins[j]), "entry": round(entry, 4),
            "stop": round(sig.stop, 4), "target": round(sig.target, 4),
            "exit_time": fmt_min(mins[k_exit]), "exit": round(exit_px, 4),
            "reason": reason, "fees": round(fee, 4), "pnl_usd": round(pnl, 2),
            "r": round(pnl / (rps * qty), 3), "ref": round(sig.ref, 4), "note": sig.note,
        })
        st.in_pos = False
        i = max(k_exit, i + 1)
    return trades
