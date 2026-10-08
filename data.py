"""Turning Alpaca minute bars into trading days, plus the local bar cache."""
import os
import zlib
from datetime import datetime, timedelta, timezone

import numpy as np
import pandas as pd

NY = "America/New_York"
HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, "data")


def bars_to_frame(bars):
    """Alpaca bar dicts -> DataFrame indexed by New York time."""
    if not bars:
        return pd.DataFrame(columns=["o", "h", "l", "c", "v"])
    df = pd.DataFrame(bars)[["t", "o", "h", "l", "c", "v"]]
    df["t"] = pd.to_datetime(df["t"], utc=True).dt.tz_convert(NY)
    return df.set_index("t").sort_index()


def regular_session(df):
    if df.empty:
        return df
    m = df.index.hour * 60 + df.index.minute
    return df[(m >= 570) & (m < 960)]


def frame_to_days(df, first_prev_close=None):
    """Split a regular-session frame into day dicts. prev_close for each day is the
    previous day's last regular-session close in the same frame."""
    if df.empty:
        return []
    df = regular_session(df)
    days = []
    prev_close = first_prev_close
    for date, g in df.groupby(df.index.date):
        mins = (g.index.hour * 60 + g.index.minute).to_numpy()
        days.append({
            "date": str(date), "prev_close": prev_close, "mins": mins,
            "o": g["o"].to_numpy(float), "h": g["h"].to_numpy(float),
            "l": g["l"].to_numpy(float), "c": g["c"].to_numpy(float),
            "v": g["v"].to_numpy(float),
        })
        prev_close = float(g["c"].iloc[-1])
    return days


# -- cache -------------------------------------------------------------------

def cache_path(sym):
    return os.path.join(CACHE, f"{sym}.csv.gz")


def load_cached(sym):
    p = cache_path(sym)
    if not os.path.exists(p):
        return pd.DataFrame(columns=["o", "h", "l", "c", "v"])
    df = pd.read_csv(p)
    df["t"] = pd.to_datetime(df["t"], utc=True).dt.tz_convert(NY)
    return df.set_index("t").sort_index()


def save_cached(sym, df):
    os.makedirs(CACHE, exist_ok=True)
    out = df.copy()
    out.index = out.index.tz_convert("UTC")
    out.index.name = "t"
    out.reset_index().to_csv(cache_path(sym), index=False, compression="gzip")


def refresh_cache(api, symbols, years, feed, log=print):
    """Download missing history (up to yesterday) for each symbol into data/."""
    end = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    start_all = end - timedelta(days=int(365.25 * years) + 7)
    for sym in symbols:
        have = load_cached(sym)
        if not have.empty:
            have = have[have.index >= start_all.astimezone(have.index.tz)]
            start = have.index[-1].tz_convert("UTC").to_pydatetime() + timedelta(minutes=1)
        else:
            start = start_all
        if start >= end:
            log(f"{sym}: cache up to date ({len(have):,} bars)")
            continue
        log(f"{sym}: downloading {start:%Y-%m-%d} -> {end:%Y-%m-%d} ({feed})")
        got = api.bars([sym], start.strftime("%Y-%m-%dT%H:%M:%SZ"),
                       end.strftime("%Y-%m-%dT%H:%M:%SZ"), feed=feed).get(sym, [])
        new = regular_session(bars_to_frame(got))
        df = pd.concat([have, new])
        df = df[~df.index.duplicated(keep="last")].sort_index()
        save_cached(sym, df)
        log(f"{sym}: {len(df):,} bars cached")


# -- synthetic market (for --synthetic tests only) ---------------------------

def synthetic_frame(sym, n_days=320, seed=0):
    """Random-walk minute bars with a little opening momentum and VWAP pull, so the
    pipeline has something to chew on. NOT a model of the real market."""
    rng = np.random.default_rng(zlib.crc32(f"{sym}-{seed}".encode()))
    days = pd.bdate_range("2024-01-02", periods=n_days, tz=NY)
    price = 100 + rng.uniform(0, 300)
    rows, idx = [], []
    for d in days:
        gap = rng.normal(0, 0.008)
        price *= 1 + gap
        drift = rng.normal(0, 0.0004)
        vw_num = vw_den = 0.0
        for k in range(390):
            t = d + pd.Timedelta(minutes=570 + k)
            vol = 0.0012 if k < 30 else 0.0006
            pull = 0.0
            if vw_den:
                pull = -0.02 * (price - vw_num / vw_den) / price
            ret = drift * (1 if k < 60 else 0.3) + pull + rng.normal(0, vol)
            o = price
            c = price * (1 + ret)
            h = max(o, c) * (1 + abs(rng.normal(0, vol / 3)))
            l = min(o, c) * (1 - abs(rng.normal(0, vol / 3)))
            v = float(rng.integers(500, 5000) * (3 if k < 15 else 1))
            vw_num += (h + l + c) / 3 * v
            vw_den += v
            rows.append((o, h, l, c, v))
            idx.append(t)
            price = c
    return pd.DataFrame(rows, index=pd.DatetimeIndex(idx), columns=["o", "h", "l", "c", "v"])
