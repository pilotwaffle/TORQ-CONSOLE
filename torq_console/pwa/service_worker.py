"""
Service Worker Generator for TORQ Console

Generates service worker for offline support and caching.
"""

import logging
from typing import Dict, Any, Optional


def generate_service_worker(
    cache_name: str = "torq-console-v1",
    cache_urls: Optional[list] = None,
    offline_fallback: str = "/offline"
) -> str:
    """
    Generate service worker code.

    Args:
        cache_name: Name for the cache
        cache_urls: List of URLs to cache
        offline_fallback: URL to show when offline

    Returns:
        Service worker JavaScript code
    """
    if cache_urls is None:
        cache_urls = [
            "/",
            "/static/css/main.css",
            "/static/js/main.js",
            "/dashboard"
        ]

    service_worker = f'''
// TORQ Console Service Worker
const CACHE_NAME = '{cache_name}';
const OFFLINE_FALLBACK = '{offline_fallback}';

// URLs to cache on install
const CACHE_URLS = {cache_urls};

// Install event - cache initial URLs
self.addEventListener('install', (event) => {{
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => {{
            return cache.addAll(CACHE_URLS);
        }})
    );
}});

// Fetch event - serve from cache, fallback to network
self.addEventListener('fetch', (event) => {{
    // Skip for non-GET requests
    if (event.request.method !== 'GET') {{
        return;
    }}

    event.respondWith(
        caches.open(CACHE_NAME).then((cache) => {{
            return cache.match(event.request).then((response) => {{
                if (response) {{
                    // Found in cache - return it
                    return response;
                }}

                // Not in cache - fetch from network
                return fetch(event.request).then((response) => {{
                    // Cache the new response for future
                    if (response.ok) {{
                        cache.put(event.request, response.clone());
                    }}
                    return response;
                }}).catch((error) => {{
                    // Network failed - check for offline page
                    return cache.match(OFFLINE_FALLBACK);
                }});
            }});
        }}).catch((error) => {{
            // Cache open failed - just fetch
            return fetch(event.request);
        }})
    );
}});

// Activate event - immediately claim clients
self.addEventListener('activate', (event) => {{
    event.waitUntil(clients.claim());
}});

// Message event - handle messages from clients
self.addEventListener('message', (event) => {{
    if (event.data && event.data.type === 'SKIP_WAITING') {{
        self.skipWaiting();
    }}
}});
'''

    return service_worker


def save_service_worker(
    filepath: str = "torq_console/ui/static/service-worker.js",
    config: Optional[Dict[str, Any]] = None
) -> bool:
    """
    Save service worker to file.

    Args:
        filepath: Where to save the service worker
        config: Optional configuration

    Returns:
        True if saved successfully
    """
    try:
        service_worker = generate_service_worker()

        with open(filepath, 'w') as f:
            f.write(service_worker)

        logging.info(f"Saved service worker to {filepath}")
        return True

    except Exception as e:
        logging.error(f"Failed to save service worker: {e}")
        return False
