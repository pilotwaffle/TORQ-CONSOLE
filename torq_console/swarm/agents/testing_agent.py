"""
Testing Agent for Advanced Swarm Intelligence System.

This agent specializes in test generation, test automation, validation,
and quality assurance across different testing methodologies.
"""

import asyncio
from typing import Dict, List, Any, Optional, Tuple
import logging
from datetime import datetime
import re
import json


class TestingAgent:
    """Specialized agent for testing and quality assurance."""

    def __init__(self, llm_provider=None):
        """
        Initialize TestingAgent.

        Args:
            llm_provider: LLM provider for test generation and analysis
        """
        self.llm_provider = llm_provider
        self.logger = logging.getLogger(__name__)

        # Agent specialization
        self.agent_id = "testing_agent"
        self.capabilities = [
            "unit_test_generation",
            "integration_test_creation",
            "api_testing",
            "performance_testing",
            "security_testing",
            "test_automation",
            "quality_analysis",
            "test_coverage_analysis"
        ]

        # Test frameworks and templates
        self.test_frameworks = {
            'python': {
                'unittest': {
                    'import': 'import unittest',
                    'class_template': 'class Test{class_name}(unittest.TestCase):',
                    'method_template': 'def test_{method_name}(self):',
                    'assert_template': 'self.assertEqual({actual}, {expected})'
                },
                'pytest': {
                    'import': 'import pytest',
                    'function_template': 'def test_{function_name}():',
                    'assert_template': 'assert {actual} == {expected}',
                    'fixture_template': '@pytest.fixture\ndef {fixture_name}():'
                }
            },
            'javascript': {
                'jest': {
                    'describe_template': 'describe("{description}", () => {{',
                    'test_template': 'test("{test_name}", () => {{',
                    'assert_template': 'expect({actual}).toBe({expected});'
                },
                'mocha': {
                    'describe_template': 'describe("{description}", function() {{',
                    'test_template': 'it("{test_name}", function() {{',
                    'assert_template': 'expect({actual}).to.equal({expected});'
                }
            }
        }

        # Test result cache
        self.test_cache = {}
        self.max_cache_size = 200

        # Testing patterns and heuristics
        self.test_patterns = {
            'edge_cases': ['null', 'empty', 'zero', 'negative', 'maximum', 'minimum'],
            'error_conditions': ['invalid_input', 'missing_params', 'network_error', 'timeout'],
            'performance_metrics': ['response_time', 'throughput', 'memory_usage', 'cpu_usage']
        }

    async def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a testing task.

        Args:
            task: Task dictionary with testing requirements

        Returns:
            Testing results with next agent recommendations
        """
        start_time = datetime.now()
        task_type = task.get('type', 'unit_testing')

        self.logger.info(f"Processing {task_type} testing task")

        try:
            if task_type == 'unit_test_generation':
                result = await self._generate_unit_tests(task)
            elif task_type == 'integration_testing':
                result = await self._generate_integration_tests(task)
            elif task_type == 'api_testing':
                result = await self._generate_api_tests(task)
            elif task_type == 'performance_testing':
                result = await self._generate_performance_tests(task)
            elif task_type == 'security_testing':
                result = await self._generate_security_tests(task)
            elif task_type == 'test_analysis':
                result = await self._analyze_existing_tests(task)
            elif task_type == 'test_automation':
                result = await self._create_test_automation(task)
            else:
                result = await self._general_testing_task(task)

            # Determine next agent
            next_agent = self._determine_next_agent(result, task)

            processing_time = (datetime.now() - start_time).total_seconds()

            return {
                'agent_id': self.agent_id,
                'task_type': task_type,
                'results': result,
                'next_agent': next_agent,
                'processing_time': processing_time,
                'confidence': result.get('confidence', 0.85),
                'metadata': {
                    'tests_generated': len(result.get('test_cases', [])),
                    'test_types': len(set(tc.get('type') for tc in result.get('test_cases', []))),
                    'coverage_estimate': result.get('coverage_estimate', 0)
                }
            }

        except Exception as e:
            self.logger.error(f"Testing task failed: {e}")
            return {
                'agent_id': self.agent_id,
                'task_type': task_type,
                'error': str(e),
                'next_agent': 'response_agent',
                'processing_time': (datetime.now() - start_time).total_seconds()
            }

    async def _generate_unit_tests(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive unit tests."""
        code = task.get('code', '')
        language = task.get('language', 'python')
        framework = task.get('framework', 'pytest' if language == 'python' else 'jest')

        tests = {
            'language': language,
            'framework': framework,
            'test_cases': [],
            'test_suites': [],
            'coverage_estimate': 0,
            'confidence': 0.9
        }

        if language == 'python':
            tests = await self._generate_python_unit_tests(code, framework)
        elif language == 'javascript':
            tests = await self._generate_javascript_unit_tests(code, framework)

        # Estimate test coverage
        tests['coverage_estimate'] = self._estimate_coverage(code, tests['test_cases'])

        return tests

    async def _generate_integration_tests(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Generate integration tests."""
        components = task.get('components', [])
        architecture = task.get('architecture', {})
        test_scenarios = task.get('scenarios', [])

        tests = {
            'integration_type': 'component_integration',
            'test_scenarios': [],
            'data_flow_tests': [],
            'interface_tests': [],
            'end_to_end_tests': [],
            'confidence': 0.8
        }

        # Generate component interaction tests
        for i, comp1 in enumerate(components):
            for comp2 in components[i+1:]:
                test_scenario = self._create_integration_scenario(comp1, comp2)
                tests['test_scenarios'].append(test_scenario)

        # Generate data flow tests
        if architecture.get('data_flow'):
            tests['data_flow_tests'] = self._create_data_flow_tests(architecture['data_flow'])

        # Generate interface tests
        tests['interface_tests'] = self._create_interface_tests(components)

        return tests

    async def _generate_api_tests(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Generate API tests."""
        api_spec = task.get('api_spec', {})
        endpoints = task.get('endpoints', [])
        auth_type = task.get('auth_type', 'none')

        tests = {
            'test_type': 'api_testing',
            'endpoint_tests': [],
            'authentication_tests': [],
            'error_handling_tests': [],
            'performance_tests': [],
            'security_tests': [],
            'confidence': 0.85
        }

        # Generate endpoint tests
        for endpoint in endpoints:
            endpoint_tests = self._create_endpoint_tests(endpoint)
            tests['endpoint_tests'].extend(endpoint_tests)

        # Generate authentication tests
        if auth_type != 'none':
            tests['authentication_tests'] = self._create_auth_tests(auth_type)

        # Generate error handling tests
        tests['error_handling_tests'] = self._create_error_handling_tests(endpoints)

        # Generate basic performance tests
        tests['performance_tests'] = self._create_api_performance_tests(endpoints)

        # Generate security tests
        tests['security_tests'] = self._create_api_security_tests(endpoints)

        return tests

    async def _generate_performance_tests(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Generate performance tests."""
        system_type = task.get('system_type', 'web_application')
        performance_requirements = task.get('requirements', {})
        load_scenarios = task.get('load_scenarios', [])

        tests = {
            'test_type': 'performance_testing',
            'load_tests': [],
            'stress_tests': [],
            'volume_tests': [],
            'endurance_tests': [],
            'benchmark_tests': [],
            'confidence': 0.8
        }

        # Generate load tests
        tests['load_tests'] = self._create_load_tests(system_type, performance_requirements)

        # Generate stress tests
        tests['stress_tests'] = self._create_stress_tests(system_type)

        # Generate volume tests
        tests['volume_tests'] = self._create_volume_tests(system_type)

        # Generate endurance tests
        tests['endurance_tests'] = self._create_endurance_tests(system_type)

        return tests

    async def _generate_security_tests(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Generate security tests."""
        application_type = task.get('application_type', 'web')
        security_requirements = task.get('security_requirements', [])
        threat_model = task.get('threat_model', {})

        tests = {
            'test_type': 'security_testing',
            'authentication_tests': [],
            'authorization_tests': [],
            'input_validation_tests': [],
            'injection_tests': [],
            'xss_tests': [],
            'csrf_tests': [],
            'data_protection_tests': [],
            'confidence': 0.8
        }

        if application_type == 'web':
            tests['xss_tests'] = self._create_xss_tests()
            tests['csrf_tests'] = self._create_csrf_tests()
            tests['injection_tests'] = self._create_injection_tests()

        tests['input_validation_tests'] = self._create_input_validation_tests()
        tests['authentication_tests'] = self._create_security_auth_tests()
        tests['authorization_tests'] = self._create_authorization_tests()

        return tests

    async def _analyze_existing_tests(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze existing test suite."""
        test_code = task.get('test_code', '')
        source_code = task.get('source_code', '')
        language = task.get('language', 'python')

        analysis = {
            'test_coverage': {},
            'test_quality': {},
            'missing_tests': [],
            'redundant_tests': [],
            'improvement_suggestions': [],
            'confidence': 0.85
        }

        # Analyze test coverage
        analysis['test_coverage'] = self._analyze_test_coverage(test_code, source_code)

        # Analyze test quality
        analysis['test_quality'] = self._analyze_test_quality(test_code, language)

        # Identify missing tests
        analysis['missing_tests'] = self._identify_missing_tests(test_code, source_code)

        # Find redundant tests
        analysis['redundant_tests'] = self._find_redundant_tests(test_code)

        # Generate improvement suggestions
        analysis['improvement_suggestions'] = self._generate_test_improvements(analysis)

        return analysis

    async def _create_test_automation(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Create test automation framework."""
        test_types = task.get('test_types', ['unit', 'integration'])
        ci_platform = task.get('ci_platform', 'github_actions')
        language = task.get('language', 'python')

        automation = {
            'automation_type': 'ci_cd_integration',
            'test_runners': [],
            'ci_configuration': {},
            'test_scripts': [],
            'reporting_setup': {},
            'confidence': 0.8
        }

        # Generate test runners
        automation['test_runners'] = self._create_test_runners(test_types, language)

        # Generate CI configuration
        automation['ci_configuration'] = self._create_ci_config(ci_platform, language, test_types)

        # Generate test scripts
        automation['test_scripts'] = self._create_test_scripts(language, test_types)

        # Setup reporting
        automation['reporting_setup'] = self._create_reporting_setup(language)

        return automation

    async def _generate_python_unit_tests(self, code: str, framework: str) -> Dict[str, Any]:
        """Generate Python unit tests."""
        tests = {
            'language': 'python',
            'framework': framework,
            'test_cases': [],
            'test_suites': []
        }

        # Extract functions from code
        function_pattern = r'def\s+(\w+)\s*\((.*?)\)(?:\s*->\s*([^:]+))?:'
        functions = re.findall(function_pattern, code, re.MULTILINE)

        templates = self.test_frameworks['python'][framework]

        for func_name, args, return_type in functions:
            if not func_name.startswith('_'):  # Skip private functions
                test_cases = self._create_function_test_cases(func_name, args, return_type, templates)
                tests['test_cases'].extend(test_cases)

        # Extract classes
        class_pattern = r'class\s+(\w+).*?:(.*?)(?=\nclass|\n\ndef|\Z)'
        classes = re.findall(class_pattern, code, re.DOTALL | re.MULTILINE)

        for class_name, class_body in classes:
            test_suite = self._create_class_test_suite(class_name, class_body, templates)
            tests['test_suites'].append(test_suite)

        return tests

    async def _generate_javascript_unit_tests(self, code: str, framework: str) -> Dict[str, Any]:
        """Generate JavaScript unit tests."""
        tests = {
            'language': 'javascript',
            'framework': framework,
            'test_cases': [],
            'test_suites': []
        }

        # Extract functions
        js_func_pattern = r'(?:function\s+(\w+)|(?:const|let|var)\s+(\w+)\s*=\s*(?:function|\(.*?\)\s*=>))\s*\((.*?)\)'
        functions = re.findall(js_func_pattern, code, re.MULTILINE)

        templates = self.test_frameworks['javascript'][framework]

        for match in functions:
            func_name = match[0] or match[1]
            args = match[2]

            if func_name:  # Skip anonymous functions
                test_cases = self._create_js_function_tests(func_name, args, templates)
                tests['test_cases'].extend(test_cases)

        return tests

    def _create_function_test_cases(self, func_name: str, args: str, return_type: str, templates: Dict[str, str]) -> List[Dict[str, Any]]:
        """Create test cases for a Python function."""
        test_cases = []

        # Basic functionality test
        test_cases.append({
            'type': 'basic_functionality',
            'name': f'test_{func_name}_basic',
            'description': f'Test basic functionality of {func_name}',
            'code': self._generate_basic_test_code(func_name, args, templates),
            'priority': 'high'
        })

        # Edge cases
        if args:  # Function has parameters
            test_cases.append({
                'type': 'edge_cases',
                'name': f'test_{func_name}_edge_cases',
                'description': f'Test edge cases for {func_name}',
                'code': self._generate_edge_case_tests(func_name, args, templates),
                'priority': 'medium'
            })

        # Error conditions
        test_cases.append({
            'type': 'error_conditions',
            'name': f'test_{func_name}_error_conditions',
            'description': f'Test error conditions for {func_name}',
            'code': self._generate_error_tests(func_name, args, templates),
            'priority': 'medium'
        })

        return test_cases

    def _create_endpoint_tests(self, endpoint: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create tests for an API endpoint."""
        tests = []
        method = endpoint.get('method', 'GET')
        path = endpoint.get('path', '/')

        # Success case test
        tests.append({
            'type': 'success_case',
            'name': f'test_{method.lower()}_{path.replace("/", "_")}_success',
            'method': method,
            'path': path,
            'expected_status': 200,
            'description': f'Test successful {method} request to {path}'
        })

        # Invalid input test
        if method in ['POST', 'PUT', 'PATCH']:
            tests.append({
                'type': 'invalid_input',
                'name': f'test_{method.lower()}_{path.replace("/", "_")}_invalid_input',
                'method': method,
                'path': path,
                'expected_status': 400,
                'description': f'Test {method} request with invalid input to {path}'
            })

        # Not found test
        tests.append({
            'type': 'not_found',
            'name': f'test_{method.lower()}_invalid_path_404',
            'method': method,
            'path': '/invalid/path',
            'expected_status': 404,
            'description': f'Test {method} request to non-existent endpoint'
        })

        return tests

    def _create_load_tests(self, system_type: str, requirements: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create load tests."""
        tests = []

        # Basic load test
        tests.append({
            'type': 'load_test',
            'name': 'basic_load_test',
            'description': 'Test system under normal expected load',
            'users': requirements.get('expected_users', 100),
            'duration': '5m',
            'ramp_up': '1m'
        })

        # Peak load test
        tests.append({
            'type': 'peak_load_test',
            'name': 'peak_load_test',
            'description': 'Test system under peak expected load',
            'users': requirements.get('peak_users', requirements.get('expected_users', 100) * 2),
            'duration': '10m',
            'ramp_up': '2m'
        })

        return tests

    def _create_xss_tests(self) -> List[Dict[str, Any]]:
        """Create XSS security tests."""
        return [
            {
                'type': 'reflected_xss',
                'name': 'test_reflected_xss',
                'payload': '<script>alert("XSS")</script>',
                'description': 'Test for reflected XSS vulnerabilities'
            },
            {
                'type': 'stored_xss',
                'name': 'test_stored_xss',
                'payload': '<img src=x onerror=alert("XSS")>',
                'description': 'Test for stored XSS vulnerabilities'
            }
        ]

    def _create_injection_tests(self) -> List[Dict[str, Any]]:
        """Create injection attack tests."""
        return [
            {
                'type': 'sql_injection',
                'name': 'test_sql_injection',
                'payload': "' OR '1'='1",
                'description': 'Test for SQL injection vulnerabilities'
            },
            {
                'type': 'command_injection',
                'name': 'test_command_injection',
                'payload': '; ls -la',
                'description': 'Test for command injection vulnerabilities'
            }
        ]

    def _estimate_coverage(self, code: str, test_cases: List[Dict[str, Any]]) -> int:
        """Estimate test coverage percentage."""
        # Simple heuristic: count functions/methods vs test cases
        function_count = len(re.findall(r'def\s+\w+\s*\(', code))
        method_count = len(re.findall(r'^\s*def\s+\w+\s*\(', code, re.MULTILINE))

        total_testable_units = function_count + method_count

        if total_testable_units == 0:
            return 0

        # Rough estimate based on test case count
        coverage = min(100, int((len(test_cases) / total_testable_units) * 60))
        return coverage

    def _analyze_test_coverage(self, test_code: str, source_code: str) -> Dict[str, Any]:
        """Analyze test coverage."""
        coverage = {
            'line_coverage': 0,
            'function_coverage': 0,
            'branch_coverage': 0,
            'statement_coverage': 0
        }

        # Extract functions from source code
        source_functions = set(re.findall(r'def\s+(\w+)\s*\(', source_code))

        # Extract tested functions from test code
        tested_functions = set()
        for func in source_functions:
            if func in test_code or f'test_{func}' in test_code:
                tested_functions.add(func)

        if source_functions:
            coverage['function_coverage'] = int((len(tested_functions) / len(source_functions)) * 100)

        # Estimate other coverage types (simplified)
        coverage['line_coverage'] = max(0, coverage['function_coverage'] - 10)
        coverage['branch_coverage'] = max(0, coverage['function_coverage'] - 20)
        coverage['statement_coverage'] = coverage['function_coverage']

        return coverage

    def _analyze_test_quality(self, test_code: str, language: str) -> Dict[str, Any]:
        """Analyze test code quality."""
        quality = {
            'test_count': 0,
            'assertion_count': 0,
            'test_organization': 'good',
            'test_naming': 'good',
            'quality_score': 80
        }

        if language == 'python':
            quality['test_count'] = len(re.findall(r'def\s+test_\w+\s*\(', test_code))
            quality['assertion_count'] = len(re.findall(r'assert|assertEqual|assertTrue', test_code))

        elif language == 'javascript':
            quality['test_count'] = len(re.findall(r'test\(|it\(', test_code))
            quality['assertion_count'] = len(re.findall(r'expect\(|assert', test_code))

        # Calculate quality score
        if quality['test_count'] > 0:
            assertions_per_test = quality['assertion_count'] / quality['test_count']
            if assertions_per_test >= 1:
                quality['quality_score'] = min(100, 60 + int(assertions_per_test * 10))
            else:
                quality['quality_score'] = 40

        return quality

    def _determine_next_agent(self, result: Dict[str, Any], task: Dict[str, Any]) -> Optional[str]:
        """Determine the next agent based on testing results."""
        task_type = task.get('type')

        # If we generated performance tests, might need performance agent
        if task_type == 'performance_testing':
            return 'performance_agent'

        # If we found security issues, might need documentation
        if task_type == 'security_testing' and result.get('security_tests'):
            return 'documentation_agent'

        # If test coverage is low, might need code agent
        if result.get('coverage_estimate', 0) < 70:
            return 'code_agent'

        # Otherwise proceed to response agent
        return 'response_agent'

    # Additional helper methods...
    def _generate_basic_test_code(self, func_name: str, args: str, templates: Dict[str, str]) -> str:
        """Generate basic test code."""
        if 'pytest' in templates.get('function_template', ''):
            return f"""
{templates['function_template'].format(function_name=func_name)}
    # Test basic functionality
    result = {func_name}({self._generate_sample_args(args)})
    {templates['assert_template'].format(actual='result', expected='expected_result')}
"""
        else:
            return f"""
{templates['method_template'].format(method_name=func_name)}
    # Test basic functionality
    result = {func_name}({self._generate_sample_args(args)})
    {templates['assert_template'].format(actual='result', expected='expected_result')}
"""

    def _generate_sample_args(self, args: str) -> str:
        """Generate sample arguments for testing."""
        if not args.strip():
            return ""

        # Simple heuristic for generating sample args
        arg_list = [arg.strip().split(':')[0].strip() for arg in args.split(',') if arg.strip()]
        sample_args = []

        for arg in arg_list:
            if arg != 'self':
                sample_args.append(f'test_{arg}')

        return ', '.join(sample_args)

    async def get_status(self) -> Dict[str, Any]:
        """Get agent status."""
        return {
            'agent_id': self.agent_id,
            'status': 'ready',
            'capabilities': self.capabilities,
            'supported_frameworks': list(self.test_frameworks.keys()),
            'cache_size': len(self.test_cache)
        }