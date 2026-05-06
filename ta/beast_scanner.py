"""High-probability setup scanner built on the TA indicators in this package.

The live data path intentionally keeps yfinance optional. Importing this module
does not require network packages, but live scans will raise a clear error if
yfinance is missing.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable, Protocol
from urllib.error import URLError
from urllib.request import Request, urlopen

import pandas as pd

from ta.momentum import ROCIndicator, RSIIndicator, StochRSIIndicator
from ta.trend import ADXIndicator, EMAIndicator, MACD, SMAIndicator
from ta.volatility import AverageTrueRange, BollingerBands
from ta.volume import ChaikinMoneyFlowIndicator, MFIIndicator, OnBalanceVolumeIndicator


NSE_EQUITY_LIST_URL = "https://archives.nseindia.com/content/equities/EQUITY_L.csv"
OHLCV_COLUMNS = ("Open", "High", "Low", "Close", "Volume")
TIMEFRAME_ALIASES = {
    "d": "daily",
    "day": "daily",
    "daily": "daily",
    "1d": "daily",
    "w": "weekly",
    "week": "weekly",
    "weekly": "weekly",
    "1wk": "weekly",
    "m": "monthly",
    "month": "monthly",
    "monthly": "monthly",
    "1mo": "monthly",
}
TIMEFRAME_RESAMPLE_RULES = {
    "weekly": "W-FRI",
    "monthly": "ME",
}
TECHNICAL_METRIC_FIELDS = (
    "latest_close",
    "ma20",
    "ma50",
    "ema10",
    "ema21",
    "rsi14",
    "stochrsi_k",
    "roc20",
    "roc60",
    "macd_diff",
    "adx14",
    "adx_pos14",
    "adx_neg14",
    "mfi14",
    "cmf20",
    "atr_pct",
    "bb_width_pct",
    "bb_percent_b",
    "vertical_gain_pct",
    "long_high_distance_pct",
    "long_low_gain_pct",
    "base_range_pct",
    "recent_range_pct",
    "base_drawdown_pct",
    "post_peak_drawdown_pct",
    "pivot",
    "distance_to_pivot_pct",
    "breakout_volume_ratio",
    "latest_volume",
    "avg_volume_20",
    "avg_turnover_20",
    "bars_since_breakout",
    "technical_upside_pct",
    "timeframe",
)
TECHNICAL_GATE_FIELDS = frozenset(
    ("stage", "score", "rating", *TECHNICAL_METRIC_FIELDS)
)
OPTIMIZER_NUMERIC_FIELDS = (
    "score",
    "rsi14",
    "stochrsi_k",
    "roc20",
    "roc60",
    "macd_diff",
    "adx14",
    "adx_pos14",
    "adx_neg14",
    "mfi14",
    "cmf20",
    "atr_pct",
    "bb_width_pct",
    "bb_percent_b",
    "vertical_gain_pct",
    "long_high_distance_pct",
    "long_low_gain_pct",
    "base_range_pct",
    "recent_range_pct",
    "base_drawdown_pct",
    "post_peak_drawdown_pct",
    "distance_to_pivot_pct",
    "breakout_volume_ratio",
    "latest_volume",
    "avg_volume_20",
    "avg_turnover_20",
    "technical_upside_pct",
)
OPTIMIZER_QUANTILES = (0.10, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90)


class BeastScannerError(RuntimeError):
    """Base scanner error."""


class DataProviderError(BeastScannerError):
    """Raised when live market data cannot be loaded."""


class UniverseLoadError(BeastScannerError):
    """Raised when a symbol universe cannot be loaded."""


@dataclass(frozen=True)
class BeastConfig:
    """Tunable setup rules for the daily beast scanner."""

    min_bars: int = 90
    base_lookback: int = 45
    recent_lookback: int = 15
    vertical_lookback: int = 45
    near_pivot_pct: float = 0.02
    breakout_buffer_pct: float = 0.005
    breakout_scan_bars: int = 12
    follow_through_max_bars: int = 10
    fast_follow_through_bars: int = 8
    early_min_score: int = 9
    early_min_vertical_gain_pct: float = 0.35
    early_max_below_pivot_pct: float = 0.015
    early_max_above_pivot_pct: float = 0.01
    early_max_recent_range_pct: float = 0.10
    early_max_base_drawdown_pct: float = 0.24
    early_max_volume_ratio: float = 1.30
    damaged_drawdown_pct: float = 0.33
    damaged_range_pct: float = 0.45
    min_confirming_volume_ratio: float = 1.40


@dataclass(frozen=True)
class TechnicalGateClause:
    """One pure technical filter applied to a signal or replay trade."""

    field: str
    operator: str
    value: float | str

    def to_text(self) -> str:
        if isinstance(self.value, str):
            value = self.value
        else:
            value = f"{self.value:g}"
        return f"{self.field}{self.operator}{value}"

    def to_dict(self) -> dict[str, Any]:
        return {
            "field": self.field,
            "operator": self.operator,
            "value": self.value,
            "text": self.to_text(),
        }


@dataclass(frozen=True)
class ReplayConfig:
    """Replay rules for measuring historical scanner accuracy."""

    timeframe: str = "daily"
    lookahead_bars: int = 20
    min_gain_pct: float = 5.0
    max_drawdown_pct: float = 8.0
    cooldown_bars: int = 10
    stride: int = 1
    min_score: int | None = None
    actionable_only: bool = True
    stages: tuple[str, ...] = ("early_entry", "breakout_today", "follow_through")
    max_signals_per_symbol: int | None = None
    technical_gate: tuple[TechnicalGateClause, ...] = ()


def default_beast_config(timeframe: str = "daily") -> BeastConfig:
    """Return default scanner rules scaled for the requested bar timeframe."""

    normalized = normalize_timeframe(timeframe)
    if normalized == "monthly":
        return BeastConfig(
            min_bars=36,
            base_lookback=18,
            recent_lookback=6,
            vertical_lookback=18,
            breakout_scan_bars=6,
            follow_through_max_bars=4,
            fast_follow_through_bars=3,
            early_min_vertical_gain_pct=0.28,
            early_max_recent_range_pct=0.22,
            early_max_base_drawdown_pct=0.45,
            damaged_drawdown_pct=0.55,
            damaged_range_pct=0.80,
        )
    return BeastConfig()


@dataclass(frozen=True)
class ForwardValidation:
    """Forward move validation for historical signals."""

    status: str
    passed: bool
    lookahead_bars: int
    max_gain_pct: float
    max_drawdown_pct: float
    final_return_pct: float
    reasons: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class BeastSignal:
    """Signal produced by the beast setup analysis."""

    score: int
    rating: str
    stage: str
    actionable: bool
    reasons: tuple[str, ...]
    metrics: dict[str, Any]
    validation: ForwardValidation | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class StockScan:
    """Matched scanner row."""

    symbol: str
    signal: BeastSignal

    def to_dict(self) -> dict[str, Any]:
        payload = self.signal.to_dict()
        payload["symbol"] = self.symbol
        return payload


@dataclass(frozen=True)
class ScanSummary:
    """Scanner summary and matched rows."""

    total_requested: int
    total_with_data: int
    matches: tuple[StockScan, ...]
    errors: tuple[dict[str, str], ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_requested": self.total_requested,
            "total_with_data": self.total_with_data,
            "matches": len(self.matches),
            "errors": len(self.errors),
            "results": [match.to_dict() for match in self.matches],
            "error_details": list(self.errors[:25]),
        }


@dataclass(frozen=True)
class ReplayTrade:
    """One historical replay signal and its forward outcome."""

    symbol: str
    signal_date: str
    entry_price: float
    stage: str
    score: int
    rating: str
    passed: bool
    max_gain_pct: float
    max_drawdown_pct: float
    final_return_pct: float
    lookahead_bars: int
    metrics: dict[str, Any]
    reasons: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ReplaySummary:
    """Replay accuracy summary."""

    total_requested: int
    total_with_data: int
    trades: tuple[ReplayTrade, ...]
    errors: tuple[dict[str, str], ...]

    def to_dict(self) -> dict[str, Any]:
        passed = sum(1 for trade in self.trades if trade.passed)
        failed = len(self.trades) - passed
        return {
            "total_requested": self.total_requested,
            "total_with_data": self.total_with_data,
            "total_signals": len(self.trades),
            "passed": passed,
            "failed": failed,
            "accuracy_pct": _pct(passed, len(self.trades)),
            "avg_max_gain_pct": _avg(trade.max_gain_pct for trade in self.trades),
            "avg_max_drawdown_pct": _avg(
                trade.max_drawdown_pct for trade in self.trades
            ),
            "avg_final_return_pct": _avg(
                trade.final_return_pct for trade in self.trades
            ),
            "by_stage": _replay_stats_by_stage(self.trades),
            "errors": len(self.errors),
            "results": [trade.to_dict() for trade in self.trades],
            "error_details": list(self.errors[:25]),
        }


@dataclass(frozen=True)
class ReplayGateCandidate:
    """Candidate technical gate and its train/validation accuracy."""

    clauses: tuple[TechnicalGateClause, ...]
    total_signals: int
    total_passed: int
    total_accuracy_pct: float
    train_signals: int
    train_passed: int
    train_accuracy_pct: float
    validation_signals: int
    validation_passed: int
    validation_accuracy_pct: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "gate": [clause.to_text() for clause in self.clauses],
            "clauses": [clause.to_dict() for clause in self.clauses],
            "total_signals": self.total_signals,
            "total_passed": self.total_passed,
            "total_accuracy_pct": self.total_accuracy_pct,
            "train_signals": self.train_signals,
            "train_passed": self.train_passed,
            "train_accuracy_pct": self.train_accuracy_pct,
            "validation_signals": self.validation_signals,
            "validation_passed": self.validation_passed,
            "validation_accuracy_pct": self.validation_accuracy_pct,
        }


@dataclass(frozen=True)
class ReplayOptimizationReport:
    """Pure technical replay optimizer result."""

    target_accuracy_pct: float
    achieved: bool
    split_date: str
    min_train_signals: int
    min_validation_signals: int
    max_clauses: int
    evaluated_candidates: int
    baseline: ReplayGateCandidate
    best_candidate: ReplayGateCandidate | None
    top_candidates: tuple[ReplayGateCandidate, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "target_accuracy_pct": self.target_accuracy_pct,
            "achieved": self.achieved,
            "split_date": self.split_date,
            "min_train_signals": self.min_train_signals,
            "min_validation_signals": self.min_validation_signals,
            "max_clauses": self.max_clauses,
            "evaluated_candidates": self.evaluated_candidates,
            "baseline": self.baseline.to_dict(),
            "best_candidate": (
                self.best_candidate.to_dict() if self.best_candidate else None
            ),
            "top_candidates": [
                candidate.to_dict() for candidate in self.top_candidates
            ],
        }


class HistoryProvider(Protocol):
    """Protocol for testable history providers."""

    def fetch_history(self, symbol: str) -> pd.DataFrame:
        ...


class YahooDataProvider:
    """Yahoo Finance daily-history provider."""

    def __init__(
        self,
        period: str = "2y",
        interval: str = "1d",
        exchange_suffix: str = ".NS",
        auto_adjust: bool = False,
        validate_symbols: bool = False,
    ) -> None:
        self.period = period
        self.interval = interval
        self.exchange_suffix = exchange_suffix
        self.auto_adjust = auto_adjust
        self.validate_symbols = validate_symbols

    def ensure_available(self) -> None:
        try:
            import yfinance  # noqa: F401
        except ModuleNotFoundError as exc:
            raise DataProviderError(
                "yfinance is not installed. Run `pip install yfinance` before live scans."
            ) from exc

    def fetch_history(self, symbol: str) -> pd.DataFrame:
        self.ensure_available()

        yahoo_symbol = to_yahoo_symbol(symbol, exchange_suffix=self.exchange_suffix)
        if self.validate_symbols and self.exchange_suffix == ".NS":
            if not is_valid_nse_symbol(yahoo_symbol):
                return pd.DataFrame(columns=OHLCV_COLUMNS)

        import yfinance as yf

        try:
            frame = yf.download(
                yahoo_symbol,
                period=self.period,
                interval=self.interval,
                progress=False,
                auto_adjust=self.auto_adjust,
                threads=False,
            )
        except Exception as exc:
            raise DataProviderError(
                f"{yahoo_symbol}: failed to fetch history: {exc}"
            ) from exc

        return dataframe_to_ohlcv(frame)


def normalize_symbol(symbol: str) -> str:
    """Normalize a user-supplied stock symbol."""

    return symbol.strip().upper()


def to_yahoo_symbol(symbol: str, exchange_suffix: str = ".NS") -> str:
    """Convert a symbol to a Yahoo ticker, defaulting to NSE tickers."""

    clean = normalize_symbol(symbol)
    if not clean:
        raise ValueError("empty symbol")
    if not exchange_suffix:
        return clean
    if clean.endswith(exchange_suffix.upper()):
        return clean
    if "." in clean:
        return clean
    return f"{clean}{exchange_suffix.upper()}"


def unique_yahoo_symbols(
    symbols: Iterable[str],
    exchange_suffix: str = ".NS",
) -> list[str]:
    """Return unique Yahoo symbols while preserving input order."""

    seen: set[str] = set()
    output: list[str] = []
    for raw_symbol in symbols:
        symbol = to_yahoo_symbol(raw_symbol, exchange_suffix=exchange_suffix)
        if symbol in seen:
            continue
        seen.add(symbol)
        output.append(symbol)
    return output


def parse_nse_equity_csv(
    content: str,
    allowed_series: tuple[str, ...] = ("EQ",),
) -> list[str]:
    """Parse NSE equity CSV content into Yahoo NSE symbols."""

    reader = csv.DictReader(content.splitlines())
    symbols: list[str] = []

    for row in reader:
        normalized = {
            key.strip().upper(): value.strip()
            for key, value in row.items()
            if key is not None
        }
        symbol = normalized.get("SYMBOL")
        series = normalized.get("SERIES", "")

        if not symbol:
            continue
        if allowed_series and series.upper() not in allowed_series:
            continue
        symbols.append(symbol)

    if not symbols:
        raise UniverseLoadError("NSE equity CSV did not contain any matching symbols")

    return unique_yahoo_symbols(symbols, exchange_suffix=".NS")


def load_all_nse_symbols(
    source_url: str = NSE_EQUITY_LIST_URL,
    timeout: int = 20,
    allowed_series: tuple[str, ...] = ("EQ",),
) -> list[str]:
    """Load the NSE equity universe from NSE's public CSV."""

    request = Request(
        source_url,
        headers={
            "User-Agent": "Mozilla/5.0 beast setup scanner",
            "Accept": "text/csv,*/*",
        },
    )

    try:
        with urlopen(request, timeout=timeout) as response:
            content = response.read().decode("utf-8-sig")
    except (OSError, URLError) as exc:
        raise UniverseLoadError(
            f"Unable to load NSE symbols from {source_url}: {exc}"
        ) from exc

    return parse_nse_equity_csv(content, allowed_series=allowed_series)


