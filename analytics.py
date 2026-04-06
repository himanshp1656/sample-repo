from __future__ import annotations
import math
from typing import List, Optional
from errors import NotFoundError

# Module-level metrics store
METRICS: dict[str, list[float]] = {}
_metric_labels: dict[str, str] = {}


def compute_mean(values: list[float]) -> float:
    if not values:
        raise ValueError("Cannot compute mean of empty list")
    return sum(values) / len(values)


def compute_median(values: list[float]) -> float:
    if not values:
        raise ValueError("Cannot compute median of empty list")
    sorted_vals = sorted(values)
    n = len(sorted_vals)
    mid = n // 2
    if n % 2 == 0:
        return (sorted_vals[mid - 1] + sorted_vals[mid]) / 2
    return sorted_vals[mid]


def compute_std_dev(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    mean = compute_mean(values)
    variance = sum((x - mean) ** 2 for x in values) / (len(values) - 1)
    return math.sqrt(variance)


def compute_percentile(values: list[float], p: int) -> float:
    if not (0 <= p <= 100):
        raise ValueError(f"Percentile must be 0-100, got {p}")
    if not values:
        raise ValueError("Cannot compute percentile of empty list")
    sorted_vals = sorted(values)
    idx = (p / 100) * (len(sorted_vals) - 1)
    lower = int(idx)
    upper = lower + 1
    if upper >= len(sorted_vals):
        return sorted_vals[-1]
    frac = idx - lower
    return sorted_vals[lower] * (1 - frac) + sorted_vals[upper] * frac


def summarize(values: list[float]) -> dict:
    if not values:
        return {"count": 0, "min": None, "max": None, "mean": None, "median": None, "std_dev": None}
    return {
        "count": len(values),
        "min": min(values),
        "max": max(values),
        "mean": round(compute_mean(values), 4),
        "median": compute_median(values),
        "std_dev": round(compute_std_dev(values), 4),
        "p25": compute_percentile(values, 25),
        "p75": compute_percentile(values, 75),
        "p95": compute_percentile(values, 95),
    }


def track_metric(name: str, value: float, label: str = "") -> None:
    METRICS.setdefault(name, []).append(value)
    if label:
        _metric_labels[name] = label


def get_metric_stats(name: str) -> dict:
    values = METRICS.get(name)
    if values is None:
        raise NotFoundError("Metric", name)
    stats = summarize(values)
    stats["name"] = name
    stats["label"] = _metric_labels.get(name, name)
    return stats


def compare_metrics(name_a: str, name_b: str) -> dict:
    stats_a = get_metric_stats(name_a)
    stats_b = get_metric_stats(name_b)
    mean_a = stats_a["mean"] or 0
    mean_b = stats_b["mean"] or 0
    delta = mean_b - mean_a
    pct_change = (delta / mean_a * 100) if mean_a != 0 else None
    return {
        "metric_a": stats_a,
        "metric_b": stats_b,
        "mean_delta": round(delta, 4),
        "pct_change": round(pct_change, 2) if pct_change is not None else None,
        "winner": name_b if delta > 0 else name_a if delta < 0 else "tie",
    }


def rolling_average(name: str, window: int = 10) -> Optional[float]:
    values = METRICS.get(name, [])
    if not values:
        return None
    window_vals = values[-window:]
    return compute_mean(window_vals)
