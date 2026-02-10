"""PubMed client using NCBI E-utilities."""

from __future__ import annotations

import os
import xml.etree.ElementTree as ET
from typing import Any

import requests

from .schemas import EvidenceSource


class PubMedClient:
    """Minimal PubMed search/fetch client."""

    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

    def __init__(self, email: str | None = None, tool: str | None = None, session: requests.Session | None = None):
        self.email = email or os.getenv("NCBI_EMAIL")
        self.tool = tool or os.getenv("NCBI_TOOL", "cdss-medqna")
        self.session = session or requests.Session()

    def search(self, query: str, max_results: int = 5) -> list[str]:
        params = {
            "db": "pubmed",
            "term": query,
            "retmax": max_results,
            "retmode": "json",
            "sort": "pub date",
            "tool": self.tool,
        }
        if self.email:
            params["email"] = self.email

        resp = self.session.get(f"{self.base_url}/esearch.fcgi", params=params, timeout=15)
        resp.raise_for_status()
        return self.parse_search_ids(resp.json())

    @staticmethod
    def parse_search_ids(payload: dict[str, Any]) -> list[str]:
        return payload.get("esearchresult", {}).get("idlist", [])

    def fetch_abstracts(self, pmids: list[str]) -> list[EvidenceSource]:
        if not pmids:
            return []

        params = {
            "db": "pubmed",
            "id": ",".join(pmids),
            "retmode": "xml",
            "tool": self.tool,
        }
        if self.email:
            params["email"] = self.email

        resp = self.session.get(f"{self.base_url}/efetch.fcgi", params=params, timeout=15)
        resp.raise_for_status()
        return self.parse_abstracts_xml(resp.text)

    @staticmethod
    def parse_abstracts_xml(xml_text: str) -> list[EvidenceSource]:
        root = ET.fromstring(xml_text)
        records: list[EvidenceSource] = []
        for article in root.findall(".//PubmedArticle"):
            pmid = article.findtext(".//PMID")
            title = (article.findtext(".//ArticleTitle") or "Untitled").strip()
            abstract_texts = [node.text.strip() for node in article.findall(".//AbstractText") if node.text]
            abstract = " ".join(abstract_texts) or "No abstract available."
            year_text = article.findtext(".//PubDate/Year")
            year = int(year_text) if year_text and year_text.isdigit() else None
            url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else None
            records.append(
                EvidenceSource(
                    source_type="pubmed",
                    source_name="PubMed",
                    title=title,
                    summary=abstract,
                    year=year,
                    url=url,
                    source_accessible=True,
                )
            )
        return records

    def retrieve(self, query: str, max_results: int = 5) -> list[EvidenceSource]:
        ids = self.search(query=query, max_results=max_results)
        return self.fetch_abstracts(ids)
