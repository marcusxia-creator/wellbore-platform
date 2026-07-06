#!/usr/bin/env bash
#
# Generate a static OpenAPI schema file from the current DRF views/serializers.
#
# Usage (from the backend/ directory):
#   ./scripts/generate_schema.sh              # writes schema.yml
#   ./scripts/generate_schema.sh openapi.json # custom output path
#
# Inside Docker:
#   docker compose exec backend ./scripts/generate_schema.sh
#
# The generated file is a build artifact derived from the code, so it is
# gitignored. The live schema is always available at /api/schema/.

set -euo pipefail

OUTPUT="${1:-schema.yml}"

python manage.py spectacular --color --file "$OUTPUT"

echo "Schema written to $OUTPUT"
