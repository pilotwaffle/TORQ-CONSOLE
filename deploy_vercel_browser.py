"""
TORQ-CONSOLE Vercel Deployment using Browser Automation
Automates the deployment process to Vercel with screenshots
"""

import asyncio
import os
import json
from datetime import datetime
from pathlib import Path

# Try to import Playwright
try:
    from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    print("Playwright not installed. Installing...")
    import subprocess
    subprocess.run(["pip", "install", "playwright"], check=True)
    subprocess.run(["playwright", "install", "chromium"], check=True)
    from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
    PLAYWRIGHT_AVAILABLE = True

# Screenshot directory
SCREENSHOT_DIR = Path("E:/TORQ-CONSOLE/deployment_screenshots")
SCREENSHOT_DIR.mkdir(exist_ok=True)

# Environment Variables to configure
ENV_VARS = {
    "ANTHROPIC_API_KEY": "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",
    "OPENAI_API_KEY": "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",
    "TORQ_CONSOLE_PRODUCTION": "true",
    "TORQ_DISABLE_LOCAL_LLM": "true",
    "TORQ_DISABLE_GPU": "true",
}

async def take_screenshot(page, name: str, full_page=True):
    """Take a screenshot with timestamp"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = SCREENSHOT_DIR / f"{timestamp}_{name}.png"
    await page.screenshot(path=str(path), full_page=full_page)
    print(f"Screenshot saved: {path}")
    return path

async def wait_for_selector(page, selector: str, timeout: int = 30000):
    """Wait for an element to be visible"""
    try:
        await page.wait_for_selector(selector, timeout=timeout, state="visible")
        return True
    except PlaywrightTimeout:
        print(f"Timeout waiting for selector: {selector}")
        return False

async def vercel_deployment():
    """Main deployment automation function"""

    print("=" * 60)
    print("TORQ-CONSOLE Vercel Deployment Automation")
    print("=" * 60)

    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(
            headless=False,  # Show browser for visibility
            slow_mo=1000  # Slow down actions for clarity
        )

        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            locale="en-US"
        )

        page = await context.new_page()

        try:
            # Step 1: Navigate to Vercel
            print("\n[Step 1] Navigating to Vercel...")
            await page.goto("https://vercel.com/new", wait_until="networkidle")
            await take_screenshot(page, "01_vercel_homepage")

            # Check if already logged in or need to login
            await asyncio.sleep(2)

            # Look for GitHub import button or login prompt
            login_needed = False
            if await page.query_selector("button[type='submit']"):
                # May need to continue with GitHub
                if "Continue" in await page.content():
                    login_needed = True

            if login_needed:
                print("Login required. Please login manually...")
                await take_screenshot(page, "02_login_prompt")
                print("\n" + "="*60)
                print("MANUAL ACTION REQUIRED")
                print("="*60)
                print("Please complete the GitHub login in the browser window.")
                print("After logging in, press Enter in this terminal to continue...")
                input("="*60 + "\n")
                await take_screenshot(page, "03_after_login")

            # Step 2: Navigate to import from Git
            print("\n[Step 2] Looking for Git import...")
            await take_screenshot(page, "04_import_page")

            # Try to find the import from Git option
            import_selectors = [
                "text=Import Git Repository",
                "a[href*='/import']",
                "button:has-text('Continue')",
                "[data-testid='import-button']"
            ]

            import_clicked = False
            for selector in import_selectors:
                try:
                    element = await page.wait_for_selector(selector, timeout=5000)
                    if element:
                        await element.click()
                        import_clicked = True
                        print(f"Clicked import selector: {selector}")
                        await take_screenshot(page, "05_import_clicked")
                        break
                except:
                    continue

            if not import_clicked:
                print("Trying direct URL to import page...")
                await page.goto("https://vercel.com/import", wait_until="domcontentloaded")
                await take_screenshot(page, "06_direct_import")

            # Step 3: Search for repository
            print("\n[Step 3] Searching for pilotwaffle/TORQ-CONSOLE...")

            # Look for search input
            await asyncio.sleep(2)

            # Try to find GitHub repository search
            search_selectors = [
                "input[placeholder*='Search' i]",
                "input[placeholder*='repository' i]",
                "#search-input",
                "[data-testid='repo-search']"
            ]

            search_input = None
            for selector in search_selectors:
                try:
                    search_input = await page.wait_for_selector(selector, timeout=3000)
                    if search_input:
                        print(f"Found search input: {selector}")
                        break
                except:
                    continue

            if search_input:
                await search_input.fill("pilotwaffle/TORQ-CONSOLE")
                await asyncio.sleep(1)
                await take_screenshot(page, "07_search_entered")

                # Press Enter or click search
                await search_input.press("Enter")
                await asyncio.sleep(2)
                await take_screenshot(page, "08_search_results")

            # Step 4: Select the repository
            print("\n[Step 4] Selecting repository...")

            # Look for the repository in results
            repo_selectors = [
                "text=pilotwaffle/TORQ-CONSOLE",
                "[data-repo='pilotwaffle/TORQ-CONSOLE']",
                "a[href*='pilotwaffle'] >> text=TORQ-CONSOLE"
            ]

            repo_clicked = False
            for selector in repo_selectors:
                try:
                    repo = await page.wait_for_selector(selector, timeout=5000)
                    if repo:
                        await repo.click()
                        repo_clicked = True
                        print(f"Clicked repository: {selector}")
                        await take_screenshot(page, "09_repo_selected")
                        break
                except:
                    continue

            if not repo_clicked:
                print("Repository not found in search. Trying direct import...")
                # Try direct URL to import specific repo
                await page.goto("https://vercel.com/new?pilotwaffle/TORQ-CONSOLE", wait_until="domcontentloaded")
                await take_screenshot(page, "10_direct_repo_import")

            # Step 5: Configure deployment settings
            print("\n[Step 5] Configuring deployment settings...")
            await asyncio.sleep(3)
            await take_screenshot(page, "11_configure_page")

            # Step 6: Add Environment Variables
            print("\n[Step 6] Adding environment variables...")

            # Look for environment variables section
            env_selectors = [
                "text=Environment Variables",
                "button:has-text('Add')",
                "[data-testid='env-vars']",
                "#env-vars"
            ]

            # Try to expand/click on environment variables section
            env_section_found = False
            for selector in env_selectors:
                try:
                    env_section = await page.wait_for_selector(selector, timeout=3000)
                    if env_section:
                        await env_section.click()
                        env_section_found = True
                        print(f"Found env section: {selector}")
                        break
                except:
                    continue

            await take_screenshot(page, "12_env_section")

            # Add each environment variable
            for key, value in ENV_VARS.items():
                print(f"Adding: {key}")

                # Look for key/value inputs
                key_selectors = ["input[name*='key' i]", "input[placeholder*='KEY' i]", "#env-key"]
                value_selectors = ["input[name*='value' i]", "input[placeholder*='VALUE' i]", "#env-value"]

                try:
                    # Enter key
                    for sel in key_selectors:
                        try:
                            key_input = await page.wait_for_selector(sel, timeout=2000)
                            if key_input:
                                await key_input.fill(key)
                                break
                        except:
                            continue

                    await asyncio.sleep(0.5)

                    # Enter value
                    for sel in value_selectors:
                        try:
                            value_input = await page.wait_for_selector(sel, timeout=2000)
                            if value_input:
                                await value_input.fill(value)
                                break
                        except:
                            continue

                    await asyncio.sleep(0.5)
                    await take_screenshot(page, f"13_env_{key.lower()}")

                    # Save/Add the variable
                    add_selectors = [
                        "button:has-text('Add')",
                        "button:has-text('Save')",
                        "button[type='submit']"
                    ]

                    for sel in add_selectors:
                        try:
                            add_btn = await page.wait_for_selector(sel, timeout=2000)
                            if add_btn and "Add" in await add_btn.inner_text():
                                await add_btn.click()
                                await asyncio.sleep(1)
                                break
                        except:
                            continue

                except Exception as e:
                    print(f"Error adding {key}: {e}")

            await take_screenshot(page, "14_all_env_vars")

            # Step 7: Deploy
            print("\n[Step 7] Deploying...")

            deploy_selectors = [
                "button:has-text('Deploy')",
                "button[type='submit']",
                "[data-testid='deploy-button']"
            ]

            for selector in deploy_selectors:
                try:
                    deploy_btn = await page.wait_for_selector(selector, timeout=3000)
                    if deploy_btn:
                        await deploy_btn.click()
                        print(f"Clicked deploy button: {selector}")
                        await take_screenshot(page, "15_deploy_clicked")
                        break
                except:
                    continue

            # Step 8: Monitor deployment
            print("\n[Step 8] Monitoring deployment...")

            # Wait for deployment to start
            await asyncio.sleep(5)
            await take_screenshot(page, "16_deployment_started")

            # Monitor for completion
            max_wait = 600  # 10 minutes
            start_time = asyncio.get_event_loop().time()

            deployment_complete = False
            deployment_url = None

            while (asyncio.get_event_loop().time() - start_time) < max_wait:
                await asyncio.sleep(10)
                await take_screenshot(page, f"17_monitor_{int(asyncio.get_event_loop().time() - start_time)}")

                # Check for completion indicators
                page_content = await page.content()

                # Success indicators
                success_indicators = [
                    "text=Deployment complete",
                    "text=Ready",
                    "text=Congratulations",
                    "[data-testid='deployment-success']",
                    ".deployment-success"
                ]

                for indicator in success_indicators:
                    try:
                        if await page.query_selector(indicator):
                            deployment_complete = True
                            print("Deployment completed successfully!")
                            break
                    except:
                        continue

                if deployment_complete:
                    break

                # Check for URL
                url_selectors = [
                    "a[href*='vercel.app']",
                    "[data-testid='deployment-url']",
                    ".deployment-url"
                ]

                for selector in url_selectors:
                    try:
                        url_elem = await page.query_selector(selector)
                        if url_elem:
                            deployment_url = await url_elem.get_attribute("href")
                            if deployment_url and "vercel.app" in deployment_url:
                                print(f"Found deployment URL: {deployment_url}")
                            break
                    except:
                        continue

            await take_screenshot(page, "18_final_status")

            # Results
            print("\n" + "=" * 60)
            print("DEPLOYMENT RESULTS")
            print("=" * 60)

            if deployment_url:
                print(f"Deployment URL: {deployment_url}")
            else:
                print("Deployment URL not found in page. Check screenshots.")

            print(f"\nScreenshots saved to: {SCREENSHOT_DIR}")

            # Keep browser open for final review
            print("\nKeeping browser open for review. Press Enter to close...")
            input()

        except Exception as e:
            print(f"\nError during deployment: {e}")
            import traceback
            traceback.print_exc()

            # Take error screenshot
            await take_screenshot(page, "ERROR_state")

            # Keep browser open
            print("\nError occurred. Browser staying open for inspection.")
            print("Press Enter to close...")
            input()

        finally:
            await browser.close()

if __name__ == "__main__":
    print("Starting TORQ-CONSOLE Vercel Deployment Automation...")
    print("This will open a browser window for the deployment process.")
    print("\nNote: If GitHub login is required, you will need to complete it manually.")
    print("=" * 60)

    try:
        asyncio.run(vercel_deployment())
    except KeyboardInterrupt:
        print("\n\nDeployment interrupted by user.")
    except Exception as e:
        print(f"\n\nFatal error: {e}")
        import traceback
        traceback.print_exc()
