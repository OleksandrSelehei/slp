import asyncio
import random
from typing import Tuple, Optional, Union
from patchright.async_api import Browser, BrowserContext, Page, ElementHandle, Locator
from authentication.auth_base import AuthenticationBase
from utils.logs.logs import logger
from email_fetcher.gmail_code_fetcher import GmailCodeFetcher


class AuthenticationStake(AuthenticationBase):
    """
    Class for authentication on Stake.com.

    Inherits from AuthenticationBase, which provides:
    - Configured Browser (Browser)
    - Session Context (BrowserContext)
    - Page (Page) for further automation

    This class implements the login logic specifically for Stake.com.

    Usage:
    - Access browser, context, and page for subsequent actions,
      e.g., scraping data, sending requests, interacting with UI.
    - Save cookies for reusing sessions.
    - Handle anti-bot protection (Cloudflare, reCAPTCHA, etc.).
    """

    async def __close_region_modal_if_visible(
            self,
            appear_timeout_ms: int = 6000,
            btn_timeout_ms: int = 3000,
            retries: int = 2,
    ) -> bool:
        """
        Close the restricted-region modal if it becomes visible.
        Returns True if closed, False if not present or not visible.
        """
        modal = self.page.locator('[data-testid="modal-restrictedRegion"]')
        close_btn = modal.locator('[data-testid="modal-close"]')

        for attempt in range(1, retries + 1):
            try:
                logger.info(f"[SiteParser] Modal check attempt {attempt}/{retries}…")

                await modal.wait_for(state="visible", timeout=appear_timeout_ms)
                visible = await modal.is_visible()
                if not visible:
                    logger.info("[SiteParser] Modal present but not visible — retrying…")
                    await asyncio.sleep(0.3)
                    continue

                logger.info("[SiteParser] Modal is visible. Looking for close button…")

                await close_btn.wait_for(state="visible", timeout=btn_timeout_ms)

                clickable = await close_btn.is_enabled()
                if not clickable:
                    logger.info("[SiteParser] Close button visible but disabled — small wait…")
                    await asyncio.sleep(0.25)

                try:
                    await close_btn.click()
                    logger.info("[SiteParser] Modal closed successfully (normal click).")
                    return True
                except Exception as e:
                    logger.warning(f"[SiteParser] Normal click failed: {e}. Trying force click…")
                    await close_btn.click(force=True)
                    logger.info("[SiteParser] Modal closed successfully (force click).")
                    return True

            except TimeoutError:
                logger.info("[SiteParser] No visible modal detected in time.")
                return False
            except Exception as e:
                logger.error(f"[SiteParser] Error while handling modal: {e}")
                await asyncio.sleep(0.4)

        logger.warning("[SiteParser] Modal detected but could not be closed after retries.")
        return False

    async def __find_login_inputs(self, timeout: int = 15) -> Tuple[
        Optional[Locator], Optional[Locator]]:
        """
        Attempts to reliably locate the login and password input fields on a Playwright page.
        Returns (login_element_handle | None, password_element_handle | None).
        timeout — timeout in seconds for waiting for any login candidate to appear.
        """
        candidates = [
            '[data-testid="login-name"]',
            'input[type="email"]',
            'input[name="email"]',
            'input[name="username"]',
            '//input[contains(@placeholder, "Email")]',
            '//input[contains(@placeholder, "Логин")]',
            '//input[contains(@placeholder, "E-mail")]',
            '//input[contains(@placeholder, "Username")]',
            '//input[contains(@aria-label, "email") or contains(@aria-label, "Email")]',
        ]

        login_el = None
        pass_el = None

        # First, wait for any suitable input (in order of priority)
        for sel in candidates:
            try:
                if sel.startswith("//"):
                    login_el = await self.page.wait_for_selector(f'xpath={sel[2:]}', state="attached",
                                                                 timeout=timeout * 1000)
                else:
                    login_el = await self.page.wait_for_selector(sel, state="attached", timeout=timeout * 1000)
                if login_el:
                    break
            except Exception:
                login_el = None
                continue

        if not login_el:
            return None, None

        # Try to find input[type=password] inside the same form (closest form)
        try:
            form_handle = await login_el.evaluate_handle("el => el.closest('form')")
            form_el = form_handle.as_element() if form_handle else None
            if form_el:
                pass_el = await form_el.query_selector("input[type='password']")
        except Exception:
            pass_el = None

        # If not found in form — search for nearest input[type=password] in the document
        if not pass_el:
            try:
                pass_el = await self.page.query_selector("input[type='password']")
            except Exception:
                pass_el = None

        # If still not found — try alternative selectors
        if not pass_el:
            alt_pass = [
                'input[type="password"]',
                'input[name="password"]',
                '//input[contains(@placeholder, "Password")]',
                '//input[contains(@placeholder, "Пароль")]'
            ]
            for sel in alt_pass:
                try:
                    if sel.startswith("//"):
                        h = await self.page.query_selector(f'xpath={sel[2:]}')
                    else:
                        h = await self.page.query_selector(sel)
                    if h:
                        pass_el = h
                        break
                except Exception:
                    continue

        return login_el, pass_el

    async def __try_click_login_button(self) -> bool:
        """
        Attempts to click the login button on the page.
        Returns True if clicked successfully, otherwise False.
        """
        selectors = [
            '[data-testid="login-link"]',
            '//button[contains(., "Log in")]',
            '//button[contains(., "Вход")]',
            '//a[contains(., "Log in")]',
        ]

        for sel in selectors:
            try:
                if sel.startswith("//"):
                    locator = self.page.locator(f"xpath={sel[2:]}")
                else:
                    locator = self.page.locator(sel)

                await locator.wait_for(state="visible", timeout=3000)
                await locator.click()
                logger.info(f"✅ Login button clicked: {sel}")
                return True
            except Exception:
                continue

        logger.warning("⚠️ Could not find the login button.")
        return False

    async def __get_login_code_input(self, timeout_ms: int = 4000) -> Optional[Locator]:
        """
        Locate the login code input by its data-testid.
        Returns a Locator or None if not found/visible in time.
        """
        try:
            locator = self.page.locator('[data-testid="login-code"]')
            await locator.wait_for(state="visible", timeout=timeout_ms)
            visible = await locator.is_visible()
            if not visible:
                logger.info("[UI] Login code input found but not visible.")
                return None
            return locator
        except TimeoutError:
            logger.info("[UI] Login code input not visible within timeout.")
            return None
        except Exception as e:
            logger.error(f"[UI] Error locating login code input: {e}")
            return None

    async def __fill_login_code(self, code: Union[str, int]) -> bool:
        """
        High-level helper: locate the login code input and type the code.
        Returns True on success, False otherwise.
        """
        input_el: Locator = await self.__get_login_code_input()
        if not input_el:
            return False

        code_str = str(code)
        await self.human_type(input_el, code_str)
        logger.info(f"[UI] Code typed: {code_str}")
        return True

    async def login(self) -> Tuple[Optional[Browser], Optional[BrowserContext], Optional[Page]]:
        await self.verify_human()
        # Initial wait to ensure page is loaded
        await asyncio.sleep(10)

        # Close the restricted region modal if it appears
        await self.__close_region_modal_if_visible()
        await asyncio.sleep(3)

        # Try clicking the login button
        clicked = await self.__try_click_login_button()
        if not clicked:
            logger.warning("Login button not found — skipping this step.")
            await self.browser.close()
            return None, None, None

        # Locate login and password fields
        login_el, pass_el = await self.__find_login_inputs(timeout=12)
        if not login_el or not pass_el:
            logger.error("Failed to automatically locate login/password fields.")
            await self.browser.close()
            return None, None, None

        # Type login credentials using human-like typing
        await self.human_type(login_el, self.email)
        await self.human_type(pass_el, self.password)

        await asyncio.sleep(random.uniform(2, 5))

        try:
            # Try clicking the submit button
            submit = self.page.locator("button[type='submit']").first
            await submit.click()
        except Exception:
            # Fallback: press Enter on the active element
            await self.page.keyboard.press("Enter")

        await asyncio.sleep(10)

        # Fetch 2FA/login code from Gmail
        gmail_service = GmailCodeFetcher()
        code = gmail_service.run()

        if code:
            logger.info(f'Code for login from Gmail message successfully fetched: {code}')
            ok = await self.__fill_login_code(code)
            if not ok:
                logger.warning("[Flow] Could not type code into the input.")
            try:
                await asyncio.sleep(random.uniform(2, 5))
                submit = self.page.locator("button[type='submit']").first
                await submit.click()
            except Exception:
                # Fallback: press Enter on the active element
                await self.page.keyboard.press("Enter")

        try:
            # Wait for elements that indicate successful login
            await self.page.wait_for_function(
                """() => {
                    return document.body.innerText.includes('Deposit') ||
                           document.body.innerText.includes('Депозит') ||
                           !!document.querySelector('[data-testid="user-menu"]');
                }""",
                timeout=30000  # 30 seconds
            )
            await asyncio.sleep(random.uniform(2, 5))
            logger.info("✅ Login successful")
        except Exception:
            logger.warning("⚠️ Automatic login confirmation failed. Captcha may be present.")
            logger.error("❌ Still not logged in.")

        await asyncio.sleep(15)

        return self.browser, self.context, self.page
