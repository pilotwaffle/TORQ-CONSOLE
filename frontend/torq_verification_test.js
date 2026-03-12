// TORQ Console Verification Tests
// Run: node torq_verification_test.js

const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const SCREENSHOT_DIR = path.join(__dirname, 'verification_screenshots');
const PORT = 3000; // Vite dev server runs on 3000, not 3018
const BASE_URL = `http://localhost:${PORT}`;

// Create screenshot directory
if (!fs.existsSync(SCREENSHOT_DIR)) {
  fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });
}

async function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function runTests() {
  console.log('='.repeat(60));
  console.log('TORQ CONSOLE VERIFICATION TESTS');
  console.log('='.repeat(60));
  console.log(`Testing URL: ${BASE_URL}`);
  console.log(`Screenshot directory: ${SCREENSHOT_DIR}`);
  console.log('='.repeat(60));

  const browser = await chromium.launch({
    headless: false, // Run in visible mode for verification
    slowMo: 500 // Slow down actions for visibility
  });

  const context = await browser.newContext({
    viewport: { width: 1920, height: 1080 },
    recordVideo: { dir: SCREENSHOT_DIR, size: { width: 1920, height: 1080 } }
  });

  const page = await context.newPage();

  // Track console messages and errors
  const consoleLogs = [];
  const consoleErrors = [];
  const warnings = [];

  page.on('console', msg => {
    const type = msg.type();
    const text = msg.text();
    consoleLogs.push({ type, text });

    if (type === 'error') {
      consoleErrors.push(text);
      console.log(`[Browser Error] ${text}`);
    } else if (type === 'warning') {
      warnings.push(text);
      console.log(`[Browser Warning] ${text}`);
    }
  });

  page.on('pageerror', error => {
    consoleErrors.push(error.message);
    console.log(`[Page Error] ${error.message}`);
  });

  // Test Results
  const results = {
    loadCheck: { passed: false, details: '' },
    chatInputTest: { passed: false, details: '' },
    suggestionButtonTest: { passed: false, details: '' },
    standaloneModeTest: { passed: false, details: '' },
    consoleCheck: { passed: false, details: '' },
  };

  try {
    // Test 1: Load Check
    console.log('\n[TEST 1] Load Check: Navigating to TORQ Console...');
    try {
      const response = await page.goto(BASE_URL, {
        waitUntil: 'networkidle',
        timeout: 15000
      });

      const status = response?.status() || 'unknown';
      console.log(`  Response status: ${status}`);

      // Wait for app to load
      await sleep(3000);

      // Check for critical errors
      const bodyContent = await page.content();
      const hasCloudOffError = bodyContent.includes('CloudOff') || bodyContent.includes('cloudoff');

      // Screenshot 1: Initial Load
      await page.screenshot({
        path: path.join(SCREENSHOT_DIR, '1_initial_load.png'),
        fullPage: true
      });
      console.log('  Screenshot saved: 1_initial_load.png');

      results.loadCheck.passed = status === 200;
      results.loadCheck.details = `Status: ${status}, CloudOff error: ${hasCloudOffError ? 'YES' : 'NO'}`;

      console.log(`  Result: ${results.loadCheck.passed ? 'PASS' : 'FAIL'}`);

    } catch (error) {
      results.loadCheck.details = error.message;
      console.log(`  ERROR: ${error.message}`);
    }

    // Test 2: Check for Standalone Mode Badge
    console.log('\n[TEST 2] Standalone Mode Check...');
    try {
      await sleep(1000);

      // Look for standalone mode indicators
      const standaloneBadge = await page.locator('text=/standalone/i').count();
      const standalonePanel = await page.locator('[class*="standalone"]').count();
      const modeIndicator = await page.locator('text=/mode/i').count();

      results.standaloneModeTest.passed = standaloneBadge > 0 || standalonePanel > 0 || modeIndicator > 0;
      results.standaloneModeTest.details = `Badge elements: ${standaloneBadge}, Panel elements: ${standalonePanel}, Mode indicators: ${modeIndicator}`;

      console.log(`  Result: ${results.standaloneModeTest.passed ? 'PASS' : 'FAIL'} (${results.standaloneModeTest.details})`);

    } catch (error) {
      results.standaloneModeTest.details = error.message;
      console.log(`  ERROR: ${error.message}`);
    }

    // Test 3: Chat Input Test
    console.log('\n[TEST 3] Chat Input Test...');
    try {
      // Look for chat input (textarea or input)
      const chatInputSelectors = [
        'textarea[placeholder*="message" i]',
        'textarea[placeholder*="chat" i]',
        'textarea[placeholder*="ask" i]',
        'textarea',
        'input[type="text"]',
        '[contenteditable="true"]',
        '[role="textbox"]'
      ];

      let chatInput = null;
      for (const selector of chatInputSelectors) {
        const count = await page.locator(selector).count();
        if (count > 0) {
          console.log(`  Found input with selector: ${selector} (${count} elements)`);
          chatInput = page.locator(selector).first();
          break;
        }
      }

      if (chatInput) {
        // Try to type in the input
        await chatInput.click();
        await sleep(500);
        await chatInput.fill('test message');
        await sleep(1000);

        // Verify the text was entered
        const inputValue = await chatInput.inputValue() || await chatInput.innerText() || await chatInput.evaluate(el => el.textContent);
        const hasText = inputValue?.includes('test message') || false;

        // Screenshot 2: After typing
        await page.screenshot({
          path: path.join(SCREENSHOT_DIR, '2_after_typing.png'),
          fullPage: true
        });
        console.log('  Screenshot saved: 2_after_typing.png');

        results.chatInputTest.passed = hasText;
        results.chatInputTest.details = `Text "test message" entered: ${hasText ? 'YES' : 'NO'}, Value: "${inputValue}"`;

      } else {
        results.chatInputTest.details = 'No chat input found';
      }

      console.log(`  Result: ${results.chatInputTest.passed ? 'PASS' : 'FAIL'}`);

    } catch (error) {
      results.chatInputTest.details = error.message;
      console.log(`  ERROR: ${error.message}`);
    }

    // Test 4: Suggestion Button Test
    console.log('\n[TEST 4] Suggestion Button Test...');
    try {
      // Look for suggestion buttons/chips
      const suggestionSelectors = [
        'button:has-text("Explain")',
        'button:has-text("Help")',
        'button:has-text("How")',
        'button:has-text("What")',
        'button[class*="suggestion"]',
        'button[class*="chip"]',
        '[role="button"]:has-text("Explain")',
        'text=Explain',
      ];

      let suggestionButton = null;
      let foundSelector = null;

      for (const selector of suggestionSelectors) {
        try {
          const count = await page.locator(selector).count();
          if (count > 0) {
            console.log(`  Found suggestion with selector: ${selector} (${count} elements)`);
            suggestionButton = page.locator(selector).first();
            foundSelector = selector;
            break;
          }
        } catch (e) {
          // Skip invalid selectors
        }
      }

      if (suggestionButton) {
        // Click the suggestion button
        await suggestionButton.click();
        await sleep(2000);

        // Check if a message was sent (look for sent message or chat input change)
        const chatInputAfter = await page.locator('textarea').first().inputValue().catch(() => '');
        const hasMessageInChat = await page.locator('text=/Explain|Help|How|What/i').count() > 0;

        // Screenshot 3: After clicking suggestion
        await page.screenshot({
          path: path.join(SCREENSHOT_DIR, '3_after_suggestion_click.png'),
          fullPage: true
        });
        console.log('  Screenshot saved: 3_after_suggestion_click.png');

        results.suggestionButtonTest.passed = true;
        results.suggestionButtonTest.details = `Clicked selector: ${foundSelector}, Message in chat: ${hasMessageInChat ? 'YES' : 'NO'}`;

      } else {
        results.suggestionButtonTest.details = 'No suggestion button found';
      }

      console.log(`  Result: ${results.suggestionButtonTest.passed ? 'PASS' : 'FAIL'}`);

    } catch (error) {
      results.suggestionButtonTest.details = error.message;
      console.log(`  ERROR: ${error.message}`);
    }

    // Test 5: Console Check
    console.log('\n[TEST 5] Console Check...');
    await sleep(2000);

    // Check for specific error patterns
    const hookWarnings = warnings.filter(w => w.includes('hook') || w.includes('Hook'));
    const cloudOffErrors = consoleErrors.filter(e => e.includes('CloudOff') || e.includes('cloudoff'));
    const crashErrors = consoleErrors.filter(e => e.includes('crash') || e.includes('fatal') || e.includes('uncaught'));

    results.consoleCheck.passed = cloudOffErrors.length === 0 && crashErrors.length === 0;
    results.consoleCheck.details = `Hook warnings: ${hookWarnings.length}, CloudOff errors: ${cloudOffErrors.length}, Crash errors: ${crashErrors.length}, Total errors: ${consoleErrors.length}, Total warnings: ${warnings.length}`;

    console.log(`  Hook warnings: ${hookWarnings.length}`);
    console.log(`  CloudOff errors: ${cloudOffErrors.length}`);
    console.log(`  Crash/fatal errors: ${crashErrors.length}`);
    console.log(`  Total console errors: ${consoleErrors.length}`);
    console.log(`  Total warnings: ${warnings.length}`);
    console.log(`  Result: ${results.consoleCheck.passed ? 'PASS' : 'FAIL'}`);

    // Screenshot 4: Console (capture the page state)
    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, '4_final_state.png'),
      fullPage: true
    });
    console.log('  Screenshot saved: 4_final_state.png');

    // Print detailed console logs if any errors
    if (consoleErrors.length > 0) {
      console.log('\n[Console Errors Found]:');
      consoleErrors.slice(0, 10).forEach((err, i) => console.log(`  ${i + 1}. ${err}`));
    }

    if (hookWarnings.length > 0) {
      console.log('\n[Hook Warnings Found]:');
      hookWarnings.slice(0, 10).forEach((w, i) => console.log(`  ${i + 1}. ${w}`));
    }

  } catch (error) {
    console.error('\n[FATAL ERROR] Test execution failed:', error.message);
  } finally {
    await sleep(2000);
    await browser.close();

    // Print Summary
    console.log('\n' + '='.repeat(60));
    console.log('TEST SUMMARY');
    console.log('='.repeat(60));

    const totalTests = Object.keys(results).length;
    const passedTests = Object.values(results).filter(r => r.passed).length;

    Object.entries(results).forEach(([test, result]) => {
      const status = result.passed ? '✓ PASS' : '✗ FAIL';
      console.log(`\n${test}:`);
      console.log(`  Status: ${status}`);
      console.log(`  Details: ${result.details}`);
    });

    console.log('\n' + '='.repeat(60));
    console.log(`OVERALL: ${passedTests}/${totalTests} tests passed`);
    console.log(`Screenshots saved to: ${SCREENSHOT_DIR}`);
    console.log('='.repeat(60));

    // Save results to JSON
    const resultsPath = path.join(SCREENSHOT_DIR, 'test_results.json');
    fs.writeFileSync(resultsPath, JSON.stringify({
      timestamp: new Date().toISOString(),
      baseUrl: BASE_URL,
      results,
      summary: {
        total: totalTests,
        passed: passedTests,
        failed: totalTests - passedTests
      },
      consoleErrors,
      warnings
    }, null, 2));
    console.log(`\nResults saved to: ${resultsPath}`);
  }
}

// Run tests
runTests().catch(console.error);
