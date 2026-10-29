#!/usr/bin/env python3
"""Find and verify peer-reviewed studies on PubMed, for health and fitness claims.

    python3 ~/.claude/skills/gusto-research/scripts/studies.py search "creatine strength older adults"
    python3 ~/.claude/skills/gusto-research/scripts/studies.py search "sleep deprivation testosterone" --any-type
    python3 ~/.claude/skills/gusto-research/scripts/studies.py check 10.1007/s40279-021-01499-3 29564973 --abstract

search  PubMed, best match first. By default only systematic reviews, meta-analyses
        and randomized controlled trials in humans; --any-type drops that filter.
check   confirm a PMID or DOI is a real PubMed-indexed article: title, journal,
        year, publication types, and whether it was retracted. A DOI that is not
        in PubMed is looked up on Crossref and flagged. --abstract prints the
        abstract, to confirm the study says what the claim says.
"""
import argparse
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
CROSSREF = "https://api.crossref.org/works/"
STRONG = "(systematic review[pt] OR meta-analysis[pt] OR randomized controlled trial[pt]) AND humans[mh]"


def get(url, params=None, as_json=True):
    if params:
        url += "?" + urllib.parse.urlencode({**params, "tool": "gusto-research"})
    # NCBI allows 3 requests a second without an API key.
    time.sleep(0.35)
    with urllib.request.urlopen(url, timeout=30) as resp:
        body = resp.read().decode("utf-8", "replace")
    return json.loads(body) if as_json else body


def summaries(pmids):
    if not pmids:
        return []
    result = get(EUTILS + "esummary.fcgi", {"db": "pubmed", "id": ",".join(pmids), "retmode": "json"})["result"]
    return [result[p] for p in result.get("uids", [])]


def doi_of(summary):
    return next((a["value"] for a in summary.get("articleids", []) if a.get("idtype") == "doi"), "")


def describe(summary):
    types = summary.get("pubtype", [])
    retracted = "Retracted Publication" in types
    year = (summary.get("pubdate") or "")[:4]
    authors = summary.get("authors") or []
    first = authors[0]["name"] + (" et al." if len(authors) > 1 else "") if authors else "?"
    lines = [
        f"PMID {summary['uid']}  {year}  {summary.get('fulljournalname') or summary.get('source')}",
        f"  {first}: {summary.get('title')}",
        f"  types: {', '.join(types) or '?'}   doi: {doi_of(summary) or '-'}",
    ]
    if retracted:
        lines.append("  RETRACTED: do not cite")
    return "\n".join(lines)


def search(query, n, any_type):
    term = query if any_type else f"({query}) AND {STRONG}"
    ids = get(EUTILS + "esearch.fcgi", {"db": "pubmed", "term": term, "retmax": n, "sort": "relevance",
                                        "retmode": "json"})["esearchresult"]["idlist"]
    if not ids:
        print("no results" + ("" if any_type else "; try --any-type or broader words"))
    for summary in summaries(ids):
        print(describe(summary))


def pmid_for(identifier):
    if identifier.isdigit():
        return identifier
    found = get(EUTILS + "esearch.fcgi", {"db": "pubmed", "term": f"{identifier}[doi]", "retmode": "json"})
    ids = found["esearchresult"]["idlist"]
    return ids[0] if ids else None


def crossref(doi):
    try:
        work = get(CROSSREF + urllib.parse.quote(doi))["message"]
    except urllib.error.HTTPError:
        return f"{doi}: NOT FOUND in PubMed or Crossref; the DOI may be wrong"
    journal = (work.get("container-title") or ["?"])[0]
    year = (work.get("issued", {}).get("date-parts") or [[None]])[0][0]
    title = (work.get("title") or ["?"])[0]
    return (f"{doi}: NOT IN PUBMED. Crossref: {year}  {journal}  ({work.get('type')})\n  {title}\n"
            "  Only cite it if the journal is peer-reviewed and reputable; say why in the idea file.")


def check(identifiers, abstract):
    for identifier in identifiers:
        pmid = pmid_for(identifier)
        if not pmid:
            print(crossref(identifier))
            continue
        found = summaries([pmid])
        if not found or "error" in found[0]:
            print(f"{identifier}: NOT FOUND in PubMed")
            continue
        print(describe(found[0]))
        if abstract:
            text = get(EUTILS + "efetch.fcgi", {"db": "pubmed", "id": pmid, "rettype": "abstract",
                                                "retmode": "text"}, as_json=False)
            print("\n".join("    " + line for line in text.strip().splitlines()))
        print()


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    p_search = sub.add_parser("search")
    p_search.add_argument("query")
    p_search.add_argument("--n", type=int, default=10)
    p_search.add_argument("--any-type", action="store_true")
    p_check = sub.add_parser("check")
    p_check.add_argument("ids", nargs="+", help="PMIDs or DOIs")
    p_check.add_argument("--abstract", action="store_true")
    args = parser.parse_args()
    try:
        if args.command == "search":
            search(args.query, args.n, args.any_type)
        else:
            check(args.ids, args.abstract)
    except urllib.error.URLError as err:
        sys.exit(f"could not reach PubMed or Crossref: {err}")


if __name__ == "__main__":
    main()
