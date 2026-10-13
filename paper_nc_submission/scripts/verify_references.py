#!/usr/bin/env python3
from __future__ import annotations

import csv
import html
import json
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
OUT_BIB = PACKAGE_ROOT / "references_verified.bib"
OUT_CSV = PACKAGE_ROOT / "reference_verification.csv"
OUT_MD = PACKAGE_ROOT / "reference_verification.md"

CROSSREF = "https://api.crossref.org/works/{doi}"
USER_AGENT = "SCRS-NC-reference-verifier/1.0 (mailto:research@example.com)"

DOI_REFS = [
    ("hardin1968tragedy", "10.1126/science.162.3859.1243"),
    ("axelrod1981evolution", "10.1126/science.7466396"),
    ("fehr2002altruistic", "10.1038/415137a"),
    ("hauert2002volunteering", "10.1126/science.1070582"),
    ("nowak1992spatial", "10.1038/359826a0"),
    ("nowak2006five", "10.1126/science.1133755"),
    ("ohtsuki2006simple", "10.1038/nature04605"),
    ("santos2005scale", "10.1103/PhysRevLett.95.098104"),
    ("santos2008social", "10.1038/nature06940"),
    ("szabo2007evolutionary", "10.1016/j.physrep.2007.04.004"),
    ("roca2009evolutionary", "10.1016/j.plrev.2009.08.001"),
    ("perc2010coevolutionary", "10.1016/j.biosystems.2009.10.003"),
    ("perc2013evolutionary", "10.1098/rsif.2012.0997"),
    ("perc2017statistical", "10.1016/j.physrep.2017.05.004"),
    ("traulsen2007pairwise", "10.1016/j.jtbi.2007.01.002"),
    ("hofbauer2003evolutionary", "10.1090/S0273-0979-03-00988-1"),
    ("rand2013human", "10.1016/j.tics.2013.06.003"),
    ("levin2014public", "10.1073/pnas.1400830111"),
    ("allen2017evolutionary", "10.1038/nature21723"),
    ("holme2012temporal", "10.1016/j.physrep.2012.03.001"),
    ("holme2015modern", "10.1140/epjb/e2015-60657-4"),
    ("perra2012activity", "10.1038/srep00469"),
    ("karsai2012universal", "10.1038/srep00397"),
    ("masuda2013temporal", "10.1103/PhysRevLett.111.188701"),
    ("scholtes2014causality", "10.1038/ncomms6024"),
    ("li2017fundamental", "10.1126/science.aai7488"),
    ("li2020evolution", "10.1038/s41467-020-16088-w"),
    ("benson2016higher", "10.1126/science.aad9029"),
    ("benson2018simplicial", "10.1073/pnas.1800683115"),
    ("battiston2020networks", "10.1016/j.physrep.2020.05.004"),
    ("battiston2021physics", "10.1038/s41567-021-01371-4"),
    ("iacopini2019simplicial", "10.1038/s41467-019-10431-6"),
    ("torres2021representations", "10.1137/20M1355896"),
    ("bick2023what", "10.1137/21M1414024"),
    ("alvarezrodriguez2021evolutionary", "10.1038/s41562-020-01024-1"),
    ("civilini2021evolutionary", "10.1103/PhysRevLett.127.268301"),
    ("gallo2024higherorder", "10.1038/s41467-024-48578-6"),
    ("malizia2025hyperedge", "10.1038/s41467-024-55506-1"),
    ("meng2024personalised", "10.1038/s41467-024-47380-8"),
    ("wang2024multiplayer", "10.1038/s41467-024-49505-5"),
    ("rossetti2025concurrent", "10.1038/s41467-025-56083-7"),
    ("wang2026strategy", "10.1073/pnas.2516380123"),
    ("cattuto2010dynamics", "10.1371/journal.pone.0011596"),
    ("stehle2011high", "10.1371/journal.pone.0023176"),
    ("fournet2014contact", "10.1371/journal.pone.0107878"),
    ("mastrandrea2015contact", "10.1371/journal.pone.0136497"),
    ("vanhems2013estimating", "10.1371/journal.pone.0073970"),
    ("isella2011crowd", "10.1016/j.jtbi.2010.11.033"),
    ("genois2015office", "10.1017/nws.2015.10"),
    ("sapiezynski2019interaction", "10.1038/s41597-019-0325-x"),
    ("wilkinson2016fair", "10.1038/sdata.2016.18"),
    ("harris2020array", "10.1038/s41586-020-2649-2"),
    ("virtanen2020scipy", "10.1038/s41592-019-0686-2"),
    ("hunter2007matplotlib", "10.1109/MCSE.2007.55"),
]

