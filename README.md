# llama-index-readers-wellmarked

The official [LlamaIndex](https://www.llamaindex.ai/) reader for **[WellMarked](https://wellmarked.io)** — load any URL as clean Markdown `Document`s.

```bash
pip install llama-index-readers-wellmarked
```

## Quick start

Set your API key (get one at [wellmarked.io](https://wellmarked.io)):

```bash
export WELLMARKED_API_KEY="wm_..."
```

Load a single page:

```python
from llama_index.readers.wellmarked import WellMarkedReader

reader = WellMarkedReader()
docs = reader.load_data("https://example.com/article")

docs[0].text       # clean Markdown
docs[0].metadata   # {"source": ..., "title": ..., "author": ..., "retrieved_at": ...}
```

Or crawl a whole site BFS-style — one `Document` per successfully extracted page (Pro plan and above):

```python
reader = WellMarkedReader(mode="crawl", depth=2)
docs = reader.load_data("https://docs.example.com")

docs[0].metadata["depth"]   # how far from the root URL this page sits
```

Drop the documents straight into an index:

```python
from llama_index.core import VectorStoreIndex

index = VectorStoreIndex.from_documents(docs)
```

## Options

All options are constructor arguments; `load_data(url)` takes only the URL.

| Parameter     | Default     | Description                                                        |
|---------------|-------------|--------------------------------------------------------------------|
| `api_key`     | env var     | WellMarked API key; falls back to `WELLMARKED_API_KEY`              |
| `mode`        | `"extract"` | `"extract"` (single page) or `"crawl"` (same-site BFS)              |
| `depth`       | `1`         | Crawl depth (`mode="crawl"` only)                                   |
| `render_js`   | `False`     | Render JS-heavy pages with a headless browser (Pro and above)       |
| `job_timeout` | `300.0`     | Seconds to wait for a crawl job; `None` waits forever               |

In `crawl` mode, pages that fail to extract (timeouts, robots-disallowed, no content) are skipped; only successful pages become `Document`s.

## Related

- [`wellmarked`](https://pypi.org/project/wellmarked/) — the underlying Python SDK (this package wraps it)
- [WellMarked API docs](https://wellmarked.io/docs)
- [`langchain-wellmarked`](https://github.com/WellMarkedAPI/langchain-wellmarked) — the LangChain equivalent
