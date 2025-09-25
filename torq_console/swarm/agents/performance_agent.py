"""
Performance Agent for Advanced Swarm Intelligence System.

This agent specializes in performance analysis, optimization recommendations,
benchmarking, and system performance monitoring across different metrics.
"""

import asyncio
from typing import Dict, List, Any, Optional, Tuple
import logging
from datetime import datetime
import re
import json
import time


class PerformanceAgent:
    """Specialized agent for performance analysis and optimization."""

    def __init__(self, llm_provider=None):
        """
        Initialize PerformanceAgent.

        Args:
            llm_provider: LLM provider for performance analysis
        """
        self.llm_provider = llm_provider
        self.logger = logging.getLogger(__name__)

        # Agent specialization
        self.agent_id = "performance_agent"
        self.capabilities = [
            "performance_analysis",
            "bottleneck_identification",
            "optimization_recommendations",
            "benchmark_creation",
            "resource_monitoring",
            "scalability_analysis",
            "load_testing_design",
            "performance_profiling"
        ]

        # Performance metrics and thresholds
        self.performance_metrics = {
            'response_time': {
                'excellent': 100,  # ms
                'good': 300,
                'acceptable': 1000,
                'poor': 3000
            },
            'throughput': {
                'unit': 'requests/second',
                'minimum': 100,
                'target': 500,
                'optimal': 1000
            },
            'memory_usage': {
                'unit': 'MB',
                'low': 100,
                'normal': 500,
                'high': 1000,
                'critical': 2000
            },
            'cpu_usage': {
                'unit': 'percentage',
                'low': 25,
                'normal': 50,
                'high': 75,
                'critical': 90
            }
        }

        # Optimization patterns and recommendations
        self.optimization_patterns = {
            'database': [
                'add_indexes',
                'query_optimization',
                'connection_pooling',
                'caching',
                'pagination'
            ],
            'api': [
                'response_compression',
                'request_batching',
                'async_processing',
                'rate_limiting',
                'cdn_usage'
            ],
            'frontend': [
                'code_splitting',
                'lazy_loading',
                'image_optimization',
                'minification',
                'caching_strategies'
            ],
            'backend': [
                'algorithm_optimization',
                'memory_management',
                'async_operations',
                'load_balancing',
                'microservices'
            ]
        }

        # Performance cache for analysis results
        self.performance_cache = {}
        self.max_cache_size = 100

    async def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a performance analysis task.

        Args:
            task: Task dictionary with performance analysis requirements

        Returns:
            Performance analysis results with recommendations
        """
        start_time = datetime.now()
        task_type = task.get('type', 'performance_analysis')

        self.logger.info(f"Processing {task_type} performance task")

        try:
            if task_type == 'performance_analysis':
                result = await self._analyze_performance(task)
            elif task_type == 'bottleneck_identification':
                result = await self._identify_bottlenecks(task)
            elif task_type == 'optimization_recommendations':
                result = await self._generate_optimizations(task)
            elif task_type == 'benchmark_creation':
                result = await self._create_benchmarks(task)
            elif task_type == 'scalability_analysis':
                result = await self._analyze_scalability(task)
            elif task_type == 'resource_monitoring':
                result = await self._setup_monitoring(task)
            elif task_type == 'load_test_design':
                result = await self._design_load_tests(task)
            else:
                result = await self._general_performance_task(task)

            # Determine next agent
            next_agent = self._determine_next_agent(result, task)

            processing_time = (datetime.now() - start_time).total_seconds()

            return {
                'agent_id': self.agent_id,
                'task_type': task_type,
                'results': result,
                'next_agent': next_agent,
                'processing_time': processing_time,
                'confidence': result.get('confidence', 0.8),
                'metadata': {
                    'recommendations_count': len(result.get('recommendations', [])),
                    'bottlenecks_found': len(result.get('bottlenecks', [])),
                    'performance_score': result.get('performance_score', 0)
                }
            }

        except Exception as e:
            self.logger.error(f"Performance analysis failed: {e}")
            return {
                'agent_id': self.agent_id,
                'task_type': task_type,
                'error': str(e),
                'next_agent': 'response_agent',
                'processing_time': (datetime.now() - start_time).total_seconds()
            }

    async def _analyze_performance(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Perform comprehensive performance analysis."""
        code = task.get('code', '')
        system_type = task.get('system_type', 'web_application')
        performance_data = task.get('performance_data', {})

        analysis = {
            'system_type': system_type,
            'performance_score': 0,
            'metrics_analysis': {},
            'bottlenecks': [],
            'recommendations': [],
            'optimization_opportunities': [],
            'confidence': 0.85
        }

        # Analyze performance metrics
        if performance_data:
            analysis['metrics_analysis'] = self._analyze_metrics(performance_data)
            analysis['performance_score'] = self._calculate_performance_score(analysis['metrics_analysis'])

        # Code-based analysis
        if code:
            code_analysis = await self._analyze_code_performance(code)
            analysis['bottlenecks'].extend(code_analysis.get('bottlenecks', []))
            analysis['optimization_opportunities'].extend(code_analysis.get('optimizations', []))

        # Generate recommendations
        analysis['recommendations'] = self._generate_performance_recommendations(analysis)

        return analysis

    async def _identify_bottlenecks(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Identify performance bottlenecks."""
        system_metrics = task.get('metrics', {})
        application_logs = task.get('logs', [])
        profiling_data = task.get('profiling_data', {})

        bottlenecks = {
            'identified_bottlenecks': [],
            'severity_levels': {},
            'impact_analysis': {},
            'resolution_priority': [],
            'confidence': 0.8
        }

        # Analyze system metrics for bottlenecks
        if system_metrics:
            metric_bottlenecks = self._find_metric_bottlenecks(system_metrics)
            bottlenecks['identified_bottlenecks'].extend(metric_bottlenecks)

        # Analyze application logs
        if application_logs:
            log_bottlenecks = self._analyze_log_bottlenecks(application_logs)
            bottlenecks['identified_bottlenecks'].extend(log_bottlenecks)

        # Analyze profiling data
        if profiling_data:
            profile_bottlenecks = self._analyze_profiling_bottlenecks(profiling_data)
            bottlenecks['identified_bottlenecks'].extend(profile_bottlenecks)

        # Categorize by severity
        bottlenecks['severity_levels'] = self._categorize_by_severity(bottlenecks['identified_bottlenecks'])

        # Analyze impact
        bottlenecks['impact_analysis'] = self._analyze_bottleneck_impact(bottlenecks['identified_bottlenecks'])

        # Prioritize resolution
        bottlenecks['resolution_priority'] = self._prioritize_bottlenecks(bottlenecks['identified_bottlenecks'])

        return bottlenecks

    async def _generate_optimizations(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Generate optimization recommendations."""
        system_type = task.get('system_type', 'web_application')
        current_performance = task.get('current_performance', {})
        target_performance = task.get('target_performance', {})
        constraints = task.get('constraints', [])

        optimizations = {
            'system_type': system_type,
            'optimization_categories': {},
            'recommended_actions': [],
            'implementation_roadmap': {},
            'expected_improvements': {},
            'confidence': 0.8
        }

        # Get optimization patterns for system type
        patterns = self.optimization_patterns.get(system_type, self.optimization_patterns['backend'])

        for category in ['immediate', 'short_term', 'long_term']:
            optimizations['optimization_categories'][category] = self._categorize_optimizations(
                patterns, category, current_performance
            )

        # Generate specific recommendations
        optimizations['recommended_actions'] = self._create_optimization_actions(
            optimizations['optimization_categories']
        )

        # Create implementation roadmap
        optimizations['implementation_roadmap'] = self._create_implementation_roadmap(
            optimizations['recommended_actions']
        )

        # Estimate expected improvements
        optimizations['expected_improvements'] = self._estimate_improvements(
            optimizations['recommended_actions'], current_performance
        )

        return optimizations

    async def _create_benchmarks(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Create performance benchmarks."""
        system_type = task.get('system_type', 'web_application')
        components = task.get('components', [])
        performance_requirements = task.get('requirements', {})

        benchmarks = {
            'benchmark_suite': [],
            'performance_baselines': {},
            'test_scenarios': [],
            'measurement_tools': [],
            'reporting_framework': {},
            'confidence': 0.8
        }

        # Create benchmark tests for each component
        for component in components:
            component_benchmarks = self._create_component_benchmarks(component, system_type)
            benchmarks['benchmark_suite'].extend(component_benchmarks)

        # Establish performance baselines
        benchmarks['performance_baselines'] = self._establish_baselines(
            system_type, performance_requirements
        )

        # Create test scenarios
        benchmarks['test_scenarios'] = self._create_benchmark_scenarios(system_type)

        # Recommend measurement tools
        benchmarks['measurement_tools'] = self._recommend_measurement_tools(system_type)

        # Setup reporting framework
        benchmarks['reporting_framework'] = self._setup_benchmark_reporting()

        return benchmarks

    async def _analyze_scalability(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze system scalability."""
        current_capacity = task.get('current_capacity', {})
        growth_projections = task.get('growth_projections', {})
        architecture = task.get('architecture', {})

        scalability = {
            'scalability_assessment': {},
            'bottleneck_predictions': [],
            'scaling_recommendations': {},
            'capacity_planning': {},
            'architecture_suggestions': [],
            'confidence': 0.8
        }

        # Assess current scalability
        scalability['scalability_assessment'] = self._assess_current_scalability(
            current_capacity, architecture
        )

        # Predict future bottlenecks
        scalability['bottleneck_predictions'] = self._predict_scalability_bottlenecks(
            current_capacity, growth_projections
        )

        # Generate scaling recommendations
        scalability['scaling_recommendations'] = self._generate_scaling_recommendations(
            scalability['bottleneck_predictions'], architecture
        )

        # Create capacity planning
        scalability['capacity_planning'] = self._create_capacity_plan(
            growth_projections, current_capacity
        )

        # Suggest architectural improvements
        scalability['architecture_suggestions'] = self._suggest_architecture_improvements(
            architecture, scalability['scaling_recommendations']
        )

        return scalability

    async def _analyze_code_performance(self, code: str) -> Dict[str, Any]:
        """Analyze code for performance issues."""
        analysis = {
            'bottlenecks': [],
            'optimizations': [],
            'complexity_analysis': {},
            'resource_usage_patterns': []
        }

        # Detect common performance anti-patterns
        analysis['bottlenecks'] = self._detect_code_bottlenecks(code)

        # Identify optimization opportunities
        analysis['optimizations'] = self._identify_code_optimizations(code)

        # Analyze algorithmic complexity
        analysis['complexity_analysis'] = self._analyze_algorithmic_complexity(code)

        # Analyze resource usage patterns
        analysis['resource_usage_patterns'] = self._analyze_resource_patterns(code)

        return analysis

    def _analyze_metrics(self, performance_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze performance metrics."""
        metrics_analysis = {}

        for metric_name, metric_value in performance_data.items():
            if metric_name in self.performance_metrics:
                thresholds = self.performance_metrics[metric_name]
                analysis = self._evaluate_metric(metric_value, thresholds)
                metrics_analysis[metric_name] = analysis

        return metrics_analysis

    def _evaluate_metric(self, value: float, thresholds: Dict[str, float]) -> Dict[str, Any]:
        """Evaluate a single performance metric."""
        evaluation = {
            'value': value,
            'status': 'unknown',
            'score': 0,
            'recommendations': []
        }

        # Determine status based on thresholds
        if 'excellent' in thresholds and value <= thresholds['excellent']:
            evaluation['status'] = 'excellent'
            evaluation['score'] = 100
        elif 'good' in thresholds and value <= thresholds['good']:
            evaluation['status'] = 'good'
            evaluation['score'] = 80
        elif 'acceptable' in thresholds and value <= thresholds['acceptable']:
            evaluation['status'] = 'acceptable'
            evaluation['score'] = 60
            evaluation['recommendations'].append('Consider optimization to improve performance')
        else:
            evaluation['status'] = 'poor'
            evaluation['score'] = 30
            evaluation['recommendations'].append('Immediate optimization required')

        return evaluation

    def _calculate_performance_score(self, metrics_analysis: Dict[str, Any]) -> int:
        """Calculate overall performance score."""
        if not metrics_analysis:
            return 50  # Default score

        total_score = sum(analysis['score'] for analysis in metrics_analysis.values())
        return int(total_score / len(metrics_analysis))

    def _detect_code_bottlenecks(self, code: str) -> List[Dict[str, Any]]:
        """Detect performance bottlenecks in code."""
        bottlenecks = []

        # Nested loops detection
        nested_loops = len(re.findall(r'for.*?:\s*.*?for.*?:', code, re.DOTALL))
        if nested_loops > 0:
            bottlenecks.append({
                'type': 'nested_loops',
                'severity': 'high',
                'count': nested_loops,
                'description': 'Nested loops detected - potential O(n²) complexity',
                'recommendation': 'Consider algorithmic optimization or caching'
            })

        # Database queries in loops
        if re.search(r'for.*?:\s*.*?query|select.*?in.*?for', code, re.IGNORECASE | re.DOTALL):
            bottlenecks.append({
                'type': 'n_plus_one_query',
                'severity': 'high',
                'description': 'Potential N+1 query problem detected',
                'recommendation': 'Use bulk queries or eager loading'
            })

        # Synchronous I/O operations
        sync_io_patterns = ['requests.get', 'urllib.request', 'open(', 'file.read']
        for pattern in sync_io_patterns:
            if pattern in code:
                bottlenecks.append({
                    'type': 'synchronous_io',
                    'severity': 'medium',
                    'pattern': pattern,
                    'description': 'Synchronous I/O operation detected',
                    'recommendation': 'Consider using async/await or threading'
                })

        # Large data structures in memory
        large_data_patterns = ['list(range(', 'range(.*?000']
        for pattern in large_data_patterns:
            if re.search(pattern, code):
                bottlenecks.append({
                    'type': 'memory_intensive',
                    'severity': 'medium',
                    'description': 'Large data structure creation detected',
                    'recommendation': 'Consider generators or iterators for memory efficiency'
                })

        return bottlenecks

    def _identify_code_optimizations(self, code: str) -> List[Dict[str, Any]]:
        """Identify code optimization opportunities."""
        optimizations = []

        # List comprehensions opportunities
        if re.search(r'for\s+\w+\s+in.*?:\s*.*?\.append\(', code, re.DOTALL):
            optimizations.append({
                'type': 'list_comprehension',
                'impact': 'medium',
                'description': 'Replace for loop with list comprehension',
                'benefit': 'Improved performance and readability'
            })

        # Caching opportunities
        if re.search(r'def\s+\w+.*?:\s*.*?expensive_operation', code, re.DOTALL):
            optimizations.append({
                'type': 'function_caching',
                'impact': 'high',
                'description': 'Add caching to expensive function calls',
                'benefit': 'Reduce redundant computations'
            })

        # String concatenation optimization
        if '+=' in code and 'str' in code:
            optimizations.append({
                'type': 'string_optimization',
                'impact': 'medium',
                'description': 'Use join() instead of += for string concatenation',
                'benefit': 'Better memory efficiency for large strings'
            })

        return optimizations

    def _find_metric_bottlenecks(self, metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find bottlenecks from system metrics."""
        bottlenecks = []

        # Check CPU usage
        cpu_usage = metrics.get('cpu_usage', 0)
        if cpu_usage > self.performance_metrics['cpu_usage']['critical']:
            bottlenecks.append({
                'type': 'cpu_bottleneck',
                'severity': 'critical',
                'value': cpu_usage,
                'description': f'CPU usage at {cpu_usage}% - critical level',
                'recommendation': 'Investigate high CPU processes and optimize algorithms'
            })

        # Check memory usage
        memory_usage = metrics.get('memory_usage', 0)
        if memory_usage > self.performance_metrics['memory_usage']['critical']:
            bottlenecks.append({
                'type': 'memory_bottleneck',
                'severity': 'critical',
                'value': memory_usage,
                'description': f'Memory usage at {memory_usage}MB - critical level',
                'recommendation': 'Investigate memory leaks and optimize data structures'
            })

        # Check response times
        response_time = metrics.get('response_time', 0)
        if response_time > self.performance_metrics['response_time']['poor']:
            bottlenecks.append({
                'type': 'response_time_bottleneck',
                'severity': 'high',
                'value': response_time,
                'description': f'Response time at {response_time}ms - poor performance',
                'recommendation': 'Optimize queries, add caching, or scale resources'
            })

        return bottlenecks

    def _generate_performance_recommendations(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate performance recommendations based on analysis."""
        recommendations = []

        performance_score = analysis.get('performance_score', 50)

        if performance_score < 60:
            recommendations.append({
                'priority': 'high',
                'category': 'optimization',
                'title': 'Critical Performance Issues Detected',
                'description': 'System performance is below acceptable levels',
                'actions': [
                    'Identify and fix primary bottlenecks',
                    'Implement caching strategies',
                    'Optimize database queries',
                    'Consider infrastructure scaling'
                ]
            })

        # Add specific recommendations based on bottlenecks
        bottlenecks = analysis.get('bottlenecks', [])
        for bottleneck in bottlenecks:
            if bottleneck.get('severity') == 'high':
                recommendations.append({
                    'priority': 'high',
                    'category': 'bottleneck_resolution',
                    'title': f'Address {bottleneck.get("type", "Unknown")} Bottleneck',
                    'description': bottleneck.get('description', ''),
                    'actions': [bottleneck.get('recommendation', 'Investigate and optimize')]
                })

        return recommendations

    def _determine_next_agent(self, result: Dict[str, Any], task: Dict[str, Any]) -> Optional[str]:
        """Determine the next agent based on performance analysis results."""
        # If critical performance issues found, might need code agent
        bottlenecks = result.get('bottlenecks', [])
        critical_bottlenecks = [b for b in bottlenecks if b.get('severity') == 'critical']

        if critical_bottlenecks:
            return 'code_agent'

        # If we have optimization recommendations, might need documentation
        recommendations = result.get('recommendations', [])
        if len(recommendations) > 3:
            return 'documentation_agent'

        # Otherwise proceed to synthesis
        return 'synthesis_agent'

    # Additional helper methods for completeness
    def _categorize_optimizations(self, patterns: List[str], category: str, current_performance: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Categorize optimizations by implementation timeline."""
        categorized = []

        timeline_mapping = {
            'immediate': ['caching', 'query_optimization', 'minification'],
            'short_term': ['async_processing', 'load_balancing', 'code_splitting'],
            'long_term': ['microservices', 'architecture_redesign', 'infrastructure_scaling']
        }

        relevant_patterns = timeline_mapping.get(category, patterns)

        for pattern in relevant_patterns:
            if pattern in patterns:
                categorized.append({
                    'pattern': pattern,
                    'estimated_effort': self._estimate_implementation_effort(pattern),
                    'expected_impact': self._estimate_performance_impact(pattern)
                })

        return categorized

    def _estimate_implementation_effort(self, pattern: str) -> str:
        """Estimate implementation effort for optimization pattern."""
        effort_mapping = {
            'caching': 'low',
            'query_optimization': 'medium',
            'microservices': 'high',
            'load_balancing': 'medium',
            'async_processing': 'medium'
        }
        return effort_mapping.get(pattern, 'medium')

    def _estimate_performance_impact(self, pattern: str) -> str:
        """Estimate performance impact of optimization pattern."""
        impact_mapping = {
            'caching': 'high',
            'query_optimization': 'high',
            'microservices': 'medium',
            'load_balancing': 'high',
            'async_processing': 'medium'
        }
        return impact_mapping.get(pattern, 'medium')

    async def get_status(self) -> Dict[str, Any]:
        """Get agent status."""
        return {
            'agent_id': self.agent_id,
            'status': 'ready',
            'capabilities': self.capabilities,
            'supported_metrics': list(self.performance_metrics.keys()),
            'optimization_patterns': sum(len(patterns) for patterns in self.optimization_patterns.values()),
            'cache_size': len(self.performance_cache)
        }