# Gate status

Updated 2026-10-14 22:28:08 UTC. A strategy is **DEPLOYABLE** only when every gate passes. Everything else keeps paper trading.

## orb v1 - PAPER (3/10)

- PASS **settings**: slippage 1.5/3.0 bps, fees on, 750 days
- PASS **sample**: 5134 closed trades (need 100+)
- FAIL **quality**: Sharpe -1.676 (>1.0), PF 0.885 (>1.3)
- FAIL **pain**: max drawdown 150.53% of allocation (limit 15.0%)
- FAIL **benchmark**: Sharpe -1.676 vs buy-and-hold 1.376
- PASS **neutral**: beta -0.21 (|beta| <= 0.3)
- FAIL **stress**: costs x2: PF 0.751, P&L $-36547.75; plateau 0/10 nudges hold up
- FAIL **recent**: trailing year: 1691 trades, PF 0.835, P&L $-7506.27
- FAIL **risk officer**: KILL (2026-10-13): Still loses on 3 years of real minute data (5,134 trades, PF 0.885, 0.75 at costs x2, trailing year 0.835, 0/10 nudges hold), and its paper average is sliding toward that (+0.95R, -0.02R, -0.54R by day; 18 trades, +0.07R overall).
- FAIL **forward**: 25 paper trades over 4 days (need 30+ over 20+); avg +0.12R vs backtest -0.08R (floor -0.63R), PF 1.20

# Slow lane (daily)

## trend v1 - PAPER (7/10)

- PASS **settings**: 2.0 bps per trade, dividends included, 9.72 years
- PASS **sample**: 9.72 years, 38 position changes (need 8+ yrs, 20+ changes)
- PASS **quality**: Sharpe 1.087 vs holding 50% SPY + 50% QQQ 0.943
- FAIL **growth**: CAGR 15.5% vs buy-and-hold 18.32% (allowed 2.0 pts behind)
- PASS **pain**: max drawdown 21.82% vs buy-and-hold 30.87% (need <= 75% of it)
- PASS **consistency**: Sharpe by half: 1.203 vs 1.147, 0.958 vs 0.739 (within 0.25)
- PASS **stress**: costs x2: Sharpe 1.081; plateau 4/4 nudges keep Sharpe near/above buy-and-hold
- PASS **recent**: last 3 yrs: CAGR 20.12%, Sharpe 1.363 vs 1.382
- FAIL **risk officer**: KILL (2026-10-13): Gives up 2.8 pts/yr vs 50/50 SPY+QQQ for a smaller drawdown that rests on ~5 bear-market episodes in 9.7 years, with 2 out-of-sample days identical to its benchmark.
- FAIL **forward**: 3 out-of-sample days since 2026-10-08 (need 60+); return -0.01% vs -0.01% buy-and-hold, worst dip 0.55%

## momentum v1 - PAPER (3/10)

- PASS **settings**: 2.0 bps per trade, dividends included, 9.72 years
- PASS **sample**: 9.72 years, 44 position changes (need 8+ yrs, 20+ changes)
- FAIL **quality**: Sharpe 0.62 vs holding SPY 0.885
- FAIL **growth**: CAGR 10.95% vs buy-and-hold 15.27% (allowed 2.0 pts behind)
- FAIL **pain**: max drawdown 34.89% vs buy-and-hold 33.79% (need <= 75% of it)
- FAIL **consistency**: Sharpe by half: 0.409 vs 0.995, 0.864 vs 0.77 (within 0.25)
- FAIL **stress**: costs x2: Sharpe 0.611; plateau 0/3 nudges keep Sharpe near/above buy-and-hold
- PASS **recent**: last 3 yrs: CAGR 30.19%, Sharpe 1.397 vs 1.456
- FAIL **risk officer**: KILL (2026-10-13): Worse than holding SPY on Sharpe (0.62 vs 0.89), growth (-4.3 pts/yr) and drawdown, inconsistent across halves, 0/3 nudges hold up.
- FAIL **forward**: 3 out-of-sample days since 2026-10-08 (need 60+); return -0.54% vs 0.53% buy-and-hold, worst dip 1.02%

## voltarget v1 - PAPER (7/10)

