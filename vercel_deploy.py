#!/usr/bin/env python3
"""
TORQ-CONSOLE Vercel Deployment Script with Browser Automation
"""

import asyncio
import os
from datetime import datetime
from pathlib import Path
from playwright.async_api import async_playwright

# Configuration
SCREENSHOT_DIR = Path("E:/TORQ-CONSOLE/deployment_screenshots")
SCREENSHOT_DIR.mkdir(exist_ok=True)

ENV_VARS = {
    "ANTHROPIC_API_KEY": "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",
    "OPENAI_API_KEY": "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",
    "TORQ_CONSOLE_PRODUCTION": "true",
    "TORQ_DISABLE_LOCAL_LLM": "true",
    "TORQ_DISABLE_GPU": "true",
}

async def screenshot(page, name):
    path = SCREENSHOT_DIR / f"{datetime.now().strftime('%H%M%S')}_{name}.png"
    await page.screenshot(path=str(path), full_page=True)
    print(f"[Screenshot] {path}")
    return path

async def main():
    print("=" * 60)
    print("TORQ-CONSOLE Vercel Deployment")
    print("=" * 60)

    async with async_playwright() as p:
        # Launch browser (visible)
        browser = await p.chromium.launch(
            headless=False,
            args=['--start-maximized']
        )
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080}
        )
        page = await context.new_page()

        try:
            # Navigate to Vercel
            print("\n[1] Opening Vercel...")
            await page.goto("https://vercel.com/new", wait_until="networkidle", timeout=60000)
            await screenshot(page, "01_vercel_home")

            # Wait for page to be interactive
            await asyncio.sleep(3)
            await screenshot(page, "02_after_load")

            # Check if we need to login
            page_text = await page.inner_text("body")
            if "Sign In" in page_text or "Login" in page_text:
                print("\n[!] GitHub login required!")
                print("[!] Please complete login in the browser window.")
                print("[!] Press Enter here when done...")
                await screenshot(page, "03_login_required")
                input()

            # After potential login, take screenshot
            await asyncio.sleep(2)
            await screenshot(page, "04_after_login")

            # Try different approaches to find the import flow
            print("\n[2] Looking for import options...")

            # Check if we can search for the repo directly
            search_found = False

            # Try to find search input for repositories
            search_selectors = [
                'input[placeholder*="Search" i]',
                'input[placeholder*="search" i]',
                'input[type="search"]',
                '#search-input',
                '[data-testid="repo-search"]',
                'input[name="search"]'
            ]

            for selector in search_selectors:
                try:
                    search = await page.wait_for_selector(selector, timeout=5000)
                    if search:
                        print(f"Found search: {selector}")
                        await search.fill("pilotwaffle/TORQ-CONSOLE")
                        await asyncio.sleep(1)
                        await screenshot(page, "05_search_filled")
                        await search.press("Enter")
                        await asyncio.sleep(3)
                        await screenshot(page, "06_search_results")
                        search_found = True
                        break
                except:
                    continue

            if not search_found:
                # Try direct navigation
                print("\n[3] Trying direct repository import URL...")
                await page.goto("https://vercel.com/new?pilotwaffle/TORQ-CONSOLE", timeout=60000)
                await asyncio.sleep(5)
                await screenshot(page, "07_direct_import")

            # Look for repository selection
            print("\n[4] Selecting repository...")
            repo_found = False

            # Try multiple selector patterns
            repo_patterns = [
                'text=pilotwaffle/TORQ-CONSOLE',
                'a[href*="pilotwaffle/TORQ-CONSOLE"]',
                '[data-repo="pilotwaffle/TORQ-CONSOLE"]',
                'div:has-text("pilotwaffle/TORQ-CONSOLE")',
            ]

            for pattern in repo_patterns:
                try:
                    elem = await page.wait_for_selector(pattern, timeout=5000)
                    if elem:
                        await elem.click()
                        print(f"Clicked repo with pattern: {pattern}")
                        await asyncio.sleep(2)
                        await screenshot(page, "08_repo_selected")
                        repo_found = True
                        break
                except:
                    continue

            # Configure the project
            print("\n[5] Configuring project settings...")
            await asyncio.sleep(3)
            await screenshot(page, "09_configure_page")

            # Look for and configure build settings
            print("\n[6] Setting environment variables...")

            # Find environment variables section
            env_patterns = [
                'text=Environment Variables',
                'button:has-text("Environment")',
                '[data-testid="env-vars"]',
                'button:has-text("Add Variable")',
            ]

            for pattern in env_patterns:
                try:
                    elem = await page.wait_for_selector(pattern, timeout=3000)
                    if elem:
                        await elem.click()
                        print(f"Clicked env section: {pattern}")
                        await asyncio.sleep(1)
                        break
                except:
                    continue

            await screenshot(page, "10_env_section")

            # Add environment variables - Vercel UI specific approach
            for key, value in ENV_VARS.items():
                print(f"Adding {key}...")

                # Vercel typically has inputs for Key and Value
                try:
                    # Try multiple patterns for key input
                    key_input = None
                    key_patterns = [
                        'input[placeholder*="KEY" i]',
                        'input[placeholder*="Key" i]',
                        'input[name*="key" i]',
                        '#env-key-input',
                    ]

                    for pat in key_patterns:
                        try:
                            key_input = await page.wait_for_selector(pat, timeout=2000)
                            if key_input:
                                break
                        except:
                            continue

                    if key_input:
                        await key_input.click()
                        await key_input.fill("")
                        await key_input.type(key, delay=50)
                        await asyncio.sleep(0.5)

                    # Value input
                    value_input = None
                    value_patterns = [
                        'input[placeholder*="VALUE" i]',
                        'input[placeholder*="Value" i]',
                        'input[name*="value" i]',
                        '#env-value-input',
                    ]

                    for pat in value_patterns:
                        try:
                            value_input = await page.wait_for_selector(pat, timeout=2000)
                            if value_input:
                                break
                        except:
                            continue

                    if value_input:
                        await value_input.click()
                        await value_input.fill("")
                        await value_input.type(value, delay=50)
                        await asyncio.sleep(0.5)

                    await screenshot(page, f"11_env_{key[:10]}")

                    # Add/Save button
                    add_patterns = [
                        'button:has-text("Add")',
                        'button:has-text("Save")',
                        'button[type="submit"]',
                    ]

                    for pat in add_patterns:
                        try:
                            btn = await page.wait_for_selector(pat, timeout=2000)
                            if btn and "Add" in await btn.inner_text():
                                await btn.click()
                                await asyncio.sleep(1)
                                break
                        except:
                            continue

                except Exception as e:
                    print(f"  Error adding {key}: {e}")

            await screenshot(page, "12_all_env_vars")

            # Deploy
            print("\n[7] Starting deployment...")
            deploy_patterns = [
                'button:has-text("Deploy")',
                'button:has-text("deploy")',
                '[data-testid="deploy-button"]',
                'button[type="submit"]',
            ]

            for pattern in deploy_patterns:
                try:
                    btn = await page.wait_for_selector(pattern, timeout=5000)
                    if btn:
                        await btn.click()
                        print(f"Clicked deploy: {pattern}")
                        await screenshot(page, "13_deploy_clicked")
                        break
                except:
                    continue

            # Monitor deployment
            print("\n[8] Monitoring deployment...")
            await asyncio.sleep(5)

            deployment_url = None
            checks = 0
            max_checks = 60  # 10 minutes max

            while checks < max_checks:
                await asyncio.sleep(10)
                checks += 1
                print(f"  Check {checks}/{max_checks}...")

                await screenshot(page, f"14_monitor_{checks:02d}")

                # Check for completion
                content = await page.content()

                # Look for URL
                url_elem = await page.query_selector('a[href*="vercel.app"]')
                if url_elem:
                    deployment_url = await url_elem.get_attribute('href')
                    print(f"  Found URL: {deployment_url}")

                # Check for success indicators
                success_indicators = ['Deployment complete', 'Ready', 'Congratulations', 'Production']
                for indicator in success_indicators:
                    if indicator in content:
                        print(f"  Deployment appears complete ({indicator})")
                        await screenshot(page, "15_complete")
                        break

                if 'Deployment complete' in content or 'Ready' in content:
                    break

            await screenshot(page, "16_final")

            # Results
            print("\n" + "=" * 60)
            print("DEPLOYMENT SUMMARY")
            print("=" * 60)

            if deployment_url:
                print(f"\nDeployment URL: {deployment_url}")
            else:
                # Try to extract URL from page one more time
                urls = await page.query_selector_all('a[href*="vercel.app"]')
                if urls:
                    deployment_url = await urls[0].get_attribute('href')
                    print(f"\nDeployment URL: {deployment_url}")
                else:
                    print("\nCould not find deployment URL.")
                    print("Please check the browser and screenshots.")

            print(f"\nScreenshots: {SCREENSHOT_DIR}")

            print("\n[!] Press Enter to close browser and finish...")
            input()

        except Exception as e:
            print(f"\n[ERROR] {e}")
            import traceback
            traceback.print_exc()
            await screenshot(page, "ERROR")
            print("\n[!] Error occurred. Browser stays open for inspection.")
            input()

        finally:
            await browser.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[!] Interrupted")
