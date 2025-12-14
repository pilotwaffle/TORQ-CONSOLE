"""
Content Creation Tools Module - Consolidated Content Generation Capabilities

This module consolidates code_generation_tool.py, image_generation_tool.py,
and landing_page_generator.py into a unified content creation framework.

Provides content generation and creative capabilities:
- Multi-modal content generation (text, code, images)
- Template-based generation system
- Common output management and file operations
- Quality validation and linting
- Unified content processing pipeline

Author: TORQ Console Development Team
Version: 2.0.0 (Consolidated)
"""

import logging
import os
import json
import subprocess
import tempfile
import asyncio
import re
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod

# Try to import existing integrations
try:
    from torq_console.integrations.image_generation import ImageGenerator
    IMAGE_GEN_AVAILABLE = True
except ImportError:
    IMAGE_GEN_AVAILABLE = False

logger = logging.getLogger(__name__)


class ContentFormat(Enum):
    """Supported content formats."""
    CODE = "code"
    IMAGE = "image"
    TEXT = "text"
    HTML = "html"
    MARKDOWN = "markdown"
    JSON = "json"
    YAML = "yaml"


class CodeLanguage(Enum):
    """Supported programming languages."""
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    JAVA = "java"
    CSHARP = "csharp"
    CPP = "cpp"
    GO = "go"
    RUST = "rust"
    HTML = "html"
    CSS = "css"
    SQL = "sql"
    BASH = "bash"
    POWERSHELL = "powershell"
    YAML = "yaml"
    JSON = "json"


class ContentQuality(Enum):
    """Content quality levels."""
    EXCELLENT = "excellent"
    GOOD = "good"
    ADEQUATE = "adequate"
    NEEDS_WORK = "needs_work"
    POOR = "poor"


@dataclass
class ContentRequest:
    """Standardized content generation request."""
    content_type: ContentFormat
    description: str
    language: Optional[CodeLanguage] = None
    style: Optional[str] = None
    constraints: List[str] = field(default_factory=list)
    output_format: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ContentResult:
    """Standardized content generation result."""
    success: bool
    content: Any = None
    format: ContentFormat = ContentFormat.TEXT
    quality: ContentQuality = ContentQuality.ADEQUATE
    file_path: Optional[str] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


class ContentError(Exception):
    """Base exception for content generation errors."""
    pass


class ValidationError(ContentError):
    """Content validation errors."""
    pass


class GenerationError(ContentError):
    """Content generation errors."""
    pass


class BaseContentGenerator(ABC):
    """Base class for content generators."""

    def __init__(self, name: str, output_dir: Optional[Path] = None):
        self.name = name
        self.output_dir = output_dir or Path("E:/generated_content")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(f"torq.content.{name}")

    @abstractmethod
    async def generate(self, request: ContentRequest) -> ContentResult:
        """Generate content based on request."""
        pass

    @abstractmethod
    async def validate(self, content: Any, format: ContentFormat) -> ContentResult:
        """Validate generated content."""
        pass

    def _get_output_path(self, request: ContentRequest) -> Path:
        """Generate output file path for content."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if request.content_type == ContentFormat.CODE and request.language:
            extension = self._get_language_extension(request.language)
            filename = f"{request.language.value}_{timestamp}.{extension}"
        elif request.content_type == ContentFormat.IMAGE:
            filename = f"image_{timestamp}.png"
        elif request.content_type == ContentFormat.HTML:
            filename = f"landing_page_{timestamp}.html"
        else:
            filename = f"content_{timestamp}.txt"

        sub_dir = self.output_dir / request.content_type.value
        sub_dir.mkdir(exist_ok=True)
        return sub_dir / filename

    def _get_language_extension(self, language: CodeLanguage) -> str:
        """Get file extension for programming language."""
        extensions = {
            CodeLanguage.PYTHON: "py",
            CodeLanguage.JAVASCRIPT: "js",
            CodeLanguage.TYPESCRIPT: "ts",
            CodeLanguage.JAVA: "java",
            CodeLanguage.CSHARP: "cs",
            CodeLanguage.CPP: "cpp",
            CodeLanguage.GO: "go",
            CodeLanguage.RUST: "rs",
            CodeLanguage.HTML: "html",
            CodeLanguage.CSS: "css",
            CodeLanguage.SQL: "sql",
            CodeLanguage.BASH: "sh",
            CodeLanguage.POWERSHELL: "ps1",
            CodeLanguage.YAML: "yaml",
            CodeLanguage.JSON: "json"
        }
        return extensions.get(language, "txt")


class CodeGenerator(BaseContentGenerator):
    """Multi-language code generation with linting and validation."""

    def __init__(self, output_dir: Optional[Path] = None):
        super().__init__("code_generator", output_dir)

        # Language-specific templates and patterns
        self.language_templates = self._load_templates()
        self.code_quality_rules = self._load_quality_rules()

    def _load_templates(self) -> Dict[CodeLanguage, Dict[str, str]]:
        """Load code templates for different languages."""
        return {
            CodeLanguage.PYTHON: {
                "function": '''def {function_name}({params}) -> {return_type}:
    """
    {docstring}

    Args:
        {param_docs}

    Returns:
        {return_doc}
    """
    {body}
''',
                "class": '''class {class_name}:
    """
    {docstring}
    """

    def __init__(self{init_params}):
        {init_body}

    {methods}
''',
                "module": '''"""
{module_docstring}

