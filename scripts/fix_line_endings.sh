#!/bin/bash
#
# Converts line endings from Windows (CRLF) to Unix (LF) for all relevant
# source code and script files in the project.

set -e
echo "🔎 Finding and converting files with Windows line endings..."

# Find all files with common text extensions and run dos2unix on them.
# The `2>/dev/null` part suppresses benign permission errors that occur
# when running as a different user inside a Docker-mounted volume.
# The `|| true` ensures the script doesn't exit if a file fails for any reason.
find ../ -type f \( \
    -name "*.py" -o \
    -name "*.sh" -o \
    -name "*.cpp" -o \
    -name "*.hpp" -o \
    -name "*.h" -o \
    -name "*.c" -o \
    -name "*.txt" -o \
    -name "Dockerfile" \
    \) -exec dos2unix {} + 2>/dev/null || true

echo "✅ Line ending conversion complete."