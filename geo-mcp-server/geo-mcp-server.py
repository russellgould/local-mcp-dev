#!/usr/bin/env python3
"""
Simple MCP server for querying Gene Expression Omnibus (GEO) datasets.
"""

import logging
from typing import Any, Dict, Optional

import httpx
from fastmcp import FastMCP

# ----------------------------- Configure Logging ---------------------------- #
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ------------------------ NCBI e-Utilities Base URLs ------------------------ #
EUTILS_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
ESEARCH_URL = f"{EUTILS_BASE}/esearch.fcgi"
ESUMMARY_URL = f"{EUTILS_BASE}/esummary.fcgi"

# ------------------------------- Create Server ------------------------------ #
mcp = FastMCP("geo-query-server")


# ------------------------------- Define Tools ------------------------------- #
@mcp.tool()
async def search_geo(
    query: str,
    organism: Optional[str] = None,
    platform: Optional[str] = None,
    study_type: Optional[str] = None,
    max_results: int = 10,
) -> Dict[str, Any]:
    """Search GEO database for datasets matching criteria."""

    # Build search query
    search_terms = [query]
    if organism:
        search_terms.append(f'"{organism}"[Organism]')
    if platform:
        search_terms.append(f"{platform}[All Fields]")
    if study_type:
        search_terms.append(f'"{study_type}"[DataSet Type]')

    search_query = " AND ".join(search_terms)

    params = {
        "db": "gds",
        "term": search_query,
        "retmax": max_results,
        "retmode": "json",
    }

    async with httpx.AsyncClient() as client:
        try:
            # Search for datasets
            response = await client.get(ESEARCH_URL, params=params)
            search_data = response.json()

            if "error" in search_data:
                return {"error": search_data["error"]}

            id_list = search_data.get("esearchresult", {}).get("idlist", [])

            if not id_list:
                return {
                    "count": 0,
                    "datasets": [],
                    "message": "No datasets found matching the criteria",
                }

            # Get summaries for found datasets
            summary_params = {
                "db": "gds",
                "id": ",".join(id_list),
                "retmode": "json",
            }

            response = await client.get(ESUMMARY_URL, params=summary_params)
            summary_data = response.json()

            datasets = []
            for uid in id_list:
                if uid in summary_data.get("result", {}):
                    dataset = summary_data["result"][uid]
                    datasets.append(
                        {
                            "accession": dataset.get("accession"),
                            "title": dataset.get("title"),
                            "summary": dataset.get("summary"),
                            "organism": dataset.get("taxon"),
                            "platform": dataset.get("gpl"),
                            "samples": dataset.get("n_samples"),
                            "date": dataset.get("pdat"),
                            "type": dataset.get("gdstype"),
                        }
                    )

            return {
                "count": len(datasets),
                "datasets": datasets,
                "query": search_query,
            }

        except Exception as e:
            logger.error(f"Error searching GEO: {e}")
            return {"error": str(e)}


@mcp.tool()
async def get_geo_details(accession: str) -> Dict[str, Any]:
    """Get detailed information about a specific GEO dataset."""

    params = {"db": "gds", "term": f"{accession}[Accession]", "retmode": "json"}

    async with httpx.AsyncClient() as client:
        try:
            # Search for the specific dataset
            response = await client.get(ESEARCH_URL, params=params)
            search_data = response.json()

            id_list = search_data.get("esearchresult", {}).get("idlist", [])

            if not id_list:
                return {"error": f"Dataset {accession} not found"}

            # Get detailed summary
            summary_params = {"db": "gds", "id": id_list[0], "retmode": "json"}

            response = await client.get(ESUMMARY_URL, params=summary_params)
            summary_data = response.json()

            if id_list[0] in summary_data.get("result", {}):
                dataset = summary_data["result"][id_list[0]]

                # Parse sample information
                samples = []
                if "samples" in dataset:
                    for sample in dataset["samples"]:
                        samples.append(
                            {
                                "accession": sample.get("accession"),
                                "title": sample.get("title"),
                            }
                        )

                return {
                    "accession": dataset.get("accession"),
                    "title": dataset.get("title"),
                    "summary": dataset.get("summary"),
                    "organism": dataset.get("taxon"),
                    "platform": {
                        "accession": dataset.get("gpl"),
                        "title": dataset.get("platformtitle"),
                    },
                    "type": dataset.get("gdstype"),
                    "publication_date": dataset.get("pdat"),
                    "update_date": dataset.get("suppfile"),
                    "sample_count": dataset.get("n_samples"),
                    "samples": samples[:10],  # Limit to first 10 samples
                    "pubmed_ids": dataset.get("pubmedids", []),
                    "ftp_link": f"https://ftp.ncbi.nlm.nih.gov/geo/series/{accession[:-3]}nnn/{accession}/",
                }
            else:
                return {"error": "Failed to retrieve dataset details"}

        except Exception as e:
            logger.error(f"Error getting GEO details: {e}")
            return {"error": str(e)}


# ------------------------------ Main Entrypoint ----------------------------- #
if __name__ == "__main__":
    mcp.run(transport="http", host="127.0.0.1", port=8000)
