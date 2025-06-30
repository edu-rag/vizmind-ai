# AI-Powered Concept Map Visual Synthesizer (CMVS) & RAG Q&A API

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)](https://fastapi.tiangolo.com)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.4+-orange.svg)](https://langchain-ai.github.io/langgraph/)
[![MongoDB](https://img.shields.io/badge/MongoDB-Atlas-green.svg)](https://mongodb.com)

This project provides a powerful FastAPI backend to automatically transform PDF documents into interactive concept maps and enables users to ask contextual questions about the content using a Retrieval Augmented Generation (RAG) pipeline. It features secure authentication via Google Sign-In with JWT, data storage on MongoDB Atlas (including vector embeddings for semantic search), and PDF storage on S3-compatible services.

## Features

* **PDF to Concept Map**: Upload PDF documents to generate a high-level concept map focusing on main ideas.
* **S3 Integration**: Original PDF documents are securely stored in an S3-compatible bucket.
* **MongoDB Atlas Integration**:
    * Stores user profiles.
    * Saves generated concept map data (triples, Mermaid code, S3 paths).
    * Stores chunked text from PDFs along with their vector embeddings for semantic search.
* **RAG Q&A Pipeline**:
    * Ask questions about concepts within a generated map.
    * Retrieves relevant context from stored document chunks using MongoDB Atlas Vector Search.
    * Intelligent grading of retrieved context by an LLM.
    * Conditional fallback to web search (Tavily API, focused on verified sites like Wikipedia and scientific journals) if initial context is insufficient.
    * LLM-generated answers with cited sources (from both database chunks and web results).
* **LangGraph Orchestration**: Complex workflows for CMVS generation and RAG Q&A are managed using LangGraph.
* **Secure Authentication**:
    * Google Sign-In for user authentication.
    * JWT (JSON Web Tokens) for securing API endpoints.
* **LLM Powered**: Utilizes LLMs (via Groq for speed) for concept extraction, grading, and answer generation.
* **Structured API**: Built with FastAPI, providing interactive API documentation (Swagger UI).
* **Modular Codebase**: Organized into a structured package for better maintainability and scalability.

## Architecture Overview

The application is built around a FastAPI backend with several key components:

* **API Layer**: Exposes RESTful endpoints for authentication, concept map generation, and Q&A.
* **Service Layer**: Contains the business logic for user management, PDF processing, S3 interaction, and orchestrating the LangGraph pipelines.
* **LangGraph Pipelines**:
    1.  **CMVS Pipeline**: Handles PDF text extraction, chunking, embedding, main idea concept map generation (triples), Mermaid diagram code generation, and storage.
    2.  **RAG Q&A Pipeline**: Manages retrieval of relevant chunks from MongoDB Atlas, LLM-based grading of context, conditional web search fallback, and final answer generation with citations.
* **Data Stores**:
    * **MongoDB Atlas**: Stores user data, concept map metadata, and text chunks with their vector embeddings (leveraging Atlas Vector Search).
    * **S3-compatible storage**: Stores original uploaded PDF files.
* **External Services**:
    * **Google OAuth**: For user sign-in.
    * **Groq API**: For fast LLM inference.
    * **HuggingFace Embedding Models**: For generating text embeddings.
    * **Tavily API**: For targeted web searches as a fallback.

## Application Flow Diagrams (Mermaid)

### 1. High-Level System Overview

```mermaid
graph LR
    subgraph User_Client [User Client / Frontend]
        direction LR
        UserAction1[User Signs In via Google]
        UserAction2[User Uploads PDFs for Concept Map]
        UserAction3[User Taps Node or Asks Question about Concept]
    end

    subgraph FastAPI_Backend [FastAPI Backend API]
        direction LR
        AuthRouter["/api/v1/auth (Google, JWT)"]
        CMVSRouter["/api/v1/maps/generate/ (PDFs)"]
        RAGQnARouter["/api/v1/maps/ask/ (Question)"]
    end

    subgraph External_Services_Stores [External Services & Data Stores]
        direction LR
        GoogleOAuth[Google OAuth Service]
        S3[S3 Storage]
        MongoDB[MongoDB Atlas <br/> - Users <br/> - CMVS Docs <br/> - ChunkEmbeddings]
        GroqLLM[Groq LLM Service]
        EmbeddingModels[HuggingFace Embedding Models]
        WebSearch[Tavily Search API]
    end

    UserAction1 --> AuthRouter
    AuthRouter --> GoogleOAuth
    AuthRouter --> MongoDB

    UserAction2 -->|JWT Auth| CMVSRouter
    CMVSRouter --> S3
    CMVSRouter --> GroqLLM
    CMVSRouter --> EmbeddingModels
    CMVSRouter --> MongoDB

    UserAction3 -->|JWT Auth| RAGQnARouter
    RAGQnARouter --> MongoDB
    RAGQnARouter --> EmbeddingModels
    RAGQnARouter --> GroqLLM
    RAGQnARouter --> WebSearch

    style User_Client fill:#D1E8FF,stroke:#333,stroke-width:2px
    style FastAPI_Backend fill:#E8D1FF,stroke:#333,stroke-width:2px
    style External_Services_Stores fill:#D1FFD1,stroke:#333,stroke-width:2px
```
**Detailed Explanation:**

This diagram provides a **high-level architectural overview** of the system.

* **User Client / Frontend**: Represents the user's interface (e.g., a web application). It shows the primary actions a user can take:
    * `User Signs In via Google`: Initiates the authentication process.
    * `User Uploads PDFs for Concept Map`: The core feature for generating concept maps.
    * `User Taps Node or Asks Question about Concept`: Interaction for knowledge retrieval (RAG).
* **FastAPI Backend API**: This is your main application server. It exposes specific API endpoint groups:
    * `/api/v1/auth`: Handles user authentication, interacting with Google OAuth and your user database.
    * `/api/v1/maps/generate/`: Receives PDF uploads (after JWT authentication) to trigger the CMVS pipeline.
    * `/api/v1/maps/ask/`: Receives questions about specific concepts within a map (after JWT authentication) to trigger the RAG pipeline.
* **External Services & Data Stores**: These are the third-party services and databases your backend relies on:
    * `Google OAuth Service`: For verifying user identities.
    * `S3 Storage`: For storing uploaded PDF files.
    * `MongoDB Atlas`: The primary database for storing user profiles, generated concept map documents (including Mermaid code and metadata), and critically, the chunked text with its vector embeddings for semantic search.
    * `Groq LLM Service`: Provides the Large Language Models for tasks like concept extraction, relevance grading, and answer generation.
    * `HuggingFace Embedding Models`: Used to generate vector embeddings for text chunks and queries.
    * `Tavily Search API`: Used as a web search fallback within the RAG pipeline to find external context from verified sites.

The **arrows** indicate the primary direction of requests and data flow. For instance, user actions trigger calls to specific API routers, which in turn interact with various external services to fulfill the request. Note the "JWT Auth" labels, indicating that those API interactions require prior authentication.

---

### 2. Authentication Flow (Google Sign-In & JWT)
```mermaid
sequenceDiagram
    actor User
    participant Frontend
    participant GoogleOAuth as Google<br>OAuth Service
    participant Backend_Auth as FastAPI Backend<br>(/api/v1/auth/google)
    participant MongoDB_Users as MongoDB<br>(Users Collection)

    User->>Frontend: Clicks "Sign in with Google"
    Frontend->>GoogleOAuth: Initiates Google Sign-In
    GoogleOAuth-->>User: Google Auth Screen
    User->>GoogleOAuth: Authenticates
    GoogleOAuth-->>Frontend: Returns Google ID Token

    Frontend->>Backend_Auth: POST /google (sends Google ID Token)
    Backend_Auth->>GoogleOAuth: Verifies ID Token
    GoogleOAuth-->>Backend_Auth: Token Status (Valid/Invalid)
    alt Token Valid
        Backend_Auth->>MongoDB_Users: Find or Create/Update User
        MongoDB_Users-->>Backend_Auth: User Document
        Backend_Auth->>Backend_Auth: Generates JWT (Access Token)
        Backend_Auth-->>Frontend: Returns JWT & User Info
        Frontend->>Frontend: Stores JWT
    else Token Invalid
        Backend_Auth-->>Frontend: Authentication Error (401)
    end
    Note over Frontend, Backend_Auth: Subsequent API calls include JWT in<br>Authorization: Bearer header.
```


**Detailed Explanation:**

This **sequence diagram** illustrates the step-by-step process of user authentication.

1.  **User Initiation**: The `User` interacts with the `Frontend`, typically by clicking a "Sign in with Google" button.
2.  **Google OAuth Flow**:
    * The `Frontend` redirects or opens a pop-up to `Google OAuth Service`.
    * Google handles the user's sign-in process (credentials, 2FA, consent).
    * Upon successful authentication, Google returns a short-lived `Google ID Token` to the `Frontend`.
3.  **Backend Token Verification**:
    * The `Frontend` sends this `Google ID Token` to the `FastAPI Backend` via a `POST` request to the `/api/v1/auth/google` endpoint.
    * The `Backend` receives the token and communicates with `Google OAuth Service` to verify its authenticity and integrity (checking the signature, audience, and expiration).
4.  **User Management & JWT Issuance (if token is valid)**:
    * If Google confirms the token is valid, the `Backend` extracts user information (like Google ID, email, name).
    * It then queries the `MongoDB (Users Collection)` to see if this user exists. It will either retrieve the existing user document or create a new one (upsert logic).
    * With the user identified or created in the local database, the `Backend` generates a **JWT (JSON Web Token)**. This JWT is specific to your application and will be used to authenticate subsequent API requests.
    * The `Backend` returns this JWT (and potentially some user information) to the `Frontend`.
5.  **Frontend JWT Storage**: The `Frontend` securely stores the JWT (e.g., in memory, `localStorage`, or `sessionStorage`, depending on security requirements).
6.  **Authenticated Requests**: For all subsequent protected API calls, the `Frontend` includes this JWT in the `Authorization: Bearer <token>` header.
7.  **Invalid Token**: If the Google ID Token is invalid, the `Backend` returns an authentication error (e.g., HTTP 401 Unauthorized) to the `Frontend`.

---

### 3. Concept Map Generation Pipeline (CMVS LangGraph)
```mermaid
graph TD
    A[User uploads PDF with JWT] --> B{FastAPI Endpoint <br> /api/v1/maps/generate/};
    B --> C{Authenticate User};
    C -- Valid JWT --> D[For each PDF: Read bytes, Upload to S3, Extract Text];
   D -- All PDFs Processed --> I["Prepare Initial State for CMVS LangGraph: text, user_id, s3_path, etc."];

    I --> J{Invoke CMVS LangGraph};

    subgraph CMVS_LangGraph [CMVS LangGraph Pipeline]
        direction LR
        J_Start[Start] --> J1[chunk_text <br> Original Text -> Chunks];
        J1 --> J2[embed_hierarchical_chunks <br> Hierarchical Chunks -> Embedded Chunks];
        J2 --> J3[extract_main_concept_map <br> Original Text -> LLM -> Main Map Triples];
        J3 --> J4[process_main_map_graph <br> Normalize, Merge Nodes];
        J4 --> J5[generate_main_map_mermaid <br> Triples -> Mermaid Code];
        J5 --> J6[store_db <br> Save Main Map Details, Mermaid, <br> S3 Path & All Embedded Chunks to MongoDB];
        J6 --> J_End[End Pipeline];
    end
    
    J --> CMVS_LangGraph;
    CMVS_LangGraph --> K[Receive Final State <br> Mermaid, DB IDs, S3 Path];
    K --> L[Return JSON Response];
    C -- Invalid JWT --> L_AuthFail[Return Auth Error];

    style CMVS_LangGraph fill:#FFF2CC,stroke:#333
```


**Detailed Explanation:**

This **flowchart** details the pipeline for generating a concept map from uploaded PDF documents.

1.  **User Action & API Call**: An authenticated `User` uploads PDF files through the `Frontend`. The frontend makes a `POST` request to the `/api/v1/maps/generate/` endpoint, including the JWT for authentication.
2.  **Backend Pre-processing**:
    * The `FastAPI Endpoint` first authenticates the user using the JWT.
    * If valid, it iterates through each uploaded PDF:
        * Reads the file content into bytes.
        * Uploads the raw PDF file to **S3 storage** (via `S3 Service`) for persistence.
        * Extracts the plain text content from the PDF bytes (via `PDF Service`).
    * Once all PDFs are processed (text extracted, S3 paths noted), the backend prepares an initial state for the CMVS LangGraph. This state includes the combined extracted text (or text per document if processed individually), the `user_id`, S3 path(s), and original filenames.
3.  **CMVS LangGraph Invocation**: The backend then invokes the CMVS LangGraph pipeline (managed by `CMVS Service`).
4.  **CMVS LangGraph Internal Flow** (represented as a subgraph):
    * `chunk_text`: The input text (from PDFs) is divided into smaller, semantically coherent chunks.
    * `embed_hierarchical_chunks`: Each hierarchical chunk is converted into a vector embedding using a sentence transformer model. These embeddings and their corresponding text are prepared for storage.
    * `extract_main_concept_map`: This crucial step takes the **original full text** (or a significant portion) and uses an LLM (Groq) to extract triples (`source`, `target`, `relation`) that represent the **main ideas and high-level structure** of the document, rather than a granular breakdown. This aims to create a mind-map style overview.
    * `process_main_map_graph`: The raw triples from the LLM are processed. This involves normalizing concept labels (e.g., lowercasing, stemming) and merging duplicate or highly similar concept nodes to create a cleaner graph structure.
    * `generate_main_map_mermaid`: The processed graph (list of unique triples) is converted into Mermaid diagram syntax, suitable for rendering as a visual concept map on the frontend.
    * `store_db`: All relevant data is persisted to MongoDB:
        * The main concept map document (including the processed triples, Mermaid code, associated `user_id`, S3 path of the original PDF, and original filename).
        * All the **embedded chunks** (text and their vector embeddings) are stored in a separate collection, linked to the main concept map document and the user. This detailed chunked data is used later for the RAG Q&A feature.
5.  **Response to Frontend**:
    * Once the LangGraph pipeline completes, it returns its final state (containing the Mermaid code, MongoDB document IDs, S3 path, etc.) to the FastAPI endpoint.
    * The endpoint formats this into a JSON response and sends it back to the `Frontend`.
    * The `Frontend` can then render the concept map using the Mermaid code.
6.  **Authentication Failure**: If the initial JWT authentication fails, an authorization error is returned.

---

### 4. Node Detail Q&A Pipeline (RAG LangGraph)
```mermaid
graph TD
    RA[User asks question about a node <br> with JWT] --> RB{FastAPI Endpoint <br> /api/v1/maps/ask/}
    RB --> RC{Authenticate User <br> with JWT}
    RC -- Valid JWT --> RD[Prepare Initial State for RAG LangGraph <br> question, user_id, map_id, etc.]
    RD --> RE{Invoke RAG LangGraph}

    subgraph RAG_LangGraph [RAG Q&A LangGraph Pipeline]
        direction LR
        RE_Start[Start] --> R1[retrieve_mongodb_docs <br> Atlas Vector Search on Chunk Embeddings <br> filtered by user_id, map_id]
        R1 --> R2[grade_db_retrieval <br> LLM assesses DB doc sufficiency]
        R2 -- Sufficient & Confident --> R_GenDB[generate_final_answer <br> LLM uses DB docs only]
        R2 -- Insufficient or Low Confidence --> R3[perform_web_search <br> Tavily for verified sites]
        R3 --> R_GenWeb[generate_final_answer <br> LLM uses DB + Web docs]
        R_GenDB --> R_End[End Pipeline]
        R_GenWeb --> R_End[End Pipeline]
    end

    RE --> RAG_LangGraph
    RAG_LangGraph --> RF[Receive Final State <br> Generated Answer + Cited Sources]
    RF --> RG[Return JSON Response]
    RC -- Invalid JWT --> R_AuthFail[Return Auth Error]

    style RAG_LangGraph fill:#CCFFE5,stroke:#333
```


**Detailed Explanation:**

This **flowchart** describes the Retrieval Augmented Generation (RAG) pipeline used when a user asks a question about a specific node/concept within a concept map.

1.  **User Action & API Call**: An authenticated `User` interacts with a displayed concept map on the `Frontend` (e.g., clicks a node or types a question related to a concept). The frontend makes a `GET` request to the `/api/v1/maps/ask/` endpoint, sending the `map_id` (to identify the context), the `question` (which could be the node's label or a specific query), and the JWT.
2.  **Backend Pre-processing**:
    * The `FastAPI Endpoint` authenticates the user via JWT.
    * It prepares an initial state for the RAG LangGraph, including the `question`, `user_id`, and `map_id`.
3.  **RAG LangGraph Invocation**: The backend invokes the RAG LangGraph pipeline (managed by `CMVS Service` or a dedicated `RAGService`).
4.  **RAG LangGraph Internal Flow** (represented as a subgraph):
    * `retrieve_mongodb_docs`: This node queries the `chunk_embeddings` collection in MongoDB Atlas. It uses **Vector Search** to find text chunks that are semantically similar to the input `question`. The search is filtered to only include chunks associated with the current `user_id` and the specified `map_id`, ensuring context relevance and data privacy.
    * `grade_db_retrieval`: The retrieved documents from MongoDB are then assessed by an **LLM**. This LLM "grades" whether these documents alone are likely sufficient and relevant enough to provide a good answer to the user's `question`.
    * **Conditional Branching (Decision Point)**:
        * If the LLM grades the database documents as **Sufficient & Confident**: The graph proceeds directly to generate an answer using only these internal documents (`R_GenDB`).
        * If the LLM grades them as **Insufficient or with Low Confidence**: The graph routes to the `perform_web_search` node.
    * `perform_web_search` (Fallback): If triggered, this node uses an external search tool like **Tavily API** (or your integrated PaperScraper) to find relevant information from the web, focusing on configured "verified sites" (like Wikipedia or scientific journals).
    * `generate_final_answer`: This node is reached either directly after sufficient DB retrieval or after web search. It uses an **LLM (Groq)** to synthesize a final answer.
        * If only DB documents were used (`R_GenDB` path), the LLM uses that context.
        * If web search was performed (`R_GenWeb` path), the LLM uses a combination of the initial (possibly few) DB documents *and* the new web documents as context.
        The LLM is prompted to base its answer on the provided context and to help identify the sources it used.
5.  **Response to Frontend**:
    * The RAG LangGraph returns its final state, which includes the generated `answer` and a list of `cited_sources` (metadata about the DB chunks or web pages used).
    * The FastAPI endpoint formats this into a JSON response.
    * The `Frontend` displays the detailed answer and its sources to the user.
6.  **Authentication Failure**: If JWT authentication fails, an error is returned.

---


## Setup and Installation

### Prerequisites

* **Python**: Version 3.9+
* **MongoDB Atlas**:
    * A running MongoDB Atlas cluster.
    * Database and collections created (the application will create collections if they don't exist, but the DB should be accessible).
    * **Crucially, a Vector Search Index** must be configured on your `chunk_embeddings` collection (default name: `settings.MONGODB_CHUNKS_COLLECTION`). See "Setting up MongoDB Atlas Vector Search Index" below.
* **S3-compatible Storage**: An S3 bucket and corresponding credentials (Access Key ID, Secret Access Key, Endpoint URL).
* **Google OAuth 2.0 Credentials**:
    * A Client ID from Google Cloud Console for your application (this will be your `GOOGLE_CLIENT_ID`). Ensure it's configured for web applications and has the necessary redirect URIs if you're building a frontend. For backend token verification, the Client ID is used as the audience.
* **API Keys**:
    * **Groq API Key**: For accessing LLMs via Groq.
    * **Tavily API Key**: For the web search fallback in the RAG pipeline.

### Installation Steps

1.  **Clone the Repository** (Replace with your actual repository URL):
    ```bash
    git clone [https://github.com/edu-rag/cmvs.git](https://github.com/edu-rag/cmvs.git)
    cd project
    ```

2.  **Create and Activate a Virtual Environment**:
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # On Windows: .venv\Scripts\activate
    ```

3.  **Install Dependencies**:
    Create a `requirements.txt` file (if not already present) with all necessary packages (FastAPI, Uvicorn, Langchain, Pydantic, Boto3, PyMongo, PyMuPDF, python-jose, google-auth, etc. - see "Key Technologies" section or run `pip freeze > requirements.txt` in your working environment).
    ```bash
    pip install -r requirements.txt
    ```
    A minimal `requirements.txt` might include:
    ```
    fastapi
    uvicorn[standard]
    pydantic
    pydantic-settings
    python-dotenv
    langchain
    langchain-core
    langchain-community
    langchain-groq
    langchain-huggingface # For HuggingFaceEmbeddings
    langchain-mongodb
    langchain_experimental # For SemanticChunker
    langgraph
    sentence-transformers
    scikit-learn
    numpy
    pymupdf # fitz
    boto3
    pymongo
    python-jose[cryptography]
    google-auth
    # Add any other specific versions if needed
    ```


4.  **Set Up Environment Variables**:
    Create a `.env` file in the root of your project directory (`cmvs_api_project/`) and populate it with your credentials and configurations. Use the `.env.example` file (if provided) as a template.

    ```env
    # LLM & Embeddings
    GROQ_API_KEY="your_groq_api_key"
    MODEL_NAME_FOR_EMBEDDING="paraphrase-multilingual-mpnet-base-v2" # Or your preferred model
    LLM_MODEL_NAME_GROQ="llama3-8b-8192" # Or your preferred Groq model

    # MongoDB Atlas
    MONGODB_URI="mongodb+srv://user:password@your_atlas_cluster_url/?retryWrites=true&w=majority"
    MONGODB_DATABASE_NAME="cmvs_prod_db"
    MONGODB_USERS_COLLECTION="users"
    MONGODB_CMVS_COLLECTION="concept_maps"
    MONGODB_CHUNKS_COLLECTION="chunk_embeddings"
    MONGODB_ATLAS_VECTOR_SEARCH_INDEX_NAME="vector_index_on_embedding" # Your Atlas Vector Search Index Name

    # S3 Compatible Storage
    S3_ACCESS_KEY_ID="your_s3_access_key_id"
    S3_SECRET_ACCESS_KEY="your_s3_secret_access_key"
    S3_ENDPOINT_URL="[https://your-s3-endpoint-url.com](https://your-s3-endpoint-url.com)" # e.g., for MinIO or other S3 compatibles. For AWS S3, this might be different or use region.
    S3_BUCKET_NAME="your_s3_bucket_name"

    # JWT Authentication
    JWT_SECRET_KEY="USE_A_VERY_STRONG_RANDOM_SECRET_KEY_HERE" # Generate a strong secret key
    ALGORITHM="HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES="1440" # e.g., 24 hours

    # Google OAuth
    GOOGLE_CLIENT_ID="your_google_oauth_client_id.apps.googleusercontent.com" # Audience for ID token verification

    # Tavily API (for RAG Web Search)
    TAVILY_API_KEY="your_tavily_api_key"

    # RAG Web Search Domain Filtering (Comma-separated list for .env, or define in config.py)
    # Example for .env if your Pydantic settings can parse it, otherwise define in config.py's list directly.
    # RAG_VERIFIED_DOMAINS="wikipedia.org,arxiv.org,nature.com,science.org" 
    # If defining directly in config.py's list, this env var isn't strictly needed for the list itself.

    # Logging
    LOG_LEVEL="INFO"
    ```

### Setting up MongoDB Atlas Vector Search Index

1.  Navigate to your MongoDB Atlas cluster.
2.  Go to the "Search" tab.
3.  Click "Create Search Index" (if none exists for vector search) or "Create Index".
4.  Choose "Atlas Vector Search" and select "JSON Editor".
5.  Configure your index. Here's a template (ensure `path` and `numDimensions` match your data and embedding model):
    ```json
    {
      "name": "vector_index_on_embedding", // Must match MONGODB_ATLAS_VECTOR_SEARCH_INDEX_NAME
      "type": "vectorSearch",
      "fields": [
        {
          "type": "vector",
          "path": "embedding",      // The field in your 'chunk_embeddings' collection that stores the vectors
          "numDimensions": 768,   // CRITICAL: Match the dimensions of your embedding model
                                  // (e.g., paraphrase-multilingual-mpnet-base-v2 is 768)
          "similarity": "cosine"  // Or "euclidean", "dotProduct"
        },
        {
          "type": "filter",
          "path": "user_id"       // To allow filtering by user_id in RAG queries
        },
        {
          "type": "filter",
          "path": "map_id" // To allow filtering by map_id
        }
        // Add other fields you might want to filter on (e.g., "original_filename_source_pdf") as type "filter"
      ]
    }
    ```
6.  Save the index and wait for it to build.

## Running the Application

Once the setup is complete, you can run the FastAPI application using Uvicorn:

```bash
# From the root directory (cmvs_api_project/)
# Ensure your virtual environment is activated
source .venv/bin/activate 

# Run using the uvicorn_runner.py (if you created it)
python uvicorn_runner.py

# Or directly with Uvicorn:
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

* `app.main:app` points to the FastAPI instance `app` in the `app/main.py` file.
* `--reload` enables auto-reloading during development. Remove this for production.
* The API will typically be available at `http://127.0.0.1:8000`.
* Interactive API documentation (Swagger UI) will be at `http://127.0.0.1:8000/docs`.
* Alternative API documentation (ReDoc) will be at `http://127.0.0.1:8000/redoc`.

## API Endpoints Summary

All endpoints are prefixed with `/api/v1`. Authentication (JWT Bearer token) is required for most endpoints after login.

### Authentication

* **`POST /auth/google`**
    * **Description**: Authenticates a user via a Google ID Token obtained from a frontend Google Sign-In flow.
    * **Request Body**: `{ "google_id_token": "YOUR_GOOGLE_ID_TOKEN" }`
    * **Response**: JWT access token and user information.
* **`GET /users/me`**
    * **Description**: Retrieves the profile of the currently authenticated user.
    * **Auth**: JWT Bearer Token required.
    * **Response**: User profile information.

### Concept Map Generation

* **`POST /maps/generate/`**
    * **Description**: Uploads one or more PDF files, processes them, generates a concept map, stores the PDF in S3, and saves map data and chunk embeddings in MongoDB.
    * **Auth**: JWT Bearer Token required.
    * **Request**: `multipart/form-data` with `files` field containing PDF(s).
    * **Response**: A list of results, each including filename, status, S3 path, Mermaid code, MongoDB document IDs for the map and chunks.

### Question Answering (RAG)

* **`GET /maps/ask/`**
    * **Description**: Answers a specific question about a concept/node within a given concept map using the RAG pipeline (MongoDB Atlas Vector Search + LLM, with Tavily fallback).
    * **Auth**: JWT Bearer Token required.
    * **Query Parameters**:
        * `map_id: str` (ID of the main concept map document)
        * `question: str` (The user's specific question)
        * `context_node_label: Optional[str]` (Optional: Label of the node the question is about)
        * `top_k: Optional[int]` (Default 3, number of chunks for RAG context)
    * **Response**: The LLM-generated answer, along with cited sources (from DB chunks or web search).

## Key Technologies Used

* **Backend Framework**: FastAPI
* **Orchestration**: Langchain, LangGraph
* **LLMs**: Groq API (for models like Llama 3)
* **Embeddings**: HuggingFace Sentence Transformers (e.g., `paraphrase-multilingual-mpnet-base-v2`)
* **Database**: MongoDB Atlas (with Vector Search)
* **Object Storage**: S3-compatible storage (e.g., AWS S3, MinIO)
* **Authentication**: Google OAuth 2.0, JWT (python-jose)
* **Web Search (RAG Fallback)**: Tavily API
* **PDF Processing**: PyMuPDF (fitz)
* **Data Validation**: Pydantic
* **Async**: `asyncio`

## Future Enhancements (To-Do)

* More sophisticated citation parsing and in-text citation generation.
* Frontend UI for PDF upload, map visualization (MermaidJS), and interactive Q&A.
* Support for other document types (e.g., DOCX, TXT).
* User ability to edit/refine concept maps.
* Advanced RAG strategies (e.g., re-ranking, query transformation).
* More robust error handling and user feedback.
* Persistent LangGraph checkpointers for resumable RAG/CMVS tasks.
* Unit and integration tests.
* CI/CD pipeline.

## Contributing

This project is currently a conceptual implementation. If it were open source, contribution guidelines would be provided here.

## License

TODO: Define a license for the project (e.g., MIT, Apache 2.0, etc.).