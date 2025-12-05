# Quick Implementation Guide - Next Steps

**For:** TORQ Console Maintainers and Contributors  
**Date:** December 5, 2025  
**Based on:** IMPROVEMENT_RECOMMENDATIONS.md

---

## Purpose

This guide provides **copy-paste ready commands and configurations** for implementing the recommended improvements. Each section is independent and can be completed separately.

---

## Phase 1: CI/CD Pipeline (High Priority)

### 1.1 Create GitHub Actions Workflow

Create `.github/workflows/ci.yml`:

```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install flake8 bandit mypy black isort
      
      - name: Format check with Black
        run: black --check torq_console/
      
      - name: Import sort check with isort
        run: isort --check-only torq_console/
      
      - name: Lint with flake8
        run: |
          flake8 torq_console/ --count --select=E9,F63,F7,F82 --show-source --statistics
          flake8 torq_console/ --count --max-complexity=10 --max-line-length=100 --statistics
      
      - name: Security scan with bandit
        run: bandit -r torq_console/ -ll -f json -o bandit-report.json
      
      - name: Type check with mypy
        run: mypy torq_console/ --ignore-missing-imports || true

  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ['3.10', '3.11', '3.12']
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -e .
          pip install pytest pytest-cov pytest-asyncio pytest-mock
      
      - name: Run tests with coverage
        run: |
          pytest --cov=torq_console --cov-report=xml --cov-report=term
      
      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
          flags: unittests
          name: codecov-umbrella

  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install safety pip-audit
      
      - name: Check for vulnerabilities with safety
        run: safety check --json || true
      
      - name: Audit dependencies with pip-audit
        run: pip-audit || true
```

**Commands to run:**
```bash
# Create workflow directory
mkdir -p .github/workflows

# Create the file (copy content above)
cat > .github/workflows/ci.yml << 'EOF'
# Paste YAML content here
EOF

# Test locally (requires act)
act -j lint
```

### 1.2 Add Code Quality Checks

Create `.flake8`:
```ini
[flake8]
max-line-length = 100
extend-ignore = E203, W503
exclude =
    .git,
    __pycache__,
    build,
    dist,
    .eggs,
    *.egg-info,
    venv,
    env
max-complexity = 10
```

Create `pyproject.toml` (add to existing or create new):
```toml
[tool.black]
line-length = 100
target-version = ['py310']
include = '\.pyi?$'
extend-exclude = '''
/(
    \.eggs
  | \.git
  | \.hg
  | \.mypy_cache
  | \.tox
  | \.venv
  | _build
  | buck-out
  | build
  | dist
)/
'''

[tool.isort]
profile = "black"
line_length = 100
skip_gitignore = true

[tool.mypy]
python_version = "3.10"
warn_return_any = true
warn_unused_configs = true
ignore_missing_imports = true

[tool.pytest.ini_options]
minversion = "7.0"
addopts = "-ra -q --strict-markers"
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
```

**Commands to run:**
```bash
# Create config files
cat > .flake8 << 'EOF'
# Paste config above
EOF

cat > pyproject.toml << 'EOF'
# Paste config above
EOF

# Test configurations
flake8 torq_console/
black --check torq_console/
isort --check-only torq_console/
```

---

## Phase 2: Pre-commit Hooks (High Priority)

### 2.1 Install Pre-commit Framework

Create `.pre-commit-config.yaml`:
```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
        args: ['--maxkb=1000']
      - id: check-json
      - id: check-toml
      - id: check-merge-conflict
      - id: detect-private-key
  
  - repo: https://github.com/psf/black
    rev: 23.12.1
    hooks:
      - id: black
        language_version: python3.10
  
  - repo: https://github.com/pycqa/isort
    rev: 5.13.2
    hooks:
      - id: isort
        args: ["--profile", "black"]
  
  - repo: https://github.com/pycqa/flake8
    rev: 7.0.0
    hooks:
      - id: flake8
        args: ['--max-line-length=100', '--extend-ignore=E203,W503']
  
  - repo: https://github.com/PyCQA/bandit
    rev: 1.7.6
    hooks:
      - id: bandit
        args: ['-ll', '-r', 'torq_console']
        pass_filenames: false
  
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.8.0
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
        args: [--ignore-missing-imports]
```

**Commands to run:**
```bash
# Install pre-commit
pip install pre-commit

# Create config file
cat > .pre-commit-config.yaml << 'EOF'
# Paste YAML above
EOF

# Install hooks
pre-commit install

# Run on all files (one-time)
pre-commit run --all-files

# Test
git add .
git commit -m "test"  # Hooks will run automatically
```

