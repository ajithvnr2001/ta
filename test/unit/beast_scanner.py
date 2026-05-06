import unittest

import pandas as pd

from ta.beast_scanner import (
    BeastConfig,
    ReplayConfig,
    ReplayTrade,
    TechnicalGateClause,
    dataframe_to_ohlcv,
    analyze_beast_setup,
    optimize_replay_quality_gate,
    parse_nse_equity_csv,
    parse_technical_gate,
    passes_technical_gate,
    replay_history,
    resample_ohlcv,
    run_replay,
    run_scan,
    validate_forward_move,
)


class BeastScannerTests(unittest.TestCase):
    def test_detects_strict_early_entry_before_breakout(self):
        frame = beast_setup_frame(latest_close=160.0, latest_volume=700.0)

        signal = analyze_beast_setup(frame)

        self.assertEqual(signal.stage, "early_entry")
        self.assertTrue(signal.actionable)
        self.assertGreaterEqual(signal.score, 9)
        self.assertLessEqual(abs(signal.metrics["distance_to_pivot_pct"]), 1.5)
        self.assertIn("strict early-entry candidate before breakout", signal.reasons)

    def test_early_entry_passes_forward_up_validation(self):
        frame = beast_setup_frame(
            latest_close=160.0,
            latest_volume=700.0,
            future_mode="up",
        )
        as_of = frame.index[114]

        signal = analyze_beast_setup(
            frame,
            as_of=as_of,
            validate_forward=True,
            validation_lookahead=12,
            validation_min_gain_pct=5.0,
            validation_max_drawdown_pct=6.0,
        )

        self.assertEqual(signal.stage, "early_entry")
        self.assertIsNotNone(signal.validation)
        self.assertTrue(signal.validation.passed)
        self.assertGreaterEqual(signal.validation.max_gain_pct, 5.0)
        self.assertGreater(signal.validation.final_return_pct, 0)

    def test_forward_validation_fails_when_signal_does_not_go_up(self):
        frame = beast_setup_frame(
            latest_close=160.0,
            latest_volume=700.0,
            future_mode="down",
        )
        history = frame.iloc[:115]
        future = frame.iloc[115:]

        validation = validate_forward_move(
            history,
            future,
            lookahead_bars=12,
            min_gain_pct=5.0,
            max_drawdown_pct=6.0,
        )

        self.assertFalse(validation.passed)
        self.assertLess(validation.final_return_pct, 0)

    def test_detects_confirmed_breakout(self):
        frame = beast_setup_frame(latest_close=166.0, latest_volume=4200.0)

        signal = analyze_beast_setup(frame)

        self.assertEqual(signal.stage, "breakout_today")
        self.assertTrue(signal.actionable)
        self.assertGreaterEqual(signal.score, 10)
        self.assertIn("breakout volume confirms demand", signal.reasons)

    def test_middle_of_base_is_not_actionable(self):
        frame = beast_setup_frame(latest_close=150.0, latest_volume=700.0)

        signal = analyze_beast_setup(frame)

        self.assertEqual(signal.stage, "base")
        self.assertFalse(signal.actionable)

    def test_rejects_damaged_base_after_vertical_move(self):
        frame = beast_setup_frame(
            latest_close=118.0,
            latest_volume=700.0,
            crash_base=True,
        )

        signal = analyze_beast_setup(frame)

        self.assertEqual(signal.stage, "damaged_base")
        self.assertFalse(signal.actionable)
        self.assertLess(signal.score, 7)

    def test_requires_enough_history(self):
        signal = analyze_beast_setup(beast_setup_frame().iloc[:40])

        self.assertEqual(signal.stage, "insufficient_data")
        self.assertFalse(signal.actionable)

    def test_normalizes_yahoo_multiindex_frame(self):
        frame = beast_setup_frame().tail(5)
        frame.columns = pd.MultiIndex.from_tuples(
            (column, "ABC.NS") for column in frame.columns
        )

        normalized = dataframe_to_ohlcv(frame)

        self.assertEqual(
            list(normalized.columns), ["Open", "High", "Low", "Close", "Volume"]
        )
        self.assertEqual(len(normalized), 5)

    def test_parses_nse_equity_universe(self):
        content = "SYMBOL,SERIES,NAME OF COMPANY\nABC,EQ,ABC LTD\nXYZ,BE,XYZ LTD\nABC,EQ,ABC LTD\n"

        symbols = parse_nse_equity_csv(content)

        self.assertEqual(symbols, ["ABC.NS"])

    def test_resamples_ohlcv_to_weekly(self):
        rows = [
            _row(100.0 + index, 101.0 + index, 99.0 + index, 10.0 + index)
            for index in range(10)
        ]
        frame = pd.DataFrame(
            rows,
            index=pd.date_range("2024-01-01", periods=10, freq="D"),
        )

        weekly = resample_ohlcv(frame, timeframe="weekly")

        self.assertEqual(list(weekly.columns), ["Open", "High", "Low", "Close", "Volume"])
        self.assertEqual(len(weekly), 2)
        self.assertAlmostEqual(float(weekly["Open"].iloc[0]), rows[0]["Open"])
        self.assertAlmostEqual(float(weekly["Close"].iloc[0]), rows[4]["Close"])
        self.assertAlmostEqual(
            float(weekly["Volume"].iloc[0]), sum(row["Volume"] for row in rows[:5])
        )

    def test_scanner_runs_end_to_end_with_fake_provider(self):
        provider = FakeProvider(
            {
                "ABC.NS": beast_setup_frame(latest_close=160.0, latest_volume=700.0),
                "WEAK.NS": beast_setup_frame(latest_close=150.0, latest_volume=700.0),
            }
        )

        summary = run_scan(
            ["ABC", "WEAK"],
            provider=provider,
            config=BeastConfig(),
            max_workers=2,
        )

        self.assertEqual(summary.total_requested, 2)
        self.assertEqual(summary.total_with_data, 2)
        self.assertEqual(len(summary.matches), 1)
        self.assertEqual(summary.matches[0].symbol, "ABC.NS")
        self.assertEqual(summary.matches[0].signal.stage, "early_entry")

    def test_replay_history_measures_forward_accuracy(self):
        frame = beast_setup_frame(
            latest_close=160.0,
            latest_volume=700.0,
            future_mode="up",
        )

        trades = replay_history(
            "ABC.NS",
            frame,
            replay_config=ReplayConfig(
                lookahead_bars=12,
                min_gain_pct=5.0,
                max_drawdown_pct=6.0,
                stages=("early_entry",),
            ),
        )

        self.assertGreaterEqual(len(trades), 1)
        self.assertTrue(any(trade.passed for trade in trades))
        self.assertTrue(all(trade.stage == "early_entry" for trade in trades))

    def test_replay_scan_summarizes_accuracy(self):
        provider = FakeProvider(
            {
                "ABC.NS": beast_setup_frame(
                    latest_close=160.0,
                    latest_volume=700.0,
                    future_mode="up",
                ),
                "FAIL.NS": beast_setup_frame(
                    latest_close=160.0,
                    latest_volume=700.0,
                    future_mode="down",
                ),
            }
        )

        summary = run_replay(
            ["ABC", "FAIL"],
            provider=provider,
            replay_config=ReplayConfig(
                lookahead_bars=12,
                min_gain_pct=5.0,
                max_drawdown_pct=6.0,
                stages=("early_entry",),
                max_signals_per_symbol=1,
            ),
            max_workers=2,
        )
        payload = summary.to_dict()

        self.assertEqual(summary.total_requested, 2)
        self.assertEqual(summary.total_with_data, 2)
        self.assertEqual(payload["total_signals"], 2)
        self.assertEqual(payload["passed"], 1)
        self.assertEqual(payload["failed"], 1)
        self.assertEqual(payload["accuracy_pct"], 50.0)

    def test_technical_gate_filters_scan_results(self):
        provider = FakeProvider(
            {
                "ABC.NS": beast_setup_frame(latest_close=160.0, latest_volume=700.0),
                "FAIL.NS": beast_setup_frame(latest_close=160.0, latest_volume=700.0),
            }
        )

        summary = run_scan(
            ["ABC", "FAIL"],
            provider=provider,
            config=BeastConfig(),
            max_workers=2,
            technical_gate=(parse_technical_gate("rsi14<=10"),),
        )

        self.assertEqual(len(summary.matches), 0)

    def test_technical_gate_accepts_signal_metric_filters(self):
        signal = analyze_beast_setup(
            beast_setup_frame(latest_close=160.0, latest_volume=700.0)
        )

        self.assertTrue(
            passes_technical_gate(
                signal,
                (
                    TechnicalGateClause("stage", "==", "early_entry"),
                    TechnicalGateClause("score", ">=", 9.0),
                ),
            )
        )

    def test_replay_optimizer_validates_target_accuracy(self):
        trades = []
        for index in range(8):
            trades.append(
                optimizer_trade(
                    f"WIN{index}.NS",
                    "2024-06-01",
                    True,
                    rsi14=42.0,
                    adx14=16.0,
                )
            )
        for index in range(4):
            trades.append(
                optimizer_trade(
                    f"LOSE{index}.NS",
                    "2024-06-01",
                    False,
                    rsi14=70.0,
                    adx14=31.0,
                )
            )
        for index in range(4):
            trades.append(
                optimizer_trade(
                    f"VWIN{index}.NS",
                    "2025-06-01",
                    True,
                    rsi14=42.0,
                    adx14=16.0,
                )
            )
        trades.append(
            optimizer_trade(
                "VLOSE.NS",
                "2025-06-01",
                False,
                rsi14=70.0,
                adx14=31.0,
            )
        )

        report = optimize_replay_quality_gate(
            trades,
            target_accuracy_pct=80.0,
            split_date="2025-01-01",
            min_train_signals=5,
            min_validation_signals=3,
            max_clauses=2,
        )

        self.assertTrue(report.achieved)
        self.assertIsNotNone(report.best_candidate)
        self.assertGreaterEqual(report.best_candidate.train_accuracy_pct, 80.0)
        self.assertGreaterEqual(report.best_candidate.validation_accuracy_pct, 80.0)


