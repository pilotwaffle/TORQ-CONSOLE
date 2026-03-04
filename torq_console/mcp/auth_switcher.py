"""
Claude Code Authentication Switcher Module

Python module for switching between API key and Claude Pro subscription.
Can be imported and used programmatically.

Usage:
    from torq_console.mcp.auth_switcher import switch_auth, AuthMode

    # Switch to subscription
    switch_auth(AuthMode.SUBSCRIPTION)

    # Switch to API key
    switch_auth(AuthMode.API_KEY)

    # Get current mode
    mode = get_auth_mode()
    print(f"Current mode: {mode}")
"""
import enum
import json
import os
import shutil
from pathlib import Path
from typing import Optional


class AuthMode(enum.Enum):
    """Authentication modes."""
    API_KEY = "api"
    SUBSCRIPTION = "subscription"
    UNKNOWN = "unknown"


# Paths
CONFIG_DIR = Path.home() / ".claude"
SETTINGS_FILE = CONFIG_DIR / "settings.json"
API_SETTINGS_BACKUP = CONFIG_DIR / "settings.json.api_backup"
CREDENTIALS_BACKUP = CONFIG_DIR / ".credentials.json.api_backup"


def get_auth_mode() -> AuthMode:
    """
    Get the current authentication mode.

    Returns:
        AuthMode: Current authentication mode
    """
    if not SETTINGS_FILE.exists():
        return AuthMode.UNKNOWN

    try:
        with open(SETTINGS_FILE, 'r') as f:
            settings = json.load(f)

        # Check for subscription mode
        if settings.get('forceLoginMethod') == 'claudeai':
            return AuthMode.SUBSCRIPTION

        # Check for API key mode
        env = settings.get('env', {})
        if 'ANTHROPIC_AUTH_TOKEN' in env:
            return AuthMode.API_KEY

        return AuthMode.UNKNOWN

    except Exception:
        return AuthMode.UNKNOWN


def save_api_config() -> bool:
    """
    Save current API configuration for later restoration.

    Returns:
        True if successful, False otherwise
    """
    if not SETTINGS_FILE.exists():
        return False

    try:
        with open(SETTINGS_FILE, 'r') as f:
            settings = json.load(f)

        # Only save if it has API configuration
        if 'ANTHROPIC_AUTH_TOKEN' in settings.get('env', {}):
            shutil.copy2(SETTINGS_FILE, API_SETTINGS_BACKUP)

            # Also backup credentials
            credentials_file = CONFIG_DIR / ".credentials.json"
            if credentials_file.exists():
                shutil.copy2(credentials_file, CREDENTIALS_BACKUP)

            return True

        return False

    except Exception:
        return False


def restore_api_config() -> bool:
    """
    Restore previously saved API configuration.

    Returns:
        True if successful, False otherwise
    """
    if not API_SETTINGS_BACKUP.exists():
        return False

    try:
        # Restore settings
        shutil.copy2(API_SETTINGS_BACKUP, SETTINGS_FILE)

        # Restore credentials if available
        if CREDENTIALS_BACKUP.exists():
            credentials_file = CONFIG_DIR / ".credentials.json"
            shutil.copy2(CREDENTIALS_BACKUP, credentials_file)

        return True

    except Exception:
        return False