def load_symbols_file(path: str | Path, exchange_suffix: str = ".NS") -> list[str]:
    """Load symbols from a newline, comma, or whitespace-separated file."""

    lines = Path(path).read_text(encoding="utf-8").splitlines()
    symbols: list[str] = []
    for line in lines:
        clean = line.split("#", 1)[0].strip()
        if not clean:
            continue
        symbols.extend(part for part in clean.replace(",", " ").split() if part)

    if not symbols:
        raise UniverseLoadError(f"No symbols found in {path}")

    return unique_yahoo_symbols(symbols, exchange_suffix=exchange_suffix)


def parse_technical_gate(text: str) -> TechnicalGateClause:
    """Parse a CLI technical gate such as ``rsi14<=55``."""

    for operator in (">=", "<=", "==", ">", "<"):
        if operator not in text:
            continue

        field, raw_value = text.split(operator, 1)
        field = field.strip()
        raw_value = raw_value.strip()
        if field not in TECHNICAL_GATE_FIELDS:
            raise ValueError(
                f"unsupported technical gate field {field!r}; "
                f"supported fields: {', '.join(sorted(TECHNICAL_GATE_FIELDS))}"
            )
        if not raw_value:
            raise ValueError(f"missing value for technical gate {text!r}")

        value: float | str
        try:
            value = float(raw_value)
        except ValueError:
            value = raw_value

        return TechnicalGateClause(field=field, operator=operator, value=value)

    raise ValueError(
        f"technical gate {text!r} must contain one of >=, <=, ==, >, <"
    )


def parse_technical_gates(values: Iterable[str] | None) -> tuple[TechnicalGateClause, ...]:
    """Parse zero or more CLI technical gate expressions."""

    if not values:
        return ()
    return tuple(parse_technical_gate(value) for value in values)


def passes_technical_gate(
    source: BeastSignal | ReplayTrade,
    clauses: tuple[TechnicalGateClause, ...],
) -> bool:
    """Return whether a signal/trade passes all pure technical gate clauses."""

    for clause in clauses:
        actual = _technical_gate_value(source, clause.field)
        if actual is None:
            return False
        if not _compare_gate_value(actual, clause.operator, clause.value):
            return False
    return True


def is_valid_nse_symbol(symbol: str) -> bool:
    """Best-effort NSE validation when nsetools is installed."""

    clean = normalize_symbol(symbol)
    if clean.endswith(".NS"):
        clean = clean[:-3]

    try:
        from nsetools import Nse
    except ModuleNotFoundError:
        return True

    try:
        quote = Nse().get_quote(clean)
    except Exception:
        return False

    return quote is not None


def dataframe_to_ohlcv(frame: Any) -> pd.DataFrame:
    """Normalize a Yahoo-style frame to Open/High/Low/Close/Volume columns."""

    if frame is None or getattr(frame, "empty", True):
        return pd.DataFrame(columns=OHLCV_COLUMNS)

    data = frame.copy()
    if getattr(data.columns, "nlevels", 1) > 1:
        data = _flatten_single_symbol_columns(data)

    missing = [column for column in OHLCV_COLUMNS if column not in data.columns]
    if missing:
        raise DataProviderError(f"history is missing columns: {', '.join(missing)}")

    data = data.loc[:, list(OHLCV_COLUMNS)].copy()
    for column in OHLCV_COLUMNS:
        data[column] = pd.to_numeric(data[column], errors="coerce")

    data = data.dropna()
    if not data.empty:
        data = data.sort_index()
    return data


def normalize_timeframe(timeframe: str | None) -> str:
    """Normalize a scanner timeframe."""

    clean = (timeframe or "daily").strip().lower()
    if clean not in TIMEFRAME_ALIASES:
        raise ValueError(
            f"unsupported timeframe {timeframe!r}; use daily, weekly, or monthly"
        )
    return TIMEFRAME_ALIASES[clean]


