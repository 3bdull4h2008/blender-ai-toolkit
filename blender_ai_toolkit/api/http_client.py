"""HTTP client for API calls using only Python stdlib (no external deps)."""
import json
import urllib.request
import urllib.error
import ssl
import time
from typing import Any, Dict, Optional


class HTTPClient:
    """Singleton HTTP client with timeout, retry, and JSON support."""

    def __init__(self, timeout: int = 60, max_retries: int = 3):
        self.timeout = timeout
        self.max_retries = max_retries
        self._ssl_ctx = ssl.create_default_context()

    def request(
        self,
        method: str,
        url: str,
        data: Optional[Dict] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[int] = None,
        raw_response: bool = False,
    ) -> Dict[str, Any]:
        """Make an HTTP request with retry logic.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            url: Full URL
            data: Optional dict to send as JSON body
            headers: Optional extra headers
            timeout: Optional override for timeout
            raw_response: If True, return raw bytes instead of JSON

        Returns:
            Parsed JSON dict or raw bytes
        """
        if headers is None:
            headers = {}
        if timeout is None:
            timeout = self.timeout

        body = None
        if data is not None:
            body = json.dumps(data).encode("utf-8")
            headers.setdefault("Content-Type", "application/json")

        last_error = None
        for attempt in range(self.max_retries):
            try:
                req = urllib.request.Request(
                    url, data=body, headers=headers, method=method
                )
                resp = urllib.request.urlopen(
                    req, timeout=timeout, context=self._ssl_ctx
                )
                resp_body = resp.read()

                if raw_response:
                    return {"status": resp.status, "data": resp_body}

                if resp_body:
                    return json.loads(resp_body.decode("utf-8"))
                return {}

            except urllib.error.HTTPError as e:
                last_error = e
                error_body = ""
                try:
                    error_body = e.read().decode("utf-8", errors="replace")
                except Exception:
                    pass

                # Don't retry on client errors (4xx except 429)
                if 400 <= e.code < 500 and e.code != 429:
                    return {
                        "error": True,
                        "status": e.code,
                        "message": str(e),
                        "detail": error_body,
                    }

                # Retry on 429 (rate limit) and 5xx
                wait = min(2 ** attempt * 1, 30)
                time.sleep(wait)

            except (urllib.error.URLError, OSError, TimeoutError) as e:
                last_error = e
                wait = min(2 ** attempt * 1, 30)
                time.sleep(wait)

        return {
            "error": True,
            "message": str(last_error) if last_error else "Unknown error",
        }

    def get(self, url: str, headers: Optional[Dict] = None, **kwargs) -> Dict:
        return self.request("GET", url, headers=headers, **kwargs)

    def post(self, url: str, data: Optional[Dict] = None, headers: Optional[Dict] = None, **kwargs) -> Dict:
        return self.request("POST", url, data=data, headers=headers, **kwargs)

    def put(self, url: str, data: Optional[Dict] = None, headers: Optional[Dict] = None, **kwargs) -> Dict:
        return self.request("PUT", url, data=data, headers=headers, **kwargs)

    def delete(self, url: str, headers: Optional[Dict] = None, **kwargs) -> Dict:
        return self.request("DELETE", url, headers=headers, **kwargs)

    def download(self, url: str, dest_path: str, headers: Optional[Dict] = None) -> bool:
        """Download a file to disk."""
        try:
            result = self.get(url, headers=headers, raw_response=True)
            if "error" in result:
                return False
            with open(dest_path, "wb") as f:
                f.write(result["data"])
            return True
        except Exception:
            return False


# Global singleton
_http_client: Optional[HTTPClient] = None


def get_http_client() -> HTTPClient:
    global _http_client
    if _http_client is None:
        _http_client = HTTPClient()
    return _http_client
