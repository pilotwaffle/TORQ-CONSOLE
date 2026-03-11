const { chromium } = require('playwright');

(async () => {
  console.log('=== TORQ Console Chat Verification ===');
  const browser = await chromium.launch({
    headless: false,
    slowMo: 200
  });

  const page = await browser.newPage();

  await page.goto('http://localhost:3016/', { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(3000);

  // Skip onboarding
  try {
    const skipBtn = await page.$('button:has-text("Skip")');
    if (skipBtn) await skipBtn.click();
    await page.waitForTimeout(1500);
  } catch (e) {}

  // Click Prince Flowers
  try {
    const prince = await page.$('text=Prince Flowers');
    if (prince) await prince.click();
    await page.waitForTimeout(1000);
  } catch (e) {}

  // Send a message
  const input = await page.$('textarea, input[type="text"]');
  if (input) {
    await input.click();
    await input.fill('What is Bitcoin price?');
    await page.waitForTimeout(500);

    // Send
    try {
      const sendBtn = await page.$('button[type="submit"]');
      if (sendBtn) await sendBtn.click();
      else await input.press('Enter');
    } catch (e) {
      await input.press('Enter');
    }

    console.log('Message sent, waiting for response...');
    await page.waitForTimeout(5000);

    // Extract messages from DOM
    const messageCount = await page.evaluate(() => {
      // Find all message elements
      const messages = document.querySelectorAll('[class*="message"], [class*="ChatMessage"]');
      return {
        count: messages.length,
        messages: Array.from(messages).map(m => ({
          text: m.textContent?.trim().substring(0, 100),
          class: m.className
        }))
      };
    });

    console.log('=== CHAT VERIFICATION ===');
    console.log(`Total messages found: ${messageCount.count}`);
    messageCount.messages.forEach((m, i) => {
      console.log(`Message ${i + 1}: [${m.class}] ${m.text}`);
    });

    // Check specifically for assistant response
    const hasAssistantResponse = await page.evaluate(() => {
      const body = document.body.innerText;
      return body.includes('standalone mode') || body.includes('Marvin') || body.includes('TORQ Console is running');
    });

    console.log(`\n✅ Assistant response displayed: ${hasAssistantResponse ? 'YES' : 'NO'}`);

    await page.screenshot({ path: 'E:/TORQ-CONSOLE/final_verification.png', fullPage: true });
    console.log('\nScreenshot saved: final_verification.png');
  }

  await page.waitForTimeout(3000);
  await browser.close();
  console.log('\n=== VERIFICATION COMPLETE ===');
})();
