#!/usr/bin/env bash
# Simple secret scan for CI. Exits 1 if potential secrets are found.
set -euo pipefail

# Directories to exclude
EXCLUDES=(".git" "node_modules" "venv" "dev/infrastructure" ".github" "test-automation")
GREP_EXCLUDE_ARGS=()
for d in "${EXCLUDES[@]}"; do
  GREP_EXCLUDE_ARGS+=(--exclude-dir="$d")
done

# Patterns to look for
PATTERNS=(
  "AKIA[0-9A-Z]{16}"
  "aws_secret_access_key"
  "AWS_SECRET_ACCESS_KEY"
  "PRIVATE KEY" 
  "BEGIN RSA PRIVATE KEY"
  "BEGIN PRIVATE KEY"
  "SECRET_KEY="
  "client_secret"
  "api_key"
  "password\s*="
)

FOUND=0
for p in "${PATTERNS[@]}"; do
  if grep -R -I -n "${p}" "./" "${GREP_EXCLUDE_ARGS[@]}"; then
    FOUND=1
  fi
done

if [ "$FOUND" -eq 1 ]; then
  echo "Potential secrets found in repository. Please remove them and retry."
  exit 1
fi

echo "No obvious secrets found."
exit 0
