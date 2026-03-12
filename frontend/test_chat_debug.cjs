const { chromium } = require('playwright');

(async () => {
  console.log('=== Testing TORQ Console Chat Response ===');
  const browser = await chromium.launch({
    headless: false,
    slowMo: 300
  });

  const page = await browser.newPage();

  // Capture all console messages and errors
  page.on('console', msg => {
    const type = msg.type();
    const text = msg.text();
    if (type === 'error' || type === 'warning' || text.includes('post') || text.includes('response') || text.includes('chat')) {
      console.log(`[CONSOLE ${type.toUpperCase()}] ${text}`);
    }
  });

  page.on('pageerror', error => {
    console.error(`[PAGE ERROR] ${error.message}`);
  });

  // Intercept network requests
  page.on('response', async response => {
    const url = response.url();
    if (url.includes('/api/chat') || url.includes('/api/agents')) {
      const request = response.request();
      const method = request ? request.method() : 'GET';
      console.log(`[NETWORK] ${response.status()} ${method} ${url}`);
      if (url.includes('/api/chat')) {
        try {
          const body = await response.json();
          console.log(`[RESPONSE BODY]`, JSON.stringify(body, null, 2));
        } catch (e) {
          const text = await response.text();
          console.log(`[RESPONSE TEXT]`, text.substring(0, 500));
        }
      }
    }
  });

  await page.goto('http://localhost:3016/', { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(3000);

  // Skip onboarding
  try {
    const skipBtn = await page.$('button:has-text("Skip")');
    if (skipBtn) {
      await skipBtn.click();
      await page.waitForTimeout(1500);
    }
  } catch (e) {}

  // Click on Prince Flowers
  try {
    const prince = await page.$('text=Prince Flowers');
    if (prince) {
      await prince.click();
      await page.waitForTimeout(1000);
    }
  } catch (e) {}

  // Find and type in chat input
  const input = await page.$('textarea, input[type="text"]');
  if (input) {
    await input.click();
    await input.fill('Test message');
    await page.waitForTimeout(500);

    // Click send button or press Enter
    try {
      const sendBtn = await page.$('button[type="submit"], button:has-text("Send"), button:has-text("➤")');
      if (sendBtn) {
        await sendBtn.click();
      } else {
        await input.press('Enter');
      }
    } catch (e) {
      await input.press('Enter');
    }

    console.log('Message sent, waiting for response...');
    await page.waitForTimeout(5000);

    // Check chat messages in DOM
    const messages = await page.evaluate(() => {
      // Try multiple selectors for messages
      const selectors = [
        '.message',
        '[class*="message"]',
        '[class*="chat"]',
        '[role="log"]',
      ];

      for (const selector of selectors) {
        const elements = document.querySelectorAll(selector);
        if (elements.length > 0) {
          return Array.from(elements).map(el => ({
            selector,
            textContent: el.textContent?.trim().substring(0, 200),
            innerHTML: el.innerHTML.substring(0, 200)
          }));
        }
      }

      // Check entire body text
      return {
        bodyText: document.body.innerText.substring(0, 1000),
        allElements: Array.from(document.querySelectorAll('*')).filter(el => el.textContent?.includes('standalone') || el.textContent?.includes('Marvin')).map(el => el.tagName)
      };
    });

    console.log('=== DOM MESSAGES ===');
    console.log(JSON.stringify(messages, null, 2));

    // Take screenshot
    await page.screenshot({ path: 'E:/TORQ-CONSOLE/chat_debug.png', fullPage: true });
    console.log('Screenshot saved: chat_debug.png');
  }

  await page.waitForTimeout(5000);
  await browser.close();
  console.log('=== TEST COMPLETE ===');
})();
