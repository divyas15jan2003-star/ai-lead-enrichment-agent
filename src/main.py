import asyncio
import json
from pathlib import Path

from src.crawler import WebsiteCrawler
from src.context_builder import ContextBuilder
from src.extractor import CompanyExtractor
from src.confidence import ConfidenceScorer
from src.linkedin_matcher import LinkedInMatcher
from src.linkedin_search import LinkedInSearcher
from src.usage_tracker import UsageTracker


DOMAINS_FILE = Path("domains.json")
OUTPUT_FILE = Path("output/output.json")
USAGE_FILE = Path("output/usage.json")


async def process_company(
    domain: str,
    crawler: WebsiteCrawler,
    context_builder: ContextBuilder,
    extractor: CompanyExtractor,
    scorer: ConfidenceScorer,
    linkedin_searcher: LinkedInSearcher,
):
    print("\n" + "=" * 70)
    print(f"PROCESSING: {domain}")
    print("=" * 70)

    try:
        # ---------------------------------------------------------
        # 1. Crawl website
        # ---------------------------------------------------------
        pages = await crawler.crawl(domain)

        print(f"✓ Crawled pages: {len(pages)}")

        if not pages:
            return {
                "domain": domain,
                "company_overview": "",
                "target_audience": "",
                "contact_points": [],
                "leadership": [],
                "confidence_score": 0.0,
                "sources": [],
            }

        # ---------------------------------------------------------
        # 2. Build cleaned context
        # ---------------------------------------------------------
        context = context_builder.build_context(pages)

        print(
            f"✓ Context size: {len(context)} characters"
        )

        # ---------------------------------------------------------
        # 3. LLM extraction
        # ---------------------------------------------------------
        extracted = extractor.extract(
            domain=domain,
            context=context,
        )

        # ---------------------------------------------------------
        # 4. Discover LinkedIn URLs from company website
        # ---------------------------------------------------------
        linkedin_urls = crawler.extract_linkedin_urls(
            pages
        )

        print(
            f"✓ LinkedIn URLs discovered: "
            f"{len(linkedin_urls)}"
        )

        # ---------------------------------------------------------
        # 5. Match website LinkedIn URLs to leadership
        # ---------------------------------------------------------
        extracted.leadership = LinkedInMatcher.match(
            extracted.leadership,
            linkedin_urls,
        )

        # ---------------------------------------------------------
        # 6. External LinkedIn search for missing profiles
        # ---------------------------------------------------------
        company_name = domain.split(".")[0].title()

        extracted.leadership = linkedin_searcher.enrich(
            leadership=extracted.leadership,
            company_name=company_name,
            domain=domain,
        )

        print("✓ LLM extraction completed")

        # ---------------------------------------------------------
        # 7. Confidence scoring
        # ---------------------------------------------------------
        confidence = scorer.calculate(
            data=extracted,
            crawled_pages=len(pages),
        )

        print(
            f"✓ Confidence score: {confidence}"
        )

        # ---------------------------------------------------------
        # 8. Build final output
        # ---------------------------------------------------------
        result = extracted.model_dump()

        result["domain"] = domain
        result["confidence_score"] = confidence

        return result

    except Exception as exc:

        print(
            f"⚠ Failed to process {domain}: {exc}"
        )

        # ---------------------------------------------------------
        # Graceful failure
        # ---------------------------------------------------------
        return {
            "domain": domain,
            "company_overview": "",
            "target_audience": "",
            "contact_points": [],
            "leadership": [],
            "confidence_score": 0.0,
            "sources": [],
            "error": str(exc),
        }


async def main():

    # -------------------------------------------------------------
    # 1. Load domains
    # -------------------------------------------------------------
    with open(
        DOMAINS_FILE,
        "r",
        encoding="utf-8",
    ) as file:

        domains = json.load(file)

    # -------------------------------------------------------------
    # 2. Initialize components
    # -------------------------------------------------------------
    crawler = WebsiteCrawler(
        max_pages=6,
        timeout_ms=30_000,
    )

    context_builder = ContextBuilder(
        max_context_characters=24_000,
    )

    # Token usage tracker
    usage_tracker = UsageTracker()

    # LLM extractor
    extractor = CompanyExtractor(
        usage_tracker=usage_tracker,
    )

    # Confidence scorer
    scorer = ConfidenceScorer()

    # External LinkedIn search
    linkedin_searcher = LinkedInSearcher()

    # -------------------------------------------------------------
    # 3. Process companies
    # -------------------------------------------------------------
    results = []

    for domain in domains:

        result = await process_company(
            domain=domain,
            crawler=crawler,
            context_builder=context_builder,
            extractor=extractor,
            scorer=scorer,
            linkedin_searcher=linkedin_searcher,
        )

        results.append(result)

    # -------------------------------------------------------------
    # 4. Create output directory
    # -------------------------------------------------------------
    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    # -------------------------------------------------------------
    # 5. Save company output
    # -------------------------------------------------------------
    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            results,
            file,
            indent=2,
            ensure_ascii=False,
        )

    # -------------------------------------------------------------
    # 6. Get usage summary
    # -------------------------------------------------------------
    usage = usage_tracker.summary()

    # -------------------------------------------------------------
    # 7. Save usage information
    # -------------------------------------------------------------
    with open(
        USAGE_FILE,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            usage,
            file,
            indent=2,
        )

    # -------------------------------------------------------------
    # 8. Final summary
    # -------------------------------------------------------------
    print("\n" + "=" * 70)
    print("FINAL PIPELINE COMPLETE")
    print("=" * 70)

    print(
        f"✓ Companies processed: {len(results)}"
    )

    print(
        f"✓ Output saved to: {OUTPUT_FILE}"
    )

    print("\n" + "=" * 70)
    print("LLM USAGE")
    print("=" * 70)

    print(
        f"✓ LLM calls: "
        f"{usage['llm_calls']}"
    )

    print(
        f"✓ Input tokens: "
        f"{usage['input_tokens']}"
    )

    print(
        f"✓ Output tokens: "
        f"{usage['output_tokens']}"
    )

    print(
        f"✓ Total tokens: "
        f"{usage['total_tokens']}"
    )

    print(
        f"✓ Estimated cost: "
        f"${usage['estimated_cost_usd']:.6f}"
    )

    print(
        f"✓ Usage saved to: {USAGE_FILE}"
    )


if __name__ == "__main__":
    asyncio.run(main())