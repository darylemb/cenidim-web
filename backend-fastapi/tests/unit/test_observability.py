"""Unit tests for app.observability: Counter / Histogram / Registry."""
from __future__ import annotations

from app.observability import (
    HTTP_4XX,
    HTTP_5XX,
    HTTP_LATENCY,
    HTTP_REQUESTS,
    REGISTRY,
    Counter,
    Histogram,
    Registry,
)


def test_counter_increments_and_labels():
    c = Counter("test_counter_total", "A test counter.")
    c.inc(method="GET", path="/foo")
    c.inc(amount=2.0, method="GET", path="/foo")
    c.inc(method="POST", path="/foo")
    rendered = c.render()
    assert "# TYPE test_counter_total counter" in rendered
    assert 'method="GET",path="/foo"} 3.0' in rendered
    assert 'method="POST",path="/foo"} 1.0' in rendered


def test_counter_empty_renders_zero():
    c = Counter("empty_total", "Empty.")
    assert "empty_total 0" in c.render()


def test_histogram_observe_and_buckets():
    h = Histogram("test_hist", "Test histogram.")
    h.observe(0.001)  # first bucket (0.005)
    h.observe(0.02)  # third bucket (0.025)
    h.observe(100.0)  # +Inf bucket
    rendered = h.render()
    assert "# TYPE test_hist histogram" in rendered
    assert 'le="0.005"} 1' in rendered
    assert 'le="0.025"} 2' in rendered
    assert 'le="+Inf"} 3' in rendered
    assert "test_hist_sum 100.021" in rendered
    assert "test_hist_count 3" in rendered


def test_registry_returns_same_instance():
    r = Registry()
    a = r.counter("foo_total", "Foo")
    b = r.counter("foo_total", "Foo")
    assert a is b
    h = r.histogram("bar_seconds", "Bar.")
    h2 = r.histogram("bar_seconds", "Bar.")
    assert h is h2


def test_registry_render_includes_all_metrics():
    r = Registry()
    c = r.counter("c_total", "C")
    h = r.histogram("h_seconds", "H")
    c.inc()
    h.observe(0.1)
    rendered = r.render()
    assert "c_total" in rendered
    assert "h_seconds" in rendered


def test_module_level_singleton_exposes_default_metrics():
    """The metrics middleware reads from these by name; verify the
    module-level singletons exist and accept inc / observe.
    """
    HTTP_REQUESTS.inc(method="GET", path="/foo", status="200")
    HTTP_4XX.inc(method="GET", path="/foo")
    HTTP_5XX.inc(method="GET", path="/foo")
    HTTP_LATENCY.observe(0.05)
    rendered = REGISTRY.render()
    assert "cenidim_http_requests_total" in rendered
    assert "cenidim_http_request_duration_seconds" in rendered
    assert "cenidim_http_4xx_total" in rendered
    assert "cenidim_http_5xx_total" in rendered


def test_metrics_endpoint_format_is_prometheus_compatible():
    """The /metrics text format must match Prometheus 0.0.4."""
    rendered = REGISTRY.render()
    # Every metric block starts with # HELP and # TYPE comments.
    for name in (
        "cenidim_http_requests_total",
        "cenidim_http_request_duration_seconds",
        "cenidim_http_4xx_total",
        "cenidim_http_5xx_total",
    ):
        assert f"# HELP {name}" in rendered, f"missing HELP for {name}"
        assert f"# TYPE {name}" in rendered, f"missing TYPE for {name}"
    # Histogram must expose _bucket, _sum, _count.
    assert "cenidim_http_request_duration_seconds_bucket" in rendered
    assert "cenidim_http_request_duration_seconds_sum" in rendered
    assert "cenidim_http_request_duration_seconds_count" in rendered
