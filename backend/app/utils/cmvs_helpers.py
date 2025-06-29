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
            'AI', 'ML', 'API', 'CPU', 'GPU', 'RAM', 'SQL', 'XML', 'JSON', 'HTML',
            'CSS', 'PHP', 'iOS', 'UI', 'UX', 'SEO', 'CRM', 'ERP', 'ROI', 'KPI',
            'SDG', 'GDP', 'NASA', 'WHO', 'FAQ', 'CEO', 'CTO', 'HR', 'IT', 'PR'
        }:
            result_words.append(word.upper())
        else:
            # Title case for regular words
            result_words.append(word.lower().capitalize())
    
    return " ".join(result_words)


def generate_react_flow_data(triples: List[Dict[str, str]]) -> Dict[str, Any]:
    """
    Generates React Flow nodes and edges data structure from concept triples.
    Creates a mind map style layout with central concepts and branching structure.
    Returns a dict with 'nodes' and 'edges' arrays compatible with React Flow.
    """
    if not triples:
        return {
            "nodes": [
                {
                    "id": "empty-node",
                    "data": {"label": "No concepts extracted"},
                    "position": {"x": 400, "y": 300},
                    "type": "default",
                    "style": {
                        "background": "#f0f0f0",
                        "border": "2px solid #ccc",
                        "borderRadius": "10px",
                        "padding": "10px"
                    }
                }
            ],
            "edges": [],
        }

    # Step 1: Analyze node connectivity to identify central concepts
    node_connections = {}
    all_nodes = set()
    
    for triple in triples:
        source = str(triple.get("source", "UnknownSource"))
        target = str(triple.get("target", "UnknownTarget"))
        all_nodes.add(source)
        all_nodes.add(target)
        
        # Count connections for each node
        node_connections[source] = node_connections.get(source, 0) + 1
        node_connections[target] = node_connections.get(target, 0) + 1

    # Step 2: Identify central nodes (most connected) for mind map layout
    sorted_nodes = sorted(node_connections.items(), key=lambda x: x[1], reverse=True)
    central_nodes = [node for node, count in sorted_nodes[:3]]  # Top 3 most connected
    
    # Step 3: Create nodes with mind map style positioning
    nodes = []
    label_to_id = {}
    
    # Position central nodes
    center_x, center_y = 400, 300
    
    for i, (node_label, _) in enumerate(sorted_nodes):
        node_id = f"node-{i}"
        label_to_id[node_label] = node_id
        
        if node_label in central_nodes:
            # Central nodes positioning
            if len(central_nodes) == 1:
                x, y = center_x, center_y
            else:
                angle = (2 * math.pi * central_nodes.index(node_label)) / len(central_nodes)
                radius = 80  # Smaller radius for central nodes
                x = center_x + radius * math.cos(angle)
                y = center_y + radius * math.sin(angle)
            
            node_style = {
                "background": "#4285f4",
                "color": "white",
                "border": "3px solid #1a73e8",
                "borderRadius": "15px",
                "padding": "12px",
                "fontSize": "14px",
                "fontWeight": "bold"
            }
        else:
            # Peripheral nodes - arrange in outer circle
            peripheral_index = list(sorted_nodes).index((node_label, node_connections[node_label])) - len(central_nodes)
            peripheral_count = len(sorted_nodes) - len(central_nodes)
            
            if peripheral_count > 0:
                angle = (2 * math.pi * peripheral_index) / peripheral_count
                radius = 200 + (peripheral_count * 5)  # Dynamic radius based on count
                x = center_x + radius * math.cos(angle)
                y = center_y + radius * math.sin(angle)
            else:
                x, y = center_x + 150, center_y
            
            node_style = {
                "background": "#34a853",
                "color": "white", 
                "border": "2px solid #137333",
                "borderRadius": "10px",
                "padding": "8px",
                "fontSize": "12px"
            }

        nodes.append(
            {
                "id": node_id,
                "data": {"label": node_label},
                "position": {"x": int(x), "y": int(y)},
                "type": "default",
                "style": node_style
            }
        )

    # Step 4: Create edges with styling for mind maps
    edges = []
    edge_id_counter = 0

    for triple in triples:
        source_label = str(triple.get("source", "UnknownSource"))
        target_label = str(triple.get("target", "UnknownTarget"))
        relation = str(triple.get("relation", "related to"))

        source_id = label_to_id.get(source_label)
        target_id = label_to_id.get(target_label)

        if source_id and target_id and source_id != target_id:
            # Style edges differently based on whether they connect central nodes
            if source_label in central_nodes or target_label in central_nodes:
                edge_style = {
                    "stroke": "#1a73e8",
                    "strokeWidth": 3,
                    "strokeDasharray": "0"
                }
                label_style = {
                    "background": "white",
                    "border": "1px solid #1a73e8", 
                    "borderRadius": "5px",
                    "padding": "2px 6px",
                    "fontSize": "11px",
                    "fontWeight": "500"
                }
            else:
                edge_style = {
                    "stroke": "#137333",
                    "strokeWidth": 2,
                    "strokeDasharray": "5,5"
                }
                label_style = {
                    "background": "white",
                    "border": "1px solid #137333",
                    "borderRadius": "5px", 
                    "padding": "2px 4px",
                    "fontSize": "10px"
                }

            edges.append(
                {
                    "id": f"edge-{edge_id_counter}",
                    "source": source_id,
                    "target": target_id,
                    "label": relation,
                    "type": "default",
                    "style": edge_style,
                    "labelStyle": label_style
                }
            )
            edge_id_counter += 1

    return {"nodes": nodes, "edges": edges}
