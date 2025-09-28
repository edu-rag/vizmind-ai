# VizMind AI - Intelligent Document Mind Mapping

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-15+-black.svg)](https://nextjs.org)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.5+-orange.svg)](https://langchain-ai.github.io/langgraph/)
[![MongoDB](https://img.shields.io/badge/MongoDB-Atlas-green.svg)](https://mongodb.com)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0+-blue.svg)](https://typescriptlang.org)

VizMind AI is a full-stack intelligent document processing platform that automatically transforms PDF documents into interactive hierarchical mind maps and enables intelligent question-answering through a sophisticated Retrieval Augmented Generation (RAG) pipeline. Built with modern LangGraph workflows, secure authentication, React Flow visualization, and cloud-ready architecture.

## 🚀 Features

### Backend (FastAPI + LangGraph)
* **🧠 AI-Powered Mind Mapping**: Transform PDFs into structured hierarchical mind maps using advanced LLM processing
* **📚 Intelligent RAG Q&A**: Ask questions about your documents with context-aware AI responses and source citations
* **💬 Smart Chat History**: Persistent, context-aware conversations with automatic caching and intelligent question deduplication
* **🔄 LangGraph Workflows**: Robust, scalable processing pipelines with automatic error handling and retry mechanisms
* **☁️ Cloud-Ready**: S3 integration for document storage and MongoDB Atlas for vector search
* **🔐 Secure Authentication**: Google Sign-In with JWT tokens for secure API access
* **⚡ High Performance**: Groq LLM integration for fast inference and Docling for superior document processing
* **📊 Processing Analytics**: Detailed metrics and status tracking for all workflows
* **🎯 Smart Chunking**: Heading-aware document chunking for better context preservation
* **🚀 Cache-First Architecture**: Instant responses for repeated questions with automatic conversation management

### Frontend (Next.js + React)
* **🎨 Interactive Mind Maps**: Beautiful, zoomable mind map visualization using React Flow
* **📱 Responsive Design**: Mobile-first design with touch-optimized interactions
* **🌙 Dark/Light Theme**: System-aware theme switching with user preferences
* **🔒 Google OAuth Integration**: Seamless authentication flow with secure token management
* **💬 Real-time Chat Interface**: Context-aware Q&A with conversation history
* **📁 File Upload**: Drag-and-drop PDF upload with progress indicators
* **🔍 Node Detail Panels**: Interactive side panels with detailed information for each concept
* **📱 Mobile Optimization**: Touch-friendly interface with responsive layouts
* **⚡ Performance Optimized**: Next.js 15 with optimized bundle splitting and caching
* **🎯 TypeScript**: Full type safety across the application

## 🏗️ Architecture Overview

VizMind AI is built as a full-stack application with a clear separation between frontend and backend:

### System Architecture

```mermaid
graph TB
    subgraph "Frontend - Next.js 15"
        UI[React Components]
        Auth[Google OAuth]
        Store[Zustand Store]
        API[API Client]
    end
    
    subgraph "Backend - FastAPI"
        FastAPI[FastAPI Server]
        JWT[JWT Auth]
        Routes[API Routes]
        Services[Service Layer]
    end
    
    subgraph "AI Processing - LangGraph"
        DocPipeline[Document Processing Workflow]
        RAGPipeline[RAG Query Workflow]
        ChatPipeline[Chat History Workflow]
    end
    
    subgraph "External Services"
        Groq[Groq LLM API]
        HF[HuggingFace Embeddings]
        GoogleOAuth[Google OAuth API]
    end
    
    subgraph "Data Layer"
        MongoDB[(MongoDB Atlas)]
        S3[(S3 Storage)]
        Vector[Vector Search Index]
    end
    
    UI --> Store
    Store --> API
    API --> FastAPI
    FastAPI --> JWT
    JWT --> Routes
    Routes --> Services
    Services --> DocPipeline
    Services --> RAGPipeline
    Services --> ChatPipeline
    
    DocPipeline --> Groq
    DocPipeline --> HF
    RAGPipeline --> Groq
    RAGPipeline --> HF
    
    Services --> MongoDB
    Services --> S3
    MongoDB --> Vector
    
    Auth --> GoogleOAuth
    
    style UI fill:#e1f5fe
    style FastAPI fill:#f3e5f5
    style DocPipeline fill:#fff3e0
    style MongoDB fill:#e8f5e8
```

### Core Components

#### Frontend (Next.js 15 + TypeScript)
* **🎯 React Components**: Modern functional components with hooks
* **🔄 State Management**: Zustand for global state with persistence
* **🎨 UI Framework**: Shadcn/ui components with Tailwind CSS
* **📊 Visualization**: React Flow for interactive mind map rendering
* **🔐 Authentication**: Google OAuth integration with JWT token management
* **📱 Responsive Design**: Mobile-first approach with touch optimization

#### Backend (FastAPI + Python 3.12)
* **🚀 API Layer**: RESTful FastAPI endpoints with comprehensive documentation
* **🧠 LangGraph Workflows**: Orchestrated AI processing pipelines
* **📊 Service Layer**: Business logic for document processing, user management, and AI operations
* **💾 Data Stores**: MongoDB Atlas with vector search and S3-compatible storage
* **🔧 External Services**: Google OAuth, Groq API, HuggingFace embeddings

## 🔄 End-to-End Feature Flows

### 1. Complete Document Upload & Mind Map Generation Flow

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant FastAPI
    participant LangGraph
    participant Docling
    participant Groq
    participant S3
    participant MongoDB
    
    User->>Frontend: Upload PDF file
    Frontend->>Frontend: Validate file (PDF, size)
    Frontend->>FastAPI: POST /api/v1/maps/generate-mindmap
    
    FastAPI->>FastAPI: Validate JWT token
    FastAPI->>S3: Upload PDF to S3 storage
    S3-->>FastAPI: Return S3 path
    
    FastAPI->>LangGraph: Execute document processing workflow
    
    LangGraph->>Docling: Extract text and structure
    Docling-->>LangGraph: Return extracted content
    
    LangGraph->>Groq: Clean and process content
    Groq-->>LangGraph: Return cleaned text
    
    LangGraph->>Groq: Generate hierarchical mind map
    Groq-->>LangGraph: Return mind map structure
    
    LangGraph->>LangGraph: Chunk content by headings
    LangGraph->>HuggingFace: Generate embeddings
    HuggingFace-->>LangGraph: Return vector embeddings
    
    LangGraph->>MongoDB: Store chunks + embeddings
    LangGraph->>MongoDB: Store mind map document
    MongoDB-->>LangGraph: Confirm storage
    
    LangGraph-->>FastAPI: Return processing result
    FastAPI-->>Frontend: Return mind map response
    
    Frontend->>Frontend: Parse hierarchical data
    Frontend->>Frontend: Render interactive mind map
    Frontend-->>User: Display complete mind map
```

### 2. Interactive Node Selection & Detail Retrieval Flow

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant ReactFlow
    participant FastAPI
    participant ChatService
    participant RAGWorkflow
    participant MongoDB
    participant Groq
    
    User->>ReactFlow: Click on mind map node
    ReactFlow->>Frontend: Trigger node selection event
    Frontend->>Frontend: Store selected node in Zustand
    Frontend->>Frontend: Open NodeDetailPanel
    
    Frontend->>FastAPI: POST /api/v1/chat (initial question)
    note over Frontend,FastAPI: Question: "What is [node_label]? Provide detailed information."
    
    FastAPI->>ChatService: Check conversation history
    ChatService->>MongoDB: Query chat collection
    MongoDB-->>ChatService: Return existing messages
    
    alt Question exists in history
        ChatService-->>FastAPI: Return cached answer
        FastAPI-->>Frontend: Return cached response
    else New question
        FastAPI->>RAGWorkflow: Execute RAG pipeline
        RAGWorkflow->>MongoDB: Vector similarity search
        MongoDB-->>RAGWorkflow: Return relevant chunks
        
        RAGWorkflow->>Groq: Generate answer with context
        Groq-->>RAGWorkflow: Return AI response
        
        RAGWorkflow-->>FastAPI: Return answer + sources
        
        FastAPI->>ChatService: Save Q&A to history
        ChatService->>MongoDB: Store question + answer
        
        FastAPI-->>Frontend: Return response
    end
    
    Frontend->>Frontend: Render answer in detail panel
    Frontend-->>User: Display node details + sources
```

### 3. Intelligent Chat Conversation Flow

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant FastAPI
    participant ChatService
    participant RAGWorkflow
    participant MongoDB
    participant Groq
    
    User->>Frontend: Type follow-up question
    Frontend->>FastAPI: POST /api/v1/chat
    
    FastAPI->>ChatService: Check for exact question match
    ChatService->>MongoDB: Query conversation history
    
    alt Exact question found
        MongoDB-->>ChatService: Return cached answer
        ChatService-->>FastAPI: Return cached response
        FastAPI-->>Frontend: Return instant response
    else New question
        ChatService->>MongoDB: Get recent messages (last 5)
        MongoDB-->>ChatService: Return conversation context
        
        FastAPI->>RAGWorkflow: Execute with context
        note over FastAPI,RAGWorkflow: Enhanced query = context + new question
        
        RAGWorkflow->>MongoDB: Vector search with user/map filters
        MongoDB-->>RAGWorkflow: Return relevant document chunks
        
        RAGWorkflow->>Groq: Generate contextual answer
        note over RAGWorkflow,Groq: Include conversation history for context
        Groq-->>RAGWorkflow: Return contextual response
        
        RAGWorkflow-->>FastAPI: Return answer + citations
        
        FastAPI->>ChatService: Save Q&A pair to conversation
        ChatService->>MongoDB: Update conversation document
        
        FastAPI-->>Frontend: Return new response
    end
    
    Frontend->>Frontend: Update conversation UI
    Frontend->>Frontend: Auto-scroll to new message
    Frontend-->>User: Display contextual answer
```

### 4. User Authentication & Session Management Flow

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant GoogleOAuth
    participant FastAPI
    participant MongoDB
    
    User->>Frontend: Click "Sign In with Google"
    Frontend->>GoogleOAuth: Redirect to Google OAuth
    
    GoogleOAuth->>User: Show consent screen
    User->>GoogleOAuth: Approve permissions
    
    GoogleOAuth->>Frontend: Return authorization code
    Frontend->>FastAPI: POST /api/v1/auth/google-auth
    
    FastAPI->>GoogleOAuth: Exchange code for tokens
    GoogleOAuth-->>FastAPI: Return user profile + tokens
    
    FastAPI->>MongoDB: Check/create user document
    MongoDB-->>FastAPI: Return user data
    
    FastAPI->>FastAPI: Generate JWT token
    FastAPI-->>Frontend: Return JWT + user info
    
    Frontend->>Frontend: Store JWT in secure storage
    Frontend->>Frontend: Update global auth state
    
    Frontend-->>User: Redirect to dashboard
    
    Note over Frontend,FastAPI: All subsequent requests include JWT in Authorization header
    
    Frontend->>FastAPI: API requests with JWT
    FastAPI->>FastAPI: Validate JWT + extract user
    FastAPI-->>Frontend: Return authorized responses
```

### 5. Real-time Mind Map Interaction & State Management

```mermaid
sequenceDiagram
    participant User
    participant ReactFlow
    participant Zustand
    participant NodeDetailPanel
    participant ChatInterface
    participant FastAPI
    
    User->>ReactFlow: Pan/Zoom mind map
    ReactFlow->>ReactFlow: Update viewport state
    
    User->>ReactFlow: Click different node
    ReactFlow->>Zustand: Update selectedNodeData
    Zustand->>NodeDetailPanel: Trigger re-render
    
    NodeDetailPanel->>NodeDetailPanel: Check if node changed
    alt Same node
        NodeDetailPanel->>NodeDetailPanel: Keep existing data
    else Different node
        NodeDetailPanel->>NodeDetailPanel: Clear previous data
        NodeDetailPanel->>FastAPI: Fetch new node details
        FastAPI-->>NodeDetailPanel: Return node information
    end
    
    User->>ChatInterface: Ask question about node
    ChatInterface->>FastAPI: Send question with node context
    FastAPI-->>ChatInterface: Return contextual answer
    
    ChatInterface->>Zustand: Update conversation state
    Zustand->>NodeDetailPanel: Update UI with new message
    
    User->>NodeDetailPanel: Close panel
    NodeDetailPanel->>Zustand: Set isDetailPanelOpen = false
    Note over NodeDetailPanel,Zustand: Data persists for quick reopening
    
    User->>ReactFlow: Click same node again
    ReactFlow->>Zustand: Set selectedNodeData (same node)
    Zustand->>NodeDetailPanel: Open with preserved data
    NodeDetailPanel-->>User: Instant display (no API call)
```

### 6. Mobile-Responsive Touch Interaction Flow

```mermaid
sequenceDiagram
    participant User
    participant MobileDetection
    participant TouchHandler
    participant ReactFlow
    participant MobileUI
    participant NodeDetailPanel
    
    User->>MobileDetection: Load app on mobile device
    MobileDetection->>MobileUI: Apply mobile-specific styles
    MobileDetection->>TouchHandler: Initialize touch gestures
    
    User->>TouchHandler: Pinch to zoom
    TouchHandler->>ReactFlow: Update zoom level
    ReactFlow->>ReactFlow: Smooth zoom animation
    
    User->>TouchHandler: Pan with finger
    TouchHandler->>ReactFlow: Update viewport position
    ReactFlow->>ReactFlow: Follow finger movement
    
    User->>TouchHandler: Tap node (touch-optimized)
    TouchHandler->>ReactFlow: Trigger node selection
    ReactFlow->>NodeDetailPanel: Open as bottom sheet (mobile)
    
    NodeDetailPanel->>NodeDetailPanel: Apply mobile layout
    NodeDetailPanel->>NodeDetailPanel: Increase touch targets
    NodeDetailPanel->>NodeDetailPanel: Enable swipe-to-close
    
    User->>NodeDetailPanel: Swipe down to close
    NodeDetailPanel->>NodeDetailPanel: Animate close
    NodeDetailPanel-->>User: Return to mind map view
```

### LangGraph Workflows

#### 1. **Document Processing Workflow**

```mermaid
graph LR
    A[📄 Upload] --> B[🔍 Docling Extract]
    B --> C[🧹 LLM Clean]
    C --> D[🧠 Mind Map Generate]
    D --> E[✂️ Chunk Content]
    E --> F[🔢 Embed & Store]
    F --> G[✅ Complete]
    
    style A fill:#e3f2fd
    style G fill:#e8f5e8
```

#### 2. **RAG Query Workflow**

```mermaid
graph LR
    A[❓ Query Input] --> B[🔍 Vector Search]
    B --> C[📄 Retrieve Top-K Documents]
    C --> D{📊 Documents Found?}
    
    D -->|Yes| E[🧠 Initialize LLM Grader]
    D -->|No| K[🤖 Generate with Empty Context]
   
    E --> J{🔍 Relevant Docs Found?}
    J -->|Yes| K[🤖 Generate Answer with Context]
    J -->|No| K
    
    K --> M[📚 Create Citation Sources]
    M --> O[✅ Complete]
    
    style A fill:#e3f2fd
    style O fill:#e8f5e8
```

#### 3. **Chat History Management Workflow**

```mermaid
graph TD
    A[💬 Question] --> B{🔍 Check Cache}
    B -->|Found| C[⚡ Return Cached]
    B -->|Not Found| D[🔄 Run RAG]
    D --> E[💾 Save Q&A]
    E --> F[📤 Return Response]
    C --> G[✅ Complete]
    F --> G
    
    style A fill:#e3f2fd
    style G fill:#e8f5e8
    style C fill:#fff3e0
```

## 🔄 Application Flow

### Chat History & Conversation Management

VizMind AI features an advanced chat history system that provides intelligent, context-aware conversations for each mind map node:

#### **Key Features:**
* **Cache-First Architecture**: Questions are checked against conversation history before running RAG workflows, providing instant responses for repeated queries
* **Node-Specific Conversations**: Each concept node maintains its own conversation thread with full context preservation
* **Automatic Q&A Persistence**: All questions and answers are automatically saved to MongoDB with proper indexing
* **Context-Aware Responses**: Recent conversation history (limited to 5 messages for token optimization) is provided as context for better AI responses
* **Soft Delete**: Conversations can be cleared by users without permanent data loss
* **Intelligent Deduplication**: Exact question matching prevents unnecessary LLM calls and reduces costs

#### **Chat Flow:**
```
User selects node → Initial question generated → Backend checks cache → 
If cached: Return instantly | If new: Run RAG + Save to history → Display response
```

#### **Follow-up Questions:**
```
User asks question → Backend checks exact match in history → 
If found: Return cached answer | If new: Add context from recent messages → Run RAG → Save Q&A pair
```

### Document Processing Pipeline
```mermaid
graph TD
    A[PDF Upload] --> B[S3 Storage]
    B --> C[Docling Extraction]
    C --> D[LLM Content Cleaning]
    D --> E[Hierarchical Mind Map Generation]
    E --> F[Heading-Based Chunking]
    F --> G[Vector Embedding]
    G --> H[MongoDB Storage]
    H --> I[Complete]
    
    style A fill:#e1f5fe
    style I fill:#c8e6c9
```

### RAG Query Pipeline
```mermaid
graph TD
    A[User Query] --> B[Vector Search]
    B --> C[Document Retrieval]
    C --> D[Relevance Grading]
    D --> E[Context Filtering]
    E --> F[Answer Generation]
    F --> G[Source Citation]
    G --> H[Response]
    
    style A fill:#e1f5fe
    style H fill:#c8e6c9
```

## �️ Technology Stack

### Frontend Stack
* **Framework**: Next.js 15 with App Router
* **Language**: TypeScript 5.0+
* **UI Framework**: React 18 with functional components & hooks
* **Styling**: Tailwind CSS 3.4+ with custom design system
* **Components**: Shadcn/ui component library
* **State Management**: Zustand with persistence
* **Visualization**: React Flow for mind map rendering
* **Authentication**: Google OAuth 2.0 integration
* **HTTP Client**: Axios with interceptors
* **Icons**: Lucide React icons
* **Notifications**: Sonner toast library
* **Build Tool**: Next.js built-in Turbopack
* **Development**: Hot reload with Fast Refresh

### Backend Stack
* **Framework**: FastAPI 0.115+ with async/await
* **Language**: Python 3.12+
* **AI Orchestration**: LangGraph 0.5+ workflows
* **LLM Provider**: Groq API (Llama 3.3 70B)
* **Embeddings**: HuggingFace Transformers
* **Document Processing**: Docling for PDF extraction
* **Database**: MongoDB Atlas with vector search
* **Storage**: S3-compatible object storage
* **Authentication**: JWT tokens with Google OAuth
* **Validation**: Pydantic v2 models
* **Async**: asyncio with uvloop
* **Monitoring**: Structured logging with correlation IDs

### Infrastructure & DevOps
* **Frontend Hosting**: Netlify with edge functions
* **Backend Hosting**: Docker containers (cloud-ready)
* **Database**: MongoDB Atlas (cloud)
* **Storage**: AWS S3 or compatible
* **CDN**: Netlify Edge Network
* **SSL**: Automatic HTTPS certificates
* **Monitoring**: Application logs and metrics

## 🚀 Complete Setup & Deployment Guide

### Prerequisites

* **Node.js**: 18.0+ (for frontend)
* **Python**: 3.12+ (for backend)
* **MongoDB Atlas**: Vector search enabled
* **S3-Compatible Storage**: AWS S3, MinIO, etc.
* **Groq API**: For LLM inference
* **Google OAuth**: For authentication

### 1. Frontend Setup (Next.js)

```bash
# Clone and navigate to frontend
git clone <repository-url>
cd cmvs/frontend

# Install dependencies
npm install
# or
pnpm install

# Create environment file
cp .env.example .env.local
```

**Frontend Environment Variables (.env.local):**

```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
NEXT_PUBLIC_GOOGLE_CLIENT_ID=your_google_client_id
NEXT_PUBLIC_APP_NAME=VizMind AI
NEXT_PUBLIC_APP_DESCRIPTION=Transform documents into intelligent mind maps
```

```bash
# Development server
npm run dev
# or
pnpm dev

# Production build
npm run build
npm start
```

### 2. Backend Setup (FastAPI)

```bash
# Navigate to backend
cd cmvs/backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create environment file
cp .env.example .env
```

**Backend Environment Variables (.env):**

```env
# LLM & AI Services
GROQ_API_KEY=your_groq_api_key
MODEL_NAME_FOR_EMBEDDING=sentence-transformers/paraphrase-multilingual-mpnet-base-v2
LLM_MODEL_NAME_GROQ=llama-3.3-70b-versatile

# MongoDB Atlas Configuration
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/
MONGODB_DATABASE_NAME=vizmind_ai
MONGODB_MAPS_COLLECTION=concept_maps
MONGODB_CHUNKS_COLLECTION=chunk_embeddings
MONGODB_CHAT_COLLECTION=chat_conversations
MONGODB_ATLAS_VECTOR_SEARCH_INDEX_NAME=vector_index_on_embedding

# S3 Storage Configuration
S3_ACCESS_KEY_ID=your_s3_access_key
S3_SECRET_ACCESS_KEY=your_s3_secret_key
S3_ENDPOINT_URL=https://s3.amazonaws.com
S3_BUCKET_NAME=your_bucket_name
S3_PUBLIC_DOMAIN=https://your-bucket.s3.amazonaws.com

# Security & Authentication
JWT_SECRET_KEY=your_super_secret_jwt_key_min_32_chars
GOOGLE_CLIENT_ID=your_google_oauth_client_id

# Optional: Performance Tuning
WORKFLOW_MAX_RETRIES=3
WORKFLOW_TIMEOUT_SECONDS=300
DEFAULT_TOP_K=10
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
```

```bash
# Development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production server
python uvicorn_runner.py
```

### 3. MongoDB Atlas Vector Search Setup

Create a vector search index in your MongoDB Atlas cluster:

**Index Name:** `vector_index_on_embedding`

**Index Definition:**

```json
{
  "fields": [
    {
      "numDimensions": 768,
      "path": "embedding",
      "similarity": "cosine",
      "type": "vector"
    },
    {
      "path": "user_id",
      "type": "filter"
    },
    {
      "path": "map_id", 
      "type": "filter"
    },
    {
      "path": "document_id",
      "type": "filter"
    }
  ]
}
```

**Required Collections:**
* `concept_maps` - Stores mind map documents and hierarchical data
* `chunk_embeddings` - Stores document chunks with vector embeddings
* `chat_conversations` - Stores conversation history for chat functionality

### 4. Google OAuth Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable Google+ API
4. Create OAuth 2.0 credentials
5. Add authorized redirect URIs:
   * `http://localhost:3000` (development)
   * `https://your-domain.com` (production)

### 5. Production Deployment

#### Frontend Deployment (Netlify)

```bash
# Build for production
npm run build

# Deploy to Netlify
netlify deploy --prod --dir=.next
```

**netlify.toml:**

```toml
[build]
  command = "npm run build"
  publish = ".next"

[[redirects]]
  from = "/*"
  to = "/index.html"
  status = 200

[build.environment]
  NEXT_PUBLIC_API_BASE_URL = "https://your-api-domain.com"
```

#### Backend Deployment (Docker)

```dockerfile
# Dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["python", "uvicorn_runner.py"]
```

```bash
# Build and run Docker container
docker build -t vizmind-ai-backend .
docker run -p 8000:8000 --env-file .env vizmind-ai-backend
```

### 6. Development Workflow

#### Frontend Development

```bash
# Install dependencies
pnpm install

# Start development server with hot reload
pnpm dev

# Type checking
pnpm type-check

# Linting
pnpm lint

# Build for production
pnpm build
```

#### Backend Development

```bash
# Install dependencies
pip install -r requirements.txt

# Start with auto-reload
uvicorn app.main:app --reload

# Run tests
pytest

# Format code
black app/
isort app/

# Type checking
mypy app/
```

### 7. Monitoring & Debugging

#### Application Logs

Both frontend and backend provide structured logging:

**Backend Logs:**
```bash
# View logs with correlation tracking
tail -f logs/app.log | grep "correlation_id"
```

**Frontend Logs:**
```javascript
// Browser console shows detailed API interactions
console.log('API Request:', { endpoint, payload, headers });
```

#### Health Checks

```bash
# Backend health
curl http://localhost:8000/health

# Frontend build health
curl http://localhost:3000/api/health
```

### 8. Security Considerations

* **JWT Secret**: Use a strong, random secret key (minimum 32 characters)
* **CORS**: Configure appropriate origins for production
* **Rate Limiting**: Implement rate limiting for public APIs
* **Input Validation**: All inputs are validated using Pydantic models
* **File Uploads**: PDF validation and size limits enforced
* **Environment Variables**: Never commit secrets to version control

### 3.1. Chat History Database Schema

The chat system uses a dedicated MongoDB collection with the following structure:

```json
{
  "_id": "ObjectId",
  "user_id": "string",
  "map_id": "string", 
  "node_id": "string",
  "node_label": "string",
  "messages": [
    {
      "id": "string",
      "type": "question|answer",
      "content": "string",
      "cited_sources": [...],
      "timestamp": "ISODate",
      "node_id": "string",
      "user_id": "string",
      "map_id": "string"
    }
  ],
  "created_at": "ISODate",
  "updated_at": "ISODate",
  "is_deleted": false
}
```

**Database Indexes:**
* Compound index: `{user_id: 1, map_id: 1, node_id: 1, is_deleted: 1}`
* TTL index: Optional for automatic cleanup of old conversations

### 4. Run the Application

```bash
# Development
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production
python uvicorn_runner.py
```

## 📖 API Documentation

### Authentication Flow

All API endpoints (except authentication) require a JWT Bearer token in the Authorization header.

#### Google OAuth Authentication

```http
POST /api/v1/auth/google-auth
Content-Type: application/json

{
  "code": "google_oauth_authorization_code",
  "redirect_uri": "https://your-frontend-domain.com"
}
```

**Response:**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": "user_id_string",
    "email": "user@example.com",
    "name": "User Name",
    "picture": "https://lh3.googleusercontent.com/..."
  }
}
```

### Core API Endpoints

#### 1. Mind Map Generation

Transform PDF documents into interactive mind maps with AI processing.

```http
POST /api/v1/maps/generate-mindmap
Content-Type: multipart/form-data
Authorization: Bearer <jwt_token>

file: <PDF file (max 50MB)>
```

**Response:**

```json
{
  "attachment": {
    "filename": "document.pdf",
    "s3_path": "s3://bucket/user_123/uploads/uuid-document.pdf",
    "status": "success"
  },
  "status": "success",
  "hierarchical_data": {
    "id": "root",
    "data": { "label": "Document Title" },
    "children": [
      {
        "id": "node-1", 
        "data": { "label": "Chapter 1: Introduction" },
        "children": [
          {
            "id": "node-1-1",
            "data": { "label": "1.1 Overview" },
            "children": []
          }
        ]
      }
    ]
  },
  "mongodb_doc_id": "507f1f77bcf86cd799439011",
  "processing_metadata": {
    "processing_time": 45.2,
    "chunk_count": 150,
    "embedding_dimension": 768,
    "stage": "completed"
  }
}
```

#### 2. Intelligent Q&A with Context-Aware Chat

Ask questions about your documents with automatic conversation history management.

```http
POST /api/v1/chat
Content-Type: application/json
Authorization: Bearer <jwt_token>

{
  "question": "What are the key principles of machine learning discussed in chapter 2?",
  "map_id": "507f1f77bcf86cd799439011",
  "node_id": "node-2",
  "node_label": "Machine Learning Fundamentals",
  "top_k": 10
}
```

**Response Features:**
* **Cache-First**: Instant responses for repeated questions
* **Context-Aware**: Uses conversation history for better answers
* **Source Citations**: References to original document chunks
* **Auto-Save**: Q&A pairs automatically stored for future reference

```json
{
  "query": "What are the key principles of machine learning?",
  "answer": "Based on the document, the key principles of machine learning include:\n\n1. **Supervised Learning**: Learning from labeled examples...",
  "cited_sources": [
    {
      "type": "document_chunk",
      "identifier": "chunk_id_123",
      "title": "Machine Learning Fundamentals - Chapter 2",
      "page_number": 15,
      "snippet": "The fundamental principles of machine learning..."
    }
  ],
  "confidence_score": 0.95,
  "processing_time": 2.3,
  "message": "Answer generated successfully"
}
```

#### 3. Conversation History Management

```http
DELETE /api/v1/chat/delete/{map_id}/{node_id}
Authorization: Bearer <jwt_token>
```

**Response:**

```json
{
  "success": true,
  "message": "Conversation history cleared successfully",
  "conversation_id": "conversation_uuid"
}
```

#### 4. Mind Map Retrieval

```http
GET /api/v1/maps/{map_id}
Authorization: Bearer <jwt_token>
```

```http
GET /api/v1/maps/history
Authorization: Bearer <jwt_token>
```

### Frontend API Integration

The frontend uses a centralized API client with automatic error handling and token management:

```typescript
// lib/api.ts
import axios from 'axios';

const apiClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_BASE_URL,
  timeout: 30000,
});

