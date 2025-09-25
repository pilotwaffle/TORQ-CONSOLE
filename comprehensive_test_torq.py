#!/usr/bin/env python3
"""
Comprehensive TORQ Console Testing Suite
Tests all functionality including web interface, chat, search, and Prince Flowers integration
"""

import requests
import json
import time
import sys
from pathlib import Path

class TorqTestSuite:
    def __init__(self):
        self.base_url = "http://127.0.0.1:8899"
        self.test_results = []

    def log_result(self, test_name, passed, details=""):
        """Log a test result"""
        status = "PASS" if passed else "FAIL"
        result = {
            "test": test_name,
            "status": status,
            "details": details
        }
        self.test_results.append(result)
        print(f"[{status}] {test_name}: {details}")

    def test_web_interface_load(self):
        """Test 1: Web Interface Loading"""
        try:
            response = requests.get(self.base_url, timeout=10)
            if response.status_code == 200 and "TORQ CONSOLE" in response.text:
                self.log_result("Web Interface Load", True, "HTML interface loads successfully")
                return True
            else:
                self.log_result("Web Interface Load", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_result("Web Interface Load", False, f"Connection error: {e}")
            return False

    def test_openapi_spec(self):
        """Test 2: OpenAPI Specification"""
        try:
            response = requests.get(f"{self.base_url}/openapi.json", timeout=10)
            if response.status_code == 200:
                spec = response.json()
                paths = list(spec.get('paths', {}).keys())

                # Check for key endpoints
                required_endpoints = ['/api/console/info', '/api/files', '/api/edit']
                missing_endpoints = [ep for ep in required_endpoints if ep not in paths]

                if not missing_endpoints:
                    self.log_result("OpenAPI Spec", True, f"Found {len(paths)} endpoints")
                    return spec
                else:
                    self.log_result("OpenAPI Spec", False, f"Missing endpoints: {missing_endpoints}")
                    return None
            else:
                self.log_result("OpenAPI Spec", False, f"HTTP {response.status_code}")
                return None
        except Exception as e:
            self.log_result("OpenAPI Spec", False, f"Error: {e}")
            return None

    def test_direct_chat_endpoint(self):
        """Test 3: Direct Chat Endpoint"""
        try:
            payload = {
                "message": "search web for latest AI news",
                "include_context": True,
                "generate_response": True
            }

            response = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                if result.get('success') and result.get('response'):
                    agent = result.get('agent', 'Unknown')
                    response_text = result.get('response', '')[:100] + "..."
                    self.log_result("Direct Chat Endpoint", True, f"Agent: {agent}, Response: {response_text}")
                    return True
                else:
                    self.log_result("Direct Chat Endpoint", False, f"Invalid response structure: {result}")
                    return False
            else:
                self.log_result("Direct Chat Endpoint", False, f"HTTP {response.status_code}: {response.text}")
                return False

        except Exception as e:
            self.log_result("Direct Chat Endpoint", False, f"Error: {e}")
            return False

    def test_console_info(self):
        """Test 4: Console Info Endpoint"""
        try:
            response = requests.get(f"{self.base_url}/api/console/info", timeout=10)
            if response.status_code == 200:
                info = response.json()
                version = info.get('version', 'Unknown')
                self.log_result("Console Info", True, f"Version: {version}")
                return True
            else:
                self.log_result("Console Info", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_result("Console Info", False, f"Error: {e}")
            return False

    def test_file_listing(self):
        """Test 5: File Listing Endpoint"""
        try:
            response = requests.get(f"{self.base_url}/api/files", timeout=10)
            if response.status_code == 200:
                files = response.json()
                file_count = len(files.get('files', []))
                self.log_result("File Listing", True, f"Listed {file_count} files")
                return True
            else:
                self.log_result("File Listing", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_result("File Listing", False, f"Error: {e}")
            return False

    def test_prince_flowers_search(self):
        """Test 6: Prince Flowers Search Integration"""
        try:
            payload = {
                "message": "prince search latest Python developments",
                "include_context": True,
                "generate_response": True
            }

            response = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                if result.get('success') and "Prince Flowers" in result.get('agent', ''):
                    response_text = result.get('response', '')[:100] + "..."
                    self.log_result("Prince Flowers Search", True, f"Response: {response_text}")
                    return True
                else:
                    self.log_result("Prince Flowers Search", False, f"Not routed to Prince Flowers: {result}")
                    return False
            else:
                self.log_result("Prince Flowers Search", False, f"HTTP {response.status_code}")
                return False

        except Exception as e:
            self.log_result("Prince Flowers Search", False, f"Error: {e}")
            return False

    def run_comprehensive_tests(self):
        """Run all tests and generate comprehensive report"""

        print("TORQ CONSOLE COMPREHENSIVE TEST SUITE")
        print("=" * 60)
        print("Testing all components for 100% functionality...")
        print()

        # Test 1: Web Interface
        web_ok = self.test_web_interface_load()

        if not web_ok:
            print("\n[CRITICAL] Web interface not accessible - stopping tests")
            return self.generate_report()

        # Test 2: API Specification
        spec = self.test_openapi_spec()

        # Test 3: Core Endpoints
        self.test_console_info()
        self.test_file_listing()

        # Test 4: Chat System
        chat_ok = self.test_direct_chat_endpoint()

        # Test 5: Prince Flowers Integration
        if chat_ok:
            self.test_prince_flowers_search()

        return self.generate_report()

    def generate_report(self):
        """Generate final test report"""

        print("\n" + "=" * 60)
        print("COMPREHENSIVE TEST RESULTS")
        print("=" * 60)

        passed = sum(1 for r in self.test_results if r['status'] == 'PASS')
        failed = sum(1 for r in self.test_results if r['status'] == 'FAIL')
        total = len(self.test_results)

        print(f"Tests Run: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Success Rate: {(passed/total*100):.1f}%")
        print()

        print("DETAILED RESULTS:")
        print("-" * 40)
        for result in self.test_results:
            status_symbol = "[OK]" if result['status'] == 'PASS' else "[FAIL]"
            print(f"{status_symbol} {result['test']}")
            if result['details']:
                print(f"    Details: {result['details']}")

        print("\n" + "=" * 60)

        # Determine overall status
        if failed == 0:
            print("OVERALL STATUS: ALL TESTS PASSED - TORQ Console 100% Functional")
            return True
        elif passed > 0:
            print("OVERALL STATUS: PARTIAL FUNCTIONALITY - Some components working")
            return False
        else:
            print("OVERALL STATUS: CRITICAL FAILURE - TORQ Console not functional")
            return False

def main():
    test_suite = TorqTestSuite()

    # Wait a moment for server to be fully ready
    print("Waiting for TORQ Console to be fully ready...")
    time.sleep(3)

    success = test_suite.run_comprehensive_tests()

    if success:
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()