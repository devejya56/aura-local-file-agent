# 🧠 Aura — Local AI File Organization Agent

> **Zero cloud. Zero cost. 100% private.**
> Drop a file → AI reads it → auto-categorized, renamed, and organized.

Aura is a local-first autonomous agent that watches your file system, analyzes file contents using a **local LLM** (via [Ollama](https://ollama.com)), intelligently categorizes and renames files, organizes them into folders, and indexes everything in a **vector database** for instant semantic search. No data ever leaves your machine.

---

## ✨ Features

| Feature | Description |
|---|---|
| 🔍 **Smart Categorization** | LLM reads file content and assigns categories (Invoice, Resume, Code, Notes, etc.) |
| 📝 **Auto-Rename** | Generates clean, descriptive filenames with underscores |
| 📂 **Auto-Organize** | Moves files into categorized folders automatically |
| 🧠 **Semantic Search** | ChromaDB vector database indexes content for natural language search |
| ↩️ **Undo Support** | Full move history in SQLite — undo last move or view history |
| 📄 **PDF Support** | Reads PDF text via PyMuPDF for both LLM analysis and indexing |
| 🔒 **100% Local** | Ollama runs locally — zero cloud, zero API keys, zero cost |
| ⚙️ **Configurable** | `.env` file controls everything — models, paths, features |

---

## 🏗️ Architecture

```
    📁 Watch Directory
         ↓
    Watchdog Monitor (main.py)
         ↓  file detected
    Agent Core (agent_core.py)
         ↓  reads preview → prompts LLM
    Ollama LLM (llama3.2)
         ↓  CATEGORY / NEW_FILENAME / FOLDER
    File Operations (agent_tools.py)
         ├─ Move & rename file
         ├─ Log to SQLite history (database.py)
         └─ Index in ChromaDB (memory.py)
              ↓
    📂 Archive Directory
         └─ Invoices/
         └─ Resumes/
         └─ Code/
         └─ ...organized!
```

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.11+**
- **Ollama** — [Download here](https://ollama.com/download)
- **8GB+ RAM** (recommended for local LLMs)

### 1. Clone & Install

```bash
git clone https://github.com/devejya56/aura-local-file-agent.git
cd aura-local-file-agent

python -m venv venv
# Linux/Mac: source venv/bin/activate
# Windows:   venv\Scripts\activate

pip install -r requirements.txt
```

### 2. Setup Ollama

```bash
# Install and pull the model
ollama pull llama3.2
```

### 3. Configure (Optional)

```bash
cp .env.example .env
# Edit .env to customize paths, model, features
```

### 4. Run

```bash
# Terminal 1: Ensure Ollama is running
ollama serve

# Terminal 2: Start Aura
python main.py
```

You'll see:
```
     █████╗ ██╗   ██╗██████╗  █████╗
    ██╔══██╗██║   ██║██╔══██╗██╔══██╗
    ███████║██║   ██║██████╔╝███████║
    ██╔══██║██║   ██║██╔══██╗██╔══██║
    ██║  ██║╚██████╔╝██║  ██║██║  ██║
    ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝

    🧠  Local AI File Organization Agent
    ─────────────────────────────────────

    📂 Watching: /path/to/watch_dir
    📁 Archive:  /path/to/archive
    🤖 Model:    llama3.2

    Drop files into the watch folder to organize them!
    Press Ctrl+C to stop.
```

### 5. Test It

```bash
# Drop a test file into the watch directory
echo "Invoice for AWS Cloud hosting - March 2026, $450.00" > watch_dir/test.txt
```

Watch Aura automatically:
1. Detect the file
2. Read its contents
3. Query the LLM → Category: Invoice, Filename: `aws_cloud_invoice_march_2026.txt`
4. Move it to `archive/Invoices/`
5. Index it for semantic search

---

## 🔧 CLI Commands

```bash
python main.py                 # Start the file watcher
python main.py --undo          # Undo the last file move
python main.py --history       # Show recent move history
python main.py --search        # Semantic search across files
python undo.py                 # Undo last move (standalone)
python undo.py --history       # Show history (standalone)
python undo.py --all 5         # Undo last 5 moves
```

---

## ⚙️ Configuration

All settings are controlled via environment variables (or `.env` file):

| Variable | Default | Description |
|---|---|---|
| `AURA_WATCH_DIRECTORY` | `./watch_dir` | Directory to monitor |
| `AURA_ARCHIVE_DIRECTORY` | `./archive` | Where organized files go |
| `AURA_DB_PATH` | `./aura_db` | ChromaDB storage path |
| `AURA_OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server URL |
| `AURA_LLM_MODEL` | `llama3.2` | LLM model name |
| `AURA_LLM_TEMPERATURE` | `0.0` | LLM creativity (0 = deterministic) |
| `AURA_ENABLE_VECTOR_SEARCH` | `true` | Enable/disable ChromaDB indexing |
| `AURA_ENABLE_BACKUP` | `true` | Backup files before overwriting |
| `AURA_LOG_LEVEL` | `INFO` | Logging verbosity |

See [`.env.example`](./.env.example) for the full list.

---

## 📁 Project Structure

```
aura-local-file-agent/
├── main.py              # Entry point — CLI + file watcher
├── config.py            # Configuration management (pydantic-settings)
├── agent_core.py        # LLM brain — file analysis & decision making
├── agent_tools.py       # File operations — move, rename, create folders
├── memory.py            # ChromaDB vector database — indexing & search
├── database.py          # SQLite move history — undo support
├── undo.py              # Undo operations — CLI + API
├── utils.py             # Utility functions — hashing, sanitization
├── requirements.txt     # Python dependencies
├── .env.example         # Example configuration
├── LICENSE              # MIT License
└── README.md            # This file
```

---

## 🛠️ Tech Stack

| Component | Technology |
|---|---|
| **Language** | Python 3.11+ |
| **LLM Runtime** | Ollama (llama3.2) |
| **LLM Framework** | LangChain |
| **Vector Database** | ChromaDB |
| **File Monitoring** | Watchdog |
| **PDF Parsing** | PyMuPDF (fitz) |
| **Configuration** | Pydantic Settings |
| **Logging** | Loguru |
| **History DB** | SQLite3 |

---

## 📄 License

MIT License — see [LICENSE](./LICENSE) for details.

Built by [Devejya Pandey](https://github.com/devejya56) 🚀
