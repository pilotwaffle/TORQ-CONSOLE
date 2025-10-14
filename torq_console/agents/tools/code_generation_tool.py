"""
Code Generation Tool for Prince Flowers
Multi-language code generation with linting and validation
"""
import logging
import os
import subprocess
import tempfile
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path
import json
import re


class CodeGenerationTool:
    """
    Multi-language code generation with linting, validation, and best practices.
    Supports Python, JavaScript, TypeScript, Java, C++, Go, Rust, and more.
    """

    def __init__(self, output_dir: Optional[str] = None):
        """
        Initialize Code Generation Tool.

        Args:
            output_dir: Directory to save generated code (default: E:/generated_code)
        """
        self.logger = logging.getLogger(__name__)
        self.output_dir = Path(output_dir or "E:/generated_code")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Language configurations
        self.language_configs = {
            'python': {
                'extension': '.py',
                'linter': 'pylint',
                'formatter': 'black',
                'comment': '#',
                'docstring': '"""',
                'shebang': '#!/usr/bin/env python3'
            },
            'javascript': {
                'extension': '.js',
                'linter': 'eslint',
                'formatter': 'prettier',
                'comment': '//',
                'docstring': '/**',
                'shebang': None
            },
            'typescript': {
                'extension': '.ts',
                'linter': 'eslint',
                'formatter': 'prettier',
                'comment': '//',
                'docstring': '/**',
                'shebang': None
            },
            'java': {
                'extension': '.java',
                'linter': 'checkstyle',
                'formatter': 'google-java-format',
                'comment': '//',
                'docstring': '/**',
                'shebang': None
            },
            'cpp': {
                'extension': '.cpp',
                'linter': 'cpplint',
                'formatter': 'clang-format',
                'comment': '//',
                'docstring': '/**',
                'shebang': None
            },
            'go': {
                'extension': '.go',
                'linter': 'golint',
                'formatter': 'gofmt',
                'comment': '//',
                'docstring': '/**',
                'shebang': None
            },
            'rust': {
                'extension': '.rs',
                'linter': 'clippy',
                'formatter': 'rustfmt',
                'comment': '//',
                'docstring': '///',
                'shebang': None
            },
            'html': {
                'extension': '.html',
                'linter': 'htmlhint',
                'formatter': 'prettier',
                'comment': '<!--',
                'docstring': '<!--',
                'shebang': None
            },
            'css': {
                'extension': '.css',
                'linter': 'stylelint',
                'formatter': 'prettier',
                'comment': '/*',
                'docstring': '/*',
                'shebang': None
            },
            'sql': {
                'extension': '.sql',
                'linter': 'sqlfluff',
                'formatter': 'sqlfluff',
                'comment': '--',
                'docstring': '--',
                'shebang': None
            },
            'bash': {
                'extension': '.sh',
                'linter': 'shellcheck',
                'formatter': 'shfmt',
                'comment': '#',
                'docstring': '#',
                'shebang': '#!/bin/bash'
            }
        }

    def is_available(self) -> bool:
        """Check if code generation is available."""
        try:
            # Check if output directory is writable
            test_file = self.output_dir / '.write_test'
            test_file.write_text('test')
            test_file.unlink()
            return True
        except Exception as e:
            self.logger.error(f"Code generation not available: {e}")
            return False

    def _detect_language(self, description: str, code: Optional[str] = None) -> str:
        """
        Auto-detect programming language from description or code.

        Args:
            description: Task description
            code: Optional code sample

        Returns:
            Detected language (default: python)
        """
        description_lower = description.lower()

        # Check description for language keywords
        language_keywords = {
            'python': ['python', 'py', 'django', 'flask', 'pandas'],
            'javascript': ['javascript', 'js', 'node', 'react', 'vue', 'express'],
            'typescript': ['typescript', 'ts', 'angular'],
            'java': ['java', 'spring', 'hibernate'],
            'cpp': ['c++', 'cpp'],
            'go': ['golang', 'go'],
            'rust': ['rust'],
            'html': ['html', 'webpage'],
            'css': ['css', 'stylesheet'],
            'sql': ['sql', 'database', 'query'],
            'bash': ['bash', 'shell', 'script']
        }

        for lang, keywords in language_keywords.items():
            if any(keyword in description_lower for keyword in keywords):
                return lang

        # Check code syntax if provided
        if code:
            if 'def ' in code or 'import ' in code or 'print(' in code:
                return 'python'
            elif 'function ' in code or 'const ' in code or 'let ' in code:
                return 'javascript'
            elif 'interface ' in code and ': ' in code:
                return 'typescript'
            elif 'public class ' in code or 'public static void' in code:
                return 'java'

        # Default to Python
        return 'python'

    def _generate_template(self, language: str, description: str, function_name: str = None) -> str:
        """
        Generate code template based on language and description.

        Args:
            language: Programming language
            description: What the code should do
            function_name: Optional function name

        Returns:
            Generated code template
        """
        config = self.language_configs.get(language, self.language_configs['python'])

        if language == 'python':
            return self._generate_python_template(description, function_name)
        elif language in ['javascript', 'typescript']:
            return self._generate_js_template(description, function_name, language == 'typescript')
        elif language == 'java':
            return self._generate_java_template(description, function_name)
        elif language == 'cpp':
            return self._generate_cpp_template(description, function_name)
        elif language == 'go':
            return self._generate_go_template(description, function_name)
        elif language == 'rust':
            return self._generate_rust_template(description, function_name)
        elif language == 'html':
            return self._generate_html_template(description)
        elif language == 'css':
            return self._generate_css_template(description)
        elif language == 'sql':
            return self._generate_sql_template(description)
        elif language == 'bash':
            return self._generate_bash_template(description)
        else:
            return self._generate_generic_template(language, description)

    def _generate_python_template(self, description: str, function_name: str = None) -> str:
        """Generate Python code template."""
        func_name = function_name or self._extract_function_name(description) or 'process_data'

        return f'''#!/usr/bin/env python3
"""
{description}

This module was generated by Prince Flowers AI.
"""

from typing import Any, Optional, List, Dict


def {func_name}(data: Any) -> Any:
    """
    {description}

    Args:
        data: Input data to process

    Returns:
        Processed result

    Raises:
        ValueError: If input data is invalid
    """
    try:
        # TODO: Implement logic here
        result = None

        return result

    except Exception as e:
        raise ValueError(f"Processing failed: {{str(e)}}") from e


def main():
    """Main entry point for testing."""
    # Example usage
    test_data = None  # Replace with actual test data
    result = {func_name}(test_data)
    print(f"Result: {{result}}")


if __name__ == "__main__":
    main()
'''

    def _generate_js_template(self, description: str, function_name: str = None, typescript: bool = False) -> str:
        """Generate JavaScript/TypeScript code template."""
        func_name = function_name or self._extract_function_name(description) or 'processData'

        type_annotation = ': any' if typescript else ''
        return_type = ': any' if typescript else ''

        return f'''/**
 * {description}
 *
 * Generated by Prince Flowers AI
 */

/**
 * {description}
 * @param {{any}} data - Input data to process
 * @returns {{any}} Processed result
 */
function {func_name}(data{type_annotation}){return_type} {{
    try {{
        // TODO: Implement logic here
        const result = null;

        return result;
    }} catch (error) {{
        throw new Error(`Processing failed: ${{error.message}}`);
    }}
}}

// Example usage
function main() {{
    const testData = null; // Replace with actual test data
    const result = {func_name}(testData);
    console.log('Result:', result);
}}

{'export { ' + func_name + ' };' if typescript else ''}
'''

    def _generate_java_template(self, description: str, function_name: str = None) -> str:
        """Generate Java code template."""
        class_name = function_name or self._extract_class_name(description) or 'DataProcessor'

        return f'''/**
 * {description}
 *
 * Generated by Prince Flowers AI
 */

public class {class_name} {{

    /**
     * {description}
     * @param data Input data to process
     * @return Processed result
     * @throws IllegalArgumentException if input is invalid
     */
    public Object processData(Object data) {{
        try {{
            // TODO: Implement logic here
            Object result = null;

            return result;
        }} catch (Exception e) {{
            throw new IllegalArgumentException("Processing failed: " + e.getMessage(), e);
        }}
    }}

    /**
     * Main entry point for testing
     */
    public static void main(String[] args) {{
        {class_name} processor = new {class_name}();
        Object testData = null; // Replace with actual test data
        Object result = processor.processData(testData);
        System.out.println("Result: " + result);
    }}
}}
'''

    def _generate_cpp_template(self, description: str, function_name: str = None) -> str:
        """Generate C++ code template."""
        func_name = function_name or self._extract_function_name(description) or 'processData'

        return f'''/**
 * {description}
 *
 * Generated by Prince Flowers AI
 */

#include <iostream>
#include <string>
#include <stdexcept>

/**
 * {description}
 * @param data Input data to process
 * @return Processed result
 * @throws std::runtime_error if processing fails
 */
template<typename T>
T {func_name}(T data) {{
    try {{
        // TODO: Implement logic here
        T result;

        return result;
    }} catch (const std::exception& e) {{
        throw std::runtime_error("Processing failed: " + std::string(e.what()));
    }}
}}

int main() {{
    try {{
        // Example usage
        auto testData = 0; // Replace with actual test data
        auto result = {func_name}(testData);
        std::cout << "Result: " << result << std::endl;
        return 0;
    }} catch (const std::exception& e) {{
        std::cerr << "Error: " << e.what() << std::endl;
        return 1;
    }}
}}
'''

    def _generate_go_template(self, description: str, function_name: str = None) -> str:
        """Generate Go code template."""
        func_name = function_name or self._extract_function_name(description) or 'ProcessData'
        func_name = func_name[0].upper() + func_name[1:]  # Capitalize for Go export

        return f'''// {description}
//
// Generated by Prince Flowers AI

package main

import (
    "fmt"
    "errors"
)

// {func_name} {description}
func {func_name}(data interface{{}}) (interface{{}}, error) {{
    // TODO: Implement logic here
    var result interface{{}}

    if data == nil {{
        return nil, errors.New("invalid input data")
    }}

    return result, nil
}}

func main() {{
    // Example usage
    testData := nil // Replace with actual test data
    result, err := {func_name}(testData)
    if err != nil {{
        fmt.Printf("Error: %v\\n", err)
        return
    }}
    fmt.Printf("Result: %v\\n", result)
}}
'''

    def _generate_rust_template(self, description: str, function_name: str = None) -> str:
        """Generate Rust code template."""
        func_name = function_name or self._extract_function_name(description) or 'process_data'

        return f'''/// {description}
///
/// Generated by Prince Flowers AI

use std::error::Error;

/// {description}
///
/// # Arguments
/// * `data` - Input data to process
///
/// # Returns
/// Processed result
///
/// # Errors
/// Returns error if processing fails
fn {func_name}(data: &str) -> Result<String, Box<dyn Error>> {{
    // TODO: Implement logic here
    let result = String::new();

    Ok(result)
}}

fn main() -> Result<(), Box<dyn Error>> {{
    // Example usage
    let test_data = ""; // Replace with actual test data
    let result = {func_name}(test_data)?;
    println!("Result: {{}}", result);
    Ok(())
}}
'''

    def _generate_html_template(self, description: str) -> str:
        """Generate HTML template."""
        return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{description}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            line-height: 1.6;
        }}
    </style>
