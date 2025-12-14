#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TORQ Console Demo Generator
Creates comprehensive demonstrations of all ML Systems Hardening features
"""

import json
import time
import random
from datetime import datetime, timedelta
from typing import Dict, List, Any
import matplotlib.pyplot as plt
import pandas as pd
import sys

# Set UTF-8 encoding for Windows
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
    sys.stdin = codecs.getreader("utf-8")(sys.stdin.detach())

class TORQDemoGenerator:
    def __init__(self):
        self.start_time = datetime.now()

    def generate_telemetry_trace(self) -> Dict[str, Any]:
        """Generate realistic telemetry trace data"""
        trace_id = f"trace_{int(time.time())}_{random.randint(1000, 9999)}"

        return {
            "trace_id": trace_id,
            "timestamp": datetime.now().isoformat(),
            "tool_execution": {
                "tool_name": random.choice(["read_file", "write_file", "analyze_code", "run_test"]),
                "parameters": {
                    "path": f"/workspace/{random.choice(['config.json', 'main.py', 'test.js', 'data.csv'])}",
                    "options": {"timeout": random.randint(5, 30)}
                },
                "duration_ms": random.randint(20, 150),
                "status": random.choice(["SUCCESS", "SUCCESS", "SUCCESS", "TIMEOUT", "ERROR"]),
                "memory_usage_mb": round(random.uniform(1.5, 8.2), 2),
                "cpu_usage_percent": round(random.uniform(5, 25), 1),
                "context_id": f"ctx_{random.randint(100000, 999999)}"
            },
            "system_metrics": {
                "uptime_seconds": random.randint(3600, 86400),
                "total_requests": random.randint(1000, 5000),
                "active_connections": random.randint(10, 100),
                "error_rate": round(random.uniform(0.001, 0.05), 4)
            }
        }

    def generate_evaluation_results(self) -> Dict[str, Any]:
        """Generate comprehensive evaluation results"""
        test_suites = [
            "Code Quality", "Performance", "Security", "Functionality",
            "Documentation", "Test Coverage", "Memory Safety"
        ]

        results = {}
        total_score = 0
        total_duration = 0

        for suite in test_suites:
            score = round(random.uniform(85, 99), 1)
            duration = round(random.uniform(1.2, 8.5), 1)
            status = "PASS" if score >= 90 else "NEEDS_IMPROVEMENT"

            results[suite.lower().replace(" ", "_")] = {
                "score": score,
                "duration": duration,
                "status": status,
                "tests_run": random.randint(20, 150),
                "tests_passed": random.randint(18, 150)
            }

            total_score += score
            total_duration += duration

        return {
            "evaluation_id": f"eval_{int(time.time())}",
            "timestamp": datetime.now().isoformat(),
            "results": results,
            "overall_score": round(total_score / len(test_suites), 1),
            "total_duration": round(total_duration, 1),
            "status": "PASS" if total_score / len(test_suites) >= 90 else "NEEDS_IMPROVEMENT"
        }

    def generate_policy_rules(self) -> Dict[str, Any]:
        """Generate policy-driven routing rules"""
        return {
            "policy_version": "2.1.0",
            "last_updated": datetime.now().isoformat(),
            "rules": {
                "slo_compliance": {
                    "enabled": True,
                    "conditions": {
                        "response_time_ms": 100,
                        "error_rate_threshold": 0.01,
                        "memory_usage_mb": 512
                    },
                    "actions": {
                        "on_violation": "route_to_backup",
                        "escalation": "alert_team"
                    }
                },
                "security_context": {
                    "enabled": True,
                    "authentication": {
                        "required": True,
                        "methods": ["api_key", "oauth2"],
                        "timeout": 300
                    },
                    "authorization": {
                        "allowed_tools": ["read", "write", "list", "analyze"],
                        "restricted_paths": ["/etc", "/root", "/system"],
                        "action": "allow_with_audit"
                    }
                },
                "resource_limits": {
                    "enabled": True,
                    "limits": {
                        "memory_mb": 512,
                        "cpu_percent": 50,
                        "timeout_seconds": 30,
                        "max_file_size_mb": 100
                    },
                    "enforcement": "strict",
                    "action": "deny_if_exceeded"
                },
                "circuit_breaker": {
                    "enabled": True,
                    "threshold": {
                        "error_rate": 0.05,
                        "timeout_seconds": 60
                    },
                    "recovery": {
                        "half_open_requests": 3,
                        "success_threshold": 2
                    }
                }
            },
            "routing_table": {
                "primary_route": {
                    "endpoint": "https://api.torq.primary",
                    "weight": 80,
                    "health_check": "/health"
                },
                "backup_route": {
                    "endpoint": "https://api.torq.backup",
                    "weight": 20,
                    "health_check": "/health"
                }
            }
        }

    def generate_performance_metrics(self) -> Dict[str, Any]:
        """Generate performance optimization metrics"""
        return {
            "timestamp": datetime.now().isoformat(),
            "metrics": {
                "latency": {
                    "p50": round(random.uniform(40, 60), 1),
                    "p95": round(random.uniform(80, 120), 1),
                    "p99": round(random.uniform(150, 250), 1),
                    "target_p95": 100
                },
                "throughput": {
                    "current_rps": random.randint(800, 1500),
                    "peak_rps": random.randint(1200, 2000),
                    "target_rps": 1000,
                    "improvement_factor": round(random.uniform(1.5, 3.0), 1)
                },
                "resource_usage": {
                    "memory_usage_mb": random.randint(150, 300),
                    "memory_limit_mb": 512,
                    "cpu_usage_percent": random.randint(15, 40),
                    "disk_io_mb_per_sec": random.randint(10, 50)
                },
                "error_rates": {
                    "current_error_rate": round(random.uniform(0.001, 0.02), 4),
                    "target_error_rate": 0.01,
                    "timeout_rate": round(random.uniform(0.0001, 0.005), 4)
                },
                "optimization_results": {
                    "memory_reduction_percent": random.randint(30, 55),
                    "latency_improvement_percent": random.randint(25, 45),
                    "throughput_increase_factor": round(random.uniform(1.8, 2.5), 1)
                }
            }
        }

    def generate_sandbox_security_audit(self) -> Dict[str, Any]:
        """Generate security audit results for tool sandbox"""
        security_tests = [
            ("Resource Isolation", "PASSED", "Container boundaries verified"),
            ("Input Validation", "PASSED", "All inputs properly sanitized"),
            ("Output Sanitization", "PASSED", "Output filtering working"),
            ("Privilege Escalation", "BLOCKED", "Elevation attempts prevented"),
            ("Memory Safety", "VERIFIED", "No memory leaks detected"),
            ("File System Access", "RESTRICTED", "Access properly limited"),
            ("Network Access", "CONTROLLED", "External connections filtered"),
            ("Time-based Limits", "ENFORCED", "Execution timeouts working"),
            ("Process Monitoring", "ACTIVE", "Real-time monitoring enabled"),
            ("Audit Logging", "COMPLETE", "All actions logged")
        ]

        return {
            "audit_id": f"audit_{int(time.time())}",
            "timestamp": datetime.now().isoformat(),
            "sandbox_version": "1.5.2",
            "tests": [
                {
                    "name": test_name,
                    "status": status,
                    "details": details,
                    "severity": "HIGH" if status == "BLOCKED" else "MEDIUM"
                }
                for test_name, status, details in security_tests
            ],
            "overall_status": "SECURE",
            "security_score": 96.7,
            "vulnerabilities_found": 0,
            "recommendations": [
                "Continue monitoring for new attack vectors",
                "Regular security updates recommended",
                "Consider additional network segmentation"
            ]
        }

    def generate_slo_dashboard_data(self, hours: int = 24) -> Dict[str, Any]:
        """Generate SLO dashboard time series data"""
        timestamps = []
        response_times = []
        error_rates = []
        throughput = []

        for i in range(hours):
            timestamp = datetime.now() - timedelta(hours=hours-i)
            timestamps.append(timestamp.strftime("%H:%M"))

            # Simulate realistic patterns with some variation
            base_response_time = 80 + 20 * (0.5 + 0.5 * (i % 12) / 12)
            response_times.append(base_response_time + random.uniform(-10, 15))

            error_rate = 0.005 + 0.003 * (i % 8) / 8
            error_rates.append(error_rate + random.uniform(-0.002, 0.003))

            base_throughput = 1000 + 500 * (0.5 + 0.5 * (i % 24) / 24)
            throughput.append(base_throughput + random.randint(-200, 300))

        return {
            "time_series": {
                "timestamps": timestamps,
                "metrics": {
                    "response_time_p95": response_times,
                    "error_rate": error_rates,
                    "throughput_rpm": throughput
                }
            },
            "current_slo_status": {
                "response_time_compliance": 99.8,
                "error_rate_compliance": 99.9,
                "throughput_compliance": 100.0,
                "overall_compliance": 99.9
            },
            "targets": {
                "response_time_p95_ms": 100,
                "error_rate_percent": 1.0,
                "throughput_rpm": 1000
            }
        }

    def save_demo_data(self, filename: str, data: Dict[str, Any]):
        """Save demo data to JSON file"""
        with open(f"E:\\TORQ-CONSOLE\\{filename}", 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, default=str, ensure_ascii=False)
        print(f"✓ Generated {filename}")

    def create_performance_chart(self):
        """Create performance comparison chart"""
        try:
            # Set matplotlib to use a non-interactive backend
            import matplotlib
            matplotlib.use('Agg')

            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 8))
            fig.suptitle('TORQ Console Performance Metrics', fontsize=16, fontweight='bold')

            # Response Time Comparison
            before = [156, 145, 167, 142, 158, 151]
            after = [87, 82, 91, 79, 88, 85]
            ax1.plot(before, 'r-', label='Before Optimization', marker='o')
            ax1.plot(after, 'g-', label='After Optimization', marker='s')
            ax1.set_title('Response Time (ms)')
            ax1.legend()
            ax1.grid(True, alpha=0.3)

            # Memory Usage
            memory_before = [384, 412, 398, 405, 391, 387]
            memory_after = [198, 205, 192, 201, 195, 188]
            ax2.plot(memory_before, 'r-', label='Before', marker='o')
            ax2.plot(memory_after, 'g-', label='After', marker='s')
            ax2.set_title('Memory Usage (MB)')
            ax2.legend()
            ax2.grid(True, alpha=0.3)

            # Throughput
            throughput_before = [680, 720, 690, 710, 705, 695]
            throughput_after = [1247, 1320, 1280, 1310, 1295, 1305]
            ax3.plot(throughput_before, 'r-', label='Before', marker='o')
            ax3.plot(throughput_after, 'g-', label='After', marker='s')
            ax3.set_title('Throughput (req/min)')
            ax3.legend()
            ax3.grid(True, alpha=0.3)

            # Error Rate
            error_before = [0.85, 0.92, 0.78, 0.88, 0.83, 0.90]
            error_after = [0.08, 0.12, 0.05, 0.09, 0.07, 0.11]
            ax4.plot(error_before, 'r-', label='Before', marker='o')
            ax4.plot(error_after, 'g-', label='After', marker='s')
            ax4.set_title('Error Rate (%)')
            ax4.legend()
            ax4.grid(True, alpha=0.3)

            plt.tight_layout()
            plt.savefig('E:\\TORQ-CONSOLE\\performance_comparison.png', dpi=300, bbox_inches='tight')
            plt.close()
            print("✓ Generated performance_comparison.png")
        except Exception as e:
            print(f"⚠ Could not generate performance chart: {e}")

    def generate_all_demo_data(self):
        """Generate all demo data files"""
        print("Generating TORQ Console Demo Data...")

        # Generate all demo data
        telemetry_data = self.generate_telemetry_trace()
        evaluation_data = self.generate_evaluation_results()
        policy_data = self.generate_policy_rules()
        performance_data = self.generate_performance_metrics()
        security_audit = self.generate_sandbox_security_audit()
        slo_data = self.generate_slo_dashboard_data()

        # Save all data files
        self.save_demo_data("demo_telemetry_trace.json", telemetry_data)
        self.save_demo_data("demo_evaluation_results.json", evaluation_data)
        self.save_demo_data("demo_policy_rules.json", policy_data)
        self.save_demo_data("demo_performance_metrics.json", performance_data)
        self.save_demo_data("demo_security_audit.json", security_audit)
        self.save_demo_data("demo_slo_dashboard.json", slo_data)

        # Create performance chart
        self.create_performance_chart()

        # Generate CLI demo commands
        cli_commands = [
            {
                "command": "torq telemetry status",
                "output": [
                    "✅ Telemetry System: ONLINE",
                    "   - Active Traces: 1,247",
                    "   - Average Latency: 1.2ms",
                    "   - Memory Usage: 128MB / 512MB",
                    "   - Uptime: 99.8%"
                ]
            },
            {
                "command": "torq evaluate run --suite=\"full\"",
                "output": [
                    "Running evaluation suite...",
                    "✅ Code Quality: 94.5% (PASS)",
                    "✅ Performance: 98.2% (PASS)",
                    "✅ Security: 91.7% (PASS)",
                    "Overall Score: 95.3% - EXCELLENT"
                ]
            },
            {
                "command": "torq slo dashboard",
                "output": [
                    "SLO Dashboard - Last 24h",
                    "   - Response Time P95: 94ms (Target: 100ms)",
                    "   - Error Rate: 0.08% (Target: 1.0%)",
                    "   - Throughput: 1,247 req/min (Target: 1,000)",
                    "   - SLO Compliance: 99.9%"
                ]
            }
        ]

        self.save_demo_data("demo_cli_commands.json", {"commands": cli_commands})

        print("\nAll demo data generated successfully!")
        print("Files created in E:\\TORQ-CONSOLE\\")
        print("\nGenerated files:")
        print("  - torq_landing.html (Main landing page)")
        print("  - demo_telemetry_trace.json")
        print("  - demo_evaluation_results.json")
        print("  - demo_policy_rules.json")
        print("  - demo_performance_metrics.json")
        print("  - demo_security_audit.json")
        print("  - demo_slo_dashboard.json")
        print("  - demo_cli_commands.json")
        print("  - performance_comparison.png")

if __name__ == "__main__":
    # Install required packages
    try:
        import matplotlib.pyplot as plt
        import pandas as pd
    except ImportError:
        print("Installing required packages...")
        import subprocess
        subprocess.check_call(["pip", "install", "matplotlib", "pandas"])
        import matplotlib.pyplot as plt
        import pandas as pd

    # Generate demo data
    demo = TORQDemoGenerator()
    demo.generate_all_demo_data()