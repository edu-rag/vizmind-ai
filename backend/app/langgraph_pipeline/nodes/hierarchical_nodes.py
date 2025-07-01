import re
import json
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

# Langchain & supporting libs
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser

# App specific imports
from app.core.config import settings, logger
from app.langgraph_pipeline.state import HierarchicalGraphState, PageAnalysisResult
from app.models.cmvs_models import PageAnalysisLLM, MasterSynthesisLLM, HierarchicalNode
from app.db.mongodb_utils import get_db
from pymongo import ReturnDocument

try:
    from pymongo.common import UTC
except ImportError:
    import datetime as pydt

    UTC = pydt.timezone.utc


class HierarchicalMindMapNodes:
    def __init__(self, groq_api_key: str):
        logger.info("Initializing HierarchicalMindMapNodes")
        self.llm = ChatGroq(
            temperature=0.1,
            groq_api_key=groq_api_key,
            model_name=settings.LLM_MODEL_NAME_GROQ,
        )
        logger.info("HierarchicalMindMapNodes initialized.")

    def _split_text_into_pages(self, text: str) -> List[str]:
        """
        Split text into logical pages. This is a simple implementation.
        In a real scenario, you might want to use PDF page boundaries.
        """
        # Simple splitting by paragraph breaks and length
        paragraphs = text.split("\n\n")
        pages = []
        current_page = ""

        for paragraph in paragraphs:
            if len(current_page) + len(paragraph) > 2000:  # ~2000 chars per page
                if current_page:
                    pages.append(current_page.strip())
                current_page = paragraph
            else:
                current_page += "\n\n" + paragraph if current_page else paragraph

        if current_page:
            pages.append(current_page.strip())

        return pages if pages else [text]  # Return at least one page

    async def split_document_into_pages(
        self, state: HierarchicalGraphState
    ) -> Dict[str, Any]:
        """Split the document into logical pages for processing."""

        logger.info(
            f"--- Node: Splitting Document into Pages (File: {state['attachment']['filename']}) ---"
        )

        try:
            attachment = state["attachment"]
            text = attachment["extracted_text"]

            pages = self._split_text_into_pages(text)

            # Update attachment with pages
            updated_attachment = attachment.copy()
            updated_attachment["pages"] = pages

            logger.info(f"Split document into {len(pages)} pages")

            return {
                "attachment": updated_attachment,
                "page_analyses": [],  # Initialize empty
            }

        except Exception as e:
            logger.error(f"Error in split_document_into_pages: {e}")
            return {"error_message": f"Failed to split document: {str(e)}"}

    async def analyze_pages_individually(
        self, state: HierarchicalGraphState
    ) -> Dict[str, Any]:
        """Stage 1: Analyze each page individually using PageProcessorAgent."""

        logger.info(
            f"--- Node: Analyzing Pages Individually (File: {state['attachment']['filename']}) ---"
        )

        try:
            pages = state["attachment"]["pages"]
            page_analyses = []

            # Page Analyzer Prompt
            page_analyzer_template = """You are a Page Analyzer Agent. Your task is to analyze a single page of a document and extract the key topics and important points into a structured markdown format.

INSTRUCTIONS:
1. Identify the main topics/themes discussed on this page
2. Extract key points, concepts, and important details
3. Organize them in a clear hierarchical markdown structure
4. Use appropriate markdown headers (##, ###) to show relationships
5. Use bullet points for lists of related items
6. Focus on concepts that would be useful in a mind map

INPUT PAGE TEXT:
{page_text}

OUTPUT FORMAT: Provide clean markdown with topics and key points organized hierarchically."""

            page_parser = PydanticOutputParser(pydantic_object=PageAnalysisLLM)
            page_prompt = ChatPromptTemplate.from_template(
                page_analyzer_template + "\n\n{format_instructions}"
            )

            page_chain = page_prompt | self.llm | page_parser

            for i, page_text in enumerate(pages, 1):
                logger.info(f"Analyzing page {i}/{len(pages)}")

                try:
                    result = await page_chain.ainvoke(
                        {
                            "page_text": page_text,
                            "format_instructions": page_parser.get_format_instructions(),
                        }
                    )

                    page_analysis = PageAnalysisResult(
                        page_number=i,
                        page_text=page_text,
                        page_markdown=result.page_markdown,
                    )
                    page_analyses.append(page_analysis)

                except Exception as e:
                    logger.error(f"Error analyzing page {i}: {e}")
                    # Continue with a fallback
                    page_analysis = PageAnalysisResult(
                        page_number=i,
                        page_text=page_text,
                        page_markdown=f"## Page {i} Content\n{page_text[:500]}...",
                    )
                    page_analyses.append(page_analysis)

            logger.info(f"Completed analysis of {len(page_analyses)} pages")

            return {"page_analyses": page_analyses}

        except Exception as e:
            logger.error(f"Error in analyze_pages_individually: {e}")
            return {"error_message": f"Failed to analyze pages: {str(e)}"}

    async def synthesize_master_mindmap(
        self, state: HierarchicalGraphState
    ) -> Dict[str, Any]:
        """Stage 2: Synthesize all page analyses into a master hierarchical mind map."""

        logger.info(
            f"--- Node: Synthesizing Master Mind Map (File: {state['attachment']['filename']}) ---"
        )

        try:
            page_analyses = state["page_analyses"]

            # Combine all page markdowns
            all_page_notes = (
                "\n\n"
                + "=" * 50
                + "\n\n".join(
                    [
                        f"PAGE {analysis['page_number']} NOTES:\n{analysis['page_markdown']}"
                        for analysis in page_analyses
                    ]
                )
            )

            # Master Synthesizer Prompt
            master_synthesizer_template = """You are a Master Synthesizer Agent. Your task is to consolidate all the page-by-page analysis notes into a single, comprehensive hierarchical mind map structure.

INSTRUCTIONS:
1. Review all the page notes and identify the main themes/topics
2. Consolidate related concepts from different pages
3. Create a clear hierarchical structure suitable for a mind map
4. Use markdown headers to show the hierarchy: # for main title, ## for major topics, ### for subtopics, #### for details
5. Organize logically and remove redundancy
6. Focus on creating a structure that shows relationships between concepts

ALL PAGE NOTES:
{all_page_notes}

OUTPUT REQUIREMENTS:
- Start with a single main title (# Title)
- Use consistent markdown hierarchy 
- Group related concepts together
- Create a structure that would work well as a visual mind map
- Ensure each level adds meaningful detail to the parent level"""

            master_parser = PydanticOutputParser(pydantic_object=MasterSynthesisLLM)
            master_prompt = ChatPromptTemplate.from_template(
                master_synthesizer_template + "\n\n{format_instructions}"
            )

            master_chain = master_prompt | self.llm | master_parser

            logger.info("Invoking master synthesizer")

            result = await master_chain.ainvoke(
                {
                    "all_page_notes": all_page_notes,
                    "format_instructions": master_parser.get_format_instructions(),
                }
            )

            logger.info(f"Master synthesis completed. Title: {result.title}")

            return {
                "consolidated_markdown": result.hierarchical_markdown,
                "document_title": result.title,
            }

        except Exception as e:
            logger.error(f"Error in synthesize_master_mindmap: {e}")
            return {"error_message": f"Failed to synthesize mind map: {str(e)}"}

    def _parse_markdown_to_hierarchy(
        self, markdown_text: str, title: str
    ) -> HierarchicalNode:
        """
        Parse hierarchical markdown into nested JSON structure.
        """
        lines = markdown_text.split("\n")
        root = HierarchicalNode(id="root", data={"label": title}, children=[])

        # Stack to track current hierarchy level
        stack = [root]
        node_counter = 0

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Determine hierarchy level
            level = 0
            if line.startswith("####"):
                level = 4
                content = line[4:].strip()
            elif line.startswith("###"):
                level = 3
                content = line[3:].strip()
            elif line.startswith("##"):
                level = 2
                content = line[2:].strip()
            elif line.startswith("#"):
                level = 1
                content = line[1:].strip()
            elif line.startswith("-") or line.startswith("*"):
                level = len(stack)  # Bullet points go under current level
                content = line[1:].strip()
            else:
                continue  # Skip non-header, non-bullet lines

            if not content:
                continue

            # Adjust stack to current level
            while len(stack) > level:
                stack.pop()

            # Create new node
            node_counter += 1
            new_node = HierarchicalNode(
                id=f"node-{node_counter}", data={"label": content}, children=[]
            )

            # Add to current parent
            if stack:
                stack[-1].children.append(new_node)
                stack.append(new_node)
            else:
                # This shouldn't happen with proper markdown, but handle it
                root.children.append(new_node)
                stack = [root, new_node]

        return root

    async def convert_to_hierarchical_json(
        self, state: HierarchicalGraphState
    ) -> Dict[str, Any]:
        """Convert the consolidated markdown to hierarchical JSON structure."""

        logger.info(
            f"--- Node: Converting to Hierarchical JSON (File: {state['attachment']['filename']}) ---"
        )

        try:
            markdown_text = state["consolidated_markdown"]
            title = state["document_title"]

            hierarchical_data = self._parse_markdown_to_hierarchy(markdown_text, title)

            logger.info("Successfully converted markdown to hierarchical JSON")

            return {"hierarchical_data": hierarchical_data.model_dump()}

        except Exception as e:
            logger.error(f"Error in convert_to_hierarchical_json: {e}")
            return {"error_message": f"Failed to convert to JSON: {str(e)}"}

    async def store_mindmap_in_mongodb(
        self, state: HierarchicalGraphState
    ) -> Dict[str, Any]:
        """Store the hierarchical mind map in MongoDB."""

        logger.info(
            f"--- Node: Storing Mind Map in MongoDB (File: {state['attachment']['filename']}) ---"
        )

        try:
            db = get_db()
            mindmaps_collection = db[settings.MONGODB_CMVS_COLLECTION]

            # Prepare document for storage
            mindmap_doc = {
                "user_id": state["user_id"],
                "title": state["document_title"],
                "original_filename": state["attachment"]["filename"],
                "s3_path": state["attachment"]["s3_path"],
                "hierarchical_data": state["hierarchical_data"],
                "consolidated_markdown": state["consolidated_markdown"],
                "created_at": datetime.now(UTC),
                "updated_at": datetime.now(UTC),
                "type": "hierarchical_mindmap",
            }

            # Insert document
            result = mindmaps_collection.insert_one(mindmap_doc)
            mongodb_doc_id = str(result.inserted_id)

            logger.info(f"Stored mind map with ID: {mongodb_doc_id}")

            return {"mongodb_doc_id": mongodb_doc_id}

        except Exception as e:
            logger.error(f"Error in store_mindmap_in_mongodb: {e}")
            return {"error_message": f"Failed to store in database: {str(e)}"}
