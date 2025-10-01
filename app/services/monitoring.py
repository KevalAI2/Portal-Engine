"""
Comprehensive Monitoring and Metrics Collection Service

This module provides metrics collection, distributed tracing, and monitoring
capabilities for observability and performance tracking.
"""
import time
import uuid
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import asyncio
import json
from contextlib import asynccontextmanager
from app.core.config import settings
from app.core.logging import get_logger, log_exception
from app.services.cache_service import cache_service

logger = get_logger("monitoring")


class MetricType(str, Enum):
    """Types of metrics"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


class TraceStatus(str, Enum):
    """Trace status types"""
    SUCCESS = "success"
    ERROR = "error"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


@dataclass
class Metric:
    """Metric data structure"""
    name: str
    value: float
    metric_type: MetricType
    labels: Dict[str, str] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    description: str = ""


@dataclass
class TraceSpan:
    """Distributed trace span"""
    trace_id: str
    span_id: str
    parent_span_id: Optional[str] = None
    operation_name: str = ""
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    duration_ms: Optional[float] = None
    status: TraceStatus = TraceStatus.SUCCESS
    tags: Dict[str, Any] = field(default_factory=dict)
    logs: List[Dict[str, Any]] = field(default_factory=list)
    error: Optional[str] = None


class MetricsCollector:
    """Metrics collection and aggregation service"""
    
    def __init__(self):
        self.metrics: Dict[str, List[Metric]] = {}
        self.counters: Dict[str, float] = {}
        self.gauges: Dict[str, float] = {}
        self.histograms: Dict[str, List[float]] = {}
        self.summaries: Dict[str, Dict[str, float]] = {}
    
    def increment_counter(
        self,
        name: str,
        value: float = 1.0,
        labels: Optional[Dict[str, str]] = None
    ):
        """Increment a counter metric"""
        key = self._get_metric_key(name, labels or {})
        self.counters[key] = self.counters.get(key, 0) + value
        
        metric = Metric(
            name=name,
            value=self.counters[key],
            metric_type=MetricType.COUNTER,
            labels=labels or {}
        )
        self._store_metric(metric)
    
    def set_gauge(
        self,
        name: str,
        value: float,
        labels: Optional[Dict[str, str]] = None
    ):
        """Set a gauge metric value"""
        key = self._get_metric_key(name, labels or {})
        self.gauges[key] = value
        
        metric = Metric(
            name=name,
            value=value,
            metric_type=MetricType.GAUGE,
            labels=labels or {}
        )
        self._store_metric(metric)
    
    def observe_histogram(
        self,
        name: str,
        value: float,
        labels: Optional[Dict[str, str]] = None
    ):
        """Observe a histogram metric value"""
        key = self._get_metric_key(name, labels or {})
        if key not in self.histograms:
            self.histograms[key] = []
        self.histograms[key].append(value)
        
        metric = Metric(
            name=name,
            value=value,
            metric_type=MetricType.HISTOGRAM,
            labels=labels or {}
        )
        self._store_metric(metric)
    
    def observe_summary(
        self,
        name: str,
        value: float,
        labels: Optional[Dict[str, str]] = None
    ):
        """Observe a summary metric value"""
        key = self._get_metric_key(name, labels or {})
        if key not in self.summaries:
            self.summaries[key] = {"count": 0, "sum": 0, "min": float('inf'), "max": float('-inf')}
        
        summary = self.summaries[key]
        summary["count"] += 1
        summary["sum"] += value
        summary["min"] = min(summary["min"], value)
        summary["max"] = max(summary["max"], value)
        
        metric = Metric(
            name=name,
            value=value,
            metric_type=MetricType.SUMMARY,
            labels=labels or {}
        )
        self._store_metric(metric)
    
    def _get_metric_key(self, name: str, labels: Dict[str, str]) -> str:
        """Generate metric key with labels"""
        label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{name}{{{label_str}}}" if label_str else name
    
    def _store_metric(self, metric: Metric):
        """Store metric in collection"""
        if metric.name not in self.metrics:
            self.metrics[metric.name] = []
        self.metrics[metric.name].append(metric)
    
    def get_metrics(self, name: Optional[str] = None) -> Dict[str, Any]:
        """Get collected metrics"""
        if name:
            return {name: self.metrics.get(name, [])}
        return self.metrics
    
    def get_metric_summary(self) -> Dict[str, Any]:
        """Get metric summary statistics"""
        return {
            "counters": dict(self.counters),
            "gauges": dict(self.gauges),
            "histograms": {
                key: {
                    "count": len(values),
                    "min": min(values) if values else 0,
                    "max": max(values) if values else 0,
                    "avg": sum(values) / len(values) if values else 0
                }
                for key, values in self.histograms.items()
            },
            "summaries": dict(self.summaries)
        }


class DistributedTracer:
    """Distributed tracing service"""
    
    def __init__(self):
        self.spans: Dict[str, TraceSpan] = {}
        self.active_spans: Dict[str, str] = {}  # trace_id -> span_id
        self.trace_context: Dict[str, str] = {}
    
    def start_span(
        self,
        operation_name: str,
        trace_id: Optional[str] = None,
        parent_span_id: Optional[str] = None,
        tags: Optional[Dict[str, Any]] = None
    ) -> TraceSpan:
        """Start a new trace span"""
        if not trace_id:
            trace_id = str(uuid.uuid4())
        
        span_id = str(uuid.uuid4())
        
        span = TraceSpan(
            trace_id=trace_id,
            span_id=span_id,
            parent_span_id=parent_span_id,
            operation_name=operation_name,
            tags=tags or {}
        )
        
        self.spans[span_id] = span
        self.active_spans[trace_id] = span_id
        
        logger.debug("Span started", 
                    trace_id=trace_id, 
                    span_id=span_id, 
                    operation=operation_name)
        
        return span
    
    def finish_span(
        self,
        span_id: str,
        status: TraceStatus = TraceStatus.SUCCESS,
        error: Optional[str] = None
    ):
        """Finish a trace span"""
        if span_id not in self.spans:
            logger.warning("Span not found", span_id=span_id)
            return
        
        span = self.spans[span_id]
        span.end_time = datetime.now()
        span.duration_ms = (span.end_time - span.start_time).total_seconds() * 1000
        span.status = status
        span.error = error
        
        # Remove from active spans
        if span.trace_id in self.active_spans:
            del self.active_spans[span.trace_id]
        
        logger.debug("Span finished", 
                    trace_id=span.trace_id, 
                    span_id=span_id, 
                    duration_ms=span.duration_ms,
                    status=status.value)
    
    def add_span_log(self, span_id: str, message: str, level: str = "info", **kwargs):
        """Add log entry to span"""
        if span_id not in self.spans:
            return
        
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "message": message,
            **kwargs
        }
        self.spans[span_id].logs.append(log_entry)
    
    def add_span_tag(self, span_id: str, key: str, value: Any):
        """Add tag to span"""
        if span_id not in self.spans:
            return
        
        self.spans[span_id].tags[key] = value
    
    def get_trace(self, trace_id: str) -> List[TraceSpan]:
        """Get all spans for a trace"""
        return [span for span in self.spans.values() if span.trace_id == trace_id]
    
    def get_span(self, span_id: str) -> Optional[TraceSpan]:
        """Get specific span by ID"""
        return self.spans.get(span_id)
    
    def cleanup_old_spans(self, max_age_hours: int = 24):
        """Clean up old spans"""
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        old_span_ids = [
            span_id for span_id, span in self.spans.items()
            if span.start_time < cutoff_time
        ]
        
        for span_id in old_span_ids:
            del self.spans[span_id]
        
        logger.info("Old spans cleaned up", count=len(old_span_ids))


class MonitoringService:
    """Comprehensive monitoring service"""
    
    def __init__(self):
        self.metrics_collector = MetricsCollector()
        self.tracer = DistributedTracer()
        self.health_checks: Dict[str, Callable] = {}
        self.alerts: List[Dict[str, Any]] = []
        self.start_time = datetime.now()
    
    def register_health_check(self, name: str, check_func: Callable):
        """Register a health check function"""
        self.health_checks[name] = check_func
        logger.info("Health check registered", name=name)
    
    async def run_health_checks(self) -> Dict[str, Any]:
        """Run all registered health checks"""
        results = {}
        
        for name, check_func in self.health_checks.items():
            try:
                if asyncio.iscoroutinefunction(check_func):
                    result = await check_func()
                else:
                    result = check_func()
                results[name] = {"status": "healthy", "result": result}
            except Exception as e:
                results[name] = {"status": "unhealthy", "error": str(e)}
                logger.error("Health check failed", name=name, error=str(e))
        
        return results
    
    def record_request_metrics(
        self,
        method: str,
        endpoint: str,
        status_code: int,
        duration_ms: float,
        user_id: Optional[str] = None
    ):
        """Record HTTP request metrics"""
        labels = {
            "method": method,
            "endpoint": endpoint,
            "status_code": str(status_code)
        }
        
        if user_id:
            labels["user_id"] = user_id
        
        # Increment request counter
        self.metrics_collector.increment_counter("http_requests_total", labels=labels)
        
        # Record request duration
        self.metrics_collector.observe_histogram("http_request_duration_ms", duration_ms, labels=labels)
        
        # Record status code distribution
        self.metrics_collector.increment_counter("http_status_codes_total", labels=labels)
    
    def record_cache_metrics(
        self,
        operation: str,
        cache_type: str,
        hit: bool,
        duration_ms: float
    ):
        """Record cache operation metrics"""
        labels = {
            "operation": operation,
            "cache_type": cache_type,
            "hit": str(hit).lower()
        }
        
        self.metrics_collector.increment_counter("cache_operations_total", labels=labels)
        self.metrics_collector.observe_histogram("cache_operation_duration_ms", duration_ms, labels=labels)
    
    def record_database_metrics(
        self,
        operation: str,
        table: str,
        duration_ms: float,
        success: bool
    ):
        """Record database operation metrics"""
        labels = {
            "operation": operation,
            "table": table,
            "success": str(success).lower()
        }
        
        self.metrics_collector.increment_counter("database_operations_total", labels=labels)
        self.metrics_collector.observe_histogram("database_operation_duration_ms", duration_ms, labels=labels)
    
    def record_celery_metrics(
        self,
        task_name: str,
        status: str,
        duration_ms: float,
        retry_count: int = 0
    ):
        """Record Celery task metrics"""
        labels = {
            "task_name": task_name,
            "status": status,
            "retry_count": str(retry_count)
        }
        
        self.metrics_collector.increment_counter("celery_tasks_total", labels=labels)
        self.metrics_collector.observe_histogram("celery_task_duration_ms", duration_ms, labels=labels)
    
    @asynccontextmanager
    async def trace_operation(
        self,
        operation_name: str,
        trace_id: Optional[str] = None,
        parent_span_id: Optional[str] = None,
        tags: Optional[Dict[str, Any]] = None
    ):
        """Context manager for tracing operations"""
        span = self.tracer.start_span(operation_name, trace_id, parent_span_id, tags)
        
        try:
            yield span
            self.tracer.finish_span(span.span_id, TraceStatus.SUCCESS)
        except Exception as e:
            self.tracer.finish_span(span.span_id, TraceStatus.ERROR, str(e))
            raise
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get system-level metrics"""
        import psutil
        
        return {
            "cpu_percent": psutil.cpu_percent(),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage('/').percent,
            "uptime_seconds": (datetime.now() - self.start_time).total_seconds(),
            "active_connections": len(self.tracer.active_spans),
            "total_spans": len(self.tracer.spans)
        }
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get comprehensive metrics summary"""
        return {
            "metrics": self.metrics_collector.get_metric_summary(),
            "system": self.get_system_metrics(),
            "traces": {
                "active_spans": len(self.tracer.active_spans),
                "total_spans": len(self.tracer.spans)
            }
        }
    
    async def export_metrics(self, format: str = "prometheus") -> str:
        """Export metrics in specified format"""
        if format == "prometheus":
            return self._export_prometheus_metrics()
        elif format == "json":
            return json.dumps(self.get_metrics_summary(), default=str)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def _export_prometheus_metrics(self) -> str:
        """Export metrics in Prometheus format"""
        lines = []
        
        # Counters
        for key, value in self.metrics_collector.counters.items():
            lines.append(f"# TYPE {key} counter")
            lines.append(f"{key} {value}")
        
        # Gauges
        for key, value in self.metrics_collector.gauges.items():
            lines.append(f"# TYPE {key} gauge")
            lines.append(f"{key} {value}")
        
        # Histograms
        for key, values in self.metrics_collector.histograms.items():
            if values:
                lines.append(f"# TYPE {key} histogram")
                lines.append(f"{key}_count {len(values)}")
                lines.append(f"{key}_sum {sum(values)}")
                lines.append(f"{key}_min {min(values)}")
                lines.append(f"{key}_max {max(values)}")
        
        return "\n".join(lines)
    
    def create_alert(
        self,
        name: str,
        condition: Callable,
        severity: str = "warning",
        message: str = ""
    ):
        """Create an alert rule"""
        alert = {
            "name": name,
            "condition": condition,
            "severity": severity,
            "message": message,
            "created_at": datetime.now(),
            "triggered": False
        }
        self.alerts.append(alert)
        logger.info("Alert created", name=name, severity=severity)
    
    async def check_alerts(self) -> List[Dict[str, Any]]:
        """Check all alert conditions"""
        triggered_alerts = []
        
        for alert in self.alerts:
            try:
                if asyncio.iscoroutinefunction(alert["condition"]):
                    triggered = await alert["condition"]()
                else:
                    triggered = alert["condition"]()
                
                if triggered and not alert["triggered"]:
                    alert["triggered"] = True
                    alert["triggered_at"] = datetime.now()
                    triggered_alerts.append(alert)
                    logger.warning("Alert triggered", name=alert["name"], message=alert["message"])
            except Exception as e:
                logger.error("Alert check failed", name=alert["name"], error=str(e))
        
        return triggered_alerts


# Global monitoring service instance
monitoring_service = MonitoringService()