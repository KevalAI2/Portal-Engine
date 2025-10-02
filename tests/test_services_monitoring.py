"""
Tests for monitoring and metrics collection service
"""
import pytest
import asyncio
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock

from app.services.monitoring import (
    MetricType, TraceStatus, Metric, TraceSpan, MetricsCollector,
    DistributedTracer, MonitoringService, monitoring_service
)


class TestMetricType:
    """Test MetricType enum"""
    
    def test_metric_type_values(self):
        """Test metric type enum values"""
        assert MetricType.COUNTER == "counter"
        assert MetricType.GAUGE == "gauge"
        assert MetricType.HISTOGRAM == "histogram"
        assert MetricType.SUMMARY == "summary"


class TestTraceStatus:
    """Test TraceStatus enum"""
    
    def test_trace_status_values(self):
        """Test trace status enum values"""
        assert TraceStatus.SUCCESS == "success"
        assert TraceStatus.ERROR == "error"
        assert TraceStatus.TIMEOUT == "timeout"
        assert TraceStatus.CANCELLED == "cancelled"


class TestMetric:
    """Test Metric dataclass"""
    
    def test_metric_creation(self):
        """Test metric creation"""
        now = datetime.now()
        metric = Metric(
            name="test_metric",
            value=42.0,
            metric_type=MetricType.COUNTER,
            labels={"env": "test"},
            timestamp=now,
            description="Test metric"
        )
        
        assert metric.name == "test_metric"
        assert metric.value == 42.0
        assert metric.metric_type == MetricType.COUNTER
        assert metric.labels == {"env": "test"}
        assert metric.timestamp == now
        assert metric.description == "Test metric"
    
    def test_metric_defaults(self):
        """Test metric with default values"""
        metric = Metric(
            name="test_metric",
            value=42.0,
            metric_type=MetricType.COUNTER
        )
        
        assert metric.labels == {}
        assert isinstance(metric.timestamp, datetime)
        assert metric.description == ""


class TestTraceSpan:
    """Test TraceSpan dataclass"""
    
    def test_trace_span_creation(self):
        """Test trace span creation"""
        now = datetime.now()
        span = TraceSpan(
            trace_id="trace_123",
            span_id="span_456",
            parent_span_id="parent_789",
            operation_name="test_operation",
            start_time=now,
            end_time=now + timedelta(seconds=1),
            duration_ms=1000.0,
            status=TraceStatus.SUCCESS,
            tags={"key": "value"},
            logs=[{"message": "test log"}],
            error="test error"
        )
        
        assert span.trace_id == "trace_123"
        assert span.span_id == "span_456"
        assert span.parent_span_id == "parent_789"
        assert span.operation_name == "test_operation"
        assert span.start_time == now
        assert span.end_time == now + timedelta(seconds=1)
        assert span.duration_ms == 1000.0
        assert span.status == TraceStatus.SUCCESS
        assert span.tags == {"key": "value"}
        assert span.logs == [{"message": "test log"}]
        assert span.error == "test error"
    
    def test_trace_span_defaults(self):
        """Test trace span with default values"""
        span = TraceSpan(
            trace_id="trace_123",
            span_id="span_456"
        )
        
        assert span.parent_span_id is None
        assert span.operation_name == ""
        assert isinstance(span.start_time, datetime)
        assert span.end_time is None
        assert span.duration_ms is None
        assert span.status == TraceStatus.SUCCESS
        assert span.tags == {}
        assert span.logs == []
        assert span.error is None


