"""
Paper wheel bot: the options lane's forward test, on the Alpaca PAPER account.

It runs the wheel on one stock with a virtual $1,000 ledger (the paper account
has more, but the ledger only ever commits $1,000):
  * no shares  -> sell one cash-secured put about 5% below the price, strike <= $10
  * assigned   -> own 100 shares; sell one covered call >= 5% above the price and
                  >= what was paid
  * called away -> back to cash, start over
Orders are limit orders at the mid of the free (indicative) quote, good for the
day; an unfilled order is cancelled and re-priced on the next run.

Run once a day during market hours (options.yml). State: logs/wheel_state.json,
history: logs/wheel_log.csv.

    python wheel_bot.py            normal run
    python wheel_bot.py --dry-run  look up the contract it would trade, send nothing
"""
import argparse
import csv
import json
import os
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

HERE = os.path.dirname(os.path.abspath(__file__))
LOGS = os.path.join(HERE, "logs")
STATE = os.path.join(LOGS, "wheel_state.json")
HIST = os.path.join(LOGS, "wheel_log.csv")
NY = ZoneInfo("America/New_York")
OPEN_ST = ("new", "accepted", "pending_new", "partially_filled", "held")


def load_config():
    with open(os.path.join(HERE, "config.json"), encoding="utf-8") as f:
        return json.load(f)


