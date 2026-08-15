"""
The polite scraper — entry point.
Run with: python src/main.py
"""
from crawler import discover_book_urls


def main() -> None:
    book_urls = discover_book_urls()
    print(book_urls[0])
    print(book_urls[-1])


if __name__ == "__main__":
    main()