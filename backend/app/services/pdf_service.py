import fitz  # PyMuPDF
import re
from typing import Dict, List, Any, Optional
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


async def extract_structured_text_from_pdf_bytes(file_content: bytes) -> Dict[str, Any]:
    """
    Extracts text from a PDF file with structural information (headers, subheaders, etc.).
    Returns both plain text and hierarchical structured data.

    Returns:
        Dict containing:
        - plain_text: Complete text content
        - structured_content: Hierarchical document structure with nested sections
        - metadata: Document metadata (title, pages, etc.)
    """
    try:
        doc = fitz.open(stream=file_content, filetype="pdf")

        # Extract document metadata
        metadata = {
            "page_count": len(doc),
            "title": doc.metadata.get("title", ""),
            "author": doc.metadata.get("author", ""),
            "subject": doc.metadata.get("subject", ""),
        }

        # Extract text with structure detection
        structured_content = []
        plain_text = ""

        for page_num in range(len(doc)):
            page = doc.load_page(page_num)

            # Get text blocks with formatting information
            text_dict = page.get_text("dict")
            page_text = ""

            for block in text_dict["blocks"]:
                if "lines" in block:  # Text block
                    block_text = ""
                    block_font_sizes = []

                    for line in block["lines"]:
                        line_text = ""
                        for span in line["spans"]:
                            line_text += span["text"]
                            block_font_sizes.append(span["size"])

                        if line_text.strip():
                            block_text += line_text + "\n"

                    if block_text.strip():
                        # Analyze font sizes to determine hierarchy level
                        avg_font_size = (
                            sum(block_font_sizes) / len(block_font_sizes)
                            if block_font_sizes
                            else 12
                        )
                        max_font_size = (
                            max(block_font_sizes) if block_font_sizes else 12
                        )

                        # Determine if this might be a header based on font size and content
                        hierarchy_level = _determine_hierarchy_level(
                            block_text.strip(), avg_font_size, max_font_size
                        )

                        structured_content.append(
                            {
                                "text": block_text.strip(),
                                "page": page_num + 1,
                                "hierarchy_level": hierarchy_level,
                                "font_size": avg_font_size,
                                "max_font_size": max_font_size,
                            }
                        )

                        page_text += block_text

            plain_text += page_text

        doc.close()

        # Post-process to improve hierarchy detection
        structured_content = _improve_hierarchy_detection(structured_content)

        # Convert flat structure to hierarchical structure
        hierarchical_content = _build_hierarchical_structure(structured_content)

        if not plain_text.strip():
            logger.warning("PDF text extraction resulted in empty string.")

        logger.info(
            f"Successfully extracted structured PDF with {len(structured_content)} text blocks across {metadata['page_count']} pages, converted to hierarchical structure"
        )

        return {
            "plain_text": plain_text,
            "structured_content": hierarchical_content,  # Hierarchical format
            "metadata": metadata,
        }

    except Exception as e:
        logger.error(f"Error extracting structured PDF text: {e}", exc_info=True)
        raise RuntimeError(f"Failed to process PDF content with structure: {e}")


