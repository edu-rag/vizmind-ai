from typing import Optional
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from app.langgraph_pipeline.state import HierarchicalGraphState
from app.langgraph_pipeline.nodes.hierarchical_nodes import HierarchicalMindMapNodes
from app.core.config import settings, logger

# Global LangGraph app instance for hierarchical mind maps
hierarchical_langgraph_app: Optional[StateGraph] = None


def build_hierarchical_graph_instance() -> StateGraph:
    global hierarchical_langgraph_app
    if hierarchical_langgraph_app:
        return hierarchical_langgraph_app

    hierarchical_nodes_instance = HierarchicalMindMapNodes(
        groq_api_key=settings.GROQ_API_KEY
    )

    workflow = StateGraph(HierarchicalGraphState)

    # Define the nodes in the hierarchical processing graph
    workflow.add_node(
        "split_pages", hierarchical_nodes_instance.split_document_into_pages
    )
    workflow.add_node(
        "analyze_pages", hierarchical_nodes_instance.analyze_pages_individually
    )
    workflow.add_node(
        "synthesize_master", hierarchical_nodes_instance.synthesize_master_mindmap
    )
    workflow.add_node(
        "convert_to_json", hierarchical_nodes_instance.convert_to_hierarchical_json
    )
    workflow.add_node(
        "store_mindmap", hierarchical_nodes_instance.store_mindmap_in_mongodb
    )

    # Define the workflow edges
    workflow.set_entry_point("split_pages")
    workflow.add_edge("split_pages", "analyze_pages")
    workflow.add_edge("analyze_pages", "synthesize_master")
    workflow.add_edge("synthesize_master", "convert_to_json")
    workflow.add_edge("convert_to_json", "store_mindmap")
    workflow.add_edge("store_mindmap", END)

    # Compile the graph
    hierarchical_langgraph_app = workflow.compile()
    logger.info("✅ Hierarchical Mind Map LangGraph App Compiled and Ready.")
    return hierarchical_langgraph_app


def get_hierarchical_langgraph_app() -> StateGraph:
    if not hierarchical_langgraph_app:
        return build_hierarchical_graph_instance()
    return hierarchical_langgraph_app