def load_state(cap):
    try:
        with open(STATE, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {"strategy": "wheel", "started": str(datetime.now(NY).date()), "capital": cap,
                "cash": float(cap), "symbol": None, "shares": 0, "basis": None, "open": None,
                "cycles_done": 0, "equity": float(cap), "phase": "cash", "n": 0}


def save_state(st):
    os.makedirs(LOGS, exist_ok=True)
    with open(STATE, "w", encoding="utf-8") as f:
        json.dump(st, f, indent=2)


def log_event(row):
    os.makedirs(LOGS, exist_ok=True)
    new = not os.path.exists(HIST)
    fields = ["time", "event", "symbol", "contract", "kind", "strike", "expiry", "price", "cash_after",
              "shares_after", "note"]
    with open(HIST, "a", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        if new:
            w.writeheader()
        w.writerow({"time": datetime.now(NY).strftime("%Y-%m-%d %H:%M"), **row})
    print(row)


def mid(q):
    bp, ap = float(q.get("bp") or 0), float(q.get("ap") or 0)
    if bp <= 0 or ap <= 0 or ap < bp:
        return None, bp, ap
    return round((bp + ap) / 2, 2), bp, ap


def last_price(api, sym, feed):
    snap = api.snapshots([sym], feed=feed).get(sym) or {}
    for k in ("latestTrade", "minuteBar", "dailyBar"):
        v = snap.get(k) or {}
        if v.get("p") or v.get("c"):
            return float(v.get("p") or v.get("c"))
    return None


def pick_contract(api, sym, kind, price, target, cap_strike, live, today):
    """Nearest-to-30-day expiry within the window; strike at/below target for puts,
    at/above for calls; must have a sane quote."""
    lo, hi = today + timedelta(days=live["min_dte"]), today + timedelta(days=live["max_dte"])
    params = {"type": kind, "expiration_date_gte": str(lo), "expiration_date_lte": str(hi)}
    if kind == "put":
        params["strike_price_lte"] = min(target, cap_strike)
        params["strike_price_gte"] = round(target * 0.8, 2)
    else:
        params["strike_price_gte"] = target
        params["strike_price_lte"] = round(target * 1.3, 2)
    snaps = api.option_chain(sym, feed="indicative", **params)
    best = None
    for occ, s in snaps.items():
        try:
            exp = datetime.strptime(occ[-15:-9], "%y%m%d").date()
        except ValueError:
            continue
        strike = int(occ[-8:]) / 1000
        m, bp, ap = mid(s.get("latestQuote") or {})
        if m is None or bp < live["min_bid"] or (ap - bp) > live["max_spread_frac"] * m:
            continue
        dte_gap = abs((exp - today).days - 30)
        dist = (target - strike) if kind == "put" else (strike - target)
        key = (dte_gap, dist)
        if best is None or key < best[0]:
            best = (key, {"contract": occ, "kind": kind, "strike": strike, "expiry": str(exp),
                          "mid": m, "bid": bp, "ask": ap, "iv": s.get("impliedVolatility")})
    return best[1] if best else None


def run(dry=False):
    from alpaca import Alpaca
    cfg = load_config()
    o = cfg["options"]
    live = o["live"]
    p = o["strategies"]["wheel"]["params"]
    fee = o["costs"]["commission_per_contract"]
    api = Alpaca()
    st = load_state(o["capital"])
    today = datetime.now(NY).date()
    clock = api.clock()
    if not clock["is_open"] and not dry:
        print("market closed - nothing to do")
        return st
    positions = {x["symbol"]: x for x in api.positions()}
    after = (datetime.now(timezone.utc) - timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%SZ")
    orders = {x.get("client_order_id"): x for x in api.orders(after)}

    # 1) working order from an earlier run: filled, or cancel and re-price
    op = st.get("open")
    if op and op.get("status") == "working":
        od = orders.get(op["client_id"])
        if od and od.get("status") == "filled":
            px = float(od["filled_avg_price"])
            credit = round(px * 100 - fee, 2)
            st["cash"] = round(st["cash"] + credit, 2)
            op.update(status="open", fill=px, credit=credit)
            st["phase"] = "short put" if op["kind"] == "put" else "shares + short call"
            log_event({"event": "sold", "symbol": st["symbol"], "contract": op["contract"], "kind": op["kind"],
                       "strike": op["strike"], "expiry": op["expiry"], "price": px, "cash_after": st["cash"],
                       "shares_after": st["shares"], "note": f"credit ${credit} after ${fee} fee"})
        elif od and od.get("status") in OPEN_ST:
            if not dry:
                api.cancel_order(od["id"])
            log_event({"event": "repriced", "symbol": st["symbol"], "contract": op["contract"],
                       "note": "unfilled at last mid; cancelled, will re-quote"})
            st["open"] = op = None
        else:
            st["open"] = op = None

    # 2) open option resolved? (expired, assigned, or called away - the contract position is gone)
    if op and op.get("status") == "open":
        exp = date.fromisoformat(op["expiry"])
        if op["contract"] not in positions and (today > exp or st["symbol"] in positions or st["shares"]):
            held = int(float(positions.get(st["symbol"], {}).get("qty", 0)))
            if op["kind"] == "put" and held >= 100 and st["shares"] == 0:
                st["cash"] = round(st["cash"] - op["strike"] * 100, 2)
                st.update(shares=100, basis=op["strike"], phase="shares")
                ev = "assigned"
            elif op["kind"] == "call" and held < st["shares"]:
                st["cash"] = round(st["cash"] + op["strike"] * 100, 2)
                st.update(shares=0, basis=None, phase="cash")
                ev = "called away"
            else:
                ev = "expired worthless"
            st["cycles_done"] = st.get("cycles_done", 0) + 1
            log_event({"event": ev, "symbol": st["symbol"], "contract": op["contract"], "kind": op["kind"],
                       "strike": op["strike"], "expiry": op["expiry"], "cash_after": st["cash"],
                       "shares_after": st["shares"]})
            st["open"] = op = None
            if st["shares"] == 0:
                st["symbol"] = None

    # 3) nothing open: sell the next option
    note = None
    if op is None and live.get("enabled", True):
        if st["shares"] > 0:
            sym = st["symbol"]
            px = last_price(api, sym, cfg["data_feed"])
            target = max(px * (1 + p["call_otm_pct"] / 100), st["basis"] if p.get("call_above_basis") else 0)
            choice = pick_contract(api, sym, "call", px, round(target, 2), 1e9, live, today)
        else:
            choice, sym, px = None, None, None
            order = live["priority"]
            try:                                   # follow today's screener when it ran
                with open(os.path.join(LOGS, "screener.json"), encoding="utf-8") as f:
                    scr = json.load(f)
                if scr.get("date") == str(today):
                    order = [r["symbol"] for r in scr.get("top", [])]
                    if not order:
                        print("screener found no put with positive edge today - not selling")
            except (OSError, ValueError):
                pass
            for cand in order:
                q = last_price(api, cand, cfg["data_feed"])
                if not q:
                    continue
                cap_strike = min(o["max_strike"], st["cash"] / 100)
                target = q * (1 - p["put_otm_pct"] / 100)
                # same rule as the backtest: the ~5%-below strike itself must be <= $10
                # (no reaching far out of the money just to fit the budget)
                if target < 0.5 or target > cap_strike + 0.49:
                    continue
                choice = pick_contract(api, cand, "put", q, round(target, 2), cap_strike, live, today)
                if choice:
                    sym, px = cand, q
                    break
        if choice:
            st["n"] = st.get("n", 0) + 1
            cid = f"wh-{today:%Y%m%d}-{st['n']}"
            note = (f"{'DRY RUN: would sell' if dry else 'sell'} 1 {choice['contract']} ({choice['kind']} {choice['strike']} "
                    f"exp {choice['expiry']}) at ${choice['mid']} (bid {choice['bid']} / ask {choice['ask']}, "
                    f"IV {choice['iv']}), stock ${px}")
            if not dry:
                try:
                    api.submit_option(choice["contract"], 1, "sell", choice["mid"], "sell_to_open", cid)
                    st["open"] = {**choice, "status": "working", "client_id": cid}
                    st["symbol"] = sym
                    st["phase"] = "selling put" if choice["kind"] == "put" else "shares + selling call"
                except Exception as e:                       # noqa: BLE001
                    note = f"order rejected: {str(e)[:200]}"
            log_event({"event": "order" if not dry else "dry-run", "symbol": sym, "contract": choice["contract"],
                       "kind": choice["kind"], "strike": choice["strike"], "expiry": choice["expiry"],
                       "price": choice["mid"], "cash_after": st["cash"], "shares_after": st["shares"], "note": note})
        else:
            note = "no contract passed the quote/price filters today"
            print(note)

    # 4) mark the ledger
    eq = st["cash"]
    if st["shares"] and st.get("symbol"):
        px = last_price(api, st["symbol"], cfg["data_feed"]) or 0
        eq += st["shares"] * px
    op = st.get("open")
    if op and op.get("status") == "open":
        snap = api.option_chain(st["symbol"], feed="indicative", expiration_date=op["expiry"], type=op["kind"],
                                strike_price_gte=op["strike"], strike_price_lte=op["strike"]).get(op["contract"], {})
        m, _, _ = mid(snap.get("latestQuote") or {})
        if m is not None:
            eq -= m * 100
    st["equity"] = round(eq, 2)
    st["last_run"] = datetime.now(NY).strftime("%Y-%m-%d %H:%M")
    st["last_note"] = note
    if not dry:
        save_state(st)
    print(json.dumps({k: st[k] for k in ("symbol", "phase", "cash", "shares", "equity", "cycles_done")}))
    return st


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    run(ap.parse_args().dry_run or load_config()["options"]["live"].get("dry_run", False))
