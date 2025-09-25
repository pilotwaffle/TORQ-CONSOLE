#!/usr/bin/env python3
"""
TORQ CONSOLE API INTEGRATION VALIDATOR
=====================================

Comprehensive validation suite for all API integrations in TORQ Console deployment.
Tests DeepSeek API, Google Custom Search API, and Brave Search API with real queries.

Created: 2025-09-24
Purpose: Final API validation before deployment
"""

import os
import sys
import time
import json
import requests
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class APIIntegrationValidator:
    """Comprehensive API validation for TORQ Console deployment."""

    def __init__(self):
        """Initialize validator with API keys from environment."""
        self.deepseek_api_key = os.getenv('DEEPSEEK_API_KEY', 'sk-1061efb8089744dcad1183fb2ef55960')
        self.google_api_key = os.getenv('GOOGLE_SEARCH_API_KEY', 'AIzaSyA7eNQYC-zgo2OTYjL4QnrT5GeoHxJAhDw')
        self.google_engine_id = os.getenv('GOOGLE_SEARCH_ENGINE_ID', '34dd471ccd5dd4572')
        self.brave_api_key = os.getenv('BRAVE_SEARCH_API_KEY', 'BSAkNrh316HK8uxqGjUN1_eeLon8PfO')

        self.results = {
            'timestamp': datetime.now().isoformat(),
            'apis_tested': [],
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0,
            'api_status': {},
            'performance_metrics': {},
            'recommendations': []
        }

        # Test queries for validation
        self.test_queries = [
            "leadership development trends 2024",
            "digital transformation strategies",
            "business intelligence best practices"
        ]

    def test_deepseek_api(self) -> Dict[str, Any]:
        """Test DeepSeek API with chat completion."""
        logger.info("🧠 Testing DeepSeek API...")

        test_result = {
            'service': 'DeepSeek API',
            'api_key': f"{self.deepseek_api_key[:15]}..." if self.deepseek_api_key else "Not provided",
            'status': 'UNKNOWN',
            'response_time': 0,
            'test_details': {},
            'error': None
        }

        if not self.deepseek_api_key or self.deepseek_api_key == 'YOUR_DEEPSEEK_API_KEY_HERE':
            test_result['status'] = 'FAILED'
            test_result['error'] = 'API key not configured'
            return test_result

        try:
            start_time = time.time()

            # Test with DeepSeek v3 API
            headers = {
                'Authorization': f'Bearer {self.deepseek_api_key}',
                'Content-Type': 'application/json'
            }

            payload = {
                "model": "deepseek-chat",
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a business intelligence analyst. Provide concise, professional responses."
                    },
                    {
                        "role": "user",
                        "content": "Analyze the current state of digital transformation in enterprise businesses. Keep response under 100 words."
                    }
                ],
                "max_tokens": 150,
                "temperature": 0.7
            }

            response = requests.post(
                'https://api.deepseek.com/chat/completions',
                headers=headers,
                json=payload,
                timeout=30
            )

            response_time = time.time() - start_time
            test_result['response_time'] = response_time

            if response.status_code == 200:
                data = response.json()
                if 'choices' in data and len(data['choices']) > 0:
                    content = data['choices'][0]['message']['content']

                    test_result['status'] = 'PASSED'
                    test_result['test_details'] = {
                        'response_length': len(content),
                        'model_used': data.get('model', 'deepseek-chat'),
                        'tokens_used': data.get('usage', {}).get('total_tokens', 0),
                        'sample_response': content[:200] + "..." if len(content) > 200 else content
                    }
                    logger.info(f"✅ DeepSeek API: SUCCESS ({response_time:.2f}s)")
                else:
                    test_result['status'] = 'FAILED'
                    test_result['error'] = 'Invalid response format'
            else:
                test_result['status'] = 'FAILED'
                test_result['error'] = f"HTTP {response.status_code}: {response.text}"

        except requests.exceptions.RequestException as e:
            test_result['status'] = 'FAILED'
            test_result['error'] = f"Request failed: {str(e)}"
            test_result['response_time'] = time.time() - start_time

        except Exception as e:
            test_result['status'] = 'FAILED'
            test_result['error'] = f"Unexpected error: {str(e)}"

        return test_result

    def test_google_search_api(self) -> Dict[str, Any]:
        """Test Google Custom Search API."""
        logger.info("🔍 Testing Google Custom Search API...")

        test_result = {
            'service': 'Google Custom Search API',
            'api_key': f"{self.google_api_key[:15]}..." if self.google_api_key else "Not provided",
            'status': 'UNKNOWN',
            'response_time': 0,
            'test_details': {},
            'error': None
        }

        if not self.google_api_key or self.google_api_key == 'YOUR_GOOGLE_API_KEY_HERE':
            test_result['status'] = 'FAILED'
            test_result['error'] = 'API key not configured'
            return test_result

        try:
            start_time = time.time()

            # Test search with business intelligence query
            params = {
                'key': self.google_api_key,
                'cx': self.google_engine_id,
                'q': 'business intelligence trends 2024',
                'num': 5,
                'safe': 'active'
            }

            response = requests.get(
                'https://www.googleapis.com/customsearch/v1',
                params=params,
                timeout=15
            )

            response_time = time.time() - start_time
            test_result['response_time'] = response_time

            if response.status_code == 200:
                data = response.json()

                if 'items' in data and len(data['items']) > 0:
                    test_result['status'] = 'PASSED'
                    test_result['test_details'] = {
                        'results_count': len(data['items']),
                        'total_results': data.get('searchInformation', {}).get('totalResults', '0'),
                        'search_time': data.get('searchInformation', {}).get('searchTime', 0),
                        'sample_results': [
                            {
                                'title': item.get('title', ''),
                                'link': item.get('link', ''),
                                'snippet': item.get('snippet', '')[:100] + "..."
                            }
                            for item in data['items'][:3]
                        ]
                    }
                    logger.info(f"✅ Google Search API: SUCCESS ({response_time:.2f}s, {len(data['items'])} results)")
                else:
                    test_result['status'] = 'FAILED'
                    test_result['error'] = 'No search results returned'
            else:
                test_result['status'] = 'FAILED'
                test_result['error'] = f"HTTP {response.status_code}: {response.text}"

        except requests.exceptions.RequestException as e:
            test_result['status'] = 'FAILED'
            test_result['error'] = f"Request failed: {str(e)}"
            test_result['response_time'] = time.time() - start_time

        except Exception as e:
            test_result['status'] = 'FAILED'
            test_result['error'] = f"Unexpected error: {str(e)}"

        return test_result

    def test_brave_search_api(self) -> Dict[str, Any]:
        """Test Brave Search API."""
        logger.info("🦁 Testing Brave Search API...")

        test_result = {
            'service': 'Brave Search API',
            'api_key': f"{self.brave_api_key[:15]}..." if self.brave_api_key else "Not provided",
            'status': 'UNKNOWN',
            'response_time': 0,
            'test_details': {},
            'error': None
        }

        if not self.brave_api_key or self.brave_api_key == 'YOUR_BRAVE_API_KEY_HERE':
            test_result['status'] = 'FAILED'
            test_result['error'] = 'API key not configured'
            return test_result

        try:
            start_time = time.time()

            # Test search with digital transformation query
            headers = {
                'Accept': 'application/json',
                'Accept-Encoding': 'gzip',
                'X-Subscription-Token': self.brave_api_key
            }

            params = {
                'q': 'digital transformation enterprise strategy',
                'count': 5,
                'offset': 0,
                'mkt': 'en-US',
                'safesearch': 'moderate',
                'freshness': 'pw'  # Past week
            }

            response = requests.get(
                'https://api.search.brave.com/res/v1/web/search',
                headers=headers,
                params=params,
                timeout=15
            )

            response_time = time.time() - start_time
            test_result['response_time'] = response_time

            if response.status_code == 200:
                data = response.json()

                if 'web' in data and 'results' in data['web'] and len(data['web']['results']) > 0:
                    results = data['web']['results']

                    test_result['status'] = 'PASSED'
                    test_result['test_details'] = {
                        'results_count': len(results),
                        'query_performed': params['q'],
                        'sample_results': [
                            {
                                'title': result.get('title', ''),
                                'url': result.get('url', ''),
                                'description': result.get('description', '')[:100] + "..."
                            }
                            for result in results[:3]
                        ],
                        'family_friendly': data.get('family_friendly', True)
                    }
                    logger.info(f"✅ Brave Search API: SUCCESS ({response_time:.2f}s, {len(results)} results)")
                else:
                    test_result['status'] = 'FAILED'
                    test_result['error'] = 'No search results returned'
            else:
                test_result['status'] = 'FAILED'
                test_result['error'] = f"HTTP {response.status_code}: {response.text}"

        except requests.exceptions.RequestException as e:
            test_result['status'] = 'FAILED'
            test_result['error'] = f"Request failed: {str(e)}"
            test_result['response_time'] = time.time() - start_time

        except Exception as e:
            test_result['status'] = 'FAILED'
            test_result['error'] = f"Unexpected error: {str(e)}"

        return test_result

    def test_environment_configuration(self) -> Dict[str, Any]:
        """Test environment configuration and API key loading."""
        logger.info("⚙️  Testing environment configuration...")

        config_test = {
            'service': 'Environment Configuration',
            'status': 'PASSED',
            'test_details': {},
            'issues': []
        }

        # Check .env file existence
        env_file = '.env'
        if os.path.exists(env_file):
            config_test['test_details']['env_file_found'] = True
            with open(env_file, 'r') as f:
                content = f.read()
                config_test['test_details']['env_file_size'] = len(content)
        else:
            config_test['issues'].append('No .env file found in current directory')

        # Check API key configuration
        api_keys = {
            'DEEPSEEK_API_KEY': self.deepseek_api_key,
            'GOOGLE_SEARCH_API_KEY': self.google_api_key,
            'BRAVE_SEARCH_API_KEY': self.brave_api_key
        }

        configured_keys = 0
        for key, value in api_keys.items():
            if value and value != f'YOUR_{key}_HERE':
                configured_keys += 1
                config_test['test_details'][f'{key}_configured'] = True
            else:
                config_test['test_details'][f'{key}_configured'] = False
                config_test['issues'].append(f'{key} not properly configured')

        config_test['test_details']['configured_keys_count'] = configured_keys
        config_test['test_details']['total_keys_count'] = len(api_keys)

        if configured_keys < len(api_keys):
            config_test['status'] = 'WARNING'

        return config_test

    def run_comprehensive_validation(self) -> Dict[str, Any]:
        """Run complete API validation suite."""
        logger.info("🚀 Starting TORQ Console API Integration Validation")
        logger.info("=" * 60)

        # Test environment configuration
        env_test = self.test_environment_configuration()
        self.results['apis_tested'].append(env_test)

        # Test each API
        api_tests = [
            self.test_deepseek_api(),
            self.test_google_search_api(),
            self.test_brave_search_api()
        ]

        # Collect results
        for test_result in api_tests:
            self.results['apis_tested'].append(test_result)
            self.results['total_tests'] += 1

            if test_result['status'] == 'PASSED':
                self.results['passed_tests'] += 1
            else:
                self.results['failed_tests'] += 1

            # Store individual API status
            self.results['api_status'][test_result['service']] = {
                'status': test_result['status'],
                'response_time': test_result.get('response_time', 0),
                'error': test_result.get('error')
            }

            # Store performance metrics
            if 'response_time' in test_result:
                self.results['performance_metrics'][test_result['service']] = {
                    'response_time_seconds': test_result['response_time'],
                    'performance_grade': self._grade_performance(test_result['response_time'])
                }

        # Generate recommendations
        self._generate_recommendations()

        # Calculate overall success rate
        self.results['success_rate'] = (
            self.results['passed_tests'] / self.results['total_tests'] * 100
            if self.results['total_tests'] > 0 else 0
        )

        return self.results

    def _grade_performance(self, response_time: float) -> str:
        """Grade API performance based on response time."""
        if response_time < 1.0:
            return 'EXCELLENT'
        elif response_time < 3.0:
            return 'GOOD'
        elif response_time < 5.0:
            return 'FAIR'
        else:
            return 'POOR'

    def _generate_recommendations(self):
        """Generate recommendations based on test results."""
        passed_apis = [api for api in self.results['apis_tested'] if api.get('status') == 'PASSED']
        failed_apis = [api for api in self.results['apis_tested'] if api.get('status') == 'FAILED']

        if len(passed_apis) == len([api for api in self.results['apis_tested'] if 'service' in api and 'API' in api['service']]):
            self.results['recommendations'].append("✅ All APIs are functioning correctly and ready for production")

        if len(failed_apis) > 0:
            self.results['recommendations'].append(f"❌ {len(failed_apis)} API(s) failed validation - check credentials and connectivity")

        # Performance recommendations
        slow_apis = [
            api for api in self.results['apis_tested']
            if api.get('response_time', 0) > 3.0
        ]

        if slow_apis:
            self.results['recommendations'].append("⚡ Consider implementing caching for slower APIs to improve response times")

        # Rate limiting recommendations
        if any('Google' in api.get('service', '') for api in passed_apis):
            self.results['recommendations'].append("📊 Google Search API: Monitor daily quota usage (100 queries/day free tier)")

        if any('Brave' in api.get('service', '') for api in passed_apis):
            self.results['recommendations'].append("🦁 Brave Search API: Track monthly usage (2,000 queries/month limit)")

    def print_detailed_report(self):
        """Print comprehensive validation report."""
        print("\n" + "=" * 80)
        print("🏆 TORQ CONSOLE API INTEGRATION VALIDATION REPORT")
        print("=" * 80)

        print(f"\n📊 OVERALL RESULTS:")
        print(f"   • Total Tests: {self.results['total_tests']}")
        print(f"   • Passed: {self.results['passed_tests']} ✅")
        print(f"   • Failed: {self.results['failed_tests']} ❌")
        print(f"   • Success Rate: {self.results['success_rate']:.1f}%")

        print(f"\n⏱️  PERFORMANCE METRICS:")
        for service, metrics in self.results['performance_metrics'].items():
            print(f"   • {service}: {metrics['response_time_seconds']:.2f}s ({metrics['performance_grade']})")

        print(f"\n🔍 API STATUS DETAILS:")
        for api_result in self.results['apis_tested']:
            service = api_result.get('service', 'Unknown')
            status = api_result.get('status', 'UNKNOWN')

            status_icon = "✅" if status == "PASSED" else "❌" if status == "FAILED" else "⚠️"
            print(f"   {status_icon} {service}: {status}")

            if api_result.get('error'):
                print(f"      Error: {api_result['error']}")

            if 'test_details' in api_result and api_result['test_details']:
                if 'sample_response' in api_result['test_details']:
                    print(f"      Sample: {api_result['test_details']['sample_response'][:100]}...")
                elif 'results_count' in api_result['test_details']:
                    print(f"      Results: {api_result['test_details']['results_count']} returned")

        print(f"\n💡 RECOMMENDATIONS:")
        for recommendation in self.results['recommendations']:
            print(f"   • {recommendation}")

        print(f"\n🚀 DEPLOYMENT STATUS:")
        if self.results['success_rate'] >= 100:
            print("   ✅ READY FOR PRODUCTION - All APIs validated successfully")
        elif self.results['success_rate'] >= 75:
            print("   ⚠️  CONDITIONAL DEPLOYMENT - Most APIs working, review failures")
        else:
            print("   ❌ NOT READY - Critical API failures detected")

        print("\n" + "=" * 80)


def main():
    """Main execution function."""
    print("🚀 TORQ Console API Integration Validator")
    print("Starting comprehensive API validation...")

    validator = APIIntegrationValidator()

    try:
        # Run validation
        results = validator.run_comprehensive_validation()

        # Print detailed report
        validator.print_detailed_report()

        # Save results to file
        results_file = f"api_validation_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)

        print(f"\n📄 Detailed results saved to: {results_file}")

        # Return appropriate exit code
        sys.exit(0 if results['success_rate'] >= 75 else 1)

    except KeyboardInterrupt:
        print("\n❌ Validation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Validation failed with error: {str(e)}")
        logger.exception("Unexpected error during validation")
        sys.exit(1)


if __name__ == "__main__":
    main()