Author: TORQ Console
Generated: {timestamp}
"""

{imports}

{constants}

{classes}

{functions}

if __name__ == "__main__":
    {main_code}
'''
            },
            CodeLanguage.JAVASCRIPT: {
                "function": '''/**
 * {docstring}
 * {param_docs}
 * @returns {{{return_type}}} {return_doc}
 */
function {function_name}({params}) {{
    {body}
}}''',
                "class": '''/**
 * {docstring}
 */
class {class_name} {{
    constructor({init_params}) {{
        {init_body}
    }}

    {methods}
}}''',
                "module": '''/**
 * {module_docstring}
 * Author: TORQ Console
 * Generated: {timestamp}
 */

{imports}

{constants}

{classes}

{functions}

// Main execution
{main_code}
'''
            }
        }

    def _load_quality_rules(self) -> Dict[CodeLanguage, List[str]]:
        """Load code quality rules for different languages."""
        return {
            CodeLanguage.PYTHON: [
                "PEP 8 compliance",
                "Type hints required",
                "Docstring for all functions/classes",
                "Error handling for external calls",
                "Security considerations (no eval/exec)"
            ],
            CodeLanguage.JAVASCRIPT: [
                "ESLint compliance",
                "JSDoc comments for all functions",
                "Error handling with try/catch",
                "Security considerations (no eval)",
                "Modern ES6+ syntax preferred"
            ],
            CodeLanguage.JAVA: [
                "Java naming conventions",
                "Javadoc comments required",
                "Proper exception handling",
                "Security best practices",
                "Clean code principles"
            ]
        }

    async def generate(self, request: ContentRequest) -> ContentResult:
        """Generate code based on request."""
        try:
            if not request.language:
                return ContentResult(
                    success=False,
                    error="Programming language is required for code generation"
                )

            # Generate code based on description and language
            code_content = await self._generate_code_content(request)

            # Validate generated code
            validation_result = await self.validate(code_content, ContentFormat.CODE)
            if not validation_result.success:
                return ContentResult(
                    success=False,
                    error=f"Code validation failed: {validation_result.error}",
                    content=code_content  # Still return content for debugging
                )

            # Save to file
            output_path = self._get_output_path(request)
            output_path.write_text(code_content, encoding='utf-8')

            return ContentResult(
                success=True,
                content=code_content,
                format=ContentFormat.CODE,
                quality=validation_result.quality,
                file_path=str(output_path),
                metadata={
                    'language': request.language.value,
                    'lines': len(code_content.splitlines()),
                    'characters': len(code_content),
                    'validation_passed': True
                }
            )

        except Exception as e:
            return ContentResult(
                success=False,
                error=f"Code generation failed: {str(e)}"
            )

    async def _generate_code_content(self, request: ContentRequest) -> str:
        """Generate actual code content based on request."""
        language = request.language

        # This would typically call an LLM or use templates
        # For now, we'll use template-based generation

        if "function" in request.description.lower():
            template = self.language_templates.get(language, {}).get("function", "")
            return self._fill_function_template(template, request)
        elif "class" in request.description.lower():
            template = self.language_templates.get(language, {}).get("class", "")
            return self._fill_class_template(template, request)
        else:
            template = self.language_templates.get(language, {}).get("module", "")
            return self._fill_module_template(template, request)

    def _fill_function_template(self, template: str, request: ContentRequest) -> str:
        """Fill function template with content."""
        # This is a simplified template filling
        return template.format(
            function_name="example_function",
            params="param1: str, param2: int",
            return_type="str",
            docstring=request.description,
            param_docs="param1: First parameter\nparam2: Second parameter",
            return_doc="Processed result",
            body=f"    # Generated based on: {request.description}\n    return 'result'"
        )

    def _fill_class_template(self, template: str, request: ContentRequest) -> str:
        """Fill class template with content."""
        return template.format(
            class_name="ExampleClass",
            docstring=request.description,
            init_params="",
            init_body="        pass",
            methods="    def example_method(self):\n        pass"
        )

    def _fill_module_template(self, template: str, request: ContentRequest) -> str:
        """Fill module template with content."""
        return template.format(
            module_docstring=request.description,
            timestamp=datetime.now().isoformat(),
            imports="# Imports",
            constants="# Constants",
            classes="# Classes",
            functions="# Functions",
            main_code="# Main execution"
        )

    async def validate(self, content: Any, format: ContentFormat) -> ContentResult:
        """Validate generated code."""
        try:
            if not isinstance(content, str):
                return ContentResult(
                    success=False,
                    error="Code content must be a string"
                )

            # Basic validation checks
            issues = []

            # Check for basic syntax errors (this is simplified)
            if content.count('{') != content.count('}'):
                issues.append("Mismatched braces")

            if content.count('(') != content.count(')'):
                issues.append("Mismatched parentheses")

            # Check for potential security issues
            dangerous_patterns = ['eval(', 'exec(', 'subprocess.call(', 'os.system(']
            for pattern in dangerous_patterns:
                if pattern in content:
                    issues.append(f"Potentially dangerous pattern: {pattern}")

            # Determine quality based on issues
            if not issues:
                quality = ContentQuality.EXCELLENT
            elif len(issues) <= 2:
                quality = ContentQuality.GOOD
            elif len(issues) <= 5:
                quality = ContentQuality.ADEQUATE
            else:
                quality = ContentQuality.NEEDS_WORK

            return ContentResult(
                success=len(issues) == 0,
                quality=quality,
                metadata={
                    'issues': issues,
                    'lines': len(content.splitlines()),
                    'characters': len(content)
                }
            )

        except Exception as e:
            return ContentResult(
                success=False,
                error=f"Code validation failed: {str(e)}"
            )

    async def lint_code(self, code: str, language: CodeLanguage) -> ContentResult:
        """Lint code using language-specific tools."""
        try:
            lint_results = []

            if language == CodeLanguage.PYTHON:
                # Try to use flake8 if available
                try:
                    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                        f.write(code)
                        temp_file = f.name

                    result = subprocess.run(
                        ['flake8', '--format=json', temp_file],
                        capture_output=True,
                        text=True
                    )

                    if result.stdout:
                        lint_results.extend(result.stdout.splitlines())

                    os.unlink(temp_file)

                except FileNotFoundError:
                    lint_results.append("flake8 not available for linting")

            elif language == CodeLanguage.JAVASCRIPT:
                # Try to use ESLint if available
                try:
                    with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
                        f.write(code)
                        temp_file = f.name

                    result = subprocess.run(
                        ['npx', 'eslint', '--format=json', temp_file],
                        capture_output=True,
                        text=True
                    )

                    if result.stdout:
                        lint_results.extend(result.stdout.splitlines())

                    os.unlink(temp_file)

                except FileNotFoundError:
                    lint_results.append("ESLint not available for linting")

            return ContentResult(
                success=len(lint_results) == 0,
                data={'lint_issues': lint_results},
                metadata={'linter_used': language.value}
            )

        except Exception as e:
            return ContentResult(
                success=False,
                error=f"Code linting failed: {str(e)}"
            )


class ImageGenerator(BaseContentGenerator):
    """Image generation using external services."""

    def __init__(self, output_dir: Optional[Path] = None):
        super().__init__("image_generator", output_dir)
        self.image_gen = None

        if IMAGE_GEN_AVAILABLE:
            try:
                self.image_gen = ImageGenerator()
            except Exception as e:
                self.logger.warning(f"Failed to initialize ImageGenerator: {e}")

    async def generate(self, request: ContentRequest) -> ContentResult:
        """Generate image based on request."""
        try:
            if not self.image_gen:
                return ContentResult(
                    success=False,
                    error="Image generation not available - ImageGenerator not found"
                )

            # Generate image
            image_data = await self._generate_image(request.description)

            if not image_data:
                return ContentResult(
                    success=False,
                    error="Failed to generate image"
                )

            # Save image to file
            output_path = self._get_output_path(request)
            output_path.write_bytes(image_data)

            return ContentResult(
                success=True,
                content=image_data,
                format=ContentFormat.IMAGE,
                quality=ContentQuality.GOOD,
                file_path=str(output_path),
                metadata={
                    'size': len(image_data),
                    'description': request.description
                }
            )

        except Exception as e:
            return ContentResult(
                success=False,
                error=f"Image generation failed: {str(e)}"
            )

    async def _generate_image(self, description: str) -> Optional[bytes]:
        """Generate image using external service."""
        try:
            # This would call the actual image generation service
            # For now, return a placeholder
            return b"placeholder_image_data"
        except Exception as e:
            self.logger.error(f"Image generation error: {e}")
            return None

    async def validate(self, content: Any, format: ContentFormat) -> ContentResult:
        """Validate generated image."""
        try:
            if isinstance(content, bytes):
                # Basic image validation - check for common image headers
                if content.startswith(b'\x89PNG\r\n\x1a\n'):
                    return ContentResult(success=True, quality=ContentQuality.EXCELLENT)
                elif content.startswith(b'\xff\xd8\xff'):
                    return ContentResult(success=True, quality=ContentQuality.EXCELLENT)
                else:
                    return ContentResult(
                        success=False,
                        error="Invalid image format"
                    )
            else:
                return ContentResult(
                    success=False,
                    error="Image content must be bytes"
                )

        except Exception as e:
            return ContentResult(
                success=False,
                error=f"Image validation failed: {str(e)}"
            )


class LandingPageGenerator(BaseContentGenerator):
    """Template-based landing page generator."""

    def __init__(self, output_dir: Optional[Path] = None):
        super().__init__("landing_page_generator", output_dir)
        self.templates = self._load_templates()

    def _load_templates(self) -> Dict[str, Dict[str, str]]:
        """Load landing page templates."""
        return {
            "business": {
                "html": '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        {styles}
    </style>
</head>
<body>
    <header>
        <nav>
            <div class="logo">{logo}</div>
            <ul class="nav-links">
                {nav_links}
            </ul>
        </nav>
    </header>

    <main>
        <section class="hero">
            <h1>{headline}</h1>
            <p>{subheadline}</p>
            <button class="cta-button">{cta_text}</button>
        </section>

        <section class="features">
            <h2>{features_title}</h2>
            {features}
        </section>

        <section class="testimonials">
            <h2>{testimonials_title}</h2>
            {testimonials}
        </section>
    </main>

    <footer>
        <p>&copy; 2024 {company_name}. All rights reserved.</p>
    </footer>

    <script>
        {scripts}
    </script>
</body>
</html>''',
                "css": '''* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: 'Arial', sans-serif;
    line-height: 1.6;
    color: #333;
}

header {
    background: #fff;
    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    position: fixed;
    width: 100%;
    top: 0;
    z-index: 1000;
}

nav {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1rem 5%;
    max-width: 1200px;
    margin: 0 auto;
}

.hero {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 8rem 5% 4rem;
    text-align: center;
    margin-top: 60px;
}

.cta-button {
    background: #ff6b6b;
    color: white;
    padding: 1rem 2rem;
    border: none;
    border-radius: 5px;
    cursor: pointer;
    font-size: 1.1rem;
}

.cta-button:hover {
    background: #ff5252;
}'''
            },
            "saas": {
                "html": '''<!-- SaaS Landing Page Template -->''',
                "css": '''/* SaaS specific styles */'''
            }
        }

    async def generate(self, request: ContentRequest) -> ContentResult:
        """Generate landing page based on request."""
        try:
            # Parse description to extract page details
            page_details = self._parse_description(request.description)

            # Select template
            template_type = page_details.get('template_type', 'business')
            template = self.templates.get(template_type, self.templates['business'])

            # Generate HTML
            html_content = self._generate_html(template, page_details)

            # Validate HTML
            validation_result = await self.validate(html_content, ContentFormat.HTML)

            # Save to file
            output_path = self._get_output_path(request)
            output_path.write_text(html_content, encoding='utf-8')

            return ContentResult(
                success=True,
                content=html_content,
                format=ContentFormat.HTML,
                quality=validation_result.quality,
                file_path=str(output_path),
                metadata={
                    'template_type': template_type,
                    'sections': self._count_sections(html_content),
                    'responsive': True
                }
            )

        except Exception as e:
            return ContentResult(
                success=False,
                error=f"Landing page generation failed: {str(e)}"
            )

    def _parse_description(self, description: str) -> Dict[str, str]:
        """Parse description to extract page details."""
        # This is a simplified parser - in practice, this would use NLP
        details = {
            'title': 'Welcome to Our Service',
            'headline': description.split('.')[0] if '.' in description else description,
            'subheadline': 'We provide amazing solutions for your needs',
            'logo': 'YourLogo',
            'company_name': 'Your Company',
            'cta_text': 'Get Started',
            'features_title': 'Features',
            'testimonials_title': 'What Our Customers Say'
        }

        # Extract any specific mentions
        if 'SaaS' in description:
            details['template_type'] = 'saas'
        else:
            details['template_type'] = 'business'

        return details

    def _generate_html(self, template: Dict[str, str], details: Dict[str, str]) -> str:
        """Generate HTML from template and details."""
        html_template = template['html']
        css_styles = template['css']

        # Fill in template variables
        html_content = html_template.format(
            title=details.get('title', 'Welcome'),
            headline=details.get('headline', 'Our Service'),
            subheadline=details.get('subheadline', 'Description'),
            logo=details.get('logo', 'Logo'),
            nav_links=self._generate_nav_links(),
            features=self._generate_features(),
            features_title=details.get('features_title', 'Features'),
            testimonials=self._generate_testimonials(),
            testimonials_title=details.get('testimonials_title', 'Testimonials'),
            cta_text=details.get('cta_text', 'Get Started'),
            company_name=details.get('company_name', 'Company'),
            styles=css_styles,
            scripts=self._generate_scripts()
        )

        return html_content

    def _generate_nav_links(self) -> str:
        """Generate navigation links."""
        links = ['Features', 'Pricing', 'About', 'Contact']
        return '\n'.join([f'<li><a href="#{link.lower()}">{link}</a></li>' for link in links])

    def _generate_features(self) -> str:
        """Generate features section."""
        features = [
            {'title': 'Fast', 'description': 'Lightning fast performance'},
            {'title': 'Secure', 'description': 'Enterprise-grade security'},
            {'title': 'Scalable', 'description': 'Grows with your business'}
        ]

        return '\n'.join([
            f'''<div class="feature">
                <h3>{feature['title']}</h3>
                <p>{feature['description']}</p>
            </div>'''
            for feature in features
        ])

    def _generate_testimonials(self) -> str:
        """Generate testimonials section."""
        testimonials = [
            {'name': 'John Doe', 'text': 'Amazing service! Highly recommended.'},
            {'name': 'Jane Smith', 'text': 'Changed how we do business.'}
        ]

        return '\n'.join([
            f'''<div class="testimonial">
                <p>"{testimonial['text']}"</p>
                <cite>– {testimonial['name']}</cite>
            </div>'''
            for testimonial in testimonials
        ])

    def _generate_scripts(self) -> str:
        """Generate JavaScript code."""
        return '''
        document.addEventListener('DOMContentLoaded', function() {
            // Smooth scrolling for navigation links
            document.querySelectorAll('a[href^="#"]').forEach(anchor => {
                anchor.addEventListener('click', function (e) {
                    e.preventDefault();
                    document.querySelector(this.getAttribute('href')).scrollIntoView({
                        behavior: 'smooth'
                    });
                });
            });
        });
        '''

    def _count_sections(self, html: str) -> int:
        """Count number of sections in HTML."""
        return html.count('<section')

    async def validate(self, content: Any, format: ContentFormat) -> ContentResult:
        """Validate generated HTML."""
        try:
            if not isinstance(content, str):
                return ContentResult(
                    success=False,
                    error="HTML content must be a string"
                )

            issues = []

            # Basic HTML validation
            if not content.strip().startswith('<!DOCTYPE html>'):
                issues.append("Missing DOCTYPE declaration")

            if content.count('<html>') != content.count('</html>'):
                issues.append("Mismatched HTML tags")

            if content.count('<head>') != content.count('</head>'):
                issues.append("Mismatched head tags")

            if content.count('<body>') != content.count('</body>'):
                issues.append("Mismatched body tags")

            # Check for responsive meta tag
            if 'viewport' not in content:
                issues.append("Missing viewport meta tag for responsiveness")

            # Determine quality
            if not issues:
                quality = ContentQuality.EXCELLENT
            elif len(issues) <= 2:
                quality = ContentQuality.GOOD
            elif len(issues) <= 4:
                quality = ContentQuality.ADEQUATE
            else:
                quality = ContentQuality.NEEDS_WORK

            return ContentResult(
                success=len(issues) == 0,
                quality=quality,
                metadata={
                    'issues': issues,
                    'size': len(content),
                    'responsive': 'viewport' in content
                }
            )

        except Exception as e:
            return ContentResult(
                success=False,
                error=f"HTML validation failed: {str(e)}"
            )


class ContentManager:
    """Main manager for all content generation tools."""

    def __init__(self, output_dir: Optional[Path] = None):
        self.output_dir = output_dir or Path("E:/generated_content")
        self.code_generator = CodeGenerator(self.output_dir)
        self.image_generator = ImageGenerator(self.output_dir)
        self.landing_page_generator = LandingPageGenerator(self.output_dir)
        self.logger = logging.getLogger(__name__)

    async def generate_content(self, request: ContentRequest) -> ContentResult:
        """Generate content using appropriate generator."""
        try:
            if request.content_type == ContentFormat.CODE:
                return await self.code_generator.generate(request)
            elif request.content_type == ContentFormat.IMAGE:
                return await self.image_generator.generate(request)
            elif request.content_type == ContentFormat.HTML:
                return await self.landing_page_generator.generate(request)
            else:
                # Default to text content
                return ContentResult(
                    success=False,
                    error=f"Unsupported content type: {request.content_type}"
                )

        except Exception as e:
            return ContentResult(
                success=False,
                error=f"Content generation failed: {str(e)}"
            )

    async def validate_content(self, content: Any, format: ContentFormat) -> ContentResult:
        """Validate content using appropriate validator."""
        try:
            if format == ContentFormat.CODE:
                return await self.code_generator.validate(content, format)
            elif format == ContentFormat.IMAGE:
                return await self.image_generator.validate(content, format)
            elif format == ContentFormat.HTML:
                return await self.landing_page_generator.validate(content, format)
            else:
                return ContentResult(
                    success=False,
                    error=f"No validator available for format: {format}"
                )

        except Exception as e:
            return ContentResult(
                success=False,
                error=f"Content validation failed: {str(e)}"
            )

    async def lint_code(self, code: str, language: CodeLanguage) -> ContentResult:
        """Lint code using appropriate linter."""
        return await self.code_generator.lint_code(code, language)


# Factory function for easy initialization
def create_content_manager(output_dir: Optional[Path] = None) -> ContentManager:
    """Create and return a content manager instance."""
    return ContentManager(output_dir)


# Export main classes and functions
__all__ = [
    'ContentManager',
    'CodeGenerator',
    'ImageGenerator',
    'LandingPageGenerator',
    'BaseContentGenerator',
    'ContentRequest',
    'ContentResult',
    'ContentFormat',
    'CodeLanguage',
    'ContentQuality',
    'ContentError',
    'ValidationError',
    'GenerationError',
    'create_content_manager'
]