def resample_ohlcv(frame: Any, timeframe: str = "daily") -> pd.DataFrame:
    """Normalize and resample OHLCV bars to daily, weekly, or monthly candles."""

    data = dataframe_to_ohlcv(frame)
    normalized = normalize_timeframe(timeframe)
    if normalized == "daily" or data.empty:
        return data

    data = data.copy()
    data.index = pd.to_datetime(data.index, errors="coerce")
    data = data[~pd.isna(data.index)]
    if data.empty:
        return pd.DataFrame(columns=OHLCV_COLUMNS)

    resampled = data.resample(
        TIMEFRAME_RESAMPLE_RULES[normalized],
        label="right",
        closed="right",
    ).agg(
        {
            "Open": "first",
            "High": "max",
            "Low": "min",
            "Close": "last",
            "Volume": "sum",
        }
    )
    return dataframe_to_ohlcv(resampled)


def analyze_beast_setup(
    frame: Any,
    *,
    config: BeastConfig | None = None,
    timeframe: str = "daily",
    as_of: str | pd.Timestamp | None = None,
    validate_forward: bool = False,
    validation_lookahead: int = 20,
    validation_min_gain_pct: float = 5.0,
    validation_max_drawdown_pct: float = 8.0,
) -> BeastSignal:
    """Analyze one OHLCV history for an early, high-probability long setup."""

    active_timeframe = normalize_timeframe(timeframe)
    active_config = config or default_beast_config(active_timeframe)
    data = resample_ohlcv(frame, timeframe=active_timeframe)

    if as_of is not None and not data.empty:
        cutoff = pd.Timestamp(as_of)
        history = data.loc[pd.to_datetime(data.index) <= cutoff]
        future = data.loc[pd.to_datetime(data.index) > cutoff].head(
            validation_lookahead
        )
    else:
        history = data
        future = data.iloc[0:0]

    signal = _signal_with_metric(
        _analyze_history(history, active_config),
        "timeframe",
        active_timeframe,
    )
    if not validate_forward:
        return signal

    validation = validate_forward_move(
        history,
        future,
        lookahead_bars=validation_lookahead,
        min_gain_pct=validation_min_gain_pct,
        max_drawdown_pct=validation_max_drawdown_pct,
    )
    return BeastSignal(
        score=signal.score,
        rating=signal.rating,
        stage=signal.stage,
        actionable=signal.actionable,
        reasons=signal.reasons,
        metrics=signal.metrics,
        validation=validation,
    )


def validate_forward_move(
    history: pd.DataFrame,
    future: pd.DataFrame,
    *,
    lookahead_bars: int = 20,
    min_gain_pct: float = 5.0,
    max_drawdown_pct: float = 8.0,
) -> ForwardValidation:
    """Validate that a historical signal moved up before failing risk."""

    history = dataframe_to_ohlcv(history)
    future = dataframe_to_ohlcv(future)
    if history.empty or future.empty:
        return ForwardValidation(
            status="unavailable",
            passed=False,
            lookahead_bars=0,
            max_gain_pct=0.0,
            max_drawdown_pct=0.0,
            final_return_pct=0.0,
            reasons=("future candles are not available for validation",),
        )

    entry = float(history["Close"].iloc[-1])
    selected = future.head(lookahead_bars)
    max_high = float(selected["High"].max())
    min_low = float(selected["Low"].min())
    final_close = float(selected["Close"].iloc[-1])

    forward_max_gain_pct = ((max_high - entry) / entry) * 100.0
    forward_max_drawdown_pct = ((entry - min_low) / entry) * 100.0
    forward_final_return_pct = ((final_close - entry) / entry) * 100.0

    passed = (
        forward_max_gain_pct >= min_gain_pct
        and forward_max_drawdown_pct <= max_drawdown_pct
        and forward_final_return_pct > 0
    )
    reasons: list[str] = []
    if forward_max_gain_pct >= min_gain_pct:
        reasons.append("forward high reached the required upside")
    else:
        reasons.append("forward high did not reach the required upside")
    if forward_max_drawdown_pct <= max_drawdown_pct:
        reasons.append("forward drawdown stayed inside risk")
    else:
        reasons.append("forward drawdown broke risk")
    if forward_final_return_pct > 0:
        reasons.append("forward close stayed positive")
    else:
        reasons.append("forward close was not positive")

    return ForwardValidation(
        status="passed" if passed else "failed",
        passed=passed,
        lookahead_bars=len(selected),
        max_gain_pct=round(forward_max_gain_pct, 2),
        max_drawdown_pct=round(forward_max_drawdown_pct, 2),
        final_return_pct=round(forward_final_return_pct, 2),
        reasons=tuple(reasons),
    )


def process_stock(
    symbol: str,
    provider: HistoryProvider,
    *,
    config: BeastConfig | None = None,
    timeframe: str = "daily",
    min_score: int | None = None,
    actionable_only: bool = True,
    technical_gate: tuple[TechnicalGateClause, ...] = (),
) -> tuple[StockScan | None, bool, dict[str, str] | None]:
    """Fetch and analyze a single symbol."""

    try:
        history = provider.fetch_history(symbol)
        if history.empty:
            return None, False, None

        signal = analyze_beast_setup(history, config=config, timeframe=timeframe)
        threshold = (
            min_score
            if min_score is not None
            else (config or BeastConfig()).early_min_score
        )
        is_match = signal.score >= threshold and (
            signal.actionable or not actionable_only
        )
        if is_match and technical_gate:
            is_match = passes_technical_gate(signal, technical_gate)
        if not is_match:
            return None, True, None

        return StockScan(symbol=symbol, signal=signal), True, None
    except Exception as exc:
        return None, False, {"symbol": symbol, "error": str(exc)}


def run_scan(
    symbols: list[str] | None = None,
    *,
    provider: HistoryProvider | None = None,
    config: BeastConfig | None = None,
    timeframe: str = "daily",
    min_score: int | None = None,
    max_workers: int | None = None,
    actionable_only: bool = True,
    exchange_suffix: str = ".NS",
    technical_gate: tuple[TechnicalGateClause, ...] = (),
) -> ScanSummary:
    """Scan a symbol list, or the full NSE equity universe by default."""

    active_timeframe = normalize_timeframe(timeframe)
    active_config = config or default_beast_config(active_timeframe)
    scan_symbols = (
        unique_yahoo_symbols(symbols, exchange_suffix=exchange_suffix)
        if symbols is not None
        else load_all_nse_symbols()
    )
    history_provider = provider or YahooDataProvider(exchange_suffix=exchange_suffix)
    worker_count = max_workers or min(16, max(4, (os.cpu_count() or 2) * 2))

    matches: list[StockScan] = []
    errors: list[dict[str, str]] = []
    total_with_data = 0

    with ThreadPoolExecutor(max_workers=worker_count) as executor:
        futures = {
            executor.submit(
                process_stock,
                symbol,
                history_provider,
                config=active_config,
                timeframe=active_timeframe,
                min_score=min_score,
                actionable_only=actionable_only,
                technical_gate=technical_gate,
            ): symbol
            for symbol in scan_symbols
        }

        for future in as_completed(futures):
            match, had_data, error = future.result()
            if had_data:
                total_with_data += 1
            if error:
                errors.append(error)
            if match:
                matches.append(match)

    matches.sort(key=_scan_sort_key, reverse=True)
    return ScanSummary(
        total_requested=len(scan_symbols),
        total_with_data=total_with_data,
        matches=tuple(matches),
        errors=tuple(errors),
    )


def replay_history(
    symbol: str,
    frame: Any,
    *,
    config: BeastConfig | None = None,
    replay_config: ReplayConfig | None = None,
) -> tuple[ReplayTrade, ...]:
    """Replay one symbol and score historical forward outcomes."""

    active_replay = replay_config or ReplayConfig()
    active_timeframe = normalize_timeframe(active_replay.timeframe)
    active_config = config or default_beast_config(active_timeframe)
    data = resample_ohlcv(frame, timeframe=active_timeframe)
    if len(data) < active_config.min_bars + active_replay.lookahead_bars:
        return ()

    features = _build_indicator_features(data, active_config)
    min_score = (
        active_replay.min_score
        if active_replay.min_score is not None
        else active_config.early_min_score
    )
    stage_filter = set(active_replay.stages)
    trades: list[ReplayTrade] = []
    cooldown_until = active_config.min_bars - 1
    last_signal_index = len(data) - active_replay.lookahead_bars - 1

    for index in range(active_config.min_bars - 1, last_signal_index + 1):
        if (
            active_replay.stride > 1
            and (index - active_config.min_bars + 1) % active_replay.stride
        ):
            continue
        if index < cooldown_until:
            continue

        signal = _analyze_at_index(data, features, index, active_config)
        if signal.stage not in stage_filter:
            continue
        if signal.score < min_score:
            continue
        if active_replay.actionable_only and not signal.actionable:
            continue
        if active_replay.technical_gate and not passes_technical_gate(
            signal, active_replay.technical_gate
        ):
            continue

        history = data.iloc[: index + 1]
        future = data.iloc[index + 1 : index + 1 + active_replay.lookahead_bars]
        validation = validate_forward_move(
            history,
            future,
            lookahead_bars=active_replay.lookahead_bars,
            min_gain_pct=active_replay.min_gain_pct,
            max_drawdown_pct=active_replay.max_drawdown_pct,
        )
        trades.append(
            ReplayTrade(
                symbol=symbol,
                signal_date=str(
                    getattr(data.index[index], "date", lambda: data.index[index])()
                ),
                entry_price=signal.metrics["latest_close"],
                stage=signal.stage,
                score=signal.score,
                rating=signal.rating,
                passed=validation.passed,
                max_gain_pct=validation.max_gain_pct,
                max_drawdown_pct=validation.max_drawdown_pct,
                final_return_pct=validation.final_return_pct,
                lookahead_bars=validation.lookahead_bars,
                metrics={**signal.metrics, "timeframe": active_timeframe},
                reasons=signal.reasons,
            )
        )
        cooldown_until = index + active_replay.cooldown_bars

        if (
            active_replay.max_signals_per_symbol is not None
            and len(trades) >= active_replay.max_signals_per_symbol
        ):
            break

    return tuple(trades)


