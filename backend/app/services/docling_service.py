from typing import List
from langchain_docling import DoclingLoader
from langchain_docling.loader import ExportType
from app.core.config import logger


class DoclingService:
    """
    A service class to encapsulate Docling functionality for file conversion.
    This service uses the official LangChain integration for Docling.
    """

    def __init__(self, file_paths: List[str]):
        """
        Initializes the DoclingService.

        Args:
            file_paths (List[str]): A list of file paths or URLs to process.
        """
        self.file_paths = file_paths

    def get_markdown_content(self) -> str:
        """
        Loads the document(s) and returns the full markdown content.

        Returns:
            str: A single string containing the concatenated markdown of all documents.
        """
        try:
            logger.info(f"Initializing DoclingLoader for: {self.file_paths}")
            loader = DoclingLoader(
                file_path=self.file_paths,
                export_type=ExportType.MARKDOWN,
            )
            docs = loader.load()

            if not docs:
                logger.warning("DoclingLoader returned no documents.")
                return ""

            # Combine content if multiple documents were processed (though we handle one at a time)
            full_content = "\n\n".join([doc.page_content for doc in docs])
            logger.info("Successfully loaded document content as markdown.")
            return full_content
        except Exception as e:
            logger.error(f"Error using DoclingLoader: {e}", exc_info=True)
            raise e
