#!/bin/bash

echo "🧹 Cleaning up codebase..."
echo ""

# 1. Remove legacy
echo "1️⃣ Removing legacy files..."
rm -rf legacy/
rm -f .env.bak
rm -rf test_conversations/
echo "   ✅ Cleaned legacy files"

# 2. Reorganize
echo "2️⃣ Reorganizing structure..."
if [ -f webhook_server.py ]; then
    mv webhook_server.py scripts/
fi
mkdir -p tests/integration tests/unit
echo "   ✅ Reorganized"

# 3. Update gitignore
echo "3️⃣ Updating .gitignore..."
cat >> .gitignore << 'GITIGNORE'

# Backup files
*.bak
*.backup
*~

# Legacy
legacy/

# Tests
test_output/
*.test.log
GITIGNORE
echo "   ✅ Updated .gitignore"

echo ""
echo "✅ CLEANUP COMPLETE!"
