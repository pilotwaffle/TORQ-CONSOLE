#!/usr/bin/env python3
"""
Simple Configuration Status Check

A lightweight script to verify the configuration fixes without
requiring complex imports or dependencies.
"""

import os
from pathlib import Path

def check_env_file():
    """Check if .env file exists and has proper configuration."""
    env_file = Path(".env")
    print("=" * 50)
    print("CHECKING .ENV FILE")
    print("=" * 50)

    if not env_file.exists():
        print("❌ .env file not found!")
        return False

    print(f"✅ .env file found at: {env_file.absolute()}")

    # Read and analyze .env file
    with open(env_file, 'r') as f:
        content = f.read()

    # Check for key configurations
    checks = {
        'TBS_FALLBACK_MODE=disabled': 'Demo mode disabled',
        'TBS_DEMO_DATA_SOURCE=disabled': 'Demo data source disabled',
        'TBS_WEB_SEARCH_PROXY=enabled': 'Web search proxy enabled',
        'ALPHA_VANTAGE_API_KEY=': 'Alpha Vantage key configured',
        'FRED_API_KEY=': 'FRED key configured',
        'NEWS_API_KEY=': 'News API key configured'
    }

    print("\n📋 Configuration Status:")
    for check, description in checks.items():
        if check in content:
            print(f"  ✅ {description}")
        else:
            print(f"  ❌ {description} - NOT FOUND")

    return True


def check_environment_variables():
    """Check environment variables after .env loading."""
    print("\n" + "=" * 50)
    print("CHECKING ENVIRONMENT VARIABLES")
    print("=" * 50)

    # Key environment variables to check
    env_vars = {
        'TBS_FALLBACK_MODE': 'TBS Fallback Mode',
        'TBS_DEMO_DATA_SOURCE': 'TBS Demo Data Source',
        'TBS_WEB_SEARCH_PROXY': 'TBS Web Search Proxy',
        'ALPHA_VANTAGE_API_KEY': 'Alpha Vantage API Key',
        'FRED_API_KEY': 'FRED API Key',
        'NEWS_API_KEY': 'News API Key',
        'OPENAI_API_KEY': 'OpenAI API Key',
        'ANTHROPIC_API_KEY': 'Anthropic API Key'
    }

    print("\n🔍 Environment Variable Status:")

    for var, description in env_vars.items():
        value = os.getenv(var)
        if value:
            # Mask API keys for security
            if 'API_KEY' in var:
                if value.upper().startswith('YOUR_'):
                    display_value = "⚠️  PLACEHOLDER (needs real key)"
                    status = "🟡"
                else:
                    display_value = f"{value[:8]}***"
                    status = "✅"
            else:
                display_value = value
                status = "✅" if value.lower() == 'disabled' and 'FALLBACK' in var or 'DEMO' in var else "✅"

            print(f"  {status} {description}: {display_value}")
        else:
            print(f"  ❌ {description}: NOT SET")


def check_demo_mode_status():
    """Check if demo mode is properly disabled."""
    print("\n" + "=" * 50)
    print("DEMO MODE STATUS CHECK")
    print("=" * 50)

    fallback_mode = os.getenv('TBS_FALLBACK_MODE', '').lower()
    demo_source = os.getenv('TBS_DEMO_DATA_SOURCE', '').lower()

    is_demo_disabled = (
        fallback_mode in ['disabled', 'false', '0'] and
        demo_source in ['disabled', 'false', '0']
    )

    if is_demo_disabled:
        print("✅ DEMO MODE DISABLED - Real functionality enabled")
        print(f"  • TBS_FALLBACK_MODE: {fallback_mode}")
        print(f"  • TBS_DEMO_DATA_SOURCE: {demo_source}")
    else:
        print("⚠️  DEMO MODE STILL ACTIVE")
        print(f"  • TBS_FALLBACK_MODE: {fallback_mode}")
        print(f"  • TBS_DEMO_DATA_SOURCE: {demo_source}")
        print("  → Set both to 'disabled' to enable real functionality")

    return is_demo_disabled


