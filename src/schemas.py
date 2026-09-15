from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator

class LeadershipMember(BaseModel):
    name: str = Field(...)
    role: str = Field(...)
    linkedin_url: Optional[str] = Field(default=None)
    source: Optional[str] = Field(default=None)


class ExtractedCompanyData(BaseModel):
    company_overview: str = Field(...)
    target_audience: str = Field(...)
    contact_points: list[EmailStr] = Field(default_factory=list)
    leadership: list[LeadershipMember] = Field(default_factory=list)
    sources: list[str] = Field(default_factory=list)

    @field_validator("contact_points")
    @classmethod
    def remove_duplicate_emails(
        cls,
        emails: list[str],
    ) -> list[str]:

        return list(
            dict.fromkeys(
                email.strip().lower()
                for email in emails
                if email.strip()
            )
        )

    @field_validator("sources")
    @classmethod
    def remove_duplicate_sources(
        cls,
        sources: list[str],
    ) -> list[str]:

        return list(
            dict.fromkeys(
                source.strip()
                for source in sources
                if source.strip()
            )
        )


class CompanyProfile(BaseModel):
    domain: str = Field(...)
    company_overview: str = Field(...)
    target_audience: str = Field(...)
    contact_points: list[str] = Field(default_factory=list)
    leadership: list[LeadershipMember] = Field(default_factory=list)
    confidence_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
    )
    sources: list[str] = Field(default_factory=list)

    @field_validator("contact_points")
    @classmethod
    def remove_duplicate_emails(
        cls,
        emails: list[str],
    ) -> list[str]:

        return list(
            dict.fromkeys(
                email.strip().lower()
                for email in emails
                if email.strip()
            )
        )

    @field_validator("sources")
    @classmethod
    def remove_duplicate_sources(
        cls,
        sources: list[str],
    ) -> list[str]:

        return list(
            dict.fromkeys(
                source.strip()
                for source in sources
                if source.strip()
            )
        )