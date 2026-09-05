"""Base asynchronous HTTP client with timeout, retry and secure logging."""

import asyncio
import logging
from typing import Any, Dict, Optional
import httpx

logger = logging.getLogger(__name__)


class BaseApiClient:
    """Reusable HTTP client wrapper using httpx.AsyncClient with limited retries."""

    def __init__(self, timeout: float = 30.0, max_retries: int = 3) -> None:
        self.timeout = httpx.Timeout(timeout, connect=20.0)
        self.max_retries = max_retries
        self._client: Optional[httpx.AsyncClient] = None

    async def get_client(self) -> httpx.AsyncClient:
        """Get or initialize the underlying AsyncClient."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=self.timeout, follow_redirects=True)
        return self._client


    async def close(self) -> None:
        """Close the underlying HTTP client session."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def request(
        self,
        method: str,
        url: str,
        *,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Any] = None,
        json: Optional[Any] = None,
    ) -> httpx.Response:
        """Execute async HTTP request with exponential backoff for transient errors."""
        client = await self.get_client()
        attempt = 0
        backoff = 1.0

        while attempt < self.max_retries:
            attempt += 1
            try:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=headers,
                    params=params,
                    data=data,
                    json=json,
                )
                # Retry on server errors or rate limits
                if response.status_code in (429, 500, 502, 503, 504):
                    if attempt < self.max_retries:
                        logger.warning(
                            "Transient HTTP %s from %s (Attempt %d/%d). Retrying in %.1fs...",
                            response.status_code,
                            url,
                            attempt,
                            self.max_retries,
                            backoff,
                        )
                        await asyncio.sleep(backoff)
                        backoff *= 2.0
                        continue
                return response
            except (httpx.ConnectError, httpx.ConnectTimeout, httpx.ReadTimeout, httpx.WriteTimeout, httpx.PoolTimeout) as exc:
                if attempt < self.max_retries:
                    logger.warning(
                        "Network error (%s: %s) when calling %s (Attempt %d/%d). Retrying in %.1fs...",
                        type(exc).__name__,
                        str(exc) or "timeout/connect failed",
                        url,
                        attempt,
                        self.max_retries,
                        backoff,
                    )
                    await asyncio.sleep(backoff)
                    backoff *= 2.0
                else:
                    logger.error("HTTP request failed after %d attempts: %s", self.max_retries, exc)
                    raise exc
            except Exception as e:
                logger.error("Unexpected HTTP error when calling %s: %s", url, e, exc_info=True)
                raise e

        raise httpx.RequestError(f"Failed to execute request to {url} after {self.max_retries} attempts.")
