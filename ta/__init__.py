"""It is a Technical Analysis library useful to do feature
engineering from financial time series datasets (Open,
Close, High, Low, Volume). It is built on Pandas and Numpy.

.. moduleauthor:: Dario Lopez Padial (Bukosabino)

"""
from importlib import import_module

from ta.wrapper import (
    add_all_ta_features,
    add_momentum_ta,
    add_others_ta,
    add_trend_ta,
    add_volatility_ta,
    add_volume_ta,
)

__all__ = [
    "BeastConfig",
    "ReplayConfig",
    "ReplayOptimizationReport",
    "TechnicalGateClause",
    "YahooDataProvider",
    "add_all_ta_features",
    "add_momentum_ta",
    "add_others_ta",
    "add_trend_ta",
    "add_volatility_ta",
    "add_volume_ta",
    "analyze_beast_setup",
    "optimize_beast_replay_quality_gate",
    "parse_beast_technical_gate",
    "run_beast_replay",
    "run_beast_scan",
]


def __getattr__(name):
    if name in {
        "BeastConfig",
        "ReplayConfig",
        "ReplayOptimizationReport",
        "TechnicalGateClause",
        "YahooDataProvider",
        "analyze_beast_setup",
    }:
        beast_scanner = import_module("ta.beast_scanner")
        return getattr(beast_scanner, name)
    if name == "optimize_beast_replay_quality_gate":
        beast_scanner = import_module("ta.beast_scanner")
        return beast_scanner.optimize_replay_quality_gate
    if name == "parse_beast_technical_gate":
        beast_scanner = import_module("ta.beast_scanner")
        return beast_scanner.parse_technical_gate
    if name == "run_beast_scan":
        beast_scanner = import_module("ta.beast_scanner")
        return beast_scanner.run_scan
    if name == "run_beast_replay":
        beast_scanner = import_module("ta.beast_scanner")
        return beast_scanner.run_replay
    raise AttributeError(f"module 'ta' has no attribute {name!r}")
