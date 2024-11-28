"""
Taxonomy Data Fetcher
=====================

This script fetches taxonomic data from NCBI Entrez for given taxon IDs or names.

Features:
- Accepts both taxon IDs and names as input.
- Automatically infers input type (ID or name).
- Fetches specified fields (lineage and/or ranks) from NCBI.
- Outputs data in text, JSON, or CSV format.
- Structured using classes for modularity and reusability.

Usage Examples:
---------------

1. Fetch Lineage and Ranks for Taxon ID 9606 (Human) in Text Format:
python taxonomy_fetcher.py 9606 --email your_email@example.com --fields lineage ranks

2. Fetch Lineage for "Escherichia coli" in JSON Format:
python taxonomy_fetcher.py "Escherichia coli" --email your_email@example.com --fields lineage --output-format json

3. Fetch Lineage for Multiple Taxon IDs and Output as CSV:
python taxonomy_fetcher.py 9606 10090 10116 --email your_email@example.com --fields lineage --output-format csv

4. Fetch Ranks for "Saccharomyces cerevisiae" and "Arabidopsis thaliana":
python taxonomy_fetcher.py "Saccharomyces cerevisiae" "Arabidopsis thaliana" --email your_email@example.com --fields ranks

5. Fetch Lineage and Ranks for Mixed Inputs (IDs and Names):
python taxonomy_fetcher.py 9606 "Mus musculus" 7227 --email your_email@example.com --fields lineage ranks

Replace your_email@example.com with your actual email address.
The script requires Biopython to be installed (pip install biopython).
"""

import argparse
import csv
import json
import sys
import time
from typing import Any, Dict, List

from Bio import Entrez


class TaxonRecord:
    """Class representing a single taxonomic record."""

    def __init__(self, record_data: Dict[str, Any]):
        self.record_data = record_data
        self.taxon_id = record_data.get("TaxId", "")
        self.scientific_name = record_data.get("ScientificName", "")
        self.rank = record_data.get("Rank", "")
        self.lineage = self._parse_lineage()
        self.ranks = self._parse_ranks()

    def _parse_lineage(self) -> List[str]:
        if "LineageEx" in self.record_data:
            lineage = [
                taxon["ScientificName"]
                for taxon in self.record_data["LineageEx"]
            ]
            lineage.append(self.scientific_name)
            return lineage
        else:
            return []

    def _parse_ranks(self) -> List[str]:
        if "LineageEx" in self.record_data:
            ranks = [taxon["Rank"] for taxon in self.record_data["LineageEx"]]
            ranks.append(self.rank)
            return ranks
        else:
            return []

    def get_field(self, field: str) -> Any:
        if field == "lineage":
            return self.lineage
        elif field == "ranks":
            return self.ranks
        else:
            return self.record_data.get(field, "")


class TaxonomyFetcher:
    """Class to fetch taxonomic data from NCBI Entrez."""

    def __init__(self, email: str, batch_size: int = 500, delay: float = 0.5):
        Entrez.email = email
        self.batch_size = batch_size
        self.delay = delay

    def resolve_taxon_names(self, taxon_names: List[str]) -> List[str]:
        """Resolve taxon names to IDs using Entrez.esearch."""
        taxon_ids = []
        for name in taxon_names:
            try:
                handle = Entrez.esearch(db="taxonomy", term=name)
                record = Entrez.read(handle)
                handle.close()
                ids = record.get("IdList", [])
                if ids:
                    taxon_ids.append(ids[0])
                else:
                    print(f"No taxon ID found for name '{name}'")
            except Exception as e:
                print(f"Error searching for taxon name '{name}': {e}")
        return taxon_ids

    def fetch_taxonomy_records(self, taxon_ids: List[str]) -> List[TaxonRecord]:
        """Fetch taxonomy records for a list of taxon IDs."""
        all_records = []
        for i in range(0, len(taxon_ids), self.batch_size):
            batch_ids = taxon_ids[i : i + self.batch_size]
            try:
                handle = Entrez.efetch(
                    db="taxonomy",
                    id=",".join(map(str, batch_ids)),
                    retmode="xml",
                )
                records = Entrez.read(handle)
                handle.close()
                all_records.extend([TaxonRecord(record) for record in records])
                time.sleep(self.delay)
            except Exception as e:
                print(f"Error fetching data for taxon IDs {batch_ids}: {e}")
        return all_records


def print_taxon_data(
    taxon_records: List[TaxonRecord], fields: List[str], output_format: str
):
    results = []
    for record in taxon_records:
        data = {field: record.get_field(field) for field in fields}
        data["TaxId"] = record.taxon_id
        results.append(data)

    if output_format == "text":
        for data in results:
            print(f"Taxon ID {data['TaxId']}:")
            for field in fields:
                value = data.get(field, "")
                if isinstance(value, list):
                    value = "; ".join(value)
                print(f"  {field}: {value}")
            print()
    elif output_format == "json":
        print(json.dumps(results, indent=2))
    elif output_format == "csv":
        fieldnames = ["TaxId"] + fields
        writer = csv.DictWriter(sys.stdout, fieldnames=fieldnames)
        writer.writeheader()
        for data in results:
            row = {}
            for key in fieldnames:
                value = data.get(key, "")
                if isinstance(value, list):
                    value = "; ".join(value)
                row[key] = value
            writer.writerow(row)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Fetch and print taxonomic data for given taxon IDs or names."
    )
    parser.add_argument(
        "taxon_inputs",
        nargs="+",
        help="List of taxon IDs or names to fetch data for.",
    )
    parser.add_argument(
        "--email",
        required=True,
        help="Email address to use for NCBI Entrez.",
    )
    parser.add_argument(
        "--fields",
        nargs="+",
        choices=["lineage", "ranks"],
        default=["lineage"],
        help="Fields to retrieve from taxonomy records.",
    )
    parser.add_argument(
        "--output-format",
        choices=["text", "json", "csv"],
        default="text",
        help="Format of the output data.",
    )

    args = parser.parse_args()

    fetcher = TaxonomyFetcher(email=args.email)

    # Infer whether inputs are IDs or names
    taxon_inputs = args.taxon_inputs
    taxon_ids = []
    taxon_names = []

    for input_str in taxon_inputs:
        if input_str.isdigit():
            taxon_ids.append(input_str)
        else:
            taxon_names.append(input_str)

    if taxon_names:
        resolved_ids = fetcher.resolve_taxon_names(taxon_names)
        taxon_ids.extend(resolved_ids)

    if not taxon_ids:
        print("No valid taxon IDs found. Please check your inputs.")
        sys.exit(1)

    taxon_records = fetcher.fetch_taxonomy_records(taxon_ids)
    print_taxon_data(taxon_records, args.fields, args.output_format)
