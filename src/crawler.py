import asyncio
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse, urlunparse

from playwright.async_api import (
    Browser,
    Page,
    TimeoutError as PlaywrightTimeoutError,
    async_playwright,
)


@dataclass
class CrawledPage:
    url: str
    title: str
    html: str


class WebsiteCrawler:

    RELEVANT_KEYWORDS = {
        "leadership": 15,
        "team": 14,
        "founders": 14,
        "founder": 13,
        "about": 12,
        "about-us": 12,
        "company": 10,
        "contact": 9,
        "contact-us": 9,
        "contact-sales": 8,
        "customers": 7,
        "solutions": 6,
        "pricing": 5,
        "careers": 3,
        "press": 2,
    }

    MAX_RETRIES = 2

    def __init__(
        self,
        max_pages: int = 6,
        timeout_ms: int = 30_000,
    ):
        self.max_pages = max_pages
        self.timeout_ms = timeout_ms

    async def crawl(self, domain: str) -> list[CrawledPage]:

        base_url = f"https://{domain}"

        async with async_playwright() as playwright:

            browser = await playwright.chromium.launch(
                headless=True
            )

            context = await browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 "
                    "(KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                )
            )

            try:
                pages = await self._crawl_site(
                    context,
                    base_url,
                    domain,
                )

                return pages

            finally:
                await browser.close()

    async def _crawl_site(
        self,
        context,
        base_url: str,
        domain: str,
    ) -> list[CrawledPage]:

        results: list[CrawledPage] = []

        page = await context.new_page()

        try:

            homepage = await self._fetch_page_with_retry(
                page,
                base_url,
            )

            if not homepage:
                print(f"⚠ Could not crawl homepage: {base_url}")
                return results

            results.append(homepage)

            final_url = homepage.url

            print(f"✓ Crawled: {base_url}")
            print(f"✓ Final website URL: {final_url}")

            # Discover internal links
            links = await self._discover_links(
                page,
                final_url,
                domain,
            )

            print(f"✓ Discovered {len(links)} internal links")

            # Select relevant pages
            relevant_urls = self._select_relevant_urls(
                links,
                max_pages=self.max_pages - 1,
            )

            print(
                f"✓ Selected {len(relevant_urls)} relevant pages"
            )

        finally:
            await page.close()

        # Crawl selected pages
        for url in relevant_urls:

            page = await context.new_page()

            try:

                result = await self._fetch_page_with_retry(
                    page,
                    url,
                )

                if result:
                    results.append(result)
                    print(f"✓ Crawled: {url}")

                else:
                    print(
                        f"⚠ Skipped unavailable page: {url}"
                    )

            finally:
                await page.close()

        return results

    async def _fetch_page_with_retry(
        self,
        page: Page,
        url: str,
    ) -> CrawledPage | None:

        for attempt in range(1, self.MAX_RETRIES + 1):

            try:

                response = await page.goto(
                    url,
                    wait_until="domcontentloaded",
                    timeout=self.timeout_ms,
                )

                if response is None:
                    print(
                        f"⚠ No response received: {url}"
                    )
                    return None

                status = response.status

                if status >= 400:

                    print(
                        f"⚠ HTTP {status}: {url}"
                    )

                    # Retry only temporary server errors
                    if status >= 500 and attempt < self.MAX_RETRIES:
                        await asyncio.sleep(attempt)
                        continue

                    return None

                # Allow JavaScript-rendered content to settle
                await page.wait_for_timeout(1000)

                title = await page.title()

                html = await page.content()

                return CrawledPage(
                    url=page.url,
                    title=title,
                    html=html,
                )

            except PlaywrightTimeoutError:

                print(
                    f"⚠ Timeout "
                    f"(attempt {attempt}/{self.MAX_RETRIES}): "
                    f"{url}"
                )

                if attempt < self.MAX_RETRIES:
                    await asyncio.sleep(attempt)
                    continue

                return None

            except Exception as exc:

                print(
                    f"⚠ Crawl error "
                    f"(attempt {attempt}/{self.MAX_RETRIES}): "
                    f"{url} -> {exc}"
                )

                if attempt < self.MAX_RETRIES:
                    await asyncio.sleep(attempt)
                    continue

                return None

        return None

    async def _discover_links(
        self,
        page: Page,
        base_url: str,
        domain: str,
    ) -> list[str]:

        try:

            links = await page.locator(
                "a[href]"
            ).evaluate_all(
                """
                elements => elements.map(
                    element => element.href
                )
                """
            )

        except Exception as exc:

            print(
                f"⚠ Link discovery failed: {exc}"
            )

            return []

        normalized_links = []

        for link in links:

            normalized = self._normalize_url(
                link,
                base_url,
            )

            if not normalized:
                continue

            hostname = urlparse(normalized).hostname

            if not hostname:
                continue

            if self._is_same_domain(
                hostname,
                domain,
            ):
                normalized_links.append(normalized)

        return list(dict.fromkeys(normalized_links))

    def _select_relevant_urls(
        self,
        urls: list[str],
        max_pages: int,
    ) -> list[str]:

        scored_urls = []

        for url in urls:

            score = self._score_url(url)

            if score > 0:
                scored_urls.append(
                    (score, url)
                )

        scored_urls.sort(
            key=lambda item: item[0],
            reverse=True,
        )

        return [
            url
            for _, url in scored_urls[:max_pages]
        ]

    def _score_url(self, url: str) -> int:

        parsed = urlparse(url)

        path = parsed.path.lower()

        score = 0

        for keyword, points in self.RELEVANT_KEYWORDS.items():

            if keyword in path:
                score += points

        # Prefer clean pages over URLs with query parameters
        if parsed.query:
            score -= 2

        return score

    @staticmethod
    def _is_same_domain(
        hostname: str,
        base_domain: str,
    ) -> bool:

        hostname = hostname.lower().removeprefix("www.")
        base_domain = (
            base_domain.lower().removeprefix("www.")
        )

        return hostname == base_domain

    @staticmethod
    def _normalize_url(
        url: str,
        base_url: str,
    ) -> str | None:

        if not url:
            return None

        url = urljoin(base_url, url)

        parsed = urlparse(url)

        if parsed.scheme not in {"http", "https"}:
            return None

        # Remove fragments
        parsed = parsed._replace(
            fragment=""
        )

        path = parsed.path.lower()

        ignored_extensions = (
            ".pdf",
            ".jpg",
            ".jpeg",
            ".png",
            ".gif",
            ".svg",
            ".webp",
            ".zip",
            ".mp4",
            ".mp3",
            ".css",
            ".js",
        )

        if path.endswith(ignored_extensions):
            return None

        return urlunparse(parsed)

    def extract_linkedin_urls(self, pages):
        """Extract LinkedIn URLs from crawled pages."""

        linkedin_urls = []

        for page in pages:
            try:
                from bs4 import BeautifulSoup

                soup = BeautifulSoup(page.html, "html.parser")

                for link in soup.find_all("a", href=True):
                    href = link["href"].strip()

                    if "linkedin.com/" in href.lower():
                        linkedin_urls.append(href)

            except Exception as exc:
                print(
                    f"⚠ LinkedIn extraction failed for {page.url}: {exc}"
                )

        # Remove duplicates while preserving order
        return list(dict.fromkeys(linkedin_urls))   
    

    async def discover_linkedin_links(
        self,
        pages: list[CrawledPage],
    ) -> list[str]:

        linkedin_urls = []

        for page_data in pages:

            page = None

            try:
                # This method works from already crawled HTML,
                # so no additional browser request is required.
                from bs4 import BeautifulSoup

                soup = BeautifulSoup(
                    page_data.html,
                    "html.parser",
                )

                for link in soup.find_all(
                    "a",
                    href=True,
                ):

                    href = link["href"].strip()

                    if "linkedin.com/" in href.lower():

                        linkedin_urls.append(href)

            except Exception as exc:

                print(
                    f"⚠ LinkedIn extraction failed for "
                    f"{page_data.url}: {exc}"
                )

        # Remove duplicates while preserving order
        return list(dict.fromkeys(linkedin_urls))

    
    