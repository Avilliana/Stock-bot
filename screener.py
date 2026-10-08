"""
Daily options screener for a $1,000 budget: which cash-secured put (the first leg
of the wheel) looks best today, using live quotes?

For every stock in the screen universe whose ~5%-below strike is <= $10:
  * picks the put nearest 30 days out, about 5% below the price, with a sane quote,
  * prices it two ways: the market (live indicative quote) and our model's "fair"
    value (Black-Scholes at the stock's own 60-day realized volatility),
  * edge = what we'd collect (between bid and mid, after the $0.65 fee) minus the
    model's fair value, per contract. Positive = the market is paying more than the
    stock's recent moves justify. That gap is the only source of profit in selling
    options, and it is an estimate, not a promise.
  * also: annualized yield on the $ held as collateral, chance of being assigned
    (from the option's own implied volatility), break-even, and whether earnings
    land before expiry (options are pricey before earnings for a reason).

Writes logs/screener.json and SCREENER.md. Run during market hours.

    python screener.py
"""
import json
import math
import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import numpy as np
import requests

from options import _N, bs, implied_vol

HERE = os.path.dirname(os.path.abspath(__file__))
NY = ZoneInfo("America/New_York")


def load_config():
    with open(os.path.join(HERE, "config.json"), encoding="utf-8") as f:
        return json.load(f)


def earnings_between(start, end):
    """symbol -> earnings date, from Nasdaq's public calendar. Empty dict if unreachable."""
    out = {}
    s = requests.Session()
    s.headers.update({"User-Agent": "Mozilla/5.0 (stock-bot screener)", "Accept": "application/json"})
    d = start
    ok = 0
    while d <= end:
        if d.weekday() < 5:
            try:
                r = s.get("https://api.nasdaq.com/api/calendar/earnings", params={"date": str(d)}, timeout=10)
                rows = ((r.json().get("data") or {}).get("rows")) or []
                for row in rows:
                    out.setdefault(row.get("symbol", "").upper(), str(d))
                ok += 1
            except Exception:                              # noqa: BLE001
                pass
        d += timedelta(days=1)
    return out if ok else None


