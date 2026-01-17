"""
PubMed Service for Clinical Intelligence Platform.

Integrates with NCBI E-utilities API for literature discovery.
https://www.ncbi.nlm.nih.gov/books/NBK25500/
"""
import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from urllib.parse import quote
import httpx
import os

logger = logging.getLogger(__name__)

# NCBI E-utilities API endpoints
EUTILS_BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
ESEARCH_URL = f"{EUTILS_BASE_URL}/esearch.fcgi"
EFETCH_URL = f"{EUTILS_BASE_URL}/efetch.fcgi"
ESUMMARY_URL = f"{EUTILS_BASE_URL}/esummary.fcgi"

# Rate limit: 3 requests per second without API key, 10 with API key
REQUEST_DELAY_SECONDS = 0.35

# Retry configuration
MAX_RETRIES = 3
INITIAL_BACKOFF_SECONDS = 1.0
MAX_BACKOFF_SECONDS = 10.0
RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}


class PubMedService:
    """
    Service for searching and retrieving publications from PubMed.

    Features:
    - Search PubMed using E-utilities API
    - Retrieve article metadata and abstracts
    - Parse and structure publication data
    - Rate limiting to comply with NCBI guidelines
    """

    def __init__(self):
        """Initialize PubMed service."""
        self._http_client: Optional[httpx.AsyncClient] = None
        self._last_request_time: float = 0
        self._api_key = os.getenv("NCBI_API_KEY", "")

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client with connection pooling."""
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient(
                timeout=30.0,
                limits=httpx.Limits(max_keepalive_connections=5, max_connections=10),
            )
        return self._http_client

    async def _rate_limited_request(
        self,
        client: httpx.AsyncClient,
        url: str,
        params: Dict[str, Any],
        max_retries: int = MAX_RETRIES,
    ) -> httpx.Response:
        """
        Make rate-limited request to NCBI API with exponential backoff retry.

        Args:
            client: HTTP client
            url: Request URL
            params: Request parameters
            max_retries: Maximum number of retry attempts

        Returns:
            HTTP response

        Raises:
            httpx.RequestError: If all retries fail
        """
        import time

        # Apply rate limiting
        now = time.time()
        elapsed = now - self._last_request_time
        delay = 0.1 if self._api_key else REQUEST_DELAY_SECONDS
        if elapsed < delay:
            await asyncio.sleep(delay - elapsed)
        self._last_request_time = time.time()

        if self._api_key:
            params["api_key"] = self._api_key

        last_exception: Optional[Exception] = None
        backoff = INITIAL_BACKOFF_SECONDS

        for attempt in range(max_retries + 1):
            try:
                response = await client.get(url, params=params)

                # Check for retryable status codes
                if response.status_code in RETRYABLE_STATUS_CODES:
                    if attempt < max_retries:
                        logger.warning(
                            f"PubMed API returned {response.status_code}, "
                            f"retrying in {backoff:.1f}s (attempt {attempt + 1}/{max_retries + 1})"
                        )
                        await asyncio.sleep(backoff)
                        backoff = min(backoff * 2, MAX_BACKOFF_SECONDS)
                        continue
                    else:
                        logger.error(
                            f"PubMed API returned {response.status_code} after {max_retries + 1} attempts"
                        )

                return response

            except httpx.TimeoutException as e:
                last_exception = e
                if attempt < max_retries:
                    logger.warning(
                        f"PubMed API timeout, retrying in {backoff:.1f}s "
                        f"(attempt {attempt + 1}/{max_retries + 1})"
                    )
                    await asyncio.sleep(backoff)
                    backoff = min(backoff * 2, MAX_BACKOFF_SECONDS)
                    continue
                else:
                    logger.error(f"PubMed API timeout after {max_retries + 1} attempts")
                    raise

            except httpx.RequestError as e:
                last_exception = e
                if attempt < max_retries:
                    logger.warning(
                        f"PubMed API network error: {e}, retrying in {backoff:.1f}s "
                        f"(attempt {attempt + 1}/{max_retries + 1})"
                    )
                    await asyncio.sleep(backoff)
                    backoff = min(backoff * 2, MAX_BACKOFF_SECONDS)
                    continue
                else:
                    logger.error(f"PubMed API network error after {max_retries + 1} attempts: {e}")
                    raise

        # Should not reach here, but raise last exception if it does
        if last_exception:
            raise last_exception
        raise httpx.RequestError("Request failed with no exception captured")

    async def search_publications(
        self,
        query: str,
        max_results: int = 50,
        min_date: Optional[str] = None,
        max_date: Optional[str] = None,
        publication_types: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Search PubMed for publications matching query.

        Args:
            query: Search query string (PubMed search syntax)
            max_results: Maximum number of results to return
            min_date: Minimum publication date (YYYY/MM/DD or YYYY)
            max_date: Maximum publication date (YYYY/MM/DD or YYYY)
            publication_types: Filter by publication types

        Returns:
            Dict with search results and metadata
        """
        client = await self._get_client()

        # Build search parameters
        params = {
            "db": "pubmed",
            "term": query,
            "retmax": min(max_results, 200),
            "retmode": "json",
            "sort": "relevance",
            "usehistory": "y",
        }

        if min_date:
            params["mindate"] = min_date
        if max_date:
            params["maxdate"] = max_date
        if min_date or max_date:
            params["datetype"] = "pdat"

        try:
            response = await self._rate_limited_request(client, ESEARCH_URL, params)

            if response.status_code != 200:
                logger.warning(f"PubMed search failed: {response.status_code}")
                return {
                    "success": False,
                    "error": f"PubMed API error: {response.status_code}",
                    "total_count": 0,
                    "articles": [],
                }

            data = response.json()
            search_result = data.get("esearchresult", {})

            pmids = search_result.get("idlist", [])
            total_count = int(search_result.get("count", 0))

            if not pmids:
                return {
                    "success": True,
                    "query": query,
                    "total_count": total_count,
                    "returned_count": 0,
                    "articles": [],
                }

            # Fetch article details
            articles = await self._fetch_article_details(pmids)

            return {
                "success": True,
                "query": query,
                "total_count": total_count,
                "returned_count": len(articles),
                "articles": articles,
                "search_timestamp": datetime.utcnow().isoformat(),
            }

        except httpx.RequestError as e:
            logger.error(f"PubMed API request failed: {e}")
            return {
                "success": False,
                "error": f"Network error: {str(e)}",
                "total_count": 0,
                "articles": [],
            }
        except Exception as e:
            logger.exception(f"Unexpected error in PubMed search: {e}")
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}",
                "total_count": 0,
                "articles": [],
            }

    async def _fetch_article_details(self, pmids: List[str]) -> List[Dict[str, Any]]:
        """
        Fetch detailed article information for given PMIDs.

        Args:
            pmids: List of PubMed IDs

        Returns:
            List of article details
        """
        if not pmids:
            return []

        client = await self._get_client()

        # Use ESummary for basic metadata (faster than EFetch)
        params = {
            "db": "pubmed",
            "id": ",".join(pmids),
            "retmode": "json",
        }

        try:
            response = await self._rate_limited_request(client, ESUMMARY_URL, params)

            if response.status_code != 200:
                logger.warning(f"PubMed esummary failed: {response.status_code}")
                return []

            data = response.json()
            result = data.get("result", {})

            articles = []
            for pmid in pmids:
                article_data = result.get(pmid, {})
                if article_data and "uid" in article_data:
                    articles.append(self._parse_article_summary(article_data))

            return articles

        except Exception as e:
            logger.error(f"Error fetching article details: {e}")
            return []

    def _parse_article_summary(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse ESummary response into structured article data."""
        authors = data.get("authors", [])
        author_names = [a.get("name", "") for a in authors[:5]]
        if len(authors) > 5:
            author_names.append("et al.")

        # Parse publication date
        pub_date = data.get("pubdate", "")
        year = ""
        if pub_date:
            parts = pub_date.split()
            if parts and parts[0].isdigit():
                year = parts[0]

        return {
            "pmid": data.get("uid", ""),
            "title": data.get("title", ""),
            "authors": author_names,
            "journal": data.get("fulljournalname", "") or data.get("source", ""),
            "journal_abbrev": data.get("source", ""),
            "pub_date": pub_date,
            "year": year,
            "volume": data.get("volume", ""),
            "issue": data.get("issue", ""),
            "pages": data.get("pages", ""),
            "doi": self._extract_doi(data.get("articleids", [])),
            "pub_types": data.get("pubtype", []),
            "has_abstract": data.get("hasabstract", 0) == 1,
            "url": f"https://pubmed.ncbi.nlm.nih.gov/{data.get('uid', '')}/",
        }

    def _extract_doi(self, article_ids: List[Dict]) -> Optional[str]:
        """Extract DOI from article IDs list."""
        for id_info in article_ids:
            if id_info.get("idtype") == "doi":
                return id_info.get("value")
        return None

    async def get_article_abstract(self, pmid: str) -> Optional[str]:
        """
        Fetch abstract for a specific article.

        Args:
            pmid: PubMed ID

        Returns:
            Abstract text or None
        """
        client = await self._get_client()

        params = {
            "db": "pubmed",
            "id": pmid,
            "rettype": "abstract",
            "retmode": "text",
        }

        try:
            response = await self._rate_limited_request(client, EFETCH_URL, params)

            if response.status_code == 200:
                return response.text.strip()
            return None

        except Exception as e:
            logger.error(f"Error fetching abstract for {pmid}: {e}")
            return None

    async def search_by_mesh_terms(
        self,
        mesh_terms: List[str],
        additional_terms: Optional[List[str]] = None,
        max_results: int = 50,
    ) -> Dict[str, Any]:
        """
        Search PubMed using MeSH terms.

        Args:
            mesh_terms: List of MeSH terms
            additional_terms: Additional free-text search terms
            max_results: Maximum results

        Returns:
            Search results
        """
        # Build MeSH query
        mesh_query_parts = [f'"{term}"[MeSH Terms]' for term in mesh_terms]
        query = " AND ".join(mesh_query_parts)

        if additional_terms:
            additional_query = " OR ".join([f'"{t}"[Title/Abstract]' for t in additional_terms])
            query = f"({query}) AND ({additional_query})"

        return await self.search_publications(query, max_results=max_results)

    async def search_for_product(
        self,
        product_name: str,
        indication: str,
        technologies: List[str],
        max_results: int = 50,
    ) -> Dict[str, Any]:
        """
        Search for publications related to a medical product.

        Args:
            product_name: Name of the product
            indication: Primary indication
            technologies: Key technologies
            max_results: Maximum results

        Returns:
            Categorized search results
        """
        # Build comprehensive search query
        search_terms = []

        # Add indication-related terms
        if indication:
            search_terms.append(f'"{indication}"[Title/Abstract]')

        # Add technology terms
        for tech in technologies:
            search_terms.append(f'"{tech}"[Title/Abstract]')

        # Add product name if it seems searchable
        if product_name and not product_name.startswith("Unknown"):
            search_terms.append(f'"{product_name}"[Title/Abstract]')

        if not search_terms:
            return {
                "success": False,
                "error": "No search terms provided",
                "total_count": 0,
                "articles": [],
            }

        query = " OR ".join(search_terms)

        # Filter to clinical studies and reviews
        query = f"({query}) AND (clinical trial[pt] OR review[pt] OR meta-analysis[pt] OR randomized controlled trial[pt])"

        results = await self.search_publications(
            query,
            max_results=max_results,
            min_date="2015",
        )

        # Categorize by relevance
        if results.get("success") and results.get("articles"):
            results["articles"] = self._rank_by_relevance(
                results["articles"],
                indication,
                technologies,
            )

        return results

    def _rank_by_relevance(
        self,
        articles: List[Dict],
        indication: str,
        technologies: List[str],
    ) -> List[Dict]:
        """Rank articles by relevance to product context."""
        indication_lower = indication.lower() if indication else ""
        tech_lower = [t.lower() for t in technologies]

        for article in articles:
            score = 0
            title_lower = article.get("title", "").lower()

            # Check indication match
            if indication_lower and indication_lower in title_lower:
                score += 3

            # Check technology match
            for tech in tech_lower:
                if tech in title_lower:
                    score += 2

            # Prefer recent publications
            year = article.get("year", "")
            if year and year.isdigit():
                year_int = int(year)
                if year_int >= 2023:
                    score += 2
                elif year_int >= 2020:
                    score += 1

            # Prefer clinical trials and meta-analyses
            pub_types = [pt.lower() for pt in article.get("pub_types", [])]
            if "meta-analysis" in pub_types:
                score += 2
            if "randomized controlled trial" in pub_types:
                score += 2
            if "clinical trial" in pub_types:
                score += 1

            article["relevance_score"] = score / 10.0  # Normalize to 0-1

        # Sort by relevance score
        articles.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)

        return articles

    async def close(self):
        """Close HTTP client."""
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None


# Singleton pattern
_pubmed_service: Optional[PubMedService] = None


def get_pubmed_service() -> PubMedService:
    """Get singleton PubMed service instance."""
    global _pubmed_service
    if _pubmed_service is None:
        _pubmed_service = PubMedService()
    return _pubmed_service
