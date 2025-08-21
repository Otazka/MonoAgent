#!/usr/bin/env python3
"""
MonoAgent Monitoring and Performance Benchmarking Module

This module provides comprehensive monitoring, alerting, and performance 
benchmarking capabilities for the MonoAgent production deployment.

Features:
- Health checks and system metrics
- Performance benchmarks for large repositories
- Alerting via webhooks and email
- Resource usage monitoring
- Error rate tracking
- Custom metrics collection
"""

import json
import logging
import os
import psutil
import smtplib
import subprocess
import time
import traceback
from dataclasses import dataclass, field
from datetime import datetime, timezone
from email.mime.text import MIMEText
from typing import Dict, List, Optional, Any
import requests


@dataclass
class PerformanceMetrics:
    """Performance metrics for monitoring."""
    
    operation: str
    start_time: float
    end_time: Optional[float] = None
    duration_seconds: Optional[float] = None
    memory_usage_mb: Optional[float] = None
    cpu_percent: Optional[float] = None
    disk_io_read_mb: Optional[float] = None
    disk_io_write_mb: Optional[float] = None
    network_sent_mb: Optional[float] = None
    network_recv_mb: Optional[float] = None
    success: bool = True
    error_message: Optional[str] = None
    repo_size_mb: Optional[float] = None
    projects_count: Optional[int] = None
    files_processed: Optional[int] = None


@dataclass
class MonitoringConfig:
    """Configuration for monitoring and alerting."""
    
    # Health check settings
    health_check_interval: int = 30  # seconds
    health_check_timeout: int = 10   # seconds
    
    # Performance monitoring
    enable_performance_monitoring: bool = True
    performance_log_file: Optional[str] = "performance.jsonl"
    benchmark_large_repo_threshold_mb: float = 100.0
    
    # Alerting
    enable_alerting: bool = False
    webhook_url: Optional[str] = None
    smtp_server: Optional[str] = None
    smtp_port: int = 587
    email_from: Optional[str] = None
    email_to: Optional[str] = None
    email_password: Optional[str] = None
    
    # Thresholds for alerting
    max_memory_usage_mb: float = 2048.0
    max_processing_time_minutes: float = 60.0
    max_error_rate_percent: float = 10.0
    
    # Metrics collection
    collect_system_metrics: bool = True
    metrics_retention_days: int = 30


