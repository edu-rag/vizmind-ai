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


def generate_react_flow_data(triples: List[Dict[str, str]]) -> Dict[str, Any]:
    """
    Generates React Flow nodes and edges data structure from concept triples.
    Uses minimal React Flow format as per documentation.
    Returns a dict with 'nodes' and 'edges' arrays compatible with React Flow.
    """
    print(f"[generate_react_flow_data] Processing {len(triples)} triples")

    if not triples:
        print("[generate_react_flow_data] No triples provided, returning empty node")
        return {
            "nodes": [
                {
                    "id": "empty-node",
                    "type": "default",
                    "data": {"label": "No concepts extracted"},
                    "position": {"x": 250, "y": 150},
                }
            ],
            "edges": [],
        }

    # Collect all unique nodes from triples
    all_nodes = set()
    for triple in triples:
        source = str(triple.get("source", "")).strip()
        target = str(triple.get("target", "")).strip()
        if source:
            all_nodes.add(source)
        if target:
            all_nodes.add(target)

    print(
        f"[generate_react_flow_data] Found {len(all_nodes)} unique nodes: {list(all_nodes)}"
    )

    # Create nodes with simple grid layout
    nodes = []
    label_to_id = {}
    node_list = list(all_nodes)

    # Calculate grid dimensions
    grid_size = math.ceil(math.sqrt(len(node_list)))
    spacing_x = 200
    spacing_y = 150
    start_x = 100
    start_y = 100

    for i, node_label in enumerate(node_list):
        node_id = f"node-{i}"
        label_to_id[node_label] = node_id

        # Calculate grid position
        row = i // grid_size
        col = i % grid_size
        x = start_x + (col * spacing_x)
        y = start_y + (row * spacing_y)

        # Create minimal node format
        node = {
            "id": node_id,
            "type": "default",
            "data": {"label": normalize_label(node_label)},
            "position": {"x": x, "y": y},
        }
        nodes.append(node)
        print(f"[generate_react_flow_data] Created node: {node}")

    # Create edges from triples
    edges = []
    edge_id_counter = 0

    for triple in triples:
        source_label = str(triple.get("source", "")).strip()
        target_label = str(triple.get("target", "")).strip()
        relation = str(triple.get("relation", "related to")).strip()

        source_id = label_to_id.get(source_label)
        target_id = label_to_id.get(target_label)

        if source_id and target_id and source_id != target_id:
            # Create minimal edge format
            edge = {
                "id": f"edge-{edge_id_counter}",
                "source": source_id,
                "target": target_id,
                "type": "default",
            }

            # Add label if relation is meaningful
            if relation and relation.lower() not in ["", "related to", "relates to"]:
                edge["label"] = relation

            edges.append(edge)
            edge_id_counter += 1
            print(f"[generate_react_flow_data] Created edge: {edge}")
        else:
            print(
                f"[generate_react_flow_data] Skipped invalid edge: source='{source_label}' -> target='{target_label}' (source_id={source_id}, target_id={target_id})"
            )

    print(
        f"[generate_react_flow_data] Final result: {len(nodes)} nodes, {len(edges)} edges"
    )
    return {"nodes": nodes, "edges": edges}
