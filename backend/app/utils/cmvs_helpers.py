import re
import math
from typing import List, Dict, Any


def normalize_label(label: str) -> str:
    """Normalizes a node label for comparison."""
    return label.lower().strip()


def generate_react_flow_data(triples: List[Dict[str, str]]) -> Dict[str, Any]:
    """
    Generates React Flow nodes and edges data structure from concept triples.
    Returns a dict with 'nodes' and 'edges' arrays compatible with React Flow.
    """
    if not triples:
        return {
            "nodes": [
                {
                    "id": "empty-node",
                    "data": {"label": "No concepts extracted"},
                    "position": {"x": 100, "y": 100},
                    "type": "default",
                }
            ],
            "edges": [],
        }

    # Step 1: Collect all unique labels
    unique_labels = set()
    for triple in triples:
        unique_labels.add(str(triple.get("source", "UnknownSource")))
        unique_labels.add(str(triple.get("target", "UnknownTarget")))

    # Step 2: Create nodes with positions
    nodes = []
    label_to_id = {}

    # Calculate positions in a circular layout
    num_nodes = len(unique_labels)
    center_x, center_y = 300, 300
    radius = max(150, num_nodes * 30)  # Dynamic radius based on node count

    for i, label in enumerate(sorted(unique_labels)):
        # Generate unique, React Flow compatible ID
        node_id = f"node-{i}"
        label_to_id[label] = node_id

        # Calculate position in circular layout
        if num_nodes == 1:
            x, y = center_x, center_y
        else:
            angle = (2 * math.pi * i) / num_nodes
            x = center_x + radius * math.cos(angle)
            y = center_y + radius * math.sin(angle)

        nodes.append(
            {
                "id": node_id,
                "data": {"label": label},
                "position": {"x": int(x), "y": int(y)},
                "type": "default",
            }
        )

    # Step 3: Create edges
    edges = []
    edge_id_counter = 0

    for triple in triples:
        source_label = str(triple.get("source", "UnknownSource"))
        target_label = str(triple.get("target", "UnknownTarget"))
        relation = str(triple.get("relation", "related to"))

        source_id = label_to_id.get(source_label)
        target_id = label_to_id.get(target_label)

        if source_id and target_id and source_id != target_id:
            edges.append(
                {
                    "id": f"edge-{edge_id_counter}",
                    "source": source_id,
                    "target": target_id,
                    "label": relation,
                    "type": "default",
                }
            )
            edge_id_counter += 1

    return {"nodes": nodes, "edges": edges}
