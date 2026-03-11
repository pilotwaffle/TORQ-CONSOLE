const { chromium } = require('playwright');

(async () => {
  console.log('Launching browser for BTC price research...');
  const browser = await chromium.launch({
    headless: false,
    slowMo: 500
  });

  const page = await browser.newPage();

  // Log console messages
  page.on('console', msg => {
    if (msg.type() === 'error') {
      console.error(`[ERROR] ${msg.text()}`);
    } else if (msg.type() === 'log') {
      console.log(`[LOG] ${msg.text()}`);
    }
  });

  console.log('Navigating to TORQ Console...');
  await page.goto('http://localhost:3016/', { waitUntil: 'domcontentloaded', timeout: 30000 });

  console.log('Waiting for app to load...');
  await page.waitForTimeout(3000);

  // Skip the onboarding tour if present
  console.log('Looking for onboarding tour to skip...');

  try {
    // Try multiple selectors for the skip button
    const skipButton = await page.$('button:has-text("Skip"), button:has-text("skip"), button:has-text("X"), [aria-label*="close" i]');

    if (skipButton) {
      console.log('Found skip button, clicking...');
      await skipButton.click();
      await page.waitForTimeout(2000);
    } else {
      // Try clicking "Continue" multiple times to get through the tour
      console.log('Skip button not found, trying to continue through tour...');
      for (let i = 0; i < 5; i++) {
        const continueButton = await page.$('button:has-text("Continue"), button:has-text("Get Started")');
        if (continueButton) {
          await continueButton.click();
          await page.waitForTimeout(1000);
        } else {
          break;
        }
      }
    }
  } catch (e) {
    console.log('Onboarding handling:', e.message);
  }

  await page.waitForTimeout(2000);

  // Take screenshot after skipping tour
  await page.screenshot({
    path: 'E:/TORQ-CONSOLE/btc_research_2_after_skip.png',
    fullPage: true
  });
  console.log('Screenshot saved: btc_research_2_after_skip.png');

  // Now try to click on Prince Flowers agent
  console.log('Looking for Prince Flowers agent...');

  try {
    // Try to click on Prince Flowers
    const princeFlowers = await page.$('text=Prince Flowers, [data-agent-id="prince_flowers"], .agent-card:has-text("Prince")');

    if (princeFlowers) {
      console.log('Clicking on Prince Flowers...');
      await princeFlowers.click();
      await page.waitForTimeout(2000);
    }

    // Look for chat input - try multiple selectors
    const chatInput = await page.$('textarea, input[type="text"], .chat-input, [contenteditable="true"], input[placeholder*="Type" i], input[placeholder*="Message" i]');

    if (chatInput) {
      console.log('Found chat input! Typing BTC research query...');

      // Clear and type the message
      await chatInput.click();
      await page.keyboard.press('Control+A');
      await chatInput.fill('');
      await chatInput.fill('What is the current Bitcoin (BTC) price? Please search for the latest price and market data.');

      await page.waitForTimeout(1500);

      // Try to find and click send button
      const sendButton = await page.$('button[aria-label*="send" i], button:has-text("Send"), button:has-text("➤"), button[type="submit"], .send-button');

      if (sendButton) {
        console.log('Clicking send button...');
        await sendButton.click();
      } else {
        // Try pressing Enter with possible modifier
        console.log('Trying to send with Enter key...');
        await page.keyboard.down('Control');
        await page.keyboard.press('Enter');
        await page.keyboard.up('Control');
      }

      // Wait for response
      console.log('Waiting for agent response...');
      await page.waitForTimeout(10000);

      // Take screenshot of response
      await page.screenshot({
        path: 'E:/TORQ-CONSOLE/btc_research_3_result.png',
        fullPage: true
      });
      console.log('Screenshot saved: btc_research_3_result.png');

      // Get chat messages
      const messages = await page.evaluate(() => {
        const messageElements = document.querySelectorAll('.message, [class*="message"], [class*="chat"]');
        return Array.from(messageElements).map(el => el.textContent?.trim()).filter(Boolean);
      });

      console.log('=== CHAT MESSAGES ===');
      messages.forEach((msg, i) => {
        console.log(`Message ${i + 1}: ${msg.substring(0, 300)}`);
      });

    } else {
      console.log('Chat input still not found!');

      // Debug: show what interactive elements exist
      const inputs = await page.evaluate(() => {
        return Array.from(document.querySelectorAll('input, textarea, button')).map(el => ({
          tag: el.tagName,
          type: el.type || '',
          placeholder: el.placeholder || '',
          className: el.className || '',
          textContent: el.textContent?.substring(0, 50) || ''
        }));
      });

      console.log('Available interactive elements:', JSON.stringify(inputs, null, 2));
    }
  } catch (e) {
    console.error('Error during chat:', e.message);
  }

  // Keep browser open for manual testing
  console.log('Browser will stay open for 30 seconds...');
  await page.waitForTimeout(30000);

  await browser.close();
  console.log('Done!');
})();
