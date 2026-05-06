"""Source manifests and polite fetch placeholders for Mongolian data collection.

This script intentionally does not scrape by default. It creates auditable manifests
with source URL, license status, retrieval date, and allowed usage fields. Any fetch
implementation must respect robots.txt, rate limits, and licensing.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path


@dataclass(frozen=True)
class SourceManifest:
    name: str
    category: str
    source_url: str
    license_status: str
    allowed_usage: str
    retrieval_date: str
    notes: str
    fetch_enabled_by_default: bool = False


def default_manifests() -> list[SourceManifest]:
    today = date.today().isoformat()
    return [
        SourceManifest("General Mongolian public/open data", "general", "TBD", "verify_before_use", "manifest_only", today, "Add only sources with clear public/open licenses."),
        SourceManifest("Mongolian Wikipedia", "general", "https://mn.wikipedia.org/", "CC BY-SA; verify dump terms", "research_and_training_if_license_compliant", today, "Prefer official Wikimedia dumps over crawling pages."),
        SourceManifest("OSCAR Mongolian", "general", "https://oscar-project.org/", "verify_dataset_license", "research_and_training_if_license_compliant", today, "Use dataset access paths and license documentation."),
        SourceManifest("CC100 Mongolian", "general", "https://data.statmt.org/cc-100/", "verify_dataset_license", "research_and_training_if_license_compliant", today, "Deduplicate and filter quality before training."),
        SourceManifest("Common Crawl Mongolian candidates", "general", "https://commoncrawl.org/", "verify_page_level_rights", "filter_and_review_before_training", today, "Use URL-level license/robots checks and avoid copyrighted content."),
        SourceManifest("Public government/legal texts", "legal", "TBD government portals", "verify_public_sector_terms", "legal_review_required", today, "Store document-level license and retrieval metadata."),
        SourceManifest("Public library metadata/public-domain texts", "general", "TBD library sources", "public_domain_or_license_required", "only_where_rights_allow", today, "Do not ingest copyrighted books without license."),
        SourceManifest("Khan Bank website", "finance", "https://www.khanbank.com/", "copyrighted_public_site_verify", "benchmark_reference_only_until_licensed", today, "Respect robots.txt; do not scrape aggressively."),
        SourceManifest("TDB website", "finance", "https://www.tdbm.mn/", "copyrighted_public_site_verify", "benchmark_reference_only_until_licensed", today, "Respect robots.txt; do not scrape aggressively."),
        SourceManifest("Golomt Bank website", "finance", "https://www.golomtbank.com/", "copyrighted_public_site_verify", "benchmark_reference_only_until_licensed", today, "Respect robots.txt; do not scrape aggressively."),
        SourceManifest("XacBank website", "finance", "https://www.xacbank.mn/", "copyrighted_public_site_verify", "benchmark_reference_only_until_licensed", today, "Respect robots.txt; do not scrape aggressively."),
        SourceManifest("State Bank website", "finance", "https://www.statebank.mn/", "copyrighted_public_site_verify", "benchmark_reference_only_until_licensed", today, "Respect robots.txt; do not scrape aggressively."),
    ]


def write_manifest(output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as handle:
        for source in default_manifests():
            handle.write(json.dumps(asdict(source), ensure_ascii=False) + "\n")


def polite_fetch_placeholder(manifest_path: Path) -> None:
    raise SystemExit(
        "Fetching is disabled by default. Review licenses, robots.txt, rate limits, "
        f"and allowed_usage in {manifest_path} before implementing a source-specific fetcher."
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("datasets/processed/source_manifest.jsonl"))
    parser.add_argument("--fetch", action="store_true", help="Reserved for audited source-specific fetchers.")
    args = parser.parse_args()
    write_manifest(args.output)
    if args.fetch:
        polite_fetch_placeholder(args.output)
    print(f"Wrote source manifest to {args.output}")


if __name__ == "__main__":
    main()
