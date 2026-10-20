# Options lane results

Updated 2026-10-20 23:13:45 UTC · 2016-04-15 to 2026-10-19 · $1000 per stock, one contract

Each strategy runs on every candidate stock separately ($1,000 each), then results are averaged. Option prices are modeled (Black-Scholes); the IV/RV ratio is measured from real option data since Feb 2024 (pooled 1.069, n=313).

| | CAGR | Sharpe | worst drop |
|---|---|---|---|
| hold the same stocks | 11.98% | 0.612 | 49.14% |
| $1k in SPY instead | 15.02% | 0.891 | 33.79% |
| **wheel** v1 | 5.66% | 0.887 | 12.4% |
| ↳ if options were priced fairly + 2x spreads | 4.2% | 0.604 | 14.95% |
| **covered_call** v1 | 5.73% | 1.023 | 13.65% |
| ↳ if options were priced fairly + 2x spreads | 3.45% | 0.552 | 17.69% |
| **csp** v1 | 3.88% | 1.075 | 10.26% |
| ↳ if options were priced fairly + 2x spreads | 0.51% | 0.147 | 15.91% |

Per-stock detail is in `reports/options_<strategy>.json`. Costs: $0.65 per contract, half-spread max($0.025, 10% of premium) on every sale.
