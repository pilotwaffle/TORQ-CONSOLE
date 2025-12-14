#!/usr/bin/env python3
"""
Generate Capability Report - Proof of what TORQ Console can do

This script runs all capability tests and generates a comprehensive report
showing what users can actually do with TORQ Console, backed by test evidence.
"""

import subprocess
import json
import sys
import os
from pathlib import Path
import datetime
import platform
import hashlib

class CapabilityReportGenerator:
    def __init__(self):
        self.base_dir = Path(__file__).parent.parent
        self.reports_dir = self.base_dir / "reports" / "capabilities"
        self.git_sha = self._get_git_sha()
        self.report_data = {
            "metadata": {
                "timestamp": datetime.datetime.now().isoformat(),
                "git_sha": self.git_sha,
                "git_short_sha": self.git_sha[:8] if self.git_sha else "unknown",
                "platform": platform.platform(),
                "python_version": sys.version,
                "working_directory": str(self.base_dir),
                "torq_console_version": self._get_torq_version()
            },
            "contract": {},
            "results": {},
            "summary": {}
        }

    def _get_git_sha(self):
        """Get current git commit SHA"""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                capture_output=True,
                text=True,
                cwd=self.base_dir
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except:
            pass
        return None

    def _get_torq_version(self):
        """Get TORQ Console version"""
        try:
            import torq_console
            return getattr(torq_console, '__version__', 'unknown')
        except:
            return 'unknown'

    def load_contract(self):
        """Load the capability contract"""
        contract_path = self.base_dir / "docs" / "capabilities.yml"
        try:
            import yaml
            with open(contract_path) as f:
                self.report_data["contract"] = yaml.safe_load(f)
            print(f"Loaded contract with {len(self.report_data['contract']['capabilities'])} capabilities")
        except Exception as e:
            print(f"Failed to load contract: {e}")
            return False
        return True

    def run_capability_tests(self):
        """Run all capability tests"""
        print("\nRunning Capability Tests")
        print("=" * 50)

        # Run pytest on all capability test files
        import tempfile
        import glob
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        temp_file.close()

        # Find all capability test files
        test_files = glob.glob(str(self.base_dir / "tests/capability/test_*.py"))

        cmd = [
            sys.executable, "-m", "pytest",
            "tests/capability/",
            "-v",
            "--json-report",
            f"--json-report-file={temp_file.name}",
            "--tb=short"
        ]

        try:
            result = subprocess.run(cmd, cwd=self.base_dir, capture_output=True, text=True)

            if result.returncode == 0:
                print("All tests completed")
            else:
                print("Some tests failed")

            # Save raw output
            self.report_data["results"]["pytest_output"] = result.stdout

            # Parse JSON report if available
            try:
                with open(temp_file.name) as f:
                    test_results = json.load(f)
                self.report_data["results"]["test_summary"] = test_results.get("summary", {})
                self.report_data["results"]["tests"] = test_results.get("tests", [])
            except:
                print("Could not parse test results JSON")

            # Cleanup temp file
            import os
            try:
                os.unlink(temp_file.name)
            except:
                pass

            return result.returncode == 0

        except Exception as e:
            print(f"Failed to run tests: {e}")
            return False

    def generate_capability_matrix(self):
        """Generate capability matrix showing what works"""
        print("\nGenerating Capability Matrix")
        print("=" * 50)

        matrix = {}
        capabilities = self.report_data.get("contract", {}).get("capabilities", [])
        test_results = self.report_data.get("results", {}).get("tests", [])

        # Create a lookup for test results
        test_lookup = {}
        for test in test_results:
            test_name = test.get("name", "")
            # Extract capability ID from test name
            if "test_" in test_name:
                parts = test_name.split("_", 2)
                if len(parts) >= 2:
                    capability_id = "_".join(parts[1:2])
                    test_lookup[capability_id] = {
                        "outcome": test.get("outcome", "unknown"),
                        "duration": test.get("duration", 0),
                        "nodeid": test.get("nodeid", "")
                    }

        # Process each capability
        for capability in capabilities:
            cap_id = capability["id"]
            cap_result = {
                "id": cap_id,
                "category": capability.get("category", "unknown"),
                "description": capability.get("description", ""),
                "personas": capability.get("personas", []),
                "status": "unknown",
                "details": ""
            }

            # Check if we have test results
            if cap_id in test_lookup:
                test_info = test_lookup[cap_id]
                if test_info["outcome"] == "passed":
                    cap_result["status"] = "PASS"
                    cap_result["details"] = f"Passed in {test_info['duration']:.3f}s"
                elif test_info["outcome"] == "failed":
                    cap_result["status"] = "FAIL"
                    cap_result["details"] = f"Test failed"
                elif test_info["outcome"] == "skipped":
                    cap_result["status"] = "SKIP"
                    cap_result["details"] = f"Test skipped"
            else:
                cap_result["status"] = "UNKNOWN"
                cap_result["details"] = "No test result found"

            matrix[cap_id] = cap_result

        self.report_data["results"]["capability_matrix"] = matrix

        # Count results
        total = len(matrix)
        passed = sum(1 for c in matrix.values() if c["status"] == "PASS")
        failed = sum(1 for c in matrix.values() if c["status"] == "FAIL")
        skipped = sum(1 for c in matrix.values() if c["status"] == "SKIP")
        unknown = sum(1 for c in matrix.values() if c["status"] == "UNKNOWN")

        self.report_data["summary"] = {
            "total_capabilities": total,
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "unknown": unknown,
            "success_rate": (passed / total * 100) if total > 0 else 0
        }

        # Print summary
        print(f"Total Capabilities: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Skipped: {skipped}")
        print(f"Unknown: {unknown}")
        print(f"Success Rate: {self.report_data['summary']['success_rate']:.1f}%")

    def save_reports(self):
        """Save capability reports in multiple formats"""
        print(f"\nSaving Reports to {self.reports_dir}")
        print("=" * 50)

        # Create reports directory with git SHA
        report_dir = self.reports_dir / self.report_data["metadata"]["git_short_sha"]
        report_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

        # Save JSON report
        json_file = report_dir / f"capability_report_{timestamp}.json"
        with open(json_file, "w") as f:
            json.dump(self.report_data, f, indent=2)
        print(f"JSON report: {json_file}")

        # Save Markdown report
        md_file = report_dir / f"capability_report_{timestamp}.md"
        self._save_markdown_report(md_file)
        print(f"Markdown report: {md_file}")

        # Save latest symlink
        latest_json = self.reports_dir / "latest_capability_report.json"
        latest_md = self.reports_dir / "latest_capability_report.md"

        # Remove existing symlinks (Windows compatible)
        if latest_json.exists():
            latest_json.unlink()
        if latest_md.exists():
            latest_md.unlink()

        # Copy latest reports
        import shutil
        shutil.copy2(json_file, latest_json)
        shutil.copy2(md_file, latest_md)

        print(f"Latest reports linked in {self.reports_dir}")

    def _save_markdown_report(self, filepath):
        """Generate and save Markdown report"""
        md_content = f"""# TORQ Console Capability Report

**Generated:** {self.report_data["metadata"]["timestamp"]}
**Git SHA:** {self.report_data["metadata"]["git_short_sha"]}
**Platform:** {self.report_data["metadata"]["platform"]}

## Executive Summary

- **Total Capabilities:** {self.report_data["summary"]["total_capabilities"]}
- **Passed:** {self.report_data["summary"]["passed"]}
- **Failed:** {self.report_data["summary"]["failed"]}
- **Skipped:** {self.report_data["summary"]["skipped"]}
- **Success Rate:** {self.report_data["summary"]["success_rate"]:.1f}%

## Capability Matrix

| ID | Category | Status | Description | Personas |
|----|----------|--------|-------------|----------|
"""

        matrix = self.report_data["results"].get("capability_matrix", {})
        for cap_id, cap in matrix.items():
            md_content += f"| {cap_id} | {cap['category']} | {cap['status']} | {cap['description']} | {', '.join(cap['personas'])} |\n"

        md_content += f"""

## Test Details

### What Works

"""
        passed_caps = [c for c in matrix.values() if c["status"] == "PASS"]
        for cap in passed_caps:
            md_content += f"- **{cap['id']}**: {cap['description']}\n"

        md_content += f"""

### What Doesn't Work

"""
        failed_caps = [c for c in matrix.values() if c["status"] == "FAIL"]
        for cap in failed_caps:
            md_content += f"- **{cap['id']}**: {cap['description']} - {cap['details']}\n"

        md_content += f"""

### Unknown Status

"""
        unknown_caps = [c for c in matrix.values() if c["status"] == "UNKNOWN"]
        for cap in unknown_caps:
            md_content += f"- **{cap['id']}**: {cap['description']} - No test found\n"

        md_content += """

## Generation Details

This report was generated by running the capability test suite:

```bash
pytest tests/capability/ -m capability -v --json-report
```

All claims in this report are backed by automated tests that verify
actual functionality. For test details, see the JSON report.

---

*This report serves as proof of TORQ Console's actual capabilities.*
"""

        with open(filepath, "w") as f:
            f.write(md_content)

    def run(self):
        """Main execution"""
        print("TORQ Console Capability Report Generator")
        print("=" * 50)
        print(f"Working Directory: {self.base_dir}")
        print(f"Reports Directory: {self.reports_dir}")
        print("=" * 50)

        if not self.load_contract():
            return False

        tests_passed = self.run_capability_tests()
        self.generate_capability_matrix()
        self.save_reports()

        print(f"\nReport generation complete!")
        print(f"Success Rate: {self.report_data['summary']['success_rate']:.1f}%")

        return tests_passed


if __name__ == "__main__":
    generator = CapabilityReportGenerator()
    success = generator.run()
    sys.exit(0 if success else 1)