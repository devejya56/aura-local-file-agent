# 🧠 Aura — Local AI File Organization Agent

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/downloads/)
[![Status: Active](https://img.shields.io/badge/Status-Active-brightgreen?style=for-the-badge)]()
[![PRs Welcome](https://img.shields.io/badge/PRs-Welcome-brightgreen?style=for-the-badge)](https://github.com/devejya56/aura-local-file-agent/pulls)

**Zero cloud. Zero cost. 100% private.** 🔒

Drop a file → AI reads it → auto-categorized, renamed, and organized.

[Features](#-features) • [Quick Start](#-quick-start) • [Architecture](#%EF%B8%8F-architecture) • [Configuration](#%EF%B8%8F-configuration) • [License](#-license)

</div>

---

## 📋 Overview

Aura is a **local-first autonomous agent** that watches your file system, analyzes file contents using a **local LLM** (via [Ollama](https://ollama.com/)), intelligently categorizes and renames files, organizes them into folders, and indexes everything in a **vector database** for instant semantic search.

**No data ever leaves your machine.** No API keys. No subscriptions. No cloud services.

### ⚡ Why Aura?

| Feature | Aura | Cloud Services |
|---------|------|----------------|
| **Privacy** | 100% Local ✅ | Uploaded to servers ❌ |
| **Cost** | Free ✅ | $$ per month ❌ |
| **Speed** | Instant ✅ | Network dependent ❌ |
| **Data Control** | Full ownership ✅ | Company-dependent ❌ |

---

## ✨ Features

<table>
<tr>
<td>🔍 <b>Smart Categorization</b></td>
<td>LLM reads file content and assigns categories (Invoice, Resume, Code, Notes, etc.)</td>
</tr>
<tr>
<td>📝 <b>Auto-Rename</b></td>
<td>Generates clean, descriptive filenames with underscores</td>
</tr>
<tr>
<td>📂 <b>Auto-Organize</b></td>
<td>Moves files into categorized folders automatically</td>
</tr>
<tr>
<td>🧠 <b>Semantic Search</b></td>
<td>ChromaDB vector database indexes content for natural language search</td>
</tr>
<tr>
<td>↩️ <b>Undo Support</b></td>
<td>Full move history in SQLite — undo last move or view history</td>
</tr>
<tr>
<td>📄 <b>PDF Support</b></td>
<td>Reads PDF text via PyMuPDF for both LLM analysis and indexing</td>
</tr>
<tr>
<td>🔒 <b>100% Local</b></td>
<td>Ollama runs locally — zero cloud, zero API keys, zero cost</td>
</tr>
<tr>
<td>⚙️ <b>Configurable</b></td>
<td>.env file controls everything — models, paths, features</td>
</tr>
</table>

---

## 🏗️ Architecture

```
📁 Watch Directory
    ↓
🔍 Watchdog Monitor (main.py)
    ├─ Detects file changes
    ↓
🧠 Agent Core (agent_core.py)
    ├─ Reads preview
    ├─ Prepares prompts
    ↓
🤖 Ollama LLM (llama3.2)
    ├─ Analyzes content
    ├─ Returns: CATEGORY / NEW_FILENAME / FOLDER
    ↓
⚙️ File Operations (agent_tools.py)
    ├─ Move & rename file
    ├─ Create folders
    ├─ Log to SQLite history (database.py)
    ├─ Index in ChromaDB (memory.py)
    ↓
📂 Archive Directory
    ├─ Invoices/
    ├─ Resumes/
    ├─ Code/
    └─ ...organized!
```

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.11+**
- **Ollama** — [Download here](https://ollama.com/download)
- **8GB+ RAM** (recommended for local LLMs)

### 1️⃣ Clone & Install

```bash
git clone https://github.com/devejya56/aura-local-file-agent.git
cd aura-local-file-agent

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Linux/Mac:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2️⃣ Setup Ollama

```bash
# Install and pull the model
ollama pull llama3.2
```

### 3️⃣ Configure (Optional)

```bash
cp .env.example .env
# Edit .env to customize paths, model, features
```

### 4️⃣ Run

```bash
# Terminal 1: Start Ollama
ollama serve

# Terminal 2: Start Aura
python main.py
```

You'll see:

```
█████╗ ██╗ ██╗██████╗ █████╗
██╔══██╗██║ ██║██╔══██╗██╔══██╗
███████║██║ ██║██████╔╝███████║
██╔══██║██║ ██║██╔══██╗██╔══██║
██║ ██║╚██████╔╝██║ ██║██║ ██║
╚═╝ ╚═╝ ╚═════╝ ╚═╝ ╚═╝╚═╝ ╚═╝

🧠 Local AI File Organization Agent
───────────────────────────────────
📂 Watching: /path/to/watch_dir
📁 Archive: /path/to/archive
🤖 Model: llama3.2
✅ Vector Search: Enabled

Drop files into the watch folder to organize them!
Press Ctrl+C to stop.
```

### 5️⃣ Test It

```bash
# Drop a test file into the watch directory
echo "Invoice for AWS Cloud hosting - March 2026, $450.00" > watch_dir/test.txt
```

Watch Aura automatically:

1. ✅ Detect the file
2. ✅ Read its contents
3. ✅ Query the LLM → Category: `Invoice`, Filename: `aws_cloud_invoice_march_2026.txt`
4. ✅ Move it to `archive/Invoices/`
5. ✅ Index it for semantic search

---

## 🔧 CLI Commands

| Command | Description |
|---------|-------------|
| `python main.py` | Start the file watcher |
| `python main.py --undo` | Undo the last file move |
| `python main.py --history` | Show recent move history |
| `python main.py --search` | Semantic search across files |
| `python undo.py` | Undo last move (standalone) |
| `python undo.py --history` | Show history (standalone) |
| `python undo.py --all 5` | Undo last 5 moves |

---

## ⚙️ Configuration

All settings are controlled via environment variables (or `.env` file):

| Variable | Default | Description |
|----------|---------|-------------|
| `AURA_WATCH_DIRECTORY` | `./watch_dir` | Directory to monitor |
| `AURA_ARCHIVE_DIRECTORY` | `./archive` | Where organized files go |
| `AURA_DB_PATH` | `./aura_db` | ChromaDB storage path |
| `AURA_OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server URL |
| `AURA_LLM_MODEL` | `llama3.2` | LLM model name |
| `AURA_LLM_TEMPERATURE` | `0.0` | LLM creativity (0 = deterministic) |
| `AURA_ENABLE_VECTOR_SEARCH` | `true` | Enable/disable ChromaDB indexing |
| `AURA_ENABLE_BACKUP` | `true` | Backup files before overwriting |
| `AURA_LOG_LEVEL` | `INFO` | Logging verbosity |

See [`.env.example`](https://github.com/devejya56/aura-local-file-agent/blob/main/.env.example) for the full list.

---

## 📁 Project Structure

```
aura-local-file-agent/
├── main.py                    # Entry point — CLI + file watcher
├── config.py                  # Configuration management (pydantic-settings)
├── agent_core.py              # LLM brain — file analysis & decision making
├── agent_tools.py             # File operations — move, rename, create folders
├── memory.py                  # ChromaDB vector database — indexing & search
├── database.py                # SQLite move history — undo support
├── undo.py                    # Undo operations — CLI + API
├── utils.py                   # Utility functions — hashing, sanitization
├── ocr.py                     # OCR processing for images
├── watch_dir/                 # Watch directory (configure in .env)
├── archive/                   # Organized files output
├── aura_db/                   # ChromaDB vector database
├── templates/                 # Web UI templates
├── static/                    # CSS & JavaScript assets
├── requirements.txt           # Python dependencies
├── .env.example               # Example configuration
├── LICENSE                    # MIT License
└── README.md                  # This file
```

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|------------|
| **Language** | Python 3.11+ |
| **LLM Runtime** | Ollama (llama3.2) |
| **LLM Framework** | LangChain |
| **Vector Database** | ChromaDB |
| **File Monitoring** | Watchdog |
| **PDF Parsing** | PyMuPDF (fitz) |
| **Configuration** | Pydantic Settings |
| **Logging** | Loguru |
| **History DB** | SQLite3 |
| **Web Framework** | Flask (optional) |

---

## 📚 Documentation

- [**SETUP.md**](./SETUP.md) — Detailed installation & configuration guide
- [**BUILD_LOCALLY.md**](./BUILD_LOCALLY.md) — Local build instructions
- [**COMPLETE_IMPLEMENTATION.md**](./COMPLETE_IMPLEMENTATION.md) — Full implementation details

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 License

MIT License — see [LICENSE](./LICENSE) for details.

---

## 👨‍💻 Author

Built by **[Devejya Pandey](https://github.com/devejya56)** 🚀

---

## ⭐ Show Your Support

If you find Aura helpful, please consider:

- ⭐ Starring this repository
- 🐛 Reporting issues
- 💡 Suggesting features
- 🤝 Contributing code

---

<div align="center">

Made with ❤️ for the privacy-conscious developer

[Back to top](#-aura--local-ai-file-organization-agent)

</div>
