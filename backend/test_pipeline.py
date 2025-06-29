"""
Test script to verify the complete CMVS pipeline after fixing the Groq API error.
"""

import asyncio
import sys
import os

# Add the app directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), "app"))

from app.langgraph_pipeline.state import GraphState
from app.services.cmvs_service import run_cmvs_pipeline
from app.core.config import logger


async def test_complete_pipeline():
    """Test the complete CMVS pipeline with sample text."""

    # Sample text that should generate meaningful triples
    sample_text = """
    Artificial Intelligence (AI) is a branch of computer science that aims to create intelligent machines. 
    Machine Learning is a subset of AI that enables computers to learn without being explicitly programmed.
    Deep Learning is a subset of Machine Learning that uses neural networks with multiple layers.
    Natural Language Processing (NLP) is an area of AI that helps computers understand human language.
    Computer Vision is another important area of AI that enables machines to interpret visual information.
    """

    # Create initial state
    initial_state = GraphState(
        original_text=sample_text,
        text_chunks=[],
        embedded_chunks=[],
        raw_triples=[],
        processed_triples=[],
        react_flow_data={},
        mongodb_doc_id=None,
        mongodb_chunk_ids=[],
        error_message=None,
        current_filename="test_ai_concepts.txt",
        s3_path=None,
        user_id="test_user_123",
    )

    try:
        logger.info("🚀 Starting complete CMVS pipeline test...")

        # Run the complete pipeline
        final_state = await run_cmvs_pipeline(initial_state)

        # Check results
        if final_state.get("error_message"):
            logger.error(
                f"❌ Pipeline failed with error: {final_state['error_message']}"
            )
            return False

        # Verify each stage
        text_chunks = final_state.get("text_chunks", [])
        embedded_chunks = final_state.get("embedded_chunks", [])
        raw_triples = final_state.get("raw_triples", [])
        processed_triples = final_state.get("processed_triples", [])
        react_flow_data = final_state.get("react_flow_data", {})
        mongodb_doc_id = final_state.get("mongodb_doc_id")

        logger.info(f"✅ Text chunking: {len(text_chunks)} chunks created")
        logger.info(f"✅ Embedding: {len(embedded_chunks)} chunks embedded")
        logger.info(f"✅ Triple extraction: {len(raw_triples)} raw triples extracted")
        logger.info(f"✅ Triple processing: {len(processed_triples)} processed triples")
        logger.info(
            f"✅ React Flow generation: {len(react_flow_data.get('nodes', []))} nodes, {len(react_flow_data.get('edges', []))} edges"
        )
        logger.info(
            f"✅ MongoDB storage: {'Success' if mongodb_doc_id else 'Skipped/Failed'}"
        )

        # Show some sample results
        if raw_triples:
            logger.info("📊 Sample raw triples:")
            for i, triple in enumerate(raw_triples[:3]):
                logger.info(
                    f"  {i+1}. {triple['source']} --[{triple['relation']}]--> {triple['target']}"
                )

        if processed_triples:
            logger.info("🔄 Sample processed triples:")
            for i, triple in enumerate(processed_triples[:3]):
                logger.info(
                    f"  {i+1}. {triple['source']} --[{triple['relation']}]--> {triple['target']}"
                )

        if react_flow_data and react_flow_data.get("nodes"):
            logger.info("🎨 React Flow data preview:")
            nodes = react_flow_data.get("nodes", [])
            edges = react_flow_data.get("edges", [])
            logger.info(f"  Nodes: {len(nodes)} total")
            for i, node in enumerate(nodes[:3]):
                logger.info(
                    f"    {i+1}. {node['data']['label']} at ({node['position']['x']}, {node['position']['y']})"
                )
            if len(nodes) > 3:
                logger.info("    ...")
            logger.info(f"  Edges: {len(edges)} total")
            for i, edge in enumerate(edges[:3]):
                logger.info(
                    f"    {i+1}. {edge['source']} --[{edge.get('label', '')}]--> {edge['target']}"
                )
            if len(edges) > 3:
                logger.info("    ...")

        # Overall success check
        success = (
            len(text_chunks) > 0
            and len(embedded_chunks) > 0
            and len(raw_triples) > 0
            and len(processed_triples) > 0
            and len(react_flow_data.get("nodes", [])) > 0
        )

        if success:
            logger.info(
                "🎉 Complete pipeline test PASSED! All stages working correctly."
            )
            return True
        else:
            logger.error("❌ Pipeline test FAILED! Some stages produced no output.")
            return False

    except Exception as e:
        logger.error(f"❌ Pipeline test FAILED with exception: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    asyncio.run(test_complete_pipeline())