def process_replay_stock(
    symbol: str,
    provider: HistoryProvider,
    *,
    config: BeastConfig | None = None,
    replay_config: ReplayConfig | None = None,
) -> tuple[tuple[ReplayTrade, ...], bool, dict[str, str] | None]:
    """Fetch and replay a single symbol."""

    try:
        history = provider.fetch_history(symbol)
        if history.empty:
            return (), False, None
        trades = replay_history(
            symbol,
            history,
            config=config,
            replay_config=replay_config,
        )
        return trades, True, None
    except Exception as exc:
        return (), False, {"symbol": symbol, "error": str(exc)}


def run_replay(
    symbols: list[str] | None = None,
    *,
    provider: HistoryProvider | None = None,
    config: BeastConfig | None = None,
    replay_config: ReplayConfig | None = None,
    max_workers: int | None = None,
    exchange_suffix: str = ".NS",
) -> ReplaySummary:
    """Replay scanner signals for a symbol list or the full NSE universe."""

    active_replay = replay_config or ReplayConfig()
    active_config = config or default_beast_config(active_replay.timeframe)
    scan_symbols = (
        unique_yahoo_symbols(symbols, exchange_suffix=exchange_suffix)
        if symbols is not None
        else load_all_nse_symbols()
    )
    history_provider = provider or YahooDataProvider(exchange_suffix=exchange_suffix)
    worker_count = max_workers or min(16, max(4, (os.cpu_count() or 2) * 2))

    trades: list[ReplayTrade] = []
    errors: list[dict[str, str]] = []
    total_with_data = 0

    with ThreadPoolExecutor(max_workers=worker_count) as executor:
        futures = {
            executor.submit(
                process_replay_stock,
                symbol,
                history_provider,
                config=active_config,
                replay_config=active_replay,
            ): symbol
            for symbol in scan_symbols
        }

        for future in as_completed(futures):
            symbol_trades, had_data, error = future.result()
            if had_data:
                total_with_data += 1
            if error:
                errors.append(error)
            trades.extend(symbol_trades)

    trades.sort(
        key=lambda trade: (
            trade.signal_date,
            trade.score,
            trade.max_gain_pct,
            -trade.max_drawdown_pct,
        ),
        reverse=True,
    )
    return ReplaySummary(
        total_requested=len(scan_symbols),
        total_with_data=total_with_data,
        trades=tuple(trades),
        errors=tuple(errors),
    )


def load_replay_summary_json(path: str | Path) -> ReplaySummary:
    """Load a replay JSON produced by this module."""

    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    trades = tuple(
        ReplayTrade(
            symbol=str(row["symbol"]),
            signal_date=str(row["signal_date"]),
            entry_price=float(row["entry_price"]),
            stage=str(row["stage"]),
            score=int(row["score"]),
            rating=str(row["rating"]),
            passed=bool(row["passed"]),
            max_gain_pct=float(row["max_gain_pct"]),
            max_drawdown_pct=float(row["max_drawdown_pct"]),
            final_return_pct=float(row["final_return_pct"]),
            lookahead_bars=int(row["lookahead_bars"]),
            metrics=dict(row.get("metrics", {})),
            reasons=tuple(row.get("reasons", ())),
        )
        for row in payload.get("results", ())
    )
    return ReplaySummary(
        total_requested=int(payload.get("total_requested", 0)),
        total_with_data=int(payload.get("total_with_data", 0)),
        trades=trades,
        errors=tuple(payload.get("error_details", ())),
    )


def optimize_replay_quality_gate(
    trades: Iterable[ReplayTrade],
    *,
    target_accuracy_pct: float = 80.0,
    split_date: str | pd.Timestamp | None = None,
    min_train_signals: int = 30,
    min_validation_signals: int = 10,
    max_clauses: int = 3,
    beam_width: int = 80,
) -> ReplayOptimizationReport:
    """Search pure technical gates and validate them on a chronological holdout."""

    frame = _trades_to_optimizer_frame(tuple(trades))
    if frame.empty:
        baseline = ReplayGateCandidate((), 0, 0, 0.0, 0, 0, 0.0, 0, 0, 0.0)
        return ReplayOptimizationReport(
            target_accuracy_pct=target_accuracy_pct,
            achieved=False,
            split_date="",
            min_train_signals=min_train_signals,
            min_validation_signals=min_validation_signals,
            max_clauses=max_clauses,
            evaluated_candidates=0,
            baseline=baseline,
            best_candidate=None,
            top_candidates=(),
        )

    resolved_split = _resolve_optimizer_split_date(frame, split_date)
    train_mask = frame["signal_date"] < resolved_split
    validation_mask = frame["signal_date"] >= resolved_split
    all_mask = pd.Series(True, index=frame.index)
    baseline = _gate_candidate_from_mask(
        frame,
        all_mask,
        (),
        train_mask,
        validation_mask,
    )
    clauses = _build_optimizer_clauses(frame, train_mask)
    clause_masks = {
        clause.to_text(): _clause_mask(frame, clause) for clause in clauses
    }

    states: list[tuple[tuple[TechnicalGateClause, ...], pd.Series, ReplayGateCandidate]]
    states = [((), all_mask, baseline)]
    candidates: list[ReplayGateCandidate] = []
    seen: set[tuple[str, ...]] = set()

    for _depth in range(max(1, max_clauses)):
        next_states: list[
            tuple[tuple[TechnicalGateClause, ...], pd.Series, ReplayGateCandidate]
        ] = []
        for existing_clauses, existing_mask, _candidate in states:
            for clause in clauses:
                if _is_redundant_clause(existing_clauses, clause):
                    continue

                new_clauses = tuple(
                    sorted((*existing_clauses, clause), key=lambda item: item.to_text())
                )
                key = tuple(item.to_text() for item in new_clauses)
                if key in seen:
                    continue
                seen.add(key)

                new_mask = existing_mask & clause_masks[clause.to_text()]
                candidate = _gate_candidate_from_mask(
                    frame,
                    new_mask,
                    new_clauses,
                    train_mask,
                    validation_mask,
                )
                if candidate.train_signals < min_train_signals:
                    continue

                candidates.append(candidate)
                next_states.append((new_clauses, new_mask, candidate))

        if not next_states:
            break

        states = [
            item
            for item in sorted(
                next_states,
                key=lambda item: _optimizer_train_rank(item[2]),
                reverse=True,
            )[:beam_width]
        ]

    validated = [
        candidate
        for candidate in candidates
        if candidate.validation_signals >= min_validation_signals
    ]
    achieved = [
        candidate
        for candidate in validated
        if candidate.train_accuracy_pct >= target_accuracy_pct
        and candidate.validation_accuracy_pct >= target_accuracy_pct
    ]
    ranked = sorted(
        achieved or validated or candidates,
        key=_optimizer_validation_rank,
        reverse=True,
    )
    top_candidates = tuple(ranked[:5])
    best_candidate = ranked[0] if ranked else None

    return ReplayOptimizationReport(
        target_accuracy_pct=target_accuracy_pct,
        achieved=bool(achieved),
        split_date=str(resolved_split.date()),
        min_train_signals=min_train_signals,
        min_validation_signals=min_validation_signals,
        max_clauses=max_clauses,
        evaluated_candidates=len(candidates),
        baseline=baseline,
        best_candidate=best_candidate,
        top_candidates=top_candidates,
    )