class TestMetricsCollector:
    """Test MetricsCollector class"""
    
    @pytest.fixture
    def collector(self):
        """Create MetricsCollector instance"""
        return MetricsCollector()
    
    def test_collector_initialization(self, collector):
        """Test collector initialization"""
        assert isinstance(collector.metrics, dict)
        assert isinstance(collector.counters, dict)
        assert isinstance(collector.gauges, dict)
        assert isinstance(collector.histograms, dict)
        assert isinstance(collector.summaries, dict)
    
    def test_increment_counter(self, collector):
        """Test counter increment"""
        collector.increment_counter("test_counter", 5.0, {"env": "test"})
        
        assert collector.counters["test_counter{env=test}"] == 5.0
        assert "test_counter" in collector.metrics
        assert len(collector.metrics["test_counter"]) == 1
        
        metric = collector.metrics["test_counter"][0]
        assert metric.name == "test_counter"
        assert metric.value == 5.0
        assert metric.metric_type == MetricType.COUNTER
        assert metric.labels == {"env": "test"}
    
    def test_increment_counter_default_value(self, collector):
        """Test counter increment with default value"""
        collector.increment_counter("test_counter")
        
        assert collector.counters["test_counter"] == 1.0
    
    def test_set_gauge(self, collector):
        """Test gauge setting"""
        collector.set_gauge("test_gauge", 42.0, {"env": "test"})
        
        assert collector.gauges["test_gauge{env=test}"] == 42.0
        assert "test_gauge" in collector.metrics
        
        metric = collector.metrics["test_gauge"][0]
        assert metric.name == "test_gauge"
        assert metric.value == 42.0
        assert metric.metric_type == MetricType.GAUGE
    
    def test_observe_histogram(self, collector):
        """Test histogram observation"""
        collector.observe_histogram("test_histogram", 1.5, {"env": "test"})
        collector.observe_histogram("test_histogram", 2.5, {"env": "test"})
        
        assert "test_histogram{env=test}" in collector.histograms
        assert collector.histograms["test_histogram{env=test}"] == [1.5, 2.5]
        assert "test_histogram" in collector.metrics
        assert len(collector.metrics["test_histogram"]) == 2
    
    def test_observe_summary(self, collector):
        """Test summary observation"""
        collector.observe_summary("test_summary", 10.0, {"env": "test"})
        collector.observe_summary("test_summary", 20.0, {"env": "test"})
        
        assert "test_summary{env=test}" in collector.summaries
        summary = collector.summaries["test_summary{env=test}"]
        assert summary["count"] == 2
        assert summary["sum"] == 30.0
        assert summary["min"] == 10.0
        assert summary["max"] == 20.0
        assert "test_summary" in collector.metrics
        assert len(collector.metrics["test_summary"]) == 2
    
    def test_get_metric_key(self, collector):
        """Test metric key generation"""
        key1 = collector._get_metric_key("test_metric", {"a": "1", "b": "2"})
        key2 = collector._get_metric_key("test_metric", {"b": "2", "a": "1"})
        key3 = collector._get_metric_key("test_metric", {})
        
        assert key1 == "test_metric{a=1,b=2}"
        assert key1 == key2  # Should be consistent regardless of order
        assert key3 == "test_metric"
    
    def test_get_metrics(self, collector):
        """Test getting metrics"""
        collector.increment_counter("counter1")
        collector.set_gauge("gauge1", 10.0)
        
        all_metrics = collector.get_metrics()
        assert "counter1" in all_metrics
        assert "gauge1" in all_metrics
        
        counter_metrics = collector.get_metrics("counter1")
        assert "counter1" in counter_metrics
        assert "gauge1" not in counter_metrics
    
    def test_get_metric_summary(self, collector):
        """Test getting metric summary"""
        collector.increment_counter("counter1", 5.0)
        collector.set_gauge("gauge1", 10.0)
        collector.observe_histogram("hist1", 1.0)
        collector.observe_histogram("hist1", 2.0)
        collector.observe_summary("sum1", 5.0)
        
        summary = collector.get_metric_summary()
        
        assert "counters" in summary
        assert "gauges" in summary
        assert "histograms" in summary
        assert "summaries" in summary
        
        assert summary["counters"]["counter1"] == 5.0
        assert summary["gauges"]["gauge1"] == 10.0
        assert "hist1" in summary["histograms"]
        assert "sum1" in summary["summaries"]