def run():
    from alpaca import Alpaca
    from wheel_bot import mid
    cfg = load_config()
    o = cfg["options"]
    sc = o["screener"]
    fee = o["costs"]["commission_per_contract"]
    api = Alpaca()
    now = datetime.now(NY)
    today = now.date()
    universe = list(dict.fromkeys(sc["universe"]))

    # recent daily bars for realized volatility; BIL for the interest rate
    start = (today - timedelta(days=140)).strftime("%Y-%m-%dT00:00:00Z")
    bars = api.bars(universe + ["BIL"], start, timeframe="1Day", feed=cfg["data_feed"], adjustment="split")
    snaps = {}
    for i in range(0, len(universe), 50):
        snaps.update(api.snapshots(universe[i:i + 50], feed=cfg["data_feed"]))
    bil = [b["c"] for b in bars.get("BIL", [])]
    rate = max(0.0, (bil[-1] / bil[-22] - 1) * 252 / 21) if len(bil) > 22 else 0.04

    try:
        divs = api.cash_dividends(universe, str(today - timedelta(days=365)), str(today))
        div_ok = True
    except Exception as e:                                 # noqa: BLE001
        print(f"dividend data unavailable: {str(e)[:120]}")
        divs, div_ok = {}, False

    earn = earnings_between(today, today + timedelta(days=sc["max_dte"] + 2)) if sc.get("check_earnings") else None

    rows, skipped = [], {}
    for sym in universe:
        sn = snaps.get(sym) or {}
        px = (sn.get("latestTrade") or {}).get("p") or (sn.get("dailyBar") or {}).get("c")
        closes = [b["c"] for b in bars.get(sym, [])]
        if not px or len(closes) < 65:
            skipped[sym] = "no price/history"
            continue
        px = float(px)
        target = px * (1 - sc["otm_pct"] / 100)
        if target > o["max_strike"] + 0.49 or target < 0.5:
            skipped[sym] = f"${px:.2f}: 5%-below strike doesn't fit the $10 cap"
            continue
        lr = np.diff(np.log(closes))
        rv60 = float(np.std(lr[-60:], ddof=1) * math.sqrt(252))
        rv20 = float(np.std(lr[-20:], ddof=1) * math.sqrt(252))
        lo, hi = today + timedelta(days=sc["min_dte"]), today + timedelta(days=sc["max_dte"])
        try:
            chain = api.option_chain(sym, feed="indicative", type="put", expiration_date_gte=str(lo),
                                     expiration_date_lte=str(hi), strike_price_lte=min(target, o["max_strike"]),
                                     strike_price_gte=round(target * 0.8, 2))
        except Exception as e:                             # noqa: BLE001
            skipped[sym] = f"chain error {str(e)[:60]}"
            continue
        best = None
        for occ, s in chain.items():
            try:
                exp = datetime.strptime(occ[-15:-9], "%y%m%d").date()
            except ValueError:
                continue
            K = int(occ[-8:]) / 1000
            m, bp, ap = mid(s.get("latestQuote") or {})
            if m is None or bp < sc["min_bid"] or (ap - bp) > sc["max_spread_frac"] * m:
                continue
            key = (abs((exp - today).days - 30), target - K)
            if best is None or key < best[0]:
                best = (key, occ, exp, K, m, bp, ap, s.get("impliedVolatility"))
        if not best:
            skipped[sym] = "no put with a usable quote"
            continue
        _, occ, exp, K, m, bp, ap, iv = best
        T = max(1, (exp - today).days) / 365
        q = sum(r_ for _, r_ in divs.get(sym, [])) / px     # trailing 12-month dividend yield
        iv = float(iv) if iv else implied_vol("put", m, px, K, T, rate, q)
        if not iv:
            skipped[sym] = "could not read implied volatility"
            continue
        fill = round((bp + m) / 2, 2)                      # conservative: between bid and mid
        credit = fill * 100 - fee
        fair = bs("put", px, K, T, rate, rv60, q) * 100
        edge = credit - fair
        sq = iv * math.sqrt(T)
        d2 = (math.log(px / K) + (rate - q - 0.5 * iv * iv) * T) / sq
        p_assign = _N(-d2)
        e_date = (earn or {}).get(sym)
        earnings_before = bool(e_date and e_date <= str(exp))
        rows.append({
            "symbol": sym, "price": round(px, 2), "contract": occ, "strike": K, "expiry": str(exp),
            "dte": (exp - today).days, "bid": bp, "ask": ap, "mid": m, "fill_est": fill,
            "credit_usd": round(credit, 2), "collateral_usd": round(K * 100, 2),
            "yield_annual_pct": round(credit / (K * 100) * 365 / max(1, (exp - today).days) * 100, 1),
            "iv_pct": round(iv * 100, 1), "rv60_pct": round(rv60 * 100, 1), "rv20_pct": round(rv20 * 100, 1),
            "richness": round(iv / rv60, 2) if rv60 > 0 else None,
            "fair_usd": round(fair, 2), "edge_usd": round(edge, 2),
            "p_assign_pct": round(p_assign * 100, 1), "breakeven": round(K - fill, 2),
            "otm_pct": round((1 - K / px) * 100, 1), "div_yield_pct": round(q * 100, 1), "spread_pct": round((ap - bp) / m * 100, 1),
            "earnings": e_date if earnings_before else None,
        })
    clean = sorted([r for r in rows if not r["earnings"]], key=lambda r: -r["edge_usd"])
    flagged = sorted([r for r in rows if r["earnings"]], key=lambda r: -r["edge_usd"])
    top = [r for r in clean if r["edge_usd"] > 0][: sc["top_n"]]
    out = {"updated": now.strftime("%Y-%m-%d %H:%M ET"), "date": str(today), "rate_pct": round(rate * 100, 2),
           "earnings_checked": earn is not None, "dividends_checked": div_ok, "budget_usd": o["capital"],
           "pick": top[0] if top else None, "top": top, "earnings_flagged": flagged[:5],
           "all": clean + flagged, "skipped": skipped,
           "how": "edge = estimated credit (between bid and mid, after $0.65) minus fair value at the stock's "
                  "60-day realized volatility. Positive edge only means the option looks expensive versus recent "
                  "moves; it is an estimate, not a forecast."}
    os.makedirs(os.path.join(HERE, "logs"), exist_ok=True)
    with open(os.path.join(HERE, "logs", "screener.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
    md = [f"# Options screener - {out['updated']}\n",
          "Cash-secured puts ~5% below the price, ~30 days, strike <= $10 (fits $1,000). "
          "Sorted by estimated edge. Not financial advice.\n",
          "| stock | contract | credit | edge vs fair | yield/yr | assign odds | break-even | IV / 60d moves |",
          "|---|---|---|---|---|---|---|---|"]
    for r in clean + flagged:
        md.append(f"| {r['symbol']} ${r['price']} | {r['strike']}P {r['expiry']} | ${r['credit_usd']} | ${r['edge_usd']} | "
                  f"{r['yield_annual_pct']}% | {r['p_assign_pct']}% | ${r['breakeven']} | "
                  f"{r['iv_pct']}% / {r['rv60_pct']}%{' · div ' + str(r['div_yield_pct']) + '%' if r['div_yield_pct'] else ''}"
                  f"{' · EARNINGS ' + r['earnings'] if r['earnings'] else ''} |")
    md.append(f"\nEarnings check: {'on' if earn is not None else 'unavailable today - check before trading'}. "
              f"Dividends: {'priced in' if div_ok else 'unavailable today'}. Skipped: "
              + ", ".join(f"{k} ({v})" for k, v in skipped.items()))
    with open(os.path.join(HERE, "SCREENER.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(md) + "\n")
    p = out["pick"]
    print("PICK:", f"sell 1 {p['contract']} ~${p['fill_est']} (${p['credit_usd']}), edge ${p['edge_usd']}, "
          f"assign {p['p_assign_pct']}%" if p else "nothing with positive edge today")
    print(f"{len(rows)} screened, {len(flagged)} with earnings before expiry, {len(skipped)} skipped")
    return out


if __name__ == "__main__":
    run()
