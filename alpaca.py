"""
Small Alpaca REST client. PAPER ONLY: the trading URL is hard-coded to the paper
endpoint and there is no switch to change it.

Keys come from environment variables (GitHub secrets in the cloud):
    ALPACA_API_KEY_ID, ALPACA_API_SECRET_KEY
"""
import os
import time

import requests

PAPER_URL = "https://paper-api.alpaca.markets"
DATA_URL = "https://data.alpaca.markets"


class AlpacaError(Exception):
    def __init__(self, status, body):
        super().__init__(f"HTTP {status}: {body[:300]}")
        self.status = status
        self.body = body


class Alpaca:
    def __init__(self, key=None, secret=None):
        key = key or os.environ.get("ALPACA_API_KEY_ID")
        secret = secret or os.environ.get("ALPACA_API_SECRET_KEY")
        if not key or not secret:
            raise SystemExit("Missing ALPACA_API_KEY_ID / ALPACA_API_SECRET_KEY "
                             "(add them as GitHub secrets, or set them in your shell).")
        self.s = requests.Session()
        self.s.headers.update({"APCA-API-KEY-ID": key, "APCA-API-SECRET-KEY": secret})

    # -- plumbing ----------------------------------------------------------
    def _req(self, method, url, **kw):
        for attempt in range(5):
            try:
                r = self.s.request(method, url, timeout=20, **kw)
            except requests.RequestException:
                if attempt == 4:
                    raise
                time.sleep(2 ** attempt)
                continue
            if r.status_code in (429, 500, 502, 503, 504) and attempt < 4:
                time.sleep(float(r.headers.get("Retry-After", 2 ** attempt)))
                continue
            if r.status_code >= 400:
                raise AlpacaError(r.status_code, r.text)
            return r.json() if r.text else None
        raise AlpacaError(0, "retries exhausted")

    def _t(self, method, path, **kw):
        return self._req(method, PAPER_URL + path, **kw)

    def _d(self, path, **kw):
        return self._req("GET", DATA_URL + path, **kw)

    # -- trading -----------------------------------------------------------
    def account(self):
        return self._t("GET", "/v2/account")

    def clock(self):
        return self._t("GET", "/v2/clock")

    def positions(self):
        return self._t("GET", "/v2/positions")

    def orders(self, after_iso, status="all"):
        out, until = [], None
        while True:
            params = {"status": status, "after": after_iso, "limit": 500,
                      "nested": "true", "direction": "desc"}
            if until:
                params["until"] = until
            page = self._t("GET", "/v2/orders", params=params)
            out.extend(page)
            if len(page) < 500:
                return out
            until = page[-1]["submitted_at"]

    def asset(self, symbol):
        return self._t("GET", f"/v2/assets/{symbol}")

    def submit_bracket(self, symbol, qty, side, take_profit, stop_loss, client_id):
        body = {
            "symbol": symbol, "qty": str(qty), "side": side, "type": "market",
            "time_in_force": "day", "order_class": "bracket",
            "take_profit": {"limit_price": f"{take_profit:.2f}"},
            "stop_loss": {"stop_price": f"{stop_loss:.2f}"},
            "client_order_id": client_id,
        }
        return self._t("POST", "/v2/orders", json=body)

    def cancel_order(self, order_id):
        try:
            self._t("DELETE", f"/v2/orders/{order_id}")
        except AlpacaError as e:
            if e.status not in (404, 422):
                raise

    def close_position(self, symbol):
        try:
            return self._t("DELETE", f"/v2/positions/{symbol}")
        except AlpacaError as e:
            if e.status != 404:
                raise

    def fills(self, date):
        out, token = [], None
        while True:
            params = {"date": date, "page_size": 100, "direction": "asc"}
            if token:
                params["page_token"] = token
            page = self._t("GET", "/v2/account/activities/FILL", params=params)
            out.extend(page)
            if len(page) < 100:
                return out
            token = page[-1]["id"]

    # -- market data -------------------------------------------------------
    def bars(self, symbols, start_iso, end_iso=None, timeframe="1Min", feed="iex", adjustment="split"):
        """Returns {symbol: [bar, ...]} following every page."""
        out = {s: [] for s in symbols}
        token = None
        while True:
            params = {"symbols": ",".join(symbols), "timeframe": timeframe,
                      "start": start_iso, "limit": 10000, "adjustment": adjustment,
                      "feed": feed, "sort": "asc"}
            if end_iso:
                params["end"] = end_iso
            if token:
                params["page_token"] = token
            page = self._d("/v2/stocks/bars", params=params)
            for sym, bs in (page.get("bars") or {}).items():
                out.setdefault(sym, []).extend(bs)
            token = page.get("next_page_token")
            if not token:
                return out

    # -- options -------------------------------------------------------------
    def option_bars(self, symbols, start, end, timeframe="1Day"):
        out, token = {}, None
        while True:
            params = {"symbols": ",".join(symbols), "timeframe": timeframe, "start": start,
                      "end": end, "limit": 10000}
            if token:
                params["page_token"] = token
            page = self._d("/v1beta1/options/bars", params=params)
            for sym, bs in (page.get("bars") or {}).items():
                out.setdefault(sym, []).extend(bs)
            token = page.get("next_page_token")
            if not token:
                return out

    def option_chain(self, underlying, **params):
        """Snapshots (quotes, greeks, IV) for an underlying's contracts. Free plan = indicative feed."""
        out, token = {}, None
        while True:
            q = dict(params, limit=1000)
            if token:
                q["page_token"] = token
            page = self._d(f"/v1beta1/options/snapshots/{underlying}", params=q)
            out.update(page.get("snapshots") or {})
            token = page.get("next_page_token")
            if not token:
                return out

    def option_contracts(self, **params):
        out, token = [], None
        while True:
            q = dict(params, limit=1000)
            if token:
                q["page_token"] = token
            page = self._t("GET", "/v2/options/contracts", params=q)
            out.extend(page.get("option_contracts") or [])
            token = page.get("next_page_token")
            if not token:
                return out

    def submit_option(self, symbol, qty, side, limit_price, intent, client_id):
        body = {"symbol": symbol, "qty": str(qty), "side": side, "type": "limit",
                "limit_price": f"{limit_price:.2f}", "time_in_force": "day",
                "position_intent": intent, "client_order_id": client_id}
        return self._t("POST", "/v2/orders", json=body)

    def submit_stock(self, symbol, qty, side, client_id):
        body = {"symbol": symbol, "qty": str(qty), "side": side, "type": "market",
                "time_in_force": "day", "client_order_id": client_id}
        return self._t("POST", "/v2/orders", json=body)

    def activities(self, kinds, after_iso):
        return self._t("GET", "/v2/account/activities",
                       params={"activity_types": ",".join(kinds), "after": after_iso, "direction": "asc",
                               "page_size": 100})

    def snapshots(self, symbols, feed="iex"):
        return self._d("/v2/stocks/snapshots",
                       params={"symbols": ",".join(symbols), "feed": feed})
