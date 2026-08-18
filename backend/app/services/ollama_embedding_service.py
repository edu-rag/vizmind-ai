from functools import lru_cache
from typing import List

import httpx
from langchain_core.embeddings import Embeddings

from app.core.config import logger, settings


class OllamaEmbeddings(Embeddings):
    """LangChain-compatible embeddings backed by Ollama's HTTP API."""

    def __init__(
        self,
        base_url: str,
        model: str,
        timeout: float = 120.0,
        batch_size: int = 32,
    ):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout
        self.batch_size = batch_size

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []

        all_embeddings: List[List[float]] = []
        with httpx.Client(timeout=self.timeout) as client:
            for start in range(0, len(texts), self.batch_size):
                batch = texts[start : start + self.batch_size]
                response = client.post(
                    f"{self.base_url}/api/embed",
                    json={"model": self.model, "input": batch},
                )
                response.raise_for_status()
                embeddings = response.json().get("embeddings")

                if not embeddings or len(embeddings) != len(batch):
                    raise RuntimeError(
                        "Ollama returned an invalid embedding response "
                        f"({len(embeddings or [])} vectors for {len(batch)} inputs)"
                    )
                all_embeddings.extend(embeddings)

        return all_embeddings

    def embed_query(self, text: str) -> List[float]:
        embeddings = self.embed_documents([text])
        return embeddings[0]


@lru_cache(maxsize=1)
def get_embedding_model() -> OllamaEmbeddings:
    logger.info(
        "Using Ollama embedding model '%s' at %s",
        settings.OLLAMA_EMBED_MODEL,
        settings.OLLAMA_BASE_URL,
    )
    return OllamaEmbeddings(
        base_url=settings.OLLAMA_BASE_URL,
        model=settings.OLLAMA_EMBED_MODEL,
        timeout=settings.OLLAMA_EMBED_TIMEOUT_SECONDS,
        batch_size=settings.OLLAMA_EMBED_BATCH_SIZE,
    )