URL_REFS = [
    {
        "key": "cornellHigherOrderData",
        "title": "Higher-order network datasets",
        "author": "Austin R. Benson",
        "year": "2026",
        "url": "https://www.cs.cornell.edu/~arb/data/",
        "note": "Accessed 2026-09-02.",
    },
    {
        "key": "emailEuData",
        "title": "Email-Eu higher-order network dataset",
        "author": "Austin R. Benson",
        "year": "2026",
        "url": "https://www.cs.cornell.edu/~arb/data/email-Eu/",
        "note": "Accessed 2026-09-02.",
    },
    {
        "key": "emailEnronData",
        "title": "Email-Enron higher-order network dataset",
        "author": "Austin R. Benson",
        "year": "2026",
        "url": "https://www.cs.cornell.edu/~arb/data/email-Enron/",
        "note": "Accessed 2026-09-02.",
    },
    {
        "key": "congressBillsData",
        "title": "Congress bills higher-order network dataset",
        "author": "Austin R. Benson",
        "year": "2026",
        "url": "https://www.cs.cornell.edu/~arb/data/congress-bills/",
        "note": "Accessed 2026-09-02.",
    },
    {
        "key": "askUbuntuThreadsData",
        "title": "Threads-Ask-Ubuntu higher-order network dataset",
        "author": "Austin R. Benson",
        "year": "2026",
        "url": "https://www.cs.cornell.edu/~arb/data/threads-ask-ubuntu/",
        "note": "Accessed 2026-09-02.",
    },
    {
        "key": "sociopatternsData",
        "title": "SocioPatterns data sets",
        "author": "SocioPatterns Collaboration",
        "year": "2026",
        "url": "http://www.sociopatterns.org/datasets/",
        "note": "Accessed 2026-09-02.",
    },
]

PAGE_OVERRIDES = {
    # Crossref omits pages for this PNAS article; PMC/PubMed record E11221-E11230.
    "benson2018simplicial": "E11221-E11230",
}


def ascii_text(value: str) -> str:
    value = html.unescape(value)
    value = (
        value.replace("—", "--")
        .replace("–", "-")
        .replace("−", "-")
        .replace("“", '"')
        .replace("”", '"')
        .replace("’", "'")
        .replace("‘", "'")
    )
    normalized = unicodedata.normalize("NFKD", value)
    return normalized.encode("ascii", "ignore").decode("ascii")


def bib_escape(value: Any) -> str:
    text = ascii_text(str(value))
    return (
        text.replace("\\", "\\textbackslash{}")
        .replace("{", "\\{")
        .replace("}", "\\}")
        .replace("&", "\\&")
        .replace("%", "\\%")
        .replace("$", "\\$")
        .replace("#", "\\#")
        .replace("_", "\\_")
    )


def first(values: Any, default: str = "") -> str:
    if isinstance(values, list) and values:
        return str(values[0])
    if isinstance(values, str):
        return values
    return default


def date_parts(item: dict[str, Any]) -> list[int]:
    for field in ("published-print", "published-online", "published", "issued"):
        parts = item.get(field, {}).get("date-parts")
        if parts and parts[0]:
            return [int(part) for part in parts[0]]
    return []


def date_string(parts: list[int]) -> str:
    if not parts:
        return ""
    if len(parts) == 1:
        return f"{parts[0]:04d}"
    if len(parts) == 2:
        return f"{parts[0]:04d}-{parts[1]:02d}"
    return f"{parts[0]:04d}-{parts[1]:02d}-{parts[2]:02d}"


def format_author(person: dict[str, Any]) -> str:
    if "family" in person:
        given = ascii_text(str(person.get("given", ""))).strip()
        family = ascii_text(str(person.get("family", ""))).strip()
        return f"{given} {family}".strip()
    if "name" in person:
        return ascii_text(str(person["name"]))
    return ""


def format_authors(item: dict[str, Any]) -> str:
    authors = [format_author(author) for author in item.get("author", [])]
    authors = [author for author in authors if author]
    return " and ".join(authors)


def fetch_crossref(doi: str) -> dict[str, Any]:
    quoted = urllib.parse.quote(doi, safe="")
    req = urllib.request.Request(
        CROSSREF.format(doi=quoted),
        headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
    )
    last_error: Exception | None = None
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                payload = json.loads(response.read().decode("utf-8"))
            return payload["message"]
        except urllib.error.HTTPError as exc:
            last_error = exc
            if exc.code != 429 or attempt == 3:
                raise
            time.sleep(2.0 * (attempt + 1))
        except urllib.error.URLError as exc:
            last_error = exc
            if attempt == 3:
                raise
            time.sleep(1.0 * (attempt + 1))
    raise RuntimeError(f"Crossref lookup failed for {doi}: {last_error!r}")


def bib_type(item: dict[str, Any]) -> str:
    kind = item.get("type", "misc")
    if kind in {"journal-article", "proceedings-article"}:
        return "article"
    if kind == "book":
        return "book"
    if kind == "book-chapter":
        return "incollection"
    return "misc"