class MonitoringAgent:
    """Advanced monitoring and alerting for MonoAgent."""
    
    def __init__(self, config: MonitoringConfig):
        self.config = config
        self.logger = self._setup_logging()
        self.metrics_history: List[PerformanceMetrics] = []
        self.error_count = 0
        self.operation_count = 0
        
    def _setup_logging(self) -> logging.Logger:
        """Set up monitoring logger."""
        logger = logging.getLogger("monoagent.monitoring")
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            
        return logger
    
    def start_operation_monitoring(self, operation: str, **kwargs) -> PerformanceMetrics:
        """Start monitoring an operation."""
        metrics = PerformanceMetrics(
            operation=operation,
            start_time=time.time(),
            **kwargs
        )
        
        if self.config.collect_system_metrics:
            self._collect_system_metrics(metrics)
            
        self.logger.info(f"🔍 Started monitoring operation: {operation}")
        return metrics
    
    def end_operation_monitoring(self, metrics: PerformanceMetrics, 
                               success: bool = True, 
                               error_message: Optional[str] = None) -> PerformanceMetrics:
        """End monitoring an operation and calculate final metrics."""
        metrics.end_time = time.time()
        metrics.duration_seconds = metrics.end_time - metrics.start_time
        metrics.success = success
        metrics.error_message = error_message
        
        if self.config.collect_system_metrics:
            self._collect_final_system_metrics(metrics)
        
        # Update counters
        self.operation_count += 1
        if not success:
            self.error_count += 1
        
        # Log performance
        self._log_performance_metrics(metrics)
        
        # Store metrics
        self.metrics_history.append(metrics)
        
        # Check thresholds and alert if needed
        self._check_alert_thresholds(metrics)
        
        self.logger.info(
            f"✅ Completed monitoring operation: {metrics.operation} "
            f"(Duration: {metrics.duration_seconds:.2f}s, Success: {success})"
        )
        
        return metrics
    
    def _collect_system_metrics(self, metrics: PerformanceMetrics):
        """Collect initial system metrics."""
        try:
            process = psutil.Process()
            
            # Memory usage
            memory_info = process.memory_info()
            metrics.memory_usage_mb = memory_info.rss / 1024 / 1024
            
            # CPU usage
            metrics.cpu_percent = process.cpu_percent()
            
            # Disk I/O
            io_counters = process.io_counters()
            metrics.disk_io_read_mb = io_counters.read_bytes / 1024 / 1024
            metrics.disk_io_write_mb = io_counters.write_bytes / 1024 / 1024
            
        except Exception as e:
            self.logger.warning(f"Failed to collect system metrics: {e}")
    
    def _collect_final_system_metrics(self, metrics: PerformanceMetrics):
        """Collect final system metrics and calculate deltas."""
        try:
            process = psutil.Process()
            
            # Update memory usage (peak)
            memory_info = process.memory_info()
            final_memory_mb = memory_info.rss / 1024 / 1024
            if metrics.memory_usage_mb:
                metrics.memory_usage_mb = max(metrics.memory_usage_mb, final_memory_mb)
            else:
                metrics.memory_usage_mb = final_memory_mb
            
            # Network I/O delta (if available)
            try:
                net_io = psutil.net_io_counters()
                if hasattr(metrics, '_initial_net_sent'):
                    metrics.network_sent_mb = (net_io.bytes_sent - metrics._initial_net_sent) / 1024 / 1024
                    metrics.network_recv_mb = (net_io.bytes_recv - metrics._initial_net_recv) / 1024 / 1024
                else:
                    metrics.network_sent_mb = net_io.bytes_sent / 1024 / 1024
                    metrics.network_recv_mb = net_io.bytes_recv / 1024 / 1024
            except Exception:
                pass  # Network stats not available on all systems
                
        except Exception as e:
            self.logger.warning(f"Failed to collect final system metrics: {e}")
    
    def _log_performance_metrics(self, metrics: PerformanceMetrics):
        """Log performance metrics to file."""
        if not self.config.performance_log_file:
            return
            
        try:
            metric_data = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "operation": metrics.operation,
                "duration_seconds": metrics.duration_seconds,
                "memory_usage_mb": metrics.memory_usage_mb,
                "cpu_percent": metrics.cpu_percent,
                "disk_io_read_mb": metrics.disk_io_read_mb,
                "disk_io_write_mb": metrics.disk_io_write_mb,
                "network_sent_mb": metrics.network_sent_mb,
                "network_recv_mb": metrics.network_recv_mb,
                "success": metrics.success,
                "error_message": metrics.error_message,
                "repo_size_mb": metrics.repo_size_mb,
                "projects_count": metrics.projects_count,
                "files_processed": metrics.files_processed,
            }
            
            with open(self.config.performance_log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(metric_data, ensure_ascii=False) + "\n")
                
        except Exception as e:
            self.logger.error(f"Failed to log performance metrics: {e}")
    
    def _check_alert_thresholds(self, metrics: PerformanceMetrics):
        """Check if metrics exceed alert thresholds."""
        if not self.config.enable_alerting:
            return
            
        alerts = []
        
        # Memory threshold
        if (metrics.memory_usage_mb and 
            metrics.memory_usage_mb > self.config.max_memory_usage_mb):
            alerts.append(
                f"High memory usage: {metrics.memory_usage_mb:.1f}MB "
                f"(threshold: {self.config.max_memory_usage_mb}MB)"
            )
        
        # Processing time threshold
        if (metrics.duration_seconds and 
            metrics.duration_seconds > self.config.max_processing_time_minutes * 60):
            alerts.append(
                f"Long processing time: {metrics.duration_seconds / 60:.1f}min "
                f"(threshold: {self.config.max_processing_time_minutes}min)"
            )
        
        # Error rate threshold
        if self.operation_count > 0:
            error_rate = (self.error_count / self.operation_count) * 100
            if error_rate > self.config.max_error_rate_percent:
                alerts.append(
                    f"High error rate: {error_rate:.1f}% "
                    f"(threshold: {self.config.max_error_rate_percent}%)"
                )
        
        if alerts:
            self._send_alerts(metrics.operation, alerts)
    
    def _send_alerts(self, operation: str, alerts: List[str]):
        """Send alerts via configured channels."""
        alert_message = f"MonoAgent Alert - Operation: {operation}\n\n" + "\n".join(alerts)
        
        # Webhook alert
        if self.config.webhook_url:
            try:
                payload = {
                    "text": alert_message,
                    "operation": operation,
                    "alerts": alerts,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
                response = requests.post(
                    self.config.webhook_url, 
                    json=payload, 
                    timeout=10
                )
                if response.status_code == 200:
                    self.logger.info("✅ Webhook alert sent successfully")
                else:
                    self.logger.error(f"❌ Webhook alert failed: {response.status_code}")
            except Exception as e:
                self.logger.error(f"❌ Webhook alert error: {e}")
        
        # Email alert
        if (self.config.smtp_server and self.config.email_from and 
            self.config.email_to and self.config.email_password):
            try:
                msg = MIMEText(alert_message)
                msg['Subject'] = f"MonoAgent Alert - {operation}"
                msg['From'] = self.config.email_from
                msg['To'] = self.config.email_to
                
                with smtplib.SMTP(self.config.smtp_server, self.config.smtp_port) as server:
                    server.starttls()
                    server.login(self.config.email_from, self.config.email_password)
                    server.send_message(msg)
                    
                self.logger.info("✅ Email alert sent successfully")
            except Exception as e:
                self.logger.error(f"❌ Email alert error: {e}")
    
    def health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check."""
        health_status = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "healthy",
            "checks": {},
            "metrics": {}
        }
        
        try:
            # System resources check
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            health_status["checks"]["memory"] = {
                "status": "ok" if memory.percent < 90 else "warning",
                "usage_percent": memory.percent,
                "available_gb": memory.available / 1024 / 1024 / 1024
            }
            
            health_status["checks"]["disk"] = {
                "status": "ok" if disk.percent < 90 else "warning",
                "usage_percent": disk.percent,
                "free_gb": disk.free / 1024 / 1024 / 1024
            }
            
            # Git availability check
            try:
                result = subprocess.run(['git', '--version'], 
                                      capture_output=True, text=True, timeout=5)
                health_status["checks"]["git"] = {
                    "status": "ok" if result.returncode == 0 else "error",
                    "version": result.stdout.strip() if result.returncode == 0 else None,
                    "error": result.stderr if result.returncode != 0 else None
                }
            except Exception as e:
                health_status["checks"]["git"] = {
                    "status": "error",
                    "error": str(e)
                }
            
            # Python dependencies check
            try:
                import split_repo_agent
                health_status["checks"]["dependencies"] = {
                    "status": "ok",
                    "monoagent_available": True
                }
            except Exception as e:
                health_status["checks"]["dependencies"] = {
                    "status": "error",
                    "error": str(e)
                }
            
            # Performance metrics summary
            if self.metrics_history:
                recent_metrics = self.metrics_history[-10:]  # Last 10 operations
                avg_duration = sum(m.duration_seconds for m in recent_metrics if m.duration_seconds) / len(recent_metrics)
                success_rate = sum(1 for m in recent_metrics if m.success) / len(recent_metrics) * 100
                
                health_status["metrics"] = {
                    "recent_operations": len(recent_metrics),
                    "avg_duration_seconds": avg_duration,
                    "success_rate_percent": success_rate,
                    "total_operations": self.operation_count,
                    "total_errors": self.error_count
                }
            
            # Overall status determination
            failed_checks = [
                name for name, check in health_status["checks"].items()
                if check["status"] == "error"
            ]
            
            if failed_checks:
                health_status["status"] = "unhealthy"
                health_status["failed_checks"] = failed_checks
            elif any(check["status"] == "warning" for check in health_status["checks"].values()):
                health_status["status"] = "warning"
                
        except Exception as e:
            health_status["status"] = "error"
            health_status["error"] = str(e)
            health_status["traceback"] = traceback.format_exc()
        
        return health_status
    
    def run_performance_benchmark(self, test_repo_url: Optional[str] = None) -> Dict[str, Any]:
        """Run comprehensive performance benchmark."""
        self.logger.info("🚀 Starting performance benchmark...")
        
        benchmark_results = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "test_repo_url": test_repo_url,
            "benchmarks": {},
            "system_info": {}
        }
        
        try:
            # System info
            benchmark_results["system_info"] = {
                "cpu_count": psutil.cpu_count(),
                "memory_total_gb": psutil.virtual_memory().total / 1024 / 1024 / 1024,
                "python_version": os.sys.version,
                "platform": os.uname().sysname if hasattr(os, 'uname') else "unknown"
            }
            
            # Benchmark 1: Import time
            start_time = time.time()
            import split_repo_agent
            import_time = time.time() - start_time
            
            benchmark_results["benchmarks"]["import_time_seconds"] = import_time
            
            # Benchmark 2: Configuration loading
            start_time = time.time()
            config = split_repo_agent.RepoSplitterConfig(
                source_repo_url="https://github.com/test/repo.git",
                org="test",
                github_token="dummy",
                dry_run=True
            )
            config_time = time.time() - start_time
            
            benchmark_results["benchmarks"]["config_load_time_seconds"] = config_time
            
            # Benchmark 3: Memory usage baseline
            process = psutil.Process()
            baseline_memory_mb = process.memory_info().rss / 1024 / 1024
            benchmark_results["benchmarks"]["baseline_memory_mb"] = baseline_memory_mb
            
            # If test repo provided, run more comprehensive benchmarks
            if test_repo_url:
                self.logger.info(f"🔄 Running repository benchmark with: {test_repo_url}")
                
                # This would require actual repository processing
                # For now, we'll simulate the metrics
                benchmark_results["benchmarks"]["simulated_repo_analysis"] = {
                    "note": "Actual repo analysis would require full setup",
                    "estimated_small_repo_seconds": 10.0,
                    "estimated_medium_repo_seconds": 60.0,
                    "estimated_large_repo_seconds": 300.0
                }
            
            benchmark_results["status"] = "completed"
            self.logger.info("✅ Performance benchmark completed successfully")
            
        except Exception as e:
            benchmark_results["status"] = "failed"
            benchmark_results["error"] = str(e)
            benchmark_results["traceback"] = traceback.format_exc()
            self.logger.error(f"❌ Performance benchmark failed: {e}")
        
        # Save benchmark results
        try:
            with open("benchmark_results.json", "w", encoding="utf-8") as f:
                json.dump(benchmark_results, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"Failed to save benchmark results: {e}")
        
        return benchmark_results
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get summary of collected metrics."""
        if not self.metrics_history:
            return {"message": "No metrics collected yet"}
        
        successful_ops = [m for m in self.metrics_history if m.success]
        failed_ops = [m for m in self.metrics_history if not m.success]
        
        summary = {
            "total_operations": len(self.metrics_history),
            "successful_operations": len(successful_ops),
            "failed_operations": len(failed_ops),
            "success_rate_percent": (len(successful_ops) / len(self.metrics_history)) * 100,
            "performance": {}
        }
        
        if successful_ops:
            durations = [m.duration_seconds for m in successful_ops if m.duration_seconds]
            memory_usage = [m.memory_usage_mb for m in successful_ops if m.memory_usage_mb]
            
            if durations:
                summary["performance"]["avg_duration_seconds"] = sum(durations) / len(durations)
                summary["performance"]["min_duration_seconds"] = min(durations)
                summary["performance"]["max_duration_seconds"] = max(durations)
            
            if memory_usage:
                summary["performance"]["avg_memory_mb"] = sum(memory_usage) / len(memory_usage)
                summary["performance"]["peak_memory_mb"] = max(memory_usage)
        
        return summary


def load_monitoring_config() -> MonitoringConfig:
    """Load monitoring configuration from environment variables."""
    return MonitoringConfig(
        health_check_interval=int(os.getenv("MONITOR_HEALTH_INTERVAL", "30")),
        health_check_timeout=int(os.getenv("MONITOR_HEALTH_TIMEOUT", "10")),
        enable_performance_monitoring=os.getenv("MONITOR_PERFORMANCE", "true").lower() == "true",
        performance_log_file=os.getenv("MONITOR_PERFORMANCE_LOG", "performance.jsonl"),
        benchmark_large_repo_threshold_mb=float(os.getenv("MONITOR_LARGE_REPO_THRESHOLD", "100.0")),
        enable_alerting=os.getenv("MONITOR_ENABLE_ALERTS", "false").lower() == "true",
        webhook_url=os.getenv("MONITOR_WEBHOOK_URL"),
        smtp_server=os.getenv("MONITOR_SMTP_SERVER"),
        smtp_port=int(os.getenv("MONITOR_SMTP_PORT", "587")),
        email_from=os.getenv("MONITOR_EMAIL_FROM"),
        email_to=os.getenv("MONITOR_EMAIL_TO"),
        email_password=os.getenv("MONITOR_EMAIL_PASSWORD"),
        max_memory_usage_mb=float(os.getenv("MONITOR_MAX_MEMORY_MB", "2048.0")),
        max_processing_time_minutes=float(os.getenv("MONITOR_MAX_TIME_MIN", "60.0")),
        max_error_rate_percent=float(os.getenv("MONITOR_MAX_ERROR_RATE", "10.0")),
        collect_system_metrics=os.getenv("MONITOR_SYSTEM_METRICS", "true").lower() == "true",
        metrics_retention_days=int(os.getenv("MONITOR_RETENTION_DAYS", "30"))
    )


def main():
    """CLI for monitoring operations."""
    import argparse
    
    parser = argparse.ArgumentParser(description="MonoAgent Monitoring and Benchmarking")
    parser.add_argument("--health-check", action="store_true", 
                       help="Run health check")
    parser.add_argument("--benchmark", action="store_true",
                       help="Run performance benchmark")
    parser.add_argument("--test-repo", type=str,
                       help="Test repository URL for benchmarking")
    parser.add_argument("--metrics-summary", action="store_true",
                       help="Show metrics summary")
    
    args = parser.parse_args()
    
    config = load_monitoring_config()
    monitor = MonitoringAgent(config)
    
    if args.health_check:
        health = monitor.health_check()
        print(json.dumps(health, indent=2))
        exit(0 if health["status"] == "healthy" else 1)
    
    if args.benchmark:
        results = monitor.run_performance_benchmark(args.test_repo)
        print(json.dumps(results, indent=2))
        exit(0 if results["status"] == "completed" else 1)
    
    if args.metrics_summary:
        summary = monitor.get_metrics_summary()
        print(json.dumps(summary, indent=2))
        exit(0)
    
    parser.print_help()


if __name__ == "__main__":
    main()
