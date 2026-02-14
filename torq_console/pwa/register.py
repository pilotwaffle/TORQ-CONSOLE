"""
Service Worker Registration for TORQ Console

Registers service worker and provides PWA utilities.
"""

import logging
from typing import Optional


def register_service_worker(
    script_path: str = "/static/service-worker.js",
    scope: str = "/"
) -> str:
    """
    Generate service worker registration code.

    Args:
        script_path: Path to service worker script
        scope: Scope for service worker

    Returns:
        JavaScript code to register service worker
    """
    registration_code = f'''
// Register Service Worker
if ('serviceWorker' in navigator) {{
    navigator.serviceWorker.register('{script_path}', {{ scope: '{scope}' }})
        .then((registration) => {{
            console.log('Service Worker registered:', registration.scope);

            // Listen for controlling changes
            if (registration.active) {{
                registration.active.postMessage({{{
                    type: 'SKIP_WAITING'
                }}});

                // Force update if new version available
                registration.addEventListener('updatefound', () => {{
                    console.log('New Service Worker available');
                }});

                // Handle update
                registration.addEventListener('controllerchange', () => {{
                    console.log('Service Worker controller changed');
                }});
            }}

            // Check for updates
            registration.addEventListener('updatefound', () => {{
                const newWorker = registration.installing;
                if (newWorker) {{
                    console.log('Installing new Service Worker...');
                }}
            }});

            registration.addEventListener('updated', () => {{
                console.log('Service Worker updated');
                // Optionally notify user
            }});

        }})
        .catch((error) => {{
            console.error('Service Worker registration failed:', error);
        }});
}} else {{
    console.warn('Service Workers not supported in this browser');
}}
'''

    return registration_code


def get_pwa_integration_code(
    register_button: bool = True,
    update_notification: bool = True
) -> str:
    """
    Get PWA integration code for the web UI.

    Args:
        register_button: Whether to add install button
        update_notification: Whether to show update notifications

    Returns:
        JavaScript code for PWA integration
    """
    code = """
// TORQ Console PWA Integration
"""

    if register_button:
        code += """
// Add to home screen
let deferredPrompt;
const installButton = document.createElement('button');
installButton.textContent = 'Install App';
installButton.style.cssText = `
    position: fixed;
    bottom: 20px;
    right: 20px;
    padding: 12px 24px;
    background: #1e3c72;
    color: white;
    border: none;
    border-radius: 8px;
    cursor: pointer;
    font-size: 14px;
    font-weight: 500;
`;

window.addEventListener('beforeinstallprompt', (e) => {
    e.preventDefault();
    deferredPrompt = e;
    installButton.style.display = 'block';
    document.body.appendChild(installButton);
});

installButton.addEventListener('click', async () => {
    if (deferredPrompt) {
        deferredPrompt.prompt();
        const { outcome } = await deferredPrompt.userChoice;
        if (outcome === 'accepted') {
            console.log('App installed');
        }
        deferredPrompt = null;
        installButton.style.display = 'none';
    }
});
"""

    if update_notification:
        code += """
// Show update notification
if ('serviceWorker' in navigator) {
    navigator.serviceWorker.addEventListener('controllerchange', () => {
        const notification = document.createElement('div');
        notification.textContent = 'New version available! Refresh to update.';
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            left: 50%;
            transform: translateX(-50%);
            padding: 16px 24px;
            background: #10b981;
            color: white;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.2);
            z-index: 10000;
            cursor: pointer;
        `;
        notification.onclick = () => {
            window.location.reload();
        };
        document.body.appendChild(notification);

        // Auto-hide after 10 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 10000);
    });
}
"""

    return code


def generate_pwa_files(output_dir: str = "torq_console/ui/static") -> Dict[str, bool]:
    """
    Generate all PWA files.

    Args:
        output_dir: Directory to save files

    Returns:
        Dictionary with file paths and success status
    """
    results = {}

    # Generate manifest
    from .manifest import save_manifest
    results["manifest"] = save_manifest(f"{output_dir}/manifest.json")

    # Generate service worker
    from .service_worker import save_service_worker
    results["service_worker"] = save_service_worker(f"{output_dir}/service-worker.js")

    return results
