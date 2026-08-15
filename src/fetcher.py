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
import time
from pathlib import Path
from urllib.parse import quote
import requests

USER_AGENT = "FlyRankInternshipA9/1.0 (+https://github.com/joaofmsilvaa/scraper)"
TIMEOUT_SECONDS = 10
POLITE_DELAY_SECONDS = 0.5

CACHE_DIR = Path(__file__).resolve().parent.parent / "cache"
CACHE_DIR.mkdir(exist_ok=True)


def _cache_path_for(url: str) -> Path:
    """Turn a URL into a safe, unique filename inside cache/."""
    safe_name = quote(url, safe="") + ".html"
    return CACHE_DIR / safe_name


def fetch(url: str) -> tuple[str, str]:
    """
    Fetch a URL politely, using the on-disk cache when available.

    Returns (html, source) where source is "CACHE HIT" or "FETCH".
    Raises requests.HTTPError if the response is not a 200.
    Raises requests.Timeout if the site does not answer in time.
    """
    cache_path = _cache_path_for(url)

    if cache_path.exists():
        html = cache_path.read_text(encoding="utf-8")
        print(f"CACHE HIT  {url}  ({len(html)} bytes)")
        return html, "CACHE HIT"

    headers = {"User-Agent": USER_AGENT}
    response = requests.get(url, headers=headers, timeout=TIMEOUT_SECONDS)

    # Only a 200 means "here is your page" — anything else is a failed
    # fetch, not HTML to parse. This raises requests.HTTPError on 4xx/5xx.
    response.raise_for_status()

    html = response.text
    cache_path.write_text(html, encoding="utf-8")
    print(f"FETCH      {url}  ({len(html)} bytes)")

    # Be a polite guest: only real network requests get a delay.
    # Cached pages never leave the computer, so they skip this.
    time.sleep(POLITE_DELAY_SECONDS)

    return html, "FETCH"