# Aura - Setup Guide

Step-by-step instructions to build and run Aura locally.

## Prerequisites

- Python 3.11+
- Ollama (for running local LLMs)
- 8GB+ RAM (recommended for running LLMs locally)
- pip and venv

## Installation

### Step 1: Install Ollama

Download and install Ollama from [ollama.com](https://ollama.com)

```bash
# On Linux/Mac
curl -sSL https://ollama.ai/install.sh | sh

# On Windows
# Download from https://ollama.com/download
```

### Step 2: Pull the Language Models

```bash
# Main LLM for reasoning
ollama pull llama3.2

# Embedding model for vector search
ollama pull nomic-embed-text
```

### Step 3: Clone the Repository

```bash
git clone https://github.com/devejya56/aura-local-file-agent.git
cd aura-local-file-agent
```

### Step 4: Create Virtual Environment

```bash
python -m venv venv

# On Linux/Mac
source venv/bin/activate

# On Windows
venv\\Scripts\\activate
```

### Step 5: Install Dependencies

```bash
pip install -r requirements.txt
```

## Running Aura

### Start the Ollama Server

```bash
# Ollama runs on localhost:11434 by default
ollama serve
```

### Start Aura Agent

In a new terminal (with venv activated):

```bash
python main.py
```

You should see output like:
```
2026-03-03 14:30:00 | INFO     | Aura agent initialized
2026-03-03 14:30:00 | INFO     | Aura is now monitoring: ./Downloads_Test
```

## Testing

### Create a Test File

```bash
# Create a test text file
echo "Invoice for AWS Cloud hosting - January 2026" > Downloads_Test/test.txt
```

Watch Aura process the file:
- Read the file contents
- Determine it's an invoice
- Move it to an `Invoices` folder
- Index it in the vector database

## Configuration

Set environment variables to customize behavior:

```bash
# Watch directory
export WATCH_DIR="/path/to/watch"

# Vector database location
export DB_PATH="./my_vector_db"

# Ollama server endpoint (if not localhost:11434)
export OLLAMA_BASE_URL="http://localhost:11434"
```

## Architecture

```
File System
    ↓
Watchdog Monitor (main.py)
    ↓
File Detection
    ↓
Agent Core (agent_core.py)
    ↓ (uses tools)
Agent Tools (agent_tools.py)
    ├─ move_and_rename_file()
    ├─ create_folder()
    └─ get_file_size()
    ↓
File Operations & Memory
    ├─ Memory/Vector DB (memory.py)
    │   └─ ChromaDB for semantic search
    └─ Local File System
```

## Troubleshooting

### "Connection refused" error

Ensure Ollama server is running:
```bash
curl http://localhost:11434/api/tags
```

### ChromaDB directory errors

Delete and recreate the vector database:
```bash
rm -rf local_file_db/
python -c "from memory import init_memory; init_memory()"
```

### Files not being detected

Check file permissions and watch directory path:
```bash
ls -la Downloads_Test/
```

## Next Steps

After setup, read [ARCHITECTURE.md](./ARCHITECTURE.md) for detailed technical documentation.
