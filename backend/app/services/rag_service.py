from typing import List, Dict, Any
from langchain_core.prompts import PromptTemplate
from langchain.chains.retrieval import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_groq import ChatGroq
from langchain_mongodb import MongoDBAtlasVectorSearch
from langchain_huggingface.embeddings import HuggingFaceEmbeddings
from app.core.config import settings, logger
from app.db.mongodb_utils import get_db


class RAGService:
    """
    A service class for the Retrieval-Augmented Generation (RAG) pipeline
    that retrieves context from a pre-populated MongoDB Atlas Vector Search index.
    """

    def __init__(self, user_id: str, concept_map_id: str):
        """
        Initializes the RAGService.

        Args:
            user_id (str): The ID of the user to filter the search by.
            concept_map_id (str): The ID of the concept map to filter the search by.
        """
        self.user_id = user_id
        self.concept_map_id = concept_map_id
        self.embedding = HuggingFaceEmbeddings(
            model_name=settings.MODEL_NAME_FOR_EMBEDDING
        )
        self.llm = ChatGroq(
            temperature=0.1,
            groq_api_key=settings.GROQ_API_KEY,
            model_name=settings.LLM_MODEL_NAME_GROQ,
        )
        # Updated prompt specific to the CMVS project
        self.prompt = PromptTemplate.from_template(
            """
            You are an intelligent assistant for the Concept Map Visual Synthesizer (CMVS).
            Your purpose is to provide detailed, clear, and structured explanations about concepts found in the user's documents.

            Use the following retrieved context from the user's uploaded document to answer the question.
            The context is the most relevant information available. Do not use any outside knowledge.

            **Context:**
            ---------------------
            {context}
            ---------------------

            **Question:**
            {input}

            **Answer:**
            Provide a comprehensive answer formatted in markdown. If the context is insufficient,
            clearly state that the information is not available in the provided documents.
            """
        )
        db = get_db()
        self.collection = db[settings.MONGODB_CHUNKS_COLLECTION]

    async def run_rag(self, question: str, top_k: int) -> Dict[str, Any]:
        """
        Runs the RAG pipeline to answer a question by retrieving from MongoDB Atlas.

        Args:
            question (str): The question to answer.

        Returns:
            Dict[str, Any]: A dictionary containing the answer and the retrieved context.
        """
        try:
            # 1. Initialize the vector store to connect to the existing collection
            vectorstore = MongoDBAtlasVectorSearch(
                collection=self.collection,
                embedding=self.embedding,
                index_name=settings.MONGODB_ATLAS_VECTOR_SEARCH_INDEX_NAME,
            )
            logger.info("Successfully connected to MongoDB Atlas Vector Search index.")

            # 2. Create a retriever with pre-filtering for the specific user and map
            retriever_filter = {
                "user_id": self.user_id,
                "concept_map_id": self.concept_map_id,
            }
            retriever = vectorstore.as_retriever(
                search_kwargs={"k": top_k, "pre_filter": retriever_filter}
            )

            # 3. Set up and run the RAG chain
            question_answer_chain = create_stuff_documents_chain(self.llm, self.prompt)
            rag_chain = create_retrieval_chain(retriever, question_answer_chain)

            logger.info(
                f"Invoking RAG chain for user '{self.user_id}' with question: '{question}'"
            )
            response = await rag_chain.ainvoke({"input": question})
            logger.info("RAG pipeline completed successfully.")
            return response

        except Exception as e:
            logger.error(f"Error running RAG pipeline: {e}", exc_info=True)
            return {"error": str(e)}
