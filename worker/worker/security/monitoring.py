"""
Monitoring and logging utilities for the security module.

Provides performance metrics tracking, audit logging, and security
event monitoring capabilities.
"""

import json
import logging
import time
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

from .security_refactor import PerformanceMetrics, SecurityViolation

logger = logging.getLogger(__name__)


@dataclass
class SecurityMetricsCollector:
    """Collects and aggregates security metrics."""

    metrics: List[PerformanceMetrics]
    violations: List[SecurityViolation]
    operation_counts: Dict[str, int]
    provider_usage: Dict[str, int]

    def __init__(self) -> None:
        self.metrics = []
        self.violations = []
        self.operation_counts = defaultdict(int)
        self.provider_usage = defaultdict(int)

    def record_metric(self, metric: PerformanceMetrics) -> None:
        """Record a performance metric."""
        self.metrics.append(metric)
        self.operation_counts[metric.operation] += 1
        self.provider_usage[metric.provider] += 1

    def record_violation(self, violation: SecurityViolation) -> None:
        """Record a security violation."""
        self.violations.append(violation)

    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of collected metrics."""
        if not self.metrics:
            avg_duration = 0.0
        else:
            avg_duration = sum(m.duration_ms for m in self.metrics) / len(
                self.metrics
            )

        return {
            "total_operations": len(self.metrics),
            "total_violations": len(self.violations),
            "average_duration_ms": avg_duration,
            "operation_counts": dict(self.operation_counts),
            "provider_usage": dict(self.provider_usage),
            "success_rate": self._calculate_success_rate(),
        }

    def _calculate_success_rate(self) -> float:
        """Calculate the success rate of operations."""
        if not self.metrics:
            return 0.0

        successful = sum(1 for m in self.metrics if m.success)
        return (successful / len(self.metrics)) * 100

    def clear(self) -> None:
        """Clear all collected metrics."""
        self.metrics.clear()
        self.violations.clear()
        self.operation_counts.clear()
        self.provider_usage.clear()


class SecurityAuditLogger:
    """Handles audit logging for security events."""

    def __init__(
        self,
        logger_name: str = "security.audit",
        enable_file_logging: bool = False,
        log_file: Optional[str] = None,
    ) -> None:
        self.logger = logging.getLogger(logger_name)
        self.enable_file_logging = enable_file_logging
        self.log_file = log_file

        if enable_file_logging and log_file:
            self._setup_file_handler(log_file)

    def _setup_file_handler(self, log_file: str) -> None:
        """Setup file handler for audit logging."""
        try:
            handler = logging.FileHandler(log_file)
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
        except Exception as e:
            logger.error(f"Failed to setup file handler: {e}")

    def log_violation(self, violation: SecurityViolation) -> None:
        """Log a security violation."""
        violation_dict = asdict(violation)
        violation_dict["timestamp"] = violation.timestamp.isoformat()
        violation_dict["violation_type"] = violation.violation_type.value

        self.logger.warning(
            f"Security violation: {json.dumps(violation_dict)}"
        )

    def log_provider_change(
        self, old_provider: str, new_provider: str, reason: str
    ) -> None:
        """Log a provider change."""
        self.logger.info(
            f"Provider changed from {old_provider} to {new_provider}: "
            f"{reason}"
        )

    def log_validation_failure(
        self,
        operation: str,
        reason: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Log a validation failure."""
        message = f"Validation failure in {operation}: {reason}"
        if details:
            message += f" - {json.dumps(details)}"

        self.logger.error(message)

    def log_configuration_change(
        self, config_key: str, old_value: Any, new_value: Any
    ) -> None:
        """Log a configuration change."""
        self.logger.info(
            f"Configuration changed: {config_key} "
            f"from {old_value} to {new_value}"
        )


class PerformanceMonitor:
    """Monitors performance of security operations."""

    def __init__(self) -> None:
        self.operation_times: Dict[str, List[float]] = defaultdict(list)
        self.operation_errors: Dict[str, int] = defaultdict(int)

    def start_operation(self, operation_name: str) -> "OperationTimer":
        """Start timing an operation."""
        return OperationTimer(self, operation_name)

    def record_operation_time(
        self, operation_name: str, duration_ms: float
    ) -> None:
        """Record the time taken for an operation."""
        self.operation_times[operation_name].append(duration_ms)

    def record_operation_error(self, operation_name: str) -> None:
        """Record an error for an operation."""
        self.operation_errors[operation_name] += 1

    def get_operation_stats(
        self, operation_name: str
    ) -> Dict[str, float]:
        """Get statistics for an operation."""
        times = self.operation_times.get(operation_name, [])

        if not times:
            return {
                "count": 0,
                "average_ms": 0.0,
                "min_ms": 0.0,
                "max_ms": 0.0,
                "errors": 0,
            }

        return {
            "count": len(times),
            "average_ms": sum(times) / len(times),
            "min_ms": min(times),
            "max_ms": max(times),
            "errors": self.operation_errors.get(operation_name, 0),
        }

    def get_all_stats(self) -> Dict[str, Dict[str, float]]:
        """Get statistics for all operations."""
        return {
            op: self.get_operation_stats(op)
            for op in self.operation_times.keys()
        }

    def clear(self) -> None:
        """Clear all recorded statistics."""
        self.operation_times.clear()
        self.operation_errors.clear()


class OperationTimer:
    """Context manager for timing operations."""

    def __init__(
        self, monitor: PerformanceMonitor, operation_name: str
    ) -> None:
        self.monitor = monitor
        self.operation_name = operation_name
        self.start_time: Optional[float] = None

    def __enter__(self) -> "OperationTimer":
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if self.start_time is not None:
            duration_ms = (time.time() - self.start_time) * 1000
            self.monitor.record_operation_time(
                self.operation_name, duration_ms
            )

            if exc_type is not None:
                self.monitor.record_operation_error(self.operation_name)


class SecurityEventLogger:
    """Logs security-related events."""

    def __init__(self) -> None:
        self.logger = logging.getLogger("security.events")
        self.events: List[Dict[str, Any]] = []

    def log_event(
        self,
        event_type: str,
        severity: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Log a security event."""
        event = {
            "timestamp": datetime.now().isoformat(),
            "type": event_type,
            "severity": severity,
            "message": message,
            "details": details or {},
        }

        self.events.append(event)

        log_level = getattr(logging, severity.upper(), logging.INFO)
        self.logger.log(
            log_level, f"[{event_type}] {message} - {details}"
        )

    def get_recent_events(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent events."""
        return self.events[-limit:]

    def clear_events(self) -> None:
        """Clear all recorded events."""
        self.events.clear()


# Global instances
_metrics_collector: Optional[SecurityMetricsCollector] = None
_audit_logger: Optional[SecurityAuditLogger] = None
_performance_monitor: Optional[PerformanceMonitor] = None
_event_logger: Optional[SecurityEventLogger] = None


def get_metrics_collector() -> SecurityMetricsCollector:
    """Get or create the global metrics collector."""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = SecurityMetricsCollector()
    return _metrics_collector


def get_audit_logger() -> SecurityAuditLogger:
    """Get or create the global audit logger."""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = SecurityAuditLogger()
    return _audit_logger


def get_performance_monitor() -> PerformanceMonitor:
    """Get or create the global performance monitor."""
    global _performance_monitor
    if _performance_monitor is None:
        _performance_monitor = PerformanceMonitor()
    return _performance_monitor


def get_event_logger() -> SecurityEventLogger:
    """Get or create the global event logger."""
    global _event_logger
    if _event_logger is None:
        _event_logger = SecurityEventLogger()
    return _event_logger
