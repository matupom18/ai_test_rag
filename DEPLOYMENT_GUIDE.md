# Internal AI Assistant - OpenRouter Deployment Guide

## Quick Deployment with OpenRouter

This guide provides step-by-step instructions for deploying the Internal AI Assistant using OpenRouter API.

## Prerequisites

### System Requirements
- **Docker** and **Docker Compose** installed
- **Git** for cloning the repository
- **OpenRouter API Key** (get one at https://openrouter.ai/)

### Required Files
Ensure these files exist in your project directory:
```
ai-inter/
├── docker-compose.yml
├── Dockerfile
├── .env.example
├── Makefile
├── deploy.sh (Linux/Mac) or deploy.bat (Windows)
└── data/
    ├── ai_test_bug_report.txt
    ├── @AI Engineer Test.txt
```

## Environment Configuration

### Step 1: Create Environment File

**For Development:**
```bash
cp .env.example .env
```

**For Production:**
```bash
cp .env.production.example .env.production
```

### Step 2: Configure OpenRouter API

Edit your environment file with OpenRouter credentials:

```bash
# OpenRouter Configuration (Required)
OPENROUTER_API_KEY=sk-or-v1-your-actual-api-key-here
OPENROUTER_MODEL_NAME=google/gemini-2.5-flash
OPENROUTER_API_BASE=https://openrouter.ai/api/v1

# Alternative OpenRouter Models:
# OPENROUTER_MODEL_NAME=anthropic/claude-3.5-sonnet
# OPENROUTER_MODEL_NAME=openai/gpt-4o
# OPENROUTER_MODEL_NAME=meta-llama/llama-3.1-70b-instruct
```

### Step 3: Additional Configuration (Optional)

```bash
# Embedding Settings
EMBEDDING_MODEL=intfloat/multilingual-e5-base
TOP_K=4
MAX_CHUNK_CHARS=1024

# LLM Settings
TEMPERATURE=0.2
MAX_TOKENS=800

# Server Settings
PORT=8000
LOG_LEVEL=INFO
```

## Docker Deployment

### Method 1: Automated Deployment (Recommended)

#### Linux/Mac Users:
```bash
# Development Deployment
make deploy

# Production Deployment
make deploy-prod

# Full Production Workflow
make deploy-full
```

#### Windows Users:
```cmd
# Development Deployment
deploy.bat

# Production Deployment
deploy.bat -e prod -b
```

### Method 2: Manual Docker Commands

#### Step 1: Build Docker Image
```bash
docker build -t internal-assistant:latest .
```

#### Step 2: Run with Docker Compose

**Development:**
```bash
docker-compose --env-file .env up -d
```

**Production:**
```bash
docker-compose --env-file .env.production up -d
```

#### Step 3: Verify Deployment
```bash
# Check container status
docker-compose ps

# View logs
docker-compose logs -f

# Test API
curl http://localhost:8000/api/v1/healthz
```

## API Access and Testing

### Access Points
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/api/v1/healthz
- **Stats**: http://localhost:8000/api/v1/stats

### Test OpenRouter Integration

#### 1. Test API Connection
```bash
curl -X POST http://localhost:8000/api/v1/qa \
  -H "Content-Type: application/json" \
  -d '{"query":"What are the search issues?"}'
```

#### 2. Test Router with OpenRouter
```bash
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"query":"Users report upload stuck at 99%"}'
```

#### 3. Test Issue Summarization
```bash
curl -X POST http://localhost:8000/api/v1/summarize \
  -H "Content-Type: application/json" \
  -d '{"issue_text":"Email notifications are not being sent to users"}'
```

## Troubleshooting

### Common Issues

#### 1. OpenRouter API Key Issues
**Symptom**: 401 Unauthorized errors
**Solution**:
```bash
# Verify API key is correctly set
grep OPENROUTER_API_KEY .env

# Test API key manually
curl -H "Authorization: Bearer $OPENROUTER_API_KEY" \
     -H "Content-Type: application/json" \
     https://openrouter.ai/api/v1/chat/completions \
     -d '{"model":"google/gemini-2.5-flash","messages":[{"role":"user","content":"test"}]}'
```

#### 2. Docker Container Won't Start
**Symptom**: Container exits immediately
**Solution**:
```bash
# Check container logs
docker-compose logs assistant

# Verify environment file
docker-compose --env-file .env config

# Recreate container
docker-compose down
docker-compose up -d --force-recreate
```

#### 3. API Endpoints Not Responding
**Symptom**: Connection refused
**Solution**:
```bash
# Check if container is running
docker-compose ps

# Check port mapping
docker-compose port assistant 8000

# Restart services
docker-compose restart
```

#### 4. Vector Database Issues
**Symptom**: No search results
**Solution**:
```bash
# Re-ingest documents
docker-compose exec assistant python -m app.ingestion --reset --default

# Check vector database status
curl http://localhost:8000/api/v1/stats
```

### Debug Commands

#### Docker Debugging
```bash
# Check container health
docker-compose ps

# View real-time logs
docker-compose logs -f assistant

# Execute commands inside container
docker-compose exec assistant bash

# Check environment variables
docker-compose exec assistant printenv | grep OPENROUTER
```

#### API Debugging
```bash
# Test API connection directly
curl -v http://localhost:8000/api/v1/healthz

# Check OpenRouter model info
curl -H "Authorization: Bearer $OPENROUTER_API_KEY" \
     https://openrouter.ai/api/v1/models

# Test full request flow
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"query":"test"}' -v
```

## Production Considerations

### Security
1. **API Key Management**: Never commit API keys to version control
2. **Environment Variables**: Use secure methods to manage secrets
3. **Network Security**: Configure proper CORS origins in production
4. **Container Security**: Run containers with non-root users (already configured)

### Performance
1. **Resource Limits**: Set appropriate memory and CPU limits
2. **Monitoring**: Implement health checks and monitoring
3. **Scaling**: Consider horizontal scaling for high load
4. **Caching**: Vector embeddings are cached automatically

### Backup and Recovery
1. **Vector Data**: Volume mount persists ChromaDB data
2. **Configuration**: Backup environment files
3. **Logs**: Configure log rotation
4. **Disaster Recovery**: Document recovery procedures

### Monitoring Setup
```yaml
# Add to docker-compose.yml for monitoring
services:
  assistant:
    # ... existing config ...
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/healthz"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

## Monitoring and Maintenance

### Health Monitoring
```bash
# Automated health check
make deploy-test

# Manual health check
curl http://localhost:8000/api/v1/healthz

# Vector database stats
curl http://localhost:8000/api/v1/stats
```

### Log Management
```bash
# View recent logs
docker-compose logs --tail=100

# Follow logs in real-time
docker-compose logs -f

# Export logs to file
docker-compose logs > assistant-logs.txt
```

### Updates and Maintenance
```bash
# Update Docker image
docker-compose pull
docker-compose up -d

# Rebuild with latest code
docker-compose build --no-cache
docker-compose up -d --force-recreate

# Cleanup old images
docker image prune -f
```

## Advanced Configuration

### Custom OpenRouter Models
```bash
# High-performance model
OPENROUTER_MODEL_NAME=google/gemini-2.5-flash-exp

# High-quality reasoning
OPENROUTER_MODEL_NAME=anthropic/claude-3.5-sonnet

# Cost-effective option
OPENROUTER_MODEL_NAME=meta-llama/llama-3.1-8b-instruct
```

### Environment-Specific Configurations

#### Development (.env)
```bash
OPENROUTER_MODEL_NAME=google/gemini-2.5-flash
TEMPERATURE=0.2
LOG_LEVEL=DEBUG
```

#### Production (.env.production)
```bash
OPENROUTER_MODEL_NAME=anthropic/claude-3.5-sonnet
TEMPERATURE=0.1
LOG_LEVEL=INFO
CORS_ORIGINS=https://yourdomain.com
```

### Scaling Configuration
```yaml
# docker-compose.prod.yml
version: "3.8"
services:
  assistant:
    image: internal-assistant:latest
    deploy:
      replicas: 3
      resources:
        limits:
          memory: 2G
          cpus: '1.0'
```

## Additional Resources

### OpenRouter Documentation
- [OpenRouter API Docs](https://openrouter.ai/docs)
- [Available Models](https://openrouter.ai/models)
- [Pricing](https://openrouter.ai/pricing)

### Docker Documentation
- [Docker Compose Reference](https://docs.docker.com/compose/)
- [Dockerfile Best Practices](https://docs.docker.com/develop/dev-best-practices/)

### API Documentation
Once deployed, visit http://localhost:8000/docs for interactive API documentation.

## Support

If you encounter issues:

1. **Check this guide** for troubleshooting steps
2. **Verify environment** configuration
3. **Test OpenRouter API** connectivity
4. **Review container logs** for errors
5. **Check Docker resources** and system requirements

## Success Checklist

Before going to production, verify:

- [ ] OpenRouter API key is valid and has sufficient credits
- [ ] All data files are present in the `data/` directory
- [ ] Docker containers start successfully
- [ ] Health check endpoint responds correctly
- [ ] All API endpoints function properly
- [ ] Vector database contains ingested documents
- [ ] CORS is configured for your domain (production)
- [ ] Monitoring and logging are set up
- [ ] Backup strategy is in place

Once all items are checked, your Internal AI Assistant is ready for production use with OpenRouter! 🚀