---

## Phase 3: Test Organization (Medium Priority)

### 3.1 Reorganize Test Structure

**Commands to run:**
```bash
# Create new test structure
mkdir -p tests/{unit,integration,e2e}
mkdir -p tests/unit/{test_agents,test_api,test_core,test_utils}

# Create conftest.py for shared fixtures
cat > tests/conftest.py << 'EOF'
"""Shared pytest fixtures for TORQ Console tests."""
import pytest
import asyncio
from pathlib import Path

@pytest.fixture
def temp_workspace(tmp_path):
    """Create a temporary workspace directory."""
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    return workspace

@pytest.fixture
def sample_code_file(temp_workspace):
    """Create a sample Python file for testing."""
    code_file = temp_workspace / "sample.py"
    code_file.write_text("""
def hello_world():
    '''Say hello.'''
    return "Hello, World!"

class Calculator:
    def add(self, a, b):
        return a + b
""")
    return code_file

@pytest.fixture
def event_loop():
    """Create an event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()
EOF

# Create example unit test
cat > tests/unit/test_core/test_context_manager.py << 'EOF'
"""Unit tests for ContextManager."""
import pytest
from torq_console.core.context_manager import ContextManager

@pytest.mark.asyncio
async def test_context_manager_initialization():
    """Test ContextManager can be initialized."""
    cm = ContextManager()
    assert cm is not None

@pytest.mark.asyncio
async def test_parse_simple_reference(sample_code_file):
    """Test parsing simple file reference."""
    cm = ContextManager()
    result = await cm.parse(f"@{sample_code_file}")
    assert result is not None
EOF

# Move existing tests (if any)
find . -maxdepth 1 -name "test_*.py" -exec mv {} tests/unit/ \;

# Update pytest configuration
cat >> pyproject.toml << 'EOF'

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
markers = [
    "unit: Unit tests",
    "integration: Integration tests",
    "e2e: End-to-end tests",
    "slow: Slow-running tests",
]
EOF
```

### 3.2 Add Coverage Configuration

Add to `pyproject.toml`:
```toml
[tool.coverage.run]
source = ["torq_console"]
omit = [
    "*/tests/*",
    "*/test_*.py",
    "*/__pycache__/*",
    "*/site-packages/*",
]

[tool.coverage.report]
precision = 2
show_missing = true
skip_covered = false
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError",
    "if __name__ == .__main__.:",
    "if TYPE_CHECKING:",
]
```

**Commands to run:**
```bash
# Run tests with coverage
pytest --cov=torq_console --cov-report=html --cov-report=term

# View coverage report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

---

## Phase 4: Documentation Setup (Medium Priority)

### 4.1 Set Up Sphinx Documentation

**Commands to run:**
```bash
# Install Sphinx
pip install sphinx sphinx-rtd-theme sphinx-autodoc-typehints

# Create docs directory
mkdir -p docs
cd docs

# Initialize Sphinx
sphinx-quickstart --quiet --project="TORQ Console" --author="B Flowers" \
  --release="0.80.0" --language="en" --ext-autodoc --ext-viewcode \
  --ext-napoleon --extensions=sphinx_autodoc_typehints

# Configure theme in conf.py
cat >> conf.py << 'EOF'
html_theme = 'sphinx_rtd_theme'
html_theme_options = {
    'navigation_depth': 4,
    'collapse_navigation': False,
}
EOF

# Create index structure
cat > index.rst << 'EOF'
TORQ Console Documentation
==========================

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   getting-started/index
   user-guide/index
   api-reference/index
   development/index

Getting Started
--------------

Quick start guide and installation instructions.

User Guide
----------

Comprehensive guide for using TORQ Console.

API Reference
------------

Detailed API documentation for developers.

Development
-----------

Contributing guidelines and development setup.

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
EOF

# Build documentation
make html

# View documentation
cd ..
open docs/_build/html/index.html
```

---

## Phase 5: Development Tools (Low Priority)

### 5.1 Add Makefile for Common Tasks

Create `Makefile`:
```makefile
.PHONY: help install test lint format security clean docs

help:
	@echo "TORQ Console - Development Commands"
	@echo ""
	@echo "  make install    Install development dependencies"
	@echo "  make test       Run tests with coverage"
	@echo "  make lint       Run linters"
	@echo "  make format     Format code with black and isort"
	@echo "  make security   Run security checks"
	@echo "  make clean      Clean build artifacts"
	@echo "  make docs       Build documentation"
	@echo ""

