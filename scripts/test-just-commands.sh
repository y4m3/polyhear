#!/usr/bin/env bash
# Smoke test for just commands
# Tests all just commands to verify development environment is working
# Note: We don't use 'set -e' because test functions handle failures internally
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

# === Configuration ===
MODE="quick"
SKIP_DOCKER=0
VERBOSE=0
JSON_OUTPUT=0
SINGLE_CMD=""

# === Global State ===
PASSED=0
FAILED=0
SKIPPED=0
CLEANUP_PIDS=()
declare -a RESULTS=()

# === Environment Detection Results ===
HAS_DOCKER=0
HAS_ENV_LOCAL=0
HAS_BACKEND_VENV=0
HAS_NODE_MODULES=0
POLYHEAR_PORT="${POLYHEAR_PORT:-8000}"
VITE_PORT="${VITE_PORT:-5173}"

# === Color Output (NO_COLOR support) ===
if [[ -z "${NO_COLOR:-}" && -t 1 ]]; then
    GREEN='\033[0;32m'
    RED='\033[0;31m'
    YELLOW='\033[0;33m'
    BLUE='\033[0;34m'
    BOLD='\033[1m'
    NC='\033[0m'
else
    GREEN='' RED='' YELLOW='' BLUE='' BOLD='' NC=''
fi

# === Usage ===
usage() {
    cat <<EOF
Usage: $(basename "$0") [OPTIONS]

Smoke test for just commands. Verifies development environment is working.

Modes:
  --quick       Quick mode (default) - non-destructive tests only
  --full        Full mode - clean state, ordered test sequence
  --single CMD  Test a single command

Options:
  --no-docker   Skip Docker-related tests
  --verbose     Show command output on failure
  --json        Output results as JSON
  --help        Show this help

Examples:
  $(basename "$0")                        # Quick mode
  $(basename "$0") --full                 # Full test sequence
  $(basename "$0") --single lint-backend  # Test one command
  $(basename "$0") --no-docker            # Skip Docker tests
EOF
    exit 0
}

# === Argument Parsing ===
parse_args() {
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --quick)
                MODE="quick"
                shift
                ;;
            --full)
                MODE="full"
                shift
                ;;
            --single)
                MODE="single"
                SINGLE_CMD="${2:-}"
                if [[ -z "$SINGLE_CMD" ]]; then
                    echo "ERROR: --single requires a command name"
                    exit 1
                fi
                shift 2
                ;;
            --no-docker)
                SKIP_DOCKER=1
                shift
                ;;
            --verbose)
                VERBOSE=1
                shift
                ;;
            --json)
                JSON_OUTPUT=1
                shift
                ;;
            --help|-h)
                usage
                ;;
            *)
                echo "Unknown option: $1"
                usage
                ;;
        esac
    done
}

# === Cleanup ===
cleanup() {
    if [[ $JSON_OUTPUT -eq 0 ]]; then
        echo ""
        echo "Cleaning up..."
    fi

    # Kill background processes
    for pid in "${CLEANUP_PIDS[@]:-}"; do
        kill "$pid" 2>/dev/null || true
    done

    # Stop Docker containers
    just down 2>/dev/null || true
}
trap cleanup EXIT INT TERM

# === Environment Detection ===
detect_environment() {
    # Check Docker
    if command -v docker &>/dev/null && docker info &>/dev/null 2>&1; then
        HAS_DOCKER=1
    fi

    # Check .env.local
    if [[ -f .env.local ]]; then
        HAS_ENV_LOCAL=1
        # Source port values
        source .env.local 2>/dev/null || true
        POLYHEAR_PORT="${POLYHEAR_PORT:-8000}"
        VITE_PORT="${VITE_PORT:-5173}"
    fi

    # Check backend venv
    if [[ -d backend/.venv ]]; then
        HAS_BACKEND_VENV=1
    fi

    # Check node_modules
    if [[ -d frontend/node_modules ]]; then
        HAS_NODE_MODULES=1
    fi

    if [[ $JSON_OUTPUT -eq 0 ]]; then
        echo "Environment:"
        echo "  Docker:        $(bool_to_status $HAS_DOCKER)"
        echo "  .env.local:    $(bool_to_status $HAS_ENV_LOCAL)"
        echo "  backend/.venv: $(bool_to_status $HAS_BACKEND_VENV)"
        echo "  node_modules:  $(bool_to_status $HAS_NODE_MODULES)"
        echo ""
    fi
}

bool_to_status() {
    if [[ $1 -eq 1 ]]; then
        echo -e "${GREEN}OK${NC}"
    else
        echo -e "${YELLOW}NOT FOUND${NC}"
    fi
}

