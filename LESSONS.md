# Lessons

One rule per real pattern, with the date and the evidence. Written by the nightly
review. A pattern needs evidence across several days before it earns a line here.

- 2026-10-12 | day | The $10k notional cap, not the $50 risk budget, sizes SPY/QQQ trades: real risk was $5-26 per trade on 3 of 3 days (vwap 10-08 $5-25; orb SPY $11 / QQQ $26 on 10-09; orb QQQ $22 on 10-12). Read SPY/QQQ results in R, and expect their dollar P&L to count about half as much as the stocks'.
- 2026-10-12 | day/ops | The 15:55 flatten fails with HTTP 403 "insufficient qty" when bracket legs still hold the shares, and the 2-second retry isn't enough: MSFT 10-09 and QQQ 10-12 both closed only at 15:56. Code fix needed (wait until the leg cancels are confirmed). 2026-10-13: third day running (NVDA, 36 shares, closed 15:56).
- 2026-10-12 | options/live | Wheel put orders priced at the mid of a 3¢-wide market went unfilled 2 of 2 times (AGNC 10-08 $0.14, 10-09 $0.16). They expired as day orders and weren't logged as repriced, so they disappear from wheel_log.csv.
- 2026-10-15 | day/orb | Early breakouts in several names in the same few minutes are one correlated market bet, not separate trades, and they stopped out together 3 days running: 10-13 (4 longs 09:46-09:55), 10-14 (SPY/QQQ/GOOGL longs 09:48, all stopped by 09:53), 10-15 (SPY/QQQ/TSLA/NVDA shorts 09:54-55, all stopped). orb v1 entries before 10:00: 19 trades, -0.42R, negative 4 of 5 days; from 10:00 on: 12 trades, +0.65R. Small sample; the backtest's or_minutes 18 nudge still loses (PF 0.92).
