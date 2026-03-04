/**
 * TORQ Chrome Bridge - Background Service Worker
 *
 * Handles Native Messaging with the host process and executes browser actions.
 *
 * Native Host Name: com.torq.chrome_bridge
 * Message Types:
 *   - execute: Host asks extension to execute actions
 *   - result: Extension returns action results
 *   - approve: User approves a session
 *   - deny: User denies a session
 *   - ping/pong: Heartbeat
 */

// Native messaging port (created on install/startup)
let port = null;
const NATIVE_HOST_NAME = "com.torq.chrome_bridge";

// Console log prefix
const LOG_PREFIX = "[TORQ Bridge]";

/**
 * Ensure native messaging port is connected.
 */
async function ensurePort() {
  if (port && !port.disconnected) {
    return port;
  }

  console.log(`${LOG_PREFIX} Connecting to native host: ${NATIVE_HOST_NAME}`);

  try {
    port = chrome.runtime.connectNative(NATIVE_HOST_NAME);

    port.onMessage.addListener(async (msg) => {
      await handleNativeMessage(msg);
    });

    port.onDisconnect.addListener(() => {
      console.error(`${LOG_PREFIX} Port disconnected:`, chrome.runtime.lastError?.message);
      port = null;
    });

    console.log(`${LOG_PREFIX} Connected to native host`);
    return port;

  } catch (err) {
    console.error(`${LOG_PREFIX} Failed to connect to native host:`, err);
    return null;
  }
}

/**
 * Handle incoming messages from native host.
 */
async function handleNativeMessage(msg) {
  if (!msg || !msg.type) {
    console.warn(`${LOG_PREFIX} Received message without type:`, msg);
    return;
  }

  console.log(`${LOG_PREFIX} Received:`, msg.type);

  switch (msg.type) {
    case "execute":
      await handleExecute(msg);
      break;

    case "ack":
      console.log(`${LOG_PREFIX} Acknowledged:`, msg.request_id);
      break;

    case "pong":
      console.log(`${LOG_PREFIX} Pong:`, msg.ts);
      break;

    case "error":
      console.error(`${LOG_PREFIX} Error from host:`, msg.message);
      break;

    default:
      console.warn(`${LOG_PREFIX} Unknown message type:`, msg.type);
  }
}

/**
 * Execute browser actions requested by host.
 */
async function handleExecute(msg) {
  const { request_id, session_id, actions, require_approval } = msg;

  console.log(`${LOG_PREFIX} Executing ${actions?.length || 0} actions for session ${session_id}`);

  const result = {
    type: "result",
    request_id,
    session_id,
    ok: true,
    results: [],
    artifacts: {},
    console: [],
    network: [],
    errors: []
  };

  try {
    // Get active tab
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (!tab?.id) {
      throw new Error("No active tab found");
    }

    // Execute each action
    for (const action of actions || []) {
      const actionResult = await executeAction(tab, action);
      result.results.push(actionResult);

      // Collect artifacts
      if (actionResult.artifact) {
        Object.assign(result.artifacts, actionResult.artifact);
      }

      // Small delay between actions for stability
      await sleep(100);
    }

    // Get console logs if possible
    result.console = await getConsoleLogs(tab);

  } catch (err) {
    result.ok = false;
    result.errors.push({
      message: err.message,
      stack: err.stack
    });
  }

  // Send result back to host
  sendMessage(result);
}

/**
 * Execute a single browser action.
 */
async function executeAction(tab, action) {
  const { op } = action;
  const result = { op, status: "ok" };

  try {
    switch (op) {
      case "navigate":
        await chrome.tabs.update(tab.id, { url: action.url });
        await sleep(1200); // Wait for page load
        result.url = action.url;
        break;

      case "wait":
        if (action.ms) {
          await sleep(action.ms);
          result.waited_ms = action.ms;
        } else if (action.selector) {
          await waitForSelector(tab, action.selector, action.timeout_ms || 5000);
          result.waited_for = action.selector;
        }
        break;

      case "click":
      case "type":
      case "extract":
        const execResult = await executeScript(tab, action);
        Object.assign(result, execResult);
        break;

      case "screenshot":
        const dataUrl = await chrome.tabs.captureVisibleTab(tab.windowId, { format: "png" });
        result.artifact = { screenshot_png_data_url: dataUrl };
        break;

      case "get_title":
        const titleResult = await executeScript(tab, {
          op: "extract",
          selector: "title",
          mode: "document_title"
        });
        result.title = titleResult.text || titleResult.value;
        break;

      case "get_url":
        result.url = tab.url;
        break;

      case "reload":
        await chrome.tabs.reload(tab.id);
        await sleep(1000);
        break;

      case "go_back":
        await chrome.tabs.goBack(tab.id);
        await sleep(500);
        break;

      case "go_forward":
        await chrome.tabs.goForward(tab.id);
        await sleep(500);
        break;

      default:
        result.status = "unsupported";
        result.error = `Unknown operation: ${op}`;
    }
  } catch (err) {
    result.status = "error";
    result.error = err.message;
  }

  return result;
}

