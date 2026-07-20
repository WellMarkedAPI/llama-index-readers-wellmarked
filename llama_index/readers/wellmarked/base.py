"""WellMarked reader for LlamaIndex."""
from __future__ import annotations

from typing import Any, List, Optional

from llama_index.core.readers.base import BasePydanticReader
from llama_index.core.schema import Document
from wellmarked import ExtractionMeta, WellMarked


def _metadata(meta: ExtractionMeta, source: str, depth: Optional[int] = None) -> dict[str, Any]:
    """Build JSON-serializable Document metadata from the SDK's ExtractionMeta."""
    out: dict[str, Any] = {"source": meta.url or source}
    if meta.title is not None:
        out["title"] = meta.title
    if meta.author is not None:
        out["author"] = meta.author
    if meta.date is not None:
        out["date"] = meta.date
    if meta.retrieved_at is not None:
        out["retrieved_at"] = meta.retrieved_at.isoformat()
    if depth is not None:
        out["depth"] = depth
    return out


class WellMarkedReader(BasePydanticReader):
    """Load web pages as clean Markdown via the WellMarked API.

    Install ``llama-index-readers-wellmarked`` and set the
    ``WELLMARKED_API_KEY`` environment variable (or pass ``api_key=``).
    Get a key at https://wellmarked.io.

    Examples:
        >>> from llama_index.readers.wellmarked import WellMarkedReader
        >>> reader = WellMarkedReader()
        >>> docs = reader.load_data("https://example.com/article")

        Crawl a whole site, one Document per page (Pro plan and above):

        >>> reader = WellMarkedReader(mode="crawl", depth=2)
        >>> docs = reader.load_data("https://docs.example.com")

        Retrieve from the live web by query (search + extract, Pro plan and above):

        >>> reader = WellMarkedReader(num_results=5)
        >>> docs = reader.search("best open-source vector databases")

    In ``crawl`` mode the reader blocks until the crawl job finishes
    (up to ``job_timeout`` seconds) and returns only successfully
    extracted pages; failed pages (timeouts, robots-disallowed) are
    skipped.

    Args:
        api_key: WellMarked API key (``wm_...``). Falls back to the
            ``WELLMARKED_API_KEY`` environment variable.
        mode: ``"extract"`` loads a single page; ``"crawl"`` BFS-crawls
            same-site links from the given root URL.
        depth: Crawl depth (``mode="crawl"`` only).
        render_js: Render JS-heavy pages with a headless browser
            (Pro plan and above).
        job_timeout: Seconds to wait for a crawl job to finish.
            ``None`` waits forever.
    """

    is_remote: bool = True
    api_key: Optional[str] = None
    mode: str = "extract"
    depth: int = 1
    render_js: bool = False
    job_timeout: Optional[float] = 300.0
    # Used by search(), not load_data(). How many results to fetch + extract;
    # clamped to 1..10 server-side.
    num_results: int = 5

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        if self.mode not in ("extract", "crawl"):
            raise ValueError(f"mode must be 'extract' or 'crawl', got {self.mode!r}")

    @classmethod
    def class_name(cls) -> str:
        return "WellMarkedReader"

    def load_data(self, url: str) -> List[Document]:
        """Extract ``url`` (or crawl from it) and return Documents.

        Args:
            url: The URL to extract (``mode="extract"``) or the root URL
                to crawl from (``mode="crawl"``).
        """
        with WellMarked(api_key=self.api_key) as wm:
            if self.mode == "extract":
                result = wm.extract(url, render_js=self.render_js)
                return [
                    Document(
                        text=result.markdown,
                        metadata=_metadata(result.metadata, url),
                    )
                ]

            job = wm.crawl(url, depth=self.depth, render_js=self.render_js)
            job = wm.wait_for_job(job.job_id, timeout=self.job_timeout)
            docs: List[Document] = []
            for page in job.results:
                if not page.ok:
                    continue
                assert page.markdown is not None and page.metadata is not None
                docs.append(
                    Document(
                        text=page.markdown,
                        metadata=_metadata(page.metadata, page.url, depth=page.depth),
                    )
                )
            return docs

    def search(self, query: str) -> List[Document]:
        """Search the web and return the extracted result pages as Documents.

        Unlike :meth:`load_data`, this takes a *query* rather than a URL: it
        searches the web and extracts the top ``num_results`` results in one
        round trip. Only successfully extracted results are returned; a page
        that timed out or was blocked is skipped. Requires a Pro plan or above
        (search is a paid feature).
        """
        with WellMarked(api_key=self.api_key) as wm:
            results = wm.search(
                query, num_results=self.num_results, render_js=self.render_js,
            ).results

        docs: List[Document] = []
        for r in results:
            if not r.ok or not r.markdown:
                continue
            metadata: dict[str, Any] = {"source": r.url}
            if r.title:
                metadata["title"] = r.title
            if r.snippet:
                metadata["snippet"] = r.snippet
            docs.append(Document(text=r.markdown, metadata=metadata))
        return docs
