#!/bin/bash
# Run all Edge Function tests using Deno

set -e

echo "Running Edge Function tests..."
echo "================================"

# Change to the functions directory
cd "$(dirname "$0")/.."

# Run all tests in the _tests directory
deno test \
  --allow-env \
  --allow-read \
  --allow-net \
  --import-map=import_map.json \
  _tests/*.ts

echo ""
echo "================================"
echo "All tests completed!"
