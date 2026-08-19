from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, HttpUrl, field_validator

class Book(BaseModel):
    title: str
    product_url: HttpUrl          # canonical identity — must be a real absolute URL
    price_text: str               # original text kept side by side with the clean value
    price_gbp: float              # clean, numeric, sortable/comparable
    availability_text: str
    rating_text: Optional[str] = None
    description: Optional[str] = None   # None when the page had no description
    source_page: HttpUrl
    fetched_at: str

    @field_validator("title")
    @classmethod
    def title_not_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("title is empty")
        return value

    @field_validator("price_gbp")
    @classmethod
    def price_must_be_positive(cls, value: float) -> float:
        if value <= 0:
            raise ValueError(f"price_gbp must be positive, got {value}")
        return value