# Internal AI Assistant

An AI-powered assistant for product and engineering teams to extract insights from internal documents, bug reports, and user feedback. The system provides document Q&A, issue summarization, and intelligent routing capabilities.

## Features

- **Document Q&A**: Answer questions from internal documents using semantic search
- **Issue Summarization**: Extract structured information from bug reports and user feedback
- **Intelligent Routing**: LLM-powered agent that routes queries to the appropriate tool
- **Multilingual Support**: Supports both Thai and English content with multilingual embeddings
- **FastAPI Integration**: RESTful API with automatic documentation
- **Docker Support**: Containerized deployment for easy setup and scaling

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   API Layer     │    │   Router Agent   │    │    Tools        │
│                 │    │                  │    │                 │
│ ┌─────────────┐ │    │ ┌──────────────┐ │    │ ┌─────────────┐ │
│ │   FastAPI   │ │────│ │ LLM Router   │ │────│ │ QA Tool      │ │
│ └─────────────┘ │    │ └──────────────┘ │    │ └─────────────┘ │
│                 │    │                  │    │                 │
│ ┌─────────────┐ │    │ ┌──────────────┐ │    │ ┌─────────────┐ │
│ │ Endpoints   │ │    │ │ Tool Decision│ │    │ │ Summary Tool│ │
│ └─────────────┘ │    │ └──────────────┘ │    │ └─────────────┘ │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │ Vector Database │
                    │                 │
                    │ ┌─────────────┐ │
                    │ │ ChromaDB    │ │
                    │ └─────────────┘ │
                    │                 │
                    │ ┌─────────────┐ │
                    │ │ Embeddings  │ │
                    │ └─────────────┘ │
                    └─────────────────┘
```

## Quick Start

### Prerequisites

- Python 3.11+
- Docker (optional, for containerized deployment)
- OpenAI-compatible API access

### Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd ai-inter
   ```

2. **Set up environment variables**:
   
   **Option A: Using OpenRouter (Recommended)**
   ```bash
   # Create .env file
   cat > .env << EOF
   # OpenRouter Configuration
   OPENROUTER_API_KEY=your-openrouter-api-key-here
   OPENROUTER_MODEL_NAME=google/gemini-2.5-flash
   OPENROUTER_API_BASE=https://openrouter.ai/api/v1
   EOF
   ```
   
   **Option B: Using OpenAI**
   ```bash
   # Create .env file
   cat > .env << EOF
   OPENAI_API_BASE=https://api.openai.com/v1
   OPENAI_API_KEY=your-openai-api-key-here
   OPENAI_MODEL=gpt-4o-mini
   EOF
   ```

3. **Choose Deployment Method**:
   
   **Method A: Local Development**
   ```bash
   make setup
   make ingest
   make run
   ```
   
   **Method B: Docker Development**
   ```bash
   docker-compose up --build
   ```
   
   **Method C: Docker Production**
   ```bash
   make deploy-prod  # Production deployment
   ```

3. **Install dependencies**:
   ```bash
   make setup
   ```

4. **Ingest documents**:
   ```bash
   make ingest
   ```

5. **Run the server**:
   ```bash
   make run
   ```

The API will be available at `http://localhost:8000`

### Docker Deployment

1. **Build and run with Docker Compose**:
   ```bash
   docker-compose up --build
   ```

2. **Or build manually**:
   ```bash
   docker build -t internal-assistant:latest .
   docker run -p 8000:8000 --env-file .env internal-assistant:latest
   ```

## API Documentation

Once the server is running, visit:
- **Swagger UI**: `http://localhost:8000/docs`
- **OpenAPI Schema**: `http://localhost:8000/openapi.json`

### Key Endpoints

#### Health Check
```bash
GET /api/v1/healthz
```

#### Document Q&A
```bash
POST /api/v1/qa
Content-Type: application/json

{
  "query": "What are the issues reported on email notification?"
}
```

