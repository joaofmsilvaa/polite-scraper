"""
Stage 1 — Fetch once, cache once.

Responsible for the ONLY thing allowed to touch the network:
- honest user-agent
- timeout
- status-code check
- on-disk cache so re-running the script during development never re-hits
  the site
"""
from __future__ import annotations

import hashlib
import time
from pathlib import Path

import requests

USER_AGENT = "FlyRankInternshipA9/1.0 (+https://github.com/joaofmsilvaa/polite-scraper)"
TIMEOUT_SECONDS = 10
POLITE_DELAY_SECONDS = 0.5
RETRY_DELAY_SECONDS = 1.0

CACHE_DIR = Path(__file__).resolve().parent.parent / "cache"
CACHE_DIR.mkdir(exist_ok=True)

# Simple run-wide counters, read by main.py when it writes the report.
stats = {"fetch": 0, "cache_hit": 0}


def _cache_path_for(url: str) -> Path:
    """
    Turn a URL into a short, fixed-length, filesystem-safe cache filename.

    Uses a hash instead of the raw (encoded) URL because some Books to
    Scrape titles are long enough that the encoded URL alone breaks the
    filename/path length limit on Windows.
    """
    digest = hashlib.sha256(url.encode("utf-8")).hexdigest()
    return CACHE_DIR / f"{digest}.html"


def _do_request(url: str) -> requests.Response:
    headers = {"User-Agent": USER_AGENT}
    return requests.get(url, headers=headers, timeout=TIMEOUT_SECONDS)


def fetch(url: str) -> tuple[str, str]:
    """
    Fetch a URL politely, using the on-disk cache when available.

    Returns (html, source) where source is "CACHE HIT" or "FETCH".
    Raises requests.HTTPError if the response is not a 200 (after any
    retry). Raises requests.Timeout if the site never answers in time.

    Retry policy: a timeout or a 5xx gets ONE retry after a short pause
    — the page may just be having a bad moment. A 404 (page doesn't
    exist) or 403 (site said no) is never retried — asking again either
    can't help or is rude.
    """
    cache_path = _cache_path_for(url)

    if cache_path.exists():
        html = cache_path.read_text(encoding="utf-8")
        print(f"CACHE HIT  {url}  ({len(html)} bytes)")
        stats["cache_hit"] += 1
        return html, "CACHE HIT"

    attempts_left = 2  # first try + one retry
    last_error: Exception | None = None

    while attempts_left > 0:
        attempts_left -= 1
        try:
            response = _do_request(url)
        except requests.Timeout as exc:
            last_error = exc
            if attempts_left > 0:
                print(f"TIMEOUT    {url}  — retrying in {RETRY_DELAY_SECONDS}s")
                time.sleep(RETRY_DELAY_SECONDS)
                continue
            raise

        if response.status_code == 200:
            html = response.text
            cache_path.write_text(html, encoding="utf-8")
            print(f"FETCH      {url}  ({len(html)} bytes)")
            stats["fetch"] += 1
            # Be a polite guest: only real network requests get a delay.
            time.sleep(POLITE_DELAY_SECONDS)
            return html, "FETCH"

        if response.status_code in (404, 403):
            # Never retry: 404 won't exist on a second try, 403 means "no".
            response.raise_for_status()

        if 500 <= response.status_code < 600 and attempts_left > 0:
            print(f"SERVER ERROR {response.status_code} {url} — retrying in {RETRY_DELAY_SECONDS}s")
            time.sleep(RETRY_DELAY_SECONDS)
            continue

        # Any other non-200 (or a 5xx with no attempts left): fail.
        response.raise_for_status()

    # Only reached if every attempt timed out.
    raise last_error