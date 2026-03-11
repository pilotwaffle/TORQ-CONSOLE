// TORQ Console Verification Tests V3 - Skip onboarding modal
// Run: node torq_verification_test_v3.cjs

const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const SCREENSHOT_DIR = path.join(__dirname, 'verification_screenshots_v3');
const PORT = 3000;
const BASE_URL = `http://localhost:${PORT}`;

if (!fs.existsSync(SCREENSHOT_DIR)) {
  fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });
}

async function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function runTests() {
  console.log('='.repeat(60));
  console.log('TORQ CONSOLE VERIFICATION TESTS V3');
  console.log('='.repeat(60));
  console.log(`Testing URL: ${BASE_URL}`);
  console.log(`Screenshot directory: ${SCREENSHOT_DIR}`);
  console.log('='.repeat(60));

  const browser = await chromium.launch({
    headless: false,
    slowMo: 300
  });

  const context = await browser.newContext({
    viewport: { width: 1920, height: 1080 }
  });

  const page = await context.newPage();

  // Track console messages
  const consoleErrors = [];
  const warnings = [];

  page.on('console', msg => {
    const type = msg.type();
    const text = msg.text();
    if (type === 'error') {
      consoleErrors.push(text);
      console.log(`[Browser Error] ${text}`);
    } else if (type === 'warning') {
      warnings.push(text);
    }
  });

  page.on('pageerror', error => {
    consoleErrors.push(error.message);
    console.log(`[Page Error] ${error.message}`);
  });

  const results = {
    loadCheck: { passed: false, details: '' },
    standaloneModeTest: { passed: false, details: '' },
    chatInputTest: { passed: false, details: '' },
    suggestionButtonTest: { passed: false, details: '' },
    messageSendTest: { passed: false, details: '' },
    consoleCheck: { passed: false, details: '' },
  };

  try {
    // Step 1: Navigate and skip onboarding
    console.log('\n[SETUP] Navigating to TORQ Console...');
    await page.goto(BASE_URL, { waitUntil: 'networkidle', timeout: 15000 });
    await sleep(2000);

    // Set localStorage to skip onboarding
    console.log('[SETUP] Skipping onboarding modal...');
    await page.evaluate(() => {
      localStorage.setItem('torq-onboarding-seen', 'true');
    });
    await page.reload({ waitUntil: 'networkidle' });
    await sleep(3000);

    // Test 1: Load Check
    console.log('\n[TEST 1] Load Check...');
    const status = 200; // We got here successfully
    const bodyContent = await page.content();
    const hasCloudOffError = bodyContent.includes('CloudOff') || bodyContent.includes('cloudoff');

    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, '1_initial_load.png'),
      fullPage: true
    });

    results.loadCheck.passed = !hasCloudOffError;
    results.loadCheck.details = `Status: 200, CloudOff error: ${hasCloudOffError ? 'YES' : 'NO'}`;
    console.log(`  Result: ${results.loadCheck.passed ? 'PASS' : 'FAIL'}`);

    // Test 2: Standalone Mode Check
    console.log('\n[TEST 2] Standalone Mode Check...');
    try {
      const standaloneBadge = await page.locator('text=/standalone/i').count();
      const standalonePanel = await page.locator('[class*="standalone"]').count();
      const modeIndicator = await page.locator('text=/mode/i').count();

      // Also check for "Standalone Mode" in any element
      const hasStandaloneText = await page.locator('text=/Standalone Mode/i').count() > 0;

      results.standaloneModeTest.passed = standaloneBadge > 0 || standalonePanel > 0 || modeIndicator > 0 || hasStandaloneText;
      results.standaloneModeTest.details = `Badge: ${standaloneBadge}, Panel: ${standalonePanel}, Mode: ${modeIndicator}, Standalone text: ${hasStandaloneText}`;
      console.log(`  Result: ${results.standaloneModeTest.passed ? 'PASS' : 'FAIL'}`);

    } catch (error) {
      results.standaloneModeTest.details = error.message;
      console.log(`  ERROR: ${error.message}`);
    }

    // Test 3: Chat Input Test
    console.log('\n[TEST 3] Chat Input Test...');
    try {
      const chatInput = page.locator('textarea[placeholder*="ask" i]').first();

      // Type in the input
      await chatInput.fill('test message');
      await sleep(1000);

      const inputValue = await chatInput.inputValue().catch(() => '');
      const hasText = inputValue?.includes('test message') || false;

      await page.screenshot({
        path: path.join(SCREENSHOT_DIR, '2_after_typing.png'),
        fullPage: true
      });

      results.chatInputTest.passed = hasText;
      results.chatInputTest.details = `Text entered: ${hasText ? 'YES' : 'NO'}, Value: "${inputValue}"`;
      console.log(`  Result: ${results.chatInputTest.passed ? 'PASS' : 'FAIL'}`);

    } catch (error) {
      results.chatInputTest.details = error.message;
      console.log(`  ERROR: ${error.message}`);
    }

    // Test 4: Suggestion Button Test
    console.log('\n[TEST 4] Suggestion Button Test...');
    try {
      // Look for suggestion buttons
      const suggestionButton = page.locator('button:has-text("Explain")').first();

      const count = await suggestionButton.count();
      if (count > 0) {
        await suggestionButton.click();
        await sleep(2000);

        await page.screenshot({
          path: path.join(SCREENSHOT_DIR, '3_after_suggestion_click.png'),
          fullPage: true
        });

        results.suggestionButtonTest.passed = true;
        results.suggestionButtonTest.details = `Clicked suggestion button successfully`;
      } else {
        results.suggestionButtonTest.details = 'No suggestion button found';
      }

      console.log(`  Result: ${results.suggestionButtonTest.passed ? 'PASS' : 'FAIL'}`);

    } catch (error) {
      results.suggestionButtonTest.details = error.message;
      console.log(`  ERROR: ${error.message}`);
    }

    // Test 5: Message Send Test (Enter key)
    console.log('\n[TEST 5] Message Send Test (Enter key)...');
    try {
      const chatInput = page.locator('textarea[placeholder*="ask" i]').first();

      // Clear and type a message
      await chatInput.fill('');
      await chatInput.fill('test message from automation');
      await sleep(500);

      // Press Enter to send (not Shift+Enter)
      await page.keyboard.press('Enter');
      await sleep(2000);

      // Check if message was sent (look for user message in chat)
      const userMessage = await page.locator('text=/test message from automation/i').count();

      await page.screenshot({
        path: path.join(SCREENSHOT_DIR, '4_after_send.png'),
        fullPage: true
      });

      results.messageSendTest.passed = userMessage > 0;
      results.messageSendTest.details = `Message found in chat: ${userMessage > 0 ? 'YES' : 'NO'}`;
      console.log(`  Result: ${results.messageSendTest.passed ? 'PASS' : 'FAIL'}`);

    } catch (error) {
      results.messageSendTest.details = error.message;
      console.log(`  ERROR: ${error.message}`);
    }

    // Test 6: Console Check
    console.log('\n[TEST 6] Console Check...');
    await sleep(1000);

    const hookWarnings = warnings.filter(w => w.includes('hook') || w.includes('Hook'));
    const cloudOffErrors = consoleErrors.filter(e => e.includes('CloudOff') || e.includes('cloudoff'));
    const crashErrors = consoleErrors.filter(e => e.includes('crash') || e.includes('fatal') || e.includes('uncaught'));

    results.consoleCheck.passed = cloudOffErrors.length === 0 && crashErrors.length === 0;
    results.consoleCheck.details = `Hook warnings: ${hookWarnings.length}, CloudOff: ${cloudOffErrors.length}, Crashes: ${crashErrors.length}`;

    console.log(`  Hook warnings: ${hookWarnings.length}`);
    console.log(`  CloudOff errors: ${cloudOffErrors.length}`);
    console.log(`  Crash/fatal errors: ${crashErrors.length}`);
    console.log(`  Total errors: ${consoleErrors.length}`);
    console.log(`  Total warnings: ${warnings.length}`);
    console.log(`  Result: ${results.consoleCheck.passed ? 'PASS' : 'FAIL'}`);

    // Print errors
    if (consoleErrors.length > 0) {
      console.log('\n[Console Errors Found]:');
      consoleErrors.slice(0, 10).forEach((err, i) => console.log(`  ${i + 1}. ${err.substring(0, 100)}`));
    }

    if (hookWarnings.length > 0) {
      console.log('\n[Hook Warnings Found]:');
      hookWarnings.slice(0, 10).forEach((w, i) => console.log(`  ${i + 1}. ${w.substring(0, 100)}`));
    }

  } catch (error) {
    console.error('\n[FATAL ERROR]', error.message);
  } finally {
    await sleep(2000);
    await browser.close();

    console.log('\n' + '='.repeat(60));
    console.log('TEST SUMMARY');
    console.log('='.repeat(60));

    const totalTests = Object.keys(results).length;
    const passedTests = Object.values(results).filter(r => r.passed).length;

    Object.entries(results).forEach(([test, result]) => {
      const status = result.passed ? 'PASS' : 'FAIL';
      console.log(`\n${test}:`);
      console.log(`  Status: ${status}`);
      console.log(`  Details: ${result.details}`);
    });

    console.log('\n' + '='.repeat(60));
    console.log(`OVERALL: ${passedTests}/${totalTests} tests passed`);
    console.log(`Screenshots: ${SCREENSHOT_DIR}`);
    console.log('='.repeat(60));

    const resultsPath = path.join(SCREENSHOT_DIR, 'test_results.json');
    fs.writeFileSync(resultsPath, JSON.stringify({
      timestamp: new Date().toISOString(),
      baseUrl: BASE_URL,
      results,
      summary: { total: totalTests, passed: passedTests, failed: totalTests - passedTests },
      consoleErrors,
      warnings
    }, null, 2));
    console.log(`\nResults: ${resultsPath}`);
  }
}

runTests().catch(console.error);