class FakeProvider:
    def __init__(self, histories):
        self.histories = histories

    def fetch_history(self, symbol):
        return self.histories[symbol]


def beast_setup_frame(
    *,
    latest_close=166.0,
    latest_volume=4200.0,
    crash_base=False,
    future_mode=None,
):
    rows = []
    dates = []
    day = 1

    for index in range(45):
        close = 100.0 + (index % 5 - 2) * 0.25
        rows.append(_row(close, close + 1.0, close - 1.0, 900 + index * 2))
        dates.append(_date(day))
        day += 1

    for index in range(25):
        close = 103.0 + index * 2.35
        rows.append(_row(close, close * 1.025, close * 0.985, 2200 + index * 50))
        dates.append(_date(day))
        day += 1

    if crash_base:
        for index in range(44):
            close = 158.0 - index * 1.1
            rows.append(_row(close, close + 3.0, close - 12.0, 1200 - index * 8))
            dates.append(_date(day))
            day += 1
    else:
        for index in range(44):
            if index < 16:
                center = 153.0
                amplitude = 8.0 - index * 0.18
            elif index < 32:
                center = 156.0
                amplitude = 4.4 - (index - 16) * 0.08
            else:
                center = 157.0
                amplitude = 2.0 - (index - 32) * 0.04

            close = center + (0.35 if index % 2 == 0 else -0.35)
            volume = 1250.0 - index * 18.0
            rows.append(_row(close, center + amplitude, center - amplitude, volume))
            dates.append(_date(day))
            day += 1

    rows.append(
        _row(latest_close, latest_close + 2.0, latest_close - 5.0, latest_volume)
    )
    dates.append(_date(day))
    day += 1

    if future_mode == "up":
        for index in range(12):
            close = latest_close * (1.01 + index * 0.006)
            rows.append(_row(close, close * 1.012, close * 0.992, 1800 + index * 25))
            dates.append(_date(day))
            day += 1
    elif future_mode == "down":
        for index in range(12):
            close = latest_close * (0.99 - index * 0.007)
            rows.append(_row(close, close * 1.006, close * 0.982, 1800 + index * 25))
            dates.append(_date(day))
            day += 1

    return pd.DataFrame(rows, index=pd.to_datetime(dates))


