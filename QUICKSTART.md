# AYITI AI - Quick Start Guide

Get started with AYITI AI in 5 minutes!

## Prerequisites

- Python 3.8 or higher
- pip package manager
- DeepSeek API key (sign up at https://platform.deepseek.com)

## Quick Setup

### 1. Run Setup Script

```bash
# Make setup script executable (if not already)
chmod +x scripts/setup.sh

# Run setup
./scripts/setup.sh
```

This script will:
- Create a virtual environment
- Install all dependencies
- Create data directories
- Initialize the agriculture knowledge base
- Create .env file from template

### 2. Configure API Key

Edit the `.env` file and add your DeepSeek API key:

```bash
DEEPSEEK_API_KEY=your_actual_api_key_here
SECRET_KEY=your_secret_key_for_jwt
```

Generate a secret key with:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 3. Start the Server

```bash
# Activate virtual environment
source ayiti_env/bin/activate

# Start server
python -m uvicorn api.app:app --reload --host 0.0.0.0 --port 8000
```

### 4. Test the API

Open your browser and go to:
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Root**: http://localhost:8000

## Example API Calls

### Query in Kreyòl (Haitian Creole)

```bash
curl -X POST "http://localhost:8000/api/v1/query" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Kijan mwen ka amelyore pwodiksyon manyòk mwen?",
    "language_preference": "ht"
  }'
```

### Query in English

```bash
curl -X POST "http://localhost:8000/api/v1/query" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "How can I improve my cassava production?",
    "language_preference": "en"
  }'
```

### Query in French

```bash
curl -X POST "http://localhost:8000/api/v1/query" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Comment puis-je améliorer ma production de manioc?",
    "language_preference": "fr"
  }'
```

## Check System Stats

### View Cost Statistics

```bash
curl http://localhost:8000/api/v1/stats/cost
```

### View Knowledge Base Statistics

```bash
curl http://localhost:8000/api/v1/stats/knowledge
```

### List Available Sectors

```bash
curl http://localhost:8000/api/v1/sectors
```

### List Supported Languages

```bash
curl http://localhost:8000/api/v1/languages
```

## Interactive API Documentation

Visit http://localhost:8000/docs for interactive Swagger UI documentation where you can:
- Test all endpoints
- See request/response schemas
- Try different queries in different languages

## Example Queries by Sector

### Agriculture (Agrikilti)
- "Kijan pou m plante bannann?" (How to plant plantains?)
- "Ki jan pou m pwoteje jaden mwen kont sechrès?" (How to protect my garden from drought?)
- "Kisa m ka fè pou kontwole ensèk san chimik?" (What can I do to control insects without chemicals?)

### Education (Edikasyon)
- "Ki resous disponib pou aprann timoun yon trade?" (What resources are available to teach children a trade?)
- "Kijan pou m amelyore metòd ansèyman mwen?" (How can I improve my teaching methods?)

### Fishing (Lapèch)
- "Ki teknik pèch dirab?" (What are sustainable fishing techniques?)
- "Kijan pou m konsève pwason?" (How can I preserve fish?)

## Project Structure

```
ayiti-ai/
├── core/                  # Core system components
│   ├── llm_integration.py      # DeepSeek API integration
│   ├── multilingual_handler.py # Language detection & translation
│   ├── context_router.py       # Sector detection
│   └── config_manager.py       # Configuration management
├── rag_system/           # RAG (Retrieval-Augmented Generation)
│   ├── vector_store.py        # Vector database
│   ├── document_processor.py  # Document processing
│   └── retrieval_engine.py    # Search & retrieval
├── api/                  # FastAPI application
│   ├── app.py                 # Main application
│   └── endpoints.py           # API endpoints
├── knowledge_base/       # Sector knowledge bases
│   ├── agriculture/           # Agriculture KB (loaded)
│   ├── education/            # Education KB (to be loaded)
│   ├── fishing/              # Fishing KB (to be loaded)
│   ├── infrastructure/       # Infrastructure KB (to be loaded)
│   ├── health/               # Health KB (to be loaded)
│   └── governance/           # Governance KB (to be loaded)
├── scripts/              # Utility scripts
│   ├── setup.sh              # Setup script
│   └── init_agriculture_kb.py # Agriculture KB loader
└── data/                 # Data storage
    ├── vector_db/            # Vector database storage
    ├── processed/            # Processed documents
    └── raw_documents/        # Raw source documents
```

## Troubleshooting

### Import Errors

Make sure you're in the virtual environment:
```bash
source ayiti_env/bin/activate
```

### API Key Issues

Verify your `.env` file has the correct API key:
```bash
cat .env | grep DEEPSEEK_API_KEY
```

### Vector Store Issues

If you need to reinitialize the agriculture knowledge base:
```bash
python scripts/init_agriculture_kb.py
```

### Port Already in Use

If port 8000 is in use, specify a different port:
```bash
python -m uvicorn api.app:app --reload --port 8001
```

## Next Steps

1. **Add More Knowledge**: Expand the agriculture knowledge base or add other sectors
2. **Customize**: Adjust configurations in `.env` file
3. **Monitor Costs**: Check `/api/v1/stats/cost` regularly
4. **Expand Sectors**: Create knowledge bases for education, fishing, etc.
5. **Deploy**: Follow production deployment guidelines in README.md

## Support

For issues or questions:
- Check the main README.md for detailed documentation
- Review API documentation at /docs endpoint
- Check logs in the `logs/` directory

## Phase 1 Complete! 🎉

You now have:
- ✅ Working DeepSeek LLM integration
- ✅ Multilingual support (Kreyòl, French, English, Spanish)
- ✅ RAG system with vector search
- ✅ Agriculture knowledge base loaded
- ✅ FastAPI server with endpoints
- ✅ Cost tracking and monitoring

Ready to help Haiti! 🇭🇹
