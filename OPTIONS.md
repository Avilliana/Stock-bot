# Options lane results

Updated 2026-10-09 23:10:54 UTC · 2016-04-15 to 2026-10-08 · $1000 per stock, one contract

Each strategy runs on every candidate stock separately ($1,000 each), then results are averaged. Option prices are modeled (Black-Scholes); the IV/RV ratio is measured from real option data since Feb 2024 (pooled 1.07, n=304).

| | CAGR | Sharpe | worst drop |
|---|---|---|---|
| hold the same stocks | 12.46% | 0.632 | 49.14% |
| $1k in SPY instead | 15.17% | 0.898 | 33.79% |
| **wheel** v1 | 5.72% | 0.894 | 12.47% |
| ↳ if options were priced fairly + 2x spreads | 4.31% | 0.619 | 14.95% |
| **covered_call** v1 | 5.22% | 0.951 | 14.0% |
| ↳ if options were priced fairly + 2x spreads | 3.55% | 0.567 | 17.69% |
| **csp** v1 | 3.89% | 1.077 | 10.38% |
| ↳ if options were priced fairly + 2x spreads | 0.61% | 0.171 | 15.91% |

Per-stock detail is in `reports/options_<strategy>.json`. Costs: $0.65 per contract, half-spread max($0.025, 10% of premium) on every sale.
