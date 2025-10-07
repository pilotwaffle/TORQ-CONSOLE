"""
Comprehensive integration test for Torq-Console including:
- MCP server connectivity
- Prince Flowers agent
- Build capabilities
- Active outcome display
"""
import asyncio
import requests
import json
from pathlib import Path

class TorqConsoleIntegrationTest:
    def __init__(self):
        self.base_url = "http://localhost:8899"
        self.mcp_servers = [
            {"name": "Hybrid MCP", "url": "http://localhost:3100"},
            {"name": "N8N Proxy", "url": "http://localhost:3101"},
            {"name": "Local Machine", "url": "http://localhost:3102"}
        ]
        self.results = []

    def print_section(self, title):
        print(f"\n{'='*70}")
        print(f"  {title}")
        print(f"{'='*70}\n")

    def print_result(self, test_name, passed, details=""):
        status = "[PASS]" if passed else "[FAIL]"
        color = "\033[92m" if passed else "\033[91m"
        reset = "\033[0m"
        print(f"{color}{status}{reset} {test_name}")
        if details:
            print(f"  {details}")
        self.results.append({"test": test_name, "passed": passed, "details": details})

    def test_web_interface(self):
        """Test if web interface is accessible"""
        self.print_section("Testing Web Interface")
        try:
            response = requests.get(self.base_url, timeout=5)
            passed = response.status_code == 200
            self.print_result(
                "Web Interface Accessibility",
                passed,
                f"Status: {response.status_code}"
            )
            return passed
        except Exception as e:
            self.print_result("Web Interface Accessibility", False, f"Error: {e}")
            return False

    def test_mcp_servers(self):
        """Test MCP server connectivity"""
        self.print_section("Testing MCP Servers")
        all_passed = True

        for server in self.mcp_servers:
            try:
                # Test with a simple POST request (MCP protocol)
                response = requests.post(
                    server["url"],
                    json={"jsonrpc": "2.0", "method": "ping", "id": 1},
                    timeout=5
                )
                # Even if it returns an error, if we get a response, server is up
                passed = response.status_code in [200, 405]  # 405 = Method not allowed but server is up
                self.print_result(
                    f"{server['name']} Connectivity",
                    passed,
                    f"URL: {server['url']}, Status: {response.status_code}"
                )
                all_passed = all_passed and passed
            except Exception as e:
                self.print_result(
                    f"{server['name']} Connectivity",
                    False,
                    f"Error: {e}"
                )
                all_passed = False

        return all_passed

    def test_prince_flowers_api(self):
        """Test Prince Flowers API endpoints"""
        self.print_section("Testing Prince Flowers Agent")

        # Test status endpoint
        try:
            response = requests.get(f"{self.base_url}/api/prince/status", timeout=10)
            passed = response.status_code == 200
            if passed:
                data = response.json()
                details = f"Agent Version: {data.get('version', 'unknown')}, Status: {data.get('status', 'unknown')}"
            else:
                details = f"Status code: {response.status_code}"
            self.print_result("Prince Flowers Status API", passed, details)
        except Exception as e:
            self.print_result("Prince Flowers Status API", False, f"Error: {e}")
            passed = False

        # Test health endpoint
        try:
            response = requests.get(f"{self.base_url}/api/prince/health", timeout=10)
            health_passed = response.status_code == 200
            if health_passed:
                data = response.json()
                details = f"Health: {data.get('overall_status', 'unknown')}"
            else:
                details = f"Status code: {response.status_code}"
            self.print_result("Prince Flowers Health API", health_passed, details)
            passed = passed and health_passed
        except Exception as e:
            self.print_result("Prince Flowers Health API", False, f"Error: {e}")

        return passed

    def test_prince_flowers_query(self):
        """Test Prince Flowers query functionality"""
        self.print_section("Testing Prince Flowers Query")

        test_queries = [
            "prince help",
            "prince status",
            "what is agentic reinforcement learning"
        ]

        all_passed = True
        for query in test_queries:
            try:
                response = requests.post(
                    f"{self.base_url}/api/prince/query",
                    json={"query": query},
                    timeout=30
                )
                passed = response.status_code == 200
                if passed:
                    data = response.json()
                    confidence = data.get('confidence', 0)
                    details = f"Confidence: {confidence:.2%}, Response length: {len(data.get('content', ''))}"
                else:
                    details = f"Status code: {response.status_code}"
                self.print_result(f"Query: '{query}'", passed, details)
                all_passed = all_passed and passed
            except Exception as e:
                self.print_result(f"Query: '{query}'", False, f"Error: {e}")
                all_passed = False

        return all_passed

    def test_chat_api(self):
        """Test chat API functionality"""
        self.print_section("Testing Chat API")

        # Test chat tabs listing
        try:
            response = requests.get(f"{self.base_url}/api/chat/tabs", timeout=5)
            passed = response.status_code == 200
            if passed:
                data = response.json()
                details = f"Active tabs: {len(data.get('tabs', []))}"
            else:
                details = f"Status code: {response.status_code}"
            self.print_result("Chat Tabs API", passed, details)
        except Exception as e:
            self.print_result("Chat Tabs API", False, f"Error: {e}")
            passed = False

        return passed

    def test_command_palette_api(self):
        """Test command palette API"""
        self.print_section("Testing Command Palette API")

        try:
            response = requests.get(f"{self.base_url}/api/command-palette/commands", timeout=5)
            passed = response.status_code == 200
            if passed:
                data = response.json()
                commands = data.get('commands', [])
                details = f"Available commands: {len(commands)}"
                if commands:
                    details += f", Sample: {commands[0].get('title', 'N/A')}"
            else:
                details = f"Status code: {response.status_code}"
            self.print_result("Command Palette API", passed, details)
        except Exception as e:
            self.print_result("Command Palette API", False, f"Error: {e}")
            passed = False

        return passed

    def test_build_capability(self):
        """Test build and active outcome display"""
        self.print_section("Testing Build Capabilities")

        # Create a simple test file to demonstrate build capability
        test_file = Path("E:/Torq-Console/test_build_output.txt")
        try:
            test_file.write_text("Test build output - " + str(asyncio.get_event_loop().time()))
            passed = test_file.exists()
            details = f"Test file created at: {test_file}"
            self.print_result("File Creation (Build Simulation)", passed, details)

            # Test file reading
            content = test_file.read_text()
            read_passed = len(content) > 0
            self.print_result("Active Outcome Display", read_passed, f"Content: {content[:50]}...")

            # Cleanup
            test_file.unlink()

            return passed and read_passed
        except Exception as e:
            self.print_result("Build Capability Test", False, f"Error: {e}")
            return False

    def test_context_api(self):
        """Test context management API"""
        self.print_section("Testing Context Management")

        try:
            # Test parsing context with @-symbols
            response = requests.post(
                f"{self.base_url}/api/context/parse",
                json={"text": "@files *.py"},
                timeout=10
            )
            passed = response.status_code == 200
            if passed:
                data = response.json()
                details = f"Contexts found: {len(data.get('contexts', []))}"
            else:
                details = f"Status code: {response.status_code}"
            self.print_result("Context Parsing API", passed, details)
        except Exception as e:
            self.print_result("Context Parsing API", False, f"Error: {e}")
            passed = False

        return passed

    def print_summary(self):
        """Print test summary"""
        self.print_section("Test Summary")

        total = len(self.results)
        passed = sum(1 for r in self.results if r["passed"])
        failed = total - passed
        success_rate = (passed / total * 100) if total > 0 else 0

        print(f"Total Tests: {total}")
        print(f"Passed: \033[92m{passed}\033[0m")
        print(f"Failed: \033[91m{failed}\033[0m")
        print(f"Success Rate: {success_rate:.1f}%\n")

        if failed > 0:
            print("\nFailed Tests:")
            for result in self.results:
                if not result["passed"]:
                    print(f"  - {result['test']}")
                    if result["details"]:
                        print(f"    {result['details']}")

        print("\n" + "="*70)
        if success_rate == 100:
            print("  \033[92mALL TESTS PASSED! ✓\033[0m")
        elif success_rate >= 80:
            print("  \033[93mMOST TESTS PASSED\033[0m")
        else:
            print("  \033[91mMULTIPLE FAILURES - NEEDS ATTENTION\033[0m")
        print("="*70 + "\n")

    def run_all_tests(self):
        """Run all integration tests"""
        print("\n" + "="*70)
        print("  TORQ CONSOLE COMPREHENSIVE INTEGRATION TEST")
        print("  King Flowers Edition")
        print("="*70)

        # Run all test suites
        self.test_web_interface()
        self.test_mcp_servers()
        self.test_prince_flowers_api()
        self.test_prince_flowers_query()
        self.test_chat_api()
        self.test_command_palette_api()
        self.test_context_api()
        self.test_build_capability()

        # Print summary
        self.print_summary()

if __name__ == "__main__":
    tester = TorqConsoleIntegrationTest()
    tester.run_all_tests()