install:
	pip install -e ".[dev]"
	pip install pytest pytest-cov black flake8 mypy isort bandit safety
	pre-commit install

test:
	pytest --cov=torq_console --cov-report=html --cov-report=term-missing

lint:
	flake8 torq_console/
	mypy torq_console/ --ignore-missing-imports

format:
	black torq_console/
	isort torq_console/

security:
	bandit -r torq_console/ -ll
	safety check
	pip-audit

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	rm -rf build/ dist/ htmlcov/ .coverage

docs:
	cd docs && make html
	@echo "Documentation built: docs/_build/html/index.html"
```

**Commands to run:**
```bash
# Test the Makefile
make help
make install
make format
make test
```

### 5.2 Add requirements-dev.txt

Create `requirements-dev.txt`:
```txt
# Testing
pytest>=7.4.0
pytest-cov>=4.1.0
pytest-asyncio>=0.21.0
pytest-mock>=3.11.0
hypothesis>=6.82.0

# Code Quality
black>=23.7.0
isort>=5.12.0
flake8>=6.1.0
mypy>=1.5.0
pylint>=2.17.0

# Security
bandit>=1.7.5
safety>=2.3.0
pip-audit>=2.6.0

# Documentation
sphinx>=7.1.0
sphinx-rtd-theme>=1.3.0
sphinx-autodoc-typehints>=1.24.0

# Development Tools
pre-commit>=3.3.0
ipython>=8.14.0
ipdb>=0.13.13
```

**Commands to run:**
```bash
# Install dev dependencies
pip install -r requirements-dev.txt
```

---

## Phase 6: Code Quality Improvements (Ongoing)

### 6.1 Add Type Hints

**Example refactoring:**
```python
# Before
def process_data(data):
    return data.upper()

# After
from typing import Optional

def process_data(data: str) -> Optional[str]:
    """
    Process data by converting to uppercase.
    
    Args:
        data: Input string to process
        
    Returns:
        Uppercase string, or None if input is invalid
    """
    if not isinstance(data, str):
        return None
    return data.upper()
```

### 6.2 Add Docstrings

**Template:**
```python
def function_name(param1: Type1, param2: Type2) -> ReturnType:
    """
    Brief one-line description.
    
    Detailed explanation if needed. Can be multiple paragraphs.
    
    Args:
        param1: Description of param1
        param2: Description of param2
        
    Returns:
        Description of return value
        
    Raises:
        ValueError: When input is invalid
        RuntimeError: When operation fails
        
    Example:
        >>> result = function_name("test", 42)
        >>> print(result)
        Expected output
        
    Note:
        Additional notes or warnings.
    """
    pass
```

---

## Quick Reference

### Daily Development Workflow

```bash
# 1. Pull latest changes
git pull origin main

# 2. Create feature branch
git checkout -b feature/my-feature

# 3. Make changes...

# 4. Format code
make format

# 5. Run tests
make test

# 6. Commit (pre-commit hooks run automatically)
git add .
git commit -m "feat: add new feature"

# 7. Push and create PR
git push origin feature/my-feature
```

### Before Committing

```bash
# Run all checks
make format && make lint && make test && make security
```

### CI/CD Status Check

```bash
# View GitHub Actions status
gh run list

# View specific run
gh run view <run-id>

# Re-run failed jobs
gh run rerun <run-id>
```

---

## Troubleshooting

### Pre-commit Hook Failures

```bash
# Skip hooks for emergency commit (use sparingly)
git commit --no-verify -m "emergency fix"

# Update hooks
pre-commit autoupdate

# Clear cache and retry
pre-commit clean
pre-commit run --all-files
```

### Test Failures

```bash
# Run specific test
pytest tests/unit/test_agents/test_agent.py::test_specific_case -v

# Debug with pdb
pytest --pdb tests/unit/test_agents/test_agent.py

# Show print statements
pytest -s tests/unit/test_agents/test_agent.py
```

### Documentation Build Errors

```bash
# Clean and rebuild
cd docs
make clean
make html

# Check for warnings
make html SPHINXOPTS="-W"
```

---

## Next Steps After Implementation

1. ✅ **Verify CI/CD** - Check that all GitHub Actions pass
2. ✅ **Monitor Coverage** - Ensure coverage doesn't decrease
3. ✅ **Update Team** - Share new workflow with contributors
4. ✅ **Iterate** - Refine configurations based on feedback

---

**Questions?** See CONTRIBUTING.md or open an issue on GitHub.
