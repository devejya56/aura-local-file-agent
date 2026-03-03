# Build Aura Locally - Complete Instructions

This guide will help you build and run Aura with complete, production-ready code on your local machine.

## Quick Start (5 minutes)

```bash
# 1. Clone the repository
git clone https://github.com/devejya56/aura-local-file-agent.git
cd aura-local-file-agent

# 2. Install Ollama
# Visit https://ollama.com and download/install for your OS

# 3. Pull the required models
ollama pull llama3.2
ollama pull nomic-embed-text

# 4. Create Python environment
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 5. Install dependencies
pip install -r requirements.txt

# 6. Create .env file (see section below)
cp .env.example .env

# 7. Start Ollama server (Terminal 1)
ollama serve

# 8. Start Aura (Terminal 2, venv activated)
python main.py
```

## Production Code Implementation

The repository contains skeleton files. To use complete, production-ready code:

### Step 1: Get the Full Implementation

Read `COMPLETE_IMPLEMENTATION.md` in the repository. It contains complete implementations for:
- `config.py` - Configuration management
- `utils.py` - Utility functions
- `agent_core.py` - LLM integration (complete version)
- `memory.py` - Vector database (complete version)
- `agent_tools.py` - File tools (enhanced version)
- `main.py` - File watcher (production version)

### Step 2: Replace Skeleton Code

For each Python file in the repo:
1. Copy the production code from `COMPLETE_IMPLEMENTATION.md`
2. Replace the skeleton code
3. Save and commit to GitHub

### Step 3: Environment Configuration

Create a `.env` file in the root directory:

```env
# File System
AURA_WATCH_DIRECTORY=./watch_dir
AURA_ARCHIVE_DIRECTORY=./archive

# Database
AURA_DB_PATH=./aura_db

# LLM Configuration
AURA_OLLAMA_BASE_URL=http://localhost:11434
AURA_LLM_MODEL=llama3.2
AURA_EMBEDDING_MODEL=nomic-embed-text
AURA_LLM_TEMPERATURE=0.0
AURA_LLM_TIMEOUT=300

# Processing
AURA_MAX_FILE_SIZE_MB=100
AURA_BATCH_SIZE=5

# Logging
AURA_LOG_LEVEL=INFO
AURA_LOG_FILE=./aura.log

# Features
AURA_ENABLE_BACKUP=true
AURA_ENABLE_OCR=false
AURA_ENABLE_VECTOR_SEARCH=true
```

## Verification Checklist

- [ ] Python 3.11+ installed
- [ ] Ollama installed and running on port 11434
- [ ] Models downloaded: `llama3.2` and `nomic-embed-text`
- [ ] Virtual environment created and activated
- [ ] All dependencies installed: `pip list | grep -E "langchain|chromadb|watchdog"`
- [ ] `.env` file created in project root
- [ ] `watch_dir` folder exists
- [ ] No errors when running: `python -c "import langchain; import chromadb; import watchdog"`

## Testing the Installation

```bash
# Test 1: Check Python packages
python -c "import langchain; import chromadb; print('Imports OK')"

# Test 2: Check Ollama connection
curl http://localhost:11434/api/tags

# Test 3: Test ChromaDB
python -c "import chromadb; c = chromadb.Client(); print('ChromaDB OK')"

# Test 4: Start Aura in debug mode
python -c "from config import get_config; cfg = get_config(); print('Config loaded:', cfg.watch_directory)"
```

## Running Aura

### Terminal 1: Start Ollama
```bash
ollama serve
```

### Terminal 2: Start Aura Agent
```bash
cd aura-local-file-agent
source venv/bin/activate
python main.py
```

You should see:
```
2026-03-03 15:30:00 | INFO     | Aura agent initialized
2026-03-03 15:30:00 | INFO     | Aura is now monitoring: ./watch_dir
```

## Testing the Agent

```bash
# Create a test file
echo "Invoice for AWS cloud services March 2026" > watch_dir/test_invoice.txt

# Watch the logs - Aura should:
# 1. Detect the file
# 2. Read its content
# 3. Query the LLM for categorization
# 4. Move it to an organized folder
# 5. Index it in the vector database
```

## Production Deployment

For production use:

1. Use systemd service (Linux):
```ini
[Unit]
Description=Aura File Agent

[Service]
Type=simple
User=aura
ExecStart=/home/aura/aura-local-file-agent/venv/bin/python /home/aura/aura-local-file-agent/main.py
Restart=always
WorkingDirectory=/home/aura/aura-local-file-agent

[Install]
WantedBy=multi-user.target
```

2. Use Ollama as a service
3. Configure log rotation
4. Set up monitoring and alerts
5. Use dedicated disk space for database

## Troubleshooting

### "Cannot connect to Ollama"
- Ensure Ollama is running: `curl http://localhost:11434/api/tags`
- Check URL in `.env`: `AURA_OLLAMA_BASE_URL`

### "Module not found"
- Ensure venv is activated
- Run: `pip install -r requirements.txt`

### "Files not being processed"
- Check watch directory exists: `ls -la ./watch_dir`
- Check logs: `tail -f ./aura.log`
- Verify Aura is running: `ps aux | grep python`

### "Low performance"
- Use a smaller model or increase timeout
- Check system resources: `top`, `free -h`
- Reduce batch size in `.env`

## Next Steps

1. Review `COMPLETE_IMPLEMENTATION.md` for detailed code
2. Implement production code from the guide
3. Test with various file types
4. Configure for your specific use case
5. Set up monitoring and alerts
