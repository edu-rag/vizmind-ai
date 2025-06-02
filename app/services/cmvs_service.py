from app.langgraph_pipeline.builder import get_langgraph_app
from app.langgraph_pipeline.state import GraphState
from app.core.config import logger
import uuid


async def run_cmvs_pipeline(initial_state: GraphState) -> GraphState:
    logger.info(
        f"Running CMVS pipeline for file: {initial_state.get('current_filename')}, User: {initial_state.get('user_id')}"
    )
    langgraph_app = get_langgraph_app()

    # Ensure a unique thread_id for each run if using MemorySaver or similar checkpointers
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    final_state = await langgraph_app.ainvoke(initial_state, config=config)
    logger.info(
        f"CMVS pipeline finished for file: {initial_state.get('current_filename')}"
    )
    return final_state
