import fitz  # PyMuPDF
from fastapi import HTTPException
from app.core.config import logger  # Use centralized logger


async def extract_text_from_pdf_bytes(file_content: bytes) -> str:
    """Extracts text from a PDF file stored in bytes."""
    try:
        # PyMuPDF's open method is synchronous. For very large files or high concurrency,
        # consider running this in a thread pool as well if it becomes a bottleneck.
        # For typical PDF sizes, direct call within an async function is often acceptable.
        doc = fitz.open(stream=file_content, filetype="pdf")
        text = ""
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            text += page.get_text("text")  # "text" for plain text
        doc.close()
        if not text.strip():
            logger.warning("PDF text extraction resulted in empty string.")
        return text
    except Exception as e:
        logger.error(f"Error extracting PDF text: {e}", exc_info=True)
        # It's better for the endpoint to raise HTTPException if this is user-facing.
        # This service function can return None or raise a custom service error.
        # For now, let it propagate or raise a generic error.
        # The endpoint currently catches generic Exception and re-wraps.
        raise RuntimeError(f"Failed to process PDF content: {e}")