# === Prerequisite Checking ===
check_prereq() {
    local req="$1"
    case "$req" in
        "")
            return 0
            ;;
        "docker")
            [[ $HAS_DOCKER -eq 1 && $SKIP_DOCKER -eq 0 ]]
            ;;
        "env")
            [[ $HAS_ENV_LOCAL -eq 1 ]]
            ;;
        "backend")
            [[ $HAS_BACKEND_VENV -eq 1 ]]
            ;;
        "frontend")
            [[ $HAS_NODE_MODULES -eq 1 ]]
            ;;
        "docker+env")
            [[ $HAS_DOCKER -eq 1 && $HAS_ENV_LOCAL -eq 1 && $SKIP_DOCKER -eq 0 ]]
            ;;
        *)
            return 0
            ;;
    esac
}

# === Port Checking ===
port_in_use() {
    local port="$1"
    if command -v nc &>/dev/null; then
        nc -z localhost "$port" 2>/dev/null
    elif command -v ss &>/dev/null; then
        ss -tuln | grep -q ":$port "
    else
        # Fallback: assume port is free
        return 1
    fi
}

# === JSON Escaping ===
escape_json() {
    local str="$1"
    str="${str//\\/\\\\}"   # backslash
    str="${str//\"/\\\"}"   # double quote
    str="${str//$'\n'/\\n}" # newline
    str="${str//$'\r'/\\r}" # carriage return
    str="${str//$'\t'/\\t}" # tab
    echo "$str"
}

# === Result Recording ===
record_result() {
    local cmd="$1"
    local status="$2"
    local duration="${3:-0}"
    local error="${4:-}"

    # Escape strings for JSON output
    local escaped_cmd escaped_error
    escaped_cmd=$(escape_json "$cmd")
    escaped_error=$(escape_json "$error")

    RESULTS+=("{\"command\":\"$escaped_cmd\",\"status\":\"$status\",\"duration\":$duration,\"error\":\"$escaped_error\"}")

    case "$status" in
        "pass") ((PASSED++)) ;;
        "fail") ((FAILED++)) ;;
        "skip") ((SKIPPED++)) ;;
    esac
}

# === Output Functions ===
print_pass() {
    local cmd="$1"
    local msg="${2:-}"
    if [[ $JSON_OUTPUT -eq 0 ]]; then
        printf "  ${GREEN}✓${NC} %-24s %s\n" "$cmd" "$msg"
    fi
}

print_fail() {
    local cmd="$1"
    local msg="${2:-}"
    if [[ $JSON_OUTPUT -eq 0 ]]; then
        printf "  ${RED}✗${NC} %-24s %s\n" "$cmd" "$msg"
    fi
}

print_skip() {
    local cmd="$1"
    local msg="${2:-}"
    if [[ $JSON_OUTPUT -eq 0 ]]; then
        printf "  ${YELLOW}⊘${NC} %-24s SKIPPED: %s\n" "$cmd" "$msg"
    fi
}

section() {
    local title="$1"
    if [[ $JSON_OUTPUT -eq 0 ]]; then
        echo ""
        echo -e "${BOLD}${BLUE}$title${NC}"
    fi
}

# === Test Functions ===

# Test quick/instant commands
# Always returns 0 - failures are tracked via FAILED counter
test_quick() {
    local cmd="$1"
    local requires="${2:-}"

    # Check prerequisites
    if ! check_prereq "$requires"; then
        print_skip "$cmd" "requires: $requires"
        record_result "$cmd" "skip" 0 "missing prerequisite: $requires"
        return 0
    fi

    local start_time end_time duration
    start_time=$(date +%s.%N)

    local output exit_code
    output=$(just "$cmd" 2>&1) && exit_code=0 || exit_code=$?

    end_time=$(date +%s.%N)
    duration=$(echo "$end_time - $start_time" | bc 2>/dev/null || echo "0")

    if [[ $exit_code -eq 0 ]]; then
        print_pass "$cmd" "$(printf '%.1fs' "$duration")"
        record_result "$cmd" "pass" "$duration"
    else
        print_fail "$cmd" "exit code $exit_code"
        record_result "$cmd" "fail" "$duration" "exit code $exit_code"
        if [[ $VERBOSE -eq 1 ]]; then
            echo "    Output:"
            echo "$output" | head -20 | sed 's/^/    /'
        fi
    fi
    # Always return success - failures tracked via counter
    return 0
}

