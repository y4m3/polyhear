# Development Guide

## Prerequisites

- [Just](https://github.com/casey/just) - Command runner
- Python 3.11+ with [uv](https://github.com/astral-sh/uv)
- Node.js 20+ with npm
- Docker & Docker Compose (optional)

### Install Just

```bash
# Ubuntu/Debian
sudo apt install just

# macOS
brew install just

# Or via cargo
cargo install just
```

## Quick Start (Single Worktree)

```bash
just setup-worktree      # Auto-detects and assigns ports
just dev-local-backend   # Terminal 1
just dev-local-frontend  # Terminal 2
# Open the URL shown during setup
```

## Multiple Worktrees (Claude Code Workflow)

Claude Code will automatically handle port assignment:

### 1. Create Worktree

```bash
git worktree add ../polyhear-worktree/feature-foo -b feature/foo
cd ../polyhear-worktree/feature-foo
```

### 2. Setup (Automatic Port Detection)

```bash
just setup-worktree
# Output:
# Detecting available ports...
# Ports auto-assigned:
#   Backend:  http://localhost:8001
#   Frontend: http://localhost:5174
```

**No manual editing required!** Ports are automatically detected and saved.

### 3. Run Development Servers

```bash
just dev-local-backend   # Terminal 1
just dev-local-frontend  # Terminal 2
```

## Re-assigning Ports

If ports become unavailable, regenerate:

```bash
rm .env.local
just setup-worktree
```

## Viewing Current Port Assignment

```bash
cat .env.local
```

## Available Commands

```bash
just --list  # Show all available commands
```

### Common Commands

| Command | Description |
|---------|-------------|
| `just setup-worktree` | Setup with auto port detection |
| `just dev-local-backend` | Start backend dev server (local) |
| `just dev-local-frontend` | Start frontend dev server (local) |
| `just dev` | Start both servers in Docker |
| `just test` | Run all tests |
| `just lint` | Run linters |
| `just format` | Format code |

## Docker Development

```bash
# Setup (same as local)
just setup-worktree

# Start with Docker
just dev

# Check running containers
docker ps

# Stop containers (only this worktree)
just down
```

## Troubleshooting

### Port already in use

```bash
# Regenerate port assignment
rm .env.local
just setup-worktree
```

### Missing tools

Check that required tools are installed:
- `just --version`
- `uv --version`
- `node --version`
- `npm --version`
