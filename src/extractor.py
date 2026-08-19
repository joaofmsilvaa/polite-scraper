"""
Stage 3 — Extract the raw records.

Opens each book detail page and pulls out the 8 raw fields, keeping
provenance (source_page, fetched_at) on every record. Never invents a
value that wasn't on the page — missing description becomes None.
"""
from __future__ import annotations
from datetime import datetime, timezone
from bs4 import BeautifulSoup
from fetcher import fetch


def extract_book(product_url: str, source_page: str) -> dict:
    """
    Fetch one book detail page and return its raw record (8 fields).
    """
    html, _source = fetch(product_url)
    soup = BeautifulSoup(html, "html.parser")

    # Aim selectors at the product area, not the whole document.
    product_main = soup.select_one("div.product_main")

    title = product_main.select_one("h1").get_text(strip=True)

    price_text = product_main.select_one("p.price_color").get_text(strip=True)

    availability_text = product_main.select_one("p.availability").get_text(strip=True)

    # The star rating is encoded as a CSS class, e.g. <p class="star-rating Three">
    rating_tag = product_main.select_one("p.star-rating")
    rating_classes = rating_tag.get("class", []) if rating_tag else []
    # classes look like ["star-rating", "Three"] — the rating word is the second one
    rating_text = next((c for c in rating_classes if c != "star-rating"), None)

    # Some books have no description at all — store None, never invent text.
    description_tag = soup.select_one("#product_description ~ p")
    description = description_tag.get_text(strip=True) if description_tag else None

    return {
        "title": title,
        "product_url": product_url,
        "price_text": price_text,
        "availability_text": availability_text,
        "rating_text": rating_text,
        "description": description,
        "source_page": source_page,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }