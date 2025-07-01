import re
import math
from typing import List, Dict, Any


def normalize_label(label: str) -> str:
    """
    Normalizes a node label for comparison, with special handling for conceptual terms.
    Preserves meaningful capitalization and removes excessive whitespace.
    """
    if not label:
        return ""

    # Remove extra whitespace and normalize
    normalized = " ".join(label.strip().split())

    # Convert to title case for better readability in mind maps
    # But preserve common acronyms and technical terms
    words = normalized.split()
    result_words = []

    for word in words:
        # Keep common acronyms uppercase
        if (len(word) <= 4 and word.isupper()) or word.upper() in {
            "AI",
            "ML",
            "API",
            "CPU",
            "GPU",
            "RAM",
            "SQL",
            "XML",
            "JSON",
            "HTML",
            "CSS",
            "PHP",
            "iOS",
            "UI",
            "UX",
            "SEO",
            "CRM",
            "ERP",
            "ROI",
            "KPI",
            "SDG",
            "GDP",
            "NASA",
            "WHO",
            "FAQ",
            "CEO",
            "CTO",
            "HR",
            "IT",
            "PR",
        }:
            result_words.append(word.upper())
        else:
            # Title case for regular words
            result_words.append(word.lower().capitalize())

    return " ".join(result_words)


# Legacy ReactFlow data generation function removed
# The new hierarchical mind map system uses a different data structure
# See: langgraph_pipeline/nodes/ for the new hierarchical processing
