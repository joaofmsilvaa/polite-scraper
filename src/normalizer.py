"""
Stage 4 — Clean it, check it, store it.

Turns raw text fields into clean, typed values and validates the result
against the Book schema. A record that fails validation is set aside
with the reason — it never reaches books.json.
"""
from __future__ import annotations
import re
from pydantic import ValidationError
from models import Book

PRICE_PATTERN = re.compile(r"[\d.]+")

def parse_price_gbp(price_text: str) -> float:
    """
    "£51.77" -> 51.77

    Regex-extracts the numeric part rather than assuming a fixed prefix,
    so it survives currency symbols encoded oddly in the HTML.
    """
    match = PRICE_PATTERN.search(price_text)
    if match is None:
        raise ValueError(f"could not find a number in price_text: {price_text!r}")
    return float(match.group())


def normalize_and_validate(raw_record: dict) -> tuple[Book | None, str | None]:
    """
    Take one raw record (as produced by extractor.extract_book) and try to
    turn it into a validated Book.

    Returns (book, None) on success, or (None, reason) on failure —
    exactly one of the two is set.
    """
    try:
        price_gbp = parse_price_gbp(raw_record["price_text"])
        book = Book(
            title=raw_record["title"],
            product_url=raw_record["product_url"],
            price_text=raw_record["price_text"],
            price_gbp=price_gbp,
            availability_text=raw_record["availability_text"],
            rating_text=raw_record["rating_text"],
            description=raw_record["description"],
            source_page=raw_record["source_page"],
            fetched_at=raw_record["fetched_at"],
        )
        return book, None
    except (ValidationError, ValueError, KeyError) as exc:
        return None, str(exc)


def deduplicate_by_url(books: list[Book]) -> list[Book]:
    """
    product_url is each record's canonical identity. If the same book
    shows up twice, it counts once — this is what makes re-running the
    scraper idempotent instead of duplicating records.
    """
    seen: set[str] = set()
    unique: list[Book] = []
    for book in books:
        url = str(book.product_url)
        if url not in seen:
            seen.add(url)
            unique.append(book)
    return unique