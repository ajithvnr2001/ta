# Architecture

This repo now has two layers:

1. The core `ta` library for technical indicators.
2. The `ta.beast_scanner` layer for live scanning, replay, validation, and gate
   search.

## Scanner Flow

- `YahooDataProvider` loads price history through `yfinance`.
- `dataframe_to_ohlcv` and `resample_ohlcv` normalize daily, weekly, and
  monthly bars.
- `analyze_beast_setup` computes the technical signal for one symbol at one
  bar.
- `run_scan` walks the live universe and returns current matches.
- `run_replay` replays historical signals and scores them with forward
  validation.
- `optimize_replay_quality_gate` searches pure technical filters against a
  replay snapshot and checks a chronological holdout split.

## Timeframes

- `daily` uses the daily Yahoo bars directly.
- `weekly` resamples daily bars to Friday-closed weeks.
- `monthly` resamples daily bars to month-end bars and uses shorter replay
  windows where needed.

## Validation Rules

- Default replay success requires `+5%` forward high, `<=8%` drawdown, and a
  positive final close.
- Weekly is the strongest balanced result.
- Monthly has the highest selective win ratio.
- Daily did not validate to the same level as weekly or monthly.

## Docs

- [README.md](/workspaces/ta/README.md) is the full benchmarked guide.
- [USAGE.md](/workspaces/ta/USAGE.md) is the short command reference.
- [TRADING.md](/workspaces/ta/TRADING.md) is the buy-check checklist.
- [RELEASE.md](/workspaces/ta/RELEASE.md) records the scanner release note.