# Test long-running commands (servers, daemons)
# Always returns 0 - failures are tracked via FAILED counter
test_long_running() {
    local cmd="$1"
    local timeout_sec="${2:-10}"
    local port="${3:-}"
    local requires="${4:-}"

    # Check prerequisites
    if ! check_prereq "$requires"; then
        print_skip "$cmd" "requires: $requires"
        record_result "$cmd" "skip" 0 "missing prerequisite: $requires"
        return 0
    fi

    # Check port availability
    if [[ -n "$port" ]] && port_in_use "$port"; then
        print_fail "$cmd" "port $port already in use"
        record_result "$cmd" "fail" 0 "port $port already in use"
        return 0  # Always return success - failure tracked via counter
    fi

    local tmp_log
    tmp_log=$(mktemp)

    # Start command in background
    just "$cmd" >"$tmp_log" 2>&1 &
    local pid=$!
    CLEANUP_PIDS+=("$pid")

    local elapsed=0
    local start_time
    start_time=$(date +%s)

    while [[ $elapsed -lt $timeout_sec ]]; do
        # Check if process died
        if ! kill -0 "$pid" 2>/dev/null; then
            wait "$pid" 2>/dev/null || true
            local exit_code=$?
            if [[ $exit_code -ne 0 ]]; then
                print_fail "$cmd" "exited with code $exit_code"
                record_result "$cmd" "fail" "$elapsed" "process exited with $exit_code"
                if [[ $VERBOSE -eq 1 ]]; then
                    echo "    Output:"
                    head -20 "$tmp_log" | sed 's/^/    /'
                fi
                rm -f "$tmp_log"
                return 0  # Always return success - failure tracked via counter
            fi
        fi

        # Check port if specified
        if [[ -n "$port" ]] && port_in_use "$port"; then
            kill "$pid" 2>/dev/null || true
            wait "$pid" 2>/dev/null || true
            rm -f "$tmp_log"
            print_pass "$cmd" "port $port listening (${elapsed}s)"
            record_result "$cmd" "pass" "$elapsed"
            return 0
        fi

        sleep 1
        elapsed=$(($(date +%s) - start_time))
    done

    # Timeout reached - command is still running = success for long-running
    kill "$pid" 2>/dev/null || true
    wait "$pid" 2>/dev/null || true
    rm -f "$tmp_log"
    print_pass "$cmd" "running after ${timeout_sec}s"
    record_result "$cmd" "pass" "$timeout_sec"
    return 0
}

# === Mode Implementations ===

run_quick_mode() {
    if [[ $JSON_OUTPUT -eq 0 ]]; then
        echo -e "${BOLD}=== Quick Mode ===${NC}"
    fi

    section "Environment Check"
    test_quick "doctor"

    section "Backend Tests"
    test_quick "lint-backend" "backend"
    test_quick "typecheck-backend" "backend"
    test_quick "test-backend" "backend"
    test_quick "format-backend" "backend"

    section "Frontend Tests"
    test_quick "lint-frontend" "frontend"
    test_quick "typecheck-frontend" "frontend"
    test_quick "test-frontend" "frontend"
    test_quick "format-frontend" "frontend"

    section "Database"
    test_quick "db-migrate" "backend"

    if [[ $SKIP_DOCKER -eq 0 && $HAS_DOCKER -eq 1 ]]; then
        section "Docker Tests"
        test_long_running "dev" 20 "$POLYHEAR_PORT" "docker+env"
        just down 2>/dev/null || true
    fi
}

run_full_mode() {
    if [[ $JSON_OUTPUT -eq 0 ]]; then
        echo -e "${BOLD}=== Full Mode ===${NC}"
    fi

    section "Phase 1: Cleanup"
    just down 2>/dev/null || true
    print_pass "down" "(cleanup)"
    record_result "down" "pass" 0

    section "Phase 2: Setup"
    test_quick "setup-backend"
    test_quick "setup-frontend"
    test_quick "doctor"

    section "Phase 3: Static Analysis"
    test_quick "lint-backend" "backend"
    test_quick "lint-frontend" "frontend"
    test_quick "typecheck-backend" "backend"
    test_quick "typecheck-frontend" "frontend"
    test_quick "test-backend" "backend"
    test_quick "test-frontend" "frontend"
    test_quick "format-backend" "backend"
    test_quick "format-frontend" "frontend"
    test_quick "db-migrate" "backend"

    if [[ $SKIP_DOCKER -eq 0 && $HAS_DOCKER -eq 1 ]]; then
        section "Phase 4: Docker Build & Run"
        test_quick "build" "docker"
        test_long_running "dev" 25 "$POLYHEAR_PORT" "docker+env"
        just down 2>/dev/null || true
        test_long_running "up" 30 "$POLYHEAR_PORT" "docker+env"

        section "Phase 5: Cleanup"
        test_quick "down" "docker"
    fi
}

