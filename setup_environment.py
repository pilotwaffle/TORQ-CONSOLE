#!/usr/bin/env python3
"""
TORQ Console - Environment Setup and Compatibility Checker

This script checks for and fixes common compatibility issues with TORQ Console dependencies,
particularly the Pydantic v2 + Marvin integration issues.
"""

import sys
import subprocess
import os
from typing import List, Dict, Any


def check_python_version() -> bool:
    """Check if Python version is compatible."""
    if sys.version_info < (3, 10):
        print(f"❌ Python {sys.version_info.major}.{sys.version_info.minor} is not supported. Please use Python 3.10+")
        return False
    print(f"[OK] Python {sys.version_info.major}.{sys.version_info.minor} is compatible")
    return True


def check_package_version(package_name: str, min_version: str = None) -> Dict[str, Any]:
    """Check if a package is installed and its version."""
    try:
        result = subprocess.run([sys.executable, "-m", "pip", "show", package_name],
                              capture_output=True, text=True)
        if result.returncode == 0:
            lines = result.stdout.split('\n')
            version = None
            for line in lines:
                if line.startswith('Version:'):
                    version = line.split(':')[1].strip()
                    break

            return {
                "installed": True,
                "version": version,
                "compatible": True  # Would implement version comparison if needed
            }
        else:
            return {"installed": False, "version": None, "compatible": False}
    except Exception as e:
        return {"installed": False, "version": None, "compatible": False, "error": str(e)}


def install_package(package_name: str, version_spec: str = None) -> bool:
    """Install a package with optional version specification."""
    try:
        if version_spec:
            package_spec = f"{package_name}{version_spec}"
        else:
            package_spec = package_name

        print(f"📦 Installing {package_spec}...")
        result = subprocess.run([sys.executable, "-m", "pip", "install", package_spec],
                              capture_output=True, text=True)
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Failed to install {package_name}: {e}")
        return False


def check_marvin_compatibility() -> Dict[str, Any]:
    """Check Marvin installation and Pydantic compatibility."""
    print("\n🔍 Checking Marvin compatibility...")

    # Check Pydantic
    pydantic_info = check_package_version("pydantic")
    if not pydantic_info["installed"]:
        print("❌ Pydantic is not installed")
        return {"compatible": False, "issue": "pydantic_missing"}

    print(f"✅ Pydantic {pydantic_info['version']} is installed")

    # Check Marvin
    marvin_info = check_package_version("marvin")
    if not marvin_info["installed"]:
        print("❌ Marvin is not installed")
        return {"compatible": False, "issue": "marvin_missing"}

    print(f"✅ Marvin {marvin_info['version']} is installed")

    # Test Marvin import with proper error handling
    try:
        # Set environment variable to help with forward reference resolution
        os.environ.setdefault('PYDANTIC_SKIP_VALIDATORS_DURING_IMPORT', '1')

        # Try importing Marvin
        import marvin
        print("✅ Marvin imports successfully")

        # Test basic functionality
        try:
            from pydantic import BaseModel, Field
            class TestModel(BaseModel):
                name: str = Field(..., description="Test field")

            print("✅ Pydantic Field works correctly")
            return {"compatible": True}

        except Exception as e:
            print(f"❌ Pydantic Field issue detected: {e}")
            return {"compatible": False, "issue": "field_import", "error": str(e)}

    except ImportError as e:
        print(f"❌ Marvin import failed: {e}")
        return {"compatible": False, "issue": "marvin_import", "error": str(e)}
    except Exception as e:
        print(f"❌ Marvin compatibility issue: {e}")
        return {"compatible": False, "issue": "unknown", "error": str(e)}


def fix_marvin_compatibility() -> bool:
    """Attempt to fix Marvin compatibility issues."""
    print("\n🔧 Attempting to fix Marvin compatibility...")

    # Strategy 1: Upgrade to latest compatible versions
    print("📈 Upgrading to latest compatible versions...")

    packages_to_upgrade = [
        ("pydantic", ">=2.0.0"),
        ("marvin", ">=0.19.0"),
        ("pydantic-ai", ">=0.0.14"),  # This is often the culprit
    ]

    for package, version_spec in packages_to_upgrade:
        if not install_package(package, version_spec):
            print(f"❌ Failed to upgrade {package}")
            return False

    # Strategy 2: If still failing, try reinstalling
    compatibility = check_marvin_compatibility()
    if not compatibility["compatible"]:
        print("\n🔄 Reinstalling Marvin and dependencies...")

        # Uninstall and reinstall
        packages_to_reinstall = ["marvin", "pydantic-ai"]
        for package in packages_to_reinstall:
            subprocess.run([sys.executable, "-m", "pip", "uninstall", package, "-y"],
                          capture_output=True)
            if not install_package(package):
                print(f"❌ Failed to reinstall {package}")
                return False

    # Final check
    final_compatibility = check_marvin_compatibility()
    return final_compatibility["compatible"]


def test_torq_imports() -> bool:
    """Test if TORQ Console modules can be imported."""
    print("\n🧪 Testing TORQ Console imports...")

    try:
        # Test basic torq_console import
        import torq_console
        print("✅ torq_console imports successfully")

        # Test marvin_integration import
        from torq_console.marvin_integration import MARVIN_AVAILABLE
        print(f"✅ marvin_integration imports successfully (Marvin available: {MARVIN_AVAILABLE})")

        return True

    except ImportError as e:
        print(f"❌ TORQ Console import failed: {e}")
        return False
    except Exception as e:
        print(f"❌ TORQ Console error: {e}")
        return False


def main():
    """Main setup and compatibility check routine."""
    print("TORQ Console - Environment Setup & Compatibility Check")
    print("=" * 60)

    # Check Python version
    if not check_python_version():
        sys.exit(1)

    # Check Marvin compatibility
    compatibility = check_marvin_compatibility()

    if not compatibility["compatible"]:
        print(f"\n❌ Compatibility issue detected: {compatibility.get('issue', 'unknown')}")

        if compatibility.get("error"):
            print(f"Error details: {compatibility['error']}")

        # Attempt to fix
        if fix_marvin_compatibility():
            print("\n✅ Compatibility issues resolved!")
        else:
            print("\n❌ Unable to resolve compatibility issues automatically.")
            print("\n💡 Manual resolution steps:")
            print("1. Upgrade pip: python -m pip install --upgrade pip")
            print("2. Install compatible versions:")
            print("   pip install 'pydantic>=2.0.0' 'marvin>=0.19.0' 'pydantic-ai>=0.0.14'")
            print("3. If issues persist, create a fresh virtual environment")
            sys.exit(1)

    # Test TORQ Console imports
    if test_torq_imports():
        print("\n🎉 TORQ Console is ready to use!")
        print("\n📋 Next steps:")
        print("1. Set your API key (ANTHROPIC_API_KEY or OPENAI_API_KEY)")
        print("2. Run: torq-console or python -m torq_console")
        sys.exit(0)
    else:
        print("\n❌ TORQ Console setup incomplete. Check the errors above.")
        sys.exit(1)


if __name__ == "__main__":
    main()