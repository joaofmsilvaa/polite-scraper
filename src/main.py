"""
The polite scraper — entry point.
Run with: python src/main.py
"""
import json
from pathlib import Path

from crawler import discover_book_urls
from extractor import extract_book
from normalizer import deduplicate_by_url, normalize_and_validate

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)


def main() -> None:
    book_urls = discover_book_urls()

    valid_books = []
    errors = []

    for product_url, source_page in book_urls:
        raw_record = extract_book(product_url, source_page)
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

    print(f"\nvalid_records={len(valid_books)}  invalid_records={len(errors)}")
    print(f"wrote {books_path}")
    print(f"wrote {errors_path}")


if __name__ == "__main__":
    main()