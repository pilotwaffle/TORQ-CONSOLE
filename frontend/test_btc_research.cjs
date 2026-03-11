const { chromium } = require('playwright');

(async () => {
  console.log('Launching browser for BTC price research...');
  const browser = await chromium.launch({
    headless: false,
    slowMo: 500
  });

  const context = await browser.newContext({
    viewport: { width: 1920, height: 1080 }
  });

  const page = await context.newPage();

  // Log console messages
  page.on('console', msg => {
    console.log(`[${msg.type()}] ${msg.text()}`);
  });

  // Log page errors
  page.on('pageerror', error => {
    console.error(`PAGE ERROR: ${error}`);
  });

  console.log('Navigating to TORQ Console at http://localhost:3016/');
  await page.goto('http://localhost:3016/', { waitUntil: 'domcontentloaded', timeout: 30000 });

  console.log('Waiting for app to load...');
  await page.waitForTimeout(3000);

  // Take initial screenshot
  await page.screenshot({
    path: 'E:/TORQ-CONSOLE/btc_research_1_initial.png',
    fullPage: true
  });
  console.log('Screenshot 1 saved: btc_research_1_initial.png');

  // Try to click on Prince Flowers agent or the chat area
  console.log('Looking for chat interface...');

  // Check if there's an input field we can use
  try {
    // Look for any input field (chat input)
    const chatInput = await page.$('input[placeholder*="message" i], input[placeholder*="chat" i], textarea[placeholder*="message" i], .chat-input, input[type="text"]');

    if (chatInput) {
      console.log('Found chat input, typing BTC research query...');
      await chatInput.click();
      await chatInput.fill('What is the current Bitcoin (BTC) price? Please search for the latest price and provide details.');

      await page.waitForTimeout(1000);

      // Look for a send button
      const sendButton = await page.$('button[aria-label*="send" i], button[aria-label*="Send" i], button:has-text("Send"), button:has-text("send"), .send-button');

      if (sendButton) {
        console.log('Clicking send button...');
        await sendButton.click();
      } else {
        // Try pressing Enter
        console.log('Send button not found, pressing Enter...');
        await chatInput.press('Enter');
      }

      // Wait for response
      console.log('Waiting for response...');
      await page.waitForTimeout(8000);

      // Take screenshot of response
      await page.screenshot({
        path: 'E:/TORQ-CONSOLE/btc_research_2_response.png',
        fullPage: true
      });
      console.log('Screenshot 2 saved: btc_research_2_response.png');
    } else {
      console.log('Chat input not found. Checking for agents...');

      // Try to click on an agent to start a chat
      const agentCard = await page.$('text=Prince Flowers, text=Agent, .agent-card, [data-agent-id]');
      if (agentCard) {
        console.log('Clicking on agent...');
        await agentCard.click();
        await page.waitForTimeout(2000);

        // Try again to find input
        const chatInput2 = await page.$('input, textarea');
        if (chatInput2) {
          await chatInput2.click();
          await chatInput2.fill('What is the current Bitcoin (BTC) price? Please search for the latest price and provide details.');
          await page.waitForTimeout(1000);
          await chatInput2.press('Enter');

          console.log('Waiting for response...');
          await page.waitForTimeout(8000);

          await page.screenshot({
            path: 'E:/TORQ-CONSOLE/btc_research_3_response.png',
            fullPage: true
          });
          console.log('Screenshot 3 saved: btc_research_3_response.png');
        }
      }
    }
  } catch (e) {
    console.error('Error during chat interaction:', e.message);
  }

  // Get page content to see what happened
  const pageText = await page.evaluate(() => {
    const body = document.body.innerText;
    return body.substring(0, 2000);
  });
  console.log('Page content preview:', pageText.substring(0, 500));

  // Keep browser open for 20 seconds for manual testing
  console.log('Browser will stay open for 20 seconds for manual testing...');
  await page.waitForTimeout(20000);

  await browser.close();
  console.log('Done! Check screenshots for results.');
})();