class TestDistributedTracer:
    """Test DistributedTracer class"""
    
    @pytest.fixture
    def tracer(self):
        """Create DistributedTracer instance"""
        return DistributedTracer()
    
    def test_tracer_initialization(self, tracer):
        """Test tracer initialization"""
        assert isinstance(tracer.spans, dict)
        assert isinstance(tracer.active_spans, dict)
        assert isinstance(tracer.trace_context, dict)
    
    def test_start_span(self, tracer):
        """Test starting a span"""
        span = tracer.start_span("test_operation", "trace_123", "parent_456", {"key": "value"})
        
        assert span.trace_id == "trace_123"
        assert span.span_id is not None
        assert span.parent_span_id == "parent_456"
        assert span.operation_name == "test_operation"
        assert span.tags == {"key": "value"}
        assert span.span_id in tracer.spans
        assert tracer.active_spans["trace_123"] == span.span_id
    
    def test_start_span_generate_trace_id(self, tracer):
        """Test starting a span with generated trace ID"""
        span = tracer.start_span("test_operation")
        
        assert span.trace_id is not None
        assert span.span_id is not None
        assert span.parent_span_id is None
        assert span.operation_name == "test_operation"
        assert span.tags == {}
    
    def test_finish_span(self, tracer):
        """Test finishing a span"""
        span = tracer.start_span("test_operation", "trace_123")
        span_id = span.span_id
        
        tracer.finish_span(span_id, TraceStatus.SUCCESS)
        
        finished_span = tracer.spans[span_id]
        assert finished_span.end_time is not None
        assert finished_span.duration_ms is not None
        assert finished_span.status == TraceStatus.SUCCESS
        assert finished_span.error is None
        assert "trace_123" not in tracer.active_spans
    
    def test_finish_span_with_error(self, tracer):
        """Test finishing a span with error"""
        span = tracer.start_span("test_operation", "trace_123")
        span_id = span.span_id
        
        tracer.finish_span(span_id, TraceStatus.ERROR, "test error")
        
        finished_span = tracer.spans[span_id]
        assert finished_span.status == TraceStatus.ERROR
        assert finished_span.error == "test error"
    
    def test_finish_nonexistent_span(self, tracer):
        """Test finishing a nonexistent span"""
        # Should not raise an exception
        tracer.finish_span("nonexistent_span")
    
    def test_add_span_log(self, tracer):
        """Test adding log to span"""
        span = tracer.start_span("test_operation")
        span_id = span.span_id
        
        tracer.add_span_log(span_id, "test message", "info", key="value")
        
        span = tracer.spans[span_id]
        assert len(span.logs) == 1
        log_entry = span.logs[0]
        assert log_entry["message"] == "test message"
        assert log_entry["level"] == "info"
        assert log_entry["key"] == "value"
        assert "timestamp" in log_entry
    
    def test_add_span_tag(self, tracer):
        """Test adding tag to span"""
        span = tracer.start_span("test_operation")
        span_id = span.span_id
        
        tracer.add_span_tag(span_id, "key", "value")
        
        span = tracer.spans[span_id]
        assert span.tags["key"] == "value"
    
    def test_get_trace(self, tracer):
        """Test getting all spans for a trace"""
        span1 = tracer.start_span("operation1", "trace_123")
        span2 = tracer.start_span("operation2", "trace_123")
        span3 = tracer.start_span("operation3", "trace_456")
        
        trace_spans = tracer.get_trace("trace_123")
        assert len(trace_spans) == 2
        assert span1 in trace_spans
        assert span2 in trace_spans
        assert span3 not in trace_spans
    
    def test_get_span(self, tracer):
        """Test getting specific span"""
        span = tracer.start_span("test_operation")
        span_id = span.span_id
        
        retrieved_span = tracer.get_span(span_id)
        assert retrieved_span == span
        
        assert tracer.get_span("nonexistent") is None
    
    def test_cleanup_old_spans(self, tracer):
        """Test cleaning up old spans"""
        # Create spans with different ages
        old_span = tracer.start_span("old_operation")
        old_span.start_time = datetime.now() - timedelta(hours=25)
        
        new_span = tracer.start_span("new_operation")
        
        tracer.cleanup_old_spans(max_age_hours=24)
        
        assert old_span.span_id not in tracer.spans
        assert new_span.span_id in tracer.spans


