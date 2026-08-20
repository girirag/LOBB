from datetime import datetime
from typing import Optional
from pydantic import BaseModel, HttpUrl, Field, field_validator
import re

CUSTOM_CODE_REGEX = re.compile(r"^[a-zA-Z0-9_-]{3,32}$")


class ShortenRequest(BaseModel):
    url: HttpUrl = Field(..., description="The original long URL to shorten (e.g. https://example.com/long/path)")
    custom_code: Optional[str] = Field(
        default=None,
        min_length=3,
        max_length=32,
        description="Optional custom alias for the shortened URL",
        examples=["my-custom-link"]
    )

    @field_validator("custom_code")
    @classmethod
    def validate_custom_code(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            if not CUSTOM_CODE_REGEX.match(v):
                raise ValueError(
                    "custom_code must be 3-32 characters long and contain only alphanumeric characters, underscores, or hyphens."
                )
        return v


class ShortenResponse(BaseModel):
    short_code: str
    short_url: str
    original_url: str
    created_at: datetime

    model_config = {
        "from_attributes": True
    }


class StatsResponse(BaseModel):
    short_code: str
    original_url: str
    short_url: str
    clicks: int
    created_at: datetime

    model_config = {
        "from_attributes": True
    }


class HealthResponse(BaseModel):
    status: str
    database: str
