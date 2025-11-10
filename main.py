# open_page_playwright.py
# Простая утилита: открыть страницу в видимом браузере, сделать скриншот и показать первые байты HTML.
import json
import asyncio
import random
from typing import Tuple, Optional
from patchright.async_api import async_playwright, Browser, Page, BrowserContext, ElementHandle
from loguru import logger


# Настройка логирования
logger.add("stake_playwright.log", rotation="5 MB", retention="10 days", level="INFO", enqueue=True)


URL = "https://stake.com"   # менять можно на любой сайт
COOKIES_FILE = "stake_cookies.json"
EMAIL = "animtestwork@gmail.com"        # вставь свой email
PASSWORD = "AnimStoreAdmin"     # вставь свой пароль


async def save_cookies(context: BrowserContext, path=COOKIES_FILE):
    cookies = await context.cookies()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(cookies, f, ensure_ascii=False, indent=2)
    logger.info(f"✅ Cookies saved to {path}")


async def find_login_inputs(page: Page, timeout: int = 15) -> Tuple[Optional[ElementHandle], Optional[ElementHandle]]:
    """
    Пытается надёжно найти поля логина и пароля на странице Playwright.
    Возвращает (login_element_handle | None, password_element_handle | None).
    timeout — таймаут в секундах для ожидания появления любого кандидата логина.
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
        # aria-label XPath для Playwright: используем page.locator с xpath
        '//input[contains(@aria-label, "email") or contains(@aria-label, "Email")]',
    ]

    login_el = None
    pass_el = None

    # сначала ждём появления любого подходящего input (в порядке приоритета)
    for sel in candidates:
        try:
            if sel.startswith("//"):
                # XPath
                login_el = await page.wait_for_selector(f'xpath={sel[2:]}', state="attached", timeout=timeout * 1000)
            else:
                login_el = await page.wait_for_selector(sel, state="attached", timeout=timeout * 1000)
            if login_el:
                break
        except Exception:
            login_el = None
            continue

    if not login_el:
        return None, None

    # Попытка: найти input[type=password] внутри той же формы (closest form)
    try:
        form_handle = await login_el.evaluate_handle("el => el.closest('form')")
        form_el = form_handle.as_element() if form_handle else None
        if form_el:
            pass_el = await form_el.query_selector("input[type='password']")
    except Exception:
        pass_el = None

    # Если не нашли в форме — ищем ближайший input[type=password] в документе
    if not pass_el:
        try:
            pass_el = await page.query_selector("input[type='password']")
        except Exception:
            pass_el = None

    # Если всё ещё не найден — пробуем альтернативные селекторы
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
                    h = await page.query_selector(f'xpath={sel[2:]}')
                else:
                    h = await page.query_selector(sel)
                if h:
                    pass_el = h
                    break
            except Exception:
                continue

    return login_el, pass_el



async def try_click_login_button(page: Page) -> bool:
    """
    Пытается нажать кнопку логина на странице Playwright.
    Возвращает True, если клик выполнен, иначе False.
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
                locator = page.locator(f"xpath={sel[2:]}")
            else:
                locator = page.locator(sel)

            # Ждём, пока элемент появится и станет видимым
            await locator.wait_for(state="visible", timeout=3000)
            await locator.click()
            logger.info(f"✅ Кнопка логина нажата: {sel}")
            return True
        except Exception:
            continue

    logger.warning("⚠️ Не удалось найти кнопку логина.")
    return False


async def human_type(element, text: str, min_delay: float = 0.03, max_delay: float = 0.12):
    """Печатает текст по одному символу, имитируя человеческий ввод."""
    # Очищаем поле (если поддерживается)
    try:
        await element.fill("")
    except Exception:
        # Иногда fill не работает для нестандартных инпутов — пробуем клавишами
        await element.click(click_count=3)
        await element.press("Backspace")

    # Печатаем по символу
    for ch in text:
        await element.type(ch)
        await asyncio.sleep(random.uniform(min_delay, max_delay))


async def main():
    async with async_playwright() as playwright:
        async with await playwright.chromium.launch(
            channel='chrome',
            headless=False,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--window-position=-32000,-32000',
            ]) as browser: # type: Browser
            context: BrowserContext = await browser.new_context()

            page: Page = await context.new_page()
            await page.goto(URL)

            bounding_box = None
            await asyncio.sleep(10)
            for _ in range(25):
                await asyncio.sleep(1)

                for frame in page.frames:
                    if frame.url.startswith('https://challenges.cloudflare.com'):
                        frame_element = await frame.frame_element()
                        bounding_box = await frame_element.bounding_box()
                        if bounding_box:
                            break
                    if bounding_box:
                        break
                coord_x = bounding_box['x']
                coord_y = bounding_box['y']

                width = bounding_box['width']
                height = bounding_box['height']

                checkbox_x = coord_x + width / 9
                checkbox_y = coord_y + height / 2

                await page.mouse.click(x=checkbox_x, y=checkbox_y)

            clicked = await try_click_login_button(page)
            if not clicked:
                logger.warning("Кнопка логина не найдена — пропускаем этот шаг.")
                try:
                    await page.screenshot(path="login_button_not_found.png", full_page=True)
                    logger.info("📸 Скриншот сохранён: login_button_not_found.png")
                except Exception as e:
                    logger.error(f"Не удалось сделать скриншот: {e}")
                await browser.close()
                return

            login_el, pass_el = await find_login_inputs(page, timeout=12)
            if not login_el or not pass_el:
                logger.error("Не удалось найти поля логина/пароля автоматически.")
                await browser.close()
                return

            await human_type(login_el, EMAIL)
            await human_type(pass_el, PASSWORD)

            await asyncio.sleep(random.uniform(2, 5))

            try:
                submit = page.locator("button[type='submit']").first
                await submit.click()
            except Exception:
                # fallback: Enter в активном элементе
                await page.keyboard.press("Enter")

            try:
                # Ждём появления элементов, которые сигнализируют об успешном входе
                await page.wait_for_function(
                    """() => {
                        return document.body.innerText.includes('Deposit') ||
                               document.body.innerText.includes('Депозит') ||
                               !!document.querySelector('[data-testid="user-menu"]');
                    }""",
                    timeout=12000  # 12 секунд
                )
                logger.info("✅ Вход успешен — сохраняем cookies.")
                await save_cookies(context, path="stake_cookies.json")
            except Exception:
                logger.warning("⚠️ Вход автоматически не подтверждён. Вполне возможно капча.")
                logger.error("❌ Всё ещё не залогинен — cookies не сохранены. Смотри файлы debug для диагностики.")

            await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
