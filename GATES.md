# Gate status

Updated 2026-10-21 21:51:51 UTC. A strategy is **DEPLOYABLE** only when every gate passes. Everything else keeps paper trading.

# Slow lane (daily)

## trend v1 - PAPER (7/10)

- PASS **settings**: 2.0 bps per trade, dividends included, 9.74 years
- PASS **sample**: 9.74 years, 38 position changes (need 8+ yrs, 20+ changes)
- PASS **quality**: Sharpe 1.067 vs holding 50% SPY + 50% QQQ 0.929
- FAIL **growth**: CAGR 15.18% vs buy-and-hold 17.98% (allowed 2.0 pts behind)
- PASS **pain**: max drawdown 21.82% vs buy-and-hold 30.87% (need <= 75% of it)
- PASS **consistency**: Sharpe by half: 1.176 vs 1.126, 0.946 vs 0.731 (within 0.25)
- PASS **stress**: costs x2: Sharpe 1.06; plateau 4/4 nudges keep Sharpe near/above buy-and-hold
- PASS **recent**: last 3 yrs: CAGR 18.66%, Sharpe 1.272 vs 1.309
- FAIL **risk officer**: KILL (2026-10-20): Gives up 2.8 pts/yr vs 50/50 SPY+QQQ for a smaller drawdown that rests on about 5 bear-market episodes; its 7 out-of-sample days match the benchmark exactly (-2.44% vs -2.44%).
- FAIL **forward**: 7 out-of-sample days since 2026-10-08 (need 60+); return -2.44% vs -2.44% buy-and-hold, worst dip 3.76%

## momentum v1 - PAPER (3/10)

- PASS **settings**: 2.0 bps per trade, dividends included, 9.74 years
- PASS **sample**: 9.74 years, 44 position changes (need 8+ yrs, 20+ changes)
- FAIL **quality**: Sharpe 0.601 vs holding SPY 0.876
- FAIL **growth**: CAGR 10.54% vs buy-and-hold 15.06% (allowed 2.0 pts behind)
- FAIL **pain**: max drawdown 34.89% vs buy-and-hold 33.79% (need <= 75% of it)
- FAIL **consistency**: Sharpe by half: 0.393 vs 0.97, 0.841 vs 0.776 (within 0.25)
- FAIL **stress**: costs x2: Sharpe 0.592; plateau 0/3 nudges keep Sharpe near/above buy-and-hold
- PASS **recent**: last 3 yrs: CAGR 28.09%, Sharpe 1.312 vs 1.4
- FAIL **risk officer**: KILL (2026-10-20): Worse than holding SPY on Sharpe (0.60 vs 0.88), growth (-4.5 pts/yr) and drawdown; forward -3.91% vs -0.96% for SPY after 7 days, all from one QQQ bet.
- FAIL **forward**: 7 out-of-sample days since 2026-10-08 (need 60+); return -3.91% vs -0.96% buy-and-hold, worst dip 5.52%

## voltarget v1 - PAPER (7/10)

- PASS **settings**: 2.0 bps per trade, dividends included, 9.74 years
- PASS **sample**: 9.74 years, 88 position changes (need 8+ yrs, 20+ changes)
- PASS **quality**: Sharpe 0.985 vs holding SPY 0.876
- FAIL **growth**: CAGR 12.67% vs buy-and-hold 15.06% (allowed 2.0 pts behind)
- PASS **pain**: max drawdown 17.82% vs buy-and-hold 33.79% (need <= 75% of it)
- PASS **consistency**: Sharpe by half: 1.148 vs 0.97, 0.834 vs 0.776 (within 0.25)
- PASS **stress**: costs x2: Sharpe 0.981; plateau 8/8 nudges keep Sharpe near/above buy-and-hold
- PASS **recent**: last 3 yrs: CAGR 18.11%, Sharpe 1.392 vs 1.4
- FAIL **risk officer**: KILL (2026-10-20): Trails SPY (held as VOO) by 2.4 pts/yr, is 91% SPY today, and its halved drawdown comes from a handful of crashes, with only 7 forward days.
- FAIL **forward**: 7 out-of-sample days since 2026-10-08 (need 60+); return -0.86% vs -0.96% buy-and-hold, worst dip 1.78%

# Options lane

## wheel v1 - PAPER (5/10)

- PASS **settings**: costs on, IV/RV calibrated, 10.49 years
- PASS **sample**: 362 option cycles across stocks (need 100+)
- PASS **quality**: Sharpe 0.887 vs holding the same stocks 0.612
- FAIL **growth**: CAGR 5.66% vs $1k in SPY 15.02% (allowed 2.0 pts behind)
- PASS **pain**: worst drop 12.4% vs holding the stocks 49.14%
- FAIL **no-edge stress**: with options priced fairly and spreads x2: Sharpe 0.604 vs holding 0.612
- FAIL **breadth**: beats holding in 56% of stocks (need 60%+)
- PASS **recent**: last 3 yrs: CAGR 5.02%, Sharpe 0.881 vs holding 0.811
- FAIL **risk officer**: KILL (2026-10-20): Fails the no-edge stress (Sharpe 0.605 vs 0.613 for holding the stocks) and earns 5.7%/yr vs 15.0% for $1k in SPY, with 0 completed paper cycles.
- FAIL **forward**: 0 completed paper option cycles (need 3+)

## covered_call v1 - PAPER (6/10)

- PASS **settings**: costs on, IV/RV calibrated, 10.49 years
- PASS **sample**: 618 option cycles across stocks (need 100+)
- PASS **quality**: Sharpe 1.023 vs holding the same stocks 0.612
- FAIL **growth**: CAGR 5.73% vs $1k in SPY 15.02% (allowed 2.0 pts behind)
- PASS **pain**: worst drop 13.65% vs holding the stocks 49.14%
- FAIL **no-edge stress**: with options priced fairly and spreads x2: Sharpe 0.552 vs holding 0.612
- PASS **breadth**: beats holding in 62% of stocks (need 60%+)
- PASS **recent**: last 3 yrs: CAGR 7.76%, Sharpe 1.649 vs holding 0.811
- FAIL **risk officer**: KILL (2026-10-20): Its edge is the modeled IV/RV ratio: Sharpe falls to 0.55 at fair prices with doubled spreads (below holding's 0.61), and it grows 9 pts/yr slower than SPY.
- FAIL **forward**: not paper traded (only the wheel runs live)

## csp v1 - PAPER (5/10)

- PASS **settings**: costs on, IV/RV calibrated, 10.49 years
- PASS **sample**: 617 option cycles across stocks (need 100+)
- PASS **quality**: Sharpe 1.075 vs holding the same stocks 0.612
- FAIL **growth**: CAGR 3.88% vs $1k in SPY 15.02% (allowed 2.0 pts behind)
- PASS **pain**: worst drop 10.26% vs holding the stocks 49.14%
- FAIL **no-edge stress**: with options priced fairly and spreads x2: Sharpe 0.147 vs holding 0.612
- FAIL **breadth**: beats holding in 50% of stocks (need 60%+)
- PASS **recent**: last 3 yrs: CAGR 5.28%, Sharpe 1.968 vs holding 0.811
- FAIL **risk officer**: KILL (2026-10-20): Almost all of its edge is priced in: with fair option prices and doubled spreads its Sharpe is 0.15, and it beats holding in only 50% of stocks.
- FAIL **forward**: not paper traded (only the wheel runs live)