def main(argv: list[str] | None = None) -> int:
    """Command line entry point."""

    args = _parse_args(argv)
    technical_gate = parse_technical_gates(args.technical_gate)
    if args.optimize_accuracy and not args.replay_input_json:
        args.replay = True

    if args.replay_input_json:
        replay_summary = load_replay_summary_json(args.replay_input_json)
        if technical_gate:
            replay_summary = ReplaySummary(
                total_requested=replay_summary.total_requested,
                total_with_data=replay_summary.total_with_data,
                trades=tuple(
                    trade
                    for trade in replay_summary.trades
                    if passes_technical_gate(trade, technical_gate)
                ),
                errors=replay_summary.errors,
            )
        replay_payload = replay_summary.to_dict()
        optimization_report = None
        if args.optimize_accuracy:
            optimization_report = optimize_replay_quality_gate(
                replay_summary.trades,
                target_accuracy_pct=args.target_accuracy_pct,
                split_date=args.split_date,
                min_train_signals=args.min_train_signals,
                min_validation_signals=args.min_validation_signals,
                max_clauses=args.max_gate_clauses,
                beam_width=args.optimizer_beam_width,
            )
            replay_payload["optimization"] = optimization_report.to_dict()

        if args.output_json:
            Path(args.output_json).write_text(
                json.dumps(replay_payload, indent=2), encoding="utf-8"
            )

        if args.json:
            print(json.dumps(replay_payload, indent=2))
        else:
            _print_replay_summary(replay_summary, top=args.top)
            if optimization_report:
                _print_optimization_report(optimization_report)

        return 0

    symbols = _resolve_cli_symbols(args)
    provider = YahooDataProvider(
        period=args.period,
        interval=args.interval,
        exchange_suffix=args.exchange_suffix,
        validate_symbols=args.validate_symbols,
    )
    if args.replay:
        replay_config = ReplayConfig(
            timeframe=args.timeframe,
            lookahead_bars=args.lookahead_bars,
            min_gain_pct=args.min_gain_pct,
            max_drawdown_pct=args.max_drawdown_pct,
            cooldown_bars=args.cooldown_bars,
            stride=args.stride,
            min_score=args.min_score,
            actionable_only=not args.include_watchlist,
            stages=tuple(args.replay_stages),
            max_signals_per_symbol=args.max_signals_per_symbol,
            technical_gate=technical_gate,
        )
        replay_summary = run_replay(
            symbols,
            provider=provider,
            replay_config=replay_config,
            max_workers=args.max_workers,
            exchange_suffix=args.exchange_suffix,
        )
        replay_payload = replay_summary.to_dict()
        optimization_report = None
        if args.optimize_accuracy:
            optimization_report = optimize_replay_quality_gate(
                replay_summary.trades,
                target_accuracy_pct=args.target_accuracy_pct,
                split_date=args.split_date,
                min_train_signals=args.min_train_signals,
                min_validation_signals=args.min_validation_signals,
                max_clauses=args.max_gate_clauses,
                beam_width=args.optimizer_beam_width,
            )
            replay_payload["optimization"] = optimization_report.to_dict()

        if args.output_json:
            Path(args.output_json).write_text(
                json.dumps(replay_payload, indent=2), encoding="utf-8"
            )

        if args.json:
            print(json.dumps(replay_payload, indent=2))
        else:
            _print_replay_summary(replay_summary, top=args.top)
            if optimization_report:
                _print_optimization_report(optimization_report)

        return 0

    summary = run_scan(
        symbols,
        provider=provider,
        min_score=args.min_score,
        max_workers=args.max_workers,
        actionable_only=not args.include_watchlist,
        exchange_suffix=args.exchange_suffix,
        technical_gate=technical_gate,
        timeframe=args.timeframe,
    )
    payload = summary.to_dict()

    if args.output_json:
        Path(args.output_json).write_text(
            json.dumps(payload, indent=2), encoding="utf-8"
        )

    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        _print_text_summary(summary, top=args.top)

    return 0


def _build_indicator_features(
    data: pd.DataFrame,
    config: BeastConfig,
) -> dict[str, pd.Series]:
    high = data["High"]
    low = data["Low"]
    close = data["Close"]
    volume = data["Volume"]
    prior_high = high.shift(1)
    prior_low = low.shift(1)
    prior_volume = volume.shift(1)
    prior_turnover = close.shift(1) * prior_volume
    prior_gain_low = (
        close.shift(1).rolling(config.vertical_lookback, min_periods=1).min()
    )
    vertical_gain = ((close - prior_gain_low) / prior_gain_low).clip(lower=0)
    macd = MACD(close, fillna=True)
    adx = ADXIndicator(high, low, close, window=14, fillna=True)
    stoch_rsi = StochRSIIndicator(close, window=14, smooth1=3, smooth2=3, fillna=True)
    bollinger = BollingerBands(close, window=20, window_dev=2, fillna=True)
    long_window = max(90, config.base_lookback * 4)
    features = {
        "vertical_gain": vertical_gain.cummax().fillna(0),
        "sma20": SMAIndicator(close, window=20, fillna=True).sma_indicator(),
        "sma50": SMAIndicator(close, window=50, fillna=True).sma_indicator(),
        "ema10": EMAIndicator(close, window=10, fillna=True).ema_indicator(),
        "ema21": EMAIndicator(close, window=21, fillna=True).ema_indicator(),
        "rsi": RSIIndicator(close, window=14, fillna=True).rsi(),
        "stochrsi_k": stoch_rsi.stochrsi_k(),
        "roc20": ROCIndicator(close, window=20, fillna=True).roc(),
        "roc60": ROCIndicator(close, window=60, fillna=True).roc(),
        "macd_diff": macd.macd_diff(),
        "adx": adx.adx(),
        "adx_pos": adx.adx_pos(),
        "adx_neg": adx.adx_neg(),
        "mfi": MFIIndicator(
            high, low, close, volume, window=14, fillna=True
        ).money_flow_index(),
        "cmf": ChaikinMoneyFlowIndicator(
            high, low, close, volume, window=20, fillna=True
        ).chaikin_money_flow(),
        "obv": OnBalanceVolumeIndicator(close, volume, fillna=True).on_balance_volume(),
        "atr": AverageTrueRange(
            high, low, close, window=14, fillna=True
        ).average_true_range(),
        "bb_width": bollinger.bollinger_wband(),
        "bb_percent_b": bollinger.bollinger_pband(),
        "long_high": high.shift(1).rolling(long_window, min_periods=1).max(),
        "long_low": low.shift(1).rolling(long_window, min_periods=1).min(),
        "base_high": prior_high.rolling(config.base_lookback - 1).max(),
        "base_low": prior_low.rolling(config.base_lookback - 1).min(),
        "recent_high": prior_high.rolling(config.recent_lookback - 1).max(),
        "recent_low": prior_low.rolling(config.recent_lookback - 1).min(),
        "c45_high": prior_high.rolling(config.base_lookback - 1).max(),
        "c45_low": prior_low.rolling(config.base_lookback - 1).min(),
        "c25_high": prior_high.rolling(24).max(),
        "c25_low": prior_low.rolling(24).min(),
        "c12_high": prior_high.rolling(11).max(),
        "c12_low": prior_low.rolling(11).min(),
        "volume_20": prior_volume.rolling(20).mean(),
        "turnover_20": prior_turnover.rolling(20).mean(),
        "recent_base_volume": prior_volume.rolling(10).mean(),
        "prior_base_volume": volume.shift(11).rolling(20).mean(),
        "rolling_breakout_pivot": prior_high.rolling(config.base_lookback).max(),
        "post_peak_drawdown": _rolling_post_peak_drawdown(
            high.tolist(),
            low.tolist(),
            config.base_lookback,
            data.index,
        ),
    }
    return features


def _analyze_history(data: pd.DataFrame, config: BeastConfig) -> BeastSignal:
    data = dataframe_to_ohlcv(data)
    data = data[(data["Close"] > 0) & (data["High"] > 0) & (data["Low"] > 0)]

    if len(data) < config.min_bars:
        return BeastSignal(
            score=0,
            rating="insufficient_data",
            stage="insufficient_data",
            actionable=False,
            reasons=(f"needs at least {config.min_bars} candles",),
            metrics={"candles": len(data)},
        )

    return _analyze_at_index(
        data,
        _build_indicator_features(data, config),
        len(data) - 1,
        config,
    )