def _determine_hierarchy_level(
    text: str, avg_font_size: float, max_font_size: float
) -> int:
    """
    Determines the hierarchy level of a text block based on various factors.
    Enhanced to better handle academic papers and research documents.

    Returns:
        0: Main title/document title
        1: Chapter/major section header
        2: Section header
        3: Subsection header
        4: Body text
        5: Minor text (footnotes, captions, etc.)
    """
    text_lower = text.lower().strip()
    text_clean = text.strip()

    # First, identify non-content patterns that should NOT be headers
    non_header_patterns = [
        r"^arxiv:",  # arXiv identifiers
        r"^\w+:\d+\.\d+\w*",  # Document identifiers like "arXiv:2410.22392v2"
        r"^\[[\w\s\.]+\]",  # Content in square brackets like "[eess.IV]"
        r"^\d{1,2}\s+(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)",  # Dates
        r"^email:",  # Email addresses
        r"^https?://",  # URLs
        r"^www\.",  # Web addresses
        r"^doi:",  # DOI identifiers
        r"^isbn:",  # ISBN numbers
        r"^\d+\s+pages?",  # Page references
        r"^page\s+\d+",  # Page indicators
        r"^figure\s+\d+",  # Figure captions
        r"^table\s+\d+",  # Table captions
        r"^algorithm\s+\d+",  # Algorithm captions
    ]

    # Check if this is a non-header pattern first
    for pattern in non_header_patterns:
        if re.search(pattern, text_lower):
            return 5  # Minor text/metadata

    # Check text length - very long texts are likely body text
    if len(text) > 300:
        return 4  # Likely body text

    # Enhanced header patterns for academic papers
    header_patterns = [
        # Roman numerals (common in academic papers) - highest priority for main sections
        (r"^[IVX]+\.\s+[A-Z]", 1),  # "I. INTRODUCTION", "II. METHODOLOGY"
        (r"^[IVX]+\s+[A-Z]", 1),  # "I INTRODUCTION", "II METHODOLOGY"
        # Numbered subsections (more specific patterns first)
        (r"^\d+\.\d+\.\d+\s", 3),  # "1.1.1 Sub-subsection"
        (r"^\d+\.\d+\s+[A-Z]", 2),  # "1.1 Subsection"
        (r"^\d+\.\d+\.\s*[A-Z]", 2),  # "1.1. Subsection"
        # Lettered sections (usually subsections)
        (r"^[A-Z]\.\s+[A-Z]", 2),  # "A. Subsection"
        (r"^[A-Z]\s+[A-Z]", 2),  # "A Subsection"
        (r"^[A-Z]\.\d+\s", 3),  # "A.1 Sub-subsection"
        # Single digit numbers - be more careful about these
        # Only treat as main sections if they're very short and likely to be actual main sections
        (
            r"^([1-9]|1[0-2])\.\s+[A-Z][A-Z\s]{2,}[A-Z]$",
            1,
        ),  # "1. INTRODUCTION" (ALL CAPS, short)
        (
            r"^([1-9]|1[0-2])\s+[A-Z][A-Z\s]{2,}[A-Z]$",
            1,
        ),  # "1 INTRODUCTION" (ALL CAPS, short)
        # Numbered items that are likely subsections (more specific context)
        (r"^\d+\.\s+[A-Z][a-z]", 2),  # "2. Feature Aggregation" - treat as subsection
        (r"^\d+\s+[A-Z][a-z]", 2),  # "2 Feature Aggregation" - treat as subsection
        # Common academic section headers
        (
            r"^(abstract|introduction|methodology|methods|results|discussion|conclusion|references|acknowledgments|appendix)$",
            1,
        ),
        (
            r"^(related\s+work|literature\s+review|experimental\s+setup|evaluation|future\s+work)$",
            1,
        ),
        # ALL CAPS headers (but not metadata)
        (r"^[A-Z][A-Z\s]{2,}[A-Z]$", 1),  # ALL CAPS headers
        # Headers with colons
        (r"^[A-Z][a-z\s]+:$", 2),  # "Introduction:"
        # Numbered items that might be subsections
        (r"^\d+\)\s+[A-Z]", 2),  # "1) Section"
        (r"^\(\d+\)\s+[A-Z]", 2),  # "(1) Section"
    ]

    # Check against header patterns with specific hierarchy levels
    for pattern, level in header_patterns:
        if re.match(pattern, text_clean, re.IGNORECASE):
            # Additional validation for Roman numerals
            if pattern.startswith(r"^[IVX]"):
                # Validate it's actually a Roman numeral
                roman_match = re.match(r"^([IVX]+)[\.\s]", text_clean)
                if roman_match:
                    roman_num = roman_match.group(1)
                    if _is_valid_roman_numeral(roman_num):
                        return level
            else:
                return level

    # Font size analysis (less priority than pattern matching)
    if max_font_size > 16:
        # Very large font - likely title, but check if it's metadata first
        if len(text) < 200 and not any(
            re.search(p, text_lower) for p in non_header_patterns
        ):
            return 0  # Title
    elif max_font_size > 14:
        # Large font - could be title if it's substantial content
        if (
            len(text) > 30
            and len(text) < 150
            and not any(re.search(p, text_lower) for p in non_header_patterns)
        ):
            return 0  # Title
        elif len(text) < 100:
            return 1  # Major header
    elif max_font_size > 12:
        if len(text) < 80:
            return 2  # Section header

    # Check for academic keywords that indicate headers regardless of font size
    academic_header_keywords = [
        "introduction",
        "background",
        "methodology",
        "methods",
        "approach",
        "results",
        "findings",
        "analysis",
        "discussion",
        "conclusion",
        "related work",
        "literature review",
        "experimental setup",
        "evaluation",
        "implementation",
        "experiments",
        "future work",
        "acknowledgments",
        "references",
        "bibliography",
        "appendix",
    ]

    # Check for standalone academic section headers (not embedded in longer text)
    text_words = text_lower.split()
    if (
        len(text_words) <= 3
        and len(text) < 50  # Short, standalone text
        and any(
            keyword == text_lower or text_lower.endswith(keyword)
            for keyword in academic_header_keywords
        )
        and not any(re.search(p, text_lower) for p in non_header_patterns)
    ):
        return 1

    # Check for very small font (footnotes, captions, metadata)
    if avg_font_size < 9:
        return 5  # Minor text

    return 4  # Default to body text