- PASS **settings**: 2.0 bps per trade, dividends included, 9.72 years
- PASS **sample**: 9.72 years, 88 position changes (need 8+ yrs, 20+ changes)
- PASS **quality**: Sharpe 0.997 vs holding SPY 0.885
- FAIL **growth**: CAGR 12.85% vs buy-and-hold 15.27% (allowed 2.0 pts behind)
- PASS **pain**: max drawdown 17.82% vs buy-and-hold 33.79% (need <= 75% of it)
- PASS **consistency**: Sharpe by half: 1.185 vs 0.995, 0.825 vs 0.77 (within 0.25)
- PASS **stress**: costs x2: Sharpe 0.993; plateau 8/8 nudges keep Sharpe near/above buy-and-hold
- PASS **recent**: last 3 yrs: CAGR 19.02%, Sharpe 1.455 vs 1.456
- FAIL **risk officer**: KILL (2026-10-13): Trails SPY (held as VOO) by 2.4 pts/yr, is 91% SPY today, and its halved drawdown comes from a handful of crashes with only 2 forward days.
- FAIL **forward**: 3 out-of-sample days since 2026-10-08 (need 60+); return 0.48% vs 0.53% buy-and-hold, worst dip 0.06%

# Options lane

## wheel v1 - PAPER (5/10)

- PASS **settings**: costs on, IV/RV calibrated, 10.46 years
- PASS **sample**: 358 option cycles across stocks (need 100+)
- PASS **quality**: Sharpe 0.899 vs holding the same stocks 0.637
- FAIL **growth**: CAGR 5.75% vs $1k in SPY 15.23% (allowed 2.0 pts behind)
- PASS **pain**: worst drop 12.47% vs holding the stocks 49.14%
- FAIL **no-edge stress**: with options priced fairly and spreads x2: Sharpe 0.624 vs holding 0.637
- FAIL **breadth**: beats holding in 56% of stocks (need 60%+)
- PASS **recent**: last 3 yrs: CAGR 5.45%, Sharpe 0.945 vs holding 0.886
- FAIL **risk officer**: KILL (2026-10-13): Fails the no-edge stress (Sharpe 0.62 vs 0.64 holding the stocks) and earns 5.8%/yr vs 15.2% for $1k in SPY; the live SNAP put leans on SNAP's modeled 1.29 IV/RV ratio and likely spans an earnings date.
- FAIL **forward**: 0 completed paper option cycles (need 3+)

## covered_call v1 - PAPER (5/10)

- PASS **settings**: costs on, IV/RV calibrated, 10.46 years
- PASS **sample**: 601 option cycles across stocks (need 100+)
- PASS **quality**: Sharpe 0.956 vs holding the same stocks 0.637
- FAIL **growth**: CAGR 5.25% vs $1k in SPY 15.23% (allowed 2.0 pts behind)
- PASS **pain**: worst drop 14.0% vs holding the stocks 49.14%
- FAIL **no-edge stress**: with options priced fairly and spreads x2: Sharpe 0.573 vs holding 0.637
- FAIL **breadth**: beats holding in 56% of stocks (need 60%+)
- PASS **recent**: last 3 yrs: CAGR 7.64%, Sharpe 1.692 vs holding 0.886
- FAIL **risk officer**: KILL (2026-10-13): Its edge is the modeled IV/RV ratio: Sharpe falls from 0.96 to 0.57 at fair prices with doubled spreads, and it grows 10 pts/yr slower than SPY.
- FAIL **forward**: not paper traded (only the wheel runs live)

## csp v1 - PAPER (5/10)

- PASS **settings**: costs on, IV/RV calibrated, 10.46 years
- PASS **sample**: 613 option cycles across stocks (need 100+)
- PASS **quality**: Sharpe 1.08 vs holding the same stocks 0.637
- FAIL **growth**: CAGR 3.9% vs $1k in SPY 15.23% (allowed 2.0 pts behind)
- PASS **pain**: worst drop 10.38% vs holding the stocks 49.14%
- FAIL **no-edge stress**: with options priced fairly and spreads x2: Sharpe 0.174 vs holding 0.637
- FAIL **breadth**: beats holding in 50% of stocks (need 60%+)
- PASS **recent**: last 3 yrs: CAGR 5.68%, Sharpe 2.076 vs holding 0.886
- FAIL **risk officer**: KILL (2026-10-13): Almost entirely priced-in edge: with fair option prices and doubled spreads its Sharpe is 0.17 and it beats holding in only 50% of stocks.
- FAIL **forward**: not paper traded (only the wheel runs live)
