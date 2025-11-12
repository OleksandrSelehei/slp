import os
import time
import base64
import re
from typing import Optional, Tuple

# Google API imports
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

# HTML parsing (optional but recommended)
try:
    from bs4 import BeautifulSoup
    _HAS_BS4 = True
except Exception:
    _HAS_BS4 = False

from utils.logs.logs import logger


class GmailCodeFetcher:
    """
    Fetches login/verification codes from a Gmail inbox using the Gmail API.

    This class encapsulates the full flow:
      1) OAuth authentication (using credentials in ./credentials/)
      2) Searching for the latest matching message (by From + Subject)
      3) Extracting the email body (HTML preferred, then plain text)
      4) Parsing a verification code using robust heuristics
      5) Optional retry loop (wait for the email to arrive)
    """

    GMAIL_SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]
    CODE_REGEX = re.compile(r"\b(\d{4,8})\b")  # default: 4..8 digits

    def __init__(
        self,
        credentials_dir: str = "credentials",
        credentials_file: str = "credentials.json",
        token_file: str = "token.json",
        sender_email: str = "noreply@stake.com",
        subject_phrase: Optional[str] = "",
        newer_than: Optional[str] = "1h",
        retries: int = 3,
        retry_delay_sec: float = 2.0,
        return_as_int: Optional[bool] = False,
        save_last_html_to: Optional[str] = None,
    ):
        self.credentials_dir = credentials_dir
        self.credentials_path = os.path.join(credentials_dir, credentials_file)
        self.token_path = os.path.join(credentials_dir, token_file)

        self.sender_email = sender_email
        self.subject_phrase = subject_phrase
        self.newer_than = newer_than

        self.retries = max(1, retries)
        self.retry_delay_sec = max(0.0, retry_delay_sec)
        self.return_as_int = return_as_int
        self.save_last_html_to = save_last_html_to

        self._service = None  # lazy-built Gmail service

    def run(self) -> Optional[str]:
        """
        Orchestrates the full flow:
          - Build Gmail service
          - Try to locate the most recent matching message (with retry)
          - Extract the body (HTML preferred)
          - Parse and return the verification code

        Returns:
            The verification code as str or int (depending on 'return_as_int'),
            or None if not found.
        """
        logger.info("[GmailCodeFetcher] Starting run()")
        self._ensure_service()

        for attempt in range(1, self.retries + 1):
            logger.info(f"[GmailCodeFetcher] Attempt {attempt}/{self.retries}: searching for the email...")
            msg_id = self._get_latest_message_id()

            if msg_id:
                logger.info(f"[GmailCodeFetcher] Found message id: {msg_id}")
                mime, body = self._get_message_body(msg_id)
                if not body:
                    logger.warning("[GmailCodeFetcher] Could not extract message body; retrying if attempts remain.")
                else:
                    code = self._extract_code(body)
                    if code is not None:
                        code_out = int(code) if self.return_as_int else str(code)
                        logger.info(f"[GmailCodeFetcher] Code extracted: {code_out}")
                        return code_out
                    else:
                        logger.warning("[GmailCodeFetcher] Matching email found but code not detected; retrying if attempts remain.")
            else:
                logger.info("[GmailCodeFetcher] No matching email found yet.")

            if attempt < self.retries:
                time.sleep(self.retry_delay_sec)

        logger.warning("[GmailCodeFetcher] No code found after retries.")
        return None

    def _ensure_service(self) -> None:
        """
        Builds the Gmail API service using OAuth credentials & token.
        """
        if self._service:
            return

        if not os.path.exists(self.credentials_path):
            raise RuntimeError(
                f"Missing credentials file: {self.credentials_path}. "
                "Place your OAuth client JSON into the credentials directory."
            )

        creds = None
        if os.path.exists(self.token_path):
            creds = Credentials.from_authorized_user_file(self.token_path, self.GMAIL_SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                logger.info("[GmailCodeFetcher] Refreshing OAuth token...")
                creds.refresh(Request())
                os.makedirs(self.credentials_dir, exist_ok=True)
                with open(self.token_path, "w") as f:
                    f.write(creds.to_json())
            else:
                raise RuntimeError(
                    "OAuth token is missing or invalid. "
                    "Run your one-time authorization script to generate token.json."
                )

        self._service = build("gmail", "v1", credentials=creds)
        logger.info("[GmailCodeFetcher] Gmail service is ready.")

    def _build_query(self) -> str:
        parts = []
        if self.sender_email:
            parts.append(f'from:{self.sender_email}')
        if self.newer_than:
            parts.append(f'newer_than:{self.newer_than}')
        return " ".join(parts)

    def _get_latest_message_id(self) -> Optional[str]:
        query = self._build_query()
        res = self._service.users().messages().list(
            userId="me",
            q=query,
            maxResults=1,
            includeSpamTrash=False
        ).execute()
        msgs = res.get("messages", [])
        return msgs[0]["id"] if msgs else None

    def _get_message_body(self, msg_id: str) -> Tuple[Optional[str], Optional[str]]:
        msg = self._service.users().messages().get(
            userId="me",
            id=msg_id,
            format="full"
        ).execute()

        payload = msg.get("payload", {})
        mime, body = self._extract_best_body_from_payload(payload)
        return mime, body

    def _extract_best_body_from_payload(self, payload: dict) -> Tuple[Optional[str], Optional[str]]:
        if "parts" in payload:
            html = None
            plain = None
            for part in payload["parts"]:
                m, b = self._extract_best_body_from_payload(part)
                if m == "text/html" and b and not html:
                    html = b
                elif m == "text/plain" and b and not plain:
                    plain = b
            if html:
                return "text/html", html
            if plain:
                return "text/plain", plain
            return None, None

        mime = payload.get("mimeType")
        data = payload.get("body", {}).get("data")
        if not data:
            return None, None

        raw = base64.urlsafe_b64decode(data)
        try:
            from email import message_from_bytes
            em = message_from_bytes(raw)
            if em.is_multipart():
                html = None
                plain = None
                for p in em.walk():
                    ctype = p.get_content_type()
                    if ctype == "text/html" and not html:
                        html = p.get_payload(decode=True).decode("utf-8", errors="ignore")
                    elif ctype == "text/plain" and not plain:
                        plain = p.get_payload(decode=True).decode("utf-8", errors="ignore")
                if html:
                    return "text/html", html
                if plain:
                    return "text/plain", plain
                return None, None
            else:
                body = em.get_payload(decode=True)
                if body is None:
                    body = em.get_payload()
                    if isinstance(body, str):
                        return mime, body
                    return None, None
                return mime, body.decode("utf-8", errors="ignore")
        except Exception:
            return mime, raw.decode("utf-8", errors="ignore")

    def _extract_code(self, content: str) -> Optional[str]:
        if _HAS_BS4:
            soup = BeautifulSoup(content, "lxml")
            hint = soup.find(string=re.compile(r"(login|verification)\s+code", re.I))
            if hint:
                container = hint.parent or soup
                for node in container.find_all(True, limit=80):
                    txt = node.get_text(strip=True)
                    m = self.CODE_REGEX.search(txt)
                    if m:
                        return m.group(1)
            for tag in soup.select("td,div,p,span,strong,b,h1,h2,h3"):
                txt = tag.get_text(strip=True)
                if re.fullmatch(r"\d{4,8}", txt):
                    return txt
            text_all = soup.get_text(" ", strip=True)
            m = self.CODE_REGEX.search(text_all)
            if m:
                return m.group(1)
            return None
        m = self.CODE_REGEX.search(content)
        return m.group(1) if m else None

    def _save_body_for_debug(self, body: str, mime: Optional[str]) -> None:
        try:
            os.makedirs(os.path.dirname(self.save_last_html_to), exist_ok=True)
        except Exception:
            pass
        if mime != "text/html":
            body = f"<html><body><pre style='white-space:pre-wrap'>{body}</pre></body></html>"
        with open(self.save_last_html_to, "w", encoding="utf-8") as f:
            f.write(body)
        logger.info(f"[GmailCodeFetcher] Saved body to: {self.save_last_html_to}")


if __name__ == "__main__":
    fetcher = GmailCodeFetcher(
        credentials_dir="credentials",
        credentials_file="../credentials/credentials.json",
        token_file="../credentials/token.json",
        sender_email="noreply@stake.com",
        subject_phrase="Login to stake.com",
        newer_than="7d",
        retries=3,
        retry_delay_sec=2.0,
        return_as_int=False,
        save_last_html_to="last_email.html"
    )
    code = fetcher.run()
    logger.info(f"[MAIN] Result code: {code}")
