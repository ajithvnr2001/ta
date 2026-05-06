![CircleCI](https://img.shields.io/circleci/build/github/bukosabino/ta/master)
[![Documentation Status](https://readthedocs.org/projects/technical-analysis-library-in-python/badge/?version=latest)](https://technical-analysis-library-in-python.readthedocs.io/en/latest/?badge=latest)
[![Coverage Status](https://coveralls.io/repos/github/bukosabino/ta/badge.svg)](https://coveralls.io/github/bukosabino/ta)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Linter: Prospector](https://img.shields.io/badge/Linter-Prospector-coral.svg)](http://prospector.landscape.io/en/master/)
![PyPI](https://img.shields.io/pypi/v/ta)
![PyPI - Downloads](https://img.shields.io/pypi/dm/ta)
[![Donate PayPal](https://img.shields.io/badge/Donate%20%24-PayPal-brightgreen.svg)](https://www.paypal.me/guau/3)

# Technical Analysis Library in Python

It is a Technical Analysis library useful to do feature engineering from financial time series datasets (Open, Close, High, Low, Volume). It is built on Pandas and Numpy.

![Bollinger Bands graph example](static/figure.png)

The library has implemented 43 indicators:

## Volume


ID | Name | Class | defs
-- |-- |-- |-- |
1 | Money Flow Index (MFI) | [MFIIndicator](https://technical-analysis-library-in-python.readthedocs.io/en/latest/ta.html#ta.volume.MFIIndicator) | [money_flow_index](https://technical-analysis-library-in-python.readthedocs.io/en/latest/ta.html#ta.volume.money_flow_index)
2 | Accumulation/Distribution Index (ADI) | [AccDistIndexIndicator](https://technical-analysis-library-in-python.readthedocs.io/en/latest/ta.html#ta.volume.AccDistIndexIndicator) | [acc_dist_index](https://technical-analysis-library-in-python.readthedocs.io/en/latest/ta.html#ta.volume.acc_dist_index)
3 | On-Balance Volume (OBV) | [OnBalanceVolumeIndicator](https://technical-analysis-library-in-python.readthedocs.io/en/latest/ta.html#ta.volume.OnBalanceVolumeIndicator) | [on_balance_volume](https://technical-analysis-library-in-python.readthedocs.io/en/latest/ta.html#ta.volume.on_balance_volume)
4 | Chaikin Money Flow (CMF) | [ChaikinMoneyFlowIndicator](https://technical-analysis-library-in-python.readthedocs.io/en/latest/ta.html#ta.volume.ChaikinMoneyFlowIndicator) | [chaikin_money_flow](https://technical-analysis-library-in-python.readthedocs.io/en/latest/ta.html#ta.volume.chaikin_money_flow)
5 | Force Index (FI) | [ForceIndexIndicator](https://technical-analysis-library-in-python.readthedocs.io/en/latest/ta.html#ta.volume.ForceIndexIndicator) | [force_index](https://technical-analysis-library-in-python.readthedocs.io/en/latest/ta.html#ta.volume.force_index)
6 | Ease of Movement (EoM, EMV) | [EaseOfMovementIndicator](https://technical-analysis-library-in-python.readthedocs.io/en/latest/ta.html#ta.volume.EaseOfMovementIndicator) | [ease_of_movement](https://technical-analysis-library-in-python.readthedocs.io/en/latest/ta.html#ta.volume.ease_of_movement)<br>[sma_ease_of_movement](https://technical-analysis-library-in-python.readthedocs.io/en/latest/ta.html#ta.volume.sma_ease_of_movement)
7 | Volume-price Trend (VPT) | [VolumePriceTrendIndicator](https://technical-analysis-library-in-python.readthedocs.io/en/latest/ta.html#ta.volume.VolumePriceTrendIndicator)| [volume_price_trend](https://technical-analysis-library-in-python.readthedocs.io/en/latest/ta.html#ta.volume.volume_price_trend)
8 | Negative Volume Index (NVI) | [NegativeVolumeIndexIndicator](https://technical-analysis-library-in-python.readthedocs.io/en/latest/ta.html#ta.volume.NegativeVolumeIndexIndicator)| [negative_volume_index](https://technical-analysis-library-in-python.readthedocs.io/en/latest/ta.html#ta.volume.negative_volume_index)
9 | Volume Weighted Average Price (VWAP) | [VolumeWeightedAveragePrice](https://technical-analysis-library-in-python.readthedocs.io/en/latest/ta.html#ta.volume.VolumeWeightedAveragePrice) | [volume_weighted_average_price](https://technical-analysis-library-in-python.readthedocs.io/en/latest/ta.html#ta.volume.volume_weighted_average_price)



<br>

## Volatility

ID | Name | Class | defs
-- |-- |-- |-- |
10 | Average True Range (ATR) | [AverageTrueRange](https://technical-analysis-library-in-python.readthedocs.io/en/latest/ta.html#ta.volatility.AverageTrueRange) | [average_true_range](https://technical-analysis-library-in-python.readthedocs.io/en/latest/ta.html#ta.volatility.average_true_range)
11 | Bollinger Bands (BB) | [BollingerBands](https://technical-analysis-library-in-python.readthedocs.io/en/latest/ta.html#ta.volatility.BollingerBands) | [bollinger_hband](https://technical-analysis-library-in-python.readthedocs.io/en/latest/ta.html#ta.volatility.bollinger_hband)<br>[bollinger_hband_indicator](https://technical-analysis-library-in-python.readthedocs.io/en/latest/ta.html#ta.volatility.bollinger_hband_indicator)<br>[bollinger_lband](https://technical-analysis-library-in-python.readthedocs.io/en/latest/ta.html#ta.volatility.bollinger_lband)<br>[bollinger_lband_indicator](https://technical-analysis-library-in-python.readthedocs.io/en/latest/ta.html#ta.volatility.bollinger_lband_indicator)<br>[bollinger_mavg](https://technical-analysis-library-in-python.readthedocs.io/en/latest/ta.html#ta.volatility.bollinger_mavg)<br>[bollinger_pband](https://technical-analysis-library-in-python.readthedocs.io/en/latest/ta.html#ta.volatility.bollinger_pband)<br>[bollinger_wband](https://technical-analysis-library-in-python.readthedocs.io/en/latest/ta.html#ta.volatility.bollinger_wband)
12 | Keltner Channel (KC) | [KeltnerChannel](https://technical-analysis-library-in-python.readthedocs.io/en/latest/ta.html#ta.volatility.KeltnerChannel) |  [keltner_channel_hband](https://technical-analysis-library-in-python.readthedocs.io/en/latest/ta.html#ta.volatility.keltner_channel_hband)<br>[keltner_channel_hband_indicator](https://technical-analysis-library-in-python.readthedocs.io/en/latest/ta.html#ta.volatility.keltner_channel_hband_indicator)<br>[keltner_channel_lband](https://technical-analysis-library-in-python.readthedocs.io/en/latest/ta.html#ta.volatility.keltner_channel_lband)<br>[keltner_channel_lband_indicator](https://technical-analysis-library-in-python.readthedocs.io/en/latest/ta.html#ta.volatility.keltner_channel_lband_indicator)<br>[keltner_channel_mband](https://technical-analysis-library-in-python.readthedocs.io/en/latest/ta.html#ta.volatility.keltner_channel_mband)<br>[keltner_channel_pband](https://technical-analysis-library-in-python.readthedocs.io/en/latest/ta.html#ta.volatility.keltner_channel_pband)<br>[keltner_channel_wband](https://technical-analysis-library-in-python.readthedocs.io/en/latest/ta.html#ta.volatility.keltner_channel_wband)
13 | Donchian Channel (DC) | [DonchianChannel](https://technical-analysis-library-in-python.readthedocs.io/en/latest/ta.html#ta.volatility.DonchianChannel)| [donchian_channel_hband](https://technical-analysis-library-in-python.readthedocs.io/en/latest/ta.html#ta.volatility.donchian_channel_hband)<br>[donchian_channel_lband](https://technical-analysis-library-in-python.readthedocs.io/en/latest/ta.html#ta.volatility.donchian_channel_lband)<br>[donchian_channel_mban](https://technical-analysis-library-in-python.readthedocs.io/en/latest/ta.html#ta.volatility.donchian_channel_mband)<br>[donchian_channel_pband](https://technical-analysis-library-in-python.readthedocs.io/en/latest/ta.html#ta.volatility.donchian_channel_pband)<br>[donchian_channel_wband](https://technical-analysis-library-in-python.readthedocs.io/en/latest/ta.html#ta.volatility.donchian_channel_wband)
14 | Ulcer Index (UI) | [UlcerIndex](https://technical-analysis-library-in-python.readthedocs.io/en/latest/ta.html#ta.volatility.UlcerIndex)|  [ulcer_index](https://technical-analysis-library-in-python.readthedocs.io/en/latest/ta.html#ta.volatility.ulcer_index)

<br>

## Trend

ID | Name | Class | defs
-- |-- |-- |-- |
15 | Simple Moving Average (SMA) | [SMAIndicator](https://technical-analysis-library-in-python.readthedocs.io/en/latest/ta.html#ta.trend.SMAIndicator) | [sma_indicator](https://technical-analysis-library-in-python.readthedocs.io/en/latest/ta.html#ta.trend.sma_indicator)
16 | Exponential Moving Average (EMA) | [EMAIndicator](https://technical-analysis-library-in-python.readthedocs.io/en/latest/ta.html#ta.trend.EMAIndicator)  | [ema_indicator](https://technical-analysis-library-in-python.readthedocs.io/en/latest/ta.html#ta.trend.ema_indicator) | Trend
17 | Weighted Moving Average (WMA) | [WMAIndicator](https://technical-analysis-library-in-python.readthedocs.io/en/latest/ta.html#ta.trend.WMAIndicator) | [wma_indicator](https://technical-analysis-library-in-python.readthedocs.io/en/latest/ta.html#ta.trend.wma_indicator)
18 | Moving Average Convergence Divergence (MACD) | [MACD](https://technical-analysis-library-in-python.readthedocs.io/en/latest/ta.html#ta.trend.MACD) | [macd](https://technical-analysis-library-in-python.readthedocs.io/en/latest/ta.html#ta.trend.macd) <br>[macd_diff](https://technical-analysis-library-in-python.readthedocs.io/en/latest/ta.html#ta.trend.macd_diff)<br>[macd_signal](https://technical-analysis-library-in-python.readthedocs.io/en/latest/ta.html#ta.trend.macd_signal)
19 | Average Directional Movement Index (ADX) | [ADXIndicator](https://technical-analysis-library-in-python.readthedocs.io/en/latest/ta.html#ta.trend.ADXIndicator) | [adx](https://technical-analysis-library-in-python.readthedocs.io/en/latest/ta.html#ta.trend.adx)<br>[adx_neg](https://technical-analysis-library-in-python.readthedocs.io/en/latest/ta.html#ta.trend.adx_neg)<br>[adx_pos](https://technical-analysis-library-in-python.readthedocs.io/en/latest/ta.html#ta.trend.adx_pos)
20 | Vortex Indicator (VI) | [VortexIndicator](https://technical-analysis-library-in-python.readthedocs.io/en/latest/ta.html#ta.trend.VortexIndicator) | [vortex_indicator_neg](https://technical-analysis-library-in-python.readthedocs.io/en/latest/ta.html#ta.trend.vortex_indicator_neg) <br>[vortex_indicator_pos](https://technical-analysis-library-in-python.readthedocs.io/en/latest/ta.html#ta.trend.vortex_indicator_pos)
21 | Trix (TRIX) | [TRIXIndicator](https://technical-analysis-library-in-python.readthedocs.io/en/latest/ta.html#ta.trend.TRIXIndicator) | [trix](https://technical-analysis-library-in-python.readthedocs.io/en/latest/ta.html#ta.trend.trix)
22 | Mass Index (MI) | [MassIndex](https://technical-analysis-library-in-python.readthedocs.io/en/latest/ta.html#ta.trend.MassIndex) | [mass_index](https://technical-analysis-library-in-python.readthedocs.io/en/latest/ta.html#ta.trend.mass_index)
23 | Commodity Channel Index (CCI) | [CCIIndicator](https://technical-analysis-library-in-python.readthedocs.io/en/latest/ta.html#ta.trend.CCIIndicator)| [cci](https://technical-analysis-library-in-python.readthedocs.io/en/latest/ta.html#ta.trend.cci)
24 | Detrended Price Oscillator (DPO) | [DPOIndicator](https://technical-analysis-library-in-python.readthedocs.io/en/latest/ta.html#ta.trend.DPOIndicator) | [dpo](https://technical-analysis-library-in-python.readthedocs.io/en/latest/ta.html#ta.trend.dpo)
25 | KST Oscillator (KST) | [KSTIndicator](https://technical-analysis-library-in-python.readthedocs.io/en/latest/ta.html#ta.trend.KSTIndicator)  | [kst](https://technical-analysis-library-in-python.readthedocs.io/en/latest/ta.html#ta.trend.kst)<br>[kst_sig](https://technical-analysis-library-in-python.readthedocs.io/en/latest/ta.html#ta.trend.kst_sig)
26 | Ichimoku Kinkō Hyō (Ichimoku) | [IchimokuIndicator](https://technical-analysis-library-in-python.readthedocs.io/en/latest/ta.html#ta.trend.IchimokuIndicator) | [ichimoku_a](https://technical-analysis-library-in-python.readthedocs.io/en/latest/ta.html#ta.trend.ichimoku_a)<br>[ichimoku_b](https://technical-analysis-library-in-python.readthedocs.io/en/latest/ta.html#ta.trend.ichimoku_b)<br>[ichimoku_base_line](https://technical-analysis-library-in-python.readthedocs.io/en/latest/ta.html#ta.trend.ichimoku_base_line)<br>[ichimoku_conversion_line](https://technical-analysis-library-in-python.readthedocs.io/en/latest/ta.html#ta.trend.ichimoku_conversion_line)
27 | Parabolic Stop And Reverse (Parabolic SAR) | [PSARIndicator](https://technical-analysis-library-in-python.readthedocs.io/en/latest/ta.html#ta.trend.PSARIndicator) | [psar_down](https://technical-analysis-library-in-python.readthedocs.io/en/latest/ta.html#ta.trend.psar_down) <br>[psar_down_indicator](https://technical-analysis-library-in-python.readthedocs.io/en/latest/ta.html#ta.trend.psar_down_indicator)<br>[psar_up](https://technical-analysis-library-in-python.readthedocs.io/en/latest/ta.html#ta.trend.psar_up)<br>[psar_up_indicator](https://technical-analysis-library-in-python.readthedocs.io/en/latest/ta.html#ta.trend.psar_up_indicator)
28 | Schaff Trend Cycle (STC) | [STCIndicator](https://technical-analysis-library-in-python.readthedocs.io/en/latest/ta.html#ta.trend.STCIndicator) | [stc](https://technical-analysis-library-in-python.readthedocs.io/en/latest/ta.html#ta.trend.stc)
29 | Aroon Indicator | [AroonIndicator](https://technical-analysis-library-in-python.readthedocs.io/en/latest/ta.html#ta.trend.AroonIndicator) | [aroon_down](https://technical-analysis-library-in-python.readthedocs.io/en/latest/ta.html#ta.trend.aroon_down)<br>[aroon_up](https://technical-analysis-library-in-python.readthedocs.io/en/latest/ta.html#ta.trend.aroon_up)




<br>

## Momentum

ID | Name | Class | defs
-- |-- |-- |-- |
30 | Relative Strength Index (RSI) | [RSIIndicator](https://technical-analysis-library-in-python.readthedocs.io/en/latest/ta.html#ta.momentum.RSIIndicator) | [rsi](https://technical-analysis-library-in-python.readthedocs.io/en/latest/ta.html#ta.momentum.rsi)
31 | Stochastic RSI (SRSI) | [StochRSIIndicator](https://technical-analysis-library-in-python.readthedocs.io/en/latest/ta.html#ta.momentum.StochRSIIndicator) | [stochrsi](https://technical-analysis-library-in-python.readthedocs.io/en/latest/ta.html#ta.momentum.stochrsi)<br>[stochrsi_d](https://technical-analysis-library-in-python.readthedocs.io/en/latest/ta.html#ta.momentum.stochrsi_d)<br>[stochrsi_k](https://technical-analysis-library-in-python.readthedocs.io/en/latest/ta.html#ta.momentum.stochrsi_k)
32 | True strength index (TSI) | [TSIIndicator](https://technical-analysis-library-in-python.readthedocs.io/en/latest/ta.html#ta.momentum.TSIIndicator) | [tsi](https://technical-analysis-library-in-python.readthedocs.io/en/latest/ta.html#ta.momentum.tsi)
33 | Ultimate Oscillator (UO) | [UltimateOscillator](https://technical-analysis-library-in-python.readthedocs.io/en/latest/ta.html#ta.momentum.UltimateOscillator) | [ultimate_oscillator](https://technical-analysis-library-in-python.readthedocs.io/en/latest/ta.html#ta.momentum.ultimate_oscillator)
34 | Stochastic Oscillator (SR) | [StochasticOscillator](https://technical-analysis-library-in-python.readthedocs.io/en/latest/ta.html#ta.momentum.StochasticOscillator) | [stoch](https://technical-analysis-library-in-python.readthedocs.io/en/latest/ta.html#ta.momentum.stoch)<br>[stoch_signal](https://technical-analysis-library-in-python.readthedocs.io/en/latest/ta.html#ta.momentum.stoch_signal)
35 | Williams %R (WR) | [WilliamsRIndicator](https://technical-analysis-library-in-python.readthedocs.io/en/latest/ta.html#ta.momentum.WilliamsRIndicator) | [williams_r](https://technical-analysis-library-in-python.readthedocs.io/en/latest/ta.html#ta.momentum.williams_r)
36 | Awesome Oscillator (AO) | [AwesomeOscillatorIndicator](https://technical-analysis-library-in-python.readthedocs.io/en/latest/ta.html#ta.momentum.AwesomeOscillatorIndicator) | [awesome_oscillator](https://technical-analysis-library-in-python.readthedocs.io/en/latest/ta.html#ta.momentum.awesome_oscillator)
37 | Kaufman's Adaptive Moving Average (KAMA) | [KAMAIndicator](https://technical-analysis-library-in-python.readthedocs.io/en/latest/ta.html#ta.momentum.KAMAIndicator) | [kama](https://technical-analysis-library-in-python.readthedocs.io/en/latest/ta.html#ta.momentum.kama)
38 | Rate of Change (ROC) | [ROCIndicator](https://technical-analysis-library-in-python.readthedocs.io/en/latest/ta.html#ta.momentum.ROCIndicator) | [roc](https://technical-analysis-library-in-python.readthedocs.io/en/latest/ta.html#ta.momentum.roc)
39 | Percentage Price Oscillator (PPO) | [PercentagePriceOscillator](https://technical-analysis-library-in-python.readthedocs.io/en/latest/ta.html#ta.momentum.PercentagePriceOscillator) | [ppo](https://technical-analysis-library-in-python.readthedocs.io/en/latest/ta.html#ta.momentum.ppo)<br>[ppo_hist](https://technical-analysis-library-in-python.readthedocs.io/en/latest/ta.html#ta.momentum.ppo_hist)<br>[ppo_signal](https://technical-analysis-library-in-python.readthedocs.io/en/latest/ta.html#ta.momentum.ppo_signal)
40 | Percentage Volume Oscillator (PVO) | [PercentageVolumeOscillator](https://technical-analysis-library-in-python.readthedocs.io/en/latest/ta.html#ta.momentum.PercentageVolumeOscillator) | [pvo](https://technical-analysis-library-in-python.readthedocs.io/en/latest/ta.html#ta.momentum.pvo)<br>[pvo_hist](https://technical-analysis-library-in-python.readthedocs.io/en/latest/ta.html#ta.momentum.pvo_hist)<br>[pvo_signal](https://technical-analysis-library-in-python.readthedocs.io/en/latest/ta.html#ta.momentum.pvo_signal)


<br>

## Others

ID | Name | Class | defs
-- |-- |-- |-- |
41 | Daily Return (DR) | [DailyReturnIndicator](https://technical-analysis-library-in-python.readthedocs.io/en/latest/ta.html#ta.others.DailyReturnIndicator) | [daily_return](https://technical-analysis-library-in-python.readthedocs.io/en/latest/ta.html#ta.others.daily_return)
42 | Daily Log Return (DLR) | [DailyLogReturnIndicator](https://technical-analysis-library-in-python.readthedocs.io/en/latest/ta.html#ta.others.DailyLogReturnIndicator) | [daily_log_return](https://technical-analysis-library-in-python.readthedocs.io/en/latest/ta.html#ta.others.daily_log_return)
43 | Cumulative Return (CR) | [CumulativeReturnIndicator](https://technical-analysis-library-in-python.readthedocs.io/en/latest/ta.html#ta.others.CumulativeReturnIndicator) | [cumulative_return](https://technical-analysis-library-in-python.readthedocs.io/en/latest/ta.html#ta.others.cumulative_return)

<br>


# Documentation

https://technical-analysis-library-in-python.readthedocs.io/en/latest/


# Motivation to use

* [English](https://towardsdatascience.com/technical-analysis-library-to-financial-datasets-with-pandas-python-4b2b390d3543)
* [Spanish](https://medium.com/datos-y-ciencia/biblioteca-de-an%C3%A1lisis-t%C3%A9cnico-sobre-series-temporales-financieras-para-machine-learning-with-cb28f9427d0)


# How to use (Python 3)

```sh
$ pip install --upgrade ta
```

To use this library you should have a financial time series dataset including `Timestamp`, `Open`, `High`, `Low`, `Close` and `Volume` columns.

You should clean or fill NaN values in your dataset before add technical analysis features.

You can get code examples in [examples_to_use](https://github.com/bukosabino/ta/tree/master/examples_to_use) folder.

You can visualize the features in [this notebook](https://github.com/bukosabino/ta/blob/master/examples_to_use/visualize_features.ipynb).


#### Example adding all features

```python
import pandas as pd
from ta import add_all_ta_features
from ta.utils import dropna


# Load datas
df = pd.read_csv('ta/tests/data/datas.csv', sep=',')

# Clean NaN values
df = dropna(df)

# Add all ta features
df = add_all_ta_features(
    df, open="Open", high="High", low="Low", close="Close", volume="Volume_BTC")
```


#### Example adding particular feature

```python
import pandas as pd
from ta.utils import dropna
from ta.volatility import BollingerBands


# Load datas
df = pd.read_csv('ta/tests/data/datas.csv', sep=',')

# Clean NaN values
df = dropna(df)

# Initialize Bollinger Bands Indicator
indicator_bb = BollingerBands(close=df["Close"], window=20, window_dev=2)

# Add Bollinger Bands features
df['bb_bbm'] = indicator_bb.bollinger_mavg()
df['bb_bbh'] = indicator_bb.bollinger_hband()
df['bb_bbl'] = indicator_bb.bollinger_lband()

# Add Bollinger Band high indicator
df['bb_bbhi'] = indicator_bb.bollinger_hband_indicator()

# Add Bollinger Band low indicator
df['bb_bbli'] = indicator_bb.bollinger_lband_indicator()

# Add Width Size Bollinger Bands
df['bb_bbw'] = indicator_bb.bollinger_wband()

# Add Percentage Bollinger Bands
df['bb_bbp'] = indicator_bb.bollinger_pband()
```

#### Beast scanner: Yahoo/NSE scan, replay, and accuracy validation

For the architecture overview, see [ARCHITECTURE.md](/workspaces/ta/ARCHITECTURE.md).
For a shorter command reference, see [USAGE.md](/workspaces/ta/USAGE.md).
For common questions, see [FAQ.md](/workspaces/ta/FAQ.md).

```python
from ta import run_beast_scan


# Omit symbols=... to scan the full NSE EQ universe from Yahoo Finance.
summary = run_beast_scan(symbols=["RELIANCE", "TCS", "INFY"], max_workers=4)
for match in summary.matches:
    print(match.symbol, match.signal.stage, match.signal.score, match.signal.metrics)
```

The scanner follows the Yahoo integration pattern from `scans-test`: it loads
daily OHLCV data with `yfinance.download`, normalizes raw NSE symbols to Yahoo
tickers with the `.NS` suffix, and can load the full NSE EQ universe from NSE's
public `EQUITY_L.csv` symbol file.

Live scans use `yfinance` as an optional dependency:

```sh
$ pip install yfinance
$ python -m ta.beast_scanner --symbols RELIANCE TCS INFY --max-workers 4
$ python -m ta.beast_scanner --replay --symbols RELIANCE TCS INFY --max-workers 4
$ python -m ta.beast_scanner --replay --timeframe weekly --period 10y --max-workers 12
$ python -m ta.beast_scanner --replay --timeframe monthly --period 10y --max-workers 12
```

The signal uses only technical data available at the signal candle: SMA/EMA
trend, MACD histogram, RSI, StochRSI, ROC, ADX direction, MFI, CMF, OBV
accumulation, ATR percent, Bollinger Band width/position, volume
dry-up/expansion, base contraction, long-range high/low distance, pivot
distance, breakout stage, liquidity, and measured technical upside. It does not
use forward data to create a signal.

Replay mode validates whether a historical signal actually went up afterward.
The strict default pass rule is:

* the forward high reaches at least `+5%` within `20` bars;
* the forward low does not breach `-8%` from entry;
* the final close in the lookahead window is positive.

Run a full NSE replay and save the evidence. `--timeframe` can be `daily`,
`weekly`, or `monthly`; weekly/monthly use resampled Yahoo daily bars and scaled
monthly defaults where required. To compare timeframes by a similar calendar
horizon, use `20` weekly bars, `100` daily bars, or `5` monthly bars.

```sh
$ python -m ta.beast_scanner \
    --replay \
    --timeframe daily \
    --period 10y \
    --lookahead-bars 100 \
    --cooldown-bars 50 \
    --max-workers 12 \
    --output-json /tmp/beast-daily-replay-calendar-v4.json
```

Run the pure technical optimizer against that replay without downloading data
again:

```sh
$ python -m ta.beast_scanner \
    --replay-input-json /tmp/beast-daily-replay-calendar-v4.json \
    --optimize-accuracy \
    --target-accuracy-pct 87.5 \
    --split-date 2024-01-01 \
    --min-train-signals 35 \
    --min-validation-signals 8 \
    --max-gate-clauses 6 \
    --optimizer-beam-width 80 \
    --output-json /tmp/beast-daily-calendar-weekly-ratio-wide-v4.json
```

Validation run on May 6, 2026:

* Daily, 10 years: `50,683` signals, `40.51%` strict accuracy. With split
  `2024-01-01`, the best larger-sample gate was
  `adx_pos14>=31.33 AND atr_pct<=2.77 AND cmf20<=0.13 AND roc60>=40.25`,
  producing `66.42%` full accuracy on `134` signals and `68.00%` holdout
  accuracy on `25` signals. A thinner daily search reached `79.55%` full
  accuracy but only `75.00%` holdout accuracy, so daily did not validate `80%`.
  Calendar-normalized daily replay using `100` bars produced `24,342` signals
  and `28.53%` baseline accuracy. The widest six-clause search still topped out
  at `75.00%` full and `75.00%` holdout accuracy, so daily did not validate the
  weekly-level `87.50%` holdout target.
* Weekly, 10 years: `1,597` signals, `39.39%` strict accuracy. With split
  `2024-01-01`, the best validated gate was
  `bb_width_pct<=28.18 AND breakout_volume_ratio<=1.44 AND long_low_gain_pct>=123.2 AND post_peak_drawdown_pct<=12.84`,
  producing `91.89%` full accuracy on `37` signals, `93.10%` train accuracy on
  `29` signals, and `87.50%` holdout accuracy on `8` signals.
* Monthly, 10 years: `856` signals, `26.99%` strict accuracy. With split
  `2023-01-01`, the best wide search produced `73.33%` full accuracy and
  `70.00%` holdout accuracy. With split `2024-01-01`, an in-sample gate reached
  `82.14%` full accuracy but only `50.00%` holdout accuracy, so monthly did not
  validate `80%` under the original `20`-month lookahead. Calendar-normalized
  monthly replay using `5` bars produced `1,440` signals and `35.07%` baseline
  accuracy. The validated monthly gate
  `adx_neg14>=13.67 AND atr_pct<=15.08 AND bb_width_pct>=31.42 AND mfi14>=63.95 AND recent_range_pct<=24.04 AND roc60<=99.74`
  produced `90.91%` full accuracy on `33` signals and `91.67%` holdout
  accuracy on `12` signals.

That means the strict, purely technical weekly-level target is currently
validated for weekly and calendar-normalized monthly. Daily is still not
validated at the same level. To apply the validated weekly gate to a live scan
or replay, repeat `--technical-gate`:

```sh
$ python -m ta.beast_scanner \
    --timeframe weekly \
    --period 10y \
    --technical-gate 'bb_width_pct<=28.18' \
    --technical-gate 'breakout_volume_ratio<=1.44' \
    --technical-gate 'long_low_gain_pct>=123.2' \
    --technical-gate 'post_peak_drawdown_pct<=12.84'
```

To apply the validated calendar-normalized monthly gate:

```sh
$ python -m ta.beast_scanner \
    --timeframe monthly \
    --period 10y \
    --lookahead-bars 5 \
    --cooldown-bars 3 \
    --technical-gate 'adx_neg14>=13.67' \
    --technical-gate 'atr_pct<=15.08' \
    --technical-gate 'bb_width_pct>=31.42' \
    --technical-gate 'mfi14>=63.95' \
    --technical-gate 'recent_range_pct<=24.04' \
    --technical-gate 'roc60<=99.74'
```

For the highest monthly win ratio found, use the stricter monthly
follow-through variant. It produced `13` signals, `13` passed, `100.00%` full
accuracy, `9/9` train wins, and `4/4` holdout wins on the calendar-normalized
monthly replay. This is the best win ratio, but it is more selective than the
broader monthly gate above.

```sh
$ python -m ta.beast_scanner \
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
    --technical-gate 'roc60<=99.74'
```


# Deploy and develop (for developers)

```sh
$ git clone https://github.com/bukosabino/ta.git
$ cd ta
$ pip install -r requirements-play.txt
$ make test
```


# Sponsor

![Logo OpenSistemas](static/logo_neuroons_byOS_blue.png)

Thank you to [OpenSistemas](https://opensistemas.com)! It is because of your contribution that I am able to continue the development of this open source library.


# Based on

* https://en.wikipedia.org/wiki/Technical_analysis
* https://pandas.pydata.org
* https://github.com/FreddieWitherden/ta
* https://github.com/femtotrader/pandas_talib


# In Progress

* Automated tests for all the indicators.


# TODO

* Use [NumExpr](https://github.com/pydata/numexpr) to speed up the NumPy/Pandas operations? [Article Motivation](https://towardsdatascience.com/speed-up-your-numpy-and-pandas-with-numexpr-package-25bd1ab0836b)
* Add [more technical analysis features](https://en.wikipedia.org/wiki/Technical_analysis).
* Wrapper to get financial data.
* Use of the Pandas multi-indexing techniques to calculate several indicators at the same time.
* Use Plotly/Streamlit to visualize features


# Changelog

Check the [changelog](https://github.com/bukosabino/ta/blob/master/RELEASE.md) of project.


# Donation

If you think `ta` library help you, please consider [buying me a coffee](https://www.paypal.me/guau/3).



# Credits

Developed by Darío López Padial (aka Bukosabino) and [other contributors](https://github.com/bukosabino/ta/graphs/contributors).

Please, let me know about any comment or feedback.

Also, I am a software engineer freelance focused on Data Science using Python tools such as Pandas, Scikit-Learn, Backtrader, Zipline or Catalyst. Don't hesitate to contact me if you need to develop something related with this library, Python, Technical Analysis, AlgoTrading, Machine Learning, etc.
