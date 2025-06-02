import re
from typing import List, Dict


def normalize_label(label: str) -> str:
    """Normalizes a node label for comparison."""
    return label.lower().strip()


def generate_mermaid_graph_syntax(triples: List[Dict[str, str]]) -> str:
    """
    Generates Mermaid syntax for a concept map (using graph TD).
    Handles unique node IDs and escaping for labels.
    """
    if not triples:
        return "graph TD\n  EmptyGraph[No concepts extracted or an error occurred.];"

    mermaid_string = "graph TD\n"
    # Node ID generation needs to be robust and consistent
    # Using a simple counter and sanitized label prefix
    # A more robust approach might map original labels to truly unique alphanumeric IDs if issues arise

    # Step 1: Collect all unique labels to define nodes first with proper escaping
    unique_labels = set()
    for triple in triples:
        unique_labels.add(str(triple.get("source", "UnknownSource")))
        unique_labels.add(str(triple.get("target", "UnknownTarget")))

    node_id_map = {}  # Maps original label to generated mermaid_id
    node_counter = 0
    for label in unique_labels:
        # Create a more robust ID: replace non-alphanumeric, ensure not empty, add counter
        # Basic sanitization for ID:
        temp_id = re.sub(r"\W+", "_", label)  # Replace non-alphanumeric with underscore
        temp_id = re.sub(
            r"^[^a-zA-Z_]+", "", temp_id
        )  # Ensure starts with letter or underscore
        if not temp_id:  # If label was all special characters or empty
            temp_id = f"concept_{node_counter}"
        else:
            temp_id = f"c_{node_counter}_{temp_id[:50]}"  # Add prefix and limit length

        node_id_map[label] = temp_id
        node_counter += 1

        # Escape quotes and backticks within the displayed label string
        # Mermaid handles most other special characters within quotes fine.
        display_label = label.replace('"', "#quot;").replace("`", "#gt;")
        mermaid_string += f'  {node_id_map[label]}["{display_label}"]\n'

    # Step 2: Add edges using the generated node IDs
    for triple in triples:
        source_label = str(triple.get("source", "UnknownSource"))
        target_label = str(triple.get("target", "UnknownTarget"))
        relation = (
            str(triple.get("relation", "related to"))
            .replace('"', "#quot;")
            .replace("`", "#gt;")
        )

        source_id = node_id_map.get(source_label)
        target_id = node_id_map.get(target_label)

        if source_id and target_id:  # Only add edge if both nodes were mapped
            mermaid_string += f'  {source_id} --"{relation}"--> {target_id}\n'
        else:
            # This case should ideally not happen if all labels are processed above
            # logger.warning(f"Could not find mapped ID for source '{source_label}' or target '{target_label}' for triple: {triple}")
            pass  # Silently skip if a node ID wasn't generated (should be rare)

    return mermaid_string
