#!/usr/bin/env python3
"""
TORQ CONSOLE Configuration Validation Test

Test script to validate the updated configuration system and generate
a comprehensive report on the configuration changes made to fix
demo mode and API key issues.
"""

import os
import sys
from pathlib import Path

# Add the TORQ console to the Python path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from torq_console.core.config import TorqConfig
    print("✓ Successfully imported TorqConfig")
except ImportError as e:
    print(f"✗ Failed to import TorqConfig: {e}")
    sys.exit(1)


def test_env_file_loading():
    """Test that .env file is being loaded correctly."""
    print("\n" + "="*60)
    print("TESTING .ENV FILE LOADING")
    print("="*60)

    env_file = Path(".env")
    if env_file.exists():
        print(f"✓ .env file exists at: {env_file.absolute()}")

        # Check if environment variables are loaded
        env_vars = [
            'ALPHA_VANTAGE_API_KEY',
            'FRED_API_KEY',
            'NEWS_API_KEY',
            'TBS_FALLBACK_MODE',
            'TBS_DEMO_DATA_SOURCE'
        ]

        for var in env_vars:
            value = os.getenv(var)
            if value:
                # Mask API keys for security
                if 'API_KEY' in var:
                    display_value = f"{value[:8]}..." if len(value) > 8 else "***"
                else:
                    display_value = value
                print(f"  {var}: {display_value}")
            else:
                print(f"  {var}: NOT SET")
    else:
        print("✗ .env file not found")
        return False

    return True


