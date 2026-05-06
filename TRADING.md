# Trading Checklist

This scanner only finds technical setups. It does not place orders or manage
risk. Use this checklist before acting on a live match.

## Before buying

1. Confirm the symbol appears in the live scanner output for the intended
   timeframe.
2. Prefer the validated gate for that timeframe.
3. Check that the stage is `follow_through` or `breakout_today`.
4. Avoid names in `base`, `damaged_base`, or `insufficient_data`.
5. Keep the entry small enough that a failed signal does not matter.

## Validated gates

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

## Reading the output

- `score` and `rating` are the scanner's technical quality flags.
- `stage` tells you whether the setup is `follow_through`, `breakout_today`,
  `early_entry`, or something weaker.
- `pivot`, `dist%`, `upside%`, `rsi`, `adx`, and `volx` are the most useful
  fields for a quick pass/fail judgment.

## Risk

- The scanner is not a profit guarantee.
- Weekly and monthly were validated from replay; daily was not.
- Use position sizing and stops outside the scanner.
