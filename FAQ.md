# FAQ

## Which timeframe should I use?

- Use `weekly` if you want the best balanced validated scanner.
- Use `monthly` if you want the highest monthly win ratio, but it is more
  selective.
- Avoid treating `daily` as validated at the same level as weekly or monthly.

## What is actually validated?

- Weekly replay validated with a strong holdout result.
- Monthly replay validated in two forms: a broader gate and a very selective
  follow-through gate.
- Daily did not validate to the same level on the strict replay standard.

## Does the scanner place orders?

- No. It prints matches only.
- You still decide how to enter, size, and manage risk.

## What does a match mean?

- It means the symbol passed the current technical gate for the selected
  timeframe.
- It does not guarantee profit.
- It is a filter, not a trade engine.

## How do I run the best live scans?

Weekly:
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

Monthly, broader:
```sh
python -m ta.beast_scanner \
  --timeframe monthly \
  --period 10y \
  --lookahead-bars 5 \
  --cooldown-bars 3 \
  --technical-gate 'adx_neg14>=13.67' \
  --technical-gate 'atr_pct<=15.08' \
  --technical-gate 'bb_width_pct>=31.42' \
  --technical-gate 'mfi14>=63.95' \
  --technical-gate 'recent_range_pct<=24.04' \
  --technical-gate 'roc60<=99.74' \
  --max-workers 12
```

Monthly, highest win ratio:
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

## Where do I read the details?

- [README.md](/workspaces/ta/README.md) for the full benchmarked guide.
- [USAGE.md](/workspaces/ta/USAGE.md) for the short command reference.
- [TRADING.md](/workspaces/ta/TRADING.md) for the buy-check checklist.
- [ARCHITECTURE.md](/workspaces/ta/ARCHITECTURE.md) for how the scanner fits
  together.