</head>
<body>
    <h1>{description}</h1>
    <p>Generated by Prince Flowers AI</p>

    <!-- TODO: Add your content here -->

</body>
</html>
'''

    def _generate_css_template(self, description: str) -> str:
        """Generate CSS template."""
        return f'''/**
 * {description}
 *
 * Generated by Prince Flowers AI
 */

/* TODO: Add your styles here */

/* Example styles */
.container {{
    max-width: 1200px;
    margin: 0 auto;
    padding: 20px;
}}

.button {{
    display: inline-block;
    padding: 10px 20px;
    background-color: #007bff;
    color: white;
    text-decoration: none;
    border-radius: 4px;
    transition: background-color 0.3s;
}}

.button:hover {{
    background-color: #0056b3;
}}
'''

    def _generate_sql_template(self, description: str) -> str:
        """Generate SQL template."""
        return f'''-- {description}
-- Generated by Prince Flowers AI

-- TODO: Add your SQL queries here

-- Example query structure
/*
SELECT
    column1,
    column2
FROM
    table_name
WHERE
    condition = value
ORDER BY
    column1;
*/
'''

    def _generate_bash_template(self, description: str) -> str:
        """Generate Bash script template."""
        return f'''#!/bin/bash
# {description}
# Generated by Prince Flowers AI

