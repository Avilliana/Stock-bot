"""
Gate checker: the scorecard, enforced in code. A strategy is DEPLOYABLE only when
every line passes. Anything else stays in paper mode.

Reads  reports/<strategy>.json  (backtest.py)
       reviews/verdicts.json    (risk officer, written by the nightly review)
       logs/trades.csv          (live paper trades, written by reconcile.py)
Writes logs/gates.json and GATES.md

    python gate.py
"""
import csv
import json
import math
import os
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))


def _load(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return default


def live_trades(name, version):
    path = os.path.join(HERE, "logs", "trades.csv")
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8", newline="") as f:
        return [r for r in csv.DictReader(f)
                if r["strategy"] == name and r.get("version") == version]


def check(name, cfg, verdicts):
    sc = cfg["scorecard"]
    strat = cfg["strategies"][name]
    rep = _load(os.path.join(HERE, "reports", f"{name}.json"), None)
    gates = []

    def g(label, ok, detail):
        gates.append({"gate": label, "pass": bool(ok), "detail": detail})

    if rep is None:
        g("backtest", False, "no backtest report yet - run backtest.py")
    else:
        b, s, r = rep["base"], rep["stress"], rep["recent"]
        stale = rep.get("version") != strat["version"] or rep.get("params") != strat["params"]
        costs_on = (cfg["costs"]["slippage_bps_etf"] > 0 and cfg["costs"]["slippage_bps_stock"] > 0
                    and rep.get("honest_slippage_mult", 1) >= 1)
        g("settings", costs_on and not rep.get("synthetic") and not stale,
          "synthetic data" if rep.get("synthetic") else
          "report is for an older version/params - re-run backtest" if stale else
          f"slippage {cfg['costs']['slippage_bps_etf']}/{cfg['costs']['slippage_bps_stock']} bps, fees on, "
          f"{rep['days']} days")
        g("sample", b["trades"] >= sc["min_trades"], f"{b['trades']} closed trades (need {sc['min_trades']}+)")
        g("quality", b["sharpe"] > sc["min_sharpe"] and b["profit_factor"] > sc["min_profit_factor"],
          f"Sharpe {b['sharpe']} (>{sc['min_sharpe']}), PF {b['profit_factor']} (>{sc['min_profit_factor']})")
        g("pain", b["max_dd_pct"] <= sc["max_drawdown_pct"],
          f"max drawdown {b['max_dd_pct']}% of allocation (limit {sc['max_drawdown_pct']}%)")
        g("benchmark", b["sharpe"] > rep["benchmark"]["sharpe"],
          f"Sharpe {b['sharpe']} vs buy-and-hold {rep['benchmark']['sharpe']}")
        beta = b.get("beta")
        g("neutral", beta is not None and abs(beta) <= sc["max_abs_beta"], f"beta {beta} (|beta| <= {sc['max_abs_beta']})")
        plate = rep.get("plateau", [])
        ok_n = sum(1 for x in plate if x["profit_factor"] >= sc["plateau_min_pf"] and x["total_pnl"] > 0)
        share = ok_n / len(plate) if plate else 0
        g("stress", s["profit_factor"] >= sc["stress_min_pf"] and s["total_pnl"] > 0 and share >= sc["plateau_share"],
          f"costs x2: PF {s['profit_factor']}, P&L ${s['total_pnl']}; plateau {ok_n}/{len(plate)} nudges hold up")
        g("recent", r["trades"] >= 20 and r["profit_factor"] >= sc["recent_min_pf"] and r["total_pnl"] > 0,
          f"trailing year: {r['trades']} trades, PF {r['profit_factor']}, P&L ${r['total_pnl']}")

    v = verdicts.get(name, {})
    g("risk officer", v.get("verdict") == "KEEP" and v.get("version") == strat["version"],
      f"{v.get('verdict', 'no review yet')} ({v.get('date', '-')}): {v.get('reason', '')}".strip())

    lt = live_trades(name, strat["version"])
    rs = [float(t["r"]) for t in lt if t.get("r") not in (None, "")]
    days = len({t["date"] for t in lt})
    detail = f"{len(rs)} paper trades over {days} days (need {sc['forward_min_trades']}+ over {sc['forward_min_days']}+)"
    fwd_ok = False
    if rep is not None and rs:
        mean = sum(rs) / len(rs)
        floor = rep["base"]["avg_r"] - 2 * rep["base"].get("std_r", 0) / math.sqrt(len(rs))
        wins = sum(x for x in rs if x > 0)
        losses = -sum(x for x in rs if x < 0)
        pf = wins / losses if losses > 0 else (99.0 if wins > 0 else 0.0)
        detail += f"; avg {mean:+.2f}R vs backtest {rep['base']['avg_r']:+.2f}R (floor {floor:+.2f}R), PF {pf:.2f}"
        fwd_ok = (len(rs) >= sc["forward_min_trades"] and days >= sc["forward_min_days"]
                  and mean >= floor and pf >= 1.0)
    g("forward", fwd_ok, detail)

    passed = sum(x["pass"] for x in gates)
    notes = []
    if rep is not None:
        b = rep["base"]
        if (b.get("best_symbol_share") or 0) > 0.5:
            notes.append(f"over half the profit came from one symbol ({b['best_symbol_share']:.0%})")
        if (b.get("top5_trades_share") or 0) > 0.5:
            notes.append(f"top 5 trades made {b['top5_trades_share']:.0%} of the profit")
    return {"version": strat["version"], "status": "DEPLOYABLE" if passed == len(gates) else "PAPER",
            "passed": passed, "total": len(gates), "gates": gates, "notes": notes}


def main():
    with open(os.path.join(HERE, "config.json"), encoding="utf-8") as f:
        cfg = json.load(f)
    verdicts = _load(os.path.join(HERE, "reviews", "verdicts.json"), {})
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    out = {"updated": stamp, "strategies": {}}
    md = [f"# Gate status\n\nUpdated {stamp} UTC. A strategy is **DEPLOYABLE** only when every gate "
          "passes. Everything else keeps paper trading.\n"]
    for name, s in cfg["strategies"].items():
        if not s["enabled"]:
            continue
        res = check(name, cfg, verdicts)
        out["strategies"][name] = res
        md.append(f"## {name} {res['version']} - {res['status']} ({res['passed']}/{res['total']})\n")
        md += [f"- {'PASS' if x['pass'] else 'FAIL'} **{x['gate']}**: {x['detail']}" for x in res["gates"]]
        md += [f"- note: {n}" for n in res["notes"]]
        md.append("")
        print(f"{name}: {res['status']} {res['passed']}/{res['total']}")
    os.makedirs(os.path.join(HERE, "logs"), exist_ok=True)
    with open(os.path.join(HERE, "logs", "gates.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
    with open(os.path.join(HERE, "GATES.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(md))


if __name__ == "__main__":
    main()
