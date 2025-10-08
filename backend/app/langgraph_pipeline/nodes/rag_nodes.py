"""
RAG nodes for VizMind AI LangGraph workflow.
Handles retrieval, grading, and answer generation.
"""

from typing import Dict, Any, List
from langchain_core.documents import Document
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_groq import ChatGroq
from langchain_mongodb import MongoDBAtlasVectorSearch
from langchain_huggingface.embeddings import HuggingFaceEmbeddings
from langchain_core.messages import HumanMessage, AIMessage
import time
import json

from app.core.config import settings, logger
from app.db.mongodb_utils import get_db
from app.langgraph_pipeline.state import RAGState, transition_stage, set_error


async def retrieve_documents_node(state: RAGState) -> RAGState:
    """
    Node to retrieve relevant documents from MongoDB Atlas Vector Search.
    """
    logger.info(
        f"[RAG] Starting document retrieval for query: '{state['query'][:100]}...'"
    )

    try:
        start_time = time.time()

        # Initialize embedding model
        embedding_model = HuggingFaceEmbeddings(
            model_name=settings.MODEL_NAME_FOR_EMBEDDING
        )

        # Connect to MongoDB collection
        db = get_db()
        collection = db[settings.MONGODB_CHUNKS_COLLECTION]

        # Initialize vector store
        vectorstore = MongoDBAtlasVectorSearch(
            collection=collection,
            embedding=embedding_model,
            index_name=settings.MONGODB_ATLAS_VECTOR_INDEX_NAME,
        )

        # Set up retriever with filtering
        retriever_filter = {
            "user_id": state["user_id"],
            "map_id": state["map_id"],
        }

        top_k = state.get("top_k", 10)
        retriever = vectorstore.as_retriever(
            search_kwargs={"k": top_k, "pre_filter": retriever_filter}
        )

        # Retrieve documents
        retrieved_docs = await retriever.ainvoke(state["query"])

        state["retrieved_documents"] = retrieved_docs
        state["total_documents_found"] = len(retrieved_docs)
        state["retrieval_time"] = time.time() - start_time

        logger.info(
            f"[RAG] Retrieved {len(retrieved_docs)} documents in {state['retrieval_time']:.2f}s"
        )

        return transition_stage(state, "documents_retrieved")

    except Exception as e:
        logger.error(f"[RAG] Document retrieval failed: {e}", exc_info=True)
        return set_error(state, f"Document retrieval failed: {str(e)}")


async def grade_documents_node(state: RAGState) -> RAGState:
    """
    Node to grade retrieved documents for relevance to the query and node context.
    """
    logger.info("[RAG] Starting document grading")

    try:
        retrieved_docs = state.get("retrieved_documents", [])
        if not retrieved_docs:
            logger.warning("[RAG] No documents to grade")
            state["filtered_documents"] = []
            state["relevance_scores"] = []
            state["relevant_documents_count"] = 0
            return transition_stage(state, "documents_graded")

        logger.info(f"[RAG] Grading {len(retrieved_docs)} documents")

        # Initialize LLM for grading
        llm = ChatGroq(
            temperature=0.0,
            groq_api_key=settings.GROQ_API_KEY,
            model_name=settings.LLM_MODEL_NAME_GROQ,
        )

        # Build context-aware grading prompt with hierarchical information
        node_context = ""
        if state.get("node_label"):
            node_context = f"\n\n**Mind Map Node Context:** {state['node_label']}"

            # Add children context if available (for scope understanding)
            if state.get("node_children") and len(state["node_children"]) > 0:
                children_list = ", ".join(
                    state["node_children"][:5]
                )  # Limit to first 5
                if len(state["node_children"]) > 5:
                    children_list += f", and {len(state['node_children']) - 5} more"
                node_context += f"\nThis node covers subtopics: {children_list}"

            node_context += "\n\nThe question is asked in the context of this specific topic from the mind map."

        # Enhanced grading prompt with node context
        grading_prompt = ChatPromptTemplate.from_template(
            """
            You are a grader assessing the relevance of a retrieved document to a user question for VizMind AI.
            
            Your task is to determine if the document contains information that could help answer the question.
            {node_context}
            
            Give a binary score 'yes' or 'no' to indicate whether the document is relevant.
            - Answer 'yes' if the document discusses the topic or provides information helpful for answering the question
            - Answer 'no' if the document is completely unrelated or off-topic
            
            Provide your answer as a single word: 'yes' or 'no'.
            
            Question: {question}
            
            Document: {document}
            
            Relevance Score:
            """
        )

        grading_chain = grading_prompt | llm | StrOutputParser()

        # Grade each document
        relevant_docs = []
        relevance_scores = []

        for doc in retrieved_docs:
            try:
                score_result = await grading_chain.ainvoke(
                    {
                        "question": state["query"],
                        "document": doc.page_content,
                        "node_context": node_context,
                    }
                )

                is_relevant = score_result.lower().strip() == "yes"
                relevance_scores.append(1.0 if is_relevant else 0.0)

                if is_relevant:
                    relevant_docs.append(doc)

            except Exception as doc_error:
                logger.warning(f"[RAG] Failed to grade document: {doc_error}")
                relevance_scores.append(0.0)

        state["filtered_documents"] = relevant_docs
        state["relevance_scores"] = relevance_scores
        state["relevant_documents_count"] = len(relevant_docs)

        logger.info(
            f"[RAG] Graded {len(retrieved_docs)} documents, {len(relevant_docs)} relevant"
        )

        return transition_stage(state, "documents_graded")

    except Exception as e:
        logger.error(f"[RAG] Document grading failed: {e}", exc_info=True)
        return set_error(state, f"Document grading failed: {str(e)}")


