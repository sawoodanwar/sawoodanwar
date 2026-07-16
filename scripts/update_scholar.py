#!/usr/bin/env python3
"""
Automatically fetches publications and citation counts from Google Scholar
and updates the Publications & Citations table in README.md.

Scheduled via GitHub Actions every Monday.
"""

import re
import time
from scholarly import scholarly, ProxyGenerator

SCHOLAR_USER_ID = "Z2kACpkAAAAJ"
README_PATH = "README.md"

# Section markers in README.md
SECTION_START = "## \ud83d\udcc4 Publications & Citations"
SECTION_END = "---"


def fetch_scholar_data(user_id: str) -> dict:
    """Fetch author profile and publications from Google Scholar."""
    try:
        author = scholarly.search_author_id(user_id)
        author = scholarly.fill(author, sections=["basics", "publications"])
        return author
    except Exception as e:
        print(f"Primary fetch failed: {e}. Retrying with free proxy...")
        try:
            pg = ProxyGenerator()
            pg.FreeProxies()
            scholarly.use_proxy(pg)
            time.sleep(5)
            author = scholarly.search_author_id(user_id)
            author = scholarly.fill(author, sections=["basics", "publications"])
            return author
        except Exception as e2:
            print(f"Proxy fetch also failed: {e2}")
            return None


def build_publications_table(publications: list) -> str:
    """Build a Markdown table from the list of publications."""
    rows = []
    for pub in publications:
        bib = pub.get("bib", {})
        title = bib.get("title", "Untitled")
        authors = bib.get("author", "")
        venue = bib.get("venue", "") or bib.get("journal", "") or bib.get("booktitle", "")
        year = bib.get("pub_year", "") or bib.get("year", "")
        cited_by = pub.get("num_citations", 0)
        citation_id = pub.get("author_pub_id", "")

        # Build Scholar citation link
        if citation_id:
            link = f"https://scholar.google.com/citations?view_op=view_citation&hl=en&user={SCHOLAR_USER_ID}&citation_for_view={SCHOLAR_USER_ID}:{citation_id}"
            title_cell = f"[{title}]({link})"
        else:
            title_cell = title

        cited_cell = f"**{cited_by}**" if cited_by and int(cited_by) > 0 else "\u2014"
        rows.append(f"| {title_cell} | {authors} | {venue} | {cited_cell} | {year} |")

    header = (
        "| Title | Authors | Venue | Cited by | Year |\n"
        "|---|---|---|---|---|\n"
    )
    return header + "\n".join(rows)


def update_readme(new_table: str, total_citations: int) -> bool:
    """Replace the Publications & Citations section in README.md."""
    with open(README_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    # Build the new section block
    new_section = (
        f"{SECTION_START}\n\n"
        f"> **Total citations: {total_citations}** · "
        f"Auto-updated via [Google Scholar](https://scholar.google.com/citations?user={SCHOLAR_USER_ID}&hl=en)\n\n"
        f"{new_table}\n"
    )

    # Use regex to replace everything between section markers
    pattern = re.compile(
        rf"({re.escape(SECTION_START)}).*?(?=\n---)",
        re.DOTALL
    )

    if pattern.search(content):
        new_content = pattern.sub(new_section.rstrip(), content)
        if new_content == content:
            print("No changes detected in README.")
            return False
        with open(README_PATH, "w", encoding="utf-8") as f:
            f.write(new_content)
        print(f"README updated successfully. Total citations: {total_citations}")
        return True
    else:
        print("Could not find the Publications section marker in README.md.")
        return False


def main():
    print(f"Fetching Google Scholar data for user: {SCHOLAR_USER_ID}")
    author = fetch_scholar_data(SCHOLAR_USER_ID)

    if not author:
        print("Failed to fetch Scholar data. Exiting without changes.")
        return

    publications = author.get("publications", [])
    total_citations = author.get("citedby", 0)

    print(f"Found {len(publications)} publications. Total citations: {total_citations}")

    # Sort by year descending
    publications.sort(
        key=lambda p: int(p.get("bib", {}).get("pub_year", 0) or 0),
        reverse=True
    )

    table = build_publications_table(publications)
    update_readme(table, total_citations)


if __name__ == "__main__":
    main()
