# Gate status

Updated 2026-10-08 18:53:14 UTC. A strategy is **DEPLOYABLE** only when every gate passes. Everything else keeps paper trading.

## orb v1 - PAPER (3/10)

- PASS **settings**: slippage 1.5/3.0 bps, fees on, 750 days
- PASS **sample**: 5138 closed trades (need 100+)
- FAIL **quality**: Sharpe -1.706 (>1.0), PF 0.883 (>1.3)
- FAIL **pain**: max drawdown 150.76% of allocation (limit 15.0%)
- FAIL **benchmark**: Sharpe -1.706 vs buy-and-hold 1.394
- PASS **neutral**: beta -0.209 (|beta| <= 0.3)
- FAIL **stress**: costs x2: PF 0.75, P&L $-36842.45; plateau 0/10 nudges hold up
- FAIL **recent**: trailing year: 1690 trades, PF 0.827, P&L $-7873.64
- FAIL **risk officer**: no review yet (-):
- FAIL **forward**: 0 paper trades over 0 days (need 30+ over 20+)

## vwap v1 - PAPER (3/10)

- PASS **settings**: slippage 1.5/3.0 bps, fees on, 750 days
- PASS **sample**: 13935 closed trades (need 100+)
- FAIL **quality**: Sharpe -7.859 (>1.0), PF 0.706 (>1.3)
- FAIL **pain**: max drawdown 665.9% of allocation (limit 15.0%)
- FAIL **benchmark**: Sharpe -7.859 vs buy-and-hold 1.394
- PASS **neutral**: beta 0.086 (|beta| <= 0.3)
- FAIL **stress**: costs x2: PF 0.517, P&L $-134973.18; plateau 0/12 nudges hold up
- FAIL **recent**: trailing year: 4706 trades, PF 0.748, P&L $-18768.62
- FAIL **risk officer**: no review yet (-):
- FAIL **forward**: 0 paper trades over 0 days (need 30+ over 20+)

## gapfade v1 - PAPER (3/10)

- PASS **settings**: slippage 1.5/3.0 bps, fees on, 750 days
- PASS **sample**: 987 closed trades (need 100+)
- FAIL **quality**: Sharpe -1.939 (>1.0), PF 0.726 (>1.3)
- FAIL **pain**: max drawdown 54.87% of allocation (limit 15.0%)
- FAIL **benchmark**: Sharpe -1.939 vs buy-and-hold 1.394
- PASS **neutral**: beta -0.019 (|beta| <= 0.3)
- FAIL **stress**: costs x2: PF 0.603, P&L $-8419.26; plateau 0/10 nudges hold up
- FAIL **recent**: trailing year: 343 trades, PF 0.691, P&L $-2057.27
- FAIL **risk officer**: no review yet (-):
- FAIL **forward**: 0 paper trades over 0 days (need 30+ over 20+)

# Slow lane (daily)

## trend v1 - PAPER (7/10)

- PASS **settings**: 2.0 bps per trade, dividends included, 9.71 years
- PASS **sample**: 9.71 years, 38 position changes (need 8+ yrs, 20+ changes)
- PASS **quality**: Sharpe 1.095 vs holding 50% SPY + 50% QQQ 0.948
- FAIL **growth**: CAGR 15.63% vs buy-and-hold 18.46% (allowed 2.0 pts behind)
- PASS **pain**: max drawdown 21.82% vs buy-and-hold 30.87% (need <= 75% of it)
- PASS **consistency**: Sharpe by half: 1.217 vs 1.157, 0.96 vs 0.74 (within 0.25)
- PASS **stress**: costs x2: Sharpe 1.088; plateau 4/4 nudges keep Sharpe near/above buy-and-hold
- PASS **recent**: last 3 yrs: CAGR 20.77%, Sharpe 1.397 vs 1.41
- FAIL **risk officer**: no review yet (-):
- FAIL **forward**: 0 out-of-sample days since 2026-10-08 (need 60+)

## momentum v1 - PAPER (3/10)

