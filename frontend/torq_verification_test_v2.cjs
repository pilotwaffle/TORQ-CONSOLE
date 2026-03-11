// TORQ Console Verification Tests V2 - Handles modal
// Run: node torq_verification_test_v2.cjs

const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const SCREENSHOT_DIR = path.join(__dirname, 'verification_screenshots_v2');
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
  console.log('TORQ CONSOLE VERIFICATION TESTS V2');
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
    modalHandling: { passed: false, details: '' },
    chatInputTest: { passed: false, details: '' },
    suggestionButtonTest: { passed: false, details: '' },
    standaloneModeTest: { passed: false, details: '' },
    consoleCheck: { passed: false, details: '' },
  };

  try {
    // Test 1: Load Check
    console.log('\n[TEST 1] Load Check: Navigating to TORQ Console...');
    const response = await page.goto(BASE_URL, {
      waitUntil: 'networkidle',
      timeout: 15000
    });

    const status = response?.status() || 'unknown';
    await sleep(3000);

    const bodyContent = await page.content();
    const hasCloudOffError = bodyContent.includes('CloudOff') || bodyContent.includes('cloudoff');

    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, '1_initial_load.png'),
      fullPage: true
    });

    results.loadCheck.passed = status === 200;
    results.loadCheck.details = `Status: ${status}, CloudOff error: ${hasCloudOffError ? 'YES' : 'NO'}`;
    console.log(`  Result: ${results.loadCheck.passed ? 'PASS' : 'FAIL'}`);

    // Test 2: Handle Modal
    console.log('\n[TEST 2] Modal Handling...');
    try {
      // Look for common modal close buttons
      const modalCloseSelectors = [
        'button[aria-label="Close"]',
        'button[aria-label="close"]',
        'button:has-text("Close")',
        'button:has-text("close")',
        'button:has-text("×")',
        'button:has-text("X")',
        '[class*="close"]',
        '[class*="dismiss"]',
        'button[class*="modal"][class*="close"]',
      ];

      let modalClosed = false;
      for (const selector of modalCloseSelectors) {
        try {
          const count = await page.locator(selector).count();
          if (count > 0) {
            console.log(`  Found close button: ${selector}`);
            await page.locator(selector).first().click({ timeout: 2000 });
            await sleep(1000);
            modalClosed = true;
            break;
          }
        } catch (e) {
          // Continue
        }
      }

      // Try pressing Escape key
      if (!modalClosed) {
        console.log(`  Trying Escape key to close modal...`);
        await page.keyboard.press('Escape');
        await sleep(1000);
      }

      // Check if modal is still there
      const modalStillPresent = await page.locator('.fixed.inset-0.z-50').count() > 0;
      modalClosed = !modalStillPresent;

      results.modalHandling.passed = modalClosed;
      results.modalHandling.details = `Modal closed: ${modalClosed ? 'YES' : 'NO'}`;
      console.log(`  Result: ${results.modalHandling.passed ? 'PASS' : 'FAIL'}`);

    } catch (error) {
      results.modalHandling.details = error.message;
      console.log(`  ERROR: ${error.message}`);
    }

    await sleep(1000);

    // Test 3: Standalone Mode
    console.log('\n[TEST 3] Standalone Mode Check...');
    try {
      const standaloneBadge = await page.locator('text=/standalone/i').count();
      const standalonePanel = await page.locator('[class*="standalone"]').count();
      const modeIndicator = await page.locator('text=/mode/i').count();

      results.standaloneModeTest.passed = standaloneBadge > 0 || standalonePanel > 0 || modeIndicator > 0;
      results.standaloneModeTest.details = `Badge: ${standaloneBadge}, Panel: ${standalonePanel}, Mode: ${modeIndicator}`;
      console.log(`  Result: ${results.standaloneModeTest.passed ? 'PASS' : 'FAIL'}`);

    } catch (error) {
      results.standaloneModeTest.details = error.message;
      console.log(`  ERROR: ${error.message}`);
    }

    // Test 4: Chat Input Test
    console.log('\n[TEST 4] Chat Input Test...');
    try {
      const chatInputSelectors = [
        'textarea[placeholder*="ask" i]',
        'textarea[placeholder*="message" i]',
        'textarea[placeholder*="chat" i]',
        'textarea',
        'input[type="text"]',
        '[contenteditable="true"]',
      ];

      let chatInput = null;
      for (const selector of chatInputSelectors) {
        const count = await page.locator(selector).count();
        if (count > 0) {
          console.log(`  Found input: ${selector}`);
          chatInput = page.locator(selector).first();
          break;
        }
      }

      if (chatInput) {
        // Use fill instead of click to avoid modal issues
        await chatInput.fill('test message');
        await sleep(1000);

        const inputValue = await chatInput.inputValue().catch(() => '') ||
                           await chatInput.evaluate(el => el.value).catch(() => '') ||
                           await chatInput.evaluate(el => el.textContent).catch(() => '');

        const hasText = inputValue?.includes('test message') || false;

        await page.screenshot({
          path: path.join(SCREENSHOT_DIR, '2_after_typing.png'),
          fullPage: true
        });

        results.chatInputTest.passed = hasText;
        results.chatInputTest.details = `Text entered: ${hasText ? 'YES' : 'NO'}, Value: "${inputValue?.substring(0, 50)}"`;

      } else {
        results.chatInputTest.details = 'No chat input found';
      }

      console.log(`  Result: ${results.chatInputTest.passed ? 'PASS' : 'FAIL'}`);

    } catch (error) {
      results.chatInputTest.details = error.message;
      console.log(`  ERROR: ${error.message}`);
    }

    // Test 5: Suggestion Button Test
    console.log('\n[TEST 5] Suggestion Button Test...');
    try {
      const suggestionSelectors = [
        'button:has-text("Explain")',
        'button:has-text("Help")',
        'button:has-text("How")',
        'button[class*="suggestion"]',
      ];

      let suggestionButton = null;
      let foundSelector = null;

      for (const selector of suggestionSelectors) {
        try {
          const count = await page.locator(selector).count();
          if (count > 0) {
            console.log(`  Found suggestion: ${selector}`);
            suggestionButton = page.locator(selector).first();
            foundSelector = selector;
            break;
          }
        } catch (e) {}
      }

      if (suggestionButton) {
        await suggestionButton.click();
        await sleep(2000);

        await page.screenshot({
          path: path.join(SCREENSHOT_DIR, '3_after_suggestion_click.png'),
          fullPage: true
        });

        results.suggestionButtonTest.passed = true;
        results.suggestionButtonTest.details = `Clicked: ${foundSelector}`;

      } else {
        results.suggestionButtonTest.details = 'No suggestion button found';
      }

      console.log(`  Result: ${results.suggestionButtonTest.passed ? 'PASS' : 'FAIL'}`);

    } catch (error) {
      results.suggestionButtonTest.details = error.message;
      console.log(`  ERROR: ${error.message}`);
    }

    // Test 6: Console Check
    console.log('\n[TEST 6] Console Check...');
    await sleep(2000);

    const hookWarnings = warnings.filter(w => w.includes('hook') || w.includes('Hook'));
    const cloudOffErrors = consoleErrors.filter(e => e.includes('CloudOff') || e.includes('cloudoff'));
    const crashErrors = consoleErrors.filter(e => e.includes('crash') || e.includes('fatal') || e.includes('uncaught'));

    results.consoleCheck.passed = cloudOffErrors.length === 0 && crashErrors.length === 0;
    results.consoleCheck.details = `Hook warnings: ${hookWarnings.length}, CloudOff: ${cloudOffErrors.length}, Crashes: ${crashErrors.length}`;

    console.log(`  Hook warnings: ${hookWarnings.length}`);
    console.log(`  CloudOff errors: ${cloudOffErrors.length}`);
    console.log(`  Crash/fatal errors: ${crashErrors.length}`);
    console.log(`  Total errors: ${consoleErrors.length}`);
    console.log(`  Result: ${results.consoleCheck.passed ? 'PASS' : 'FAIL'}`);

    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, '4_final_state.png'),
      fullPage: true
    });

    if (consoleErrors.length > 0) {
      console.log('\n[Console Errors Found]:');
      consoleErrors.slice(0, 10).forEach((err, i) => console.log(`  ${i + 1}. ${err}`));
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
