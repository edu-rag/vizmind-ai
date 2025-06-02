from typing import Optional
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from app.langgraph_pipeline.state import GraphState
from app.langgraph_pipeline.nodes import CMVSNodes
from app.core.config import settings, logger

# Global LangGraph app instance
cmvs_langgraph_app: Optional[StateGraph] = None


def build_graph_instance() -> (
    StateGraph
):  # Renamed to avoid confusion with build_graph in nodes
    global cmvs_langgraph_app
    if cmvs_langgraph_app:
        return cmvs_langgraph_app

    cmvs_nodes_instance = CMVSNodes(
        groq_api_key=settings.GROQ_API_KEY,
        embedding_model_name=settings.MODEL_NAME_FOR_EMBEDDING,
    )
    workflow = StateGraph(GraphState)
    # ... (add nodes and edges as previously defined) ...
    workflow.add_node("chunk_text", cmvs_nodes_instance.chunk_text)
    workflow.add_node("embed_chunks", cmvs_nodes_instance.embed_text_chunks)
    workflow.add_node(
        "extract_triples", cmvs_nodes_instance.extract_triples_from_chunks
    )
    workflow.add_node("process_graph", cmvs_nodes_instance.process_graph_data)
    workflow.add_node("generate_mermaid", cmvs_nodes_instance.generate_mermaid)
    workflow.add_node("store_db", cmvs_nodes_instance.store_cmvs_data_in_mongodb)

    workflow.set_entry_point("chunk_text")
    workflow.add_edge("chunk_text", "embed_chunks")
    workflow.add_edge("embed_chunks", "extract_triples")
    workflow.add_edge("extract_triples", "process_graph")
    workflow.add_edge("process_graph", "generate_mermaid")
    workflow.add_edge("generate_mermaid", "store_db")
    workflow.add_edge("store_db", END)

    memory = MemorySaver()  # Consider more persistent checkpointers for production
    cmvs_langgraph_app = workflow.compile(checkpointer=memory)
    logger.info("✅ CMVS LangGraph App Compiled and Ready.")
    return cmvs_langgraph_app


def get_langgraph_app() -> StateGraph:
    if not cmvs_langgraph_app:
        return build_graph_instance()  # Ensure it's built if accessed directly
    return cmvs_langgraph_app