run_single_mode() {
    local cmd="$SINGLE_CMD"

    if [[ $JSON_OUTPUT -eq 0 ]]; then
        echo -e "${BOLD}=== Testing: $cmd ===${NC}"
        echo ""
    fi

    # Determine command type and test accordingly
    case "$cmd" in
        dev|dev-local-backend|dev-local-frontend|up|logs)
            # Long-running commands
            local port=""
            local timeout=15
            local requires=""
            case "$cmd" in
                dev)
                    port="$POLYHEAR_PORT"
                    timeout=20
                    requires="docker+env"
                    ;;
                dev-local-backend)
                    port="$POLYHEAR_PORT"
                    timeout=10
                    requires="backend"
                    ;;
                dev-local-frontend)
                    port="$VITE_PORT"
                    timeout=10
                    requires="frontend"
                    ;;
                up)
                    port="$POLYHEAR_PORT"
                    timeout=30
                    requires="docker+env"
                    ;;
                logs)
                    timeout=5
                    requires="docker"
                    ;;
            esac
            test_long_running "$cmd" "$timeout" "$port" "$requires"
            ;;
        build)
            test_quick "$cmd" "docker"
            ;;
        lint-backend|typecheck-backend|test-backend|format-backend|db-migrate)
            test_quick "$cmd" "backend"
            ;;
        lint-frontend|typecheck-frontend|test-frontend|format-frontend)
            test_quick "$cmd" "frontend"
            ;;
        setup-backend|setup-frontend|setup|setup-worktree|doctor|default)
            test_quick "$cmd"
            ;;
        down|clean|db-reset)
            # Destructive commands - warn but allow
            if [[ $JSON_OUTPUT -eq 0 ]]; then
                echo -e "${YELLOW}Warning: This is a destructive command${NC}"
            fi
            test_quick "$cmd"
            ;;
        lint|typecheck|test|format|check)
            # Composite commands
            local requires=""
            if [[ $HAS_BACKEND_VENV -eq 1 && $HAS_NODE_MODULES -eq 1 ]]; then
                requires=""
            elif [[ $HAS_BACKEND_VENV -eq 1 ]]; then
                requires="backend"
            elif [[ $HAS_NODE_MODULES -eq 1 ]]; then
                requires="frontend"
            fi
            test_quick "$cmd" "$requires"
            ;;
        *)
            echo "Unknown command: $cmd"
            echo "Run 'just --list' to see available commands"
            exit 1
            ;;
    esac
}

# === Summary Output ===
print_summary() {
    local total=$((PASSED + FAILED + SKIPPED))

    if [[ $JSON_OUTPUT -eq 1 ]]; then
        # JSON output
        local results_json
        results_json=$(printf '%s\n' "${RESULTS[@]}" | paste -sd ',' -)
        cat <<EOF
{
  "timestamp": "$(date -Iseconds)",
  "mode": "$MODE",
  "environment": {
    "docker": $([[ $HAS_DOCKER -eq 1 ]] && echo true || echo false),
    "env_local": $([[ $HAS_ENV_LOCAL -eq 1 ]] && echo true || echo false),
    "backend_venv": $([[ $HAS_BACKEND_VENV -eq 1 ]] && echo true || echo false),
    "node_modules": $([[ $HAS_NODE_MODULES -eq 1 ]] && echo true || echo false)
  },
  "results": [$results_json],
  "summary": {
    "total": $total,
    "passed": $PASSED,
    "failed": $FAILED,
    "skipped": $SKIPPED
  }
}
EOF
    else
        # Human-readable output
        echo ""
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        printf "Summary: ${GREEN}%d passed${NC}" "$PASSED"
        [[ $FAILED -gt 0 ]] && printf ", ${RED}%d failed${NC}" "$FAILED"
        [[ $SKIPPED -gt 0 ]] && printf ", ${YELLOW}%d skipped${NC}" "$SKIPPED"
        printf " (total: %d)\n" "$total"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    fi

    # Exit code
    if [[ $FAILED -gt 0 ]]; then
        exit 1
    fi
    exit 0
}

# === Main ===
main() {
    parse_args "$@"

    if [[ $JSON_OUTPUT -eq 0 ]]; then
        echo ""
        echo -e "${BOLD}Just Commands Smoke Test${NC}"
        echo ""
    fi

    detect_environment

    case "$MODE" in
        quick)
            run_quick_mode
            ;;
        full)
            run_full_mode
            ;;
        single)
            run_single_mode
            ;;
    esac

    print_summary
}

main "$@"
