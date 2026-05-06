# Beast Scanner Usage

This is the short command reference for the Yahoo/NSE beast scanner in this repo.

## Live scan

```sh
python -m ta.beast_scanner \
  --timeframe weekly \
  --period 10y \
  --technical-gate 'bb_width_pct<=28.18' \
  --technical-gate 'breakout_volume_ratio<=1.44' \
  --technical-gate 'long_low_gain_pct>=123.2' \
  --technical-gate 'post_peak_drawdown_pct<=12.84' \
  --max-workers 12
```

Use this for the best balanced validated scan. It is the strongest all-round
weekly setup found in replay.

## Monthly high-win scan

```sh
python -m ta.beast_scanner \
  --timeframe monthly \
  --period 10y \
  --lookahead-bars 5 \
  --cooldown-bars 3 \
  --technical-gate 'stage==follow_through' \
  --technical-gate 'adx_neg14>=13.67' \
  --technical-gate 'atr_pct<=15.08' \
  --technical-gate 'bb_width_pct>=31.42' \
  --technical-gate 'mfi14>=63.95' \
  --technical-gate 'recent_range_pct<=24.04' \
  --technical-gate 'roc60<=99.74' \
  --max-workers 12
```

Use this if you want the highest validated monthly win ratio. It is very
selective.

## Monthly full-scan replay

```sh
python -m ta.beast_scanner \
  --replay \
  --timeframe monthly \
  --period 10y \
  --lookahead-bars 5 \
  --cooldown-bars 3 \
  --max-workers 12 \
  --output-json /tmp/beast-monthly-replay-calendar-v4.json
```

## Daily replay check

```sh
python -m ta.beast_scanner \
  --replay \
  --timeframe daily \
  --period 10y \
  --lookahead-bars 100 \
  --cooldown-bars 50 \
  --max-workers 12 \
  --output-json /tmp/beast-daily-replay-calendar-v4.json
```

## Notes

- `--technical-gate` can be repeated.
- `--timeframe` accepts `daily`, `weekly`, or `monthly`.
- The scanner prints only current matches. It does not place orders.
- Weekly is the strongest balanced result. Monthly has the highest select win
  ratio, but it is much narrower.
