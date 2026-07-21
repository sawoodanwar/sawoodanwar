#!/usr/bin/env python3
"""
Fetches citation counts from Semantic Scholar and Crossref APIs
and writes them to citations.json in the repo root.

Scheduled via GitHub Actions every Monday at 06:00 UTC.
No scraping — uses only official public APIs.
"""

import json
import urllib.request
import urllib.error
from datetime import datetime, timezone

# --- Configuration ---
DOI_FRONTIERS = "10.3389/fsoc.2024.1379265"
SEMANTIC_SCHOLAR_API = "https://api.semanticscholar.org/graph/v1/paper/DOI:{doi}?fields=citationCount"
CROSSREF_API = "https://api.crossref.org/works/{doi}/transform/application/vnd.citationstyles.csl+json"
OUTPUT_PATH = "citations.json"


def fetch_json(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "sawoodanwar-citation-bot/1.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode())


def get_semantic_scholar_citations(doi: str) -> int:
    try:
        data = fetch_json(SEMANTIC_SCHOLAR_API.format(doi=doi))
        return data.get("citationCount", 0)
    except Exception as e:
        print(f"Semantic Scholar fetch failed: {e}")
        return 0


def get_crossref_citations(doi: str) -> int:
    try:
        data = fetch_json(CROSSREF_API.format(doi=doi))
        return data.get("is-referenced-by-count", 0)
    except Exception as e:
        print(f"Crossref fetch failed: {e}")
        return 0


def main():
    print("Fetching citation counts...")

    ss_count = get_semantic_scholar_citations(DOI_FRONTIERS)
    cr_count = get_crossref_citations(DOI_FRONTIERS)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    print(f"Semantic Scholar: {ss_count} | Crossref: {cr_count} | Date: {now}")

    output = {
        "frontiers2024": {
            "doi": DOI_FRONTIERS,
            "semanticScholar": ss_count,
            "crossref": cr_count,
            "lastUpdated": now
        }
    }

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)

    print(f"Written to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
