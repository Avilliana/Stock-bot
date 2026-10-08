# Stock day-trading bot (paper)

Same frame as Pump-bot, pointed at US stocks: it runs itself on GitHub Actions
every market day, trades an **Alpaca paper account** (fake money, real prices),
logs every trade, and gets a nightly review that may make at most one change.

The difference is the gauntlet. Nothing is "ready" because it made money for a
week. A strategy has to pass every line of the scorecard below, and every change
to it starts the count over.

## What it trades

Ten liquid names: SPY, QQQ, AAPL, MSFT, NVDA, AMZN, META, GOOGL, TSLA, AMD.
All positions are closed by 3:55 PM New York time. Nothing is held overnight.

Three strategies race each other. The plan is to kill two:

| Strategy | Idea | Who's on the other side |
|---|---|---|
| `orb` opening-range breakout | First clean break of the first 15 min high/low; stop at the range midpoint, target 2R | Early faders and stops parked just outside the opening range |
| `vwap` VWAP reversion | Fade moves stretched 2+ standard deviations from VWAP; target VWAP; 60 min max hold | Impatient market orders and stop cascades pushing price away from where volume traded |
| `gapfade` gap fade | Gap of 0.75-4% whose first 5 minutes move against it; target half the gap filled; out by 11:30 | Pre-market chasers who unwind once real liquidity shows up |

Each one's "what proves it wrong" condition lives in `config.json`.

Every trade is sized so that hitting the stop loses about $50 (1R), capped at
$10k per position. A kill switch flattens everything and stops new entries for the
day if the account is down $300.

## Slow lane (daily ETF strategies)

`daily.py` runs three strategies aimed at compounding. Each is judged against simply
holding SPY (the same index as VOO), over about 10 years of daily, dividend-adjusted prices:

| Strategy | Idea |
|---|---|
| `trend` | Hold SPY and QQQ (half each) only while each is above its 200-day average; otherwise T-bills (BIL) |
| `momentum` | Each month end, hold the strongest of SPY/QQQ/IWM/EFA/GLD/TLT over 6 months, or T-bills if none beat them |
| `voltarget` | Size SPY to about 15% yearly volatility; the rest sits in T-bills |

Each strategy's decision uses prices through yesterday's close and trades at today's close.
Its own scorecard (in `GATES.md` under "Slow lane") checks five things against buy-and-hold:
a better Sharpe, CAGR no more than 2 points behind, a max drawdown at most 75% of
buy-and-hold's, holding up in both halves of history and in the last 3 years, and survival
of costs x2 plus ±20% parameter nudges. The forward record is every day since the version's
`since` date. Those days are true out-of-sample, because the settings were fixed before they
happened. Results update every evening (`daily.yml`). Nothing is bought; the dashboard shows
what each one would hold today.

Monthly switching creates short-term gains. If one of these ever earns real money, it fits
an IRA/Roth better than a taxable account.

## The scorecard for day trading (enforced by `gate.py`)

| Gate | Keep if |
|---|---|
| settings | venue fees and slippage on, real data, report matches the current version |
| sample | 100+ closed trades in the backtest |
| quality | Sharpe > 1 and profit factor > 1.3 |
| pain | max drawdown under 15% of the $10k strategy allocation |
| benchmark | beats buy-and-hold SPY's Sharpe |
| neutral | beta to SPY within ±0.3 |
| stress | still profitable with costs ×2, and 75%+ of ±20% parameter nudges hold up (a plateau, not a spike) |
| recent | still profitable over the trailing year on its own |
| risk officer | the nightly review's adversarial check says KEEP for this version |
| forward | 30+ paper trades over 20+ days, with average R in line with the backtest |

`GATES.md` shows the live status. The dashboard shows it as a bar per strategy.
"DEPLOYABLE" only means it passed. Going live with real money is still your call,
made by hand, and nothing in this repo can do it (the code only talks to Alpaca's
paper endpoint).

## The schedule (all automatic)

| When | What | Workflow |
|---|---|---|
| Market days, 9:30-3:55 ET | trades every minute on paper | `session.yml` |
| After the close | pairs fills into trades, updates logs and gates | `eod.yml` |
| Weeknights | Claude reviews the day; writes lessons; risk-officer verdict; at most ONE change | Claude scheduled task |
| Saturdays, and on any strategy/config change | re-downloads data, re-runs backtest + stress + plateau, re-scores | `backtest.yml` |
| Weekdays after the close, and on slow-lane changes | refreshes daily prices, re-tests the slow lane, extends its forward record | `daily.yml` |

## One-time setup

1. **Alpaca paper account:** sign up free at alpaca.markets. In the dashboard, make
   sure you're on the **Paper** account, then create API keys (Key ID + Secret).
2. **This repo:** in GitHub, go to Settings → Secrets and variables → Actions and add
   `ALPACA_API_KEY_ID` and `ALPACA_API_SECRET_KEY`.
3. **Dashboard:** go to Settings → Pages, choose "Deploy from a branch", `main`, `/ (root)`.
   The page lives at `https://avilliana.github.io/Stock-bot/`. Add it to your
   phone's home screen.
4. **First backtest:** go to Actions → "Backtest and gauntlet" → Run workflow. The first
   run downloads 3 years of minute bars (~10-20 min).

The repo should be **public** like Pump-bot. A full trading day is ~6.5 hours of
Actions time, which is free only on public repos. The keys stay secret either way.

## Run it on your PC (optional)

```
pip install -r requirements.txt
python bot.py --sim                 fake day, fake broker, proves it all works
python backtest.py --synthetic      fake data through the whole gauntlet
python tests/test_no_lookahead.py   proves no strategy can see the future
```

With your paper keys set (`set ALPACA_API_KEY_ID=...` and `set ALPACA_API_SECRET_KEY=...`),
`python backtest.py` and `python bot.py` run the real thing.

## Files

- `config.json` holds the universe, costs, risk, each strategy's settings and version, and the scorecard thresholds
- `strategies.py` holds the strategy logic, shared by the backtest and the live bot
- `bot.py` is the live paper trader; `sim.py` is a fake broker for `--sim`
- `backtest.py` writes `reports/` and `BACKTEST.md`; `gate.py` writes `GATES.md` and `logs/gates.json`
- `reconcile.py` writes the end-of-day `logs/trades.csv`, `equity.csv` and `summary.json`
- `logs/bot_log.txt` records every entry, exit and rejection; `logs/signals.csv` records every signal, including skipped ones
- `TUNING_LOG.md` gets one line per change; `LESSONS.md` gets one rule per real pattern, with evidence
- `reviews/` holds the nightly reviews and `verdicts.json` (risk officer)

## Known differences between backtest and live

- Live data is Alpaca's free IEX feed, so VWAP uses IEX volume, not the whole market's.
  The backtest uses the same feed so the two match. Real fills happen at the national
  best price, though.
- The backtest lets two strategies hold the same symbol at once. Live, a symbol holds
  one position at a time, and the second signal is logged as skipped.
- Alpaca paper fills are optimistic, with no queue position and instant fills. The
  forward gate compares results in R, and the nightly review watches for drift.
