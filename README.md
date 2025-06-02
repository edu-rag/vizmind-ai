# CMVS - Concept Map Visual Synthesizer

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)](https://fastapi.tiangolo.com)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.4+-orange.svg)](https://langchain-ai.github.io/langgraph/)
[![MongoDB](https://img.shields.io/badge/MongoDB-Atlas-green.svg)](https://mongodb.com)

A sophisticated AI-powered API that transforms PDF documents into interactive concept maps using advanced natural language processing and graph visualization techniques.

## 🚀 Features

### Core Capabilities
- **PDF Processing**: Extract and analyze text from uploaded PDF documents
- **Intelligent Text Chunking**: Semantic-based text segmentation using embeddings
- **Concept Extraction**: AI-powered extraction of key concepts and relationships using Groq LLaMA models
- **Graph Processing**: Advanced graph analysis with semantic similarity matching
- **Mermaid Visualization**: Generate Mermaid.js compatible graph syntax for visualization
- **Vector Storage**: Embedded chunks stored for future similarity search and retrieval

### Technical Features
- **JWT Authentication**: Secure API access with Google OAuth integration
- **Async Architecture**: Built with FastAPI for high-performance async operations
- **LangGraph Pipeline**: State-based processing workflow using LangGraph
- **S3 Storage**: Document storage and management with S3-compatible services
- **MongoDB Integration**: Persistent storage for users, Maps, and embeddings
- **Error Handling**: Comprehensive error handling and logging throughout the pipeline

## 🏗️ Architecture

The CMVS system follows a modular architecture with clear separation of concerns:

```
cmvs_api_project/
├── app/                   # Main application package
│   ├── __init__.py
│   ├── main.py            # FastAPI app instance, startup/shutdown (lifespan), main routers
│   ├── api/               # API endpoint definitions (routers)
│   │   ├── __init__.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── routers.py             # Aggregates all v1 routers
│   │       ├── endpoints/
│   │       │   ├── __init__.py
│   │       │   ├── auth_ep.py         # Authentication endpoints
│   │       │   └── concept_maps_ep.py # Concept map generation endpoint
│   │       └── deps.py                # FastAPI dependencies (e.g., get_current_active_user)
│   ├── core/                          # Core application logic and settings
│   │   ├── __init__.py
│   │   ├── config.py        # Configuration loading (env vars, Pydantic Settings)
│   │   └── security.py      # JWT, Google token verification, password hashing (if needed)
│   ├── models/              # Pydantic models (data schemas)
│   │   ├── __init__.py
│   │   ├── user_models.py
│   │   ├── token_models.py
│   │   └── cmvs_models.py   # Includes API request/response and internal CMVS data structures
│   ├── services/            # Business logic, interactions with external services/DB
│   │   ├── __init__.py
│   │   ├── user_service.py
│   │   ├── s3_service.py
│   │   ├── pdf_service.py
│   │   └── cmvs_service.py  # Facade for the LangGraph pipeline execution
│   ├── db/                  # Database interaction layer
│   │   ├── __init__.py
│   │   └── mongodb_utils.py # MongoDB client, collection getters, helper functions
│   ├── langgraph_pipeline/  # LangGraph specific components
│   │   ├── __init__.py
│   │   ├── state.py         # GraphState, EmbeddedChunk definitions
│   │   ├── nodes.py         # CMVSNodes class
│   │   └── builder.py       # build_graph function, global LangGraph app instance
│   └── utils/               # General utility functions
│       ├── __init__.py
│       └── cmvs_helpers.py  # normalize_label, generate_mermaid_syntax
├── .env                     # Environment variables (KEEP THIS!)
├── requirements.txt         # Project dependencies
└── uvicorn_runner.py        # Optional: Script to run uvicorn for convenience

```

### Pipeline Flow

1. **Authentication** → Verify user via Google OAuth
2. **PDF Upload** → Store in S3 and extract text
3. **Text Chunking** → Semantic chunking using embeddings
4. **Embedding** → Generate vector embeddings for chunks
5. **Concept Extraction** → Extract triples (subject-predicate-object) using LLM
6. **Graph Processing** → Merge similar concepts using semantic similarity
7. **Visualization** → Generate Mermaid graph syntax
8. **Storage** → Save results to MongoDB

## 📋 Prerequisites

- Python 3.12+
- MongoDB Atlas account or local MongoDB instance
- Groq API key for LLM access
- Google OAuth credentials (for authentication)
- S3-compatible storage (AWS S3, MinIO, Cloudflare R2, etc.)

## ⚙️ Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd cmvs
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Configuration**
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` with your configuration:
   ```env
   # Groq Configuration
   GROQ_API_KEY=your_groq_api_key_here
   
   # MongoDB Configuration
   MONGODB_URI=your_mongodb_connection_uri_here
   MONGODB_DATABASE_NAME=cmvs_project
   
   # S3 Configuration
   S3_ACCESS_KEY_ID=your_s3_access_key_id
   S3_SECRET_ACCESS_KEY=your_s3_secret_access_key
   S3_ENDPOINT_URL=your_s3_endpoint_url
   S3_BUCKET_NAME=your_s3_bucket_name
   
   # Authentication
   JWT_SECRET_KEY=your_super_secret_jwt_key
   GOOGLE_CLIENT_ID=your_google_oauth_client_id.apps.googleusercontent.com
   
   # Optional: LangSmith Tracing
   LANGSMITH_TRACING=true
   LANGSMITH_API_KEY=your_langsmith_api_key
   LANGSMITH_PROJECT=your_project_name
   ```

## 🚀 Usage

### Starting the Server

#### Development
```bash
python uvicorn_runner.py
```

#### Production
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### API Documentation
Once running, access the interactive API documentation:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Testing the Pipeline
Run the test script to verify everything is working:
```bash
python test_pipeline.py
```

## 📚 API Endpoints

### Authentication
- `POST /api/v1/auth/google` - Authenticate with Google OAuth
- `GET /api/v1/auth/users/me` - Get current user information

### Maps
- `POST /api/v1/concept-maps/secure-generate/` - Generate Maps from PDFs

### Example Usage

1. **Authenticate**
   ```bash
   curl -X POST "http://localhost:8000/api/v1/auth/google" \
        -H "Content-Type: application/json" \
        -d '{"google_id_token": "your_google_id_token"}'
   ```

2. **Generate Concept Map**
   ```bash
   curl -X POST "http://localhost:8000/api/v1/concept-maps/secure-generate/" \
        -H "Authorization: Bearer your_jwt_token" \
        -F "files=@document.pdf"
   ```

## 🔧 Configuration

### Environment Variables

| Variable               | Description                       | Required |
| ---------------------- | --------------------------------- | -------- |
| `GROQ_API_KEY`         | Groq API key for LLM access       | Yes      |
| `MONGODB_URI`          | MongoDB connection string         | Yes      |
| `S3_ACCESS_KEY_ID`     | S3 access key                     | Yes      |
| `S3_SECRET_ACCESS_KEY` | S3 secret key                     | Yes      |
| `S3_ENDPOINT_URL`      | S3 endpoint URL                   | Yes      |
| `S3_BUCKET_NAME`       | S3 bucket name                    | Yes      |
| `JWT_SECRET_KEY`       | JWT signing secret                | Yes      |
| `GOOGLE_CLIENT_ID`     | Google OAuth client ID            | Yes      |
| `LANGSMITH_TRACING`    | Enable LangSmith tracing          | No       |
| `LOG_LEVEL`            | Logging level (INFO, DEBUG, etc.) | No       |

### Model Configuration

- **LLM Model**: `llama-3.3-70b-versatile` (Groq)
- **Embedding Model**: `paraphrase-multilingual-mpnet-base-v2`
- **Similarity Threshold**: 0.85 for concept merging

## 🗄️ Database Schema

### Collections

1. **users** - User authentication and profile data
2. **concept_maps_api_s3_auth** - Generated Maps with metadata
3. **chunk_embeddings** - Text chunks with vector embeddings

## 🔍 Monitoring & Debugging

### Logging
The application uses structured logging with configurable levels. Logs include:
- Authentication events
- Pipeline processing steps
- Error handling and debugging information
- Performance metrics

### LangSmith Integration
Optional integration with LangSmith for:
- LLM call tracing
- Performance monitoring
- Debugging AI pipeline issues

## 🚨 Error Handling

The system includes comprehensive error handling for:
- Invalid PDF files
- Authentication failures
- LLM API errors
- Database connection issues
- S3 storage problems

## 🔒 Security

- **JWT Authentication**: Secure API access
- **Google OAuth**: Trusted identity provider
- **Input Validation**: Comprehensive request validation
- **Rate Limiting**: Built-in FastAPI rate limiting
- **Secure Headers**: Security headers for API responses

## 🧪 Testing

Run the complete pipeline test:
```bash
python test_pipeline.py
```

This test verifies:
- Text chunking functionality
- Embedding generation
- Concept extraction
- Graph processing
- Mermaid code generation
- Database storage

## 📊 Performance

### Optimization Features
- Async/await throughout the pipeline
- Thread pool execution for CPU-bound operations
- Efficient vector similarity calculations
- Semantic chunking for optimal text processing
- Connection pooling for database operations

### Scalability
- Stateless API design
- Horizontal scaling capabilities
- Efficient memory usage
- Configurable processing parameters

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For support and questions:
1. Check the [API documentation](http://localhost:8000/docs)
2. Review the logs for detailed error information
3. Run the test pipeline to verify configuration
4. Check environment variable configuration

## 🔮 Future Enhancements

- [ ] Real-time concept map visualization
- [ ] Batch processing capabilities
- [ ] Advanced graph analytics
- [ ] Multi-language support
- [ ] Custom embedding models
- [ ] Interactive concept map editing
- [ ] Export to various formats (SVG, PNG, PDF)
- [ ] Collaborative features

---

**Built with ❤️ using FastAPI, LangGraph, and modern AI technologies**
