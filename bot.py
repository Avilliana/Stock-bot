"""
Stock day-trading bot - PAPER money only (Alpaca paper account).

Every minute during the session it:
  1. pulls today's 1-minute bars for the universe (completed bars only),
  2. closes positions whose time stop or the 15:55 flatten has arrived,
  3. runs the same strategy code the backtest uses on the latest completed bar,
  4. sends a bracket order (market entry + take-profit + stop-loss) for each signal.

Positions, orders and "trades already taken today" are read back from Alpaca each
minute, so a crash or a second GitHub run can pick up where the last one stopped.
Every order's client id records strategy, version, symbol, date, count and time stop:
    sb-orb-v1-SPY-20261009-1-1555
Alpaca refuses a reused client id, so the same signal can never be sent twice.

    python bot.py                     live session (needs ALPACA_* keys)
    python bot.py --sim               one fake day against a fake broker, fast
"""
import argparse
import csv
import json
import os
import time
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import data as D
from strategies import STRATEGIES, State, fmt_min, hm, too_tight

HERE = os.path.dirname(os.path.abspath(__file__))
NY = ZoneInfo("America/New_York")


def load_config():
    with open(os.path.join(HERE, "config.json"), encoding="utf-8") as f:
        return json.load(f)


def parse_cid(cid):
    """sb-orb-v1-SPY-20261009-1-1555 -> dict, or None for orders the bot didn't send."""
    if not cid or not cid.startswith("sb-"):
        return None
    parts = cid.split("-")
    if len(parts) < 7:
        return None
    return {"strategy": parts[1], "version": parts[2], "symbol": "-".join(parts[3:-3]),
            "date": parts[-3], "n": int(parts[-2]), "time_stop": int(parts[-1][:2]) * 60 + int(parts[-1][2:])}


class Logger:
    def __init__(self, log_dir):
        self.dir = log_dir
        os.makedirs(log_dir, exist_ok=True)
        self.txt = os.path.join(log_dir, "bot_log.txt")
        self.sig = os.path.join(log_dir, "signals.csv")

    def __call__(self, msg, now=None):
        if now is None:
            now = self.clock.now() if getattr(self, "clock", None) else datetime.now(timezone.utc)
        stamp = now.astimezone(NY).strftime("%Y-%m-%d %H:%M:%S ET")
        line = f"{stamp}  {msg}"
        print(line, flush=True)
        with open(self.txt, "a", encoding="utf-8") as f:
            f.write(line + "\n")

    def signal(self, row):
        new = not os.path.exists(self.sig)
        with open(self.sig, "a", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(row))
            if new:
                w.writeheader()
            w.writerow(row)

    def trim(self, keep=6000):
        try:
            with open(self.txt, encoding="utf-8") as f:
                lines = f.readlines()
            if len(lines) > keep:
                with open(self.txt, "w", encoding="utf-8") as f:
                    f.writelines(lines[-keep:])
        except OSError:
            pass


