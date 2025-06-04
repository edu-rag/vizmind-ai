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

    # Add nodes
    workflow.add_node("retrieve_mongodb", nodes.retrieve_from_mongodb)
    workflow.add_node("grade_db_retrieval", nodes.grade_db_retrieval)
    workflow.add_node("web_search", nodes.perform_web_search)
    workflow.add_node(
        "generate_final_answer", nodes.generate_answer
    )  # Single generation node

    # Define edges
    workflow.set_entry_point("retrieve_mongodb")
    workflow.add_edge("retrieve_mongodb", "grade_db_retrieval")

    # Conditional edge after grading
    workflow.add_conditional_edges(
        "grade_db_retrieval",
        lambda state: state["db_retrieval_status"],  # Condition based on this state key
        {
            "generate_from_db": "generate_final_answer",  # If DB docs are enough
            "perform_web_search": "web_search",  # If web search is needed
        },
    )
    workflow.add_edge(
        "web_search", "generate_final_answer"
    )  # Web search results go to final answer generation
    workflow.add_edge("generate_final_answer", END)

    rag_graph_app = workflow.compile()
    logger.info("✅ RAG LangGraph App Compiled and Ready.")
    return rag_graph_app


def get_rag_app() -> StateGraph:
    if not rag_graph_app:
        return build_rag_graph()
    return rag_graph_app
