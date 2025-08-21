#!/usr/bin/env python3
"""
MonoAgent Performance Benchmarking Suite

Comprehensive performance testing and benchmarking for MonoAgent operations.
This module provides standardized benchmarks to ensure consistent performance
across different environments and identify performance regressions.
"""

import argparse
import json
import logging
import os
import tempfile
import time
from typing import Dict, List, Any, Optional
import subprocess
import shutil

# Try to import monitoring and error handling modules
try:
    from monitoring import MonitoringAgent, MonitoringConfig
    from error_handling import ErrorHandler, retry_on_failure, validate_inputs
    MONITORING_AVAILABLE = True
except ImportError:
    MONITORING_AVAILABLE = False
    print("⚠️  Monitoring modules not available, running basic benchmarks only")


class BenchmarkSuite:
    """Comprehensive benchmarking suite for MonoAgent."""
    
    def __init__(self, config: Optional[dict] = None):
        self.config = config or {}
        self.logger = self._setup_logging()
        self.results: List[Dict[str, Any]] = []
        
        if MONITORING_AVAILABLE:
            monitor_config = MonitoringConfig()
            self.monitor = MonitoringAgent(monitor_config)
            self.error_handler = ErrorHandler(self.logger)
        else:
            self.monitor = None
            self.error_handler = None
    
    def _setup_logging(self) -> logging.Logger:
        """Set up logging for benchmarks."""
        logger = logging.getLogger("monoagent.benchmark")
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def run_all_benchmarks(self) -> Dict[str, Any]:
        """Run all available benchmarks."""
        self.logger.info("🚀 Starting comprehensive MonoAgent benchmark suite...")
        
        suite_start = time.time()
        benchmarks = [
            ("System Information", self.benchmark_system_info),
            ("Import Performance", self.benchmark_import_performance),
            ("Configuration Loading", self.benchmark_config_loading),
            ("Git Operations", self.benchmark_git_operations),
            ("File System Operations", self.benchmark_filesystem_operations),
            ("Memory Usage", self.benchmark_memory_usage),
            ("Error Handling", self.benchmark_error_handling),
            ("Repository Analysis", self.benchmark_repo_analysis),
        ]
        
        results = {
            "benchmark_suite": "MonoAgent Performance",
            "timestamp": time.time(),
            "total_benchmarks": len(benchmarks),
            "benchmarks": {},
            "summary": {}
        }
        
        successful_benchmarks = 0
        failed_benchmarks = 0
        
        for name, benchmark_func in benchmarks:
            self.logger.info(f"📊 Running benchmark: {name}")
            try:
                benchmark_result = benchmark_func()
                results["benchmarks"][name] = benchmark_result
                successful_benchmarks += 1
                self.logger.info(f"✅ {name} completed successfully")
            except Exception as e:
                self.logger.error(f"❌ {name} failed: {e}")
                results["benchmarks"][name] = {
                    "status": "failed",
                    "error": str(e),
                    "timestamp": time.time()
                }
                failed_benchmarks += 1
        
        suite_duration = time.time() - suite_start
        
        results["summary"] = {
            "total_duration_seconds": suite_duration,
            "successful_benchmarks": successful_benchmarks,
            "failed_benchmarks": failed_benchmarks,
            "success_rate": (successful_benchmarks / len(benchmarks)) * 100
        }
        
        self.logger.info(
            f"🏁 Benchmark suite completed in {suite_duration:.2f}s "
            f"({successful_benchmarks}/{len(benchmarks)} successful)"
        )
        
        # Save results
        self._save_results(results)
        
        return results
    
    def benchmark_system_info(self) -> Dict[str, Any]:
        """Benchmark: System information and capabilities."""
        import platform
        import sys
        
        try:
            import psutil
            memory_info = psutil.virtual_memory()
            disk_info = psutil.disk_usage('/')
            cpu_count = psutil.cpu_count()
        except ImportError:
            memory_info = None
            disk_info = None
            cpu_count = None
        
        return {
            "status": "completed",
            "timestamp": time.time(),
            "system": {
                "platform": platform.platform(),
                "python_version": sys.version,
                "architecture": platform.architecture(),
                "processor": platform.processor(),
                "memory_total_gb": memory_info.total / 1024**3 if memory_info else None,
                "disk_total_gb": disk_info.total / 1024**3 if disk_info else None,
                "cpu_count": cpu_count
            }
        }
    
    def benchmark_import_performance(self) -> Dict[str, Any]:
        """Benchmark: Module import performance."""
        imports_to_test = [
            "split_repo_agent",
            "json",
            "os",
            "subprocess",
            "tempfile",
            "logging"
        ]
        
        results = {
            "status": "completed",
            "timestamp": time.time(),
            "imports": {}
        }
        
        for module_name in imports_to_test:
            start_time = time.time()
            try:
                __import__(module_name)
                import_time = time.time() - start_time
                results["imports"][module_name] = {
                    "success": True,
                    "time_seconds": import_time
                }
            except ImportError as e:
                results["imports"][module_name] = {
                    "success": False,
                    "error": str(e),
                    "time_seconds": time.time() - start_time
                }
        
        total_import_time = sum(
            imp["time_seconds"] for imp in results["imports"].values()
        )
        results["total_import_time_seconds"] = total_import_time
        
        return results
    
    def benchmark_config_loading(self) -> Dict[str, Any]:
        """Benchmark: Configuration loading performance."""
        try:
            import split_repo_agent
        except ImportError:
            return {
                "status": "failed",
                "error": "split_repo_agent module not available",
                "timestamp": time.time()
            }
        
        configs_to_test = [
            {
                "name": "minimal_config",
                "config": {
                    "source_repo_url": "https://github.com/test/repo.git",
                    "org": "test",
                    "github_token": "dummy"
                }
            },
            {
                "name": "full_config", 
                "config": {
                    "source_repo_url": "https://github.com/test/repo.git",
                    "org": "test",
                    "github_token": "dummy",
                    "dry_run": True,
                    "analyze_only": True,
                    "force": False,
                    "visualize": True,
                    "mode": "auto",
                    "private_repos": False,
                    "provider": "github"
                }
            }
        ]
        
        results = {
            "status": "completed",
            "timestamp": time.time(),
            "configurations": {}
        }
        
        for test in configs_to_test:
            start_time = time.time()
            try:
                config = split_repo_agent.RepoSplitterConfig(**test["config"])
                load_time = time.time() - start_time
                results["configurations"][test["name"]] = {
                    "success": True,
                    "time_seconds": load_time,
                    "config_size": len(str(config))
                }
            except Exception as e:
                results["configurations"][test["name"]] = {
                    "success": False,
                    "error": str(e),
                    "time_seconds": time.time() - start_time
                }
        
        return results
    
    def benchmark_git_operations(self) -> Dict[str, Any]:
        """Benchmark: Basic Git operations performance."""
        results = {
            "status": "completed",
            "timestamp": time.time(),
            "operations": {}
        }
        
        # Test git availability
        start_time = time.time()
        try:
            result = subprocess.run(
                ['git', '--version'], 
                capture_output=True, text=True, timeout=10
            )
            git_check_time = time.time() - start_time
            git_available = result.returncode == 0
            git_version = result.stdout.strip() if git_available else None
        except Exception as e:
            git_check_time = time.time() - start_time
            git_available = False
            git_version = None
        
        results["operations"]["git_version_check"] = {
            "success": git_available,
            "time_seconds": git_check_time,
            "version": git_version
        }
        
        if not git_available:
            results["status"] = "failed"
            results["error"] = "Git not available"
            return results
        
        # Test git init in temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            start_time = time.time()
            try:
                subprocess.run(
                    ['git', 'init'], 
                    cwd=temp_dir, 
                    capture_output=True, 
                    check=True,
                    timeout=30
                )
                git_init_time = time.time() - start_time
                results["operations"]["git_init"] = {
                    "success": True,
                    "time_seconds": git_init_time
                }
            except Exception as e:
                results["operations"]["git_init"] = {
                    "success": False,
                    "error": str(e),
                    "time_seconds": time.time() - start_time
                }
        
        return results
    
    def benchmark_filesystem_operations(self) -> Dict[str, Any]:
        """Benchmark: File system operations performance."""
        results = {
            "status": "completed",
            "timestamp": time.time(),
            "operations": {}
        }
        
        # Test file creation
        with tempfile.TemporaryDirectory() as temp_dir:
            # Write test
            start_time = time.time()
            try:
                test_file = os.path.join(temp_dir, "test_file.txt")
                test_content = "Test content " * 1000  # ~12KB file
                with open(test_file, 'w') as f:
                    f.write(test_content)
                write_time = time.time() - start_time
                results["operations"]["file_write"] = {
                    "success": True,
                    "time_seconds": write_time,
                    "file_size_bytes": len(test_content.encode())
                }
            except Exception as e:
                results["operations"]["file_write"] = {
                    "success": False,
                    "error": str(e),
                    "time_seconds": time.time() - start_time
                }
            
            # Read test
            start_time = time.time()
            try:
                with open(test_file, 'r') as f:
                    read_content = f.read()
                read_time = time.time() - start_time
                results["operations"]["file_read"] = {
                    "success": True,
                    "time_seconds": read_time,
                    "content_matches": read_content == test_content
                }
            except Exception as e:
                results["operations"]["file_read"] = {
                    "success": False,
                    "error": str(e),
                    "time_seconds": time.time() - start_time
                }
            
            # Directory operations
            start_time = time.time()
            try:
                subdir = os.path.join(temp_dir, "subdir")
                os.makedirs(subdir)
                dir_time = time.time() - start_time
                results["operations"]["directory_create"] = {
                    "success": True,
                    "time_seconds": dir_time
                }
            except Exception as e:
                results["operations"]["directory_create"] = {
                    "success": False,
                    "error": str(e),
                    "time_seconds": time.time() - start_time
                }
        
        return results
    
    def benchmark_memory_usage(self) -> Dict[str, Any]:
        """Benchmark: Memory usage patterns."""
        try:
            import psutil
            import gc
        except ImportError:
            return {
                "status": "failed",
                "error": "psutil not available",
                "timestamp": time.time()
            }
        
        process = psutil.Process()
        
        # Initial memory
        gc.collect()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        results = {
            "status": "completed",
            "timestamp": time.time(),
            "initial_memory_mb": initial_memory,
            "operations": {}
        }
        
        # Test memory allocation
        start_time = time.time()
        try:
            # Allocate some memory (10MB string)
            large_string = "x" * (10 * 1024 * 1024)
            allocation_time = time.time() - start_time
            
            current_memory = process.memory_info().rss / 1024 / 1024
            memory_increase = current_memory - initial_memory
            
            results["operations"]["memory_allocation"] = {
                "success": True,
                "time_seconds": allocation_time,
                "memory_increase_mb": memory_increase,
                "allocated_size_mb": 10
            }
            
            # Clean up
            del large_string
            gc.collect()
            
        except Exception as e:
            results["operations"]["memory_allocation"] = {
                "success": False,
                "error": str(e),
                "time_seconds": time.time() - start_time
            }
        
        # Final memory after cleanup
        final_memory = process.memory_info().rss / 1024 / 1024
        results["final_memory_mb"] = final_memory
        results["memory_cleanup_efficiency"] = (current_memory - final_memory) / memory_increase if 'memory_increase' in locals() else 0
        
        return results
    
    def benchmark_error_handling(self) -> Dict[str, Any]:
        """Benchmark: Error handling performance."""
        if not MONITORING_AVAILABLE or not self.error_handler:
            return {
                "status": "skipped",
                "reason": "Error handling modules not available",
                "timestamp": time.time()
            }
        
        results = {
            "status": "completed",
            "timestamp": time.time(),
            "operations": {}
        }
        
        # Test exception creation and handling
        start_time = time.time()
        try:
            from error_handling import MonoAgentError, ErrorContext, ErrorSeverity
            
            context = ErrorContext(operation="test", severity=ErrorSeverity.MEDIUM)
            error = MonoAgentError("Test error", context)
            error_dict = error.to_dict()
            
            exception_time = time.time() - start_time
            results["operations"]["exception_creation"] = {
                "success": True,
                "time_seconds": exception_time,
                "context_size": len(str(error_dict))
            }
        except Exception as e:
            results["operations"]["exception_creation"] = {
                "success": False,
                "error": str(e),
                "time_seconds": time.time() - start_time
            }
        
        # Test retry mechanism
        start_time = time.time()
        try:
            retry_count = 0
            
            @retry_on_failure(max_retries=3, backoff_factor=0.1)
            def failing_function():
                nonlocal retry_count
                retry_count += 1
                if retry_count < 3:
                    raise ValueError("Simulated failure")
                return "success"
            
            result = failing_function()
            retry_time = time.time() - start_time
            
            results["operations"]["retry_mechanism"] = {
                "success": True,
                "time_seconds": retry_time,
                "retry_count": retry_count,
                "result": result
            }
        except Exception as e:
            results["operations"]["retry_mechanism"] = {
                "success": False,
                "error": str(e),
                "time_seconds": time.time() - start_time
            }
        
        return results
    
    def benchmark_repo_analysis(self) -> Dict[str, Any]:
        """Benchmark: Repository analysis simulation."""
        try:
            import split_repo_agent
        except ImportError:
            return {
                "status": "failed",
                "error": "split_repo_agent module not available",
                "timestamp": time.time()
            }
        
        results = {
            "status": "completed",
            "timestamp": time.time(),
            "operations": {}
        }
        
        # Simulate project detection
        start_time = time.time()
        try:
            # Create temporary directory structure
            with tempfile.TemporaryDirectory() as temp_dir:
                # Create fake project structure
                projects = ["frontend", "backend", "api", "shared"]
                for project in projects:
                    project_dir = os.path.join(temp_dir, project)
                    os.makedirs(project_dir)
                    
                    # Add some files
                    with open(os.path.join(project_dir, "package.json"), "w") as f:
                        json.dump({"name": project, "version": "1.0.0"}, f)
                    
                    with open(os.path.join(project_dir, "README.md"), "w") as f:
                        f.write(f"# {project}\n\nDescription of {project} project.")
                
                analysis_time = time.time() - start_time
                results["operations"]["project_structure_creation"] = {
                    "success": True,
                    "time_seconds": analysis_time,
                    "projects_created": len(projects),
                    "files_created": len(projects) * 2
                }
        
        except Exception as e:
            results["operations"]["project_structure_creation"] = {
                "success": False,
                "error": str(e),
                "time_seconds": time.time() - start_time
            }
        
        return results
    
    def _save_results(self, results: Dict[str, Any]):
        """Save benchmark results to file."""
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"benchmark_results_{timestamp}.json"
        
        try:
            with open(filename, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            self.logger.info(f"📄 Benchmark results saved to: {filename}")
        except Exception as e:
            self.logger.error(f"Failed to save benchmark results: {e}")
    
    def generate_performance_report(self, results: Dict[str, Any]) -> str:
        """Generate human-readable performance report."""
        report = []
        report.append("=" * 60)
        report.append("MONOAGENT PERFORMANCE BENCHMARK REPORT")
        report.append("=" * 60)
        report.append("")
        
        # Summary
        summary = results.get("summary", {})
        report.append(f"Total Benchmarks: {summary.get('total_benchmarks', 'N/A')}")
        report.append(f"Successful: {summary.get('successful_benchmarks', 'N/A')}")
        report.append(f"Failed: {summary.get('failed_benchmarks', 'N/A')}")
        report.append(f"Success Rate: {summary.get('success_rate', 'N/A'):.1f}%")
        report.append(f"Total Duration: {summary.get('total_duration_seconds', 'N/A'):.2f}s")
        report.append("")
        
        # Individual benchmark results
        for name, result in results.get("benchmarks", {}).items():
            report.append(f"📊 {name}")
            report.append("-" * 40)
            
            if result.get("status") == "failed":
                report.append(f"❌ FAILED: {result.get('error', 'Unknown error')}")
            else:
                report.append("✅ PASSED")
                
                # Add specific metrics based on benchmark type
                if "operations" in result:
                    for op_name, op_result in result["operations"].items():
                        if op_result.get("success"):
                            time_s = op_result.get("time_seconds", 0)
                            report.append(f"  • {op_name}: {time_s:.3f}s")
                        else:
                            report.append(f"  • {op_name}: FAILED")
            
            report.append("")
        
        # Performance recommendations
        report.append("💡 PERFORMANCE RECOMMENDATIONS")
        report.append("-" * 40)
        
        # Analyze results for recommendations
        slow_operations = []
        for name, result in results.get("benchmarks", {}).items():
            if "operations" in result:
                for op_name, op_result in result["operations"].items():
                    time_s = op_result.get("time_seconds", 0)
                    if time_s > 1.0:  # Operations taking more than 1 second
                        slow_operations.append(f"{name}.{op_name}: {time_s:.2f}s")
        
        if slow_operations:
            report.append("⚠️  Slow operations detected:")
            for op in slow_operations:
                report.append(f"  • {op}")
        else:
            report.append("✅ All operations performed within acceptable time limits")
        
        report.append("")
        report.append("=" * 60)
        
        return "\n".join(report)


def main():
    """CLI for benchmark operations."""
    parser = argparse.ArgumentParser(description="MonoAgent Performance Benchmarking")
    parser.add_argument("--run-all", action="store_true",
                       help="Run all benchmarks")
    parser.add_argument("--save-report", action="store_true",
                       help="Save human-readable report")
    parser.add_argument("--config", type=str,
                       help="Path to benchmark configuration file")
    
    args = parser.parse_args()
    
    # Load config if provided
    config = {}
    if args.config and os.path.exists(args.config):
        with open(args.config, 'r') as f:
            config = json.load(f)
    
    benchmark_suite = BenchmarkSuite(config)
    
    if args.run_all:
        results = benchmark_suite.run_all_benchmarks()
        
        if args.save_report:
            report = benchmark_suite.generate_performance_report(results)
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            report_filename = f"benchmark_report_{timestamp}.txt"
            with open(report_filename, 'w') as f:
                f.write(report)
            print(f"📄 Performance report saved to: {report_filename}")
        
        # Print summary
        print("\n" + benchmark_suite.generate_performance_report(results))
        
        # Exit with appropriate code
        success_rate = results.get("summary", {}).get("success_rate", 0)
        exit(0 if success_rate > 80 else 1)
    
    parser.print_help()


if __name__ == "__main__":
    main()
