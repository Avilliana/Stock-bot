# Gate status

Updated 2026-10-19 23:23:12 UTC. A strategy is **DEPLOYABLE** only when every gate passes. Everything else keeps paper trading.

## orb v2 - PAPER (2/10)

- FAIL **settings**: report is for an older version/params - re-run backtest
- PASS **sample**: 5125 closed trades (need 100+)
- FAIL **quality**: Sharpe -1.648 (>1.0), PF 0.887 (>1.3)
- FAIL **pain**: max drawdown 148.37% of allocation (limit 15.0%)
- FAIL **benchmark**: Sharpe -1.648 vs buy-and-hold 1.364
- PASS **neutral**: beta -0.217 (|beta| <= 0.3)
- FAIL **stress**: costs x2: PF 0.753, P&L $-36194.0; plateau 0/10 nudges hold up
- FAIL **recent**: trailing year: 1685 trades, PF 0.832, P&L $-7603.5
- FAIL **risk officer**: KILL (2026-10-19): No v2 backtest exists yet (re-runs on this push) and v1 lost over 3 years of real minute data (5,125 trades, PF 0.887, 0.75 at costs x2, trailing year 0.83); a longer opening range is a hypothesis drawn from 44 paper trades, not evidence.
- FAIL **forward**: 0 paper trades over 0 days (need 30+ over 20+)

# Slow lane (daily)

## trend v1 - PAPER (7/10)

- PASS **settings**: 2.0 bps per trade, dividends included, 9.73 years
- PASS **sample**: 9.73 years, 38 position changes (need 8+ yrs, 20+ changes)
- PASS **quality**: Sharpe 1.061 vs holding 50% SPY + 50% QQQ 0.925
- FAIL **growth**: CAGR 15.09% vs buy-and-hold 17.89% (allowed 2.0 pts behind)
- PASS **pain**: max drawdown 21.82% vs buy-and-hold 30.87% (need <= 75% of it)
- PASS **consistency**: Sharpe by half: 1.207 vs 1.15, 0.899 vs 0.701 (within 0.25)
- PASS **stress**: costs x2: Sharpe 1.055; plateau 4/4 nudges keep Sharpe near/above buy-and-hold
- PASS **recent**: last 3 yrs: CAGR 18.15%, Sharpe 1.242 vs 1.284
- FAIL **risk officer**: KILL (2026-10-19): Gives up 2.8 pts/yr vs 50/50 SPY+QQQ for a smaller drawdown resting on ~5 bear-market episodes; 6 out-of-sample days identical to its benchmark (-3.23% vs -3.23%).
- FAIL **forward**: 6 out-of-sample days since 2026-10-08 (need 60+); return -3.23% vs -3.23% buy-and-hold, worst dip 3.76%

## momentum v1 - PAPER (3/10)

- PASS **settings**: 2.0 bps per trade, dividends included, 9.73 years
- PASS **sample**: 9.73 years, 44 position changes (need 8+ yrs, 20+ changes)
- FAIL **quality**: Sharpe 0.595 vs holding SPY 0.874
- FAIL **growth**: CAGR 10.4% vs buy-and-hold 15.02% (allowed 2.0 pts behind)
- FAIL **pain**: max drawdown 34.89% vs buy-and-hold 33.79% (need <= 75% of it)
- FAIL **consistency**: Sharpe by half: 0.412 vs 0.997, 0.806 vs 0.743 (within 0.25)
- FAIL **stress**: costs x2: Sharpe 0.586; plateau 0/3 nudges keep Sharpe near/above buy-and-hold
- PASS **recent**: last 3 yrs: CAGR 27.44%, Sharpe 1.287 vs 1.377
- FAIL **risk officer**: KILL (2026-10-19): Worse than holding SPY on Sharpe (0.60 vs 0.87), growth (-4.6 pts/yr) and drawdown; forward -5.05% vs -1.38% for SPY after 6 days.
- FAIL **forward**: 6 out-of-sample days since 2026-10-08 (need 60+); return -5.05% vs -1.38% buy-and-hold, worst dip 5.52%

## voltarget v1 - PAPER (7/10)