// Automatic JWT token injection
apiClient.interceptors.request.use((config) => {
  const token = getStoredToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Generate mind map from PDF
export async function generateMindMap(file: File): Promise<ApiResponse<MindMapResponse>> {
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await apiClient.post('/api/v1/maps/generate-mindmap', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  });
  
  return { data: response.data };
}

// Ask question with chat history
export async function askQuestionWithHistory(
  mapId: string,
  question: string,
  jwt: string,
  nodeId?: string,
  nodeLabel?: string
): Promise<ApiResponse<NodeDetailResponse>> {
  const response = await apiClient.post('/api/v1/chat', {
    question,
    map_id: mapId,
    node_id: nodeId,
    node_label: nodeLabel,
    top_k: 10
  });
  
  return { data: response.data };
}
```

## 🔧 Advanced Configuration

### LangGraph Workflow Customization

The workflows can be customized through environment variables:

```env
# Workflow behavior
WORKFLOW_MAX_RETRIES=3
WORKFLOW_TIMEOUT_SECONDS=300
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
RELEVANCE_THRESHOLD=0.7

# Performance tuning
DEFAULT_TOP_K=10
```

### Custom LLM Models

Modify the LLM configuration in `app/core/config.py`:

```python
LLM_MODEL_NAME_GROQ: str = "llama-3.3-70b-versatile"  # or other Groq models
```

## 🐳 Docker Deployment

```bash
# Build
docker build -t vizmind-ai .

# Run
docker run -p 8000:8000 --env-file .env vizmind-ai
```

## 📊 Monitoring and Analytics

VizMind AI provides comprehensive workflow metrics:

* **Processing Time**: Track document processing duration
* **Chunk Statistics**: Monitor chunking and embedding performance
* **Query Performance**: RAG retrieval and generation metrics
* **Error Tracking**: Detailed error logging and retry statistics
* **Chat History Analytics**: Monitor cache hit rates, conversation lengths, and user engagement patterns

### Chat Performance Metrics

The chat history system provides significant performance improvements:

* **Cache Hit Rate**: Track percentage of questions answered from cache vs. new RAG queries
* **Response Time**: Cached responses are typically 10-50x faster than RAG workflows
* **Cost Optimization**: Reduce LLM API calls by 30-70% through intelligent caching
* **Token Efficiency**: Context window limited to 5 recent messages for optimal performance
* **User Engagement**: Track conversation depth and follow-up question patterns

Access metrics through the `/api/v1/maps/history` endpoint.

## 🔒 Security Features

- **JWT Authentication**: Secure token-based authentication
- **Google OAuth**: Trusted identity provider integration
- **User Isolation**: Multi-tenant data separation
- **Input Validation**: Comprehensive request validation
- **Rate Limiting**: Protection against abuse (configurable)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **LangChain & LangGraph**: For the powerful workflow orchestration
- **Docling**: For superior PDF processing capabilities
- **Groq**: For fast LLM inference
- **MongoDB Atlas**: For vector search capabilities
- **FastAPI**: For the robust web framework
