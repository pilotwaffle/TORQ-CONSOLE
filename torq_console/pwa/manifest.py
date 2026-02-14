"""
PWA Manifest Generator for TORQ Console

Generates web app manifest for installation and mobile support.
"""

import json
import logging
from typing import Dict, Any, Optional


def generate_manifest(
    name: str = "TORQ Console",
    short_name: str = "TORQ",
    description: str = "AI-Powered Development Environment",
    start_url: str = "/",
    display: str = "standalone",
    orientation: str = "any",
    theme_color: str = "#1e3c72",
    background_color: str = "#0f172a",
    icons: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Generate PWA manifest.

    Args:
        name: Full application name
        short_name: Short name for home screen
        description: Application description
        start_url: URL to start the app
        display: Display mode (fullscreen, standalone, minimal-ui, browser)
        orientation: Default orientation (any, landscape, portrait)
        theme_color: Theme color for UI
        background_color: Background color for splash screen
        icons: Dictionary of icon sizes to paths

    Returns:
        Manifest dictionary
    """
    manifest = {
        "name": name,
        "short_name": short_name,
        "description": description,
        "start_url": start_url,
        "display": display,
        "orientation": orientation,
        "theme_color": theme_color,
        "background_color": background_color,
        "scope": "/",
        "prefer_related_applications": [],
    }

    # Default icons (can be overridden)
    if not icons:
        icons = {
            "192": "/static/icons/icon-192x192.png",
            "512": "/static/icons/icon-512x512.png"
        }
        manifest["icons"] = [
            {
                "src": icons["192"],
                "sizes": "192x192",
                "type": "image/png",
                "purpose": "any maskable"
            },
            {
                "src": icons["512"],
                "sizes": "512x512",
                "type": "image/png",
                "purpose": "any maskable"
            }
        ]

    return manifest


def get_manifest_json(config: Optional[Dict[str, Any]] = None) -> str:
    """
    Get manifest as JSON string.

    Args:
        config: Optional configuration dict

    Returns:
        JSON string of manifest
    """
    if config:
        manifest = generate_manifest(
            name=config.get("app_name", "TORQ Console"),
            short_name=config.get("app_short_name", "TORQ"),
            description=config.get("app_description", "AI-Powered Development Environment"),
            theme_color=config.get("theme_color", "#1e3c72")
        )
    else:
        manifest = generate_manifest()

    return json.dumps(manifest, indent=2)


def save_manifest(filepath: str = "torq_console/ui/static/manifest.json") -> bool:
    """
    Save manifest to file.

    Args:
        filepath: Where to save the manifest

    Returns:
        True if saved successfully
    """
    try:
        manifest = generate_manifest()

        with open(filepath, 'w') as f:
            f.write(manifest)

        logging.info(f"Saved PWA manifest to {filepath}")
        return True

    except Exception as e:
        logging.error(f"Failed to save manifest: {e}")
        return False
