#!/usr/bin/env python3
"""
TORQ-CONSOLE Vercel Browser Deployment
Uses Playwright for automated Vercel deployment with proper login handling
"""

import asyncio
import os
import sys
from datetime import datetime
from pathlib import Path

from playwright.async_api import async_playwright, Page, Browser

# Configuration
SCREENSHOT_DIR = Path("E:/TORQ-CONSOLE/deployment_screenshots")
SCREENSHOT_DIR.mkdir(exist_ok=True)

ENV_VARS = [
    {"key": "ANTHROPIC_API_KEY", "value": "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"},
    {"key": "OPENAI_API_KEY", "value": "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"},
    {"key": "TORQ_CONSOLE_PRODUCTION", "value": "true"},
    {"key": "TORQ_DISABLE_LOCAL_LLM", "value": "true"},
    {"key": "TORQ_DISABLE_GPU", "value": "true"},
]

class DeploymentLogger:
    def __init__(self):
        self.logs = []

    def log(self, message: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        entry = f"[{timestamp}] {message}"
        print(entry)
        self.logs.append(entry)

    def save(self):
        log_file = SCREENSHOT_DIR / f"deployment_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(log_file, "w") as f:
            f.write("\n".join(self.logs))
        print(f"\n[Log saved to: {log_file}]")

logger = DeploymentLogger()

async def screenshot(page: Page, name: str):
    path = SCREENSHOT_DIR / f"{datetime.now().strftime('%H%M%S')}_{name}.png"
    try:
        await page.screenshot(path=str(path), full_page=True)
        logger.log(f"Screenshot: {name}")
    except Exception as e:
        logger.log(f"Screenshot failed for {name}: {e}")
    return path

async def wait_and_click(page: Page, selector: str, timeout: int = 10000, description: str = ""):
    """Wait for element and click it"""
    try:
        elem = await page.wait_for_selector(selector, timeout=timeout, state="visible")
        if elem:
            await elem.click()
            logger.log(f"Clicked: {description or selector}")
            return True
    except Exception as e:
        logger.log(f"Click failed for {selector}: {e}")
    return False

async def wait_and_fill(page: Page, selector: str, value: str, timeout: int = 10000):
    """Wait for input and fill it"""
    try:
        elem = await page.wait_for_selector(selector, timeout=timeout, state="visible")
        if elem:
            await elem.fill(value)
            return True
    except Exception as e:
        logger.log(f"Fill failed for {selector}: {e}")
    return False

async def wait_for_text(page: Page, text: str, timeout: int = 30000):
    """Wait for text to appear on page"""
    start = asyncio.get_event_loop().time()
    while (asyncio.get_event_loop().time() - start) < (timeout / 1000):
        try:
            if await page.query_selector(f"text={text}"):
                return True
        except:
            pass
        await asyncio.sleep(0.5)
    return False

async def main():
    logger.log("="*50)
    logger.log("TORQ-CONSOLE Vercel Deployment Started")
    logger.log("="*50)

    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(
            headless=False,
            args=['--start-maximized', '--disable-blink-features=AutomationControlled']
        )

        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )

        page = await context.new_page()

        # Set default timeout
        page.set_default_timeout(60000)

        try:
            # Step 1: Go to Vercel
            logger.log("Step 1: Navigating to Vercel...")
            await page.goto("https://vercel.com/new", wait_until="domcontentloaded", timeout=60000)
            await asyncio.sleep(3)
            await screenshot(page, "01_vercel_home")

            # Step 2: Check login status
            logger.log("Step 2: Checking authentication...")

            # Check if we're already logged in
            is_logged_in = False
            page_content = await page.content()

            # Look for signs of being logged in
            logged_in_indicators = ["dashboard", "Add New", "Projects", "Deployments"]
            for indicator in logged_in_indicators:
                if indicator.lower() in page_content.lower():
                    is_logged_in = True
                    break

            if not is_logged_in:
                logger.log("NOT LOGGED IN - Manual login required")
                await screenshot(page, "02_login_needed")

                print("\n" + "="*60)
                print("MANUAL LOGIN REQUIRED")
                print("="*60)
                print("1. Complete GitHub login in the browser window")
                print("2. Grant any necessary permissions")
                print("3. Wait for redirection to Vercel dashboard")
                print("4. Return here and press ENTER to continue")
                print("="*60 + "\n")

                input("[PRESS ENTER AFTER LOGIN...]")

                await asyncio.sleep(2)
                await screenshot(page, "03_after_login")
                logger.log("User confirmed login completed")
            else:
                logger.log("Already logged in to Vercel")
                await screenshot(page, "03_already_logged_in")

            # Step 3: Import Repository
            logger.log("Step 3: Importing repository...")

            # Try to find the import/git flow
            import_attempts = [
                "https://vercel.com/import",
                "https://vercel.com/new/git",
                "https://vercel.com/new?github=pilotwaffle%2FTORQ-CONSOLE"
            ]

            import_success = False

            for url in import_attempts:
                try:
                    logger.log(f"Trying: {url}")
                    await page.goto(url, timeout=60000)
                    await asyncio.sleep(3)
                    await screenshot(page, f"04_import_{len(import_attempts) - import_attempts.index(url)}")

                    # Check if we see GitHub repos
                    if "github" in await page.content().lower() or "import" in await page.content().lower():
                        import_success = True
                        break
                except Exception as e:
                    logger.log(f"Failed to load {url}: {e}")

            # Step 4: Search/Select Repository
            logger.log("Step 4: Finding pilotwaffle/TORQ-CONSOLE...")
            await screenshot(page, "05_repo_search")

            # Try to search for the repository
            search_selectors = [
                "input[placeholder*='search' i]",
                "input[placeholder*='Search' i]",
                "input[type='search']",
                "#search-input",
                "[data-testid='search']",
            ]

            search_performed = False
            for selector in search_selectors:
                try:
                    search_input = await page.query_selector(selector)
                    if search_input:
                        await search_input.fill("pilotwaffle/TORQ-CONSOLE")
                        await asyncio.sleep(1)
                        await search_input.press("Enter")
                        await asyncio.sleep(2)
                        await screenshot(page, "06_search_done")
                        search_performed = True
                        break
                except:
                    continue

            # Try to click on the repository
            logger.log("Looking for repository card...")
            repo_selectors = [
                "a[href*='pilotwaffle/TORQ-CONSOLE']",
                "text=pilotwaffle/TORQ-CONSOLE",
                "[data-repo*='pilotwaffle']",
                "div:has-text('TORQ-CONSOLE')",
            ]

            repo_clicked = False
            for selector in repo_selectors:
                try:
                    elem = await page.query_selector(selector)
                    if elem:
                        await elem.click()
                        await asyncio.sleep(2)
                        await screenshot(page, "07_repo_clicked")
                        repo_clicked = True
                        break
                except:
                    continue

            if not repo_clicked:
                logger.log("Repository not clickable, may need manual selection")
                print("\n[!] Please click on pilotwaffle/TORQ-CONSOLE repository in the browser")
                input("[PRESS ENTER AFTER SELECTING REPO...]")
                await screenshot(page, "07_repo_selected_manually")

            # Step 5: Configure Project
            logger.log("Step 5: Configuring project...")
            await asyncio.sleep(3)
            await screenshot(page, "08_configure_page")

            # Check if there's a "Configure" button or similar
            configure_selectors = [
                "button:has-text('Configure')",
                "button:has-text('Next')",
                "button:has-text('Continue')",
            ]

            for selector in configure_selectors:
                try:
                    if await page.query_selector(selector):
                        await wait_and_click(page, selector, description="Configure/Next")
                        await asyncio.sleep(2)
                        await screenshot(page, "09_configure_clicked")
                        break
                except:
                    continue

            # Step 6: Environment Variables
            logger.log("Step 6: Adding environment variables...")

            # Find and click Environment Variables section
            env_section_selectors = [
                "button:has-text('Environment Variables')",
                "button:has-text('Environment')",
                "[data-testid='env-vars']",
                "a:has-text('Environment Variables')",
            ]

            env_opened = False
            for selector in env_section_selectors:
                try:
                    if await page.query_selector(selector):
                        await wait_and_click(page, selector, description="Env Variables section")
                        await asyncio.sleep(1)
                        env_opened = True
                        break
                except:
                    continue

            await screenshot(page, "10_env_section")

            # Add each environment variable
            for i, env_var in enumerate(ENV_VARS):
                key = env_var["key"]
                value = env_var["value"]
                logger.log(f"Adding {key}...")

                # Look for the input fields
                try:
                    # Key input
                    key_selectors = [
                        "input[name='key']",
                        "input[placeholder*='KEY' i]",
                        "input[placeholder*='Name' i]",
                        "#env-key",
                    ]

                    key_filled = False
                    for sel in key_selectors:
                        try:
                            if await page.query_selector(sel):
                                await wait_and_fill(page, sel, key)
                                key_filled = True
                                await asyncio.sleep(0.5)
                                break
                        except:
                            continue

                    # Value input
                    value_selectors = [
                        "input[name='value']",
                        "input[placeholder*='VALUE' i]",
                        "#env-value",
                    ]

                    value_filled = False
                    for sel in value_selectors:
                        try:
                            if await page.query_selector(sel):
                                await wait_and_fill(page, sel, value)
                                value_filled = True
                                await asyncio.sleep(0.5)
                                break
                        except:
                            continue

                    await screenshot(page, f"11_env_{i}")

                    # Add/Save button
                    add_selectors = [
                        "button:has-text('Add')",
                        "button:has-text('Save')",
                        "button:has-text('Create')",
                    ]

                    for sel in add_selectors:
                        try:
                            btn = await page.query_selector(sel)
                            if btn and "add" in (await btn.inner_text()).lower():
                                await btn.click()
                                await asyncio.sleep(1)
                                break
                        except:
                            continue

                except Exception as e:
                    logger.log(f"Error adding {key}: {e}")

            await screenshot(page, "12_all_env_added")

            # Step 7: Deploy
            logger.log("Step 7: Deploying...")

            deploy_selectors = [
                "button:has-text('Deploy')",
                "button[type='submit']",
                "[data-testid='deploy-button']",
            ]

            deployed = False
            for selector in deploy_selectors:
                try:
                    if await page.query_selector(selector):
                        await wait_and_click(page, selector, description="Deploy button")
                        deployed = True
                        await screenshot(page, "13_deploy_clicked")
                        break
                except:
                    continue

            if not deployed:
                logger.log("Could not find deploy button")
                print("\n[!] Please click the Deploy button in the browser")
                input("[PRESS ENTER AFTER CLICKING DEPLOY...]")
                await screenshot(page, "13_deploy_manual")

            # Step 8: Monitor Deployment
            logger.log("Step 8: Monitoring deployment...")

            deployment_url = None
            max_wait = 600  # 10 minutes
            check_interval = 10
            checks = 0
            max_checks = max_wait // check_interval

            while checks < max_checks:
                await asyncio.sleep(check_interval)
                checks += 1
                logger.log(f"Deployment check {checks}/{max_checks}")

                await screenshot(page, f"14_monitor_{checks:02d}")

                # Check for URL
                try:
                    urls = await page.query_selector_all("a[href*='vercel.app']")
                    if urls:
                        for url_elem in urls:
                            href = await url_elem.get_attribute('href')
                            if href and 'vercel.app' in href:
                                deployment_url = href
                                logger.log(f"Found URL: {deployment_url}")
                                break
                except:
                    pass

                # Check for completion
                content = await page.content()
                success_indicators = ["Deployment complete", "Successfully deployed", "Production", "Ready"]

                for indicator in success_indicators:
                    if indicator in content:
                        logger.log(f"Deployment complete! ({indicator})")
                        await screenshot(page, "15_complete")
                        break

                # If we see "error" or "failed", we should report
                if "error" in content.lower() or "failed" in content.lower():
                    logger.log("ERROR detected in deployment")
                    await screenshot(page, "ERROR_deployment_failed")
                    break

            # Final
            await screenshot(page, "16_final_state")

            # Results
            print("\n" + "="*60)
            print("DEPLOYMENT COMPLETE")
            print("="*60)

            if deployment_url:
                print(f"\n  URL: {deployment_url}")
            else:
                # Try one more time to get URL
                try:
                    urls = await page.query_selector_all("a[href*='vercel.app']")
                    if urls:
                        deployment_url = await urls[0].get_attribute('href')
                        print(f"\n  URL: {deployment_url}")
                    else:
                        print("\n  URL: Not found - check browser and screenshots")
                except:
                    print("\n  URL: Could not retrieve")

            print(f"\n  Screenshots: {SCREENSHOT_DIR}")
            print("\n[!] Press Enter to close browser...")
            input()

        except Exception as e:
            logger.log(f"FATAL ERROR: {e}")
            import traceback
            traceback.print_exc()
            await screenshot(page, "FATAL_ERROR")
            print("\n[!] Fatal error - browser staying open for inspection")
            input()

        finally:
            await browser.close()

    logger.save()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.log("Interrupted by user")
        logger.save()