- PASS **settings**: 2.0 bps per trade, dividends included, 9.73 years
- PASS **sample**: 9.73 years, 88 position changes (need 8+ yrs, 20+ changes)
- PASS **quality**: Sharpe 0.982 vs holding SPY 0.874
- FAIL **growth**: CAGR 12.64% vs buy-and-hold 15.02% (allowed 2.0 pts behind)
- PASS **pain**: max drawdown 17.82% vs buy-and-hold 33.79% (need <= 75% of it)
- PASS **consistency**: Sharpe by half: 1.188 vs 0.997, 0.793 vs 0.743 (within 0.25)
- PASS **stress**: costs x2: Sharpe 0.978; plateau 8/8 nudges keep Sharpe near/above buy-and-hold
- PASS **recent**: last 3 yrs: CAGR 17.72%, Sharpe 1.365 vs 1.377
- FAIL **risk officer**: KILL (2026-10-19): Trails SPY (held as VOO) by 2.4 pts/yr, is 91% SPY today, and its halved drawdown comes from a handful of crashes with only 6 forward days.
- FAIL **forward**: 6 out-of-sample days since 2026-10-08 (need 60+); return -1.24% vs -1.38% buy-and-hold, worst dip 1.78%

# Options lane

## wheel v1 - PAPER (5/10)

- PASS **settings**: costs on, IV/RV calibrated, 10.48 years
- PASS **sample**: 362 option cycles across stocks (need 100+)
- PASS **quality**: Sharpe 0.888 vs holding the same stocks 0.613
- FAIL **growth**: CAGR 5.66% vs $1k in SPY 14.98% (allowed 2.0 pts behind)
- PASS **pain**: worst drop 12.4% vs holding the stocks 49.14%
- FAIL **no-edge stress**: with options priced fairly and spreads x2: Sharpe 0.605 vs holding 0.613
- FAIL **breadth**: beats holding in 56% of stocks (need 60%+)
- PASS **recent**: last 3 yrs: CAGR 4.85%, Sharpe 0.852 vs holding 0.79
- FAIL **risk officer**: KILL (2026-10-19): Fails the no-edge stress (Sharpe 0.605 vs 0.613 holding the stocks) and earns 5.7%/yr vs 15.0% for $1k in SPY, with 0 completed paper cycles.
- FAIL **forward**: 0 completed paper option cycles (need 3+)

## covered_call v1 - PAPER (6/10)

- PASS **settings**: costs on, IV/RV calibrated, 10.48 years
- PASS **sample**: 618 option cycles across stocks (need 100+)
- PASS **quality**: Sharpe 1.023 vs holding the same stocks 0.613
- FAIL **growth**: CAGR 5.73% vs $1k in SPY 14.98% (allowed 2.0 pts behind)
- PASS **pain**: worst drop 13.65% vs holding the stocks 49.14%
- FAIL **no-edge stress**: with options priced fairly and spreads x2: Sharpe 0.551 vs holding 0.613
- PASS **breadth**: beats holding in 62% of stocks (need 60%+)
- PASS **recent**: last 3 yrs: CAGR 7.57%, Sharpe 1.606 vs holding 0.79
- FAIL **risk officer**: KILL (2026-10-19): Its edge is the modeled IV/RV ratio: Sharpe falls from 1.02 to 0.55 at fair prices with doubled spreads (below holding's 0.61), and it grows 9 pts/yr slower than SPY.
- FAIL **forward**: not paper traded (only the wheel runs live)

## csp v1 - PAPER (5/10)

- PASS **settings**: costs on, IV/RV calibrated, 10.48 years
- PASS **sample**: 617 option cycles across stocks (need 100+)
- PASS **quality**: Sharpe 1.074 vs holding the same stocks 0.613
- FAIL **growth**: CAGR 3.88% vs $1k in SPY 14.98% (allowed 2.0 pts behind)
- PASS **pain**: worst drop 10.26% vs holding the stocks 49.14%
- FAIL **no-edge stress**: with options priced fairly and spreads x2: Sharpe 0.146 vs holding 0.613
- FAIL **breadth**: beats holding in 50% of stocks (need 60%+)
- PASS **recent**: last 3 yrs: CAGR 5.1%, Sharpe 1.893 vs holding 0.79
- FAIL **risk officer**: KILL (2026-10-19): Almost entirely priced-in edge: with fair option prices and doubled spreads its Sharpe is 0.15, and it beats holding in only 50% of stocks.
- FAIL **forward**: not paper traded (only the wheel runs live)