def _analyze_at_index(
    data: pd.DataFrame,
    features: dict[str, pd.Series],
    index: int,
    config: BeastConfig,
) -> BeastSignal:
    open_ = data["Open"]
    high = data["High"]
    low = data["Low"]
    close = data["Close"]
    volume = data["Volume"]

    latest_open = float(open_.iloc[index])
    latest_high = float(high.iloc[index])
    latest_low = float(low.iloc[index])
    latest_close = float(close.iloc[index])
    latest_volume = float(volume.iloc[index])

    ma20 = _float_at(features["sma20"], index)
    ma50 = _float_at(features["sma50"], index)
    ema10_now = _float_at(features["ema10"], index)
    ema21_now = _float_at(features["ema21"], index)
    rsi_now = _float_at(features["rsi"], index, 50.0)
    rsi_prior = _float_at(features["rsi"], index - 5, rsi_now)
    stochrsi_now = _float_at(features["stochrsi_k"], index)
    roc20_now = _float_at(features["roc20"], index)
    roc60_now = _float_at(features["roc60"], index)
    macd_now = _float_at(features["macd_diff"], index)
    macd_prior = _float_at(features["macd_diff"], index - 3, macd_now)
    adx_now = _float_at(features["adx"], index)
    adx_pos_now = _float_at(features["adx_pos"], index)
    adx_neg_now = _float_at(features["adx_neg"], index)
    mfi_now = _float_at(features["mfi"], index, 50.0)
    cmf_now = _float_at(features["cmf"], index)
    atr_now = _float_at(features["atr"], index)
    bb_width_now = _float_at(features["bb_width"], index)
    bb_percent_b_now = _float_at(features["bb_percent_b"], index)
    long_high = _float_at(features["long_high"], index)
    long_low = _float_at(features["long_low"], index)

    vertical_end = index + 1 - config.recent_lookback
    vertical_gain = _float_at(features["vertical_gain"], vertical_end - 1)
    base_high = _float_at(features["base_high"], index)
    base_low = _float_at(features["base_low"], index)
    base_range = _range_pct_values(base_high, base_low)
    recent_range = _range_pct_values(
        _float_at(features["recent_high"], index),
        _float_at(features["recent_low"], index),
    )
    c45 = _range_pct_values(
        _float_at(features["c45_high"], index),
        _float_at(features["c45_low"], index),
    )
    c25 = _range_pct_values(
        _float_at(features["c25_high"], index),
        _float_at(features["c25_low"], index),
    )
    c12 = _range_pct_values(
        _float_at(features["c12_high"], index),
        _float_at(features["c12_low"], index),
    )
    base_drawdown = (base_high - base_low) / base_high if base_high else 1.0
    post_peak_drawdown = _float_at(features["post_peak_drawdown"], index, 1.0)
    damaged_base = (
        base_drawdown > config.damaged_drawdown_pct
        or base_range > config.damaged_range_pct
        or post_peak_drawdown > config.damaged_drawdown_pct
    )
    pivot = base_high
    distance_to_pivot = (latest_close - pivot) / pivot if pivot else -1.0
    volume_20 = _float_at(features["volume_20"], index)
    turnover_20 = _float_at(features["turnover_20"], index)
    recent_base_volume = _float_at(features["recent_base_volume"], index)
    prior_base_volume = _float_at(features["prior_base_volume"], index)
    breakout_volume_ratio = latest_volume / volume_20 if volume_20 else 0.0
    stage, bars_since_breakout, breakout_pivot = _breakout_stage_at(
        data, index, config, features
    )
    strong_close = (
        ((latest_close - latest_low) / (latest_high - latest_low)) >= 0.65
        if latest_high > latest_low
        else True
    )
    obv_now = _float_at(features["obv"], index)
    obv_accumulation = obv_now > _float_at(features["obv"], index - 20, obv_now)
    atr_pct = (atr_now / latest_close) * 100.0 if latest_close else 0.0
    long_high_distance_pct = (
        ((long_high - latest_close) / latest_close) * 100.0
        if latest_close and long_high
        else 0.0
    )
    long_low_gain_pct = (
        ((latest_close - long_low) / long_low) * 100.0 if long_low else 0.0
    )
    technical_upside_pct = _technical_upside_pct(latest_close, pivot, base_drawdown)

    score = 0
    reasons: list[str] = []

    if latest_close > ma50 and ema21_now >= ma50 * 0.98:
        score += 1
        reasons.append("price is above the 50-day trend")

    if latest_close > ema10_now > ema21_now:
        score += 1
        reasons.append("short EMAs are stacked upward")

    if vertical_gain >= 0.40:
        score += 3
        reasons.append("prior vertical move shows strong demand")
    elif vertical_gain >= 0.25:
        score += 2
        reasons.append("prior vertical move is present")

    if base_drawdown <= 0.28 and latest_close >= base_low * 1.08:
        score += 1
        reasons.append("base is controlled instead of a crash")

    contracting = c45 > c25 * 1.03 and c25 >= c12 * 0.95 and c12 <= 0.18
    tight = recent_range <= 0.14 and latest_close >= ema21_now * 0.98
    if contracting or tight:
        score += 2
        reasons.append("recent price action is tight and controlled")

    volume_dry_up = recent_base_volume < prior_base_volume * 0.90
    if volume_dry_up:
        score += 1
        reasons.append("base volume dried up before the pivot")

    if stage == "breakout_today":
        score += 2
        reasons.append("price is breaking out now")
    elif stage == "near_breakout":
        score += 1
        reasons.append("price is near the breakout pivot")
    elif stage == "follow_through":
        score += 1
        reasons.append("recent breakout is following through")

    if stage in {"breakout_today", "follow_through", "extended"}:
        if breakout_volume_ratio >= config.min_confirming_volume_ratio:
            score += 1
            reasons.append("breakout volume confirms demand")

    if (
        stage == "follow_through"
        and bars_since_breakout <= config.fast_follow_through_bars
    ):
        if latest_close >= breakout_pivot * 1.05:
            score += 1
            reasons.append("post-breakout move is working quickly")

    if 55 <= rsi_now <= 78 and rsi_now >= rsi_prior:
        score += 1
        reasons.append("RSI confirms improving momentum")

    if roc20_now > 0 and roc60_now > 0:
        score += 1
        reasons.append("multi-period rate of change is positive")

    if 45 <= mfi_now <= 82 and cmf_now > -0.05:
        score += 1
        reasons.append("money-flow indicators support accumulation")

    if macd_now > 0 or macd_now > macd_prior:
        score += 1
        reasons.append("MACD histogram is improving")

    if adx_now >= 18 and adx_pos_now > adx_neg_now:
        score += 1
        reasons.append("ADX direction favors buyers")

    if obv_accumulation:
        score += 1
        reasons.append("OBV shows accumulation")

    if 6 <= technical_upside_pct <= 35:
        score += 1
        reasons.append("measured target leaves practical upside")

    early_entry = (
        stage == "near_breakout"
        and score >= config.early_min_score
        and vertical_gain >= config.early_min_vertical_gain_pct
        and volume_dry_up
        and recent_range <= config.early_max_recent_range_pct
        and base_drawdown <= config.early_max_base_drawdown_pct
        and -config.early_max_below_pivot_pct <= distance_to_pivot
        and distance_to_pivot <= config.early_max_above_pivot_pct
        and latest_close > latest_open
        and strong_close
        and latest_close > ema21_now >= ma50 * 0.98
        and adx_now >= 18
        and adx_pos_now > adx_neg_now
        and macd_now > macd_prior
        and breakout_volume_ratio <= config.early_max_volume_ratio
        and rsi_now >= 55
    )

    if early_entry:
        stage = "early_entry"
        reasons.append("strict early-entry candidate before breakout")

    if damaged_base:
        score = min(score, 5)
        stage = "damaged_base"
        reasons.append("base is too deep to qualify")

    actionable = (
        stage in {"early_entry", "breakout_today", "follow_through"}
        and not damaged_base
    )

    metrics = {
        "candles": index + 1,
        "latest_close": round(latest_close, 4),
        "ma20": round(ma20, 4),
        "ma50": round(ma50, 4),
        "ema10": round(ema10_now, 4),
        "ema21": round(ema21_now, 4),
        "rsi14": round(rsi_now, 2),
        "stochrsi_k": round(stochrsi_now, 4),
        "roc20": round(roc20_now, 2),
        "roc60": round(roc60_now, 2),
        "macd_diff": round(macd_now, 4),
        "adx14": round(adx_now, 2),
        "adx_pos14": round(adx_pos_now, 2),
        "adx_neg14": round(adx_neg_now, 2),
        "mfi14": round(mfi_now, 2),
        "cmf20": round(cmf_now, 4),
        "atr_pct": round(atr_pct, 2),
        "bb_width_pct": round(bb_width_now, 2),
        "bb_percent_b": round(bb_percent_b_now, 4),
        "vertical_gain_pct": round(vertical_gain * 100, 2),
        "long_high_distance_pct": round(long_high_distance_pct, 2),
        "long_low_gain_pct": round(long_low_gain_pct, 2),
        "base_range_pct": round(base_range * 100, 2),
        "recent_range_pct": round(recent_range * 100, 2),
        "base_drawdown_pct": round(base_drawdown * 100, 2),
        "post_peak_drawdown_pct": round(post_peak_drawdown * 100, 2),
        "pivot": round(pivot, 4),
        "distance_to_pivot_pct": round(distance_to_pivot * 100, 2),
        "breakout_volume_ratio": round(breakout_volume_ratio, 2),
        "latest_volume": round(latest_volume, 2),
        "avg_volume_20": round(volume_20, 2),
        "avg_turnover_20": round(turnover_20, 2),
        "bars_since_breakout": bars_since_breakout,
        "technical_upside_pct": round(technical_upside_pct, 2),
    }

    return BeastSignal(
        score=score,
        rating=_rating(score),
        stage=stage,
        actionable=actionable,
        reasons=tuple(reasons),
        metrics=metrics,
    )


def _flatten_single_symbol_columns(data: pd.DataFrame) -> pd.DataFrame:
    for level in range(data.columns.nlevels):
        labels = [str(column[level]) for column in data.columns]
        if all(required in labels for required in OHLCV_COLUMNS):
            output = data.copy()
            output.columns = labels
            return output
    return data


def _signal_with_metric(signal: BeastSignal, key: str, value: Any) -> BeastSignal:
    metrics = dict(signal.metrics)
    metrics[key] = value
    return BeastSignal(
        score=signal.score,
        rating=signal.rating,
        stage=signal.stage,
        actionable=signal.actionable,
        reasons=signal.reasons,
        metrics=metrics,
        validation=signal.validation,
    )


def _breakout_stage(data: pd.DataFrame, config: BeastConfig) -> tuple[str, int, float]:
    return _breakout_stage_at(data, len(data) - 1, config)


def _breakout_stage_at(
    data: pd.DataFrame,
    index: int,
    config: BeastConfig,
    features: dict[str, pd.Series] | None = None,
) -> tuple[str, int, float]:
    close = data["Close"].tolist()
    high = data["High"].tolist()
    latest_close = close[index]
    pivot = max(high[index - config.base_lookback + 1 : index])
    first_breakout_index = None
    first_breakout_pivot = pivot
    start = max(config.base_lookback, index + 1 - config.breakout_scan_bars)

    for scan_index in range(start, index + 1):
        if features is None:
            rolling_pivot = max(high[scan_index - config.base_lookback : scan_index])
        else:
            rolling_pivot = _float_at(features["rolling_breakout_pivot"], scan_index)
        if close[scan_index] >= rolling_pivot * (1.0 + config.breakout_buffer_pct):
            first_breakout_index = scan_index
            first_breakout_pivot = rolling_pivot
            break

    if first_breakout_index is None:
        if latest_close >= pivot * (1.0 - config.near_pivot_pct):
            return "near_breakout", 0, pivot
        return "base", 0, pivot

    bars_since_breakout = index - first_breakout_index
    extension = latest_close / first_breakout_pivot if first_breakout_pivot else 0.0
    if bars_since_breakout == 0:
        return "breakout_today", 0, first_breakout_pivot
    if bars_since_breakout <= config.follow_through_max_bars and extension <= 1.25:
        return "follow_through", bars_since_breakout, first_breakout_pivot
    return "extended", bars_since_breakout, first_breakout_pivot