#### Issue Summarization
```bash
POST /api/v1/summarize
Content-Type: application/json

{
  "issue_text": "Users do not receive signup confirmation; bulk send is very slow."
}
```

#### Intelligent Routing
```bash
POST /api/v1/query
Content-Type: application/json

{
  "query": "What are the issues reported on email notification?"
}
```

## Document Sources

The system ingests and indexes these document sources:

1. **`ai_test_bug_report.txt`** - Technical bug reports with reproduction steps
2. **`ai_test_user_feedback.txt`** - Customer feedback snippets  

## Usage Examples

### Example 1: Q&A Query
```bash
curl -X POST localhost:8000/api/v1/qa \
  -H "Content-Type: application/json" \
  -d '{"query":"What did users say about the search bar?"}'
```

**Response**:
```json
{
  "query": "What did users say about the search bar?",
  "answer": "Users reported that searching for acronyms like \"CEO\" returns irrelevant documents containing individual letters separately rather than the acronym itself.",
  "sources": ["ai_test_user_feedback.txt:chunk_1", "ai_test_bug_report.txt:chunk_1"],
  "confidence": 0.85
}
```

### Example 2: Issue Summarization
```bash
curl -X POST localhost:8000/api/v1/summarize \
  -H "Content-Type: application/json" \
  -d '{"issue_text":"Users do not receive signup confirmation; bulk send is very slow."}'
```

**Response**:
```json
{
  "raw_text": "Users do not receive signup confirmation; bulk send is very slow.",
  "reported_issues": ["Email notifications not sent", "Slow bulk email sending"],
  "affected_components": ["Email service", "User registration"],
  "severity": "High",
  "suggestions": ["Check email queue", "Verify SMTP settings", "Optimize bulk sending logic"]
}
```

### Example 3: Intelligent Routing
```bash
curl -X POST localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"query":"What are the issues with pagination?"}'
```

**Response**:
```json
{
  "decision": {
    "tool": "qa",
    "rationale": "The question asks for factual information from internal documents.",
    "tool_input": {"query": "What are the issues with pagination?"}
  },
  "result": {
    "query": "What are the issues with pagination?",
    "answer": "Users report that clicking on page numbers in search results sometimes redirects back to the first page instead of the selected page.",
    "sources": ["ai_test_user_feedback.txt:chunk_3", "ai_test_bug_report.txt:chunk_3"],
    "confidence": 0.78
  }
}
```

## Development

### Project Structure

```
ai-inter/
├── app/                    # Main application code
│   ├── __init__.py
│   ├── config.py          # Configuration management
│   ├── schemas.py         # Pydantic data models
│   ├── ingestion.py       # Document ingestion logic
│   ├── vectordb.py        # Vector database operations
│   ├── llm_client.py      # LLM API client
│   ├── tools/             # Core tools
│   │   ├── qa_tool.py     # Document Q&A functionality
│   │   ├── issue_summary_tool.py  # Issue summarization
│   │   ├── router_agent.py       # Intelligent routing
│   │   └── prompts/       # Prompt templates
│   ├── api/               # FastAPI application
│   │   ├── main.py        # FastAPI app setup
│   │   └── routes.py      # API endpoints
│   └── tests/             # Unit tests
├── data/                  # Source documents
├── requirements.txt       # Python dependencies
├── Dockerfile            # Container definition
├── docker-compose.yml    # Docker Compose configuration
├── Makefile              # Build automation
└── README.md            # This file
```

### Running Tests

```bash
# Run all tests
make test

# Run with coverage
make test-coverage

# Run with verbose output
make test-verbose
```

### Development Workflow

1. **Make changes** to source code
2. **Run tests**: `make test`
3. **Format code**: `make format` (requires black)
4. **Lint code**: `make lint` (requires flake8)
5. **Test API**: `make run` then test endpoints

### Configuration

The application uses environment variables for configuration:

