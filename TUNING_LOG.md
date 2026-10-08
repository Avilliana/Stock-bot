# Tuning log

One line per change: date, strategy, setting, old -> new, version bump, reason, evidence.
Every change bumps that strategy's `version` in config.json, which re-runs the
backtest gauntlet and restarts its forward (paper) count.

- 2026-10-08 | all | initial settings, v1 for orb / vwap / gapfade | starting point, nothing tuned yet
- 2026-10-08 | day/vwap | enabled true -> false | v1 (unchanged) | failed its backtest gates with no parameter fix: every one of 12 ±20% nudges stays at PF 0.66-0.73 | backtest 13,935 trades PF 0.706, avg -0.36R, 68% stopped out, trailing year PF 0.748; first paper day 0/17 wins, avg -1.18R, $-192.97
