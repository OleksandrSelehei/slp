import asyncio
import json
import random
from typing import Union, Dict, Any, List, Iterable, Optional
from patchright.async_api import Response
from parsers.base_parser import BaseParser
from utils.logs.logs import logger


class StakeParser(BaseParser):
    """
    Parser class for Stake.com.

    Inherits from BaseParser and implements data extraction logic
    after successful authentication.
    Responsible for navigating required pages, parsing elements,
    and returning structured data as a dictionary or list of dictionaries.
    """

    @staticmethod
    def _matches_graphql(resp: Response, op_names: Iterable[str]) -> bool:
        """Returns True if the request is a POST /_api/graphql with matching operationName."""
        try:
            if not resp.url.endswith("/_api/graphql"):
                return False
            if resp.request.method != "POST":
                return False

            names = {n.strip().lower() for n in op_names}
            op = (resp.request.headers.get("x-operation-name") or "").strip().lower()
            if op and op in names:
                return True

            body = resp.request.post_data or ""
            for n in names:
                if f'"operationName":"{n}"' in body or f"query {n}" in body:
                    return True
            return False
        except Exception:
            return False

    @staticmethod
    async def _human_pause(min_ms: int = 180, max_ms: int = 420) -> None:
        await asyncio.sleep(random.uniform(min_ms, max_ms) / 1000.0)

    @staticmethod
    def _transform_referred_data_from_bet(data: dict) -> dict:
        """
        Convert Stake campaign data into a list of dictionaries with:
          - player_id: user's UUID
          - balance: value from balances.bet[0].value (default 0.0)
        """
        result = []
        users = (data.get("campaign") or {}).get("referredUserList") or []
        for u in users:
            player_id = u.get("userId")
            bet_list = ((u.get("balances") or {}).get("bet")) or []
            balance = 0.0
            if bet_list and isinstance(bet_list, list):
                first = bet_list[0] or {}
                v = first.get("value")
                if isinstance(v, (int, float)):
                    balance = round(float(v), 2)
            if player_id:
                result.append({"player_id": player_id, "balance": balance})
        return {'data': result}

    # ---------- core flow ----------

    async def run_referred_users_via_ui(
        self,
        op_names: Iterable[str] = ("Campaign",),
        appear_timeout_ms: int = 7000,   # element appearance timeout
        expect_timeout_ms: int = 20000,  # GraphQL response wait timeout
    ) -> Optional[Dict[str, Any]]:
        """
        UI flow:
          1) Click button[data-analytics="affiliate-link"] (may open a new tab)
          2) On the active page, click <a> with href containing '/affiliate/referred-users'
          3) Wrap the second click in expect_response and capture GraphQL payload
          4) Log and return payload['data']
        """
        # 1) Locate and click the “Affiliate” button
        affiliate_btn = self.page.locator('button[data-analytics="affiliate-link"]')
        await affiliate_btn.wait_for(state="visible", timeout=appear_timeout_ms)
        await self._human_pause()
        try:
            await affiliate_btn.click()
        except TimeoutError:
            # If the button disappears or rerenders — try force click
            await affiliate_btn.click(force=True)

        # Small delay to allow menu/content to render
        await self._human_pause(220, 520)

        # 2) Find the link to the referred users list.
        # Ignore locale prefix — match any <a> where href contains '/affiliate/referred-users'
        link = self.page.locator('a[href*="/affiliate/referred-users"]')
        await link.wait_for(state="visible", timeout=appear_timeout_ms)

        # 3) Wrap click in expect_response to capture GraphQL call
        predicate = lambda r: self._matches_graphql(r, op_names)

        try:
            async with self.page.expect_response(predicate, timeout=expect_timeout_ms) as resp_info:
                await self._human_pause()
                await link.click()  # this click should trigger GraphQL request(s)
            resp = await resp_info.value
            payload = await resp.json()
        except TimeoutError:
            # Fallback: if the request is slightly delayed
            await self._human_pause(350, 650)
            resp = await self.page.wait_for_response(predicate, timeout=expect_timeout_ms)
            payload = await resp.json()

        # 4) Log and return GraphQL data
        data = payload.get("data", {}) if isinstance(payload, dict) else {}
        logger.info("========== GRAPHQL DATA ==========")
        transformed = self._transform_referred_data_from_bet(data)
        logger.info(f"Transformed referred users: {transformed}")
        return transformed

    async def parse_data(self) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Main parsing entry point.
        Ensures session is active and runs referred users extraction via UI.
        """

        # Ensure session is active
        if not self.page:
            logger.info("Page not initialized. Starting session initialization...")
            await self.initialize_session()

            # Critical check: ensure session variables are valid
            if self.browser is None or self.context is None or self.page is None:
                logger.critical("Browser, context, or page is None after initialize_session()!")
                raise RuntimeError("Failed to initialize browser session: page/context/browser is None.")

        return await self.run_referred_users_via_ui()