def _row(close, high, low, volume):
    return {
        "Open": close * 0.995,
        "High": high,
        "Low": low,
        "Close": close,
        "Volume": volume,
    }


def optimizer_trade(symbol, signal_date, passed, rsi14, adx14):
    return ReplayTrade(
        symbol=symbol,
        signal_date=signal_date,
        entry_price=100.0,
        stage="early_entry",
        score=9,
        rating="B",
        passed=passed,
        max_gain_pct=6.0 if passed else 2.0,
        max_drawdown_pct=3.0,
        final_return_pct=3.0 if passed else -1.0,
        lookahead_bars=20,
        metrics={
            "latest_close": 100.0,
            "rsi14": rsi14,
            "adx14": adx14,
            "macd_diff": 0.2,
            "adx_pos14": 24.0,
            "adx_neg14": 12.0,
            "atr_pct": 3.0,
            "vertical_gain_pct": 35.0,
            "base_range_pct": 12.0,
            "recent_range_pct": 8.0,
            "base_drawdown_pct": 16.0,
            "post_peak_drawdown_pct": 12.0,
            "distance_to_pivot_pct": -1.0,
            "breakout_volume_ratio": 1.0,
            "technical_upside_pct": 18.0,
        },
        reasons=("synthetic optimizer row",),
    )


def _date(day):
    return pd.Timestamp("2024-01-01") + pd.Timedelta(days=day - 1)


if __name__ == "__main__":
    unittest.main()
