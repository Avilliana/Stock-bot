# Tuning log

One line per change: date, strategy, setting, old -> new, version bump, reason, evidence.
Every change bumps that strategy's `version` in config.json, which re-runs the
backtest gauntlet and restarts its forward (paper) count.

- 2026-10-08 | all | initial settings, v1 for orb / vwap / gapfade | starting point, nothing tuned yet
- 2026-10-08 | day/vwap | enabled true -> false | v1 (unchanged) | failed its backtest gates with no parameter fix: every one of 12 ±20% nudges stays at PF 0.66-0.73 | backtest 13,935 trades PF 0.706, avg -0.36R, 68% stopped out, trailing year PF 0.748; first paper day 0/17 wins, avg -1.18R, $-192.97
- 2026-10-09 | day/gapfade | enabled true -> false | v1 (unchanged) | failed its backtest gates with no parameter fix: 0/10 ±20% nudges hold up | backtest 987 trades PF 0.726, avg -0.13R, shorts PF 0.66, costs x2 PF 0.60, trailing year PF 0.69; one winning paper trade (+0.86R) is no counter-evidence
- 2026-10-19 | day/orb | or_minutes 15 -> 30 | v1 -> v2 | fails its backtest gates (PF 0.887) and the paper record points at the same parameter: early breakouts lose; one change, judged by the push-triggered gauntlet. If v2 still has backtest PF < 1, disable orb instead of tuning again | paper v1 44 trades over 7 days: entries before 10:00 25 trades -0.43R (negative 5 of 7 days), from 10:00 on 19 trades +0.59R; backtest or_minutes nudges rise monotonically 12 -> 15 -> 18 (PF 0.856 / 0.887 / 0.921)
- 2026-10-20 | day/orb | enabled true -> false | v2 (unchanged) | committed on 10-19: if v2's backtest PF stayed below 1, disable instead of tuning again | v2 push-triggered backtest (run 39341200218, log only; its commit lost to a push conflict) 4,173 trades PF 0.866, worse than v1's 0.887 over 5,125; 3 v2 paper trades (+0.35R) are no counter-evidence. All three day-trading strategies are now off
- 2026-10-23 | all lanes | all workflow schedules and push triggers -> removed (manual runs only) | versions unchanged | Andrew decided to stop the project: all 9 strategies KILL, none beats holding VOO/QQQ | see reviews/2026-10-22.md and verdicts.json; open paper SNAP 11-13 $6 put left to expire or be assigned on the paper account