def report_text(value: Any) -> str:
    return html.unescape(str(value)).replace("|", "/")


def format_bib_entry(key: str, item: dict[str, Any]) -> str:
    parts = date_parts(item)
    fields: list[tuple[str, str]] = []
    fields.append(("title", first(item.get("title"))))
    authors = format_authors(item)
    if authors:
        fields.append(("author", authors))
    if parts:
        fields.append(("year", str(parts[0])))
    journal = first(item.get("container-title"))
    if journal:
        fields.append(("journal", journal))
    if item.get("volume"):
        fields.append(("volume", str(item["volume"])))
    if item.get("issue"):
        fields.append(("number", str(item["issue"])))
    page = item.get("page") or PAGE_OVERRIDES.get(key)
    if page:
        fields.append(("pages", str(page)))
    article_number = item.get("article-number")
    if article_number:
        fields.append(("eid", str(article_number)))
    fields.append(("doi", str(item["DOI"]).lower()))
    url = item.get("URL")
    if url:
        fields.append(("url", str(url)))

    body = [f"@{bib_type(item)}{{{key},"]
    for name, value in fields:
        if value:
            body.append(f"  {name} = {{{bib_escape(value)}}},")
    body.append("}")
    return "\n".join(body)


def format_misc_entry(entry: dict[str, str]) -> str:
    body = [f"@misc{{{entry['key']},"]
    for field in ("title", "author", "year", "url", "note"):
        body.append(f"  {field} = {{{bib_escape(entry[field])}}},")
    body.append("}")
    return "\n".join(body)


def main() -> None:
    rows: list[dict[str, str]] = []
    bib_entries: list[str] = []

    for idx, (key, doi) in enumerate(DOI_REFS, start=1):
        try:
            item = fetch_crossref(doi)
            parts = date_parts(item)
            row = {
                "key": key,
                "type": "doi",
                "status": "ok",
                "doi": str(item.get("DOI", doi)).lower(),
                "title": report_text(first(item.get("title"))),
                "container": report_text(first(item.get("container-title"))),
                "year": str(parts[0]) if parts else "",
                "date": date_string(parts),
                "volume": str(item.get("volume", "")),
                "issue": str(item.get("issue", "")),
                "pages": str(item.get("page") or item.get("article-number") or PAGE_OVERRIDES.get(key, "")),
                "url": str(item.get("URL", f"https://doi.org/{doi}")),
                "error": "",
            }
            bib_entries.append(format_bib_entry(key, item))
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, KeyError) as exc:
            row = {
                "key": key,
                "type": "doi",
                "status": "failed",
                "doi": doi.lower(),
                "title": "",
                "container": "",
                "year": "",
                "date": "",
                "volume": "",
                "issue": "",
                "pages": "",
                "url": f"https://doi.org/{doi}",
                "error": repr(exc),
            }
        rows.append(row)
        if idx < len(DOI_REFS):
            time.sleep(0.15)

    for entry in URL_REFS:
        rows.append(
            {
                "key": entry["key"],
                "type": "url",
                "status": "manual_url",
                "doi": "",
                "title": entry["title"],
                "container": "",
                "year": entry["year"],
                "date": "",
                "volume": "",
                "issue": "",
                "pages": "",
                "url": entry["url"],
                "error": "",
            }
        )
        bib_entries.append(format_misc_entry(entry))

    with OUT_CSV.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    OUT_BIB.write_text("\n\n".join(bib_entries) + "\n", encoding="utf-8")

    ok = sum(row["status"] == "ok" for row in rows)
    failed = [row for row in rows if row["status"] == "failed"]
    md = [
        "# Reference Verification",
        "",
        "Reference metadata was fetched from the Crossref Works API on 2026-09-02 where a DOI is listed. Dataset pages without DOIs are recorded as manual URL entries with access date 2026-09-02.",
        "",
        f"- DOI references checked: {len(DOI_REFS)}",
        f"- DOI references verified: {ok}",
        f"- DOI references failed: {len(failed)}",
        f"- Manual URL references: {len(URL_REFS)}",
        "",
        "| Key | Status | DOI/URL | Year | Venue | Pages/Article | Title |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        doi_or_url = row["doi"] if row["doi"] else row["url"]
        md.append(
            "| {key} | {status} | {doi_or_url} | {year} | {container} | {pages} | {title} |".format(
                key=row["key"],
                status=row["status"],
                doi_or_url=doi_or_url,
                year=row["year"],
                container=report_text(row["container"]),
                pages=row["pages"],
                title=report_text(row["title"]),
            )
        )
    if failed:
        md.extend(["", "## Failed DOI Checks", ""])
        for row in failed:
            md.append(f"- {row['key']}: {row['doi']} ({row['error']})")
    OUT_MD.write_text("\n".join(md) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