class Bot:
    def __init__(self, api, cfg, log, clock):
        self.api, self.cfg, self.log, self.clock = api, cfg, log, clock
        self.prev_close = {}
        self.evaluated = set()     # (strategy, symbol, bar minute) already scanned
        self.shortable = {}
        self.killed = False
        self.first_pass = True
        self.busy_skips = {}       # signals skipped because another strategy held the symbol

    # -- broker state ---------------------------------------------------------
    def broker_state(self, today):
        after = datetime.combine(today, datetime.min.time(), NY).astimezone(timezone.utc)
        orders = self.api.orders(after.strftime("%Y-%m-%dT%H:%M:%SZ"))
        ymd = today.strftime("%Y%m%d")
        parents, taken, pending, owner = [], {}, set(), {}
        open_st = ("new", "accepted", "pending_new", "partially_filled")
        for o in orders:
            meta = parse_cid(o.get("client_order_id"))
            if not meta:
                if o["status"] in open_st:          # e.g. a close order still working
                    pending.add(o["symbol"])
                continue
            if meta["date"] != ymd:
                continue
            parents.append((o, meta))
            k = (meta["strategy"], meta["symbol"])
            taken[k] = taken.get(k, 0) + 1
            if o["status"] in open_st:
                pending.add(meta["symbol"])
            if o.get("filled_at"):
                prev = owner.get(meta["symbol"])
                if prev is None or o["filled_at"] > prev[0]["filled_at"]:
                    owner[meta["symbol"]] = (o, meta)
        positions = {p["symbol"]: p for p in self.api.positions()}
        return orders, taken, pending, owner, positions

    def open_child_orders(self, orders, symbol):
        """The bot's own working orders on a symbol (bracket parents and legs)."""
        out = []
        for o in orders:
            if not parse_cid(o.get("client_order_id")):
                continue
            for x in [o] + (o.get("legs") or []):
                if x["symbol"] == symbol and x["status"] in ("new", "accepted", "held", "pending_new",
                                                             "partially_filled"):
                    out.append(x)
        return out

    def close(self, orders, symbol, why, now):
        for x in self.open_child_orders(orders, symbol):
            self.api.cancel_order(x["id"])
        try:
            self.api.close_position(symbol)
        except Exception:
            # the bracket legs can take a moment to release the shares
            self.clock.sleep_until(self.clock.now() + timedelta(seconds=2))
            self.api.close_position(symbol)
        self.log(f"CLOSE {symbol}: {why}", now)

    # -- one minute -----------------------------------------------------------
    def step(self, now):
        cfg = self.cfg
        et = now.astimezone(NY)
        today = et.date()
        minute = et.hour * 60 + et.minute
        last_bar = minute - 1
        flatten = hm(cfg["risk"]["flatten_time"])

        orders, taken, pending, owner, positions = self.broker_state(today)
        closing = {o["symbol"] for o in orders
                   if not parse_cid(o.get("client_order_id")) and o["status"] in
                   ("new", "accepted", "pending_new", "partially_filled")}

        # kill switch: the day's account P&L
        acct = self.api.account()
        day_pnl = float(acct["equity"]) - float(acct["last_equity"])
        if not self.killed and day_pnl <= -cfg["risk"]["max_daily_loss_usd"]:
            self.killed = True
            self.save_kill(today)
            self.log(f"KILL SWITCH: day P&L ${day_pnl:.2f} - flattening and no new entries today", now)
            for sym in list(positions):
                if sym in owner and sym not in closing:
                    self.close(orders, sym, "kill switch", now)
                    pending.add(sym)

        # time stops and end-of-day flatten
        for sym, pos in list(positions.items()):
            if sym not in owner or sym in closing:
                continue
            meta = owner[sym][1]
            if minute >= flatten or minute >= meta["time_stop"]:
                self.close(orders, sym, f"{meta['strategy']} time stop {fmt_min(meta['time_stop'])}"
                           if minute < flatten else "end-of-day flatten", now)
                pending.add(sym)

        if self.killed or minute >= flatten:
            return

        # today's completed bars
        start = datetime.combine(today, datetime.min.time(), NY).replace(hour=9, minute=30)
        raw = self.api.bars(cfg["universe"], start.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                            feed=cfg["data_feed"])
        for sym in cfg["universe"]:
            busy = sym in positions or sym in pending
            df = D.bars_to_frame(raw.get(sym, []))
            days = D.frame_to_days(df, self.prev_close.get(sym))
            if not days or days[-1]["date"] != str(today):
                continue
            day = days[-1]
            keep = day["mins"] <= last_bar               # never use the forming bar
            for k in ("mins", "o", "h", "l", "c", "v"):
                day[k] = day[k][keep]
            if len(day["mins"]) < 2:
                continue
            for name, scfg in cfg["strategies"].items():
                if not scfg["enabled"]:
                    continue
                prepare, scan = STRATEGIES[name]
                p = scfg["params"]
                prep = prepare(day, p)
                own = owner.get(sym)
                st = State(taken=taken.get((name, sym), 0) + self.busy_skips.get((name, sym), 0),
                           in_pos=sym in positions and own is not None and own[1]["strategy"] == name)
                # scan bars from the last 3 minutes not seen yet (tolerates a slow loop);
                # on the first pass only the newest bar, so a late start can't act on stale signals
                lo = last_bar if self.first_pass else last_bar - 2
                for i in range(len(day["mins"])):
                    m = int(day["mins"][i])
                    if m < lo or (name, sym, m) in self.evaluated:
                        continue
                    self.evaluated.add((name, sym, m))
                    sig = scan(day, prep, i, st, p)
                    if sig is None:
                        continue
                    row = {"time": et.strftime("%Y-%m-%d %H:%M"), "strategy": name,
                           "version": scfg["version"], "symbol": sym, "bar": fmt_min(m),
                           "side": "long" if sig.side > 0 else "short", "ref": round(sig.ref, 4),
                           "stop": round(sig.stop, 4), "target": round(sig.target, 4),
                           "time_stop": fmt_min(sig.time_stop), "qty": 0, "result": "", "note": sig.note,
                           "cid": ""}
                    if busy:
                        # counts as this strategy's trade for the day, like the backtest
                        # would have taken it - keeps "first break only" rules honest
                        row["result"] = "skipped: symbol already has a position/order"
                        self.busy_skips[(name, sym)] = self.busy_skips.get((name, sym), 0) + 1
                        st.taken += 1
                    elif sig.side < 0 and not self.can_short(sym):
                        row["result"] = "skipped: not shortable"
                    else:
                        row.update(self.enter(name, scfg["version"], sym, sig, taken.get((name, sym), 0) + 1,
                                              today, now))
                        if row["qty"]:
                            busy = True
                            taken[(name, sym)] = taken.get((name, sym), 0) + 1
                            st.taken += 1
                    self.log.signal(row)
        self.first_pass = False

    def state_path(self):
        return os.path.join(self.log.dir, "state.json")

    def save_kill(self, today):
        with open(self.state_path(), "w", encoding="utf-8") as f:
            json.dump({"killed_date": str(today)}, f)

    def load_kill(self, today):
        try:
            with open(self.state_path(), encoding="utf-8") as f:
                self.killed = json.load(f).get("killed_date") == str(today)
        except (OSError, ValueError):
            self.killed = False

    def can_short(self, sym):
        if not self.cfg["risk"]["allow_shorts"]:
            return False
        if sym not in self.shortable:
            a = self.api.asset(sym)
            self.shortable[sym] = bool(a.get("shortable") and a.get("easy_to_borrow"))
        return self.shortable[sym]

    def enter(self, name, version, sym, sig, n, today, now):
        r = self.cfg["risk"]
        rps = abs(sig.ref - sig.stop)
        if too_tight(sig):
            return {"qty": 0, "result": "skipped: stop or target too close"}
        qty = int(min(r["risk_per_trade_usd"] / rps, r["max_notional_per_trade_usd"] / sig.ref))
        if qty < 1:
            return {"qty": 0, "result": "skipped: size < 1 share"}
        tp, sl = round(sig.target, 2), round(sig.stop, 2)
        if sig.side > 0 and not (sl < sig.ref < tp):
            return {"qty": 0, "result": "skipped: bracket invalid after rounding"}
        if sig.side < 0 and not (tp < sig.ref < sl):
            return {"qty": 0, "result": "skipped: bracket invalid after rounding"}
        cid = f"sb-{name}-{version}-{sym}-{today:%Y%m%d}-{n}-{fmt_min(sig.time_stop).replace(':', '')}"
        try:
            self.api.submit_bracket(sym, qty, "buy" if sig.side > 0 else "sell", tp, sl, cid)
        except Exception as e:                                    # broker said no
            self.log(f"REJECTED {cid}: {e}", now)
            return {"qty": 0, "result": f"rejected: {str(e)[:120]}"}
        self.log(f"ENTER {cid} {'BUY' if sig.side > 0 else 'SELL SHORT'} {qty} @mkt "
                 f"tp {tp} sl {sl} ({sig.note})", now)
        return {"qty": qty, "result": "sent", "cid": cid}