| Variable | Description | Default |
|----------|-------------|---------|
| `EMBEDDING_MODEL` | Sentence transformers model | `intfloat/multilingual-e5-base` |
| `VECTOR_DIR` | ChromaDB storage directory | `/app/chroma` |
| **OpenRouter** | | |
| `OPENROUTER_API_KEY` | OpenRouter API key | (required for OpenRouter) |
| `OPENROUTER_MODEL_NAME` | OpenRouter model name | `google/gemini-2.5-flash` |
| `OPENROUTER_API_BASE` | OpenRouter API endpoint | `https://openrouter.ai/api/v1` |
| **OpenAI** | | |
| `OPENAI_API_BASE` | OpenAI API endpoint | `https://api.openai.com/v1` |
| `OPENAI_API_KEY` | OpenAI API key | (required for OpenAI) |
| `OPENAI_MODEL` | OpenAI model name | `gpt-4o-mini` |
| **Settings** | | |
| `TOP_K` | Number of retrieved documents | `4` |
| `MAX_CHUNK_CHARS` | Maximum chunk size | `1024` |
| `TEMPERATURE` | LLM generation temperature | `0.2` |
| `MAX_TOKENS` | Maximum tokens per response | `800` |

## Troubleshooting

### Common Issues

1. **Vector Database Errors**:
   ```bash
   # Reset and re-ingest documents
   make reset-ingest
   ```

2. **LLM API Connection Issues**:
   - For OpenRouter: Verify `OPENROUTER_API_KEY` is correct
   - For OpenAI: Verify `OPENAI_API_KEY` is correct
   - Check network connectivity to API endpoint
   - Ensure API key has sufficient permissions
   - Verify model name is correct for the chosen provider

3. **Memory Issues with Large Documents**:
   - Reduce `MAX_CHUNK_CHARS` environment variable
   - Monitor system resources and adjust Docker memory limits

4. **Embedding Model Download Issues**:
   - Ensure internet connectivity for first run
   - Check sufficient disk space for model cache

### Debug Mode

Enable debug logging:
```bash
export PYTHONPATH=$(pwd)
python -m app.ingestion --default --docs "data/test_file.txt"
```

### Performance Optimization

1. **Vector Database**:
   - Tune `TOP_K` for balance between relevance and performance
   - Consider ChromaDB clustering for large datasets

2. **LLM Integration**:
   - Adjust `TEMPERATURE` and `MAX_TOKENS` for response quality/speed
   - Use faster models for high-throughput scenarios

3. **Caching**:
   - Vector embeddings are cached automatically
   - Consider response caching for frequently asked questions

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make changes and add tests
4. Run tests: `make test`
5. Submit a pull request

## Supported LLM Providers

### OpenRouter (Recommended)
OpenRouter provides access to multiple models from different providers:

**Models:**
- `google/gemini-2.5-flash`

**Setup:**
```bash
export OPENROUTER_API_KEY="sk-or-v1-your-key-here"
export OPENROUTER_MODEL_NAME="google/gemini-2.5-flash"
```

### OpenAI
Direct OpenAI API integration:

**Setup:**
```bash
export OPENAI_API_KEY="sk-your-openai-key-here"
export OPENAI_MODEL="gpt-4o-mini"
```

### Other OpenAI-Compatible Providers
The system supports any OpenAI-compatible API endpoint:

```bash
export OPENAI_API_BASE="https://your-provider.com/v1"
export OPENAI_API_KEY="your-api-key"
export OPENAI_MODEL="your-model-name"
```

## Support

For support and questions:
- Check the troubleshooting section above
- Review API documentation at `/docs`
- Examine application logs for error details
- Test with the provided example queries

## Future Enhancements

- [ ] Telemetry and monitoring dashboard
- [ ] Prometheus metrics endpoint
- [ ] Authentication and RBAC
- [ ] Document versioning support
- [ ] Advanced filtering and faceted search
- [ ] Batch processing capabilities
- [ ] Integration with external data sources