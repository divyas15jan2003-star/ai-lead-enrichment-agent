from dataclasses import dataclass

from src.crawler import CrawledPage
from src.content_cleaner import ContentCleaner


@dataclass
class CleanedPage:
    url: str
    title: str
    content: str


class ContextBuilder:

    def __init__(
        self,
        cleaner: ContentCleaner | None = None,
        max_context_characters: int = 24_000,
    ):
        self.cleaner = cleaner or ContentCleaner()
        self.max_context_characters = max_context_characters

    def build_pages(self, pages):

        cleaned_pages = []

        for page in pages:

            content = self.cleaner.clean(page.html)

            if not content:
                continue

            cleaned_pages.append(
                CleanedPage(
                    url=page.url,
                    title=page.title,
                    content=content,
                )
            )

        return cleaned_pages

    def build_context(self, pages):

        cleaned_pages = self.build_pages(pages)

        sections = []

        for page in cleaned_pages:

            section = (
                "==================================================\n"
                f"SOURCE: {page.url}\n"
                f"TITLE: {page.title}\n"
                "==================================================\n\n"
                f"{page.content}"
            )

            sections.append(section)

        context = "\n\n".join(sections)

        # Keep the request safely below Groq's current token limit.
        if len(context) > self.max_context_characters:

            context = (
                context[:self.max_context_characters]
                + "\n\n[Context truncated for token efficiency]"
            )

        return context