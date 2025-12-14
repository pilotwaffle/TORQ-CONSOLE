#!/usr/bin/env python3
"""
TORQ Console Validation Script
Tests what users can ACTUALLY do with TORQ Console
"""

import subprocess
import sys
import os
import time
import json
import requests
from pathlib import Path
import importlib.util

class TORQValidator:
    def __init__(self):
        self.results = {
            "installation": {},
            "cli_commands": {},
            "web_interface": {},
            "ml_systems": {},
            "marvin_integration": {},
            "file_operations": {}
        }
        self.base_dir = Path(__file__).parent
        self.torq_installed = False

    def log(self, category, test, status, details=None):
        """Log validation result"""
        self.results[category][test] = {
            "status": status,
            "details": details
        }
        symbol = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{symbol} [{category}] {test}: {status}")
        if details:
            print(f"   └─ {details}")

    def run_command(self, cmd, timeout=30):
        """Run command and capture output"""
        try:
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True,
                timeout=timeout, cwd=self.base_dir
            )
            return result.returncode == 0, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return False, "", "Command timed out"
        except Exception as e:
            return False, "", str(e)

    def test_installation(self):
        """Test if TORQ Console is properly installed"""
        print("\n🔍 TESTING INSTALLATION")
        print("=" * 50)

        # Check if package is installed
        try:
            import torq_console
            version = getattr(torq_console, '__version__', 'unknown')
            self.log("installation", "package_import", "PASS", f"Version: {version}")
            self.torq_installed = True
        except ImportError as e:
            self.log("installation", "package_import", "FAIL", str(e))
            return

        # Check CLI command
        success, stdout, stderr = self.run_command("torq-console --help")
        if success:
            self.log("installation", "cli_help", "PASS", "CLI command accessible")
        else:
            self.log("installation", "cli_help", "FAIL", stderr[:100])

    def test_core_cli_commands(self):
        """Test core CLI commands mentioned in README"""
        print("\n🔍 TESTING CORE CLI COMMANDS")
        print("=" * 50)

        if not self.torq_installed:
            self.log("cli_commands", "all_commands", "SKIP", "Package not installed")
            return

        commands_to_test = [
            ("torq-console --version", "version_check"),
            ("torq-console status", "status_command"),
            ("torq telemetry --compliance", "telemetry_compliance"),
            ("torq eval run --set v1.0 --seed 42", "eval_run"),
            ("torq bench run", "bench_run"),
        ]

        for cmd, test_name in commands_to_test:
            print(f"\nTesting: {cmd}")
            success, stdout, stderr = self.run_command(cmd, timeout=60)

            if success:
                self.log("cli_commands", test_name, "PASS", f"Output length: {len(stdout)} chars")
                # Save important outputs
                if test_name == "eval_run":
                    self.save_eval_output(stdout)
            else:
                self.log("cli_commands", test_name, "FAIL", stderr[:200] if stderr else "No error output")

    def test_web_interface(self):
        """Test if web interface starts and is accessible"""
        print("\n🔍 TESTING WEB INTERFACE")
        print("=" * 50)

        # Start web server in background
        try:
            print("Starting web server...")
            server_process = subprocess.Popen(
                [sys.executable, "-m", "torq_console.cli", "serve", "--port", "8899"],
                cwd=self.base_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            # Wait for server to start
            time.sleep(5)

            # Check if server is responding
            try:
                response = requests.get("http://localhost:8899", timeout=10)
                if response.status_code == 200:
                    self.log("web_interface", "server_start", "PASS", f"Status: {response.status_code}")

                    # Check for key elements
                    content = response.text.lower()
                    if "torq" in content:
                        self.log("web_interface", "branding", "PASS", "TORQ branding found")
                    else:
                        self.log("web_interface", "branding", "FAIL", "No TORQ branding found")

                else:
                    self.log("web_interface", "server_start", "FAIL", f"Status: {response.status_code}")
            except Exception as e:
                self.log("web_interface", "server_access", "FAIL", str(e))

            # Clean up
            server_process.terminate()
            server_process.wait(timeout=5)

        except Exception as e:
            self.log("web_interface", "server_start", "FAIL", str(e))

    def test_ml_systems_features(self):
        """Test ML Systems Hardening features"""
        print("\n🔍 TESTING ML SYSTEMS FEATURES")
        print("=" * 50)

        # Check eval sets exist
        eval_path = self.base_dir / "eval_sets" / "v1.0" / "tasks.json"
        if eval_path.exists():
            self.log("ml_systems", "eval_sets_exist", "PASS", f"Found at {eval_path}")

            # Try to load and validate
            try:
                with open(eval_path) as f:
                    eval_data = json.load(f)
                task_count = len(eval_data.get("tasks", []))
                self.log("ml_systems", "eval_sets_loaded", "PASS", f"Loaded {task_count} tasks")
            except Exception as e:
                self.log("ml_systems", "eval_sets_loaded", "FAIL", str(e))
        else:
            self.log("ml_systems", "eval_sets_exist", "FAIL", "eval_sets/v1.0/tasks.json not found")

        # Check policies exist
        policy_path = self.base_dir / "policies" / "routing" / "v1.yaml"
        if policy_path.exists():
            self.log("ml_systems", "policies_exist", "PASS", f"Found at {policy_path}")
        else:
            self.log("ml_systems", "policies_exist", "FAIL", "policies/routing/v1.yaml not found")

        # Check SLO config
        slo_path = self.base_dir / "slo.yml"
        if slo_path.exists():
            self.log("ml_systems", "slo_config", "PASS", f"Found at {slo_path}")
        else:
            self.log("ml_systems", "slo_config", "FAIL", "slo.yml not found")

        # Check telemetry module
        try:
            telemetry_path = self.base_dir / "torq_console" / "core" / "telemetry"
            if telemetry_path.exists():
                self.log("ml_systems", "telemetry_module", "PASS", "Telemetry module exists")
            else:
                self.log("ml_systems", "telemetry_module", "FAIL", "Telemetry module not found")
        except Exception as e:
            self.log("ml_systems", "telemetry_module", "FAIL", str(e))

    def test_marvin_integration(self):
        """Test Marvin 3.2.3 integration"""
        print("\n🔍 TESTING MARVIN INTEGRATION")
        print("=" * 50)

        # Check Marvin module exists
        marvin_path = self.base_dir / "torq_console" / "marvin_integration"
        if marvin_path.exists():
            self.log("marvin_integration", "marvin_module", "PASS", "Marvin integration module exists")

            # List Marvin files
            marvin_files = list(marvin_path.glob("*.py"))
            self.log("marvin_integration", "marvin_files", "PASS", f"Found {len(marvin_files)} Python files")
        else:
            self.log("marvin_integration", "marvin_module", "FAIL", "Marvin module not found")

        # Check agent commands
        agent_path = self.base_dir / "torq_console" / "agents"
        if agent_path.exists():
            agent_files = list(agent_path.glob("*.py"))
            self.log("marvin_integration", "agent_files", "PASS", f"Found {len(agent_files)} agent files")
        else:
            self.log("marvin_integration", "agent_files", "FAIL", "No agent files found")

    def test_file_structure(self):
        """Test critical file structure"""
        print("\n🔍 TESTING FILE STRUCTURE")
        print("=" * 50)

        critical_files = [
            "torq_console/__init__.py",
            "torq_console/cli.py",
            "torq_console/core/telemetry/event.py",
            "torq_console/core/evaluation/runner.py",
            "eval_sets/v1.0/tasks.json",
            "eval_sets/v1.0/metadata.json",
            "policies/routing/v1.yaml",
            "slo.yml",
        ]

        for file_path in critical_files:
            full_path = self.base_dir / file_path
            if full_path.exists():
                size = full_path.stat().st_size
                self.log("file_operations", file_path.replace("/", "_"), "PASS", f"Size: {size} bytes")
            else:
                self.log("file_operations", file_path.replace("/", "_"), "FAIL", "File not found")

    def save_eval_output(self, stdout):
        """Save evaluation output for review"""
        eval_output_path = self.base_dir / "validation_eval_output.json"
        try:
            # Try to parse as JSON
            if "{" in stdout:
                start = stdout.find("{")
                end = stdout.rfind("}") + 1
                json_str = stdout[start:end]
                data = json.loads(json_str)
                with open(eval_output_path, "w") as f:
                    json.dump(data, f, indent=2)
                self.log("file_operations", "eval_output_save", "PASS", f"Saved to {eval_output_path}")
        except:
            # Save as text if not JSON
            with open(eval_output_path, "w") as f:
                f.write(stdout)
            self.log("file_operations", "eval_output_save", "PARTIAL", "Saved as text")

    def generate_report(self):
        """Generate validation report"""
        print("\n📊 VALIDATION REPORT")
        print("=" * 50)

        total_tests = 0
        passed_tests = 0
        failed_tests = 0
        skipped_tests = 0

        for category, tests in self.results.items():
            if not tests:
                continue

            print(f"\n{category.upper()}:")
            for test, result in tests.items():
                status = result["status"]
                total_tests += 1

                if status == "PASS":
                    passed_tests += 1
                    print(f"  ✅ {test}")
                elif status == "FAIL":
                    failed_tests += 1
                    print(f"  ❌ {test}")
                else:
                    skipped_tests += 1
                    print(f"  ⚠️  {test}")

        print(f"\n📈 SUMMARY:")
        print(f"  Total Tests: {total_tests}")
        print(f"  Passed: {passed_tests} ({passed_tests/total_tests*100:.1f}%)")
        print(f"  Failed: {failed_tests} ({failed_tests/total_tests*100:.1f}%)")
        print(f"  Skipped: {skipped_tests} ({skipped_tests/total_tests*100:.1f}%)")

        # Save detailed report
        report_path = self.base_dir / "validation_report.json"
        with open(report_path, "w") as f:
            json.dump(self.results, f, indent=2)
        print(f"\n📄 Detailed report saved to: {report_path}")

        return {
            "total": total_tests,
            "passed": passed_tests,
            "failed": failed_tests,
            "skipped": skipped_tests,
            "pass_rate": passed_tests/total_tests*100 if total_tests > 0 else 0
        }

    def run_all_tests(self):
        """Run all validation tests"""
        print("🚀 TORQ CONSOLE VALIDATION")
        print("=" * 50)
        print("Testing what users can ACTUALLY do with TORQ Console")
        print(f"Working directory: {self.base_dir}")
        print(f"Python: {sys.version}")
        print("=" * 50)

        self.test_installation()
        self.test_core_cli_commands()
        self.test_web_interface()
        self.test_ml_systems_features()
        self.test_marvin_integration()
        self.test_file_structure()

        return self.generate_report()

if __name__ == "__main__":
    validator = TORQValidator()
    results = validator.run_all_tests()

    # Exit with appropriate code
    if results["failed"] > 0:
        print(f"\n❌ VALIDATION FAILED: {results['failed']} tests failed")
        sys.exit(1)
    else:
        print(f"\n✅ VALIDATION PASSED: {results['passed']}/{results['total']} tests passed")
        sys.exit(0)