def _is_valid_roman_numeral(roman: str) -> bool:
    """Validate if a string is a proper Roman numeral."""
    # Basic validation for common Roman numerals in academic papers
    valid_romans = [
        "I",
        "II",
        "III",
        "IV",
        "V",
        "VI",
        "VII",
        "VIII",
        "IX",
        "X",
        "XI",
        "XII",
        "XIII",
        "XIV",
        "XV",
        "XVI",
        "XVII",
        "XVIII",
        "XIX",
        "XX",
    ]
    return roman.upper() in valid_romans


def _improve_hierarchy_detection(
    structured_content: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Post-processes the structured content to improve hierarchy level detection.
    Enhanced to better handle academic papers and research documents with context awareness.
    """
    if not structured_content:
        return structured_content

    # Calculate font size statistics for better relative sizing
    font_sizes = [item["max_font_size"] for item in structured_content]
    avg_doc_font = sum(font_sizes) / len(font_sizes)
    max_doc_font = max(font_sizes)

    # Find the actual document title (not metadata)
    title_candidates = []
    for i, item in enumerate(structured_content):
        text = item["text"].strip()

        # Skip metadata patterns
        metadata_patterns = [
            r"^arxiv:",
            r"^\w+:\d+\.\d+\w*",
            r"^\[[\w\s\.]+\]",
            r"^\d{1,2}\s+(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)",
        ]

        is_metadata = any(re.search(p, text.lower()) for p in metadata_patterns)

        if (
            not is_metadata
            and len(text) > 20
            and len(text) < 200
            and item["page"] == 1  # On first page
            and item["max_font_size"] >= avg_doc_font
        ):
            title_candidates.append((i, item, len(text)))

    # The title is usually the longest meaningful text on the first page with decent font size
    if title_candidates:
        # Sort by length descending, then by font size descending
        title_candidates.sort(key=lambda x: (x[2], x[1]["max_font_size"]), reverse=True)
        title_idx = title_candidates[0][0]

        # Only set as title if it doesn't look like a section header
        title_text = title_candidates[0][1]["text"].strip()
        if not re.match(
            r"^[IVX]+[\.\s]+[A-Z]", title_text
        ):  # Not a Roman numeral section
            structured_content[title_idx]["hierarchy_level"] = 0  # Mark as title

    # Track main sections to provide context for numbered items
    main_sections = []

    # First pass: identify clear main sections
    for i, item in enumerate(structured_content):
        text = item["text"].strip()
        text_lower = text.lower()

        # Skip if already processed as title
        if item["hierarchy_level"] == 0:
            continue

        # Roman numeral sections are clearly main sections
        if re.match(r"^[IVX]+[\.\s]+[A-Z]", text):
            roman_match = re.match(r"^([IVX]+)[\.\s]", text)
            if roman_match and _is_valid_roman_numeral(roman_match.group(1)):
                item["hierarchy_level"] = 1
                main_sections.append(i)
                continue

        # Academic keywords in isolation are main sections
        academic_headers = [
            "abstract",
            "introduction",
            "background",
            "related work",
            "methodology",
            "methods",
            "approach",
            "implementation",
            "results",
            "findings",
            "analysis",
            "evaluation",
            "discussion",
            "conclusion",
            "future work",
            "acknowledgments",
            "references",
            "bibliography",
            "appendix",
        ]

        text_clean = re.sub(r"^\d+[\.\s]*", "", text_lower).strip()
        if text_clean in academic_headers and len(text) < 80:
            item["hierarchy_level"] = 1
            main_sections.append(i)
            continue

        # ALL CAPS headers (but not metadata)
        if (
            text.isupper()
            and len(text) > 3
            and len(text) < 80
            and not any(
                re.search(p, text_lower) for p in [r"^arxiv:", r"^\w+:\d+\.\d+"]
            )
        ):
            item["hierarchy_level"] = 1
            main_sections.append(i)
            continue

    # Second pass: refine numbered items based on context
    for i, item in enumerate(structured_content):
        text = item["text"].strip()
        text_lower = text.lower()

        # Skip already processed items
        if item["hierarchy_level"] <= 1:
            continue

        # Find the most recent main section and lettered subsection before this item
        recent_main_section = None
        recent_lettered_section = None

        for j in range(i - 1, -1, -1):  # Look backwards
            prev_item = structured_content[j]
            prev_text = prev_item["text"].strip()

            # Find most recent main section (Roman numerals or level 1)
            if prev_item["hierarchy_level"] == 1 or re.match(
                r"^[IVX]+[\.\s]+[A-Z]", prev_text
            ):
                if recent_main_section is None:
                    recent_main_section = j

            # Find most recent lettered section (A., B., C.)
            if (
                re.match(r"^[A-Z][\.\s]+[A-Z]", prev_text)
                and prev_item["hierarchy_level"] == 2
            ):
                recent_lettered_section = j
                break  # Stop at first lettered section found

        # Context-aware processing for numbered items
        if re.match(r"^\d+\.\s+[A-Z]", text):
            # If this is a numbered item that follows a lettered section closely,
            # treat it as a sub-subsection (level 3)
            if (
                recent_lettered_section is not None
                and (i - recent_lettered_section) <= 5
            ):
                item["hierarchy_level"] = 3  # Sub-subsection under lettered section
            # If this follows a main section closely, treat as subsection
            elif recent_main_section is not None and (i - recent_main_section) <= 5:
                item["hierarchy_level"] = 2
            # Otherwise, check if it looks like a main section
            elif re.match(r"^([1-9]|1[0-2])\.\s+[A-Z][A-Z\s]{2,}[A-Z]$", text):
                item["hierarchy_level"] = 1
                main_sections.append(i)
            else:
                item["hierarchy_level"] = 2
            continue

        # Lettered subsections
        if re.match(r"^[A-Z][\.\s]+[A-Z]", text) and len(text) < 100:
            item["hierarchy_level"] = 2
            continue

        # Decimal numbered subsections
        if re.match(r"^\d+\.\d+[\.\s]", text):
            item["hierarchy_level"] = 2
            continue

        # Sub-subsections
        if re.match(r"^\d+\.\d+\.\d+[\.\s]", text):
            item["hierarchy_level"] = 3
            continue

        # Adjust based on relative font size within document (lower priority)
        font_size = item["max_font_size"]
        if font_size > avg_doc_font * 1.4:
            if len(text) < 120 and item["hierarchy_level"] > 1:
                item["hierarchy_level"] = min(item["hierarchy_level"], 1)
        elif font_size > avg_doc_font * 1.2:
            if len(text) < 100 and item["hierarchy_level"] > 2:
                item["hierarchy_level"] = min(item["hierarchy_level"], 2)

        # Identify metadata and minor text more accurately
        metadata_patterns = [
            r"^arxiv:",
            r"^\w+:\d+\.\d+",
            r"^\[[\w\s\.]+\]",
            r"^email:",
            r"^https?://",
            r"^www\.",
            r"^doi:",
            r"^figure\s+\d+",
            r"^table\s+\d+",
            r"^algorithm\s+\d+",
        ]

        if any(re.search(p, text_lower) for p in metadata_patterns):
            item["hierarchy_level"] = 5  # Metadata/minor text

    return structured_content


def _build_hierarchical_structure(
    structured_content: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Builds a hierarchical structure from structured content.

    Args:
        structured_content: List of content blocks with hierarchy levels

    Returns:
        Hierarchical structure with title, text, and children
    """
    if not structured_content:
        return {"title": "Document", "text": "", "children": []}

    # Filter out metadata and minor text (hierarchy_level >= 5)
    content_blocks = [
        block for block in structured_content if block.get("hierarchy_level", 4) < 5
    ]

    if not content_blocks:
        return {"title": "Document", "text": "", "children": []}

    # Find document title (hierarchy_level 0) or use first major header
    doc_title = "Document"
    doc_text = ""

    # Look for main title (level 0)
    title_blocks = [
        block for block in content_blocks if block.get("hierarchy_level") == 0
    ]
    if title_blocks:
        doc_title = _clean_header_text(title_blocks[0]["text"])
        doc_text = title_blocks[0]["text"]
        # Remove title blocks from processing
        content_blocks = [
            block for block in content_blocks if block.get("hierarchy_level") != 0
        ]

    # Build the hierarchical structure
    root = {"title": doc_title, "text": doc_text, "children": []}

    # Stack to track current hierarchy path
    hierarchy_stack = [root]  # [root]
    level_stack = [-1]  # Levels corresponding to hierarchy_stack

    for block in content_blocks:
        hierarchy_level = block.get("hierarchy_level", 4)
        text = block["text"]

        if hierarchy_level <= 3:  # Header levels (1=chapter, 2=section, 3=subsection)
            # Clean the header text to extract meaningful title
            title = _clean_header_text(text)

            # Pop stack until we find the right parent level
            while level_stack and level_stack[-1] >= hierarchy_level:
                hierarchy_stack.pop()
                level_stack.pop()

            # Create new section node
            new_section = {"title": title, "text": text, "children": []}

            # Add to parent's children
            if hierarchy_stack:
                hierarchy_stack[-1]["children"].append(new_section)
            else:
                root["children"].append(new_section)

            # Push to stack
            hierarchy_stack.append(new_section)
            level_stack.append(hierarchy_level)

        else:  # Body text (level 4) or other content
            # Add to current section's text
            if hierarchy_stack and len(hierarchy_stack) > 1:
                # Add to the most recent section
                current_section = hierarchy_stack[-1]
                if current_section["text"]:
                    current_section["text"] += "\n\n" + text
                else:
                    current_section["text"] = text
            else:
                # Add to root document text
                if root["text"]:
                    root["text"] += "\n\n" + text
                else:
                    root["text"] = text

    return root


def _clean_header_text(text: str) -> str:
    """
    Cleans header text to extract meaningful title.

    Args:
        text: Raw header text

    Returns:
        Cleaned title text
    """
    if not text:
        return "Untitled"

    # Remove common prefixes and formatting
    cleaned = text.strip()

    # Remove numbering patterns - be more specific to avoid removing first characters of actual titles
    patterns_to_remove = [
        r"^[IVX]+\.?\s+",  # Roman numerals followed by space (e.g., "I. ", "II ", "III. ")
        r"^\d+\.?\s+",  # Arabic numerals followed by space (e.g., "1. ", "2 ")
        r"^[A-Z]\.\s+",  # Single letter followed by period and space (e.g., "A. ")
        r"^\d+\.\d+\.?\s+",  # Subsection numbers followed by space (e.g., "1.1. ", "2.3 ")
        r"^\d+\.\d+\.\d+\.?\s+",  # Sub-subsection numbers followed by space (e.g., "1.1.1. ")
        r"^\(\d+\)\s+",  # Numbered items in parentheses followed by space (e.g., "(1) ")
        r"^\d+\)\s+",  # Numbered items with closing parenthesis followed by space (e.g., "1) ")
    ]

    for pattern in patterns_to_remove:
        # Only remove if it leaves meaningful text
        temp_cleaned = re.sub(pattern, "", cleaned)
        if temp_cleaned.strip() and len(temp_cleaned.strip()) >= 3:
            cleaned = temp_cleaned

    # Clean up extra whitespace and common artifacts
    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    # Remove trailing colons
    cleaned = cleaned.rstrip(":")

    # Capitalize first letter if it's all lowercase
    if cleaned and cleaned.islower():
        cleaned = cleaned[0].upper() + cleaned[1:]

    # If cleaning resulted in empty string or too short, return original with minimal cleanup
    if not cleaned or len(cleaned) < 3:
        cleaned = re.sub(r"\s+", " ", text).strip()

    return cleaned or "Untitled"
