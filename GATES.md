# Gate status

Updated 2026-10-08 16:20:44 UTC. A strategy is **DEPLOYABLE** only when every gate passes. Everything else keeps paper trading.

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