- PASS **settings**: 2.0 bps per trade, dividends included, 9.71 years
- PASS **sample**: 9.71 years, 44 position changes (need 8+ yrs, 20+ changes)
- FAIL **quality**: Sharpe 0.63 vs holding SPY 0.886
- FAIL **growth**: CAGR 11.18% vs buy-and-hold 15.28% (allowed 2.0 pts behind)
- FAIL **pain**: max drawdown 34.89% vs buy-and-hold 33.79% (need <= 75% of it)
- FAIL **consistency**: Sharpe by half: 0.425 vs 0.997, 0.868 vs 0.768 (within 0.25)
- FAIL **stress**: costs x2: Sharpe 0.621; plateau 0/3 nudges keep Sharpe near/above buy-and-hold
- PASS **recent**: last 3 yrs: CAGR 31.43%, Sharpe 1.441 vs 1.462
- FAIL **risk officer**: no review yet (-):
- FAIL **forward**: 0 out-of-sample days since 2026-10-08 (need 60+)

## voltarget v1 - PAPER (7/10)

- PASS **settings**: 2.0 bps per trade, dividends included, 9.71 years
- PASS **sample**: 9.71 years, 88 position changes (need 8+ yrs, 20+ changes)
- PASS **quality**: Sharpe 0.997 vs holding SPY 0.886
- FAIL **growth**: CAGR 12.86% vs buy-and-hold 15.28% (allowed 2.0 pts behind)
- PASS **pain**: max drawdown 17.82% vs buy-and-hold 33.79% (need <= 75% of it)
- PASS **consistency**: Sharpe by half: 1.188 vs 0.997, 0.822 vs 0.768 (within 0.25)
- PASS **stress**: costs x2: Sharpe 0.993; plateau 8/8 nudges keep Sharpe near/above buy-and-hold
- PASS **recent**: last 3 yrs: CAGR 19.19%, Sharpe 1.461 vs 1.462
- FAIL **risk officer**: no review yet (-):
- FAIL **forward**: 0 out-of-sample days since 2026-10-08 (need 60+)

# Options lane

## wheel v1 - PAPER (5/10)

- PASS **settings**: costs on, IV/RV calibrated, 10.46 years
- PASS **sample**: 358 option cycles across stocks (need 100+)
- PASS **quality**: Sharpe 0.896 vs holding the same stocks 0.634
- FAIL **growth**: CAGR 5.73% vs $1k in SPY 15.22% (allowed 2.0 pts behind)
- PASS **pain**: worst drop 12.47% vs holding the stocks 49.14%
- FAIL **no-edge stress**: with options priced fairly and spreads x2: Sharpe 0.621 vs holding 0.634
- FAIL **breadth**: beats holding in 56% of stocks (need 60%+)
- PASS **recent**: last 3 yrs: CAGR 5.25%, Sharpe 0.909 vs holding 0.858
- FAIL **risk officer**: no review yet (-):
- FAIL **forward**: 0 completed paper option cycles (need 3+)

## covered_call v1 - PAPER (5/10)

- PASS **settings**: costs on, IV/RV calibrated, 10.46 years
- PASS **sample**: 601 option cycles across stocks (need 100+)
- PASS **quality**: Sharpe 0.954 vs holding the same stocks 0.634
- FAIL **growth**: CAGR 5.24% vs $1k in SPY 15.22% (allowed 2.0 pts behind)
- PASS **pain**: worst drop 14.0% vs holding the stocks 49.14%
- FAIL **no-edge stress**: with options priced fairly and spreads x2: Sharpe 0.571 vs holding 0.634
- FAIL **breadth**: beats holding in 56% of stocks (need 60%+)
- PASS **recent**: last 3 yrs: CAGR 7.44%, Sharpe 1.641 vs holding 0.858
- FAIL **risk officer**: no review yet (-):
- FAIL **forward**: not paper traded (only the wheel runs live)

## csp v1 - PAPER (5/10)

- PASS **settings**: costs on, IV/RV calibrated, 10.46 years
- PASS **sample**: 613 option cycles across stocks (need 100+)
- PASS **quality**: Sharpe 1.079 vs holding the same stocks 0.634
- FAIL **growth**: CAGR 3.9% vs $1k in SPY 15.22% (allowed 2.0 pts behind)
- PASS **pain**: worst drop 10.38% vs holding the stocks 49.14%
- FAIL **no-edge stress**: with options priced fairly and spreads x2: Sharpe 0.174 vs holding 0.634
- FAIL **breadth**: beats holding in 50% of stocks (need 60%+)
- PASS **recent**: last 3 yrs: CAGR 5.59%, Sharpe 2.025 vs holding 0.858
- FAIL **risk officer**: no review yet (-):
- FAIL **forward**: not paper traded (only the wheel runs live)