def _range_pct(data: pd.DataFrame) -> float:
    if data.empty:
        return 1.0

    low = float(data["Low"].min())
    high = float(data["High"].max())
    if low <= 0:
        return 1.0
    return (high - low) / low


def _range_pct_values(high: float, low: float) -> float:
    if high <= 0 or low <= 0:
        return 1.0
    return (high - low) / low


def _window_range_pct(data: pd.DataFrame, window: int) -> float:
    return _range_pct(data.iloc[-window:-1])


def _rolling_post_peak_drawdown(
    highs: list[float],
    lows: list[float],
    window: int,
    index: pd.Index,
) -> pd.Series:
    values: list[float] = []
    for current in range(len(highs)):
        start = max(0, current - window + 1)
        if start >= current:
            values.append(1.0)
            continue

        peak = float(highs[start])
        max_drawdown = 0.0
        for scan in range(start + 1, current):
            if peak > 0:
                max_drawdown = max(max_drawdown, (peak - float(lows[scan])) / peak)
            peak = max(peak, float(highs[scan]))
        values.append(max_drawdown)
    return pd.Series(values, index=index)


def _technical_upside_pct(
    latest_close: float,
    pivot: float,
    base_drawdown: float,
) -> float:
    if latest_close <= 0 or pivot <= 0 or base_drawdown <= 0:
        return 0.0
    measured_target = pivot * (1.0 + base_drawdown)
    return ((measured_target - latest_close) / latest_close) * 100.0


def _last_float(series: pd.Series, default: float = 0.0) -> float:
    if series.empty:
        return default
    value = series.iloc[-1]
    if pd.isna(value):
        return default
    return float(value)


def _float_at(series: pd.Series, index: int, default: float = 0.0) -> float:
    if index < 0 or index >= len(series):
        return default
    value = series.iloc[index]
    if pd.isna(value):
        return default
    return float(value)


def _prior_float(series: pd.Series, bars_back: int, default: float = 0.0) -> float:
    if len(series) <= bars_back:
        return default
    value = series.iloc[-1 - bars_back]
    if pd.isna(value):
        return default
    return float(value)


def _rating(score: int) -> str:
    if score >= 12:
        return "A+"
    if score >= 10:
        return "A"
    if score >= 8:
        return "B"
    return "C"


def _scan_sort_key(item: StockScan) -> tuple[float, float, float, float]:
    metrics = item.signal.metrics
    return (
        float(item.signal.score),
        float(metrics.get("technical_upside_pct", 0.0)),
        float(metrics.get("breakout_volume_ratio", 0.0)),
        -abs(float(metrics.get("distance_to_pivot_pct", 100.0))),
    )


def _avg(values: Iterable[float]) -> float:
    selected = list(values)
    if not selected:
        return 0.0
    return round(sum(selected) / len(selected), 2)


