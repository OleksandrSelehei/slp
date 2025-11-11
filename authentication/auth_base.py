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
        1. **First step**: call `await self.verify_human()` to prepare the browser,
           context, and page, passing bot-screening challenges if any.
        2. Finding login and password fields and entering credentials using human-like typing.
        3. Submitting the login form and verifying successful login.
        4. Saving cookies for session persistence.
        5. Returning the initialized Browser, BrowserContext, and Page objects.

        **Important:** The asynchronous method `verify_human` must be called at the start
        of `login` to ensure that `self.browser`, `self.context`, and `self.page` are
        properly initialized before performing site-specific login actions.

        Returns:
            Tuple[Optional[Browser], Optional[BrowserContext], Optional[Page]]:
                - browser: Playwright Browser instance
                - context: BrowserContext instance
                - page: Page instance for further automation
        """
        pass
