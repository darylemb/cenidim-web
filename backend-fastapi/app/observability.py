"""Lightweight Prometheus-compatible metrics.

We hand-roll a tiny registry rather than depend on
``prometheus_client`` because:
  1. Our metrics surface is small (HTTP histogram + a few counters).
  2. We don't need process collectors / GC stats / etc.
  3. Zero external deps keeps the docker image lean.

The ``/metrics`` endpoint exposes the registry in the standard
text exposition format so Prometheus (or any compatible scraper)
can ingest it.
"""
from __future__ import annotations

import threading
import time
from collections import defaultdict
from typing import Any


class Counter:
    """Monotonic counter with optional label values."""

    __slots__ = ("_name", "_help", "_values", "_lock")

    def __init__(self, name: str, help_: str) -> None:
        self._name = name
        self._help = help_
        self._values: dict[tuple[tuple[str, str], ...], float] = defaultdict(float)
        self._lock = threading.Lock()

    def inc(self, amount: float = 1.0, **labels: str) -> None:
        key = tuple(sorted(labels.items()))
        with self._lock:
            self._values[key] += amount

    def render(self) -> str:
        lines = [f"# HELP {self._name} {self._help}", f"# TYPE {self._name} counter"]
        with self._lock:
            items = list(self._values.items())
        if not items:
            lines.append(f"{self._name} 0")
            return "\n".join(lines) + "\n"
        for labels, value in sorted(items):
            if labels:
                rendered = ",".join(f'{k}="{v}"' for k, v in labels)
                lines.append(f"{self._name}{{{rendered}}} {value}")
            else:
                lines.append(f"{self._name} {value}")
        return "\n".join(lines) + "\n"


class Histogram:
    """Fixed-bucket histogram (no labels; one series per bucket)."""

    __slots__ = ("_name", "_help", "_buckets", "_counts", "_sum", "_count", "_lock")

    DEFAULT_BUCKETS = (
        0.005,
        0.01,
        0.025,
        0.05,
        0.1,
        0.25,
        0.5,
        1.0,
        2.5,
        5.0,
        10.0,
    )

    def __init__(
        self,
        name: str,
        help_: str,
        buckets: tuple[float, ...] = DEFAULT_BUCKETS,
    ) -> None:
        self._name = name
        self._help = help_
        self._buckets = buckets
        self._counts: dict[float, int] = {b: 0 for b in buckets}
        self._counts[float("inf")] = 0
        self._sum = 0.0
        self._count = 0
        self._lock = threading.Lock()

    def observe(self, value: float) -> None:
        with self._lock:
            for boundary in self._buckets:
                if value <= boundary:
                    self._counts[boundary] += 1
            self._counts[float("inf")] += 1
            self._sum += value
            self._count += 1

    def render(self) -> str:
        lines = [f"# HELP {self._name} {self._help}", f"# TYPE {self._name} histogram"]
        with self._lock:
            items = list(self._counts.items())
            total = self._count
            total_sum = self._sum
        for boundary, count in items:
            label = "+Inf" if boundary == float("inf") else str(boundary)
            lines.append(f'{self._name}_bucket{{le="{label}"}} {count}')
        lines.append(f"{self._name}_sum {total_sum}")
        lines.append(f"{self._name}_count {total}")
        return "\n".join(lines) + "\n"


class Registry:
    """In-process metric registry. One instance per app is fine."""

    def __init__(self) -> None:
        self._counters: dict[str, Counter] = {}
        self._histograms: dict[str, Histogram] = {}
        self._lock = threading.Lock()

    def counter(self, name: str, help_: str) -> Counter:
        with self._lock:
            if name not in self._counters:
                self._counters[name] = Counter(name, help_)
            return self._counters[name]

    def histogram(self, name: str, help_: str, **kwargs: Any) -> Histogram:
        with self._lock:
            if name not in self._histograms:
                self._histograms[name] = Histogram(name, help_, **kwargs)
            return self._histograms[name]

    def render(self) -> str:
        parts: list[str] = []
        with self._lock:
            counters = list(self._counters.values())
            histograms = list(self._histograms.values())
        for c in counters:
            parts.append(c.render())
        for h in histograms:
            parts.append(h.render())
        return "".join(parts)


# Module-level singleton; FastAPI middleware imports this directly.
REGISTRY = Registry()

# Default metrics; re-use the singleton via REGISTRY.counter(...) at
# import time so the registry always has them.
HTTP_REQUESTS = REGISTRY.counter(
    "cenidim_http_requests_total",
    "Total HTTP requests served, labelled by method/path/status.",
)
HTTP_LATENCY = REGISTRY.histogram(
    "cenidim_http_request_duration_seconds",
    "HTTP request latency in seconds.",
)
HTTP_5XX = REGISTRY.counter(
    "cenidim_http_5xx_total",
    "Total 5xx responses emitted.",
)
HTTP_4XX = REGISTRY.counter(
    "cenidim_http_4xx_total",
    "Total 4xx responses emitted.",
)


def timed() -> float:
    """Return a high-resolution monotonic clock suitable for latency."""
    return time.perf_counter()


__all__ = [
    "Counter",
    "Histogram",
    "REGISTRY",
    "HTTP_REQUESTS",
    "HTTP_LATENCY",
    "HTTP_5XX",
    "HTTP_4XX",
    "timed",
]
