// TORQ Console Service Worker
const CACHE_NAME = 'torq-console-v2';
const OFFLINE_FALLBACK = '/offline';
const API_CACHE_PREFIX = '/api/';

// URLs to cache on install
const CACHE_URLS = [
    '/',
    '/dashboard',
    '/static/css/main.css',
    '/static/js/main.js',
    '/manifest.json'
];

// Install event - cache initial URLs
self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => {
            return cache.addAll(CACHE_URLS);
        })
    );
    console.log('[Service Worker] Installed and cached initial URLs');
});

// Fetch event - serve from cache, fallback to network
self.addEventListener('fetch', (event) => {
    const { request } = event;
    const url = new URL(request.url);

    // Skip for non-GET requests and WebSocket
    if (request.method !== 'GET' || url.protocol === 'ws:' || url.protocol === 'wss:') {
        return;
    }

    event.respondWith(
        caches.open(CACHE_NAME).then((cache) => {
            return cache.match(request).then((response) => {
                if (response) {
                    // Found in cache - check if still valid
                    if (isCacheValid(response)) {
                        return response;
                    }
                }

                // Not in cache or stale - fetch from network
                return fetch(request).then((response) => {
                    // Cache successful GET responses
                    if (response.ok && url.pathname.startsWith(API_CACHE_PREFIX)) {
                        cache.put(request, response.clone());
                    }
                    // Cache static assets
                    if (response.ok && url.pathname.startsWith('/static/')) {
                        cache.put(request, response.clone());
                    }
                    return response;
                }).catch((error) => {
                    // Network failed - check for offline page
                    return cache.match(OFFLINE_FALLBACK).catch(() => {
                        // Generate offline response
                        return new Response('Offline - TORQ Console requires internet connection', {
                            status: 503,
                            statusText: 'Service Unavailable'
                        });
                    });
                });
            });
        }).catch((error) => {
            console.error('[Service Worker] Cache error:', error);
            return fetch(request);
        })
    );
});

// Activate event - immediately claim clients
self.addEventListener('activate', (event) => {
    event.waitUntil(clients.claim());
    console.log('[Service Worker] Activated');
});

// Message event - handle messages from clients
self.addEventListener('message', (event) => {
    if (event.data && event.data.type === 'SKIP_WAITING') {
        self.skipWaiting();
    }
    if (event.data && event.data.type === 'CLEAR_CACHE') {
        event.waitUntil(
            caches.delete(CACHE_NAME).then(() => {
                console.log('[Service Worker] Cache cleared');
                event.ports[0].postMessage({ type: 'CACHE_CLEARED' });
            })
        );
    }
});

// Helper: Check if cached response is still valid
function isCacheValid(response) {
    if (!response.headers) {
        return false;
    }
    const cacheControl = response.headers.get('cache-control');
    const expires = response.headers.get('expires');
    const date = response.headers.get('date');

    // If has max-age, consider it valid
    if (cacheControl && cacheControl.includes('max-age')) {
        return true;
    }

    // Otherwise check if expired
    if (expires && date) {
        const expiryDate = new Date(expires);
        const cacheDate = new Date(date);
        return expiryDate > new Date();
    }

    // Default: valid for 1 hour
    return true;
}

// IndexedDB for offline storage
const DB_NAME = 'torq-console-offline';
const DB_VERSION = 1;
const STORE_NAME = 'queue';

let db = null;

// Open IndexedDB
const openDB = () => {
    return new Promise((resolve, reject) => {
        const request = indexedDB.open(DB_NAME, DB_VERSION);

        request.onerror = () => reject(request.error);
        request.onsuccess = () => {
            db = request.result;
            resolve(db);
        };

        request.onupgradeneeded = (event) => {
            const database = event.target.result;
            if (!database.objectStoreNames().contains(STORE_NAME)) {
                database.createObjectStore(STORE_NAME, { keyPath: 'id', autoIncrement: true });
            }
        };
    });
};

// Store request for offline sync
const storeRequest = async (request) => {
    if (!db) {
        await openDB();
    }

    const transaction = db.transaction([STORE_NAME], 'readwrite');
    const store = transaction.objectStore(STORE_NAME);

    const item = {
        url: request.url,
        method: request.method,
        headers: Array.from(request.headers.entries()),
        body: request.body,
        timestamp: Date.now()
    };

    store.add(item);
    console.log('[Service Worker] Request stored for offline sync');
};

// Sync stored requests when back online
self.addEventListener('sync', (event) => {
    if (event.tag === 'background-sync') {
        syncOfflineRequests();
    }
});

const syncOfflineRequests = async () => {
    if (!db) {
        await openDB();
    }

    const transaction = db.transaction([STORE_NAME], 'readwrite');
    const store = transaction.objectStore(STORE_NAME);
    const request = store.getAll();

    request.onsuccess = async () => {
        const items = request.result;
        console.log(`[Service Worker] Syncing ${items.length} offline requests`);

        for (const item of items) {
            try {
                const response = await fetch(item.url, {
                    method: item.method,
                    headers: item.headers,
                    body: item.body
                });

                if (response.ok) {
                    // Remove successfully synced request
                    const deleteTx = db.transaction([STORE_NAME], 'readwrite');
                    deleteTx.objectStore(STORE_NAME).delete(item.id);
                }
            } catch (error) {
                console.error('[Service Worker] Failed to sync:', error);
            }
        }
    };
};
