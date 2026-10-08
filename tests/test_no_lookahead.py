"""
Proves the strategies can't see the future: for every bar i, the decision made
with the full day's data must equal the decision made with only bars 0..i.
That is exactly the situation the live bot is in.

    python -m pytest tests -q        (or: python tests/test_no_lookahead.py)
"""
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

import data as D                                  # noqa: E402
from strategies import STRATEGIES, State, simulate_day  # noqa: E402

CFG = json.load(open(os.path.join(os.path.dirname(HERE), "config.json")))


def truncate(day, i):
    t = dict(day)
    for k in ("mins", "o", "h", "l", "c", "v"):
        t[k] = day[k][: i + 1]
    return t


def test_decisions_match_truncated_data():
    days = D.frame_to_days(D.synthetic_frame("TEST", n_days=12, seed=3))[1:]
    checked = fired = 0
    for name, (prepare, scan) in STRATEGIES.items():
        p = CFG["strategies"][name]["params"]
        for day in days:
            full = prepare(day, p)
            for i in range(1, len(day["mins"]) - 1):
                st = State()
                a = scan(day, full, i, st, p)
                td = truncate(day, i)
                b = scan(td, prepare(td, p), i, State(), p)
                assert (a is None) == (b is None), (name, day["date"], i)
                if a is not None:
                    fired += 1
                    assert a.side == b.side
                    assert np.isclose(a.stop, b.stop) and np.isclose(a.target, b.target)
                checked += 1
    assert fired > 0 and checked > 1000


def test_entry_is_next_bar_open():
    days = D.frame_to_days(D.synthetic_frame("TEST", n_days=30, seed=4))[1:]
    for name in STRATEGIES:
        p = CFG["strategies"][name]["params"]
        for day in days:
            for t in simulate_day("TEST", day, name, p, CFG):
                h, m = map(int, t["entry_time"].split(":"))
                j = int(np.nonzero(day["mins"] == h * 60 + m)[0][0])
                slip = CFG["costs"]["slippage_bps_stock"] / 1e4
                side = 1 if t["side"] == "long" else -1
                assert np.isclose(t["entry"], round(day["o"][j] * (1 + side * slip), 4), atol=1e-3)


if __name__ == "__main__":
    test_decisions_match_truncated_data()
    test_entry_is_next_bar_open()
    print("ok: no look-ahead, entries at next bar open")
