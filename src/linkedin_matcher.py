from urllib.parse import urlparse

from src.schemas import LeadershipMember


class LinkedInMatcher:

    @staticmethod
    def match(
        leadership: list[LeadershipMember],
        linkedin_urls: list[str],
    ) -> list[LeadershipMember]:

        profile_urls = [
            url
            for url in linkedin_urls
            if LinkedInMatcher._is_profile_url(url)
        ]

        for person in leadership:

            name_parts = [
                part.lower()
                for part in person.name.split()
                if len(part) > 2
            ]

            if not name_parts:
                continue

            best_url = None
            best_score = 0

            for url in profile_urls:

                slug = LinkedInMatcher._get_profile_slug(url)

                normalized_slug = (
                    slug
                    .replace("-", "")
                    .replace("_", "")
                    .lower()
                )

                score = sum(
                    1
                    for part in name_parts
                    if part.replace("-", "").lower()
                    in normalized_slug
                )

                if score > best_score:
                    best_score = score
                    best_url = url

            required_matches = min(
                2,
                len(name_parts),
            )

            if best_score >= required_matches:
                person.linkedin_url = best_url

        return leadership

    @staticmethod
    def _is_profile_url(url: str) -> bool:

        try:
            parsed = urlparse(url)

            return (
                parsed.netloc.lower().endswith(
                    "linkedin.com"
                )
                and "/in/" in parsed.path.lower()
            )

        except Exception:
            return False

    @staticmethod
    def _get_profile_slug(url: str) -> str:

        parsed = urlparse(url)

        return (
            parsed.path
            .rstrip("/")
            .split("/")[-1]
        )