async def generate_answer_node(state: RAGState) -> RAGState:
    """
    Node to generate the final answer using relevant documents and node context.
    """
    logger.info("[RAG] Starting answer generation")

    try:
        start_time = time.time()

        relevant_docs = state.get("filtered_documents", [])

        # Ensure relevant_docs is never None
        if relevant_docs is None:
            relevant_docs = []

        # Initialize LLM
        llm = ChatGroq(
            temperature=0.1,
            groq_api_key=settings.GROQ_API_KEY,
            model_name=settings.LLM_MODEL_NAME_GROQ,
        )

        # Build node context for focused answering
        node_context_section = ""
        if state.get("node_label"):
            node_context_section = f"""
**Mind Map Node Context:**
The user clicked on the mind map node: "{state['node_label']}"

"""
            # Add hierarchical context if children are available
            if state.get("node_children") and len(state["node_children"]) > 0:
                children_preview = state["node_children"][:5]  # Show first 5 children
                children_text = ", ".join(f'"{child}"' for child in children_preview)
                if len(state["node_children"]) > 5:
                    children_text += (
                        f", and {len(state['node_children']) - 5} more subtopics"
                    )

                node_context_section += f"""This node encompasses the following subtopics: {children_text}

"""

            node_context_section += """**Important Instructions:**
- Focus your answer on the main node topic: "{node_label}"
- The subtopics listed provide scope context but should NOT be detailed individually
- Provide a cohesive answer about the main concept
- Only mention subtopics briefly if they help explain the main concept
- Keep the response focused and relevant to what the user is exploring

""".replace(
                "{node_label}", state["node_label"]
            )

        # Enhanced answer generation prompt for VizMind AI with node awareness
        answer_prompt = PromptTemplate.from_template(
            """
            You are an intelligent assistant for VizMind AI, a mind mapping platform that helps users understand complex documents.
            
            Your role is to provide comprehensive, accurate, and well-structured answers based on the user's document content.
            {node_context}
            **Retrieved Context from User's Document:**
            {context}
            
            **User Question:**
            {question}
            
            **Instructions:**
            1. **Answer based ONLY on the provided context** - do not use external knowledge
            2. **Focus on the mind map node topic** - if a node context is provided, prioritize information related to that specific concept
            3. **Be comprehensive but concise** - provide detailed explanations while staying focused on what matters
            4. **Structure your response** using markdown formatting:
               - Use headers (##) for main sections
               - Use bullet points for lists
               - Use **bold** for key concepts
               - Use code blocks for technical content if needed
            5. **If context is insufficient**, clearly state what information is missing
            6. **Be specific** - reference particular concepts, data, or examples from the context
            7. **Connect to the node context** - if the question relates to a specific mind map node, explain how the answer connects to that concept
            8. **Maintain professional tone** suitable for educational/business contexts
            
            **Answer:**
            """
        )

        # Prepare context from relevant documents
        if relevant_docs:
            context = "\n\n".join(
                [
                    f"**Document Section {i+1}:**\n{doc.page_content}"
                    for i, doc in enumerate(relevant_docs)
                ]
            )
        else:
            context = "No relevant information found in the uploaded document."

        # Generate answer
        answer_chain = answer_prompt | llm | StrOutputParser()
        generated_answer = await answer_chain.ainvoke(
            {
                "context": context,
                "question": state["query"],
                "node_context": node_context_section,
            }
        )

        # Prepare citation sources
        cited_sources = []
        if relevant_docs:  # Only iterate if we have documents
            for i, doc in enumerate(relevant_docs):
                source = {
                    "type": "mongodb_chunk",
                    "identifier": doc.metadata.get("chunk_id", f"chunk_{i}"),
                    "title": doc.metadata.get("original_filename", "Unknown Document"),
                    "snippet": (
                        doc.page_content[:200] + "..."
                        if len(doc.page_content) > 200
                        else doc.page_content
                    ),
                    "page_number": doc.metadata.get("page_number"),
                }
                cited_sources.append(source)

        # Calculate confidence score based on number of relevant documents and node context
        base_confidence = min(1.0, len(relevant_docs) / 3.0) if relevant_docs else 0.0
        # Boost confidence if node context is provided (indicates focused query)
        if state.get("node_label"):
            confidence_boost = 0.1
            confidence_score = min(1.0, base_confidence + confidence_boost)
        else:
            confidence_score = base_confidence

        state["generated_answer"] = generated_answer
        state["cited_sources"] = cited_sources
        state["confidence_score"] = confidence_score
        state["generation_time"] = time.time() - start_time

        # Add to conversation history
        messages = state.get("messages", [])
        messages.extend(
            [HumanMessage(content=state["query"]), AIMessage(content=generated_answer)]
        )
        state["messages"] = messages

        logger.info(
            f"[RAG] Answer generated successfully in {state['generation_time']:.2f}s"
        )

        return transition_stage(state, "answer_generated")

    except Exception as e:
        logger.error(f"[RAG] Answer generation failed: {e}", exc_info=True)
        return set_error(state, f"Answer generation failed: {str(e)}")