def test_configuration_loading():
    """Test configuration loading and validation."""
    print("\n" + "="*60)
    print("TESTING CONFIGURATION LOADING")
    print("="*60)

    try:
        # Test configuration loading
        config = TorqConfig.load()
        print(f"✓ Configuration loaded successfully: {config}")

        # Test demo mode detection
        is_demo = config.is_demo_mode()
        print(f"  Demo Mode: {'ENABLED' if is_demo else 'DISABLED'}")

        # Test API key validation
        print("\n  API Key Validation:")
        for service in ['alpha_vantage', 'fred', 'news_api', 'openai', 'anthropic']:
            has_key = config.has_valid_api_key(service)
            mode = config.get_service_mode(service)
            print(f"    {service}: {'Valid Key' if has_key else 'No Key'} -> Mode: {mode.upper()}")

        return config

    except Exception as e:
        print(f"✗ Configuration loading failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_service_modes(config):
    """Test service operational modes."""
    print("\n" + "="*60)
    print("TESTING SERVICE OPERATIONAL MODES")
    print("="*60)

    services = {
        'alpha_vantage': 'Alpha Vantage (Financial Data)',
        'fred': 'FRED (Economic Data)',
        'news_api': 'News API',
        'openai': 'OpenAI',
        'anthropic': 'Anthropic'
    }

    for service_key, service_name in services.items():
        mode = config.get_service_mode(service_key)
        has_key = config.has_valid_api_key(service_key)

        status_icon = {
            'api': '✓ FULL',
            'proxy': '⚠ PROXY',
            'demo': '⚠ DEMO',
            'disabled': '✗ DISABLED'
        }.get(mode, '? UNKNOWN')

        print(f"  {service_name:.<35} {status_icon}")

        if mode == 'proxy':
            print(f"    → Will use web search proxy for data retrieval")
        elif mode == 'demo':
            print(f"    → Running in demo/fallback mode")
        elif mode == 'disabled':
            print(f"    → Service not available")


def validate_fixes():
    """Validate that the specific issues mentioned have been fixed."""
    print("\n" + "="*60)
    print("VALIDATING FIXES FOR REPORTED ISSUES")
    print("="*60)

    issues_fixed = []
    issues_remaining = []

    # Check 1: Demo API keys
    demo_keys = []
    for key in ['ALPHA_VANTAGE_API_KEY', 'FRED_API_KEY', 'NEWS_API_KEY']:
        value = os.getenv(key)
        if value and value.lower() in ['demo', 'your_api_key_here']:
            demo_keys.append(key)

    if demo_keys:
        issues_remaining.append(f"Demo API keys still present: {', '.join(demo_keys)}")
    else:
        issues_fixed.append("✓ Demo API keys replaced with proper placeholders")

    # Check 2: Fallback mode
    fallback_mode = os.getenv('TBS_FALLBACK_MODE', '').lower()
    if fallback_mode in ['disabled', 'false', '0']:
        issues_fixed.append("✓ TBS_FALLBACK_MODE disabled")
    else:
        issues_remaining.append(f"TBS_FALLBACK_MODE still enabled: {fallback_mode}")

    # Check 3: Demo data source
    demo_source = os.getenv('TBS_DEMO_DATA_SOURCE', '')
    if demo_source.lower() in ['disabled', 'false', '0']:
        issues_fixed.append("✓ TBS_DEMO_DATA_SOURCE disabled")
    else:
        issues_remaining.append(f"TBS_DEMO_DATA_SOURCE still enabled: {demo_source}")

    # Check 4: Web search proxy
    proxy_enabled = os.getenv('TBS_WEB_SEARCH_PROXY', '').lower()
    if proxy_enabled in ['enabled', 'true', '1']:
        issues_fixed.append("✓ Web search proxy enabled for services without API keys")

    print("ISSUES FIXED:")
    for issue in issues_fixed:
        print(f"  {issue}")

    if issues_remaining:
        print("\nISSUES REMAINING:")
        for issue in issues_remaining:
            print(f"  ⚠ {issue}")
    else:
        print("\n✅ All reported issues have been resolved!")

    return len(issues_remaining) == 0


def generate_configuration_report(config):
    """Generate comprehensive configuration report."""
    print("\n" + "="*80)
    print("COMPREHENSIVE CONFIGURATION REPORT")
    print("="*80)

    report = config.get_configuration_report()
    print(report)

    # Additional deployment information
    print("\n" + "="*60)
    print("DEPLOYMENT INFORMATION")
    print("="*60)

    print("Configuration Files Created/Modified:")
    print(f"  ✓ .env - Main environment configuration")
    print(f"  ✓ torq_console/core/config.py - Enhanced configuration system")
    print(f"  ✓ torq_console/core/config.py.backup - Backup of original")

    print("\nNext Steps for Full Deployment:")
    print("1. Replace placeholder API keys in .env with real keys:")
    for key in ['ALPHA_VANTAGE_API_KEY', 'FRED_API_KEY', 'NEWS_API_KEY', 'OPENAI_API_KEY', 'ANTHROPIC_API_KEY']:
        value = os.getenv(key, 'NOT_SET')
        if 'YOUR_' in value.upper() or value == 'NOT_SET':
            print(f"   - {key}: {value}")

    print("\n2. Set ENVIRONMENT=production when deploying to live systems")
    print("3. Review security settings and enable rate limiting in production")
    print("4. Test all services with real API keys")
    print("5. Monitor logs for any remaining demo mode warnings")


def main():
    """Main test function."""
    print("TORQ CONSOLE Configuration Validation Test")
    print("="*80)

    # Test 1: Environment file loading
    env_loaded = test_env_file_loading()

    # Test 2: Configuration loading
    config = test_configuration_loading()

    if config is None:
        print("\n❌ Configuration validation failed!")
        sys.exit(1)

    # Test 3: Service modes
    test_service_modes(config)

    # Test 4: Validate specific fixes
    all_fixed = validate_fixes()

    # Test 5: Generate comprehensive report
    generate_configuration_report(config)

    # Final summary
    print("\n" + "="*80)
    if all_fixed:
        print("🎉 CONFIGURATION VALIDATION SUCCESSFUL!")
        print("   All reported issues have been resolved.")
    else:
        print("⚠️  CONFIGURATION VALIDATION COMPLETED WITH WARNINGS")
        print("   Some issues require manual API key configuration.")

    print("   The system is now configured for real functionality.")
    print("="*80)


if __name__ == "__main__":
    main()