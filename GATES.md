# Gate status

Updated 2026-10-10 13:42:20 UTC. A strategy is **DEPLOYABLE** only when every gate passes. Everything else keeps paper trading.

## orb v1 - PAPER (3/10)

- PASS **settings**: slippage 1.5/3.0 bps, fees on, 750 days
- PASS **sample**: 5134 closed trades (need 100+)
- FAIL **quality**: Sharpe -1.676 (>1.0), PF 0.885 (>1.3)
- FAIL **pain**: max drawdown 150.53% of allocation (limit 15.0%)
- FAIL **benchmark**: Sharpe -1.676 vs buy-and-hold 1.376
- PASS **neutral**: beta -0.21 (|beta| <= 0.3)
- FAIL **stress**: costs x2: PF 0.751, P&L $-36547.75; plateau 0/10 nudges hold up
- FAIL **recent**: trailing year: 1691 trades, PF 0.835, P&L $-7506.27
- FAIL **risk officer**: KILL (2026-10-09): Loses money on 3 years of real minute data (5,138 trades, PF 0.88, trailing year PF 0.83), no nudge gets PF above 0.92, and its one good paper day (5 trades, +0.95R) is a single trending session, not evidence.
- FAIL **forward**: 5 paper trades over 1 days (need 30+ over 20+); avg +0.95R vs backtest -0.08R (floor -1.31R), PF 5.89

# Slow lane (daily)

## trend v1 - PAPER (7/10)

- PASS **settings**: 2.0 bps per trade, dividends included, 9.71 years
- PASS **sample**: 9.71 years, 38 position changes (need 8+ yrs, 20+ changes)
- PASS **quality**: Sharpe 1.088 vs holding 50% SPY + 50% QQQ 0.944
- FAIL **growth**: CAGR 15.52% vs buy-and-hold 18.34% (allowed 2.0 pts behind)
- PASS **pain**: max drawdown 21.82% vs buy-and-hold 30.87% (need <= 75% of it)
- PASS **consistency**: Sharpe by half: 1.217 vs 1.157, 0.945 vs 0.73 (within 0.25)
- PASS **stress**: costs x2: Sharpe 1.081; plateau 4/4 nudges keep Sharpe near/above buy-and-hold
- PASS **recent**: last 3 yrs: CAGR 21.04%, Sharpe 1.414 vs 1.424
- FAIL **risk officer**: KILL (2026-10-09): Gives up 2.8 pts/yr vs 50/50 SPY+QQQ for a smaller drawdown that rests on ~5 bear-market regimes (38 switches in 9.7 years), still with zero out-of-sample days.
- FAIL **forward**: 0 out-of-sample days since 2026-10-08 (need 60+)

## momentum v1 - PAPER (3/10)

- PASS **settings**: 2.0 bps per trade, dividends included, 9.71 years
- PASS **sample**: 9.71 years, 44 position changes (need 8+ yrs, 20+ changes)
- FAIL **quality**: Sharpe 0.623 vs holding SPY 0.883
- FAIL **growth**: CAGR 11.02% vs buy-and-hold 15.22% (allowed 2.0 pts behind)
- FAIL **pain**: max drawdown 34.89% vs buy-and-hold 33.79% (need <= 75% of it)
- FAIL **consistency**: Sharpe by half: 0.425 vs 0.997, 0.852 vs 0.762 (within 0.25)
- FAIL **stress**: costs x2: Sharpe 0.614; plateau 0/3 nudges keep Sharpe near/above buy-and-hold
- PASS **recent**: last 3 yrs: CAGR 31.61%, Sharpe 1.449 vs 1.484
- FAIL **risk officer**: KILL (2026-10-09): Worse than holding SPY on Sharpe (0.63 vs 0.89), growth (-4.1 pts/yr) and drawdown, inconsistent across halves, and 0/3 parameter nudges hold up.
- FAIL **forward**: 0 out-of-sample days since 2026-10-08 (need 60+)

## voltarget v1 - PAPER (7/10)

- PASS **settings**: 2.0 bps per trade, dividends included, 9.71 years
- PASS **sample**: 9.71 years, 88 position changes (need 8+ yrs, 20+ changes)
- PASS **quality**: Sharpe 0.994 vs holding SPY 0.883
- FAIL **growth**: CAGR 12.81% vs buy-and-hold 15.22% (allowed 2.0 pts behind)
- PASS **pain**: max drawdown 17.82% vs buy-and-hold 33.79% (need <= 75% of it)
- PASS **consistency**: Sharpe by half: 1.188 vs 0.997, 0.816 vs 0.762 (within 0.25)
- PASS **stress**: costs x2: Sharpe 0.99; plateau 8/8 nudges keep Sharpe near/above buy-and-hold
- PASS **recent**: last 3 yrs: CAGR 19.57%, Sharpe 1.49 vs 1.484
- FAIL **risk officer**: KILL (2026-10-09): Halves the drawdown but trails SPY (which Andrew holds as VOO) by 2.4 pts/yr, is 91% SPY today, and has zero forward days to show it beats simply holding a bit of cash.
- FAIL **forward**: 0 out-of-sample days since 2026-10-08 (need 60+)

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
- FAIL **risk officer**: KILL (2026-10-09): Fails the no-edge stress (Sharpe 0.62 vs 0.63 holding the stocks), earns 5.7%/yr vs 15.2% for $1k in SPY, and the live bot trades AGNC, a stock the backtest never tested, so its forward record can't validate v1.
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
- FAIL **risk officer**: KILL (2026-10-09): Its edge is the modeled IV/RV ratio: at a fair 1.0 ratio Sharpe drops from 0.95 to 0.74, at 0.9 to 0.48, and it grows 10 pts/yr slower than SPY.
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
- FAIL **risk officer**: KILL (2026-10-09): Almost entirely priced-in edge: with fair option prices and doubled spreads it returns 0.6%/yr (Sharpe 0.17) and beats holding in only 50% of stocks.
- FAIL **forward**: not paper traded (only the wheel runs live)
