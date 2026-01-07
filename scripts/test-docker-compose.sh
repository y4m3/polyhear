#!/usr/bin/env bash
# Test docker-compose.yml configuration for worktree isolation support
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

echo "Testing docker-compose.yml configuration..."
echo ""

# Test 1: Validate docker-compose.yml syntax
echo "Test 1: Validating docker-compose.yml syntax..."
if docker compose config --quiet 2>/dev/null; then
    echo "  ✓ Syntax is valid"
else
    echo "  ✗ Syntax validation failed"
    exit 1
fi

# Test 2: Check name directive exists
echo "Test 2: Checking name directive..."
if grep -q "^name:" docker-compose.yml; then
    echo "  ✓ name directive found"
else
    echo "  ✗ name directive not found"
    exit 1
fi

# Test 3: Check COMPOSE_PROJECT_NAME variable is used
echo "Test 3: Checking COMPOSE_PROJECT_NAME variable..."
if grep -q 'COMPOSE_PROJECT_NAME' docker-compose.yml; then
    echo "  ✓ COMPOSE_PROJECT_NAME variable used"
else
    echo "  ✗ COMPOSE_PROJECT_NAME variable not found"
    exit 1
fi

# Test 4: Check dev-backend port is parameterized
echo "Test 4: Checking dev-backend port parameterization..."
if grep -A 10 "dev-backend:" docker-compose.yml | grep -q 'POLYHEAR_PORT'; then
    echo "  ✓ dev-backend uses POLYHEAR_PORT"
else
    echo "  ✗ dev-backend port not parameterized with POLYHEAR_PORT"
    exit 1
fi

# Test 5: Check dev-frontend port is parameterized
echo "Test 5: Checking dev-frontend port parameterization..."
if grep -A 10 "dev-frontend:" docker-compose.yml | grep -q 'VITE_PORT'; then
    echo "  ✓ dev-frontend uses VITE_PORT"
else
    echo "  ✗ dev-frontend port not parameterized with VITE_PORT"
    exit 1
fi

# Test 6: Check VITE_API_URL environment variable
echo "Test 6: Checking VITE_API_URL environment variable..."
if grep -A 20 "dev-frontend:" docker-compose.yml | grep -q 'VITE_API_URL'; then
    echo "  ✓ VITE_API_URL environment variable found"
else
    echo "  ✗ VITE_API_URL environment variable not found"
    exit 1
fi

# Test 7: Verify config with custom environment variables
echo "Test 7: Testing with custom environment variables..."
export COMPOSE_PROJECT_NAME="test-worktree"
export POLYHEAR_PORT="9000"
export VITE_PORT="9173"
# Use --profile dev to include dev-backend and dev-frontend services
CONFIG_OUTPUT=$(docker compose --profile dev config 2>/dev/null)

if echo "$CONFIG_OUTPUT" | grep -q "name: test-worktree"; then
    echo "  ✓ COMPOSE_PROJECT_NAME substitution works"
else
    echo "  ✗ COMPOSE_PROJECT_NAME substitution failed"
    exit 1
fi

# docker compose config outputs "published: 9000" format
if echo "$CONFIG_OUTPUT" | grep -qE '(9000:8000|published: "9000")'; then
    echo "  ✓ POLYHEAR_PORT substitution works"
else
    echo "  ✗ POLYHEAR_PORT substitution failed"
    exit 1
fi

if echo "$CONFIG_OUTPUT" | grep -qE '(9173:5173|published: "9173")'; then
    echo "  ✓ VITE_PORT substitution works"
else
    echo "  ✗ VITE_PORT substitution failed"
    exit 1
fi

echo ""
echo "All tests passed! ✓"
