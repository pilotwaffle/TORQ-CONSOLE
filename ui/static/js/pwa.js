/**
 TORQ Console PWA Integration

Service worker registration and PWA features.
 */

// Register Service Worker
if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/static/service-worker.js', {
        scope: '/'
    })
    .then((registration) => {
        console.log('[PWA] Service Worker registered:', registration.scope);

        // Listen for controlling changes
        if (registration.active) {
            registration.active.postMessage({
                type: 'SKIP_WAITING'
            });

            // Force update if new version available
            registration.addEventListener('updatefound', () => {
                console.log('[PWA] New Service Worker available');
            });

            // Handle update
            registration.addEventListener('controllerchange', () => {
                console.log('[PWA] Service Worker controller changed');
            });
        }

        // Check for updates
        registration.addEventListener('updatefound', () => {
            const newWorker = registration.installing;
            if (newWorker) {
                console.log('[PWA] Installing new Service Worker...');
            }
        });

        registration.addEventListener('updated', () => {
            console.log('[PWA] Service Worker updated');
            // Notify user of update
            showUpdateNotification();
        });

    })
    .catch((error) => {
        console.error('[PWA] Service Worker registration failed:', error);
    });
} else {
    console.warn('[PWA] Service Workers not supported in this browser');
}

// Add to home screen
let deferredPrompt;
const installButton = document.createElement('button');
installButton.id = 'install-prompt';
installButton.textContent = 'Install TORQ';
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
    z-index: 10000;
`;

window.addEventListener('beforeinstallprompt', (e) => {
    e.preventDefault();
    deferredPrompt = e;
    document.body.appendChild(installButton);
});

installButton.addEventListener('click', async () => {
    if (deferredPrompt) {
        deferredPrompt.prompt();
        const { outcome } = await deferredPrompt.userChoice;
        if (outcome === 'accepted') {
            console.log('[PWA] App installed');
        }
        deferredPrompt = null;
        if (installButton.parentNode) {
            installButton.parentNode.removeChild(installButton);
        }
    }
});

// Show update notification
function showUpdateNotification() {
    const notification = document.createElement('div');
    notification.id = 'update-notification';
    notification.textContent = 'New version available! Click to refresh.';
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        left: 50%;
        transform: translateX(-50%);
        padding: 16px 24px;
        background: #10b981;
        color: white;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
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
}

// Listen for online/offline events
window.addEventListener('online', () => {
    console.log('[PWA] Connection restored');
    hideOfflineIndicator();
});

window.addEventListener('offline', () => {
    console.log('[PWA] Connection lost');
    showOfflineIndicator();
});

function showOfflineIndicator() {
    let indicator = document.getElementById('offline-indicator');
    if (!indicator) {
        indicator = document.createElement('div');
        indicator.id = 'offline-indicator';
        indicator.textContent = 'You are offline. Some features may be limited.';
        indicator.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            padding: 8px;
            background: #f59e0b;
            color: white;
            text-align: center;
            font-size: 14px;
            z-index: 10001;
        `;
        document.body.appendChild(indicator);
    }
}

function hideOfflineIndicator() {
    const indicator = document.getElementById('offline-indicator');
    if (indicator && indicator.parentNode) {
        indicator.parentNode.removeChild(indicator);
    }
}

// Check connection status
function updateConnectionStatus() {
    if (navigator.connection) {
        const connection = navigator.connection;
        console.log('[PWA] Connection:', connection.effectiveType, connection.downlink, connection.rtt);

        // Show warning for slow connections
        if (connection.saveData && connection.effectiveType === 'slow-2g') {
            console.warn('[PWA] Slow connection detected - Data Saver mode on');
        }
    }
}

// Listen for connection changes
if (navigator.connection) {
    navigator.connection.addEventListener('change', updateConnectionStatus);
    updateConnectionStatus();
}

// Log PWA capabilities
console.log('[PWA] Capabilities:', {
    serviceWorker: 'serviceWorker' in navigator,
    beforeInstallPrompt: 'beforeinstallprompt' in window,
    online: navigator.onLine !== undefined,
    connection: navigator.connection !== undefined,
    shareAPI: 'share' in navigator
});
