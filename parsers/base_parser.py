# parsers/base_parser.py
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union
from patchright.async_api import Browser, BrowserContext, Page
from authentication.auth_base import AuthenticationBase


class BaseParser(ABC):
    """
    Abstract base class for resource-specific parsers.

    Each parser is responsible for:
      - Performing data extraction from a specific website or dashboard.
      - Using an authentication class to handle login and session setup.
      - Returning structured parsed data for further processing.

    The parser uses an authentication class (inheriting from AuthenticationBase)
    to initialize browser automation (Browser, Context, and Page) and must store
    them for use during parsing.
    """

    def __init__(self, auth_class: AuthenticationBase):
        """
        Initialize the parser with a specific authentication class.

        Args:
            auth_class (AuthenticationBase): An instance of the authentication
            class that has implemented site-specific login logic.
        """
        self.auth = auth_class
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None

    async def initialize_session(self) -> None:
        """
        Initialize browser session by performing authentication.

        This method:
        1. Calls the authentication class’s `login` method.
        2. Stores the resulting Browser, Context, and Page in the parser instance
           for further interaction with the site.
        """
        self.browser, self.context, self.page = await self.auth.login()

    @abstractmethod
    async def parse_data(self) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Abstract method that must be implemented by subclasses.

        Should contain the parsing logic specific to the target website.

        Returns:
            Union[Dict[str, Any], List[Dict[str, Any]]]:
                - A dictionary of parsed data.
                - Or a list of dictionaries if multiple entries are collected.
                  Each dictionary should include at least a key like 'data' or 'date'
                  if representing time-based entries.

        Example:
            {
                "date": "2025-11-11",
                "wagered": 1542.33,
                "profit": -32.12
            } OR {
                "data": [
                        {
                        "date": "2025-11-11",
                        "wagered": 1542.33,
                        "profit": -32.12
                    }
                ]
            }
        """
        pass