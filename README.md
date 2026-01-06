# polyhear

**Situational awareness for parallel development** - Git Multi-Project Dashboard

![License](https://img.shields.io/badge/license-MIT-blue.svg)

A dashboard tool for tracking progress across multiple Git projects and branches. Ideal for parallel development workflows using AI coding assistants like Claude Code.

## Features

### MVP

- **Project Registration**: Register and manage Git repositories to monitor
- **Status Overview**: View git status for all projects at a glance
- **Recent Commits**: Display latest commit logs per project
- **Change Summary**: Show uncommitted changes count and file list
- **Branch Info**: Current branch name and remote sync status (ahead/behind)
- **Worktree Support**: Recognize and display git worktree directories
- **Progress Summary**: Natural language summary from commits and diffs
- **Failure Detection**: Detect and display build errors and test failures

### Phase 2 (Planned)

- LLM-powered high-quality summaries
- Build/test execution from dashboard
- Real-time updates via WebSocket
- AI chat integration

## Quick Start

### Prerequisites

- Docker & Docker Compose

### Setup

```bash
# Clone
git clone https://github.com/yourusername/polyhear.git
cd polyhear

# Start
make up

# Open http://localhost:8000
```

### Development

```bash
# Start both backend and frontend dev servers
make dev

# Or run separately
make dev-backend   # Backend (http://localhost:8000)
make dev-frontend  # Frontend (http://localhost:5173)
```

### Local Development (Without Docker)

```bash
# Backend
cd backend
uv sync
uv run uvicorn polyhear.main:app --reload

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

## Configuration

Configuration files are loaded in order of priority:

1. Environment variables (highest)
2. `~/.config/polyhear/local.toml` (environment-specific, not in git)
3. `~/.config/polyhear/config.toml` (user customization)
4. `config/default.toml` (defaults)

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `POLYHEAR_REPOS_ROOT` | `$HOME/dev` | Root directory for monitored repositories |
| `POLYHEAR_CONFIG_DIR` | `$HOME/.config/polyhear` | Configuration directory |
| `POLYHEAR_DATA_DIR` | `$HOME/.local/share/polyhear` | Data persistence directory |
| `POLYHEAR_PORT` | `8000` | Dashboard port |

### Project Registration (local.toml)

```toml
[[projects]]
name = "project-alpha"
path = "~/dev/project-alpha"

[[projects]]
name = "project-beta"
path = "~/dev/project-beta"
parent = "project-alpha"  # Worktree parent
build_log = ".build.log"
test_log = ".test-results.json"
```

### Build/Test Log Formats

polyhear reads log files to display build and test status.

**Build Log (text)**
```
STATUS: success
EXIT_CODE: 0
DURATION: 12s
TIMESTAMP: 2024-01-15T10:30:00Z
---
<build output>
```

**Test Log (JSON recommended)**
```json
{
  "status": "failed",
  "passed": 8,
  "failed": 2,
  "skipped": 0,
  "duration_ms": 5432,
  "timestamp": "2024-01-15T10:31:00Z",
  "failures": [
    {"name": "auth.test.ts: token test", "message": "Expected..."}
  ]
}
```

## API

| Endpoint | Description |
|----------|-------------|
| `GET /api/projects` | List all projects |
| `GET /api/projects/:id` | Get project details |
| `POST /api/projects` | Add project |
| `DELETE /api/projects/:id` | Remove project |
| `POST /api/projects/:id/refresh` | Manual refresh |
| `GET /api/settings` | Get settings |
| `GET /api/health` | Health check |

## Tech Stack

- **Backend**: Python 3.11+ / FastAPI / SQLite
- **Frontend**: React 18 / Vite / TailwindCSS
- **Infrastructure**: Docker / Docker Compose

## License

MIT License