async def finalize_rag_node(state: RAGState) -> RAGState:
    """
    Node to finalize the RAG workflow and prepare response.
    """
    logger.info("[RAG] Finalizing RAG workflow")

    try:
        # Log performance metrics
        metrics = {
            "query_length": len(state["query"]),
            "retrieval_time": state.get("retrieval_time", 0),
            "generation_time": state.get("generation_time", 0),
            "total_documents_found": state.get("total_documents_found", 0),
            "relevant_documents_count": state.get("relevant_documents_count", 0),
            "confidence_score": state.get("confidence_score", 0),
            "answer_length": len(state.get("generated_answer", "")),
            "citations_count": len(state.get("cited_sources", [])),
        }

        logger.info(
            f"[RAG] Workflow completed with metrics: {json.dumps(metrics, indent=2)}"
        )

        return transition_stage(state, "completed")

    except Exception as e:
        logger.error(f"[RAG] Finalization failed: {e}", exc_info=True)
        return set_error(state, f"Finalization failed: {str(e)}")


# Router functions for conditional logic
def should_continue_after_retrieval(state: RAGState) -> str:
    """Router to determine next step after document retrieval."""
    retrieved_docs = state.get("retrieved_documents", [])

    if not retrieved_docs:
        logger.warning(
            "[RAG] No documents retrieved, proceeding to answer generation with empty context"
        )
        return "generate_answer"

    return "grade_documents"


def should_continue_after_grading(state: RAGState) -> str:
    """Router to determine next step after document grading."""
    relevant_docs = state.get("filtered_documents", [])

    # Always proceed to answer generation, even with no relevant docs
    return "generate_answer"


def should_retry_retrieval(state: RAGState) -> str:
    """Router to determine if retrieval should be retried."""
    retry_count = state.get("retry_count", 0)
    max_retries = 2

    if retry_count < max_retries and state.get("stage") == "failed":
        logger.info(f"[RAG] Retrying retrieval, attempt {retry_count + 1}")
        return "retrieve_documents"

    return "finalize"
