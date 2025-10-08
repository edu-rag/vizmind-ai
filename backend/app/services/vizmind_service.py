"""
VizMind AI service that orchestrates LangGraph workflows.
This service replaces the old direct service calls with proper LangGraph workflow execution.
"""

from typing import Dict, Any, Optional, List
from bson import ObjectId

from app.core.config import logger
from app.langgraph_pipeline.builder.graph_builder import (
    execute_document_processing,
    execute_rag_workflow,
)
from app.models.cmvs_models import (
    HierarchicalNode,
    MindMapResponse,
    AttachmentInfo,
    NodeDetailResponse,
    CitationSource,
    WorkflowMetrics,
)


class VizMindAIService:
    """
    Main service for VizMind AI that coordinates document processing and RAG workflows.
    """

    def __init__(self):
        """Initialize the VizMind AI service."""
        logger.info("VizMind AI Service initialized")

    async def process_document_and_generate_mindmap(
        self,
        file_path: str,
        user_id: str,
        s3_path: Optional[str],
        original_filename: str,
        map_id: Optional[str] = None,
    ) -> MindMapResponse:
        """
        Process a document and generate a mind map using the LangGraph workflow.

        Args:
            file_path: Path to the document file
            user_id: User identifier
            s3_path: S3 storage path (optional)
            original_filename: Original filename
            map_id: Optional concept map ID (will generate if not provided)

        Returns:
            MindMapResponse with the generated mind map or error information
        """
        logger.info(f"[VizMindAI] Starting document processing for {original_filename}")

        # Generate concept map ID if not provided
        if not map_id:
            map_id = str(ObjectId())

        # Prepare attachment info
        attachment_info = AttachmentInfo(
            filename=original_filename, s3_path=s3_path, status="processing"
        )

        try:
            # Execute the document processing workflow
            result = await execute_document_processing(
                file_path=file_path,
                user_id=user_id,
                map_id=map_id,
                s3_path=s3_path,
                original_filename=original_filename,
            )

            # Check if processing was successful
            if result.get("stage") == "completed":
                hierarchical_data = result.get("hierarchical_data")

                if hierarchical_data:
                    # Convert to Pydantic model
                    hierarchical_node = HierarchicalNode(**hierarchical_data)

                    # Prepare processing metadata
                    processing_metadata = {
                        "processing_time": self._calculate_processing_time(result),
                        "chunk_count": result.get("chunk_count"),
                        "embedding_dimension": result.get("embedding_dimension"),
                        "stage": result.get("stage"),
                    }

                    attachment_info.status = "success"

                    logger.info(
                        f"[VizMindAI] Document processing completed successfully for {original_filename}"
                    )

                    return MindMapResponse(
                        attachment=attachment_info,
                        status="success",
                        hierarchical_data=hierarchical_node,
                        mongodb_doc_id=map_id,
                        processing_metadata=processing_metadata,
                    )
                else:
                    error_msg = "No hierarchical data generated"
                    logger.error(f"[VizMindAI] {error_msg}")
                    attachment_info.status = "error"
                    attachment_info.error_message = error_msg

                    return MindMapResponse(
                        attachment=attachment_info,
                        status="error",
                        error_message=error_msg,
                    )
            else:
                # Processing failed
                error_msg = result.get(
                    "error_message",
                    f"Processing failed at stage: {result.get('stage')}",
                )
                logger.error(f"[VizMindAI] Document processing failed: {error_msg}")

                attachment_info.status = "error"
                attachment_info.error_message = error_msg

                return MindMapResponse(
                    attachment=attachment_info, status="error", error_message=error_msg
                )

        except Exception as e:
            error_msg = f"Unexpected error during document processing: {str(e)}"
            logger.error(f"[VizMindAI] {error_msg}", exc_info=True)

            attachment_info.status = "error"
            attachment_info.error_message = error_msg

            return MindMapResponse(
                attachment=attachment_info, status="error", error_message=error_msg
            )

    async def query_mind_map(
        self,
        user_id: str,
        map_id: str,
        query: str,
        top_k: int = 10,
        node_id: str = None,
        node_label: str = None,
        node_children: List[str] = None,
    ) -> NodeDetailResponse:
        """
        Query a mind map using the RAG workflow.

        Args:
            user_id: User identifier
            map_id: Concept map identifier
            query: User question
            top_k: Number of documents to retrieve
            node_id: ID of the clicked mind map node (optional, for context)
            node_label: Label of the clicked mind map node (optional, for context)
            node_children: List of child node labels (optional, for hierarchical context)

        Returns:
            NodeDetailResponse with the answer and citations
        """
        logger.info(f"[VizMindAI] Starting RAG query for user {user_id}, map {map_id}")
        if node_label:
            logger.info(f"[VizMindAI] Node context: {node_label}")
            if node_children:
                logger.info(
                    f"[VizMindAI] Node has {len(node_children)} children: {node_children[:3]}{'...' if len(node_children) > 3 else ''}"
                )

        try:
            # Execute the RAG workflow with node context
            result = await execute_rag_workflow(
                user_id=user_id,
                map_id=map_id,
                query=query,
                top_k=top_k,
                node_id=node_id,
                node_label=node_label,
                node_children=node_children,
            )

            # Check if RAG was successful
            if result.get("stage") == "completed":
                generated_answer = result.get("generated_answer", "No answer generated")
                cited_sources_data = result.get("cited_sources", [])
                confidence_score = result.get("confidence_score", 0.0)

                # Convert citation sources to Pydantic models
                cited_sources = [
                    CitationSource(**source) for source in cited_sources_data
                ]

                # Calculate total processing time
                processing_time = result.get("retrieval_time", 0) + result.get(
                    "generation_time", 0
                )

                logger.info(
                    f"[VizMindAI] RAG query completed successfully with {len(cited_sources)} citations"
                )

                return NodeDetailResponse(
                    query=query,
                    answer=generated_answer,
                    cited_sources=cited_sources,
                    confidence_score=confidence_score,
                    processing_time=processing_time,
                )
            else:
                # RAG failed
                error_msg = result.get(
                    "error_message", f"RAG failed at stage: {result.get('stage')}"
                )
                logger.error(f"[VizMindAI] RAG query failed: {error_msg}")

                return NodeDetailResponse(
                    query=query,
                    answer="I apologize, but I encountered an error while processing your question. Please try again or contact support if the issue persists.",
                    cited_sources=[],
                    message=error_msg,
                )

        except Exception as e:
            error_msg = f"Unexpected error during RAG query: {str(e)}"
            logger.error(f"[VizMindAI] {error_msg}", exc_info=True)

            return NodeDetailResponse(
                query=query,
                answer="I apologize, but I encountered an unexpected error while processing your question. Please try again or contact support if the issue persists.",
                cited_sources=[],
                message=error_msg,
            )

    def _calculate_processing_time(self, result: Dict[str, Any]) -> Optional[float]:
        """Calculate total processing time from workflow result."""
        start_time_str = result.get("processing_start_time")
        end_time_str = result.get("processing_end_time")

        if start_time_str and end_time_str:
            try:
                from datetime import datetime

                start_time = datetime.fromisoformat(start_time_str)
                end_time = datetime.fromisoformat(end_time_str)
                return (end_time - start_time).total_seconds()
            except Exception as e:
                logger.warning(f"Failed to calculate processing time: {e}")

        return None

    async def get_workflow_metrics(self, map_id: str) -> Optional[WorkflowMetrics]:
        """
        Get workflow metrics for a completed processing job.

        Args:
            map_id: Concept map identifier

        Returns:
            WorkflowMetrics if available, None otherwise
        """
        try:
            from app.db.mongodb_utils import get_db
            from app.core.config import settings

            db = get_db()
            maps_collection = db[settings.MONGODB_MAPS_COLLECTION]

            # Find the document
            doc = maps_collection.find_one({"_id": map_id})

            if doc and "processing_metadata" in doc:
                metadata = doc["processing_metadata"]

                return WorkflowMetrics(
                    processing_time_seconds=metadata.get("processing_time"),
                    chunk_count=metadata.get("chunk_count"),
                    embedding_dimension=metadata.get("embedding_dimension"),
                )

            return None

        except Exception as e:
            logger.error(f"Failed to retrieve workflow metrics: {e}", exc_info=True)
            return None
