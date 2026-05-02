"""Low-level Binance USD-M Futures Testnet REST client with HMAC signing."""

from __future__ import annotations

import hashlib
import hmac
import logging
import os
import time
from typing import Any
from urllib.parse import urlencode

import requests

logger = logging.getLogger(__name__)

DEFAULT_BASE_URL = "https://testnet.binancefuture.com"


class MissingCredentialsError(Exception):
    """API key or secret not configured."""


class BinanceAPIError(Exception):
    """Binance returned a business or HTTP error."""

    def __init__(self, message: str, *, status_code: int | None = None, payload: Any = None):
        super().__init__(message)
        self.status_code = status_code
        self.payload = payload


class BinanceFuturesClient:
    """Signed REST client for Binance USD-M Futures (testnet by default)."""

    def __init__(
        self,
        api_key: str | None = None,
        api_secret: str | None = None,
        base_url: str | None = None,
        recv_window: int = 5000,
        timeout: float = 30.0,
    ) -> None:
        self.api_key = api_key or os.environ.get("BINANCE_API_KEY", "08F1OufC3N3SLsXgQLarwHgEdUiQyT1tQGTP1RHiiK5Br9jJm0bS2a6p9ENJUx8k").strip()
        self.api_secret = api_secret or os.environ.get("BINANCE_API_SECRET", "l10uWLRaf34mtjTfo74UKm1VI3jQydWsoHAbfevdxg8LAR4jJhH2cINAJOFHEtLz").strip()
        self.base_url = (base_url or os.environ.get("BINANCE_FUTURES_BASE_URL") or DEFAULT_BASE_URL).rstrip(
            "/"
        )
        self.recv_window = recv_window
        self.timeout = timeout
        self._session = requests.Session()

    def require_credentials(self) -> None:
        if not self.api_key or not self.api_secret:
            raise MissingCredentialsError(
                "Set BINANCE_API_KEY and BINANCE_API_SECRET environment variables "
                "(Futures Testnet API credentials)."
            )

    def _sign(self, query_string: str) -> str:
        return hmac.new(
            self.api_secret.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

    def signed_request(
        self,
        method: str,
        path: str,
        params: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Send a signed request. Params should not include signature or timestamp.
        """
        self.require_credentials()

        p = {k: v for k, v in params.items() if v is not None and v != ""}
        p["timestamp"] = int(time.time() * 1000)
        p["recvWindow"] = self.recv_window

        query_string = urlencode(sorted((str(k), str(v)) for k, v in p.items()))
        signature = self._sign(query_string)
        full_query = f"{query_string}&signature={signature}"
        url = f"{self.base_url}{path}?{full_query}"

        headers = {"X-MBX-APIKEY": self.api_key}
        method_u = method.upper()

        logger.info("API %s %s", method_u, path)
        logger.debug("Request params (without secret): %s", p)

        try:
            resp = self._session.request(
                method_u,
                url,
                headers=headers,
                timeout=self.timeout,
            )
        except requests.RequestException as e:
            logger.exception("Network error calling %s %s", method_u, path)
            raise BinanceAPIError(f"Network failure: {e}") from e

        body: Any
        try:
            body = resp.json()
        except ValueError:
            body = resp.text

        if resp.status_code >= 400:
            msg = self._format_error(body, resp.status_code)
            logger.error("API error %s: %s", resp.status_code, msg)
            raise BinanceAPIError(msg, status_code=resp.status_code, payload=body)

        if not isinstance(body, dict):
            logger.warning("Unexpected non-JSON object response")
            raise BinanceAPIError("Unexpected response format from API.", status_code=resp.status_code)

        err_code = body.get("code")
        if isinstance(err_code, int) and err_code < 0:
            msg = self._format_error(body, resp.status_code)
            logger.error("Binance error payload: %s", body)
            raise BinanceAPIError(msg, status_code=resp.status_code, payload=body)

        logger.info("API %s %s succeeded (HTTP %s)", method_u, path, resp.status_code)
        logger.debug("Response body: %s", body)
        return body

    @staticmethod
    def _format_error(body: Any, status_code: int) -> str:
        if isinstance(body, dict):
            code = body.get("code")
            msg = body.get("msg", str(body))
            return f"HTTP {status_code}, code={code}: {msg}"
        return f"HTTP {status_code}: {body}"

    def close(self) -> None:
        self._session.close()
