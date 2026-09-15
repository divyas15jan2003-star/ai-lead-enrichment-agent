from urllib.parse import urlparse

from tavily import TavilyClient

from src.config import TAVILY_API_KEY
from src.schemas import LeadershipMember


class LinkedInSearcher:
    """
    Uses external web search to discover LinkedIn profiles
    for leadership/team members when the company website
    does not already provide a LinkedIn URL.
    """

    def __init__(self, api_key: str | None = TAVILY_API_KEY):
        if not api_key:
            raise RuntimeError(
                "TAVILY_API_KEY is not configured."
            )

        self.client = TavilyClient(api_key=api_key)

    def enrich(
        self,
        leadership: list[LeadershipMember],
        company_name: str,
        domain: str,
    ) -> list[LeadershipMember]:

        for person in leadership:

            # Do not search if we already have a LinkedIn URL.
            if person.linkedin_url:
                continue

            linkedin_url = self.search_person(
                name=person.name,
                company_name=company_name,
                domain=domain,
            )

            if linkedin_url:
                person.linkedin_url = linkedin_url

        return leadership

    def search_person(
        self,
        name: str,
        company_name: str,
        domain: str,
    ) -> str | None:

        query = (
            f'"{name}" "{company_name}" LinkedIn '
            f'site:linkedin.com/in'
        )

        try:
            response = self.client.search(
                query=query,
                max_results=5,
                search_depth="basic",
            )

        except Exception as exc:
            print(
                f"⚠ LinkedIn search failed for {name}: {exc}"
            )
            return None

        results = response.get("results", [])

        for result in results:

            url = result.get("url", "")

            if not self._is_linkedin_profile(url):
                continue

            if not self._name_matches_url(name, url):
                continue

            if not self._name_matches_result(name, result):
                continue

            if not self._result_matches_company(
                result=result,
                company_name=company_name,
                domain=domain,
            ):
                continue


            return self._normalize_url(url)

        return None

    @staticmethod
    def _is_linkedin_profile(url: str) -> bool:
        try:
            parsed = urlparse(url)

            hostname = parsed.netloc.lower()
            path = parsed.path.lower()

            return (
                hostname.endswith("linkedin.com")
                and "/in/" in path
            )

        except Exception:
            return False

    @staticmethod
    def _normalize_url(url: str) -> str:
        parsed = urlparse(url)

        return (
            f"https://www.linkedin.com"
            f"{parsed.path.rstrip('/')}"
        )

    @staticmethod
    def _result_matches_company(
        result: dict,
        company_name: str,
        domain: str,
    ) -> bool:

        text = " ".join(
            [
                str(result.get("title", "")),
                str(result.get("content", "")),
            ]
        ).lower()

        company = company_name.lower()
        domain_name = (
            domain.lower()
            .replace("www.", "")
            .split(".")[0]
        )

        return (
            company in text
            or domain_name in text
        )

    @staticmethod
    def _name_matches_url(name: str, url: str) -> bool:
        parsed = urlparse(url)

        slug = parsed.path.rstrip("/").split("/")[-1].lower()

        name_parts = [
            part.lower()
            for part in name.split()
            if len(part) > 2
        ]

        normalized_slug = (
            slug
            .replace("-", "")
            .replace("_", "")
            .replace(".", "")
        )

        matches = sum(
            1
            for part in name_parts
            if part.replace("-", "").replace(".", "") in normalized_slug
        )

        required_matches = min(2, len(name_parts))

        return matches >= required_matches

    @staticmethod
    def _name_matches_result(
        name: str,
        result: dict,
    ) -> bool:

        text = " ".join(
            [
                str(result.get("title", "")),
                str(result.get("content", "")),
            ]
        ).lower()

        name_parts = [
            part.lower()
            for part in name.split()
            if len(part) > 2
        ]

        return all(part in text for part in name_parts)