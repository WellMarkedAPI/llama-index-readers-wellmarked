"""Official LlamaIndex reader for the WellMarked API.

    from llama_index.readers.wellmarked import WellMarkedReader

    reader = WellMarkedReader()
    docs = reader.load_data("https://example.com/article")

See https://wellmarked.io/docs for the full API reference.
"""
from llama_index.readers.wellmarked.base import WellMarkedReader

__all__ = ["WellMarkedReader"]
