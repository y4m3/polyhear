# Getting Started

## Prerequisites

- Docker & Docker Compose (recommended)
- Or: Python 3.11+, Node.js 20+, uv

## Docker Setup

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/polyhear.git
cd polyhear
```

### 2. Configure Project Directory

```bash
# Create config directories
mkdir -p ~/.config/polyhear
mkdir -p ~/.local/share/polyhear

# Create project configuration
cat > ~/.config/polyhear/local.toml << 'EOF'
# Register projects to monitor
# Use host-side paths (automatically converted to container paths)

[[projects]]
name = "my-project"
path = "/home/dev/repos/my-project"  # Absolute path

[[projects]]
name = "dotfiles"
path = "~/dotfiles"  # Tilde expansion supported
EOF
```

### 3. Environment Variables (Optional)

```bash
cat > .env << 'EOF'
# Root directory for monitored repositories (host side)
POLYHEAR_REPOS_ROOT=$HOME/dev

# Path conversion for Docker
POLYHEAR_HOST_ROOT=$HOME/dev
POLYHEAR_HOST_HOME=$HOME

# Port
POLYHEAR_PORT=8000

# LLM API keys (Phase 2)
# ANTHROPIC_API_KEY=your-api-key
# OPENAI_API_KEY=your-api-key
EOF
```

### 4. Start

```bash
# Production mode
make up

# View logs
make logs

# Stop
make down
```

### 5. Access

Open http://localhost:8000 in your browser.

## Local Development

### Backend

```bash
cd backend

# Install uv (if not installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync

# Start dev server
uv run uvicorn polyhear.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Start dev server
npm run dev
```

Development URLs:
- Backend: http://localhost:8000
- Frontend: http://localhost:5173 (proxies API to backend)

## Configuration

### local.toml Example

```toml
# Project registration
# Use host-side paths (auto-converted in Docker)

[[projects]]
name = "frontend-app"
path = "/home/dev/repos/frontend-app"
group = "client-a"              # Optional grouping
build_log = ".build.log"        # Custom build log path
test_log = "coverage/test-results.json"

[[projects]]
name = "dotfiles"
path = "~/.local/share/chezmoi"

[[projects]]
name = "backend-api"
path = "/home/dev/repos/backend-api"
group = "client-a"

# Worktree example
[[projects]]
name = "frontend-feature"
path = "/home/dev/repos/frontend-feature"
parent = "frontend-app"         # Specify parent project

# LLM settings (Phase 2)
[llm]
provider = "anthropic"          # "anthropic" | "openai" | "ollama"
```

### Path Specification

In Docker, the following path formats are supported:

1. **Absolute paths (recommended)**: `/home/dev/repos/my-project`
   - Host-side absolute paths
   - Automatically converted to container mount points

2. **Tilde expansion**: `~/.local/share/chezmoi`
   - For paths under home directory
   - `~` expands to home directory

**Note**: Relative paths are not supported. Always use absolute paths or tilde notation.

### config.toml Example (User Customization)

```toml
[ui]
refresh_interval = 60  # Auto-refresh interval (seconds)
max_commits = 10       # Number of commits to display

[summary]
todo_patterns = ["TODO", "FIXME", "HACK", "XXX"]  # Search patterns
```

## Troubleshooting

### Docker Volume Mount Error

```
Error: Cannot access repository
```

Verify `POLYHEAR_REPOS_ROOT` is set correctly:

```bash
# Check environment variable
echo $POLYHEAR_REPOS_ROOT

# Verify mounts in docker-compose.yml
docker compose config | grep volumes -A 10
```

### Git Information Error

```
Error: Not a Git repository
```

Verify the path is a valid Git repository:

```bash
ls -la /path/to/project/.git
```

### Database Error

```bash
# Reset database
make db-reset
```

## Development

### Running Tests

```bash
# All tests
make test

# Backend only
make test-backend

# Frontend only
make test-frontend
```

### Linting and Formatting

```bash
# Lint
make lint

# Format
make format
```