def check_service_readiness():
    """Check readiness of individual services."""
    print("\n" + "=" * 50)
    print("SERVICE READINESS CHECK")
    print("=" * 50)

    services = {
        'ALPHA_VANTAGE_API_KEY': 'Alpha Vantage (Financial Data)',
        'FRED_API_KEY': 'FRED (Economic Data)',
        'NEWS_API_KEY': 'News API',
        'OPENAI_API_KEY': 'OpenAI (AI Models)',
        'ANTHROPIC_API_KEY': 'Anthropic (Claude Models)'
    }

    web_proxy_enabled = os.getenv('TBS_WEB_SEARCH_PROXY', '').lower() in ['enabled', 'true', '1']

    print(f"\n🌐 Web Search Proxy: {'✅ ENABLED' if web_proxy_enabled else '❌ DISABLED'}")
    print("\n📊 Service Status:")

    ready_count = 0
    proxy_count = 0
    placeholder_count = 0

    for key, service in services.items():
        value = os.getenv(key)

        if not value:
            if key in ['ALPHA_VANTAGE_API_KEY', 'FRED_API_KEY', 'NEWS_API_KEY'] and web_proxy_enabled:
                print(f"  🟡 {service}: PROXY MODE (web search fallback)")
                proxy_count += 1
            else:
                print(f"  ❌ {service}: DISABLED (no API key)")
        elif value.upper().startswith('YOUR_'):
            print(f"  🟡 {service}: PLACEHOLDER (needs real API key)")
            placeholder_count += 1
            if key in ['ALPHA_VANTAGE_API_KEY', 'FRED_API_KEY', 'NEWS_API_KEY'] and web_proxy_enabled:
                print(f"     → Can use proxy mode until real key is provided")
        else:
            print(f"  ✅ {service}: READY (API key configured)")
            ready_count += 1

    print(f"\n📈 Summary:")
    print(f"  • Ready Services: {ready_count}")
    print(f"  • Proxy Mode Services: {proxy_count}")
    print(f"  • Needs Configuration: {placeholder_count}")

    return ready_count + proxy_count > 0


def provide_next_steps():
    """Provide next steps for full deployment."""
    print("\n" + "=" * 60)
    print("NEXT STEPS FOR FULL DEPLOYMENT")
    print("=" * 60)

    print("\n1. 🔑 Replace API Key Placeholders:")
    placeholder_keys = []

    for key in ['ALPHA_VANTAGE_API_KEY', 'FRED_API_KEY', 'NEWS_API_KEY', 'OPENAI_API_KEY', 'ANTHROPIC_API_KEY']:
        value = os.getenv(key, '')
        if value.upper().startswith('YOUR_'):
            placeholder_keys.append(key)

    if placeholder_keys:
        print("   Replace these placeholders in .env with real API keys:")
        for key in placeholder_keys:
            print(f"   - {key}")
        print("\n   📍 Get API keys from:")
        print("   • Alpha Vantage: https://www.alphavantage.co/support/#api-key")
        print("   • FRED: https://fred.stlouisfed.org/docs/api/api_key.html")
        print("   • News API: https://newsapi.org/register")
        print("   • OpenAI: https://platform.openai.com/api-keys")
        print("   • Anthropic: https://console.anthropic.com/")
    else:
        print("   ✅ All API keys are configured!")

    print("\n2. 🚀 Production Deployment:")
    print("   Set ENVIRONMENT=production in .env for live deployment")

    print("\n3. 🧪 Test Configuration:")
    print("   Run your TORQ CONSOLE and verify all services work correctly")

    print("\n4. 📊 Monitor Status:")
    print("   Check logs for any demo mode warnings or API key issues")


def main():
    """Main function to run all checks."""
    print("TORQ CONSOLE Configuration Status Check")
    print("=" * 60)
    print("Checking configuration fixes for demo mode and API keys...")

    # Load environment from .env file manually (simple approach)
    env_file = Path(".env")
    if env_file.exists():
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    if key not in os.environ:
                        os.environ[key] = value

    # Run all checks
    env_ok = check_env_file()
    check_environment_variables()
    demo_disabled = check_demo_mode_status()
    services_ready = check_service_readiness()

    # Final summary
    print("\n" + "=" * 60)
    print("FINAL SUMMARY")
    print("=" * 60)

    if env_ok and demo_disabled and services_ready:
        print("🎉 CONFIGURATION STATUS: READY")
        print("   ✅ .env file properly configured")
        print("   ✅ Demo mode disabled")
        print("   ✅ Services ready or have fallback options")
        print("   → System ready for real functionality!")
    elif env_ok and demo_disabled:
        print("⚠️  CONFIGURATION STATUS: PARTIALLY READY")
        print("   ✅ .env file properly configured")
        print("   ✅ Demo mode disabled")
        print("   🟡 Some services need API keys")
        print("   → Add real API keys for full functionality")
    else:
        print("❌ CONFIGURATION STATUS: NEEDS ATTENTION")
        print("   → Review the issues above and fix configuration")

    provide_next_steps()

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()