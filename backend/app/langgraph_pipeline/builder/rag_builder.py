from langgraph.graph import StateGraph, END
from app.langgraph_pipeline.state import RAGGraphState
from app.langgraph_pipeline.nodes.rag_nodes import RAGNodes
from app.core.config import logger
from typing import Optional

rag_graph_app: Optional[StateGraph] = None


def build_rag_graph() -> StateGraph:
    global rag_graph_app
    if rag_graph_app:
        return rag_graph_app

    nodes = RAGNodes()
    workflow = StateGraph(RAGGraphState)

    # Add nodes - simplified to only use document retrieval
    workflow.add_node("retrieve_mongodb", nodes.retrieve_from_mongodb)
    workflow.add_node("generate_final_answer", nodes.generate_answer)

    # Define edges - simplified linear flow
    workflow.set_entry_point("retrieve_mongodb")
    workflow.add_edge("retrieve_mongodb", "generate_final_answer")
    workflow.add_edge("generate_final_answer", END)

    rag_graph_app = workflow.compile()
    logger.info("✅ Simplified RAG LangGraph App (Document-only) Compiled and Ready.")
    return rag_graph_app


def get_rag_app() -> StateGraph:
    if not rag_graph_app:
        return build_rag_graph()
    return rag_graph_app
