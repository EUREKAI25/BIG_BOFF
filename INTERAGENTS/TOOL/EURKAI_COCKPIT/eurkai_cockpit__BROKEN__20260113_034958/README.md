# EURKAI_COCKPIT

> Local-first cockpit for AI orchestration — Manage projects, briefs, runs, secrets, and modules.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 🚀 Quick Start (One Command)

```bash
bash scripts/install_all.sh
```

That's it! This command:
- ✅ Verifies Python >= 3.11
- ✅ Creates `~/.eurkai_cockpit/`
- ✅ Installs dependencies
- ✅ Initializes database
- ✅ Runs all tests
- ✅ Generates validation report

**Custom location:**
```bash
bash scripts/install_all.sh --target /opt/eurkai
```

---

## 📖 What is EURKAI_COCKPIT?

EURKAI_COCKPIT is a **local-first** management system for AI agent orchestration:

| Feature | Description |
|---------|-------------|
| **Projects** | Organize work into projects |
| **Briefs** | Define prompts and policies for AI agents |
| **Runs** | Track execution history and logs |
| **Secrets** | Encrypted credential storage with gated access |
| **Modules** | Registry for reusable AI components |
| **Backup** | Automated backup to Git |

---

## 🛠️ Usage

### Start API Server

```bash
cd ~/.eurkai_cockpit
python -m uvicorn backend.app:app --host 127.0.0.1 --port 8000
```

**Endpoints:**
- http://127.0.0.1:8000 — Root
- http://127.0.0.1:8000/docs — Swagger UI
- http://127.0.0.1:8000/health — Health check

### Use CLI

```bash
# Initialize
python -m cli.cli init

# Projects
python -m cli.cli project list
python -m cli.cli project create "My Project"
python -m cli.cli project get <id>

# Briefs
python -m cli.cli brief list --project <id>
python -m cli.cli brief create --project <id> --title "My Brief" --prompt "Do X"

# Runs
python -m cli.cli run list --brief <id>
python -m cli.cli run trigger <brief_id>

# Config
python -m cli.cli config list
python -m cli.cli config set key value

# Help
python -m cli.cli --help
```

### Backup

```bash
# Dry run (local only)
python -m backend.backup.backup --dry-run

# Full backup (requires Git)
python -m backend.backup.backup
```

---

## 🔐 Secrets Management

Secrets are **encrypted at rest** and require a master password to access.

```bash
# Set master password (required)
export EURKAI_MASTER_PASSWORD="your-secure-password"

# Create secret (via API)
curl -X POST http://localhost:8000/api/secrets \
  -H "Content-Type: application/json" \
  -d '{"key": "API_KEY", "value": "secret123"}'

# List secrets (values hidden)
curl http://localhost:8000/api/secrets

# Unlock session
curl -X POST http://localhost:8000/api/secrets/unlock \
  -H "Content-Type: application/json" \
  -d '{"master_password": "your-secure-password"}'
# Returns: {"session_token": "..."}

# Copy secret (with session token)
curl http://localhost:8000/api/secrets/<id>/copy \
  -H "X-Session-Token: <token>"
```

---

## 📁 Directory Structure

```
~/.eurkai_cockpit/
├── backend/               # API server
│   ├── api/               # FastAPI routes
│   ├── backup/            # Backup module
│   ├── secrets/           # Encryption & gating
│   └── storage/           # SQLite CRUD
├── cli/                   # CLI interface
├── data/                  # Database & runtime
│   └── cockpit.db         # SQLite database
├── docs/                  # Documentation
├── logs/                  # Logs & reports
├── scripts/               # Installation scripts
│   └── install_all.sh     # One-shot installer
├── tests/                 # Test suite
├── requirements.txt       # Python dependencies
└── README.md              # This file
```

---

## ⚙️ Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `EURKAI_DB_PATH` | Database path | `~/.eurkai_cockpit/data/cockpit.db` |
| `EURKAI_MASTER_PASSWORD` | Secrets encryption key | None (required for secrets) |
| `EURKAI_TOKEN` | API auth token | None (auth disabled) |
| `EURKAI_BACKUP_DIR` | Backup directory | `~/.eurkai_cockpit/backups` |

### Example Setup

```bash
# Add to ~/.bashrc or ~/.zshrc
export EURKAI_DB_PATH="$HOME/.eurkai_cockpit/data/cockpit.db"
export EURKAI_MASTER_PASSWORD="my-secure-password"
```

---

## 🧪 Testing

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test
python -m pytest tests/test_e2e_smoke.py -v

# With coverage
python -m pytest tests/ --cov=backend --cov-report=html
```

---

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [INSTALL.md](docs/INSTALL.md) | Installation guide |
| [API.md](docs/API.md) | API reference |
| [CLI.md](docs/CLI.md) | CLI reference |
| [STORAGE.md](docs/STORAGE.md) | Database schema |
| [SECRETS.md](docs/SECRETS.md) | Secrets management |
| [BACKUP.md](docs/BACKUP.md) | Backup procedures |

---

## 🔄 API Reference (Quick)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/projects` | List projects |
| POST | `/api/projects` | Create project |
| GET | `/api/projects/{id}` | Get project |
| PUT | `/api/projects/{id}` | Update project |
| DELETE | `/api/projects/{id}` | Delete project |
| GET | `/api/briefs` | List briefs |
| POST | `/api/briefs` | Create brief |
| POST | `/api/briefs/{id}/run` | Trigger run |
| GET | `/api/runs/{id}` | Get run status |
| GET | `/api/secrets` | List secrets (no values) |
| POST | `/api/secrets/unlock` | Get session token |
| GET | `/api/secrets/{id}/copy` | Reveal secret value |
| GET | `/api/modules` | List modules |
| POST | `/api/backups` | Trigger backup |

Full API docs: http://localhost:8000/docs

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        CLI / UI                              │
├─────────────────────────────────────────────────────────────┤
│                     FastAPI Backend                          │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐           │
│  │ Projects│ │ Briefs  │ │  Runs   │ │ Secrets │           │
│  └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘           │
│       │           │           │           │                  │
│  ┌────┴───────────┴───────────┴───────────┴────┐           │
│  │              Storage Layer                   │           │
│  │           (SQLite + JSON)                    │           │
│  └──────────────────────────────────────────────┘           │
├─────────────────────────────────────────────────────────────┤
│                    Backup Module                             │
│              (SQLite + JSON + Git)                          │
└─────────────────────────────────────────────────────────────┘
```

---

## 📋 Chantiers (Development History)

| Chantier | Description | Status |
|----------|-------------|--------|
| C01 | Specification & contracts | ✅ Done |
| C02 | Storage layer (SQLite) | ✅ Done |
| C03 | API backend (FastAPI) | ✅ Done |
| C04 | Frontend UI (optional) | ⏳ Optional |
| C05 | CLI interface | ✅ Done |
| C06 | Secrets (encrypted + gated) | ✅ Done |
| C07 | Backup (Git integration) | ✅ Done |
| C08 | Install & validation | ✅ Done |

---

## 🤝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing`
3. Run tests: `python -m pytest`
4. Commit: `git commit -m 'Add amazing feature'`
5. Push: `git push origin feature/amazing`
6. Open Pull Request

---

## 📄 License

MIT License — See [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgments

Built with:
- [FastAPI](https://fastapi.tiangolo.com/) — Modern Python web framework
- [Click](https://click.palletsprojects.com/) — CLI toolkit
- [Pydantic](https://pydantic.dev/) — Data validation
- [SQLite](https://sqlite.org/) — Embedded database

---

*EURKAI_COCKPIT — Your local AI orchestration cockpit*
