"""
The polite scraper — entry point.
Run with: python src/main.py
"""
import json
import os
from datetime import datetime, timezone
from pathlib import Path

import requests

import fetcher
from crawler import discover_book_urls
from extractor import extract_book
from normalizer import deduplicate_by_url, normalize_and_validate

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)


def main() -> None:
    run_started_at = datetime.now(timezone.utc)

    book_urls = discover_book_urls()

    # Stage 5 checkpoint helper: set BREAK_TEST=1 to inject one made-up
    # book URL on purpose and prove the run survives it.
    if os.environ.get("BREAK_TEST") == "1":
        fake_url = "https://books.toscrape.com/catalogue/this-book-does-not-exist_9999/index.html"
        book_urls.append((fake_url, "manual-break-test"))
        print(f"BREAK TEST: injected fake URL {fake_url}")

    valid_books = []
    errors = []          # records that were fetched but failed validation
    failed_pages = []    # pages that could not even be fetched

    for product_url, source_page in book_urls:
        # Stage 5: one broken page must not kill the run. Every book is
        # handled independently — a failure here is logged and skipped,
        # never allowed to crash the whole loop.
        try:
            raw_record = extract_book(product_url, source_page)
        except (requests.RequestException, AttributeError) as exc:
            # RequestException: the network/HTTP layer failed (404, 403,
            # timeout after retry, etc).
            # AttributeError: the page loaded but didn't look like a book
            # page at all (e.g. selector found nothing) — also a failed page.
            print(f"FAILED PAGE  {product_url}  — {exc}")
            failed_pages.append({"url": product_url, "reason": str(exc)})
            continue

        book, reason = normalize_and_validate(raw_record)
        if book is not None:
            valid_books.append(book)
        else:
            errors.append({"product_url": product_url, "reason": reason})

    valid_books = deduplicate_by_url(valid_books)

    books_path = OUTPUT_DIR / "books.json"
    books_path.write_text(
        json.dumps([b.model_dump(mode="json") for b in valid_books], indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    errors_path = OUTPUT_DIR / "errors.json"
    errors_path.write_text(
        json.dumps(errors, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    run_finished_at = datetime.now(timezone.utc)
    report = {
        "start_time": run_started_at.isoformat(),
        "duration_seconds": round((run_finished_at - run_started_at).total_seconds(), 2),
        "pages_fetched": fetcher.stats["fetch"],
        "cache_hits": fetcher.stats["cache_hit"],
        "valid_records": len(valid_books),
        "invalid_records": len(errors),
        "failed_pages": len(failed_pages),
        "failed_page_details": failed_pages,
    }
    report_path = OUTPUT_DIR / "run-report.json"
    report_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(f"\nvalid_records={len(valid_books)}  invalid_records={len(errors)}  failed_pages={len(failed_pages)}")
    print(f"wrote {books_path}")
    print(f"wrote {errors_path}")
    print(f"wrote {report_path}")


if __name__ == "__main__":
    main()