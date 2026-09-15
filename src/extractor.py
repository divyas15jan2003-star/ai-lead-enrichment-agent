import json
import re

from groq import Groq

from src.config import GROQ_API_KEY, GROQ_MODEL
from src.schemas import ExtractedCompanyData
from src.usage_tracker import UsageTracker


class CompanyExtractor:
    def __init__(
        self,
        api_key=GROQ_API_KEY,
        model=GROQ_MODEL,
        usage_tracker: UsageTracker | None = None,
    ):
        self.client = Groq(api_key=api_key)
        self.model = model
        self.usage_tracker = usage_tracker

    def extract(
        self,
        domain: str,
        context: str,
    ) -> ExtractedCompanyData:

        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(
            domain,
            context,
        )

        # ---------------------------------------------------------
        # LLM request
        # ---------------------------------------------------------
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": user_prompt,
                },
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "company_extraction",
                    "schema": ExtractedCompanyData.model_json_schema(),
                },
            },
            temperature=0,
        )

        # ---------------------------------------------------------
        # Track token usage
        # ---------------------------------------------------------
        if response.usage and self.usage_tracker:

            self.usage_tracker.record(
                input_tokens=response.usage.prompt_tokens,
                output_tokens=response.usage.completion_tokens,
            )

        # ---------------------------------------------------------
        # Read LLM response
        # ---------------------------------------------------------
        content = response.choices[0].message.content

        if not content:
            raise ValueError(
                "LLM returned empty output."
            )

        # ---------------------------------------------------------
        # Parse JSON
        # ---------------------------------------------------------
        try:

            data = json.loads(content)

        except json.JSONDecodeError as exc:

            raise ValueError(
                "LLM returned invalid JSON."
            ) from exc

        # ---------------------------------------------------------
        # Validate structured output
        # ---------------------------------------------------------
        result = ExtractedCompanyData.model_validate(
            data
        )

        # ---------------------------------------------------------
        # Filter invalid email addresses
        # ---------------------------------------------------------
        return self._filter_emails(result)

    @staticmethod
    def _build_system_prompt() -> str:

        return """
You are a company intelligence extraction agent.

Your task is to extract factual company information
from the supplied public website content.

STRICT RULES:

1. Use ONLY information contained in the supplied website context.
2. Do NOT invent, guess, or assume company information.
3. If information is unavailable, return an empty list or empty string.
4. Company overview must be concise and approximately two sentences.
5. Identify the target audience / ideal customer profile only
   when supported by evidence in the supplied content.
6. Extract only generic or public contact email addresses
   that actually appear in the supplied content.
7. Do NOT include phone numbers, physical addresses,
   contact forms, or other non-email contact information.
8. Extract leadership or team members only when their names
   and roles are supported by the supplied content.
9. For each leadership member, include the URL of the supplied
   website page that supports their name and role in the
   "source" field.
10. Include LinkedIn URLs only when they actually appear
    in the supplied content.
11. Do not fabricate LinkedIn URLs.
12. Sources must contain URLs from the supplied context that
    support the extracted information.
13. Do not use outside knowledge.
14. Return only the requested structured data.
""".strip()

    @staticmethod
    def _build_user_prompt(
        domain: str,
        context: str,
    ) -> str:

        return f"""
Extract structured company intelligence for:

COMPANY DOMAIN:
{domain}

WEBSITE CONTEXT:
{context}

Return the requested structured company profile.
""".strip()

    @staticmethod
    def _filter_emails(
        data: ExtractedCompanyData,
    ) -> ExtractedCompanyData:

        email_pattern = re.compile(
            r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
        )

        data.contact_points = [
            email.strip().lower()
            for email in data.contact_points
            if email_pattern.fullmatch(
                email.strip()
            )
        ]

        return data