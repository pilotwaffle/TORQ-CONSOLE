"""
Documentation Agent for Advanced Swarm Intelligence System.

This agent specializes in creating, maintaining, and improving documentation,
including API docs, user guides, code comments, and technical specifications.
"""

import asyncio
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime
import re
import json


class DocumentationAgent:
    """Specialized agent for documentation generation and maintenance."""

    def __init__(self, llm_provider=None):
        """
        Initialize DocumentationAgent.

        Args:
            llm_provider: LLM provider for documentation generation
        """
        self.llm_provider = llm_provider
        self.logger = logging.getLogger(__name__)

        # Agent specialization
        self.agent_id = "documentation_agent"
        self.capabilities = [
            "api_documentation",
            "user_guides",
            "code_comments",
            "technical_specs",
            "readme_generation",
            "changelog_creation",
            "documentation_review"
        ]

        # Documentation templates
        self.templates = {
            'function_docstring': '''"""
{summary}

Args:
{args}

Returns:
{returns}

Raises:
{raises}
"""''',
            'class_docstring': '''"""
{summary}

{description}

Attributes:
{attributes}

Methods:
{methods}
"""''',
            'api_endpoint': '''## {method} {endpoint}

{description}

### Parameters
{parameters}

### Response
{response}

### Example
```
{example}
```''',
            'readme_template': '''# {project_name}

{description}

## Installation
{installation}

## Usage
{usage}

## API Reference
{api_reference}

## Contributing
{contributing}

## License
{license}
'''
        }

        # Documentation cache
        self.doc_cache = {}
        self.max_cache_size = 100

    async def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a documentation task.

        Args:
            task: Task dictionary with documentation requirements

        Returns:
            Documentation results with next agent recommendations
        """
        start_time = datetime.now()
        task_type = task.get('type', 'documentation')

        self.logger.info(f"Processing {task_type} documentation task")

        try:
            if task_type == 'api_documentation':
                result = await self._generate_api_docs(task)
            elif task_type == 'user_guide':
                result = await self._generate_user_guide(task)
            elif task_type == 'code_comments':
                result = await self._generate_code_comments(task)
            elif task_type == 'readme':
                result = await self._generate_readme(task)
            elif task_type == 'changelog':
                result = await self._generate_changelog(task)
            elif task_type == 'documentation_review':
                result = await self._review_documentation(task)
            else:
                result = await self._general_documentation_task(task)

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
                    'docs_generated': len(result.get('documents', [])),
                    'sections': len(result.get('sections', [])),
                    'word_count': result.get('word_count', 0)
                }
            }

        except Exception as e:
            self.logger.error(f"Documentation generation failed: {e}")
            return {
                'agent_id': self.agent_id,
                'task_type': task_type,
                'error': str(e),
                'next_agent': 'response_agent',
                'processing_time': (datetime.now() - start_time).total_seconds()
            }

    async def _generate_api_docs(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Generate API documentation."""
        api_spec = task.get('api_spec', {})
        code = task.get('code', '')
        format_type = task.get('format', 'markdown')

        docs = {
            'format': format_type,
            'sections': [],
            'endpoints': [],
            'models': [],
            'examples': [],
            'confidence': 0.9
        }

        if code:
            # Extract API endpoints from code
            endpoints = self._extract_api_endpoints(code)
            docs['endpoints'] = [self._document_endpoint(ep) for ep in endpoints]

            # Extract data models
            models = self._extract_data_models(code)
            docs['models'] = [self._document_model(model) for model in models]

        # Generate examples
        docs['examples'] = self._generate_api_examples(docs['endpoints'])

        # Create sections
        docs['sections'] = self._create_api_sections(docs)
        docs['word_count'] = sum(len(section.get('content', '').split()) for section in docs['sections'])

        return docs

    async def _generate_user_guide(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Generate user guide documentation."""
        product_info = task.get('product_info', {})
        features = task.get('features', [])
        audience = task.get('audience', 'general')

        guide = {
            'audience': audience,
            'sections': [],
            'tutorials': [],
            'faqs': [],
            'troubleshooting': [],
            'confidence': 0.85
        }

        # Generate main sections
        guide['sections'] = [
            self._create_getting_started_section(product_info),
            self._create_features_section(features),
            self._create_configuration_section(product_info),
            self._create_best_practices_section()
        ]

        # Generate tutorials
        guide['tutorials'] = self._create_tutorials(features)

        # Generate FAQs
        guide['faqs'] = self._create_faqs(product_info, features)

        # Generate troubleshooting guide
        guide['troubleshooting'] = self._create_troubleshooting_guide()

        guide['word_count'] = sum(len(section.get('content', '').split()) for section in guide['sections'])

        return guide

    async def _generate_code_comments(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Generate or improve code comments."""
        code = task.get('code', '')
        language = task.get('language', 'python')
        comment_style = task.get('style', 'comprehensive')

        comments = {
            'language': language,
            'style': comment_style,
            'generated_comments': [],
            'improved_comments': [],
            'docstrings': [],
            'confidence': 0.8
        }

        if language == 'python':
            comments = await self._generate_python_comments(code, comment_style)
        elif language == 'javascript':
            comments = await self._generate_javascript_comments(code, comment_style)
        else:
            comments = await self._generate_generic_comments(code, comment_style)

        return comments

    async def _generate_readme(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Generate README documentation."""
        project_info = task.get('project_info', {})
        code_analysis = task.get('code_analysis', {})

        readme = {
            'project_name': project_info.get('name', 'Project'),
            'description': project_info.get('description', ''),
            'sections': {},
            'badges': [],
            'confidence': 0.85
        }

        # Generate each section
        readme['sections'] = {
            'installation': self._generate_installation_section(project_info),
            'usage': self._generate_usage_section(code_analysis),
            'api_reference': self._generate_api_reference_section(code_analysis),
            'contributing': self._generate_contributing_section(),
            'license': self._generate_license_section(project_info)
        }

        # Generate badges
        readme['badges'] = self._generate_badges(project_info)

        # Create full README content
        readme['full_content'] = self.templates['readme_template'].format(
            project_name=readme['project_name'],
            description=readme['description'],
            installation=readme['sections']['installation'],
            usage=readme['sections']['usage'],
            api_reference=readme['sections']['api_reference'],
            contributing=readme['sections']['contributing'],
            license=readme['sections']['license']
        )

        readme['word_count'] = len(readme['full_content'].split())

        return readme

    async def _generate_changelog(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Generate changelog documentation."""
        version_history = task.get('version_history', [])
        changes = task.get('changes', [])
        format_type = task.get('format', 'keepachangelog')

        changelog = {
            'format': format_type,
            'versions': [],
            'categories': ['Added', 'Changed', 'Deprecated', 'Removed', 'Fixed', 'Security'],
            'confidence': 0.8
        }

        if version_history:
            changelog['versions'] = self._format_version_history(version_history, format_type)
        else:
            # Generate from recent changes
            changelog['versions'] = [self._create_version_entry(changes)]

        changelog['full_content'] = self._format_changelog(changelog)
        changelog['word_count'] = len(changelog['full_content'].split())

        return changelog

    async def _review_documentation(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Review existing documentation for quality and completeness."""
        documentation = task.get('documentation', '')
        doc_type = task.get('doc_type', 'general')

        review = {
            'doc_type': doc_type,
            'quality_score': 0,
            'completeness_score': 0,
            'readability_score': 0,
            'issues': [],
            'suggestions': [],
            'missing_sections': [],
            'confidence': 0.85
        }

        # Quality analysis
        review['quality_score'] = self._assess_quality(documentation)
        review['completeness_score'] = self._assess_completeness(documentation, doc_type)
        review['readability_score'] = self._assess_readability(documentation)

        # Identify issues
        review['issues'] = self._identify_doc_issues(documentation)

        # Generate suggestions
        review['suggestions'] = self._generate_doc_suggestions(review)

        # Find missing sections
        review['missing_sections'] = self._find_missing_sections(documentation, doc_type)

        return review

    def _extract_api_endpoints(self, code: str) -> List[Dict[str, Any]]:
        """Extract API endpoints from code."""
        endpoints = []

        # Common patterns for different frameworks
        patterns = {
            'flask': r'@app\.route\([\'"]([^\'"]+)[\'"](?:,\s*methods=\[(.*?)\])?\)\s*def\s+(\w+)',
            'fastapi': r'@app\.(get|post|put|delete|patch)\([\'"]([^\'"]+)[\'"].*?\)\s*(?:async\s+)?def\s+(\w+)',
            'django': r'path\([\'"]([^\'"]+)[\'"].*?(\w+)\.as_view',
            'express': r'app\.(get|post|put|delete|patch)\([\'"]([^\'"]+)[\'"]'
        }

        for framework, pattern in patterns.items():
            matches = re.findall(pattern, code, re.MULTILINE)
            for match in matches:
                if framework == 'flask':
                    endpoint = {
                        'path': match[0],
                        'methods': match[1].split(',') if match[1] else ['GET'],
                        'function': match[2],
                        'framework': framework
                    }
                elif framework in ['fastapi', 'express']:
                    endpoint = {
                        'method': match[0].upper(),
                        'path': match[1],
                        'function': match[2] if len(match) > 2 else 'anonymous',
                        'framework': framework
                    }
                endpoints.append(endpoint)

        return endpoints

    def _extract_data_models(self, code: str) -> List[Dict[str, Any]]:
        """Extract data models from code."""
        models = []

        # Python class patterns
        class_pattern = r'class\s+(\w+).*?:\s*((?:.*?\n)*?)(?=\n\s*class|\n\s*def|\Z)'
        class_matches = re.findall(class_pattern, code, re.MULTILINE | re.DOTALL)

        for class_name, class_body in class_matches:
            # Extract attributes
            attr_pattern = r'self\.(\w+)\s*=|(\w+):\s*(\w+)'
            attributes = re.findall(attr_pattern, class_body)

            model = {
                'name': class_name,
                'attributes': [],
                'methods': []
            }

            for attr in attributes:
                if attr[0]:  # self.attribute pattern
                    model['attributes'].append({'name': attr[0], 'type': 'unknown'})
                elif attr[1]:  # typed attribute pattern
                    model['attributes'].append({'name': attr[1], 'type': attr[2]})

            # Extract methods
            method_pattern = r'def\s+(\w+)\s*\('
            methods = re.findall(method_pattern, class_body)
            model['methods'] = [{'name': method} for method in methods if not method.startswith('_')]

            models.append(model)

        return models

    def _document_endpoint(self, endpoint: Dict[str, Any]) -> Dict[str, Any]:
        """Create documentation for an API endpoint."""
        return {
            'method': endpoint.get('method', 'GET'),
            'path': endpoint.get('path', '/'),
            'function': endpoint.get('function', ''),
            'description': f"Endpoint for {endpoint.get('function', 'operation')}",
            'parameters': [],
            'responses': {
                '200': {'description': 'Success'},
                '400': {'description': 'Bad Request'},
                '500': {'description': 'Internal Server Error'}
            }
        }

    def _document_model(self, model: Dict[str, Any]) -> Dict[str, Any]:
        """Create documentation for a data model."""
        return {
            'name': model.get('name', ''),
            'description': f"Data model for {model.get('name', '')}",
            'attributes': model.get('attributes', []),
            'methods': model.get('methods', []),
            'example': self._generate_model_example(model)
        }

    def _generate_api_examples(self, endpoints: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate examples for API endpoints."""
        examples = []

        for endpoint in endpoints[:3]:  # Limit to first 3 endpoints
            example = {
                'endpoint': endpoint,
                'request': f"curl -X {endpoint.get('method', 'GET')} {endpoint.get('path', '/')}",
                'response': '{"status": "success", "data": {}}'
            }
            examples.append(example)

        return examples

    def _create_api_sections(self, docs: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create sections for API documentation."""
        sections = [
            {
                'title': 'Overview',
                'content': 'This API provides access to the application functionality.',
                'order': 1
            },
            {
                'title': 'Authentication',
                'content': 'API authentication methods and requirements.',
                'order': 2
            },
            {
                'title': 'Endpoints',
                'content': self._format_endpoints_section(docs.get('endpoints', [])),
                'order': 3
            },
            {
                'title': 'Data Models',
                'content': self._format_models_section(docs.get('models', [])),
                'order': 4
            },
            {
                'title': 'Examples',
                'content': self._format_examples_section(docs.get('examples', [])),
                'order': 5
            }
        ]

        return sections

    async def _generate_python_comments(self, code: str, style: str) -> Dict[str, Any]:
        """Generate Python-specific comments."""
        comments = {
            'language': 'python',
            'style': style,
            'generated_comments': [],
            'docstrings': [],
            'confidence': 0.8
        }

        # Extract functions and generate docstrings
        func_pattern = r'def\s+(\w+)\s*\((.*?)\)(?:\s*->\s*([^:]+))?:'
        functions = re.findall(func_pattern, code, re.MULTILINE)

        for func_name, args, return_type in functions:
            docstring = self._generate_function_docstring(func_name, args, return_type)
            comments['docstrings'].append({
                'function': func_name,
                'docstring': docstring
            })

        return comments

    async def _generate_javascript_comments(self, code: str, style: str) -> Dict[str, Any]:
        """Generate JavaScript-specific comments."""
        comments = {
            'language': 'javascript',
            'style': style,
            'generated_comments': [],
            'jsdoc_comments': [],
            'confidence': 0.8
        }

        # Extract functions and generate JSDoc comments
        func_pattern = r'function\s+(\w+)\s*\((.*?)\)|(\w+)\s*[:=]\s*(?:function\s*)?\((.*?)\)\s*(?:=>|{)'
        functions = re.findall(func_pattern, code, re.MULTILINE)

        for match in functions:
            func_name = match[0] or match[2]
            args = match[1] or match[3]

            jsdoc = self._generate_jsdoc_comment(func_name, args)
            comments['jsdoc_comments'].append({
                'function': func_name,
                'comment': jsdoc
            })

        return comments

    def _generate_function_docstring(self, func_name: str, args: str, return_type: str) -> str:
        """Generate a Python docstring for a function."""
        # Parse arguments
        arg_docs = []
        if args.strip():
            arg_list = [arg.strip().split(':')[0].strip() for arg in args.split(',') if arg.strip()]
            for arg in arg_list:
                if arg != 'self':
                    arg_docs.append(f"    {arg}: Description of {arg}")

        return self.templates['function_docstring'].format(
            summary=f"Function {func_name} description.",
            args='\n'.join(arg_docs) if arg_docs else '    None',
            returns=f"    {return_type or 'Description of return value'}",
            raises="    None"
        )

    def _generate_jsdoc_comment(self, func_name: str, args: str) -> str:
        """Generate a JSDoc comment for a JavaScript function."""
        comment_lines = [
            "/**",
            f" * Description of {func_name} function.",
            " *"
        ]

        # Add parameters
        if args.strip():
            arg_list = [arg.strip() for arg in args.split(',') if arg.strip()]
            for arg in arg_list:
                comment_lines.append(f" * @param {{*}} {arg} - Description of {arg}")

        comment_lines.extend([
            " * @returns {{*}} Description of return value",
            " */"
        ])

        return '\n'.join(comment_lines)

    def _assess_quality(self, documentation: str) -> int:
        """Assess documentation quality (0-100)."""
        score = 50  # Base score

        # Check for common quality indicators
        if re.search(r'# .+|## .+', documentation):  # Has headers
            score += 15

        if len(documentation.split()) > 100:  # Adequate length
            score += 10

        if re.search(r'```.*?```', documentation, re.DOTALL):  # Has code examples
            score += 15

        if re.search(r'\[.*?\]\(.*?\)', documentation):  # Has links
            score += 10

        return min(100, score)

    def _assess_completeness(self, documentation: str, doc_type: str) -> int:
        """Assess documentation completeness (0-100)."""
        score = 30  # Base score

        required_sections = {
            'api': ['overview', 'endpoints', 'authentication', 'examples'],
            'user_guide': ['getting started', 'features', 'configuration'],
            'readme': ['installation', 'usage', 'contributing', 'license']
        }

        sections = required_sections.get(doc_type, [])
        found_sections = sum(1 for section in sections if section.lower() in documentation.lower())

        if sections:
            score += int((found_sections / len(sections)) * 70)

        return min(100, score)

    def _assess_readability(self, documentation: str) -> int:
        """Assess documentation readability (0-100)."""
        score = 40  # Base score

        # Simple readability checks
        sentences = documentation.split('.')
        avg_sentence_length = sum(len(s.split()) for s in sentences) / max(len(sentences), 1)

        if 10 <= avg_sentence_length <= 25:  # Good sentence length
            score += 20

        # Check for good structure
        if documentation.count('\n\n') > 3:  # Has paragraph breaks
            score += 20

        # Check for formatting
        if '**' in documentation or '*' in documentation:  # Has emphasis
            score += 20

        return min(100, score)

    def _determine_next_agent(self, result: Dict[str, Any], task: Dict[str, Any]) -> Optional[str]:
        """Determine the next agent based on documentation results."""
        task_type = task.get('type')

        # If we generated code documentation, might need performance agent
        if task_type == 'code_comments' and result.get('confidence', 0) > 0.8:
            return 'performance_agent'

        # If API documentation, might need testing agent
        if task_type == 'api_documentation':
            return 'testing_agent'

        # Otherwise go to response agent
        return 'response_agent'

    # Additional helper methods continue here...
    def _create_getting_started_section(self, product_info: Dict[str, Any]) -> Dict[str, str]:
        """Create getting started section."""
        return {
            'title': 'Getting Started',
            'content': f"""
## Getting Started with {product_info.get('name', 'the application')}

Follow these steps to get up and running quickly:

1. **Installation**: Install the required dependencies
2. **Configuration**: Set up your configuration files
3. **First Run**: Execute your first command
4. **Verification**: Confirm everything is working correctly

For detailed installation instructions, see the Installation section below.
""",
            'order': 1
        }

    def _create_features_section(self, features: List[str]) -> Dict[str, str]:
        """Create features section."""
        feature_list = '\n'.join(f"- {feature}" for feature in features) if features else "- Core functionality"

        return {
            'title': 'Features',
            'content': f"""
## Features

This application provides the following features:

{feature_list}
""",
            'order': 2
        }

    def _format_endpoints_section(self, endpoints: List[Dict[str, Any]]) -> str:
        """Format endpoints section."""
        if not endpoints:
            return "No endpoints documented yet."

        content = []
        for endpoint in endpoints:
            content.append(self.templates['api_endpoint'].format(
                method=endpoint.get('method', 'GET'),
                endpoint=endpoint.get('path', '/'),
                description=endpoint.get('description', ''),
                parameters="None",
                response="Success response",
                example=f"curl -X {endpoint.get('method', 'GET')} {endpoint.get('path', '/')}"
            ))

        return '\n\n'.join(content)

    async def get_status(self) -> Dict[str, Any]:
        """Get agent status."""
        return {
            'agent_id': self.agent_id,
            'status': 'ready',
            'capabilities': self.capabilities,
            'cache_size': len(self.doc_cache),
            'templates_available': len(self.templates)
        }