def _pct(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 0.0
    return round((numerator / denominator) * 100.0, 2)


def _replay_stats_by_stage(
    trades: tuple[ReplayTrade, ...]
) -> dict[str, dict[str, Any]]:
    output: dict[str, dict[str, Any]] = {}
    stages = sorted({trade.stage for trade in trades})
    for stage in stages:
        selected = [trade for trade in trades if trade.stage == stage]
        passed = sum(1 for trade in selected if trade.passed)
        output[stage] = {
            "signals": len(selected),
            "passed": passed,
            "failed": len(selected) - passed,
            "accuracy_pct": _pct(passed, len(selected)),
            "avg_max_gain_pct": _avg(trade.max_gain_pct for trade in selected),
            "avg_max_drawdown_pct": _avg(trade.max_drawdown_pct for trade in selected),
            "avg_final_return_pct": _avg(trade.final_return_pct for trade in selected),
        }
    return output


def _technical_gate_value(source: BeastSignal | ReplayTrade, field: str) -> Any:
    if field == "score":
        return source.score
    if field == "stage":
        return source.stage
    if field == "rating":
        return source.rating
    return source.metrics.get(field)


def _compare_gate_value(actual: Any, operator: str, expected: float | str) -> bool:
    if isinstance(expected, str):
        if operator != "==":
            return False
        return str(actual) == expected

    try:
        actual_number = float(actual)
    except (TypeError, ValueError):
        return False

    if operator == ">=":
        return actual_number >= expected
    if operator == "<=":
        return actual_number <= expected
    if operator == ">":
        return actual_number > expected
    if operator == "<":
        return actual_number < expected
    if operator == "==":
        return actual_number == expected
    return False


def _trades_to_optimizer_frame(trades: tuple[ReplayTrade, ...]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for trade in trades:
        row: dict[str, Any] = {
            "signal_date": trade.signal_date,
            "passed": bool(trade.passed),
            "stage": trade.stage,
            "rating": trade.rating,
            "score": trade.score,
        }
        for field in TECHNICAL_METRIC_FIELDS:
            row[field] = trade.metrics.get(field)
        rows.append(row)

    frame = pd.DataFrame(rows)
    if frame.empty:
        return frame

    frame["signal_date"] = pd.to_datetime(frame["signal_date"], errors="coerce")
    frame = frame.dropna(subset=["signal_date"]).copy()
    for field in OPTIMIZER_NUMERIC_FIELDS:
        if field in frame.columns:
            frame[field] = pd.to_numeric(frame[field], errors="coerce")
    frame["passed"] = frame["passed"].astype(bool)
    return frame


def _resolve_optimizer_split_date(
    frame: pd.DataFrame,
    split_date: str | pd.Timestamp | None,
) -> pd.Timestamp:
    if split_date is not None:
        return pd.Timestamp(split_date).normalize()

    ordered_dates = frame["signal_date"].sort_values().reset_index(drop=True)
    split_index = min(
        len(ordered_dates) - 1,
        max(1, int(len(ordered_dates) * 0.80)),
    )
    return pd.Timestamp(ordered_dates.iloc[split_index]).normalize()


def _build_optimizer_clauses(
    frame: pd.DataFrame,
    train_mask: pd.Series,
) -> tuple[TechnicalGateClause, ...]:
    train = frame[train_mask]
    clauses: list[TechnicalGateClause] = []

    for stage in sorted(value for value in train["stage"].dropna().unique() if value):
        clauses.append(TechnicalGateClause("stage", "==", str(stage)))

    score_values = sorted(
        {
            int(value)
            for value in train["score"].dropna().unique()
            if pd.notna(value)
        }
    )
    for value in score_values:
        clauses.append(TechnicalGateClause("score", ">=", float(value)))

    for field in OPTIMIZER_NUMERIC_FIELDS:
        if field == "score" or field not in train.columns:
            continue

        values = train[field].dropna()
        if values.empty:
            continue

        thresholds = sorted(
            {
                _round_gate_threshold(float(values.quantile(quantile)))
                for quantile in OPTIMIZER_QUANTILES
                if pd.notna(values.quantile(quantile))
            }
        )
        for threshold in thresholds:
            clauses.append(TechnicalGateClause(field, "<=", threshold))
            clauses.append(TechnicalGateClause(field, ">=", threshold))

    return tuple(clauses)


def _round_gate_threshold(value: float) -> float:
    if abs(value) >= 100:
        return round(value, 1)
    return round(value, 2)


def _is_redundant_clause(
    existing_clauses: tuple[TechnicalGateClause, ...],
    clause: TechnicalGateClause,
) -> bool:
    if clause in existing_clauses:
        return True

    for existing in existing_clauses:
        if existing.field != clause.field:
            continue
        if existing.field in {"stage", "rating"}:
            return True
        if existing.operator == clause.operator:
            return True
        if existing.operator in {">=", ">"} and clause.operator in {">=", ">"}:
            return True
        if existing.operator in {"<=", "<"} and clause.operator in {"<=", "<"}:
            return True

    return False


def _clause_mask(frame: pd.DataFrame, clause: TechnicalGateClause) -> pd.Series:
    if clause.field not in frame.columns:
        return pd.Series(False, index=frame.index)

    values = frame[clause.field]
    if isinstance(clause.value, str):
        if clause.operator != "==":
            return pd.Series(False, index=frame.index)
        return values.astype(str) == clause.value

    numeric_values = pd.to_numeric(values, errors="coerce")
    if clause.operator == ">=":
        return numeric_values >= clause.value
    if clause.operator == "<=":
        return numeric_values <= clause.value
    if clause.operator == ">":
        return numeric_values > clause.value
    if clause.operator == "<":
        return numeric_values < clause.value
    if clause.operator == "==":
        return numeric_values == clause.value
    return pd.Series(False, index=frame.index)


def _gate_candidate_from_mask(
    frame: pd.DataFrame,
    mask: pd.Series,
    clauses: tuple[TechnicalGateClause, ...],
    train_mask: pd.Series,
    validation_mask: pd.Series,
) -> ReplayGateCandidate:
    selected = mask.fillna(False)
    total_signals, total_passed, total_accuracy = _optimizer_stats(
        frame, selected
    )
    train_signals, train_passed, train_accuracy = _optimizer_stats(
        frame, selected & train_mask
    )
    validation_signals, validation_passed, validation_accuracy = _optimizer_stats(
        frame, selected & validation_mask
    )
    return ReplayGateCandidate(
        clauses=clauses,
        total_signals=total_signals,
        total_passed=total_passed,
        total_accuracy_pct=total_accuracy,
        train_signals=train_signals,
        train_passed=train_passed,
        train_accuracy_pct=train_accuracy,
        validation_signals=validation_signals,
        validation_passed=validation_passed,
        validation_accuracy_pct=validation_accuracy,
    )


def _optimizer_stats(frame: pd.DataFrame, mask: pd.Series) -> tuple[int, int, float]:
    selected = frame[mask]
    signals = len(selected)
    passed = int(selected["passed"].sum()) if signals else 0
    return signals, passed, _pct(passed, signals)


def _optimizer_train_rank(candidate: ReplayGateCandidate) -> tuple[float, int, float]:
    return (
        candidate.train_accuracy_pct,
        candidate.train_signals,
        candidate.total_accuracy_pct,
    )


def _optimizer_validation_rank(
    candidate: ReplayGateCandidate,
) -> tuple[float, float, float, int, int]:
    return (
        min(candidate.train_accuracy_pct, candidate.validation_accuracy_pct),
        candidate.validation_accuracy_pct,
        candidate.train_accuracy_pct,
        candidate.validation_signals,
        candidate.total_signals,
    )


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the TA beast stock scanner.")
    parser.add_argument(
        "--symbols", nargs="*", help="Symbols to scan instead of all NSE stocks."
    )
    parser.add_argument("--symbols-file", help="File containing symbols to scan.")
    parser.add_argument(
        "--exchange-suffix", default=".NS", help="Yahoo suffix for raw symbols."
    )
    parser.add_argument("--period", default="2y", help="Yahoo history period.")
    parser.add_argument("--interval", default="1d", help="Yahoo history interval.")
    parser.add_argument(
        "--timeframe",
        default="daily",
        choices=["daily", "weekly", "monthly"],
        help="Bar timeframe to scan or replay after Yahoo data is loaded.",
    )
    parser.add_argument(
        "--min-score", type=int, default=9, help="Minimum signal score."
    )
    parser.add_argument(
        "--max-workers", type=int, default=None, help="Parallel Yahoo workers."
    )
    parser.add_argument(
        "--top", type=int, default=25, help="Rows to print in text mode."
    )
    parser.add_argument("--json", action="store_true", help="Print full JSON output.")
    parser.add_argument("--output-json", help="Write full JSON output to this path.")
    parser.add_argument(
        "--technical-gate",
        action="append",
        default=[],
        help=(
            "Pure technical filter to apply, for example rsi14<=55 or "
            "stage==early_entry. May be supplied more than once."
        ),
    )
    parser.add_argument(
        "--replay",
        action="store_true",
        help="Replay historical signals and print accuracy instead of live matches.",
    )
    parser.add_argument(
        "--replay-input-json",
        help="Read an existing replay JSON instead of downloading market history.",
    )
    parser.add_argument(
        "--optimize-accuracy",
        action="store_true",
        help="Search pure technical gates and validate the target accuracy.",
    )
    parser.add_argument(
        "--target-accuracy-pct",
        type=float,
        default=80.0,
        help="Replay optimizer target accuracy.",
    )
    parser.add_argument(
        "--split-date",
        help="Chronological validation split date. Earlier rows train the gate.",
    )
    parser.add_argument(
        "--min-train-signals",
        type=int,
        default=30,
        help="Minimum train-sample signals required for optimizer gates.",
    )
    parser.add_argument(
        "--min-validation-signals",
        type=int,
        default=10,
        help="Minimum holdout signals required for optimizer gates.",
    )
    parser.add_argument(
        "--max-gate-clauses",
        type=int,
        default=3,
        help="Maximum clauses in an optimizer-generated technical gate.",
    )
    parser.add_argument(
        "--optimizer-beam-width",
        type=int,
        default=80,
        help="Number of candidate gates retained per optimizer depth.",
    )
    parser.add_argument(
        "--lookahead-bars",
        type=int,
        default=20,
        help="Replay forward validation window.",
    )
    parser.add_argument(
        "--min-gain-pct",
        type=float,
        default=5.0,
        help="Replay pass threshold for forward upside.",
    )
    parser.add_argument(
        "--max-drawdown-pct",
        type=float,
        default=8.0,
        help="Replay max accepted forward drawdown.",
    )
    parser.add_argument(
        "--cooldown-bars",
        type=int,
        default=10,
        help="Bars to skip after a replay signal to avoid duplicate entries.",
    )
    parser.add_argument(
        "--stride",
        type=int,
        default=1,
        help="Replay every Nth eligible bar.",
    )
    parser.add_argument(
        "--replay-stages",
        nargs="*",
        default=["early_entry", "breakout_today", "follow_through"],
        help="Stages to include in replay accuracy.",
    )
    parser.add_argument(
        "--max-signals-per-symbol",
        type=int,
        default=None,
        help="Optional cap on replay signals per symbol.",
    )
    parser.add_argument(
        "--include-watchlist",
        action="store_true",
        help="Include non-actionable rows above the score threshold.",
    )
    parser.add_argument(
        "--validate-symbols",
        action="store_true",
        help="Use nsetools symbol validation when available.",
    )
    return parser.parse_args(argv)


def _resolve_cli_symbols(args: argparse.Namespace) -> list[str] | None:
    symbols: list[str] = []
    if args.symbols:
        symbols.extend(args.symbols)
    if args.symbols_file:
        symbols.extend(load_symbols_file(args.symbols_file, args.exchange_suffix))
    if not symbols:
        return None
    return unique_yahoo_symbols(symbols, exchange_suffix=args.exchange_suffix)


def _print_text_summary(summary: ScanSummary, top: int) -> None:
    print(f"requested={summary.total_requested}")
    print(f"with_data={summary.total_with_data}")
    print(f"matches={len(summary.matches)}")
    print(f"errors={len(summary.errors)}")

    if not summary.matches:
        return

    print("")
    print("symbol score rating stage close pivot dist% upside% rsi adx volx")
    for match in summary.matches[:top]:
        metrics = match.signal.metrics
        print(
            "{symbol} {score} {rating} {stage} {close} {pivot} {dist} {upside} {rsi} {adx} {volx}".format(
                symbol=match.symbol,
                score=match.signal.score,
                rating=match.signal.rating,
                stage=match.signal.stage,
                close=metrics.get("latest_close", ""),
                pivot=metrics.get("pivot", ""),
                dist=metrics.get("distance_to_pivot_pct", ""),
                upside=metrics.get("technical_upside_pct", ""),
                rsi=metrics.get("rsi14", ""),
                adx=metrics.get("adx14", ""),
                volx=metrics.get("breakout_volume_ratio", ""),
            )
        )


def _print_replay_summary(summary: ReplaySummary, top: int) -> None:
    payload = summary.to_dict()
    print(f"requested={summary.total_requested}")
    print(f"with_data={summary.total_with_data}")
    print(f"signals={payload['total_signals']}")
    print(f"passed={payload['passed']}")
    print(f"failed={payload['failed']}")
    print(f"accuracy_pct={payload['accuracy_pct']}")
    print(f"avg_max_gain_pct={payload['avg_max_gain_pct']}")
    print(f"avg_max_drawdown_pct={payload['avg_max_drawdown_pct']}")
    print(f"avg_final_return_pct={payload['avg_final_return_pct']}")
    print(f"errors={payload['errors']}")

    if payload["by_stage"]:
        print("")
        print("stage signals passed accuracy% avg_gain% avg_dd% avg_final%")
        for stage, stats in payload["by_stage"].items():
            print(
                "{stage} {signals} {passed} {accuracy} {gain} {dd} {final}".format(
                    stage=stage,
                    signals=stats["signals"],
                    passed=stats["passed"],
                    accuracy=stats["accuracy_pct"],
                    gain=stats["avg_max_gain_pct"],
                    dd=stats["avg_max_drawdown_pct"],
                    final=stats["avg_final_return_pct"],
                )
            )

    if not summary.trades:
        return

    print("")
    print("symbol date stage score entry gain% drawdown% final% passed")
    for trade in summary.trades[:top]:
        print(
            "{symbol} {date} {stage} {score} {entry} {gain} {drawdown} {final} {passed}".format(
                symbol=trade.symbol,
                date=trade.signal_date,
                stage=trade.stage,
                score=trade.score,
                entry=trade.entry_price,
                gain=trade.max_gain_pct,
                drawdown=trade.max_drawdown_pct,
                final=trade.final_return_pct,
                passed=trade.passed,
            )
        )


def _print_optimization_report(report: ReplayOptimizationReport) -> None:
    baseline = report.baseline
    best = report.best_candidate

    print("")
    print(
        "accuracy_optimization target={target}% achieved={achieved} split_date={split}".format(
            target=report.target_accuracy_pct,
            achieved=str(report.achieved).lower(),
            split=report.split_date,
        )
    )
    print(
        "baseline full={full}% train={train}% validation={validation}%".format(
            full=baseline.total_accuracy_pct,
            train=baseline.train_accuracy_pct,
            validation=baseline.validation_accuracy_pct,
        )
    )
    print(f"evaluated_candidates={report.evaluated_candidates}")

    if best is None:
        print("best_gate=none")
        return

    gate_text = " AND ".join(clause.to_text() for clause in best.clauses)
    print(f"best_gate={gate_text}")
    print(
        "best full={full}%/{full_n} train={train}%/{train_n} validation={validation}%/{validation_n}".format(
            full=best.total_accuracy_pct,
            full_n=best.total_signals,
            train=best.train_accuracy_pct,
            train_n=best.train_signals,
            validation=best.validation_accuracy_pct,
            validation_n=best.validation_signals,
        )
    )


if __name__ == "__main__":
    raise SystemExit(main())
