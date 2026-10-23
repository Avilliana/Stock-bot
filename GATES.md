# Gate status

Updated 2026-10-23 19:11:08 UTC. A strategy is **DEPLOYABLE** only when every gate passes. Everything else keeps paper trading.

# Slow lane (daily)

## trend v1 - PAPER (7/10)

- PASS **settings**: 2.0 bps per trade, dividends included, 9.75 years
- PASS **sample**: 9.75 years, 38 position changes (need 8+ yrs, 20+ changes)
- PASS **quality**: Sharpe 1.073 vs holding 50% SPY + 50% QQQ 0.933
- FAIL **growth**: CAGR 15.27% vs buy-and-hold 18.08% (allowed 2.0 pts behind)
- PASS **pain**: max drawdown 21.82% vs buy-and-hold 30.87% (need <= 75% of it)
- PASS **consistency**: Sharpe by half: 1.197 vs 1.143, 0.935 vs 0.723 (within 0.25)
- PASS **stress**: costs x2: Sharpe 1.066; plateau 4/4 nudges keep Sharpe near/above buy-and-hold
- PASS **recent**: last 3 yrs: CAGR 18.94%, Sharpe 1.289 vs 1.323
- FAIL **risk officer**: KILL (2026-10-22): Gives up 2.8 pts/yr vs 50/50 SPY+QQQ for a smaller drawdown that rests on about 5 bear-market episodes; 9 out-of-sample days match the benchmark exactly (-1.56% vs -1.56%).
- FAIL **forward**: 9 out-of-sample days since 2026-10-08 (need 60+); return -1.56% vs -1.56% buy-and-hold, worst dip 3.76%

## momentum v1 - PAPER (3/10)

- PASS **settings**: 2.0 bps per trade, dividends included, 9.75 years
- PASS **sample**: 9.75 years, 44 position changes (need 8+ yrs, 20+ changes)
- FAIL **quality**: Sharpe 0.606 vs holding SPY 0.88
- FAIL **growth**: CAGR 10.63% vs buy-and-hold 15.15% (allowed 2.0 pts behind)
- FAIL **pain**: max drawdown 34.89% vs buy-and-hold 33.79% (need <= 75% of it)
- FAIL **consistency**: Sharpe by half: 0.413 vs 0.983, 0.828 vs 0.771 (within 0.25)
- FAIL **stress**: costs x2: Sharpe 0.597; plateau 0/3 nudges keep Sharpe near/above buy-and-hold
- PASS **recent**: last 3 yrs: CAGR 28.56%, Sharpe 1.331 vs 1.408
- FAIL **risk officer**: KILL (2026-10-22): Worse than holding SPY on Sharpe (0.61 vs 0.88), growth (-4.5 pts/yr), drawdown and plateau (0/3 nudges); forward -2.99% vs -0.11% for SPY, all one QQQ bet.
- FAIL **forward**: 9 out-of-sample days since 2026-10-08 (need 60+); return -2.99% vs -0.11% buy-and-hold, worst dip 5.52%

## voltarget v1 - PAPER (7/10)

- PASS **settings**: 2.0 bps per trade, dividends included, 9.75 years
- PASS **sample**: 9.75 years, 88 position changes (need 8+ yrs, 20+ changes)
- PASS **quality**: Sharpe 0.991 vs holding SPY 0.88
- FAIL **growth**: CAGR 12.75% vs buy-and-hold 15.15% (allowed 2.0 pts behind)
- PASS **pain**: max drawdown 17.82% vs buy-and-hold 33.79% (need <= 75% of it)
- PASS **consistency**: Sharpe by half: 1.166 vs 0.983, 0.828 vs 0.771 (within 0.25)
- PASS **stress**: costs x2: Sharpe 0.987; plateau 8/8 nudges keep Sharpe near/above buy-and-hold
- PASS **recent**: last 3 yrs: CAGR 18.2%, Sharpe 1.399 vs 1.408
- FAIL **risk officer**: KILL (2026-10-22): Trails SPY (held as VOO) by 2.4 pts/yr, is 91% SPY today, and its halved drawdown comes from a handful of crashes, with only 9 forward days.
- FAIL **forward**: 9 out-of-sample days since 2026-10-08 (need 60+); return -0.08% vs -0.11% buy-and-hold, worst dip 1.78%

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
- FAIL **risk officer**: KILL (2026-10-22): Fails the no-edge stress (Sharpe 0.604 vs 0.612 for holding) and its Sharpe rises 0.60 -> 1.02 as the assumed IV/RV ratio goes 0.9 -> 1.2, so modeled premium does the work; 5.7%/yr vs 15.0% for SPY, 0 completed paper cycles.
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
- FAIL **risk officer**: KILL (2026-10-22): Its edge is the modeled IV/RV ratio: Sharpe falls to 0.55 at fair prices with doubled spreads (below holding's 0.61), and it grows 9 pts/yr slower than SPY.
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
- FAIL **risk officer**: KILL (2026-10-22): With fair option prices and doubled spreads its Sharpe is 0.15, it beats holding in only 50% of stocks, and it grows 11 pts/yr slower than SPY.
- FAIL **forward**: not paper traded (only the wheel runs live)
