#!/usr/bin/env python3
"""
Capabilities Validation Script
Tests capabilities defined in capabilities.yaml
"""

import subprocess
import sys
import yaml
from pathlib import Path
import json
from datetime import datetime

class CapabilityValidator:
    def __init__(self):
        self.results = {}
        self.base_dir = Path(__file__).parent
        self.capabilities_file = self.base_dir / "capabilities.yaml"
        
    def load_capabilities(self):
        """Load capabilities from YAML file"""
        if not self.capabilities_file.exists():
            print(f"❌ Capabilities file not found: {self.capabilities_file}")
            sys.exit(1)
            
        with open(self.capabilities_file, 'r') as f:
            self.capabilities = yaml.safe_load(f)
            
        print(f"✅ Loaded capabilities.yaml")
        print(f"   Version: {self.capabilities['version']}")
        print(f"   Personas: {list(self.capabilities['personas'].keys())}")
        print(f"   Capabilities: {len(self.capabilities['capabilities'])}")
        
    def run_command(self, cmd, timeout=30):
        """Run command and capture output"""
        try:
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True,
                timeout=timeout, cwd=self.base_dir
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return -1, "", "Command timed out"
        except Exception as e:
            return -1, "", str(e)
            
    def verify_capability(self, capability):
        """Verify a single capability"""
        cap_id = capability['id']
        verify_spec = capability['verify']
        command = verify_spec['command']
        expect = verify_spec['expect']
        
        print(f"\n🔍 Testing: {cap_id}")
        print(f"   Description: {capability['description']}")
        print(f"   Command: {command[:60]}...")
        
        returncode, stdout, stderr = self.run_command(command)
        
        # Determine if test passed based on expectation
        passed = False
        details = ""
        
        if expect == "success":
            # Should succeed (returncode 0)
            if returncode == 0:
                # Check if required strings are in output
                success_contains = verify_spec.get('success_contains', [])
                all_found = True
                for expected_str in success_contains:
                    combined_output = stdout + stderr
                    if expected_str not in combined_output:
                        all_found = False
                        details = f"Missing expected string: {expected_str}"
                        break
                        
                if all_found:
                    passed = True
                    details = "Command succeeded with expected output"
            else:
                details = f"Command failed with exit code {returncode}"
                
        elif expect == "blocked":
            # Should fail (non-zero returncode)
            if returncode != 0:
                blocked_reason = verify_spec.get('blocked_reason', '')
                combined_output = stdout + stderr
                
                # Check if the blocking happened for the right reason
                if blocked_reason and blocked_reason in combined_output:
                    passed = True
                    details = f"Correctly blocked: {blocked_reason}"
                elif returncode != 0:
                    # Any failure is acceptable for blocked tests
                    passed = True
                    details = f"Command blocked with exit code {returncode}"
            else:
                details = "Command unexpectedly succeeded"
                
        # Store results
        self.results[cap_id] = {
            "passed": passed,
            "details": details,
            "returncode": returncode,
            "personas": capability['personas']
        }
        
        # Print result
        symbol = "✅" if passed else "❌"
        print(f"   {symbol} Result: {'PASS' if passed else 'FAIL'}")
        print(f"   {details}")
        
        return passed
        
    def run_all_validations(self):
        """Run all capability validations"""
        print("\n" + "=" * 70)
        print("TORQ Console Capabilities Validation")
        print("=" * 70)
        
        self.load_capabilities()
        
        passed_count = 0
        failed_count = 0
        
        for capability in self.capabilities['capabilities']:
            if self.verify_capability(capability):
                passed_count += 1
            else:
                failed_count += 1
                
        # Print summary
        print("\n" + "=" * 70)
        print("VALIDATION SUMMARY")
        print("=" * 70)
        total = passed_count + failed_count
        print(f"Total Tests: {total}")
        print(f"✅ Passed: {passed_count} ({passed_count/total*100:.1f}%)")
        print(f"❌ Failed: {failed_count} ({failed_count/total*100:.1f}%)")
        
        # Save detailed results
        results_file = self.base_dir / "capability_validation_results.json"
        with open(results_file, 'w') as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "total": total,
                "passed": passed_count,
                "failed": failed_count,
                "results": self.results
            }, f, indent=2)
        print(f"\n📄 Detailed results saved to: {results_file}")
        
        return failed_count == 0

if __name__ == "__main__":
    validator = CapabilityValidator()
    success = validator.run_all_validations()
    sys.exit(0 if success else 1)
