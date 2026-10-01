#!/bin/bash
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
AGENT_NAME=$(echo "$CLAUDE_TOOL_INPUT" | python -c "import sys,json; d=json.load(sys.stdin); print(d.get('description','unknown'))" 2>/dev/null || echo "unknown")
echo "" >> docs/changelog.md
echo "### $TIMESTAMP — Spawning agent: $AGENT_NAME" >> docs/changelog.md
