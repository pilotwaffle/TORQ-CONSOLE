# Marvin/Pydantic Compatibility Guide

## Overview

This document explains the Marvin/Pydantic compatibility issue and the solution implemented in TORQ Console.

## The Problem

### Technical Background

In certain Pydantic v2 versions (specifically 2.5.0-2.7.x), there was an issue with how forward references were resolved during module import time. When Marvin 3.2.3 attempted to use Pydantic models with forward references that included `Field`, Pydantic would try to evaluate these forward references but `Field` wasn't available in the global namespace during the resolution phase.

### Error Symptoms

```python
NameError: name 'Field' is not defined
```

This error occurred deep in the dependency chain:
```
torq_console → marvin → pydantic_ai → pydantic.TypeAdapter() → 
pydantic._resolve_forward_ref() → ERROR: 'Field' not defined
```

### Affected Versions

- **Problematic Pydantic versions**: 2.5.0 - 2.7.x
- **Compatible Pydantic versions**: 2.8.0+ (up to 3.0.0)
- **Marvin version**: 3.2.3

## The Solution

### Version Pinning (Implemented)

We've pinned Pydantic to a compatible version range that avoids the problematic versions:

**`requirements.txt` and `pyproject.toml`:**
```python
pydantic>=2.8.0,<3.0.0
```

This ensures:
- ✅ Minimum version 2.8.0 (has fixed forward reference resolution)
- ✅ Maximum version below 3.0.0 (ensures v2 compatibility)
- ✅ Stable, tested version range
- ✅ No accidental upgrades to incompatible versions

### Optional Dependencies

Marvin is now available as an optional dependency:

```bash
# Install with Marvin support
pip install -e ".[marvin]"

# Or install Marvin separately
pip install "marvin>=3.2.0,<4.0.0"
```

## How It Works

### 1. Core Functionality (Always Available)

The following work without Marvin:
- ✅ All core TORQ functionality
- ✅ LLM providers (OpenAI, Anthropic)
- ✅ Basic agent system
- ✅ File operations
- ✅ Git integration
- ✅ Web UI

### 2. Enhanced Features (With Marvin)

With Marvin installed and compatible:
- ✅ AI-powered specification analysis
- ✅ Structured output generation
- ✅ Intelligent agent orchestration
- ✅ Automatic task planning
- ✅ Advanced AI workflows

### 3. Graceful Degradation

The system automatically detects Marvin availability:

```python
from torq_console.agents import is_marvin_available, get_marvin_status

if is_marvin_available():
    # Use Marvin-powered features
    from torq_console.marvin_integration import TorqMarvinIntegration
    integration = TorqMarvinIntegration()
else:
    # Fall back to RL-only analysis
    from torq_console.spec_kit import RLSpecAnalyzer
    analyzer = RLSpecAnalyzer()
```

## Installation Instructions

### Fresh Installation (Recommended)

```bash
# Clone the repository
git clone https://github.com/pilotwaffle/TORQ-CONSOLE.git
cd TORQ-CONSOLE

# Install with Marvin support
pip install -e ".[marvin]"

# Or install all dependencies
pip install -r requirements.txt
```

### Upgrading Existing Installation

If you have an incompatible Pydantic version:

```bash
# Check your current versions
pip list | grep -E "(pydantic|marvin)"

# Upgrade to compatible versions
pip install "pydantic>=2.8.0,<3.0.0" --upgrade
pip install "marvin>=3.2.0,<4.0.0" --upgrade

# Or reinstall from requirements
pip install -r requirements.txt --upgrade
```

### Fixing Compatibility Issues

If you encounter the Field error:

```bash
# Option 1: Upgrade Pydantic (recommended)
pip install "pydantic>=2.8.0,<3.0.0" --upgrade

# Option 2: Run without Marvin (fallback)
pip uninstall marvin
# TORQ will work with RL-only analysis
```

## Testing Compatibility

