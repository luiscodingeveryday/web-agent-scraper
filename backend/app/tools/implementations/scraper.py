# backend/app/tools/implementations/scraper.py
"""
Enterprise-grade Scraper Tool with JavaScript support via Playwright.
Now with reusable browser instance, intelligent waiting, content-type detection,
retries, URL validation, semantic extraction, and configurable limits.
"""

import asyncio
import logging
import random
import re
from typing import Dict, Optional
from urllib.parse import urlparse

import httpx
from app.core.config import settings
from app.tools.base import Tool
from bs4 import BeautifulSoup
from playwright.async_api import Browser, async_playwright
from playwright.async_api import TimeoutError as PlaywrightTimeout

logger = logging.getLogger(__name__)

# ---------- Configuration from settings ----------
MAX_LENGTH = settings.scraper_max_length
MIN_WORDS_QUALITY = settings.scraper_min_words_quality
MIN_WORDS_POOR = settings.scraper_min_words_poor
REQUEST_TIMEOUT = settings.scraper_timeout
RETRY_ATTEMPTS = settings.scraper_retry_attempts
USER_AGENTS = settings.user_agents
POLITE_DELAY = settings.scraper_polite_delay


# ---------- Browser Manager (Singleton) ----------
class BrowserManager:
    _instance: Optional["BrowserManager"] = None
    _playwright = None
    _browser: Optional[Browser] = None
    _lock = asyncio.Lock()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    async def get_browser(self) -> Browser:
        async with self._lock:
            if self._browser is None:
                logger.info("Launching shared Playwright browser...")
                self._playwright = await async_playwright().start()
                self._browser = await self._playwright.chromium.launch(
                    headless=True, args=["--disable-blink-features=AutomationControlled"]
                )
            return self._browser

    async def close(self):
        if self._browser:
            await self._browser.close()
            self._browser = None
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None


# ---------- Static Scraper ----------
class StaticScraper:
    def __init__(self, http_client: httpx.AsyncClient):
        self._http_client = http_client

    async def scrape(self, url: str) -> str:
        for attempt in range(1, RETRY_ATTEMPTS + 1):
            try:
                response = await self._http_client.get(
                    url,
                    follow_redirects=True,
                    timeout=REQUEST_TIMEOUT,
                    headers={"User-Agent": random.choice(USER_AGENTS)},
                )
                content_type = response.headers.get("content-type", "").lower()
                if "text/html" not in content_type and "application/xhtml" not in content_type:
                    logger.warning(f"Non-HTML content ({content_type}) at {url}")
                    return f"⚠️ The URL returned {content_type} content. Only HTML pages can be scraped."

                raw = response.text
                if self._looks_like_html(raw):
                    return self._extract_semantic_text(raw)
                return raw
            except (httpx.TimeoutException, httpx.NetworkError) as e:
                logger.warning(f"Static scrape attempt {attempt} failed for {url}: {e}")
                if attempt == RETRY_ATTEMPTS:
                    return f"❌ Failed to fetch URL after {RETRY_ATTEMPTS} attempts: {e}"
                await asyncio.sleep(2**attempt)
            except Exception as e:
                logger.exception(f"Unexpected error in static scrape of {url}")
                return f"❌ Unexpected error: {e}"

    def _looks_like_html(self, content: str) -> bool:
        start = content.strip()[:200].lower()
        indicators = ["<!doctype", "<html", "<head", "<body", "<div", "<p>"]
        return any(ind in start for ind in indicators)

    @staticmethod
    def _extract_semantic_text(html: str) -> str:
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style", "meta", "noscript", "iframe", "nav", "footer", "aside"]):
            tag.decompose()

        lines = []
        for element in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6", "p", "li", "div", "article", "section"]):
            text = element.get_text(strip=True)
            if not text:
                continue
            if element.name.startswith("h"):
                prefix = "#" * int(element.name[1]) + " "
                lines.append(f"\n{prefix}{text}")
            elif element.name == "li":
                lines.append(f"• {text}")
            elif element.name == "p":
                lines.append(f"\n{text}")
            else:
                lines.append(text)

        if len(lines) < 3:
            text = soup.get_text(separator="\n", strip=True)
        else:
            text = "\n".join(lines)

        text = StaticScraper._clean_whitespace(text)
        return StaticScraper._truncate(text)

    @staticmethod
    def _clean_whitespace(text: str) -> str:
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r" {2,}", " ", text)
        text = re.sub(r" +\n", "\n", text)
        text = re.sub(r"\n +", "\n", text)
        return text.strip()

    @staticmethod
    def _truncate(text: str) -> str:
        if len(text) > MAX_LENGTH:
            text = text[:MAX_LENGTH] + "\n\n... (content truncated)"
        return text


