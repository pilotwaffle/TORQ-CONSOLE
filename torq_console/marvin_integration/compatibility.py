"""
Pydantic v2 Compatibility Fixes for Marvin Integration

This module provides compatibility fixes for the known issues between
Marvin AI framework and Pydantic v2, particularly the "name 'Field' is not defined"
error that occurs during forward reference resolution.
"""

import sys
import warnings
from typing import Any, Dict, Optional


def patch_pydantic_forward_refs():
    """
    Patch Pydantic's forward reference resolution to handle Field imports.

    This addresses the issue where Pydantic v2 can't resolve 'Field' in forward
    references when used with Marvin AI framework.
    """
    try:
        from pydantic._internal._typing_extra import evaluate_fwd_ref

        # Store the original function
        original_evaluate_fwd_ref = evaluate_fwd_ref

        def patched_evaluate_fwd_ref(*args, **kwargs):
            """Patched version that adds Field to globals if missing."""
            # Handle both old and new function signatures
            if len(args) >= 3:
                ref, globalns, localns = args[0], args[1], args[2]
            elif len(args) == 2 and 'globalns' in kwargs:
                ref, globalns = args[0], kwargs['globalns']
                localns = kwargs.get('localns', None)
            else:
                # Fall back to original if signature doesn't match
                return original_evaluate_fwd_ref(*args, **kwargs)

            # Ensure Field is available in global namespace
            if globalns is None:
                globalns = {}

            # Add Field to globals if not present and not already imported
            if 'Field' not in globalns:
                try:
                    from pydantic import Field
                    globalns['Field'] = Field
                except ImportError:
                    # Fallback - create a dummy Field function
                    def dummy_field(*args, **kwargs):
                        from dataclasses import field
                        return field(default_factory=lambda: None)
                    globalns['Field'] = dummy_field

            # Also add other commonly missing imports
            common_missing = {
                'Annotated': 'typing.Annotated',
                'Optional': 'typing.Optional',
                'Union': 'typing.Union',
                'List': 'typing.List',
                'Dict': 'typing.Dict',
            }

            for name, import_path in common_missing.items():
                if name not in globalns:
                    try:
                        module, attr = import_path.split('.')
                        imported_mod = __import__(module, fromlist=[attr])
                        globalns[name] = getattr(imported_mod, attr)
                    except (ImportError, AttributeError):
                        pass

            # Call original function with patched globals
            return original_evaluate_fwd_ref(ref, globalns, localns)

        # Apply the patch
        import pydantic._internal._typing_extra
        pydantic._internal._typing_extra.evaluate_fwd_ref = patched_evaluate_fwd_ref

        return True

    except ImportError:
        warnings.warn("Could not import Pydantic internals for patching", ImportWarning)
        return False


def setup_marvin_environment():
    """
    Set up the environment for Marvin compatibility.
    """
    # Set environment variables that help with compatibility
    import os

    # These environment variables can help with various compatibility issues
    os.environ.setdefault('PYDANTIC_SKIP_VALIDATORS_DURING_IMPORT', '1')
    os.environ.setdefault('MARVIN_SKIP_PLUGINS', '1')

    # Try to patch forward reference resolution
    patch_success = patch_pydantic_forward_refs()

    if not patch_success:
        warnings.warn("Could not apply Pydantic forward reference patches", RuntimeWarning)

    return patch_success


def check_marvin_compatibility() -> Dict[str, Any]:
    """
    Check if Marvin is compatible with the current environment.
    """
    results = {
        'marvin_available': False,
        'pydantic_compatible': False,
        'patches_applied': False,
        'errors': []
    }

    try:
        import pydantic
        from pydantic import BaseModel, Field

        # Test basic Pydantic functionality
        class TestModel(BaseModel):
            name: str = Field(..., description="Test field")

        test_instance = TestModel(name="test")
        assert test_instance.name == "test"

        results['pydantic_compatible'] = True

    except Exception as e:
        results['errors'].append(f"Pydantic compatibility issue: {e}")

    try:
        import marvin
        results['marvin_available'] = True

        # Test basic Marvin functionality
        try:
            # This might fail due to the forward reference issue
            settings = marvin.settings
            results['marvin_works'] = True
        except Exception as e:
            results['errors'].append(f"Marvin settings issue: {e}")
            results['marvin_works'] = False

    except ImportError as e:
        results['errors'].append(f"Marvin not available: {e}")

    return results


def apply_compatibility_fixes():
    """
    Apply all known compatibility fixes for Marvin and Pydantic v2.
    """
    fixes_applied = []

    # Fix 1: Setup environment
    if setup_marvin_environment():
        fixes_applied.append("Environment variables set")

    # Fix 2: Patch forward references
    try:
        if patch_pydantic_forward_refs():
            fixes_applied.append("Forward reference resolution patched")
    except Exception as e:
        warnings.warn(f"Failed to patch forward references: {e}")

    # Fix 3: Pre-import Field in key modules
    try:
        # This ensures Field is in the module namespace before Marvin imports
        from pydantic import Field

        # Inject Field into sys.modules to make it globally available
        if 'Field' not in sys.modules:
            class _FieldModule:
                def __getattr__(self, name):
                    if name == 'Field':
                        return Field
                    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

            sys.modules['Field'] = _FieldModule()
            fixes_applied.append("Field injected into sys.modules")

    except ImportError:
        fixes_applied.append("Field not available for injection")

    return fixes_applied


# Apply fixes automatically when module is imported
_apply_result = apply_compatibility_fixes()

if not _apply_result:
    warnings.warn("No compatibility fixes could be applied", RuntimeWarning)