class TestMonitoringService:
    """Test MonitoringService class"""
    
    @pytest.fixture
    def service(self):
        """Create MonitoringService instance"""
        return MonitoringService()
    
    def test_service_initialization(self, service):
        """Test service initialization"""
        assert isinstance(service.metrics_collector, MetricsCollector)
        assert isinstance(service.tracer, DistributedTracer)
        assert isinstance(service.health_checks, dict)
        assert isinstance(service.alerts, list)
        assert isinstance(service.start_time, datetime)
    
    def test_register_health_check(self, service):
        """Test registering health check"""
        def test_check():
            return {"status": "healthy"}
        
        service.register_health_check("test_check", test_check)
        
        assert "test_check" in service.health_checks
        assert service.health_checks["test_check"] == test_check
    
    @pytest.mark.asyncio
    async def test_run_health_checks_success(self, service):
        """Test running health checks successfully"""
        def sync_check():
            return {"status": "healthy"}
        
        async def async_check():
            return {"status": "healthy"}
        
        service.register_health_check("sync_check", sync_check)
        service.register_health_check("async_check", async_check)
        
        results = await service.run_health_checks()
        
        assert "sync_check" in results
        assert "async_check" in results
        assert results["sync_check"]["status"] == "healthy"
        assert results["async_check"]["status"] == "healthy"
    
    @pytest.mark.asyncio
    async def test_run_health_checks_failure(self, service):
        """Test running health checks with failures"""
        def failing_check():
            raise Exception("Check failed")
        
        service.register_health_check("failing_check", failing_check)
        
        results = await service.run_health_checks()
        
        assert "failing_check" in results
        assert results["failing_check"]["status"] == "unhealthy"
        assert "error" in results["failing_check"]
    
    def test_record_request_metrics(self, service):
        """Test recording request metrics"""
        service.record_request_metrics("GET", "/test", 200, 150.0, "user_123")
        
        # Check that metrics were recorded
        metrics = service.metrics_collector.get_metrics()
        assert "http_requests_total" in metrics
        assert "http_request_duration_ms" in metrics
        assert "http_status_codes_total" in metrics
    
    def test_record_cache_metrics(self, service):
        """Test recording cache metrics"""
        service.record_cache_metrics("get", "redis", True, 5.0)
        
        metrics = service.metrics_collector.get_metrics()
        assert "cache_operations_total" in metrics
        assert "cache_operation_duration_ms" in metrics
    
    def test_record_database_metrics(self, service):
        """Test recording database metrics"""
        service.record_database_metrics("select", "users", 25.0, True)
        
        metrics = service.metrics_collector.get_metrics()
        assert "database_operations_total" in metrics
        assert "database_operation_duration_ms" in metrics
    
    def test_record_celery_metrics(self, service):
        """Test recording Celery metrics"""
        service.record_celery_metrics("test_task", "success", 100.0, 2)
        
        metrics = service.metrics_collector.get_metrics()
        assert "celery_tasks_total" in metrics
        assert "celery_task_duration_ms" in metrics
    
    @pytest.mark.asyncio
    async def test_trace_operation_success(self, service):
        """Test tracing operation successfully"""
        async with service.trace_operation("test_operation", "trace_123", tags={"key": "value"}) as span:
            assert span.operation_name == "test_operation"
            assert span.trace_id == "trace_123"
            assert span.tags == {"key": "value"}
            # Simulate some work
            await asyncio.sleep(0.01)
        
        # Check that span was finished successfully
        finished_span = service.tracer.get_span(span.span_id)
        assert finished_span.status == TraceStatus.SUCCESS
        assert finished_span.duration_ms is not None
    
    @pytest.mark.asyncio
    async def test_trace_operation_error(self, service):
        """Test tracing operation with error"""
        with pytest.raises(ValueError):
            async with service.trace_operation("test_operation") as span:
                assert span.operation_name == "test_operation"
                raise ValueError("Test error")
        
        # Check that span was finished with error
        finished_span = service.tracer.get_span(span.span_id)
        assert finished_span.status == TraceStatus.ERROR
        assert finished_span.error == "Test error"
    
    @patch('psutil.cpu_percent')
    @patch('psutil.virtual_memory')
    @patch('psutil.disk_usage')
    def test_get_system_metrics(self, mock_disk, mock_memory, mock_cpu, service):
        """Test getting system metrics"""
        mock_cpu.return_value = 25.5
        mock_memory.return_value = Mock(percent=60.0)
        mock_disk.return_value = Mock(percent=45.0)
        
        metrics = service.get_system_metrics()
        
        assert metrics["cpu_percent"] == 25.5
        assert metrics["memory_percent"] == 60.0
        assert metrics["disk_percent"] == 45.0
        assert metrics["uptime_seconds"] > 0
        assert metrics["active_connections"] >= 0
        assert metrics["total_spans"] >= 0
    
    def test_get_metrics_summary(self, service):
        """Test getting metrics summary"""
        service.record_request_metrics("GET", "/test", 200, 100.0)
        
        summary = service.get_metrics_summary()
        
        assert "metrics" in summary
        assert "system" in summary
        assert "traces" in summary
        assert "active_spans" in summary["traces"]
        assert "total_spans" in summary["traces"]
    
    @pytest.mark.asyncio
    async def test_export_metrics_prometheus(self, service):
        """Test exporting metrics in Prometheus format"""
        service.record_request_metrics("GET", "/test", 200, 100.0)
        
        prometheus_metrics = await service.export_metrics("prometheus")
        
        assert isinstance(prometheus_metrics, str)
        assert "http_requests_total" in prometheus_metrics
        assert "# TYPE" in prometheus_metrics
    
    @pytest.mark.asyncio
    async def test_export_metrics_json(self, service):
        """Test exporting metrics in JSON format"""
        service.record_request_metrics("GET", "/test", 200, 100.0)
        
        json_metrics = await service.export_metrics("json")
        
        assert isinstance(json_metrics, str)
        metrics_data = json.loads(json_metrics)
        assert "metrics" in metrics_data
        assert "system" in metrics_data
    
    @pytest.mark.asyncio
    async def test_export_metrics_unsupported_format(self, service):
        """Test exporting metrics with unsupported format"""
        with pytest.raises(ValueError):
            await service.export_metrics("unsupported")
    
    def test_create_alert(self, service):
        """Test creating alert"""
        def test_condition():
            return True
        
        service.create_alert("test_alert", test_condition, "warning", "Test message")
        
        assert len(service.alerts) == 1
        alert = service.alerts[0]
        assert alert["name"] == "test_alert"
        assert alert["condition"] == test_condition
        assert alert["severity"] == "warning"
        assert alert["message"] == "Test message"
        assert alert["triggered"] is False
        assert isinstance(alert["created_at"], datetime)
    
    @pytest.mark.asyncio
    async def test_check_alerts_no_trigger(self, service):
        """Test checking alerts with no triggers"""
        def false_condition():
            return False
        
        service.create_alert("test_alert", false_condition, "warning", "Test message")
        
        triggered = await service.check_alerts()
        assert len(triggered) == 0
        assert not service.alerts[0]["triggered"]
    
    @pytest.mark.asyncio
    async def test_check_alerts_trigger(self, service):
        """Test checking alerts with trigger"""
        def true_condition():
            return True
        
        service.create_alert("test_alert", true_condition, "warning", "Test message")
        
        triggered = await service.check_alerts()
        assert len(triggered) == 1
        assert triggered[0]["name"] == "test_alert"
        assert service.alerts[0]["triggered"] is True
        assert "triggered_at" in service.alerts[0]
    
    @pytest.mark.asyncio
    async def test_check_alerts_async_condition(self, service):
        """Test checking alerts with async condition"""
        async def async_condition():
            return True
        
        service.create_alert("async_alert", async_condition, "warning", "Test message")
        
        triggered = await service.check_alerts()
        assert len(triggered) == 1
        assert triggered[0]["name"] == "async_alert"
    
    @pytest.mark.asyncio
    async def test_check_alerts_condition_error(self, service):
        """Test checking alerts with condition error"""
        def error_condition():
            raise Exception("Condition error")
        
        service.create_alert("error_alert", error_condition, "warning", "Test message")
        
        triggered = await service.check_alerts()
        assert len(triggered) == 0  # Should handle error gracefully


class TestGlobalService:
    """Test global monitoring service instance"""
    
    def test_global_service_exists(self):
        """Test that global service instance exists"""
        assert monitoring_service is not None
        assert isinstance(monitoring_service, MonitoringService)
    
    def test_global_service_initialization(self):
        """Test global service initialization"""
        assert monitoring_service.metrics_collector is not None
        assert monitoring_service.tracer is not None
        assert isinstance(monitoring_service.health_checks, dict)
        assert isinstance(monitoring_service.alerts, list)