# ---------- JavaScript Scraper ----------
class JSScraper:
    def __init__(self):
        self._browser_manager = BrowserManager()

    async def scrape(self, url: str) -> str:
        browser = await self._browser_manager.get_browser()
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080}, user_agent=random.choice(USER_AGENTS)
        )
        page = await context.new_page()
        try:
            logger.info(f"JS scraping {url}")
            await page.goto(url, wait_until="domcontentloaded", timeout=REQUEST_TIMEOUT * 1000)
            try:
                await page.wait_for_load_state("networkidle", timeout=5000)
            except PlaywrightTimeout:
                logger.debug("networkidle timeout, continuing with current content")
            await page.wait_for_selector("body", timeout=5000)

            content_selectors = ["article", "main", "#content", ".content", "p"]
            for selector in content_selectors:
                try:
                    await page.wait_for_selector(selector, timeout=2000)
                    break
                except PlaywrightTimeout:
                    continue

            html = await page.content()
            return StaticScraper._extract_semantic_text(html)
        except PlaywrightTimeout as e:
            logger.warning(f"Timeout during JS scrape of {url}: {e}")
            return f"❌ Page load timeout: {url}"
        except Exception as e:
            logger.exception(f"Error in JS scrape of {url}")
            return f"❌ Error rendering page: {e}"
        finally:
            await context.close()


# ---------- Main Scraper Tool ----------
class ScraperTool(Tool):
    JS_HEAVY_SITES = {
        "youtube.com",
        "facebook.com",
        "twitter.com",
        "x.com",
        "instagram.com",
        "linkedin.com",
        "tiktok.com",
        "netflix.com",
        "reddit.com",
        "discord.com",
        "medium.com",
    }

    def __init__(self, http_client: httpx.AsyncClient):
        self._http_client = http_client
        self._static_scraper = StaticScraper(http_client)
        self._js_scraper = JSScraper()
        self._domain_request_times: Dict[str, float] = {}

    @property
    def name(self) -> str:
        return "scraper"

    @property
    def description(self) -> str:
        return (
            "Advanced web scraper that extracts clean text from ANY website, "
            "including JavaScript-heavy sites. Input: full URL."
        )

    async def execute(self, input_data: str) -> str:
        url = self._normalize_url(input_data.strip())
        if not self._is_valid_url(url):
            return f"❌ Invalid URL: {input_data}"

        domain = urlparse(url).netloc
        await self._respect_politeness(domain)

        if self._is_js_heavy_domain(url):
            logger.info(f"Domain {domain} known JS-heavy, using JS mode")
            result = await self._js_scraper.scrape(url)
        else:
            logger.info(f"Trying static scrape for {domain}")
            result = await self._static_scraper.scrape(url)
            if self._result_needs_js(result):
                logger.info(f"Static result poor, upgrading to JS for {url}")
                result = await self._js_scraper.scrape(url)

        return result

    def _normalize_url(self, url: str) -> str:
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        return url

    def _is_valid_url(self, url: str) -> bool:
        parsed = urlparse(url)
        return all([parsed.scheme, parsed.netloc])

    def _is_js_heavy_domain(self, url: str) -> bool:
        domain = urlparse(url).netloc.lower()
        return any(site in domain for site in self.JS_HEAVY_SITES)

    def _result_needs_js(self, result: str) -> bool:
        if result.startswith("❌") or result.startswith("⚠️"):
            return False
        clean = result.strip()
        word_count = len(clean.split())
        return word_count < MIN_WORDS_POOR or any(
            phrase in clean.lower() for phrase in ["loading", "please enable javascript", "javascript required"]
        )

    async def _respect_politeness(self, domain: str):
        last = self._domain_request_times.get(domain)
        now = asyncio.get_event_loop().time()
        if last:
            elapsed = now - last
            if elapsed < POLITE_DELAY:
                wait = POLITE_DELAY - elapsed + random.uniform(0, 0.5)
                logger.debug(f"Delaying {wait:.2f}s for {domain}")
                await asyncio.sleep(wait)
        self._domain_request_times[domain] = now
