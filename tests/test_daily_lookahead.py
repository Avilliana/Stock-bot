"""
Slow-lane look-ahead check: the weights for any day must be the same whether the
data stops that day or runs to the end. (That's the position the live record is in.)

    python tests/test_daily_lookahead.py
"""
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

import daily  # noqa: E402


def test_weights_never_use_future_prices():
    cfg = daily.load_config()
    d = cfg["daily"]
    px = daily.synthetic_closes(d["symbols"], n=900)
    for name, s in d["strategies"].items():
        f = daily.DAILY[name]
        full = f(px, s["params"], d["cash"])
        for t in range(300, len(px), 37):
            cut = f(px.iloc[: t + 1], s["params"], d["cash"])
            assert np.allclose(cut.iloc[-1].values, full.iloc[t].values), (name, px.index[t])
        # and changing a future price can't change today's weight
        bumped = px.copy()
        bumped.iloc[600:] *= 1.5
        assert np.allclose(f(bumped, s["params"], d["cash"]).iloc[:600].values, full.iloc[:600].values), name


if __name__ == "__main__":
    test_weights_never_use_future_prices()
    print("ok: slow-lane weights never use future prices")