Run the compatibility test suite:

```bash
python test_marvin_pydantic_compatibility.py
```

This test will:
- ✅ Verify Pydantic version is compatible
- ✅ Test Marvin imports without Field errors
- ✅ Validate TORQ Marvin integration
- ✅ Check optional import structure
- ✅ Detect version mismatches
- ✅ Provide upgrade recommendations

## CI/CD Integration

The CI pipeline now includes compatibility checks:

```yaml
- name: Install dependencies
  run: |
    python -m pip install --upgrade pip
    pip install -e .
    
- name: Test Marvin compatibility
  run: |
    python test_marvin_pydantic_compatibility.py
```

## Troubleshooting

### Issue: "Field not defined" error on import

**Solution:**
```bash
pip install "pydantic>=2.8.0,<3.0.0" --upgrade
```

### Issue: Marvin features not available

**Check installation:**
```python
from torq_console.agents import is_marvin_available, get_marvin_status
print(get_marvin_status())
```

**Install Marvin:**
```bash
pip install "marvin>=3.2.0,<4.0.0"
```

### Issue: API key not configured

**Set environment variables:**
```bash
export ANTHROPIC_API_KEY="your-key-here"
# or
export OPENAI_API_KEY="your-key-here"
```

### Issue: Different Pydantic version required by other packages

**Use a virtual environment:**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e ".[marvin]"
```

## Version Compatibility Matrix

| Pydantic Version | Marvin 3.2.3 | Status | Notes |
|-----------------|--------------|--------|-------|
| 2.0.0 - 2.4.x   | ⚠️ Untested  | Unknown | Not recommended |
| 2.5.0 - 2.7.x   | ❌ Incompatible | Broken | Field resolution errors |
| 2.8.0 - 2.12.x  | ✅ Compatible | Working | Recommended range |
| 2.13.0+         | ✅ Compatible | Working | Should work |
| 3.0.0+          | ⚠️ Untested  | Unknown | Not tested yet |

## What's Different After This Fix

### Before (Problematic)

```python
# requirements.txt
pydantic>=2.0.0  # Could install incompatible 2.5.0

# Result: Random Field errors depending on installed version
```

### After (Fixed)

```python
# requirements.txt
pydantic>=2.8.0,<3.0.0  # Ensures compatible version

# Result: Consistent, working installation
```

## For Developers

### Adding New Marvin Features

Always use optional imports:

```python
try:
    from torq_console.marvin_integration import TorqMarvinIntegration
    MARVIN_AVAILABLE = True
except ImportError:
    MARVIN_AVAILABLE = False

def my_feature():
    if MARVIN_AVAILABLE:
        # Use Marvin-powered implementation
        integration = TorqMarvinIntegration()
        return integration.extract(...)
    else:
        # Fallback implementation
        return basic_extraction(...)
```

### Testing with Different Versions

```bash
# Test with minimum version
pip install "pydantic==2.8.0"
python test_marvin_pydantic_compatibility.py

# Test with latest compatible version
pip install "pydantic<3.0.0" --upgrade
python test_marvin_pydantic_compatibility.py
```

## Additional Resources

- [Marvin Documentation](https://www.askmarvin.ai/)
- [Pydantic V2 Documentation](https://docs.pydantic.dev/latest/)
- [TORQ Console GitHub Issues](https://github.com/pilotwaffle/TORQ-CONSOLE/issues)

## Summary

The Marvin/Pydantic compatibility issue has been resolved by:

1. ✅ **Pinning Pydantic version** to compatible range (>=2.8.0, <3.0.0)
2. ✅ **Making Marvin optional** with proper fallback mechanisms
3. ✅ **Adding compatibility tests** to catch version mismatches
4. ✅ **Providing clear documentation** and upgrade paths
5. ✅ **Maintaining backward compatibility** with existing code

All AI-powered features work perfectly with the specified version range, and the system gracefully degrades when Marvin is not available.