/**
 * Execute script in tab context.
 */
async function executeScript(tab, action) {
  const { op, by = "css", selector } = action;

  return new Promise((resolve, reject) => {
    chrome.scripting.executeScript({
      target: { tabId: tab.id },
      func: domOperation,
      args: [action]
    }, (results) => {
      if (chrome.runtime.lastError) {
        reject(new Error(chrome.runtime.lastError.message));
        return;
      }
      resolve(results?.[0]?.result);
    });
  });
}

/**
 * DOM operation function (executed in page context).
 */
function domOperation(action) {
  const { op, by = "css", selector, text, mode } = action;

  // Helper: find element
  const findElement = (sel, method) => {
    if (method === "css") return document.querySelector(sel);
    if (method === "id") return document.getElementById(sel);
    if (method === "name") return document.getElementsByName(sel)[0];
    if (method === "xpath") {
      const result = document.evaluate(sel, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null);
      return result.singleNodeValue;
    }
    return document.querySelector(sel);
  };

  // Helper: find all elements
  const findAllElements = (sel, method) => {
    if (method === "css") return Array.from(document.querySelectorAll(sel));
    if (method === "xpath") {
      const result = document.evaluate(sel, document, XPathResult.ORDERED_NODE_SNAPSHOT_TYPE, null);
      return Array.from({ length: result.snapshotLength }, (_, i) => result.snapshotItem(i));
    }
    return Array.from(document.querySelectorAll(sel));
  };

  // Special case: document title
  if (selector === "title" && mode === "document_title") {
    return { ok: true, text: document.title, value: document.title };
  }

  const el = findElement(selector, by);
  if (!el) {
    return { ok: false, error: `Element not found: ${selector} (by=${by})` };
  }

  switch (op) {
    case "click":
      el.click();
      return { ok: true, clicked: true, tag: el.tagName };

    case "type":
    case "input":
      el.focus();
      el.value = text || "";
      el.dispatchEvent(new Event("input", { bubbles: true }));
      el.dispatchEvent(new Event("change", { bubbles: true }));
      return { ok: true, typed: true, value: text };

    case "extract":
      const extractMode = mode || "text";
      if (extractMode === "text") return { ok: true, text: el.innerText?.trim() || "" };
      if (extractMode === "html") return { ok: true, html: el.innerHTML };
      if (extractMode === "value") return { ok: true, value: el.value || "" };
      if (extractMode === "href") return { ok: true, href: el.href };
      if (extractMode === "src") return { ok: true, src: el.src };
      if (extractMode === "attr" && action.attr) return { ok: true, attr: action.attr, value: el.getAttribute(action.attr) };
      return { ok: true, text: el.innerText?.trim() || "" };

    case "exists":
      return { ok: true, exists: true, tag: el.tagName };

    case "is_visible":
      const rect = el.getBoundingClientRect();
      const isVisible = rect.width > 0 && rect.height > 0;
      return { ok: true, visible: isVisible };

    case "scroll_into_view":
      el.scrollIntoView({ behavior: "smooth", block: "center" });
      return { ok: true, scrolled: true };

    default:
      return { ok: false, error: `Unknown operation: ${op}` };
  }
}

/**
 * Wait for a selector to appear in the DOM.
 */
async function waitForSelector(tab, selector, timeoutMs) {
  const startTime = Date.now();

  return new Promise((resolve, reject) => {
    const check = () => {
      chrome.scripting.executeScript({
        target: { tabId: tab.id },
        func: (sel) => !!document.querySelector(sel),
        args: [selector]
      }, (results) => {
        const found = results?.[0]?.result;
        if (found) {
          resolve(true);
        } else if (Date.now() - startTime > timeoutMs) {
          reject(new Error(`Timeout waiting for selector: ${selector}`));
        } else {
          setTimeout(check, 200);
        }
      });
    };
    check();
  });
}

/**
 * Get console logs from tab (requires content script injection).
 */
async function getConsoleLogs(tab) {
  // v1: Return empty (would need console override content script)
  return [];
}

/**
 * Send message to native host.
 */
function sendMessage(msg) {
  if (port && !port.disconnected) {
    try {
      port.postMessage(msg);
    } catch (err) {
      console.error(`${LOG_PREFIX} Failed to send message:`, err);
    }
  }
}

/**
 * Sleep helper.
 */
function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

// =============================================================================
// Initialization
// =============================================================================

chrome.runtime.onInstalled.addListener(async () => {
  console.log(`${LOG_PREFIX} Extension installed`);
  await ensurePort();
});

chrome.runtime.onStartup.addListener(async () => {
  console.log(`${LOG_PREFIX} Browser startup`);
  await ensurePort();
});

// Initialize on load
ensurePort();

// Heartbeat: send ping every 30 seconds
setInterval(() => {
  sendMessage({
    type: "ping",
    request_id: crypto.randomUUID(),
    ts: Date.now()
  });
}, 30000);
