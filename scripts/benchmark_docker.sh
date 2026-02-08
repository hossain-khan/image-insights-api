#!/bin/bash
# Script to run benchmark inside or against a Docker container
#
# Usage:
#   # Run benchmark against a running Docker container
#   ./scripts/benchmark_docker.sh
#
#   # Build, run container, benchmark, then cleanup
#   ./scripts/benchmark_docker.sh --build-and-run
#
#   # Run benchmark inside a running container
#   ./scripts/benchmark_docker.sh --inside-container

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
IMAGE_NAME="${IMAGE_NAME:-image-insights-api}"
CONTAINER_NAME="${CONTAINER_NAME:-benchmark-api-server}"
API_PORT="${API_PORT:-8080}"
API_HOST="${API_HOST:-http://localhost:$API_PORT}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

function info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

function success() {
    echo -e "${GREEN}✅${NC} $1"
}

function warning() {
    echo -e "${YELLOW}⚠️${NC} $1"
}

function error() {
    echo -e "${RED}❌${NC} $1"
}

function print_usage() {
    cat << EOF
Usage: $(basename "$0") [OPTIONS]

Run benchmark for Image Insights API using Docker.

OPTIONS:
    --build-and-run     Build image, start container, run benchmark, cleanup
    --inside-container  Run benchmark inside a running container
    --host HOST         API host URL (default: http://localhost:8080)
    --iterations N      Number of iterations per test (default: 10)
    --help              Show this help message

EXAMPLES:
    # Run benchmark against existing container
    ./scripts/benchmark_docker.sh

    # Full cycle: build, run, benchmark, cleanup
    ./scripts/benchmark_docker.sh --build-and-run

    # Run benchmark inside container
    ./scripts/benchmark_docker.sh --inside-container

    # Custom iterations
    ./scripts/benchmark_docker.sh --iterations 20

EOF
}

function wait_for_api() {
    local max_attempts=30
    local attempt=1
    
    info "Waiting for API to be ready..."
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s -f "$API_HOST/health" > /dev/null 2>&1; then
            success "API is ready!"
            return 0
        fi
        
        echo -n "."
        sleep 1
        ((attempt++))
    done
    
    error "API did not become ready within 30 seconds"
    return 1
}

function build_and_run() {
    info "Building Docker image..."
    cd "$REPO_ROOT"
    docker build -t "$IMAGE_NAME" .
    success "Docker image built: $IMAGE_NAME"
    
    # Stop and remove existing container if it exists
    if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
        info "Stopping existing container: $CONTAINER_NAME"
        docker stop "$CONTAINER_NAME" || true
        docker rm "$CONTAINER_NAME" || true
    fi
    
    info "Starting API container..."
    docker run -d \
        --name "$CONTAINER_NAME" \
        -p "$API_PORT:8080" \
        "$IMAGE_NAME"
    
    success "Container started: $CONTAINER_NAME"
    
    # Wait for API to be ready
    wait_for_api
    
    # Run benchmark
    info "Running benchmark..."
    python "$SCRIPT_DIR/benchmark.py" --host "$API_HOST" --iterations "${ITERATIONS:-10}"
    
    # Cleanup
    info "Stopping and removing container..."
    docker stop "$CONTAINER_NAME"
    docker rm "$CONTAINER_NAME"
    success "Cleanup complete"
}

function run_benchmark_outside() {
    info "Running benchmark against API at $API_HOST"
    
    # Check if API is accessible
    if ! curl -s -f "$API_HOST/health" > /dev/null 2>&1; then
        error "API is not accessible at $API_HOST"
        error "Please ensure the API is running:"
        echo "  docker run -d -p $API_PORT:8080 --name api-server $IMAGE_NAME"
        exit 1
    fi
    
    success "API is accessible"
    
    # Run benchmark
    python "$SCRIPT_DIR/benchmark.py" --host "$API_HOST" --iterations "${ITERATIONS:-10}"
}

function run_benchmark_inside() {
    info "Running benchmark inside container: $CONTAINER_NAME"
    
    # Check if container exists
    if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
        error "Container $CONTAINER_NAME is not running"
        error "Please start the container first:"
        echo "  docker run -d -p $API_PORT:8080 --name $CONTAINER_NAME $IMAGE_NAME"
        exit 1
    fi
    
    success "Container is running"
    
    # Wait for API to be ready inside container
    API_HOST="http://localhost:8080" wait_for_api
    
    # Run benchmark inside container
    info "Executing benchmark inside container..."
    docker exec "$CONTAINER_NAME" python scripts/benchmark.py \
        --host "http://localhost:8080" \
        --iterations "${ITERATIONS:-10}"
}

# Parse arguments
MODE="outside"
ITERATIONS=10

while [[ $# -gt 0 ]]; do
    case $1 in
        --build-and-run)
            MODE="build-and-run"
            shift
            ;;
        --inside-container)
            MODE="inside"
            shift
            ;;
        --host)
            API_HOST="$2"
            shift 2
            ;;
        --iterations)
            ITERATIONS="$2"
            shift 2
            ;;
        --help)
            print_usage
            exit 0
            ;;
        *)
            error "Unknown option: $1"
            print_usage
            exit 1
            ;;
    esac
done

# Main execution
echo "========================================"
echo "Image Insights API - Docker Benchmark"
echo "========================================"
echo "Mode: $MODE"
echo "API Host: $API_HOST"
echo "Iterations: $ITERATIONS"
echo "========================================"
echo

case $MODE in
    build-and-run)
        build_and_run
        ;;
    inside)
        run_benchmark_inside
        ;;
    outside)
        run_benchmark_outside
        ;;
esac

success "Benchmark completed successfully!"
