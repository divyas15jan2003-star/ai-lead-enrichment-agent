import re

from bs4 import BeautifulSoup


class ContentCleaner:
    """
    Converts raw webpage HTML into clean, LLM-friendly text.

    The cleaner removes technical and visual noise while
    preserving meaningful textual content such as headings,
    paragraphs, lists, emails, and team information.
    """

    REMOVE_TAGS = [
        "script",
        "style",
        "svg",
        "noscript",
        "iframe",
        "canvas",
        "template",
        "video",
        "audio",
    ]

    BOILERPLATE_TAGS = [
        "nav",
        "footer",
        "header",
    ]

    NOISE_PATTERNS = [
        r"^skip to main content$",
        r"^skip to content$",
        r"^cookie settings$",
        r"^accept cookies$",
        r"^privacy settings$",
    ]

    def __init__(
        self,
        max_characters: int = 24_000,
    ):
        self.max_characters = max_characters

    def clean(self, html: str) -> str:
        """
        Convert raw HTML into clean, structured text.
        """

        if not html:
            return ""

        soup = BeautifulSoup(
            html,
            "html.parser",
        )

        self._remove_unwanted_elements(soup)

        main_content = self._find_main_content(soup)

        text = self._extract_structured_text(
            main_content
        )

        text = self._remove_noise_lines(text)

        text = self._normalize_whitespace(text)

        text = self._remove_duplicate_lines(text)

        return self._limit_content(text)

    def _remove_unwanted_elements(
        self,
        soup: BeautifulSoup,
    ) -> None:
        """
        Remove HTML elements that do not provide useful
        information for company intelligence extraction.
        """

        for tag_name in self.REMOVE_TAGS:
            for tag in soup.find_all(tag_name):
                tag.decompose()

        for tag_name in self.BOILERPLATE_TAGS:
            for tag in soup.find_all(tag_name):
                tag.decompose()

    @staticmethod
    def _find_main_content(
        soup: BeautifulSoup,
    ):
        """
        Prefer semantic main/article content when available.

        Falls back to the body if a semantic content container
        cannot be found.
        """

        main = soup.find("main")

        if main:
            return main

        article = soup.find("article")

        if article:
            return article

        body = soup.find("body")

        if body:
            return body

        return soup

    @staticmethod
    def _extract_structured_text(
        container,
    ) -> str:
        """
        Extract meaningful text while preserving basic
        document structure.
        """

        lines: list[str] = []

        for element in container.find_all(
            [
                "h1",
                "h2",
                "h3",
                "h4",
                "p",
                "li",
                "blockquote",
            ]
        ):
            text = element.get_text(
                " ",
                strip=True,
            )

            # Fix words that may become concatenated when HTML
            # contains inline elements.
            text = re.sub(
                r"(?<=[a-z])(?=[A-Z])",
                " ",
                text,
            )

            if text:
                lines.append(text)

        # If the page has very little semantic content,
        # fall back to all visible text.
        if len(" ".join(lines)) < 200:
            fallback_text = container.get_text(
                separator="\n",
                strip=True,
            )

            return fallback_text

        return "\n".join(lines)

    def _remove_noise_lines(
        self,
        text: str,
    ) -> str:
        """Remove known navigation/accessibility noise."""

        lines = text.splitlines()

        cleaned_lines: list[str] = []

        for line in lines:
            normalized = line.strip().lower()

            if not normalized:
                continue

            if any(
                re.match(pattern, normalized)
                for pattern in self.NOISE_PATTERNS
            ):
                continue

            cleaned_lines.append(line.strip())

        return "\n".join(cleaned_lines)

    @staticmethod
    def _normalize_whitespace(
        text: str,
    ) -> str:
        """
        Normalize excessive whitespace without destroying
        useful line structure.
        """

        text = re.sub(
            r"[ \t]+",
            " ",
            text,
        )

        text = re.sub(
            r"\n{3,}",
            "\n\n",
            text,
        )

        return text.strip()

    @staticmethod
    def _remove_duplicate_lines(
        text: str,
    ) -> str:
        """
        Remove repeated lines while preserving order.
        """

        lines = text.splitlines()

        seen: set[str] = set()
        unique_lines: list[str] = []

        for line in lines:
            normalized = line.strip().lower()

            if not normalized:
                continue

            if normalized in seen:
                continue

            seen.add(normalized)
            unique_lines.append(line.strip())

        return "\n".join(unique_lines)

    def _limit_content(
        self,
        text: str,
    ) -> str:
        """
        Prevent extremely large content from being sent
        to the LLM.
        """

        if len(text) <= self.max_characters:
            return text

        return (
            text[:self.max_characters]
            + "\n\n[Content truncated]"
        )