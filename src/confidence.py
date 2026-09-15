from src.schemas import ExtractedCompanyData


class ConfidenceScorer:

    def calculate(
        self,
        data: ExtractedCompanyData,
        crawled_pages: int,
    ) -> float:

        score = 0.0

        # Company overview
        if data.company_overview.strip():
            score += 0.20

        # Target audience
        if data.target_audience.strip():
            score += 0.20

        # Contact information
        if data.contact_points:
            score += 0.15

        # Leadership
        if data.leadership:
            score += 0.15

        # LinkedIn URLs
        linkedin_count = sum(
            1
            for person in data.leadership
            if person.linkedin_url
        )

        if linkedin_count > 0:
            score += 0.10

        # Sources
        if data.sources:
            score += 0.10

        # Crawl coverage
        if crawled_pages >= 5:
            score += 0.10
        elif crawled_pages >= 3:
            score += 0.05

        return round(min(score, 1.0), 2)