class RealClock:
    def now(self):
        return datetime.now(timezone.utc)

    def sleep_until(self, t):
        d = (t - self.now()).total_seconds()
        if d > 0:
            time.sleep(d)


def run(api, cfg, log, clock, max_minutes):
    log.clock = clock
    started = clock.now()
    c = api.clock()
    if not c["is_open"]:
        nxt = datetime.fromisoformat(c["next_open"].replace("Z", "+00:00"))
        wait = (nxt - clock.now()).total_seconds() / 60
        if wait > 40:
            log(f"Market closed; next open {nxt.astimezone(NY):%a %H:%M ET}. Nothing to do.")
            return
        log(f"Market opens in {wait:.0f} min - waiting.")
        clock.sleep_until(nxt + timedelta(seconds=5))

    cfg_syms = cfg["universe"]
    snaps = api.snapshots(cfg_syms, feed=cfg["data_feed"])
    bot = Bot(api, cfg, log, clock)
    bot.load_kill(clock.now().astimezone(NY).date())
    if bot.killed:
        log("Kill switch already tripped today - managing exits only.")
    for s in cfg_syms:
        try:
            bot.prev_close[s] = float(snaps[s]["prevDailyBar"]["c"])
        except (KeyError, TypeError):
            log(f"no previous close for {s}; gap fade will skip it today")
    log(f"Session start: {len(cfg_syms)} symbols, strategies "
        f"{', '.join(n + ' ' + s['version'] for n, s in cfg['strategies'].items() if s['enabled'])}")

    end = started + timedelta(minutes=max_minutes)
    while True:
        now = clock.now()
        et = now.astimezone(NY)
        if et.hour * 60 + et.minute >= 16 * 60 or now >= end:
            break
        try:
            bot.step(now)
        except Exception as e:
            log(f"ERROR in step: {type(e).__name__}: {e}", now)
        nxt = (now.replace(second=0, microsecond=0) + timedelta(minutes=1, seconds=6))
        clock.sleep_until(nxt)
    log("Session end.")
    log.trim()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sim", action="store_true", help="fake day, fake broker, runs in seconds")
    ap.add_argument("--max-minutes", type=float, default=350)
    a = ap.parse_args()
    cfg = load_config()
    if a.sim:
        from sim import SimBroker
        broker = SimBroker(cfg)
        log = Logger(os.path.join(HERE, "logs_sim"))
        run(broker, cfg, log, broker, a.max_minutes if a.max_minutes != 350 else 600)
        import reconcile
        reconcile.reconcile(broker, cfg, broker.today, os.path.join(HERE, "logs_sim"))
        return
    from alpaca import Alpaca
    run(Alpaca(), cfg, Logger(os.path.join(HERE, "logs")), RealClock(), a.max_minutes)


if __name__ == "__main__":
    main()
