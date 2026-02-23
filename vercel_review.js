const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ 
    headless: false,
    slowMo: 1000 
  });
  const context = await browser.newContext({
    viewport: { width: 1920, height: 1080 }
  });
  const page = await context.newPage();
  
  console.log('Navigating to Vercel deployments page...');
  await page.goto('https://vercel.com/pilotwaffles-projects/torq-console/deployments', { 
    waitUntil: 'domcontentloaded',
    timeout: 60000 
  });
  
  await page.waitForTimeout(5000);
  
  // Take screenshot
  await page.screenshot({ path: 'E:/vercel_deployments.png', fullPage: true });
  console.log('Screenshot saved to E:/vercel_deployments.png');
  
  // Get page info
  const title = await page.title();
  const url = page.url();
  
  console.log('\n=== PAGE INFO ===');
  console.log('Title:', title);
  console.log('URL:', url);
  
  // Get deployment list
  const deployments = await page.evaluate(() => {
    const rows = Array.from(document.querySelectorAll('tr, [role="row"], li, a[href*="/deployments/"]'));
    return rows.slice(0, 20).map(r => r.textContent.trim().replace(/\s+/g, ' ').substring(0, 200));
  });
  
  console.log('\n=== DEPLOYMENT INFO ===');
  deployments.forEach((d, i) => {
    if (d.length > 10) console.log(`${i + 1}:`, d);
  });
  
  // Check for status indicators
  const statuses = await page.evaluate(() => {
    const statusElements = document.querySelectorAll('[class*="status"], [data-status], circle, svg[class*="icon"]');
    return Array.from(statusElements).slice(0, 15).map(el => ({
      className: el.className,
      textContent: el.textContent?.trim(),
      ariaLabel: el.getAttribute('aria-label')
    }));
  });
  
  console.log('\n=== STATUS INDICATORS ===');
  statuses.forEach((s, i) => {
    if (s.textContent || s.ariaLabel) console.log(`${i + 1}:`, s);
  });
  
  await browser.close();
})();
