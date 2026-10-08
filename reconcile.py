"""
End of day: read the day's fills back from Alpaca, pair them into round-trip
trades per strategy, and update the logs the dashboard, gate and nightly review use.

    python reconcile.py               today (New York date)
    python reconcile.py --date 2026-10-09

Writes logs/trades.csv (one row per closed trade, day's rows replaced on re-run),
logs/equity.csv and logs/summary.json. Alpaca paper charges no fees, so the
regulatory fees from config.json are subtracted here to keep results honest.
"""
import argparse
import csv
import json
import os
from datetime import date as Date, datetime, timezone
from zoneinfo import ZoneInfo

import pandas as pd

from bot import parse_cid
from strategies import fees

HERE = os.path.dirname(os.path.abspath(__file__))
NY = ZoneInfo("America/New_York")
FIELDS = ["date", "strategy", "version", "symbol", "side", "qty", "entry_time", "entry", "stop",
          "exit_time", "exit", "reason", "fees", "pnl_usd", "r"]


def _et(ts):
    return pd.Timestamp(ts).tz_convert(NY)


def load_refs(log_dir):
    """client id -> decision price, from signals.csv (planned risk = |ref - stop| x qty)."""
    refs = {}
    path = os.path.join(log_dir, "signals.csv")
    if os.path.exists(path):
        with open(path, encoding="utf-8", newline="") as f:
            for row in csv.DictReader(f):
                if row.get("cid"):
                    refs[row["cid"]] = float(row["ref"])
    return refs


def pair_fills(orders, fills, cfg, day, refs=None):
    refs = refs or {}
    roles = {}
    for o in orders:
        meta = parse_cid(o.get("client_order_id"))
        if not meta:
            continue
        stop = None
        for leg in o.get("legs") or []:
            if leg.get("type") == "stop":
                stop = float(leg["stop_price"])
                roles[leg["id"]] = ("stop", meta)
            elif leg.get("type") == "limit":
                roles[leg["id"]] = ("target", meta)
        roles[o["id"]] = ("entry", dict(meta, stop=stop, ref=refs.get(o["client_order_id"])))

    open_, trades = {}, []
    for f in sorted(fills, key=lambda x: x["transaction_time"]):
        role, meta = roles.get(f["order_id"], ("time", None))
        sym, q, px = f["symbol"], float(f["qty"]), float(f["price"])
        t = _et(f["transaction_time"])
        if role == "entry":
            p = open_.setdefault(sym, {"meta": meta, "side": 1 if f["side"] == "buy" else -1,
                                       "qty": 0.0, "cost": 0.0, "time": t, "out_qty": 0.0,
                                       "out_val": 0.0, "reason": None})
            p["qty"] += q
            p["cost"] += q * px
            continue
        p = open_.get(sym)
        if p is None:
            continue                                   # not the bot's position
        p["out_qty"] += q
        p["out_val"] += q * px
        p["reason"] = role if role in ("stop", "target") else "time"
        p["exit_time"] = t
        if p["out_qty"] >= p["qty"] - 1e-9:
            entry, exit_ = p["cost"] / p["qty"], p["out_val"] / p["out_qty"]
            qty, side, m = p["qty"], p["side"], p["meta"]
            sold = (exit_ if side > 0 else entry) * qty
            fee = fees(qty, sold, cfg)
            pnl = side * (exit_ - entry) * qty - fee
            # 1R = the risk planned at the signal (same definition as the backtest);
            # falls back to the actual entry if the signal row is missing
            base = m.get("ref") or entry
            risk = abs(base - m["stop"]) * qty if m.get("stop") else None
            trades.append({
                "date": str(day), "strategy": m["strategy"], "version": m["version"], "symbol": sym,
                "side": "long" if side > 0 else "short", "qty": int(qty),
                "entry_time": p["time"].strftime("%H:%M"), "entry": round(entry, 4),
                "stop": m.get("stop"), "exit_time": t.strftime("%H:%M"), "exit": round(exit_, 4),
                "reason": p["reason"], "fees": round(fee, 4), "pnl_usd": round(pnl, 2),
                "r": round(pnl / risk, 3) if risk else "",
            })
            del open_[sym]
    return trades, sorted(open_)


def _rewrite_csv(path, rows, fields, day):
    old = []
    if os.path.exists(path):
        with open(path, encoding="utf-8", newline="") as f:
            old = [r for r in csv.DictReader(f) if r.get("date") != str(day)]
    allr = sorted(old + rows, key=lambda r: (r["date"], r.get("entry_time", "")))
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(allr)
    return allr


def _stats(rows):
    pnl = [float(r["pnl_usd"]) for r in rows]
    rs = [float(r["r"]) for r in rows if r.get("r") not in ("", None)]
    wins = sum(1 for x in pnl if x > 0)
    return {"trades": len(rows), "pnl_usd": round(sum(pnl), 2), "wins": wins,
            "win_rate_pct": round(wins / len(rows) * 100, 1) if rows else 0,
            "avg_r": round(sum(rs) / len(rs), 3) if rs else None,
            "best_usd": max(pnl) if pnl else None, "worst_usd": min(pnl) if pnl else None}


def reconcile(api, cfg, day, log_dir):
    os.makedirs(log_dir, exist_ok=True)
    after = datetime.combine(day, datetime.min.time(), NY).astimezone(timezone.utc)
    orders = api.orders(after.strftime("%Y-%m-%dT%H:%M:%SZ"))
    fills = api.fills(str(day))
    if not fills and not any(parse_cid(o.get("client_order_id")) for o in orders):
        print(f"{day}: no bot orders or fills (holiday or quiet day) - nothing to record")
        return None
    trades, still_open = pair_fills(orders, fills, cfg, day, load_refs(log_dir))
    allr = _rewrite_csv(os.path.join(log_dir, "trades.csv"), trades, FIELDS, day)

    acct = api.account()
    eq_rows = _rewrite_csv(os.path.join(log_dir, "equity.csv"),
                           [{"date": str(day), "account_equity": acct["equity"],
                             "bot_pnl_usd": round(sum(t["pnl_usd"] for t in trades), 2)}],
                           ["date", "account_equity", "bot_pnl_usd"], day)
    summary = {
        "updated": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
        "last_day": str(day), "first_day": eq_rows[0]["date"] if eq_rows else str(day),
        "account_equity": float(acct["equity"]),
        "today": _stats([r for r in allr if r["date"] == str(day)]),
        "all": _stats(allr),
        "strategies": {},
        "open_after_close": still_open,
    }
    for name, s in cfg["strategies"].items():
        rows = [r for r in allr if r["strategy"] == name]
        summary["strategies"][name] = {
            "version": s["version"], "enabled": s["enabled"], "about": s["about"],
            "current_version": _stats([r for r in rows if r["version"] == s["version"]]),
            "all_versions": _stats(rows),
        }
    with open(os.path.join(log_dir, "summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(f"{day}: {len(trades)} closed trades, bot P&L ${summary['today']['pnl_usd']}"
          + (f", STILL OPEN: {still_open}" if still_open else ""))
    return summary


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date")
    a = ap.parse_args()
    with open(os.path.join(HERE, "config.json"), encoding="utf-8") as f:
        cfg = json.load(f)
    day = Date.fromisoformat(a.date) if a.date else datetime.now(NY).date()
    from alpaca import Alpaca
    reconcile(Alpaca(), cfg, day, os.path.join(HERE, "logs"))


if __name__ == "__main__":
    main()
