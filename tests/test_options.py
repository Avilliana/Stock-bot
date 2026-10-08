"""
Options-lane sanity checks: pricing math, and the wheel's cash/share bookkeeping
on hand-made price paths where the right answer is obvious.

    python tests/test_options.py
"""
import math
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

import options as O  # noqa: E402


def test_pricing():
    S, K, T, r, v = 8.0, 7.5, 30 / 365, 0.04, 0.6
    c, p = O.bs("call", S, K, T, r, v), O.bs("put", S, K, T, r, v)
    assert abs((c - p) - (S - K * math.exp(-r * T))) < 1e-9          # put-call parity
    assert abs(O.implied_vol("put", p, S, K, T, r) - v) < 1e-4       # IV round trip


def frames_for(path):
    idx = pd.bdate_range("2024-01-02", periods=len(path))
    df = pd.DataFrame({"raw": path, "adj": path}, index=idx)
    bil = pd.Series(100.0, index=idx)
    return df, bil.pct_change().fillna(0.0), pd.Series(0.0, index=idx)


def cfg():
    o = O.load_config()["options"]
    return dict(o, vol=dict(o["vol"], rv_days=5, min_iv=0.5))


def test_wheel_put_assigned_then_called_away():
    o = cfg()
    p = o["strategies"]["wheel"]["params"]
    # noisy but flat ~$8 for a while, crash to $6 into the first expiry, then rally to $12
    rng = np.random.default_rng(0)
    n = 160
    path = 8 + rng.normal(0, 0.05, n)
    path[15:40] = np.linspace(8, 6, 25)
    path[40:] = np.linspace(6, 12, n - 40)
    df, br, rt = frames_for(path)
    eq, info = O.simulate("wheel", df, br, rt, p, o, 1.0)
    assert info["assigned"] >= 1, info
    assert info["called_away"] >= 1, info
    assert info["premium_usd"] > 0
    assert eq.iloc[-1] > 1000, eq.iloc[-1]                # bought ~$7.5, sold above basis


def test_covered_call_caps_a_rally():
    o = cfg()
    path = np.linspace(5, 15, 200) + np.random.default_rng(1).normal(0, 0.02, 200)
    df, br, rt = frames_for(path)
    eq_cc, _ = O.simulate("covered_call", df, br, rt, o["strategies"]["covered_call"]["params"], o, 1.0)
    eq_bh = O.buy_and_hold(df, br, o)
    assert eq_cc.iloc[-1] < eq_bh.iloc[-1]


def test_too_expensive_stays_in_cash():
    o = cfg()
    path = np.full(120, 25.0) + np.random.default_rng(2).normal(0, 0.1, 120)
    df, br, rt = frames_for(path)
    eq, info = O.simulate("wheel", df, br, rt, o["strategies"]["wheel"]["params"], o, 1.0)
    assert info["cycles"] == 0 and abs(eq.iloc[-1] - 1000) < 1e-6


if __name__ == "__main__":
    test_pricing()
    test_wheel_put_assigned_then_called_away()
    test_covered_call_caps_a_rally()
    test_too_expensive_stays_in_cash()
    print("ok: options pricing and wheel bookkeeping")
