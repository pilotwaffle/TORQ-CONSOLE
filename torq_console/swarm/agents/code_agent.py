"""
Code Analysis Agent for Advanced Swarm Intelligence System.

This agent specializes in code analysis, refactoring, optimization,
and development assistance with deep understanding of programming patterns.
"""

import asyncio
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime
import re
import ast

# Import Claude Code compatible tools
from ...utils.file_tools import glob_search
from ...utils.search_tools import grep_search
from ...utils.edit_tools import multi_edit


class CodeAgent:
    """Specialized agent for code analysis and development."""

    def __init__(self, llm_provider=None):
        """
        Initialize CodeAgent.

        Args:
            llm_provider: LLM provider for code analysis capabilities
        """
        self.llm_provider = llm_provider
        self.logger = logging.getLogger(__name__)

        # Agent specialization
        self.agent_id = "code_agent"
        self.capabilities = [
            "code_analysis",
            "refactoring",
            "optimization",
            "debugging",
            "pattern_recognition",
            "architecture_review",
            "security_analysis",
            "file_search",      # New: Glob tool
            "code_search",      # New: Grep tool
            "batch_editing"     # New: MultiEdit tool
        ]

        # Code analysis patterns
        self.code_patterns = {
            'python': {
                'functions': r'def\s+(\w+)\s*\(',
                'classes': r'class\s+(\w+)\s*[\(:]',
                'imports': r'(?:from\s+[\w.]+\s+)?import\s+[\w.,\s]+',
                'comments': r'#.*$|""".*?"""',
                'complexity_indicators': ['for', 'while', 'if', 'elif', 'try', 'except']
            },
            'javascript': {
                'functions': r'(?:function\s+(\w+)|(\w+)\s*=\s*(?:function|\([^)]*\)\s*=>))',
                'classes': r'class\s+(\w+)',
                'imports': r'import\s+.*?from\s+[\'"].*?[\'"]',
                'comments': r'//.*$|/\*.*?\*/',
                'complexity_indicators': ['for', 'while', 'if', 'else', 'try', 'catch', 'switch']
            }
        }

        # Memory for code context
        self.code_analysis_cache = {}
        self.max_cache_size = 50

    async def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a code analysis task.

        Args:
            task: Task dictionary with code and analysis requirements

        Returns:
            Analysis results with next agent recommendations
        """
        start_time = datetime.now()
        task_type = task.get('type', 'code_analysis')

        self.logger.info(f"Processing {task_type} task")

        try:
            if task_type == 'code_analysis':
                result = await self._analyze_code(task)
            elif task_type == 'code_review':
                result = await self._review_code(task)
            elif task_type == 'optimization':
                result = await self._optimize_code(task)
            elif task_type == 'debugging':
                result = await self._debug_code(task)
            elif task_type == 'file_search':
                result = await self._search_files(task)
            elif task_type == 'code_search':
                result = await self._search_code(task)
            elif task_type == 'batch_editing':
                result = await self._batch_edit(task)
            else:
                result = await self._general_code_task(task)

            # Determine next agent based on results
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
                    'code_analyzed': result.get('lines_analyzed', 0),
                    'issues_found': len(result.get('issues', [])),
                    'recommendations': len(result.get('recommendations', []))
                }
            }

        except Exception as e:
            self.logger.error(f"Code analysis failed: {e}")
            return {
                'agent_id': self.agent_id,
                'task_type': task_type,
                'error': str(e),
                'next_agent': 'response_agent',
                'processing_time': (datetime.now() - start_time).total_seconds()
            }

    async def _analyze_code(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Perform comprehensive code analysis."""
        code = task.get('code', '')
        language = task.get('language', 'python')

        if not code:
            return {'error': 'No code provided for analysis'}

        analysis = {
            'language': language,
            'lines_analyzed': len(code.splitlines()),
            'structure': {},
            'complexity': {},
            'issues': [],
            'recommendations': [],
            'confidence': 0.9
        }

        # Structural analysis
        if language in self.code_patterns:
            patterns = self.code_patterns[language]
            analysis['structure'] = {
                'functions': len(re.findall(patterns['functions'], code, re.MULTILINE)),
                'classes': len(re.findall(patterns['classes'], code, re.MULTILINE)),
                'imports': len(re.findall(patterns['imports'], code, re.MULTILINE))
            }

            # Complexity analysis
            complexity_count = sum(
                code.lower().count(indicator)
                for indicator in patterns['complexity_indicators']
            )
            analysis['complexity']['cyclomatic'] = complexity_count

        # Code quality checks
        analysis['issues'] = self._detect_code_issues(code, language)
        analysis['recommendations'] = self._generate_recommendations(analysis)

        # Cache analysis
        cache_key = f"{language}_{hash(code)}"
        self.code_analysis_cache[cache_key] = analysis

        return analysis

    async def _review_code(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Perform code review with best practices."""
        code = task.get('code', '')
        review_type = task.get('review_type', 'general')

        review = {
            'review_type': review_type,
            'security_issues': [],
            'performance_issues': [],
            'maintainability_issues': [],
            'style_issues': [],
            'overall_score': 0,
            'confidence': 0.85
        }

        if review_type == 'security':
            review['security_issues'] = self._security_analysis(code)
        elif review_type == 'performance':
            review['performance_issues'] = self._performance_analysis(code)
        else:
            # Comprehensive review
            review['security_issues'] = self._security_analysis(code)
            review['performance_issues'] = self._performance_analysis(code)
            review['maintainability_issues'] = self._maintainability_analysis(code)
            review['style_issues'] = self._style_analysis(code)

        # Calculate overall score
        total_issues = sum(len(issues) for issues in [
            review['security_issues'],
            review['performance_issues'],
            review['maintainability_issues'],
            review['style_issues']
        ])
        review['overall_score'] = max(0, 100 - (total_issues * 10))

        return review

    async def _optimize_code(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Generate code optimization suggestions."""
        code = task.get('code', '')
        optimization_focus = task.get('focus', 'general')

        optimizations = {
            'focus': optimization_focus,
            'suggestions': [],
            'potential_improvements': [],
            'estimated_performance_gain': '0-5%',
            'confidence': 0.8
        }

        # Analyze for common optimization opportunities
        if 'loop' in optimization_focus or optimization_focus == 'general':
            loop_optimizations = self._analyze_loops(code)
            optimizations['suggestions'].extend(loop_optimizations)

        if 'memory' in optimization_focus or optimization_focus == 'general':
            memory_optimizations = self._analyze_memory_usage(code)
            optimizations['suggestions'].extend(memory_optimizations)

        if 'algorithm' in optimization_focus or optimization_focus == 'general':
            algorithm_optimizations = self._analyze_algorithms(code)
            optimizations['suggestions'].extend(algorithm_optimizations)

        return optimizations

    async def _debug_code(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze code for debugging assistance."""
        code = task.get('code', '')
        error_message = task.get('error', '')

        debug_info = {
            'error_analysis': {},
            'potential_causes': [],
            'debugging_steps': [],
            'fixes': [],
            'confidence': 0.8
        }

        if error_message:
            debug_info['error_analysis'] = self._analyze_error(error_message, code)
            debug_info['potential_causes'] = self._identify_error_causes(error_message, code)
            debug_info['fixes'] = self._suggest_fixes(error_message, code)

        debug_info['debugging_steps'] = self._generate_debug_steps(code, error_message)

        return debug_info

    def _detect_code_issues(self, code: str, language: str) -> List[Dict[str, Any]]:
        """Detect common code issues."""
        issues = []

        # Generic issues
        lines = code.splitlines()
        for i, line in enumerate(lines, 1):
            if len(line) > 120:
                issues.append({
                    'type': 'style',
                    'line': i,
                    'message': 'Line too long (>120 characters)',
                    'severity': 'low'
                })

            if line.strip().startswith('TODO') or line.strip().startswith('FIXME'):
                issues.append({
                    'type': 'maintenance',
                    'line': i,
                    'message': 'TODO/FIXME comment found',
                    'severity': 'medium'
                })

        # Language-specific issues
        if language == 'python':
            issues.extend(self._python_specific_issues(code))
        elif language == 'javascript':
            issues.extend(self._javascript_specific_issues(code))

        return issues

    def _python_specific_issues(self, code: str) -> List[Dict[str, Any]]:
        """Detect Python-specific issues."""
        issues = []

        # Check for common Python antipatterns
        if 'eval(' in code:
            issues.append({
                'type': 'security',
                'message': 'Use of eval() detected - security risk',
                'severity': 'high'
            })

        if re.search(r'except\s*:', code):
            issues.append({
                'type': 'best_practice',
                'message': 'Bare except clause - should specify exception types',
                'severity': 'medium'
            })

        return issues

    def _javascript_specific_issues(self, code: str) -> List[Dict[str, Any]]:
        """Detect JavaScript-specific issues."""
        issues = []

        if '==' in code and '===' not in code:
            issues.append({
                'type': 'best_practice',
                'message': 'Use === instead of == for strict equality',
                'severity': 'low'
            })

        return issues

    def _security_analysis(self, code: str) -> List[Dict[str, Any]]:
        """Analyze code for security vulnerabilities."""
        security_issues = []

        # Common security patterns
        dangerous_functions = ['eval', 'exec', 'subprocess.call', 'os.system']
        for func in dangerous_functions:
            if func in code:
                security_issues.append({
                    'type': 'dangerous_function',
                    'function': func,
                    'severity': 'high',
                    'message': f'Potentially dangerous function {func} detected'
                })

        return security_issues

    def _performance_analysis(self, code: str) -> List[Dict[str, Any]]:
        """Analyze code for performance issues."""
        performance_issues = []

        # Detect potential performance bottlenecks
        if 'for ' in code and 'append(' in code:
            performance_issues.append({
                'type': 'inefficient_loop',
                'severity': 'medium',
                'message': 'Consider using list comprehension instead of append in loop'
            })

        return performance_issues

    def _maintainability_analysis(self, code: str) -> List[Dict[str, Any]]:
        """Analyze code maintainability."""
        maintainability_issues = []

        # Check function length
        functions = re.findall(r'def\s+\w+\s*\([^)]*\):(.*?)(?=\n(?:def|\Z))', code, re.DOTALL)
        for func in functions:
            lines = len([line for line in func.split('\n') if line.strip()])
            if lines > 50:
                maintainability_issues.append({
                    'type': 'long_function',
                    'severity': 'medium',
                    'message': f'Function has {lines} lines - consider breaking down'
                })

        return maintainability_issues

    def _style_analysis(self, code: str) -> List[Dict[str, Any]]:
        """Analyze code style."""
        style_issues = []

        lines = code.splitlines()
        for i, line in enumerate(lines, 1):
            # Check indentation consistency
            if line.startswith(' ') and not line.startswith('    '):
                if len(line) - len(line.lstrip()) % 4 != 0:
                    style_issues.append({
                        'type': 'indentation',
                        'line': i,
                        'severity': 'low',
                        'message': 'Inconsistent indentation'
                    })

        return style_issues

    def _generate_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate code improvement recommendations."""
        recommendations = []

        if analysis.get('complexity', {}).get('cyclomatic', 0) > 10:
            recommendations.append("Consider breaking down complex functions to improve readability")

        if len(analysis.get('issues', [])) > 0:
            recommendations.append("Address code quality issues identified in analysis")

        structure = analysis.get('structure', {})
        if structure.get('functions', 0) == 0 and structure.get('classes', 0) == 0:
            recommendations.append("Consider organizing code into functions or classes")

        return recommendations

    def _determine_next_agent(self, result: Dict[str, Any], task: Dict[str, Any]) -> Optional[str]:
        """Determine the next agent based on analysis results."""
        # If high-severity issues found, go to documentation agent
        issues = result.get('issues', [])
        high_severity_issues = [i for i in issues if i.get('severity') == 'high']

        if high_severity_issues:
            return 'documentation_agent'

        # If optimization suggestions, go to performance agent
        if result.get('suggestions') or result.get('potential_improvements'):
            return 'performance_agent'

        # Otherwise proceed to synthesis
        return 'synthesis_agent'

    async def get_status(self) -> Dict[str, Any]:
        """Get agent status."""
        return {
            'agent_id': self.agent_id,
            'status': 'ready',
            'capabilities': self.capabilities,
            'cache_size': len(self.code_analysis_cache),
            'supported_languages': list(self.code_patterns.keys())
        }

    # Additional helper methods for optimization analysis
    def _analyze_loops(self, code: str) -> List[Dict[str, Any]]:
        """Analyze loops for optimization opportunities."""
        suggestions = []

        # Look for nested loops
        nested_loop_pattern = r'for.*?:\s*.*?for.*?:'
        if re.search(nested_loop_pattern, code, re.DOTALL):
            suggestions.append({
                'type': 'loop_optimization',
                'message': 'Nested loops detected - consider algorithmic optimization',
                'priority': 'high'
            })

        return suggestions

    def _analyze_memory_usage(self, code: str) -> List[Dict[str, Any]]:
        """Analyze memory usage patterns."""
        suggestions = []

        # Look for large list operations
        if '.append(' in code and 'for ' in code:
            suggestions.append({
                'type': 'memory_optimization',
                'message': 'Consider using list comprehension for better memory efficiency',
                'priority': 'medium'
            })

        return suggestions

    def _analyze_algorithms(self, code: str) -> List[Dict[str, Any]]:
        """Analyze algorithmic complexity."""
        suggestions = []

        # Look for sorting operations
        if '.sort(' in code or 'sorted(' in code:
            suggestions.append({
                'type': 'algorithm_optimization',
                'message': 'Review sorting algorithm choice for large datasets',
                'priority': 'low'
            })

        return suggestions

    def _analyze_error(self, error_message: str, code: str) -> Dict[str, Any]:
        """Analyze error message in context of code."""
        return {
            'error_type': self._classify_error(error_message),
            'likely_location': self._find_error_location(error_message, code),
            'context': self._extract_error_context(error_message)
        }

    def _classify_error(self, error_message: str) -> str:
        """Classify the type of error."""
        if 'SyntaxError' in error_message:
            return 'syntax'
        elif 'NameError' in error_message:
            return 'undefined_variable'
        elif 'TypeError' in error_message:
            return 'type_mismatch'
        elif 'IndexError' in error_message:
            return 'index_out_of_bounds'
        else:
            return 'runtime'

    def _find_error_location(self, error_message: str, code: str) -> Optional[int]:
        """Find likely error location in code."""
        # Extract line number from error message if present
        line_match = re.search(r'line (\d+)', error_message)
        if line_match:
            return int(line_match.group(1))
        return None

    def _extract_error_context(self, error_message: str) -> Dict[str, Any]:
        """Extract contextual information from error."""
        return {
            'message': error_message,
            'extracted_info': re.findall(r"'([^']*)'", error_message)
        }

    def _identify_error_causes(self, error_message: str, code: str) -> List[str]:
        """Identify potential causes of the error."""
        causes = []
        error_type = self._classify_error(error_message)

        if error_type == 'syntax':
            causes.append("Missing or mismatched parentheses, brackets, or quotes")
            causes.append("Incorrect indentation")
            causes.append("Invalid Python syntax")
        elif error_type == 'undefined_variable':
            causes.append("Variable used before being defined")
            causes.append("Typo in variable name")
            causes.append("Variable out of scope")

        return causes

    def _suggest_fixes(self, error_message: str, code: str) -> List[Dict[str, Any]]:
        """Suggest specific fixes for the error."""
        fixes = []
        error_type = self._classify_error(error_message)

        if error_type == 'syntax':
            fixes.append({
                'fix': "Check for matching parentheses and brackets",
                'priority': 'high',
                'confidence': 0.8
            })
        elif error_type == 'undefined_variable':
            # Extract variable name from error
            var_match = re.search(r"name '([^']*)'", error_message)
            if var_match:
                var_name = var_match.group(1)
                fixes.append({
                    'fix': f"Define variable '{var_name}' before using it",
                    'priority': 'high',
                    'confidence': 0.9
                })

        return fixes

    def _generate_debug_steps(self, code: str, error_message: str) -> List[str]:
        """Generate debugging steps."""
        steps = [
            "1. Read the error message carefully to understand the issue",
            "2. Identify the line number where the error occurs",
            "3. Check syntax around the error location",
            "4. Verify all variables are defined before use",
            "5. Use print statements to debug variable values",
            "6. Test with simplified input data"
        ]

        if 'import' in error_message:
            steps.insert(2, "2a. Verify all required modules are installed")

        return steps

    # === New Claude Code Compatible Tool Methods ===

    async def _search_files(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Search for files using glob patterns (Claude Code Glob tool)."""
        pattern = task.get('pattern', '**/*.py')
        path = task.get('path')
        recursive = task.get('recursive', True)
        file_type = task.get('file_type')

        try:
            # Use the glob tool
            result = await glob_search(
                pattern=pattern,
                path=path,
                recursive=recursive,
                limit=task.get('limit', 100)
            )

            if result['success']:
                return {
                    'type': 'file_search_results',
                    'files_found': result['files'],
                    'count': result['count'],
                    'pattern': pattern,
                    'search_time_ms': result['search_time_ms'],
                    'confidence': 0.9,
                    'recommendations': [
                        f"Found {result['count']} files matching pattern '{pattern}'",
                        "Use code_search to search within these files",
                        "Consider filtering by file type for more specific results"
                    ]
                }
            else:
                return {
                    'type': 'error',
                    'error': result.get('error', 'File search failed'),
                    'confidence': 0.0,
                    'recommendations': [
                        "Check the glob pattern syntax",
                        "Verify the search path exists",
                        "Try a simpler pattern first"
                    ]
                }

        except Exception as e:
            self.logger.error(f"File search failed: {e}")
            return {
                'type': 'error',
                'error': str(e),
                'confidence': 0.0,
                'recommendations': ["Check tool installation and parameters"]
            }

    async def _search_code(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Search within code files using regex patterns (Claude Code Grep tool)."""
        pattern = task.get('pattern', '')
        path = task.get('path', '.')
        file_type = task.get('file_type', 'py')
        output_mode = task.get('output_mode', 'files_with_matches')
        case_insensitive = task.get('case_insensitive', False)

        try:
            # Use the grep tool
            result = await grep_search(
                pattern=pattern,
                path=path,
                file_type=file_type,
                output_mode=output_mode,
                case_insensitive=case_insensitive,
                show_line_numbers=True,
                head_limit=task.get('limit', 50)
            )

            if result['success']:
                return {
                    'type': 'code_search_results',
                    'matches': result['results'],
                    'total_matches': result['total_matches'],
                    'files_searched': result['files_searched'],
                    'pattern': pattern,
                    'engine': result['engine'],
                    'search_time_ms': result['search_time_ms'],
                    'confidence': 0.9,
                    'recommendations': [
                        f"Found {result['total_matches']} matches for pattern '{pattern}'",
                        "Use batch_editing to modify matching code",
                        "Review results for code quality improvements"
                    ]
                }
            else:
                return {
                    'type': 'error',
                    'error': result.get('error', 'Code search failed'),
                    'confidence': 0.0,
                    'recommendations': [
                        "Check the regex pattern syntax",
                        "Verify files exist in the search path",
                        "Try a simpler pattern first"
                    ]
                }

        except Exception as e:
            self.logger.error(f"Code search failed: {e}")
            return {
                'type': 'error',
                'error': str(e),
                'confidence': 0.0,
                'recommendations': ["Check tool installation and parameters"]
            }

    async def _batch_edit(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Perform batch edits on files (Claude Code MultiEdit tool)."""
        file_path = task.get('file_path', '')
        edits = task.get('edits', [])
        create_backup = task.get('create_backup', True)

        if not file_path or not edits:
            return {
                'type': 'error',
                'error': 'file_path and edits are required',
                'confidence': 0.0,
                'recommendations': [
                    "Provide absolute file path",
                    "Include list of edit operations",
                    "Each edit needs old_string and new_string"
                ]
            }

        try:
            # Use the multi-edit tool
            result = await multi_edit(
                file_path=file_path,
                edits=edits,
                create_backup=create_backup
            )

            if result['success']:
                return {
                    'type': 'batch_edit_results',
                    'file_path': result['file_path'],
                    'edits_successful': result['edits_successful'],
                    'edits_attempted': result['edits_attempted'],
                    'edit_results': result['results'],
                    'backup_path': result.get('backup_path'),
                    'edit_time_ms': result['edit_time_ms'],
                    'content_changed': result['content_changed'],
                    'confidence': 0.9,
                    'recommendations': [
                        f"Successfully applied {result['edits_successful']}/{result['edits_attempted']} edits",
                        "Review the changes for correctness",
                        "Run tests to verify functionality"
                    ]
                }
            else:
                return {
                    'type': 'error',
                    'error': result.get('error', 'Batch edit failed'),
                    'edit_results': result.get('results', []),
                    'confidence': 0.0,
                    'recommendations': [
                        "Check that target strings exist in the file",
                        "Ensure old_string and new_string are different",
                        "Verify file permissions allow editing"
                    ]
                }

        except Exception as e:
            self.logger.error(f"Batch edit failed: {e}")
            return {
                'type': 'error',
                'error': str(e),
                'confidence': 0.0,
                'recommendations': ["Check file path and edit parameters"]
            }