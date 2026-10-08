"""
A fake Alpaca for `python bot.py --sim`: one synthetic trading day, replayed
minute by minute in a few seconds, with bracket orders filling the way the
backtest assumes (market at next bar open, stop checked before target).
It exists to prove the plumbing works without keys or market hours.
"""
import itertools
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import data as D
from alpaca import AlpacaError

NY = ZoneInfo("America/New_York")
ISO = "%Y-%m-%dT%H:%M:%SZ"


class SimBroker:
    def __init__(self, cfg, seed=7):
        self.cfg = cfg
        self.frames, self.prev = {}, {}
        for s in cfg["universe"]:
            df = D.regular_session(D.synthetic_frame(s, n_days=3, seed=seed))
            dates = sorted(set(df.index.date))
            self.prev[s] = float(df[df.index.date == dates[-2]]["c"].iloc[-1])
            self.frames[s] = df[df.index.date == dates[-1]]
        self.today = dates[-1]
        self.t = datetime.combine(self.today, datetime.min.time(), NY).replace(hour=9, minute=20) \
            .astimezone(timezone.utc)
        self.orders_, self.fills_ = [], []
        self.pos = {}          # symbol -> signed qty
        self.cost = {}         # symbol -> avg entry price
        self.realized = 0.0
        self.ids = itertools.count(1)

    # -- clock ------------------------------------------------------------------
    def now(self):
        return self.t

    def sleep_until(self, t):
        while True:
            boundary = self.t.replace(second=0, microsecond=0) + timedelta(minutes=1)
            if boundary > t:
                self.t = max(self.t, t)
                return
            self._process_bar(boundary - timedelta(minutes=1))   # that bar just completed
            self.t = boundary

    def clock(self):
        et = self.t.astimezone(NY)
        m = et.hour * 60 + et.minute
        opn = datetime.combine(self.today, datetime.min.time(), NY).replace(hour=9, minute=30)
        return {"is_open": 570 <= m < 960, "next_open": opn.astimezone(timezone.utc).strftime(ISO)}

    # -- data -------------------------------------------------------------------
    def bars(self, symbols, start_iso, end_iso=None, timeframe="1Min", feed="iex"):
        out = {}
        for s in symbols:
            df = self.frames[s]
            done = df[df.index.tz_convert("UTC") + timedelta(minutes=1) <= self.t]
            out[s] = [{"t": ts.tz_convert("UTC").strftime(ISO), "o": r.o, "h": r.h, "l": r.l,
                       "c": r.c, "v": r.v} for ts, r in done.iterrows()]
        return out

    def snapshots(self, symbols, feed="iex"):
        return {s: {"prevDailyBar": {"c": self.prev[s]}} for s in symbols}

    def asset(self, symbol):
        return {"shortable": True, "easy_to_borrow": True}

    def _last(self, s):
        df = self.frames[s]
        done = df[df.index.tz_convert("UTC") + timedelta(minutes=1) <= self.t]
        return float(done["c"].iloc[-1]) if len(done) else float(df["o"].iloc[0])

    # -- trading ----------------------------------------------------------------
    def _new(self, **kw):
        o = {"id": f"o{next(self.ids)}", "status": "accepted", "filled_at": None, "legs": None,
             "submitted_at": self.t.strftime(ISO), "client_order_id": f"x{next(self.ids)}", **kw}
        return o

    def submit_bracket(self, symbol, qty, side, take_profit, stop_loss, client_id):
        if any(o["client_order_id"] == client_id for o in self.orders_):
            raise AlpacaError(422, "client_order_id must be unique")
        base = self._last(symbol)
        if side == "buy" and not (stop_loss <= base - 0.01 and take_profit >= base + 0.01):
            raise AlpacaError(422, "bracket prices invalid vs base price")
        if side == "sell" and not (stop_loss >= base + 0.01 and take_profit <= base - 0.01):
            raise AlpacaError(422, "bracket prices invalid vs base price")
        exit_side = "sell" if side == "buy" else "buy"
        legs = [self._new(symbol=symbol, qty=str(qty), side=exit_side, type="limit",
                          limit_price=str(take_profit), status="held"),
                self._new(symbol=symbol, qty=str(qty), side=exit_side, type="stop",
                          stop_price=str(stop_loss), status="held")]
        o = self._new(symbol=symbol, qty=str(qty), side=side, type="market", legs=legs)
        o["client_order_id"] = client_id
        self.orders_.append(o)
        return o

    def cancel_order(self, order_id):
        for o in self._all():
            if o["id"] == order_id and o["status"] in ("new", "accepted", "held"):
                o["status"] = "canceled"

    def close_position(self, symbol):
        q = self.pos.get(symbol, 0)
        if not q:
            raise AlpacaError(404, "position not found")
        o = self._new(symbol=symbol, qty=str(abs(q)), side="sell" if q > 0 else "buy", type="market")
        self.orders_.append(o)
        return o

    def positions(self):
        return [{"symbol": s, "qty": str(q), "side": "long" if q > 0 else "short"}
                for s, q in self.pos.items() if q]

    def orders(self, after_iso, status="all"):
        return sorted(self.orders_, key=lambda o: o["submitted_at"], reverse=True)

    def account(self):
        unreal = sum(q * (self._last(s) - self.cost[s]) for s, q in self.pos.items() if q)
        return {"equity": str(100000 + self.realized + unreal), "last_equity": "100000"}

    def fills(self, date):
        return list(self.fills_)

    def _all(self):
        for o in self.orders_:
            yield o
            for x in o.get("legs") or []:
                yield x

    def _fill(self, o, price, ts):
        q = int(o["qty"]) * (1 if o["side"] == "buy" else -1)
        s = o["symbol"]
        cur = self.pos.get(s, 0)
        side = o["side"]
        if o["side"] == "sell" and cur <= 0:
            side = "sell_short"
        if cur == 0 or (cur > 0) == (q > 0):
            self.cost[s] = (self.cost.get(s, 0) * abs(cur) + price * abs(q)) / (abs(cur) + abs(q))
        else:
            self.realized += -q * (price - self.cost[s]) if abs(q) <= abs(cur) else 0
        self.pos[s] = cur + q
        o["status"], o["filled_at"] = "filled", ts.strftime(ISO)
        o["filled_avg_price"] = str(price)
        self.fills_.append({"order_id": o["id"], "symbol": s, "side": side, "qty": o["qty"],
                            "price": str(price), "transaction_time": ts.strftime(ISO)})

    def _process_bar(self, bar_start):
        for s, df in self.frames.items():
            key = bar_start.astimezone(NY).replace(tzinfo=None)
            rows = df[df.index.tz_localize(None) == key]
            if rows.empty:
                continue
            b = rows.iloc[0]
            # market orders sent before or in the first seconds of this bar fill at
            # its open (the bot sends at :06, a live market order fills right away)
            cutoff = (bar_start + timedelta(seconds=30)).strftime(ISO)
            for o in self.orders_:
                if o["symbol"] == s and o["status"] == "accepted" and o["type"] == "market":
                    if o["submitted_at"] <= cutoff:
                        self._fill(o, float(b.o), bar_start)
                        for x in o.get("legs") or []:
                            x["status"] = "new"
            # live bracket legs: stop first, then target
            for o in self.orders_:
                legs = o.get("legs") or []
                if o["symbol"] != s or not legs or legs[0]["status"] != "new":
                    continue
                tp, sl = legs
                long_ = o["side"] == "buy"
                stp, lim = float(sl["stop_price"]), float(tp["limit_price"])
                if (long_ and b.l <= stp) or (not long_ and b.h >= stp):
                    px = min(b.o, stp) if long_ else max(b.o, stp)
                    self._fill(sl, float(px), bar_start)
                    tp["status"] = "canceled"
                elif (long_ and b.h >= lim) or (not long_ and b.l <= lim):
                    px = max(b.o, lim) if long_ else min(b.o, lim)
                    self._fill(tp, float(px), bar_start)
                    sl["status"] = "canceled"