def switch_to_subscription() -> dict:
    """
    Switch to Claude Pro subscription authentication.

    Saves current API config before switching.

    Returns:
        Dict with success status and message
    """
    # Save current config first
    save_api_config()

    try:
        with open(SETTINGS_FILE, 'r') as f:
            settings = json.load(f)

        # Remove API-related env vars
        env = settings.get('env', {})
        api_keys_to_remove = [
            'ANTHROPIC_AUTH_TOKEN',
            'ANTHROPIC_BASE_URL',
            'ANTHROPIC_DEFAULT_OPUS_MODEL',
            'ANTHROPIC_DEFAULT_SONNET_MODEL',
            'ANTHROPIC_DEFAULT_GLM_MODEL',
            'ANTHROPIC_AVAILABLE_MODELS',
            'ANTHROPIC_DEFAULT_GLM_47_MODEL',
            'CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC'
        ]

        for key in api_keys_to_remove:
            env.pop(key, None)

        # Set subscription mode
        settings['forceLoginMethod'] = 'claudeai'
        settings['model'] = 'claude-opus-4-6'

        with open(SETTINGS_FILE, 'w') as f:
            json.dump(settings, f, indent=2)

        # Clear credentials to force login
        credentials_file = CONFIG_DIR / ".credentials.json"
        if credentials_file.exists():
            shutil.move(credentials_file, CREDENTIALS_BACKUP)

        return {
            "success": True,
            "mode": "subscription",
            "message": "Switched to Claude Pro Subscription. Restart Claude Code to login."
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to switch: {e}"
        }


def switch_to_api() -> dict:
    """
    Switch to API key authentication.

    Restores previously saved API configuration.

    Returns:
        Dict with success status and message
    """
    if not restore_api_config():
        # No saved config, try to set up minimal API mode
        try:
            with open(SETTINGS_FILE, 'r') as f:
                settings = json.load(f)

            # Remove subscription mode
            settings.pop('forceLoginMethod', None)

            with open(SETTINGS_FILE, 'w') as f:
                json.dump(settings, f, indent=2)

            return {
                "success": True,
                "mode": "api",
                "message": "Switched to API mode. Configure your API key with: claude auth"
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to switch: {e}"
            }

    return {
        "success": True,
        "mode": "api",
        "message": "Switched to API Key. Restart Claude Code."
    }


def switch_auth(mode: AuthMode) -> dict:
    """
    Switch authentication mode.

    Args:
        mode: AuthMode to switch to

    Returns:
        Dict with success status and message
    """
    current = get_auth_mode()

    if current == mode:
        return {
            "success": True,
            "mode": mode.value,
            "message": f"Already in {mode.value} mode"
        }

    if mode == AuthMode.SUBSCRIPTION:
        return switch_to_subscription()
    elif mode == AuthMode.API_KEY:
        return switch_to_api()
    else:
        return {
            "success": False,
            "error": f"Unknown mode: {mode}"
        }


def get_status() -> dict:
    """
    Get current authentication status.

    Returns:
        Dict with current mode and details
    """
    mode = get_auth_mode()

    status = {
        "mode": mode.value,
        "settings_file": str(SETTINGS_FILE),
        "settings_exist": SETTINGS_FILE.exists(),
        "api_backup_exists": API_SETTINGS_BACKUP.exists(),
        "credentials_backup_exists": CREDENTIALS_BACKUP.exists()
    }

    # Add API details if in API mode
    if mode == AuthMode.API_KEY:
        try:
            with open(SETTINGS_FILE, 'r') as f:
                settings = json.load(f)
            env = settings.get('env', {})
            if 'ANTHROPIC_BASE_URL' in env:
                status['api_endpoint'] = env['ANTHROPIC_BASE_URL']
        except Exception:
            pass

    return status


# CLI interface
if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        command = sys.argv[1].lower()

        if command in ("sub", "pro", "subscription", "claudeai"):
            result = switch_auth(AuthMode.SUBSCRIPTION)
            print(result.get("message", "Switch complete"))

        elif command in ("api", "key", "apikey"):
            result = switch_auth(AuthMode.API_KEY)
            print(result.get("message", "Switch complete"))

        elif command in ("status", "--status", "-s"):
            status = get_status()
            mode_str = status["mode"].upper()
            print(f"Current Mode: {mode_str}")

        else:
            print("Usage: python auth_switcher.py [sub|api|status]")
    else:
        status = get_status()
        mode_str = status["mode"].upper()
        print(f"Current Mode: {mode_str}")
        print()
        print("Usage: python auth_switcher.py [sub|api|status]")
