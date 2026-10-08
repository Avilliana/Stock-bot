"""
Live vs backtest parity: run the live bot against the fake broker for one day,
backtest the same day, and check the live entries are exactly the ones the
backtest took (same strategy, symbol, side, minute).

Each strategy runs alone here. With all three on, the live bot holds one position
per symbol, so it skips some signals the backtest takes - that difference is
expected and is listed in the README.

    python tests/test_parity.py
"""
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

import bot          # noqa: E402
import data as D    # noqa: E402
import reconcile    # noqa: E402
from sim import SimBroker              # noqa: E402
from strategies import simulate_day    # noqa: E402


def test_live_entries_match_backtest():
    for name in bot.load_config()["strategies"]:
        check_one(name)


def check_one(only):
    cfg = bot.load_config()
    for n, s in cfg["strategies"].items():
        s["enabled"] = n == only
    broker = SimBroker(cfg)
    with tempfile.TemporaryDirectory() as d:
        bot.run(broker, cfg, bot.Logger(d), broker, 600)
        reconcile.reconcile(broker, cfg, broker.today, d)
        import csv
        with open(os.path.join(d, "trades.csv"), newline="") as f:
            live = list(csv.DictReader(f))
    assert live, "live sim made no trades"
    bt = set()
    for sym, df in broker.frames.items():
        day = D.frame_to_days(df, broker.prev[sym])[0]
        for name, s in cfg["strategies"].items():
            if not s["enabled"]:
                continue
            for t in simulate_day(sym, day, name, s["params"], cfg):
                bt.add((t["strategy"], sym, t["side"], t["entry_time"]))
    missing = [(t["strategy"], t["symbol"], t["side"], t["entry_time"]) for t in live
               if (t["strategy"], t["symbol"], t["side"], t["entry_time"]) not in bt]
    live_keys = {(t["strategy"], t["symbol"], t["side"], t["entry_time"]) for t in live}
    extra = sorted(bt - live_keys)
    assert not missing, f"{only}: live trades the backtest never took: {missing}"
    assert not extra, f"{only}: backtest trades the live bot missed: {extra}"
    assert broker.positions() == [], "positions left open after the close"
    print(f"ok {only}: {len(live)} live trades == {len(bt)} backtest trades")


if __name__ == "__main__":
    test_live_entries_match_backtest()
