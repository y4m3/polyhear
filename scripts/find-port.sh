#!/bin/bash
# Find an available port starting from the given base port
# WSL2 compatible: uses 'ss' (preferred) or 'lsof' (fallback)

set -e

BASE_PORT=${1:-8000}
MAX_TRIES=100

# Check if we have tools to detect port usage
if ! command -v ss &> /dev/null && ! command -v lsof &> /dev/null; then
    echo "WARNING: Neither 'ss' nor 'lsof' available. Cannot detect port usage." >&2
    echo "Installing iproute2 (for ss) is recommended: sudo apt install iproute2" >&2
    # Return base port and hope for the best
    echo $BASE_PORT
    exit 0
fi

check_port_in_use() {
    local port=$1
    # Try 'ss' first (more reliable on WSL2)
    if command -v ss &> /dev/null; then
        ss -tuln 2>/dev/null | grep -q ":$port " && return 0
    fi
    # Fallback to 'lsof'
    if command -v lsof &> /dev/null; then
        lsof -i:$port >/dev/null 2>&1 && return 0
    fi
    return 1
}

for i in $(seq 0 $MAX_TRIES); do
    PORT=$((BASE_PORT + i))
    if ! check_port_in_use $PORT; then
        echo $PORT
        exit 0
    fi
done

echo "No available port found in range $BASE_PORT-$((BASE_PORT + MAX_TRIES))" >&2
exit 1
