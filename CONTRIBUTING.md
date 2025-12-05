# Contributing to TORQ Console

Thank you for your interest in contributing to TORQ Console! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [How to Contribute](#how-to-contribute)
- [Coding Guidelines](#coding-guidelines)
- [Testing Requirements](#testing-requirements)
- [Pull Request Process](#pull-request-process)
- [Issue Reporting](#issue-reporting)
- [Community](#community)

## Code of Conduct

### Our Pledge

We are committed to providing a welcoming and inclusive environment for all contributors. We pledge to:

- Be respectful and considerate in all interactions
- Welcome diverse perspectives and experiences
- Accept constructive criticism gracefully
- Focus on what is best for the community and project
- Show empathy towards other community members

### Our Standards

**Positive Behavior:**
- Using welcoming and inclusive language
- Being respectful of differing viewpoints
- Gracefully accepting constructive criticism
- Focusing on collaboration and mutual success
- Showing empathy and kindness to others

**Unacceptable Behavior:**
- Harassment, discrimination, or offensive comments
- Trolling, insulting, or derogatory remarks
- Public or private harassment
- Publishing others' private information
- Other conduct inappropriate in a professional setting

## Getting Started

### Prerequisites

- Python 3.10 or higher
- Git for version control
- Basic understanding of async Python programming
- Familiarity with FastAPI (for API contributions)
- Knowledge of AI/LLM concepts (for agent contributions)

### Development Setup

1. **Fork and Clone the Repository**
   ```bash
   # Fork the repository on GitHub first
   git clone https://github.com/YOUR-USERNAME/TORQ-CONSOLE.git
   cd TORQ-CONSOLE
   ```

2. **Set Up Development Environment**
   ```bash
   # Create virtual environment
   python -m venv venv
   
   # Activate virtual environment
   # On Windows:
   venv\Scripts\activate
   # On Linux/Mac:
   source venv/bin/activate
   
   # Install development dependencies
   pip install -e ".[dev]"
   ```

3. **Install Development Tools**
   ```bash
   # Install code quality tools
   pip install pytest pytest-cov black flake8 mypy bandit pre-commit
   
   # Install pre-commit hooks
   pre-commit install
   ```

4. **Configure Environment**
   ```bash
   # Copy example environment file
   cp .env.example .env
   
   # Edit .env with your API keys (optional for development)
   # ANTHROPIC_API_KEY=your_key_here
   # OPENAI_API_KEY=your_key_here
   ```

5. **Verify Installation**
   ```bash
   # Run tests
   pytest
   
   # Start the application
   python -m torq_console.cli --web
   ```

## How to Contribute

### Types of Contributions

We welcome various types of contributions:

1. **Bug Fixes**
   - Fix reported issues
   - Improve error handling
   - Resolve edge cases

2. **New Features**
   - Add new AI agents
   - Integrate new LLM providers
   - Enhance existing functionality
   - Add new MCP servers

3. **Documentation**
   - Improve README and guides
   - Add code comments
   - Write tutorials and examples
   - Create API documentation

4. **Testing**
   - Write unit tests
   - Add integration tests
   - Create E2E test scenarios
   - Improve test coverage

5. **Code Quality**
   - Refactor complex code
   - Improve performance
   - Enhance type hints
   - Fix linting issues

### Finding Issues to Work On

- **Good First Issues:** Look for issues tagged with `good first issue`
- **Help Wanted:** Check issues tagged with `help wanted`
- **Bug Reports:** Browse open bug reports
- **Feature Requests:** Review feature request discussions

## Coding Guidelines

### Code Style

We follow PEP 8 with some modifications:

```python
# Line length: 100 characters (not 79)
MAX_LINE_LENGTH = 100

# Use Black for automatic formatting
black torq_console/

# Use isort for import sorting
isort torq_console/
```

### Python Style Guide

**Good:**
```python
from typing import Optional, List, Dict
import asyncio

class MyAgent:
    """Brief description of the agent.
    
    Detailed explanation of the agent's purpose and behavior.
    
    Attributes:
        name: The agent's name
        capabilities: List of agent capabilities
    """
    
    def __init__(self, name: str, capabilities: List[str]) -> None:
        """Initialize the agent.
        
        Args:
            name: The agent's name
            capabilities: List of capabilities
        """
        self.name = name
        self.capabilities = capabilities
    
    async def process(self, input_data: str) -> Optional[Dict[str, str]]:
        """Process input data asynchronously.
        
        Args:
            input_data: Input string to process
            
        Returns:
            Processed result or None if processing fails
            
        Raises:
            ValueError: If input_data is empty
        """
        if not input_data:
            raise ValueError("input_data cannot be empty")
        
        # Process the data
        result = await self._do_processing(input_data)
        return result
```

**Avoid:**
```python
# Missing type hints
def process(input_data):
    return process_data(input_data)

# Missing docstrings
class MyAgent:
    def __init__(self, name):
        self.name = name
        
# Bare except clauses
try:
    result = risky_operation()
except:  # Too broad!
    pass
```

### Documentation Standards

**Module-Level Documentation:**
```python
"""
Module for handling AI agent orchestration.

This module provides the core functionality for coordinating multiple
AI agents to accomplish complex tasks through collaboration.

Example:
    >>> from torq_console.agents import Orchestrator
    >>> orchestrator = Orchestrator()
    >>> result = await orchestrator.process("Build a web app")
"""
```

**Function Documentation:**
```python
def complex_function(
    param1: str,
    param2: int,
    optional_param: Optional[bool] = None
) -> Dict[str, Any]:
    """
    Brief one-line description.
    
    More detailed explanation of what the function does,
    including any important behavioral notes or side effects.
    
    Args:
        param1: Description of param1
        param2: Description of param2
        optional_param: Optional parameter description. Defaults to None.
        
    Returns:
        Dictionary containing:
            - key1: Description of key1
            - key2: Description of key2
            
    Raises:
        ValueError: When param2 is negative
        RuntimeError: When operation fails
        
    Example:
        >>> result = complex_function("test", 42)
        >>> print(result['key1'])
        expected value
        
    Note:
        Any important notes or warnings about usage.
    """
    pass
```

### Type Hints

Use type hints for all public functions and methods:

```python
from typing import Optional, List, Dict, Union, Any, TypeVar, Generic

T = TypeVar('T')

def process_items(items: List[str]) -> Dict[str, int]:
    """Process a list of items."""
    return {item: len(item) for item in items}

async def fetch_data(
    url: str,
    timeout: Optional[int] = None
) -> Union[Dict[str, Any], None]:
    """Fetch data from URL."""
    pass

class Container(Generic[T]):
    """Generic container class."""
    
    def add(self, item: T) -> None:
        """Add item to container."""
        pass
```

### Error Handling

**Always use specific exceptions:**
```python
# Good
try:
    result = perform_operation()
except ValueError as e:
    logger.error(f"Invalid value: {e}")
    raise
except IOError as e:
    logger.error(f"IO error: {e}")
    return None

# Avoid
try:
    result = perform_operation()
except:  # Too broad!
    pass
```

**Create custom exceptions when appropriate:**
```python
class TorqConsoleError(Exception):
    """Base exception for TORQ Console."""
    pass

class AgentError(TorqConsoleError):
    """Raised when an agent encounters an error."""
    pass

class ConfigurationError(TorqConsoleError):
    """Raised when configuration is invalid."""
    pass
```

## Testing Requirements

### Writing Tests

All contributions should include appropriate tests:

1. **Unit Tests** - Test individual functions and methods
   ```python
   # test_my_module.py
   import pytest
   from torq_console.my_module import my_function
   
   def test_my_function_success():
       """Test successful operation."""
       result = my_function("input")
       assert result == "expected"
   
   def test_my_function_error():
       """Test error handling."""
       with pytest.raises(ValueError):
           my_function("")
   ```

2. **Integration Tests** - Test component interactions
   ```python
   @pytest.mark.asyncio
   async def test_agent_integration():
       """Test agent integration with orchestrator."""
       orchestrator = Orchestrator()
       result = await orchestrator.process("task")
       assert result.success is True
   ```

3. **Test Coverage** - Aim for 80%+ coverage
   ```bash
   # Run tests with coverage
   pytest --cov=torq_console --cov-report=html
   
   # View coverage report
   open htmlcov/index.html
   ```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_agents.py

# Run specific test
pytest tests/test_agents.py::test_agent_creation

# Run with verbose output
pytest -v

# Run with coverage
pytest --cov=torq_console

# Run only fast tests (skip slow integration tests)
pytest -m "not slow"
```

### Test Markers

Use pytest markers to categorize tests:
```python
import pytest

@pytest.mark.unit
def test_unit_function():
    """Unit test."""
    pass

@pytest.mark.integration
async def test_integration():
    """Integration test."""
    pass

@pytest.mark.slow
async def test_slow_operation():
    """Slow test that takes >1 second."""
    pass
```

## Pull Request Process

### Before Submitting

1. **Create a Feature Branch**
   ```bash
   git checkout -b feature/my-new-feature
   # or
   git checkout -b fix/bug-description
   ```

2. **Make Your Changes**
   - Write clear, focused commits
   - Follow coding guidelines
   - Add tests for new functionality
   - Update documentation

3. **Run Quality Checks**
   ```bash
   # Format code
   black torq_console/
   isort torq_console/
   
   # Run linters
   flake8 torq_console/
   mypy torq_console/
   
   # Run security scan
   bandit -r torq_console/
   
   # Run tests
   pytest --cov=torq_console
   ```

4. **Update Documentation**
   - Add docstrings to new code
   - Update README if needed
   - Add examples if applicable
   - Update CHANGELOG.md

### Submitting the Pull Request

1. **Commit Your Changes**
   ```bash
   git add .
   git commit -m "feat: add new agent for code review"
   
   # Follow conventional commit format:
   # feat: new feature
   # fix: bug fix
   # docs: documentation changes
   # test: add or update tests
   # refactor: code refactoring
   # perf: performance improvements
   # chore: maintenance tasks
   ```

2. **Push to Your Fork**
   ```bash
   git push origin feature/my-new-feature
   ```

3. **Create Pull Request on GitHub**
   - Go to your fork on GitHub
   - Click "New Pull Request"
   - Select your branch
   - Fill in the PR template

### Pull Request Template

```markdown
## Description
Brief description of the changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Refactoring
- [ ] Performance improvement

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] All tests passing

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex code
- [ ] Documentation updated
- [ ] No new warnings generated
- [ ] Tests added and passing

## Related Issues
Closes #(issue number)
```

### Review Process

1. **Automated Checks** - CI/CD runs tests and quality checks
2. **Code Review** - Maintainers review your code
3. **Feedback** - Address any requested changes
4. **Approval** - Once approved, your PR will be merged

**Response Times:**
- Initial review: Usually within 1-3 days
- Follow-up reviews: Usually within 1-2 days
- Merge: After approval and passing all checks

## Issue Reporting

### Bug Reports

Use the bug report template:

```markdown
**Describe the Bug**
Clear description of the bug

**To Reproduce**
Steps to reproduce:
1. Run command '...'
2. Enter input '...'
3. See error

**Expected Behavior**
What should happen

**Actual Behavior**
What actually happens

**Environment**
- OS: [e.g., Windows 11, Ubuntu 22.04]
- Python Version: [e.g., 3.10.5]
- TORQ Console Version: [e.g., 0.80.0]

**Additional Context**
Any other relevant information
```

### Feature Requests

Use the feature request template:

```markdown
**Feature Description**
Clear description of the proposed feature

**Use Case**
Why is this feature needed?

**Proposed Solution**
How should this work?

**Alternatives Considered**
Other approaches you've considered

**Additional Context**
Any other relevant information
```

## Community

### Communication Channels

- **GitHub Issues:** Bug reports and feature requests
- **GitHub Discussions:** General questions and discussions
- **Discord/Slack:** Real-time chat (if available)

### Getting Help

- Check existing documentation
- Search closed issues for similar problems
- Ask in discussions before opening an issue
- Be specific and provide examples

### Recognition

Contributors are recognized in:
- CHANGELOG.md for each release
- README.md contributors section
- Release notes

## License

By contributing to TORQ Console, you agree that your contributions will be licensed under the MIT License.

---

**Thank you for contributing to TORQ Console!** Your efforts help make this project better for everyone.

For questions or concerns, please open an issue or start a discussion on GitHub.
