# The polite scraper

A small, polite scraping pipeline for **Books to Scrape** (`books.toscrape.com`):
downloads the first 3 catalogue pages, visits all 60 book pages, turns the messy
HTML into clean, schema-validated JSON, survives a broken page without crashing,
and ends every run with an honest report.

## Target classification

- **Site:** `books.toscrape.com`
- **Why:** the site itself, on `toscrape.com`, states it is a sandbox built
  specifically so people can practise web scraping on it. It is not a real
  bookshop; nothing here is production data.
- **Scope:** the first 3 catalogue pages only (`page-1.html` → `page-3.html`,
  following the site's own "next" link), plus the ~60 individual book pages
  those 3 catalogue pages link to. No other pages, no other site.
- **Data collected:** title, product URL, price, availability, star rating,
  description — all publicly rendered on the page, nothing behind a login.
- **robots.txt result:** requested `https://books.toscrape.com/robots.txt`
  once — the file does not exist (HTTP 404). A missing file is not permission
  by itself, but combined with the site's own stated purpose as a public
  practice sandbox, scraping it is appropriate here.

I will not reuse this code on another site without checking its rules and
terms first.

## Status

- [x] Stage 0 — classify scraping target
- [x] Stage 1 — fetch and cache HTML
- [x] Stage 2 — discover three catalogue pages
- [x] Stage 3 — extract book details
- [x] Stage 4 — validate normalized records
- [x] Stage 5 — survive failures, report the run
- [x] Stage 6 — publish scraper evidence

## How to run it

```bash
git clone https://github.com/joaofmsilva/polite-scraper.git
cd scraper
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cd src
python main.py
```

This produces `output/books.json`, `output/errors.json` and
`output/run-report.json`. Re-running is safe — it reads pages from
`cache/` instead of re-hitting the site, and always writes exactly the
same 60 records (idempotent).

- **Language / lane:** Python 3.10+, `requests` + `BeautifulSoup` + `pydantic`.
- To repeat the Stage 5 "survives a broken page" check:
  `BREAK_TEST=1 python main.py` (macOS/Linux) or
  `$env:BREAK_TEST="1"; python main.py` (PowerShell).

## Record schema

Each entry in `output/books.json`:

| Field | Type | Notes |
|---|---|---|
| `title` | string | |
| `product_url` | string (URL) | canonical identity of the record |
| `price_text` | string | original text, e.g. `"£51.77"` |
| `price_gbp` | number | cleaned, sortable numeric price |
| `availability_text` | string | e.g. `"In stock (22 available)"` |
| `rating_text` | string \| null | e.g. `"Three"` |
| `description` | string \| null | `null` when the page had none — never invented |
| `source_page` | string (URL) | which catalogue page linked to this book (provenance) |
| `fetched_at` | string (ISO 8601) | when this page was fetched (provenance) |

Records that fail this schema are written to `output/errors.json` with a
reason instead of being stored.

## Politeness rules

- **User-agent:** every request identifies itself as
  `FlyRankInternshipA9/1.0 (+link to this repo)`.
- **Timeout:** every request gives up after 10 seconds — never waits forever.
- **Delay:** at least 500 ms between real requests to the site; cached
  pages need no delay since they never leave the computer.
- **Cache:** every page is saved to `cache/` on first fetch, and read
  from there on every later run.
- **Retries:** a timeout or a `5xx` gets exactly one retry, after a short
  pause. A `404` or `403` is never retried.
- **Scope:** only the first 3 catalogue pages and the book pages they
  link to — nothing else on the site is touched.

## Sample run report

```json
{
  "start_time": "2026-08-19T16:59:37.457020+00:00",
  "duration_seconds": 72.58,
  "pages_fetched": 0,
  "cache_hits": 1050,
  "valid_records": 1000,
  "invalid_records": 0,
  "failed_pages": 0,
  "failed_page_details": []
}
```

## Why no browser was needed

The book data (title, price, availability, rating, description) is
already present in the HTML the server sends back on the very first
request — it doesn't get added later by JavaScript. Opening a real
browser (e.g. with Playwright) to render the page would only add startup
cost and memory for no extra data, so a plain HTTP request is enough here.

## Ethics note

- Prefer an official API over scraping whenever one exists — this site
  is a practice sandbox with no API, built for scraping practice.
- Never bypass logins, paywalls, CAPTCHAs, or explicit blocks.
- Collect only the fields actually needed for the task, and only from
  the pages actually needed (3 catalogue pages + their linked books).
- Identify the scraper honestly (real user-agent) so a site owner can
  always tell who is visiting and why.

## Known limitation

TODO: Work on unit tests for the normalizer.
