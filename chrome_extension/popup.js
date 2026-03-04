/**
 * TORQ Chrome Bridge - Popup Script
 *
 * Handles user approval/denial of browser sessions.
 */

const NATIVE_HOST_NAME = "com.torq.chrome_bridge";
const LOG_PREFIX = "[TORQ Popup]";

// DOM elements
const statusEl = document.getElementById("status");
const sessionInput = document.getElementById("session");
const approveBtn = document.getElementById("approve");
const denyBtn = document.getElementById("deny");
const responseEl = document.getElementById("response");

// Native messaging port
let port = null;

/**
 * Initialize connection to native host.
 */
function initPort() {
  try {
    port = chrome.runtime.connectNative(NATIVE_HOST_NAME);
    updateStatus(true);

    port.onDisconnect.addListener(() => {
      updateStatus(false);
      port = null;
    });

  } catch (err) {
    console.error(`${LOG_PREFIX} Failed to connect:`, err);
    updateStatus(false);
  }
}

/**
 * Update connection status display.
 */
function updateStatus(connected) {
  if (connected) {
    statusEl.textContent = "Connected to TORQ Bridge";
    statusEl.className = "status connected";
  } else {
    statusEl.textContent = "Disconnected - Start bridge host";
    statusEl.className = "status disconnected";
  }
}

/**
 * Show response message.
 */
function showResponse(success, message) {
  responseEl.textContent = message;
  responseEl.className = `response ${success ? "success" : "error"}`;

  // Auto-hide after 3 seconds
  setTimeout(() => {
    responseEl.className = "response";
    responseEl.textContent = "";
  }, 3000);
}

/**
 * Send approval/deny message to native host.
 */
function sendAction(type) {
  const sessionId = sessionInput.value.trim();

  if (!sessionId) {
    showResponse(false, "Enter a Session ID first");
    return;
  }

  if (!port) {
    initPort();
    if (!port) {
      showResponse(false, "Bridge not connected");
      return;
    }
  }

  const requestId = crypto.randomUUID();
  port.postMessage({
    type,
    request_id: requestId,
    session_id: sessionId
  });

  showResponse(true, `${type === "approve" ? "Approved" : "Denied"} session ${sessionId.slice(0, 8)}...`);
  sessionInput.value = "";
}

// Event listeners
approveBtn.addEventListener("click", () => sendAction("approve"));
denyBtn.addEventListener("click", () => sendAction("deny"));

// Allow Enter key to approve
sessionInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter") {
    sendAction("approve");
  }
});

// Initialize on load
initPort();

// Auto-refresh connection status every 2 seconds
setInterval(() => {
  if (!port || port.disconnected) {
    initPort();
  }
}, 2000);
