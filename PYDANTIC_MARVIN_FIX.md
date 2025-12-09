# Pydantic v2 + Marvin Compatibility Fix

## Problem Summary

The TORQ Console codebase is experiencing a `NameError: name 'Field' is not defined` error when trying to import Marvin integration modules. This is a known compatibility issue between Pydantic v2 and Marvin AI framework versions.

## Root Cause Analysis

The error occurs during forward reference resolution in Pydantic when it encounters dataclass field annotations that reference `Field` without it being available in the global namespace. The traceback shows:

1. **Pydantic Version**: 2.5.0
2. **Marvin Version**: 3.2.3
3. **pydantic-ai Version**: 1.12.0
4. **Error Location**: Deep within `pydantic_ai._function_schema` and related modules

## Solutions (in order of preference)

### Solution 1: Upgrade Dependencies (Recommended)

The preferred solution is to use compatible versions:

```bash
# Upgrade to latest compatible versions
pip install --upgrade "pydantic>=2.5.0" "marvin>=3.0.0" "pydantic-ai>=1.12.0"

# If issues persist, try specific working combination:
pip install "pydantic==2.5.3" "marvin==3.2.3" "pydantic-ai==1.12.0"
```

### Solution 2: Fresh Virtual Environment

Create a clean environment with compatible versions:

```bash
# Create new virtual environment
python -m venv torq-env
source torq-env/bin/activate  # On Windows: torq-env\Scripts\activate

# Install dependencies in correct order
pip install --upgrade pip
pip install "pydantic>=2.5.0"
pip install "pydantic-ai>=1.12.0"
pip install "marvin>=3.0.0"
pip install -e .
```

### Solution 3: Environment Variable Workaround

Set environment variables before importing:

```python
import os
os.environ['PYDANTIC_SKIP_VALIDATORS_DURING_IMPORT'] = '1'
os.environ['MARVIN_SKIP_PLUGINS'] = '1'

# Now import TORQ modules
from torq_console.marvin_integration import MARVIN_AVAILABLE
```

### Solution 4: Use the Compatibility Fixes

The codebase includes compatibility fixes in `torq_console/marvin_integration/compatibility.py`:

```python
# Apply fixes before importing
from torq_console.marvin_integration.compatibility import apply_compatibility_fixes
apply_compatibility_fixes()

# Then import normally
from torq_console.marvin_integration import MARVIN_AVAILABLE
```

## Applied Code Fixes

### 1. Updated Dependencies

**File**: `pyproject.toml`
```toml
dependencies = [
    # ... other dependencies
    "marvin>=3.0.0",  # Updated from 0.19.0
]
```

**File**: `requirements.txt`
```
# AI Framework dependencies
marvin>=3.0.0  # Updated from 0.19.0
```

### 2. Enhanced Marvin Integration Init

**File**: `torq_console/marvin_integration/__init__.py`
- Added compatibility fix application before Marvin import
- Added Field import with fallback
- Added graceful error handling when Marvin is unavailable

### 3. Compatibility Module

**File**: `torq_console/marvin_integration/compatibility.py`
- Patches Pydantic forward reference resolution
- Adds Field to global namespace during resolution
- Provides environment variable setup
- Includes comprehensive error checking

### 4. Core Module Updates

**File**: `torq_console/marvin_integration/core.py`
- Added Field import alongside BaseModel import
- Ensures Field is available throughout the integration

## Testing the Fix

### Quick Test Script

```python
import os
os.environ['PYDANTIC_SKIP_VALIDATORS_DURING_IMPORT'] = '1'

try:
    from torq_console.marvin_integration import MARVIN_AVAILABLE, Field
    print(f"✅ Import successful!")
    print(f"Marvin available: {MARVIN_AVAILABLE}")
    print(f"Field type: {type(Field)}")
except Exception as e:
    print(f"❌ Import failed: {e}")
```

### Full Integration Test

```python
import os
os.environ['PYDANTIC_SKIP_VALIDATORS_DURING_IMPORT'] = '1'

try:
    import torq_console
    from torq_console.marvin_integration import TorqMarvinIntegration, MARVIN_AVAILABLE
    print("✅ Full TORQ Console integration successful!")

    if MARVIN_AVAILABLE:
        # Test Marvin functionality
        integration = TorqMarvinIntegration()
        print("✅ Marvin integration working!")
    else:
        print("⚠️  Marvin not available, using stubs")

except Exception as e:
    print(f"❌ Integration failed: {e}")
    import traceback
    traceback.print_exc()
```

## Alternative: Disable Marvin Integration

If Marvin compatibility cannot be resolved, you can disable it temporarily:

```python
# Set environment variable to disable Marvin
os.environ['TORQ_DISABLE_MARVIN'] = '1'

# The codebase will fall back to stub implementations
```

## Manual Resolution Steps

If automated fixes don't work:

1. **Check Package Versions**:
   ```bash
   pip show pydantic marvin pydantic-ai
   ```

2. **Clean Install**:
   ```bash
   pip uninstall marvin pydantic-ai pydantic -y
   pip install "pydantic>=2.5.0" "pydantic-ai>=1.12.0" "marvin>=3.0.0"
   ```

3. **Verify Installation**:
   ```bash
   python -c "import marvin; import pydantic; print('All imports successful')"
   ```

## References

- [Pydantic v2 Migration Guide](https://docs.pydantic.dev/latest/migration/)
- [Marvin AI Documentation](https://marvin.ai/)
- [GitHub Issue: Pydantic v2 Compatibility](https://github.com/prefecthq/marvin/issues)
- [Pydantic Error Documentation](https://errors.pydantic.dev/2.5/u/undefined-annotation)

## Next Steps

1. Try Solution 1 (upgrading dependencies) first
2. If that fails, try Solution 2 (fresh environment)
3. Use Solution 3 or 4 as temporary workarounds
4. Report persistent issues to the TORQ Console maintainers

The compatibility fixes included in the codebase should handle most scenarios, but dependency version alignment is the most reliable long-term solution.