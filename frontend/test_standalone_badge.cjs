const { chromium } = require('playwright');

(async () => {
  console.log('=== Testing Standalone Mode Badge ===');
  const browser = await chromium.launch({
    headless: false,
    slowMo: 300
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

  // Check for standalone mode badge
  const hasBadge = await page.evaluate(() => {
    const body = document.body.innerText;
    return body.includes('Standalone Mode') || body.includes('AI Runtime Unavailable');
  });

  console.log(`✅ Standalone mode badge visible: ${hasBadge ? 'YES' : 'NO'}`);

  // Take screenshot
  await page.screenshot({ path: 'E:/TORQ-CONSOLE/standalone_mode_badge.png', fullPage: true });
  console.log('Screenshot saved: standalone_mode_badge.png');

  await page.waitForTimeout(3000);
  await browser.close();
  console.log('=== TEST COMPLETE ===');
})();
