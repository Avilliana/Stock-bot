# Options lane results

Updated 2026-10-10 13:42:07 UTC · 2016-04-15 to 2026-10-09 · $1000 per stock, one contract

Each strategy runs on every candidate stock separately ($1,000 each), then results are averaged. Option prices are modeled (Black-Scholes); the IV/RV ratio is measured from real option data since Feb 2024 (pooled 1.07, n=304).

| | CAGR | Sharpe | worst drop |
|---|---|---|---|
| hold the same stocks | 12.58% | 0.637 | 49.14% |
| $1k in SPY instead | 15.23% | 0.901 | 33.79% |
| **wheel** v1 | 5.75% | 0.899 | 12.47% |
| ↳ if options were priced fairly + 2x spreads | 4.35% | 0.624 | 14.95% |
| **covered_call** v1 | 5.25% | 0.956 | 14.0% |
| ↳ if options were priced fairly + 2x spreads | 3.6% | 0.573 | 17.69% |
| **csp** v1 | 3.9% | 1.08 | 10.38% |
| ↳ if options were priced fairly + 2x spreads | 0.63% | 0.174 | 15.91% |

Per-stock detail is in `reports/options_<strategy>.json`. Costs: $0.65 per contract, half-spread max($0.025, 10% of premium) on every sale.