set -euo pipefail  # Exit on error, undefined variables, and pipe failures

# TODO: Implement script logic here

main() {{
    echo "Starting..."

    # Add your logic here

    echo "Done!"
}}

# Run main function
main "$@"
'''

    def _generate_generic_template(self, language: str, description: str) -> str:
        """Generate generic template for unknown languages."""
        config = self.language_configs.get(language, {'comment': '#'})
        comment = config['comment']

        return f'''{comment} {description}
{comment} Generated by Prince Flowers AI

{comment} TODO: Implement your code here
'''

    def _extract_function_name(self, description: str) -> Optional[str]:
        """Extract function name from description."""
        # Look for common patterns: "create a function to...", "write function that..."
        patterns = [
            r'(?:create|write|make|build)\s+(?:a\s+)?function\s+(?:named|called)\s+(\w+)',
            r'function\s+(\w+)',
            r'(\w+)\s+function'
        ]

        for pattern in patterns:
            match = re.search(pattern, description.lower())
            if match:
                return match.group(1)

        return None

    def _extract_class_name(self, description: str) -> Optional[str]:
        """Extract class name from description."""
        patterns = [
            r'(?:create|write|make|build)\s+(?:a\s+)?class\s+(?:named|called)\s+(\w+)',
            r'class\s+(\w+)',
            r'(\w+)\s+class'
        ]

        for pattern in patterns:
            match = re.search(pattern, description.lower())
            if match:
                name = match.group(1)
                # Capitalize first letter for class names
                return name[0].upper() + name[1:] if name else None

        return None

    def _run_linter(self, filepath: str, language: str) -> Dict[str, Any]:
        """
        Run linter on generated code (if linter available).

        Args:
            filepath: Path to code file
            language: Programming language

        Returns:
            Linter results
        """
        config = self.language_configs.get(language)
        if not config:
            return {'available': False}

        linter = config.get('linter')
        if not linter:
            return {'available': False}

        # Check if linter is installed
        try:
            # Try to run linter (this is optional, won't fail if not installed)
            if linter == 'pylint':
                result = subprocess.run(
                    ['pylint', '--score=y', '--reports=n', filepath],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                return {
                    'available': True,
                    'linter': linter,
                    'output': result.stdout,
                    'errors': result.stderr,
                    'returncode': result.returncode
                }
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

        return {'available': False, 'linter': linter, 'message': 'Linter not installed'}

    async def generate(
        self,
        description: str,
        language: Optional[str] = None,
        function_name: Optional[str] = None,
        filename: Optional[str] = None,
        run_linter: bool = False
    ) -> Dict[str, Any]:
        """
        Generate code from description.

        Args:
            description: What the code should do
            language: Programming language (auto-detected if not provided)
            function_name: Optional function/class name
            filename: Optional output filename
            run_linter: Whether to run linter (if available)

        Returns:
            Generation result with file path and metadata
        """
        try:
            # Detect language if not provided
            if not language:
                language = self._detect_language(description)

            language = language.lower()
            self.logger.info(f"[CODE_GEN] Generating {language} code")
            self.logger.info(f"[CODE_GEN] Description: {description[:100]}...")

            # Get language config
            config = self.language_configs.get(language, self.language_configs['python'])

            # Generate code
            code = self._generate_template(language, description, function_name)

            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            if not filename:
                safe_desc = "".join(c if c.isalnum() else '_' for c in description.split('.')[0])
                safe_desc = safe_desc[:30].lower()
                filename = f"{safe_desc}_{timestamp}{config['extension']}"
            elif not filename.endswith(config['extension']):
                filename += config['extension']

            filepath = self.output_dir / filename

            # Write file
            filepath.write_text(code, encoding='utf-8')

            # Make executable if needed (bash scripts)
            if language == 'bash':
                filepath.chmod(0o755)

            # Calculate metadata
            file_size = filepath.stat().st_size
            lines = len(code.split('\n'))

            # Run linter if requested
            linter_results = None
            if run_linter:
                linter_results = self._run_linter(str(filepath), language)

            self.logger.info(f"[CODE_GEN] ✓ Generated: {filepath} ({file_size} bytes, {lines} lines)")

            return {
                'success': True,
                'filepath': str(filepath),
                'filename': filename,
                'language': language,
                'size': file_size,
                'lines': lines,
                'linter_results': linter_results,
                'description': description
            }

        except Exception as e:
            error_msg = f"Code generation failed: {str(e)}"
            self.logger.error(f"[CODE_GEN] ✗ {error_msg}")
            return {
                'success': False,
                'error': error_msg
            }


def create_code_generation_tool(output_dir: Optional[str] = None) -> CodeGenerationTool:
    """
    Factory function to create CodeGenerationTool instance.

    Args:
        output_dir: Optional custom output directory

    Returns:
        CodeGenerationTool instance
    """
    return CodeGenerationTool(output_dir=output_dir)
