"""
Pydantic schemas for language preferences
"""
from pydantic import BaseModel, Field


class LanguageUpdate(BaseModel):
    """Schema for updating language preference"""

    language: str = Field(
        "en",
        pattern=r"^[a-z]{2}$",
        description="Language code (en, fr, etc.)"
    )


class LanguageResponse(BaseModel):
    """Response schema for language preference"""

    language: str = Field(..., description="Current language setting")
    available_languages: list[str] = Field(
        default_factory=lambda: ["en", "fr"],
        description="List of available languages"
    )
