from typing import Any, Dict, List
import uuid
from app.services.docling_service import DoclingService
from app.core.config import settings, logger
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_huggingface.embeddings import HuggingFaceEmbeddings
from langchain_text_splitters import MarkdownHeaderTextSplitter
from app.db.mongodb_utils import get_db


class MindMapService:
    """
    Orchestrates the entire document processing pipeline:
    1. Loads content using DoclingService.
    2. Cleans the markdown with an LLM.
    3. Generates a mind map hierarchy.
    4. Chunks the cleaned markdown by headers.
    5. Ingests the chunks into MongoDB for RAG.
    """

    def __init__(
        self,
        file_path: str,
        user_id: str,
        concept_map_id: str,
        s3_path: str,
        original_filename: str,
    ):
        self.file_path = file_path
        self.user_id = user_id
        self.concept_map_id = concept_map_id
        self.s3_path = s3_path
        self.original_filename = original_filename
        self.llm = ChatGroq(
            temperature=0.0,
            groq_api_key=settings.GROQ_API_KEY,
            model_name=settings.LLM_MODEL_NAME_GROQ,
        )
        self.embedding = HuggingFaceEmbeddings(
            model_name=settings.MODEL_NAME_FOR_EMBEDDING
        )
        self.db = get_db()
        self.chunks_collection = self.db[settings.MONGODB_CHUNKS_COLLECTION]

    async def _cleanup_markdown_with_llm(self, markdown_content: str) -> str:
        """Uses an LLM to clean and refine the markdown structure."""
        logger.info("Cleaning up markdown with LLM...")
        cleanup_prompt = ChatPromptTemplate.from_template(
            """
            You are a document structuring expert. Refine the markdown content below for a mind map.

            **Instructions:**
            1.  **Correct Hierarchy:** Ensure logical heading levels (#, ##, ###).
            2.  **Remove Noise:** Delete irrelevant text like page numbers, headers, and footers.
            3.  **Summarize:** Convert long paragraphs into concise bullet points.
            4.  **Maintain Content:** Do not add new information. Refine what exists.
            5.  **Output ONLY Markdown.**

            **Original Markdown:**
            ---
            {markdown_text}
            ---
            **Refined Markdown:**
            """
        )
        cleanup_chain = cleanup_prompt | self.llm | StrOutputParser()
        cleaned_markdown = await cleanup_chain.ainvoke(
            {"markdown_text": markdown_content}
        )
        logger.info("Markdown cleanup complete.")
        return cleaned_markdown

    async def _ingest_chunks_for_rag(self, chunks: List[Dict[str, Any]]):
        """Embeds and stores document chunks in MongoDB for RAG."""
        if not chunks:
            logger.warning("No chunks to ingest for RAG.")
            return

        logger.info(f"Preparing to ingest {len(chunks)} chunks into MongoDB.")

        texts_to_embed = [chunk["page_content"] for chunk in chunks]
        embeddings = self.embedding.embed_documents(texts_to_embed)

        documents_to_insert = []
        for i, chunk in enumerate(chunks):
            # Add all necessary metadata for filtering during retrieval
            metadata = {
                "user_id": self.user_id,
                "concept_map_id": self.concept_map_id,
                "s3_path": self.s3_path,
                "original_filename": self.original_filename,
                **chunk.get("metadata", {}),
            }
            documents_to_insert.append(
                {"text": chunk["page_content"], "embedding": embeddings[i], **metadata}
            )

        self.chunks_collection.insert_many(documents_to_insert)
        logger.info(f"Successfully ingested {len(documents_to_insert)} chunks.")

    def _parse_markdown_to_hierarchy(self, markdown_content: str) -> Dict[str, Any]:
        """
        Parses markdown content into a hierarchical dictionary.
        """
        lines = markdown_content.split("\n")
        root_title = "Document"
        for line in lines:
            if line.startswith("# "):
                root_title = line[2:].strip()
                break

        root = {"id": str(uuid.uuid4()), "data": {"label": root_title}, "children": []}
        path = [root]

        for line in lines:
            stripped_line = line.strip()
            if stripped_line.startswith("#"):
                level = 0
                while level < len(stripped_line) and stripped_line[level] == "#":
                    level += 1

                title = stripped_line[level:].strip()
                if not title:
                    continue

                # Clean up title by removing special characters like bullet points
                cleaned_title = title.replace("\uf0b7", "").strip()
                if cleaned_title.startswith("•"):
                    cleaned_title = cleaned_title[1:].strip()

                node = {
                    "id": str(uuid.uuid4()),
                    "data": {"label": cleaned_title},
                    "children": [],
                }

                while len(path) > level:
                    path.pop()

                if path:
                    path[-1]["children"].append(node)
                path.append(node)
            elif stripped_line.startswith(("-", "*", "+")) and len(stripped_line) > 1:
                title = stripped_line[1:].strip()
                if not title or not path:
                    continue

                # Clean up title by removing special characters
                cleaned_title = title.replace("\uf0b7", "").strip()
                if cleaned_title.startswith("•"):
                    cleaned_title = cleaned_title[1:].strip()

                node = {
                    "id": str(uuid.uuid4()),
                    "data": {"label": cleaned_title},
                    "children": [],
                }
                path[-1]["children"].append(node)

        return root

    async def generate_and_ingest(self) -> Dict[str, Any]:
        """
        The main pipeline method.
        """
        try:
            # 1. Load the document content once
            docling_service = DoclingService([self.file_path])
            markdown_content = docling_service.get_markdown_content()
            if not markdown_content:
                return {"error": "Failed to extract content from the document."}

            # 2. Clean the markdown for both mind map and chunking
            cleaned_markdown = await self._cleanup_markdown_with_llm(markdown_content)

            # 3. Generate the mind map hierarchy from the cleaned markdown
            hierarchy = self._parse_markdown_to_hierarchy(cleaned_markdown)

            # 4. Chunk the same cleaned markdown for RAG
            headers_to_split_on = [("#", "H1"), ("##", "H2"), ("###", "H3")]
            markdown_splitter = MarkdownHeaderTextSplitter(
                headers_to_split_on=headers_to_split_on
            )
            chunks = markdown_splitter.split_text(markdown_content)

            # 5. Ingest chunks into MongoDB
            chunk_dicts = [chunk.model_dump() for chunk in chunks]
            await self._ingest_chunks_for_rag(chunk_dicts)

            logger.info("Mind map generation and RAG ingestion completed.")
            return hierarchy
        except Exception as e:
            logger.error(
                f"Error during generate_and_ingest pipeline: {e}", exc_info=True
            )
            return {"error": "A failure occurred during document processing."}
