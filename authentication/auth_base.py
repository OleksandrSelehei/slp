# authentication/auth_stake.py
from abc import ABC, abstractmethod
from typing import Tuple, Optional
from patchright.async_api import Browser, BrowserContext, Page
from authentication.base_browser import BaseBrowser


class AuthenticationBase(BaseBrowser, ABC):
    """
    Abstract base class for site-specific authentication.

    Inherits from BaseBrowser and defines the interface for authentication.
    All subclasses must implement the `login` method.
    Provides active Browser, BrowserContext, and Page for further automation tasks.
    """

    @abstractmethod
    async def login(self) -> Tuple[Optional[Browser], Optional[BrowserContext], Optional[Page]]:
        """
        Abstract method to perform login to the target website and return active
        Browser, BrowserContext, and Page instances.

        Subclasses must implement this method with site-specific login logic, including:
        1. Navigating to the login page.
        2. Handling bot-screening / CAPTCHA challenges.
        3. Finding login and password fields and entering credentials using human-like typing.
        4. Submitting the login form and verifying successful login.
        5. Saving cookies for session persistence.
        6. Returning the initialized Browser, BrowserContext, and Page objects.

        Returns:
            Tuple[Optional[Browser], Optional[BrowserContext], Optional[Page]]:
                - browser: Playwright Browser instance
                - context: BrowserContext instance
                - page: Page instance for further automation
        """
        pass
