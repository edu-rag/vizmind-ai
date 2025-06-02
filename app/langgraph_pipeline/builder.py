from typing import Optional
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from app.langgraph_pipeline.state import GraphState
from app.langgraph_pipeline.nodes import CMVSNodes
from app.core.config import settings, logger

# Global LangGraph app instance
cmvs_langgraph_app: Optional[StateGraph] = None  # Correct type hint


def build_graph_instance() -> StateGraph:
    global cmvs_langgraph_app
    if cmvs_langgraph_app:
        return cmvs_langgraph_app

    cmvs_nodes_instance = CMVSNodes(
        groq_api_key=settings.GROQ_API_KEY,
        embedding_model_name=settings.MODEL_NAME_FOR_EMBEDDING,
    )
    workflow = StateGraph(GraphState)

    # Define the nodes in the graph
    workflow.add_node("chunk_text", cmvs_nodes_instance.chunk_text)
    workflow.add_node("embed_chunks", cmvs_nodes_instance.embed_text_chunks)
    workflow.add_node("extract_main_map", cmvs_nodes_instance.extract_main_concept_map)
    workflow.add_node("process_main_map_graph", cmvs_nodes_instance.process_graph_data)
    workflow.add_node("generate_main_map_mermaid", cmvs_nodes_instance.generate_mermaid)
    workflow.add_node("store_db", cmvs_nodes_instance.store_cmvs_data_in_mongodb)

    workflow.set_entry_point("chunk_text")
    workflow.add_edge("chunk_text", "embed_chunks")
    workflow.add_edge("embed_chunks", "extract_main_map")
    workflow.add_edge("extract_main_map", "process_main_map_graph")
    workflow.add_edge("process_main_map_graph", "generate_main_map_mermaid")
    workflow.add_edge("generate_main_map_mermaid", "store_db")
    workflow.add_edge("store_db", END)

    # Compile the graph
    # memory = MemorySaver() # Example checkpointer
    # For production, you might use a more persistent checkpointer like ` langchain_community.graph_checkpoints.sqlite.SqliteSaver`
    # Example with SqliteSaver:
    # import sqlite3
    # memory = SqliteSaver(conn=sqlite3.connect("langgraph_checkpoints.sqlite"))
    cmvs_langgraph_app = workflow.compile()
    logger.info(
        "✅ CMVS LangGraph App (for main idea map & chunk storage) Compiled and Ready."
    )
    return cmvs_langgraph_app


def get_langgraph_app() -> StateGraph:
    if not cmvs_langgraph_app:
        return build_graph_instance()
    return cmvs_langgraph_app
