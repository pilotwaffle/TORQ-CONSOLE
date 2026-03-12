const { chromium } = require('playwright');

(async () => {
  console.log('Launching browser...');
  const browser = await chromium.launch({
    headless: false,
    slowMo: 1000
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

  console.log('Navigating to http://localhost:3016/');
  await page.goto('http://localhost:3016/', { waitUntil: 'domcontentloaded', timeout: 30000 });

  console.log('Waiting for app to load...');
  await page.waitForTimeout(5000);

  console.log('Taking screenshot...');
  await page.screenshot({
    path: 'E:/TORQ-CONSOLE/torq_screenshot.png',
    fullPage: true
  });
  console.log('Screenshot saved to E:/TORQ-CONSOLE/torq_screenshot.png');

  // Get page title
  const title = await page.title();
  console.log('Page title:', title);

  // Check for React errors in the page
  const hasReactError = await page.evaluate(() => {
    const body = document.body.innerText;
    return body.includes('Rendered fewer hooks') ||
           body.includes('hook') ||
           body.includes('Minified React error');
  });
  console.log('Has React error:', hasReactError);

  // Keep browser open for 30 seconds for manual testing
  console.log('Browser will stay open for 30 seconds...');
  await page.waitForTimeout(30000);

  await browser.close();
  console.log('Done!');
})();
