#!/usr/bin/env python
"""
Export OpenAPI spec from running FastAPI server and save to docs/swagger.json

This script connects to a running Image Insights API instance and exports the
OpenAPI specification. It ensures docs/swagger.json stays in sync with the actual
API implementation.

Usage:
    # Make sure the API is running first
    python -m uvicorn app.main:app --reload

    # In another terminal, run this script
    python scripts/export_openapi.py

    # Or specify a custom server URL
    python scripts/export_openapi.py --url http://localhost:3000
"""

import argparse
import json
import sys
from pathlib import Path

import requests


def export_openapi_spec(server_url: str, output_path: Path) -> bool:
    """
    Export OpenAPI spec from a running FastAPI server.

    Args:
        server_url: Base URL of the API server (e.g., http://localhost:8080)
        output_path: Path to save the OpenAPI spec JSON file

    Returns:
        True if successful, False otherwise
    """
    openapi_url = f"{server_url}/openapi.json"

    print(f"📡 Fetching OpenAPI spec from {openapi_url}...")

    try:
        response = requests.get(openapi_url, timeout=5)
        response.raise_for_status()
    except requests.ConnectionError:
        print(f"❌ Error: Could not connect to {server_url}")
        print("   Make sure the API is running:")
        print("   python -m uvicorn app.main:app --reload")
        return False
    except requests.RequestException as e:
        print(f"❌ Error fetching OpenAPI spec: {e}")
        return False

    spec = response.json()

    # Save to file
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with open(output_path, "w") as f:
            json.dump(spec, f, indent=2)
        print(f"✅ OpenAPI spec exported to {output_path}")
        return True
    except OSError as e:
        print(f"❌ Error writing to {output_path}: {e}")
        return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Export OpenAPI spec from FastAPI server to docs/swagger.json"
    )
    parser.add_argument(
        "--url",
        default="http://localhost:8080",
        help="Base URL of the API server (default: http://localhost:8080)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).parent.parent / "docs" / "swagger.json",
        help="Output file path (default: docs/swagger.json)",
    )

    args = parser.parse_args()

    if export_openapi_spec(args.url, args.output):
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
