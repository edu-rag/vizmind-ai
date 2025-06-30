import re
import math
from typing import List, Dict, Any, Optional


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


def generate_react_flow_data(
    triples: List[Dict[str, str]],
    hierarchical_concepts: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Generates React Flow nodes and edges data structure from document structure.
    Enhanced to support hierarchical layout based on document structure (FR-002, FR-005).
    Returns a dict with 'nodes' and 'edges' arrays compatible with React Flow.

    Args:
        triples: List of structural relationships (parent-child edges from document hierarchy)
        hierarchical_concepts: Hierarchical structure with nodes and metadata
    """
    print(
        f"[generate_react_flow_data] Processing {len(triples)} structural triples with hierarchical support"
    )

    # If we have hierarchical concepts with nodes, use those directly
    if hierarchical_concepts and "nodes" in hierarchical_concepts:
        return _generate_react_flow_from_structure(hierarchical_concepts, triples)

    # Fallback to triple-based generation
    if not triples:
        print("[generate_react_flow_data] No triples provided, returning empty node")
        return {
            "nodes": [
                {
                    "id": "empty-node",
                    "type": "default",
                    "data": {"label": "No document structure found"},
                    "position": {"x": 250, "y": 150},
                }
            ],
            "edges": [],
        }

    # Collect all unique nodes from triples with hierarchy information
    all_nodes = {}  # Use dict to track node metadata
    for triple in triples:
        source = str(triple.get("source", "")).strip()
        target = str(triple.get("target", "")).strip()

        if source:
            all_nodes[source] = {
                "label": source,
                "level": _determine_node_level(source, hierarchical_concepts),
            }
        if target:
            all_nodes[target] = {
                "label": target,
                "level": _determine_node_level(target, hierarchical_concepts),
            }

    print(
        f"[generate_react_flow_data] Found {len(all_nodes)} unique nodes with hierarchy"
    )

    # Create nodes with hierarchical layout
    nodes = []
    label_to_id = {}

    # Sort nodes by hierarchy level for better layout
    sorted_nodes = sorted(all_nodes.items(), key=lambda x: x[1]["level"])

    # Use hierarchical layout
    positioned_nodes = _create_hierarchical_layout(sorted_nodes)

    for node_info in positioned_nodes:
        node_id = node_info["id"]
        label_to_id[node_info["original_label"]] = node_id
        nodes.append(node_info)

    # Create edges from triples
    edges = []
    edge_id_counter = 0

    for triple in triples:
        source_label = str(triple.get("source", "")).strip()
        target_label = str(triple.get("target", "")).strip()
        relation = str(triple.get("relation", "contains")).strip()

        source_id = label_to_id.get(source_label)
        target_id = label_to_id.get(target_label)

        if source_id and target_id and source_id != target_id:
            # Create enhanced edge format
            edge = {
                "id": f"edge-{edge_id_counter}",
                "source": source_id,
                "target": target_id,
                "type": "default",
                "style": _get_edge_style(relation),
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


def _generate_react_flow_from_structure(
    hierarchical_structure: Dict[str, Any], triples: List[Dict[str, str]]
) -> Dict[str, Any]:
    """
    Generate React Flow data directly from hierarchical document structure.
    Implements FR-002: Node Generation from Headers and FR-005: Edge Generation.
    """
    print(
        f"[_generate_react_flow_from_structure] Generating from document structure with {len(hierarchical_structure.get('nodes', []))} header nodes"
    )

    nodes = []
    edges = []
    label_to_id = {}

    # Get nodes from hierarchical structure
    structure_nodes = hierarchical_structure.get("nodes", [])
    title = hierarchical_structure.get("title")

    # Add title node if present
    if title and title not in [node.get("label") for node in structure_nodes]:
        title_node = {
            "id": "title-node",
            "type": "default",
            "data": {
                "label": normalize_label(title),
                "level": 0,
                "summary": f"Document: {title}",
                "content": "",
                "isTitle": True,
            },
            "position": {"x": 400, "y": 50},
            "style": _get_node_style(0),
        }
        nodes.append(title_node)
        label_to_id[title] = "title-node"

    # Create nodes from structure
    for i, node_data in enumerate(structure_nodes):
        node_id = f"header-{i}"
        label = node_data.get("label", "")
        level = node_data.get("level", 4)
        summary = node_data.get("summary", "")
        content = node_data.get("content", "")

        # Calculate position based on hierarchy
        position = _calculate_hierarchical_position(node_data, i, structure_nodes)

        react_flow_node = {
            "id": node_id,
            "type": "default",
            "data": {
                "label": normalize_label(label),
                "level": level,
                "summary": summary,
                "content": content,  # For RAG (FR-006)
                "fullPath": node_data.get("full_path", label),
                "isHeader": True,
            },
            "position": position,
            "style": _get_node_style(level),
        }

        nodes.append(react_flow_node)
        label_to_id[label] = node_id

    # Create edges from triples (parent-child relationships)
    edge_id_counter = 0
    for triple in triples:
        source_label = triple.get("source", "").strip()
        target_label = triple.get("target", "").strip()
        relation = triple.get("relation", "contains")

        source_id = label_to_id.get(source_label)
        target_id = label_to_id.get(target_label)

        if source_id and target_id and source_id != target_id:
            edge = {
                "id": f"edge-{edge_id_counter}",
                "source": source_id,
                "target": target_id,
                "type": "default",
                "style": _get_edge_style(relation),
                "animated": False,
            }

            if relation and relation != "contains":
                edge["label"] = relation

            edges.append(edge)
            edge_id_counter += 1

    print(
        f"[_generate_react_flow_from_structure] Generated {len(nodes)} nodes and {len(edges)} edges from document structure"
    )
    return {"nodes": nodes, "edges": edges}


def _calculate_hierarchical_position(
    node_data: Dict[str, Any], index: int, all_nodes: List[Dict[str, Any]]
) -> Dict[str, int]:
    """Calculate position for a node based on its hierarchical level and relationships."""
    level = node_data.get("level", 4)
    parent_headers = node_data.get("parent_headers", [])

    # Y position based on hierarchy level
    level_y_positions = {0: 50, 1: 200, 2: 350, 3: 500, 4: 650}
    y_position = level_y_positions.get(level, 650)

    # X position based on sibling order at same level
    same_level_nodes = [n for n in all_nodes if n.get("level") == level]
    sibling_index = 0

    for i, sibling in enumerate(same_level_nodes):
        if sibling.get("label") == node_data.get("label"):
            sibling_index = i
            break

    # Spread nodes horizontally with some spacing
    x_spacing = 250
    x_offset = 100
    x_position = x_offset + (sibling_index * x_spacing)

    # Add some offset based on parent to avoid overlap
    if parent_headers:
        parent_offset = (
            len(parent_headers[-1]) * 5
        )  # Small offset based on parent name length
        x_position += parent_offset

    return {"x": x_position, "y": y_position}


def _determine_node_level(
    node_label: str, hierarchical_concepts: Optional[Dict[str, Any]]
) -> int:
    """Determine the hierarchy level of a node based on hierarchical concepts structure."""
    if not hierarchical_concepts or not node_label:
        return 4  # Default to body level

    # Check if node exists in document level (highest)
    document_concepts = [
        c.get("text", c) if isinstance(c, dict) else c
        for c in hierarchical_concepts.get("document_level", [])
    ]
    if any(
        node_label.lower() in concept.lower() or concept.lower() in node_label.lower()
        for concept in document_concepts
    ):
        return 0

    # Check chapter level
    chapter_concepts = [
        c.get("text", c) if isinstance(c, dict) else c
        for c in hierarchical_concepts.get("chapter_level", [])
    ]
    if any(
        node_label.lower() in concept.lower() or concept.lower() in node_label.lower()
        for concept in chapter_concepts
    ):
        return 2

    # Check section level
    section_concepts = [
        c.get("text", c) if isinstance(c, dict) else c
        for c in hierarchical_concepts.get("section_level", [])
    ]
    if any(
        node_label.lower() in concept.lower() or concept.lower() in node_label.lower()
        for concept in section_concepts
    ):
        return 3

    return 4  # Default to body level


def _create_hierarchical_layout(sorted_nodes: List[tuple]) -> List[Dict[str, Any]]:
    """Create a hierarchical layout based on node levels."""
    positioned_nodes = []
    level_counts = {}
    level_y_positions = {
        0: 50,
        1: 200,
        2: 350,
        3: 500,
        4: 650,
    }  # Y positions for each level

    for i, (label, node_data) in enumerate(sorted_nodes):
        node_id = f"node-{i}"
        level = node_data["level"]

        # Count nodes at this level
        if level not in level_counts:
            level_counts[level] = 0

        # Calculate X position based on node index at this level
        x_spacing = 300
        x_offset = 100
        x_position = x_offset + (level_counts[level] * x_spacing)
        y_position = level_y_positions.get(level, 650)

        # Create node with hierarchy-aware styling
        node = {
            "id": node_id,
            "type": "default",
            "data": {
                "label": normalize_label(label),
                "level": level,  # Add level info for potential frontend styling
            },
            "position": {"x": x_position, "y": y_position},
            "style": _get_node_style(level),
        }

        node["original_label"] = label  # Keep for edge mapping
        positioned_nodes.append(node)
        level_counts[level] += 1

        print(
            f"[_create_hierarchical_layout] Positioned node '{label}' at level {level}, position ({x_position}, {y_position})"
        )

    return positioned_nodes


def _create_grid_layout(sorted_nodes: List[tuple]) -> List[Dict[str, Any]]:
    """Create a grid layout for nodes (fallback when no hierarchy info)."""
    positioned_nodes = []
    grid_size = math.ceil(math.sqrt(len(sorted_nodes)))
    spacing_x = 200
    spacing_y = 150
    start_x = 100
    start_y = 100

    for i, (label, node_data) in enumerate(sorted_nodes):
        node_id = f"node-{i}"

        # Calculate grid position
        row = i // grid_size
        col = i % grid_size
        x = start_x + (col * spacing_x)
        y = start_y + (row * spacing_y)

        # Create minimal node format
        node = {
            "id": node_id,
            "type": "default",
            "data": {"label": normalize_label(label)},
            "position": {"x": x, "y": y},
        }

        node["original_label"] = label  # Keep for edge mapping
        positioned_nodes.append(node)
        print(f"[_create_grid_layout] Created node: {node}")

    return positioned_nodes


def _get_node_style(level: int) -> Dict[str, Any]:
    """Get styling for nodes based on hierarchy level."""
    styles = {
        0: {  # Document level (main title)
            "background": "#1f2937",
            "color": "white",
            "fontSize": "16px",
            "fontWeight": "bold",
            "padding": "12px",
            "border": "2px solid #3b82f6",
            "borderRadius": "8px",
            "minWidth": "150px",
        },
        1: {  # Chapter level
            "background": "#3b82f6",
            "color": "white",
            "fontSize": "14px",
            "fontWeight": "600",
            "padding": "10px",
            "border": "2px solid #1e40af",
            "borderRadius": "6px",
            "minWidth": "130px",
        },
        2: {  # Section level
            "background": "#60a5fa",
            "color": "white",
            "fontSize": "13px",
            "fontWeight": "500",
            "padding": "8px",
            "border": "1px solid #2563eb",
            "borderRadius": "5px",
            "minWidth": "120px",
        },
        3: {  # Subsection level
            "background": "#93c5fd",
            "color": "#1e40af",
            "fontSize": "12px",
            "fontWeight": "normal",
            "padding": "6px",
            "border": "1px solid #3b82f6",
            "borderRadius": "4px",
            "minWidth": "110px",
        },
        4: {  # Body/concept level
            "background": "#f1f5f9",
            "color": "#334155",
            "fontSize": "12px",
            "fontWeight": "normal",
            "padding": "6px",
            "border": "1px solid #cbd5e1",
            "borderRadius": "4px",
            "minWidth": "100px",
        },
    }

    return styles.get(level, styles[4])


def _get_edge_style(relation: str) -> Dict[str, Any]:
    """Get styling for edges based on relation type."""
    relation_lower = relation.lower()

    if relation_lower in ["contains", "includes", "has"]:
        return {"stroke": "#1f2937", "strokeWidth": 3}
    elif relation_lower in ["implements", "uses", "applies"]:
        return {"stroke": "#3b82f6", "strokeWidth": 2}
    elif relation_lower in ["leads to", "results in", "causes"]:
        return {"stroke": "#059669", "strokeWidth": 2}
    elif relation_lower in ["depends on", "requires", "needs"]:
        return {"stroke": "#dc2626", "strokeWidth": 2}
    else:
        return {"stroke": "#6b7280", "strokeWidth": 1}


def generate_hierarchical_react_flow_data(
    hierarchical_concepts: Dict[str, Any], triples: List[Dict[str, str]]
) -> Dict[str, Any]:
    """
    Generate React Flow data specifically optimized for hierarchical concept maps.
    This function implements FR-005: Node and Edge Creation with hierarchy awareness.
    """
    if not hierarchical_concepts and not triples:
        return generate_react_flow_data([])

    # Use the enhanced generate_react_flow_data with hierarchical information
    return generate_react_flow_data(triples, hierarchical_concepts)
