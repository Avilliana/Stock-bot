# Gate status

Updated 2026-10-17 13:53:29 UTC. A strategy is **DEPLOYABLE** only when every gate passes. Everything else keeps paper trading.

## orb v1 - PAPER (3/10)

- PASS **settings**: slippage 1.5/3.0 bps, fees on, 750 days
- PASS **sample**: 5125 closed trades (need 100+)
- FAIL **quality**: Sharpe -1.648 (>1.0), PF 0.887 (>1.3)
- FAIL **pain**: max drawdown 148.37% of allocation (limit 15.0%)
- FAIL **benchmark**: Sharpe -1.648 vs buy-and-hold 1.364
- PASS **neutral**: beta -0.217 (|beta| <= 0.3)
- FAIL **stress**: costs x2: PF 0.753, P&L $-36194.0; plateau 0/10 nudges hold up
- FAIL **recent**: trailing year: 1685 trades, PF 0.832, P&L $-7603.5
- FAIL **risk officer**: KILL (2026-10-16): Loses on 3 years of real minute data (5,134 trades, PF 0.885, 0.75 at costs x2, trailing year 0.835, 0/10 nudges hold); 36 paper trades at +0.10R on optimistic fills are within noise of that.
- FAIL **forward**: 36 paper trades over 6 days (need 30+ over 20+); avg +0.10R vs backtest -0.08R (floor -0.54R), PF 1.17

# Slow lane (daily)

## trend v1 - PAPER (7/10)

- PASS **settings**: 2.0 bps per trade, dividends included, 9.73 years
- PASS **sample**: 9.73 years, 38 position changes (need 8+ yrs, 20+ changes)
- PASS **quality**: Sharpe 1.075 vs holding 50% SPY + 50% QQQ 0.935
- FAIL **growth**: CAGR 15.31% vs buy-and-hold 18.12% (allowed 2.0 pts behind)
- PASS **pain**: max drawdown 21.82% vs buy-and-hold 30.87% (need <= 75% of it)
- PASS **consistency**: Sharpe by half: 1.207 vs 1.15, 0.93 vs 0.72 (within 0.25)
- PASS **stress**: costs x2: Sharpe 1.069; plateau 4/4 nudges keep Sharpe near/above buy-and-hold
- PASS **recent**: last 3 yrs: CAGR 19.09%, Sharpe 1.3 vs 1.331
- FAIL **risk officer**: KILL (2026-10-16): Gives up 2.8 pts/yr vs 50/50 SPY+QQQ for a smaller drawdown resting on ~5 bear-market episodes; 5 out-of-sample days identical to its benchmark (-1.45% vs -1.45%).
- FAIL **forward**: 5 out-of-sample days since 2026-10-08 (need 60+); return -1.45% vs -1.45% buy-and-hold, worst dip 2.06%

## momentum v1 - PAPER (3/10)

- PASS **settings**: 2.0 bps per trade, dividends included, 9.73 years
- PASS **sample**: 9.73 years, 44 position changes (need 8+ yrs, 20+ changes)
- FAIL **quality**: Sharpe 0.609 vs holding SPY 0.88
- FAIL **growth**: CAGR 10.7% vs buy-and-hold 15.16% (allowed 2.0 pts behind)
- FAIL **pain**: max drawdown 34.89% vs buy-and-hold 33.79% (need <= 75% of it)
- FAIL **consistency**: Sharpe by half: 0.412 vs 0.997, 0.836 vs 0.757 (within 0.25)
- FAIL **stress**: costs x2: Sharpe 0.6; plateau 0/3 nudges keep Sharpe near/above buy-and-hold
- PASS **recent**: last 3 yrs: CAGR 28.82%, Sharpe 1.343 vs 1.412
- FAIL **risk officer**: KILL (2026-10-16): Worse than holding SPY on Sharpe (0.61 vs 0.88), growth (-4.4 pts/yr) and drawdown, inconsistent across halves, 0/3 nudges hold up; forward -2.62% vs -0.28%.
- FAIL **forward**: 5 out-of-sample days since 2026-10-08 (need 60+); return -2.62% vs -0.28% buy-and-hold, worst dip 3.1%

## voltarget v1 - PAPER (7/10)

- PASS **settings**: 2.0 bps per trade, dividends included, 9.73 years
- PASS **sample**: 9.73 years, 88 position changes (need 8+ yrs, 20+ changes)
- PASS **quality**: Sharpe 0.991 vs holding SPY 0.88
- FAIL **growth**: CAGR 12.76% vs buy-and-hold 15.16% (allowed 2.0 pts behind)
- PASS **pain**: max drawdown 17.82% vs buy-and-hold 33.79% (need <= 75% of it)
- PASS **consistency**: Sharpe by half: 1.188 vs 0.997, 0.809 vs 0.757 (within 0.25)
- PASS **stress**: costs x2: Sharpe 0.987; plateau 8/8 nudges keep Sharpe near/above buy-and-hold
- PASS **recent**: last 3 yrs: CAGR 18.28%, Sharpe 1.404 vs 1.412
- FAIL **risk officer**: KILL (2026-10-16): Trails SPY (held as VOO) by 2.4 pts/yr, is 91% SPY today, and its halved drawdown comes from a handful of crashes with only 5 forward days.
- FAIL **forward**: 5 out-of-sample days since 2026-10-08 (need 60+); return -0.24% vs -0.28% buy-and-hold, worst dip 1.04%

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
- FAIL **risk officer**: KILL (2026-10-16): Fails the no-edge stress (Sharpe 0.62 vs 0.64 holding the stocks) and earns 5.8%/yr vs 15.2% for $1k in SPY; the live SNAP put is now ~1% OTM and likely spans an unconfirmed earnings date.
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
- FAIL **risk officer**: KILL (2026-10-16): Its edge is the modeled IV/RV ratio: Sharpe falls from 0.96 to 0.57 at fair prices with doubled spreads, and it grows 10 pts/yr slower than SPY.
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
- FAIL **risk officer**: KILL (2026-10-16): Almost entirely priced-in edge: with fair option prices and doubled spreads its Sharpe is 0.17 and it beats holding in only 50% of stocks.
- FAIL **forward**: not paper traded (only the wheel runs live)
