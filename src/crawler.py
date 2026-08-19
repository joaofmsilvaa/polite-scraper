"""
Stage 2 — Find all three pages.

Walks the catalogue starting at page-1.html, following the site's own
"next" link, and collects every book detail URL it finds along the way.
"""
from __future__ import annotations

from urllib.parse import urljoin

from bs4 import BeautifulSoup

from fetcher import fetch

START_URL = "https://books.toscrape.com/catalogue/page-1.html"


def discover_book_urls() -> list[tuple[str, str]]:
    """
    Follow the catalogue's own "next" link from page 1 until there isn't
    one, collecting every book link along the way.

    Returns a list of unique (book_url, source_catalogue_page) pairs —
    source_catalogue_page is kept for provenance in Stage 3.
    """
    all_pairs: list[tuple[str, str]] = []
    seen: set[str] = set()
    current_url = START_URL
    pages_visited = 0

    while current_url is not None:
        html, _source = fetch(current_url)
        soup = BeautifulSoup(html, "html.parser")
        pages_visited += 1

        # Every book on this catalogue page lives inside <article class="product_pod">
        for article in soup.select("article.product_pod"):
            link = article.select_one("h3 a")
            if link is None or not link.get("href"):
                continue
            # Links are relative (e.g. "../../a-light-in-the-attic_1000/index.html")
            # — always resolve with urljoin, never by gluing strings together.
            absolute_url = urljoin(current_url, link["href"])
            if absolute_url not in seen:
                seen.add(absolute_url)
                all_pairs.append((absolute_url, current_url))

        # Let the site tell us whether there is a next page — never hardcode it.
        next_link = soup.select_one("li.next a")
        if next_link is not None and next_link.get("href"):
            current_url = urljoin(current_url, next_link["href"])
        else:
            current_url = None

    print(f"catalogue_pages={pages_visited}  discovered={len(all_pairs)}  unique_urls={len(seen)}")
    return all_pairs