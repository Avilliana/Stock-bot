# Tuning log

One line per change: date, strategy, setting, old -> new, version bump, reason, evidence.
Every change bumps that strategy's `version` in config.json, which re-runs the
backtest gauntlet and restarts its forward (paper) count.

- 2026-10-08 | all | initial settings, v1 for orb / vwap / gapfade | starting point, nothing tuned yet
