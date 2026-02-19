"""
Tool: Fetcher – performs HTTP GET requests with proper encoding and compression handling.
"""
import random

import chardet
import httpx
from app.tools.base import Tool


class FetcherTool(Tool):
    """Fetches content from a URL with robust encoding and compression handling."""

    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36",
    ]

    def __init__(self, http_client: httpx.AsyncClient):
        self._http_client = http_client

    @property
    def name(self) -> str:
        return "fetcher"

    @property
    def description(self) -> str:
        return "Fetch the HTML content of a URL. Input should be a valid URL."

    async def execute(self, input_data: str) -> str:
        url = input_data.strip()
        if not url.startswith(("http://", "https://")):
            url = "https://" + url

        for attempt in range(2):
            user_agent = random.choice(self.USER_AGENTS)
            headers = {
                "User-Agent": user_agent,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate",
                "Connection": "keep-alive",
            }

            try:
                response = await self._http_client.get(url, headers=headers, follow_redirects=True, timeout=30.0)
                response.raise_for_status()

                # Get raw bytes
                content_bytes = response.content

                # DEBUG: Save first bytes for diagnostics
                import base64

                print(f"DEBUG: First 50 bytes (base64): {base64.b64encode(content_bytes[:50])}")

                # httpx should already decompress automatically, but we handle it explicitly

                # Detect encoding with chardet
                detection = chardet.detect(content_bytes)
                encoding = detection["encoding"] if detection and detection["confidence"] > 0.5 else "utf-8"

                try:
                    text = content_bytes.decode(encoding, errors="replace")
                except (LookupError, TypeError):
                    text = content_bytes.decode("utf-8", errors="replace")

                # If the text is still binary, it might be unhandled compression
                if len(text) > 0 and all(ord(c) < 128 for c in text[:100]):
                    # if looks like ASCII/valid text
                    pass
                else:
                    # Possibly compressed - attempt manual decompression
                    try:
                        # Attempt to decompress gzip
                        import gzip
                        from io import BytesIO

                        with gzip.GzipFile(fileobj=BytesIO(content_bytes)) as f:
                            decompressed = f.read()
                            text = decompressed.decode(encoding, errors="replace")
                    except:  # noqa: E722
                        pass  # If fail, maintain original text (could be unreadable)

                # Truncate
                if len(text) > 10000:
                    text = text[:10000] + "\n... (truncated)"

                return text

            except httpx.HTTPStatusError as e:
                if e.response.status_code == 403 and attempt == 0:
                    continue
                return f"HTTP Error {e.response.status_code}: {url}"
            except Exception as e:
                if attempt == 0:
                    continue
                return f"Error fetching {url}: {str(e)}"

        return f"Error: Failed to fetch {url} after multiple attempts."
