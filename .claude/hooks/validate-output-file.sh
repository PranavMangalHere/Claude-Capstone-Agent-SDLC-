#!/bin/bash
FILE_PATH=$(echo "$CLAUDE_TOOL_INPUT" | python -c "import sys,json; d=json.load(sys.stdin); print(d.get('file_path',''))" 2>/dev/null || echo "")

# Only validate files in docs/ or output/
if [[ "$FILE_PATH" == docs/* ]] || [[ "$FILE_PATH" == output/* ]]; then
  if [ ! -s "$FILE_PATH" ]; then
    echo "WARNING: $FILE_PATH was written but is empty. The agent may have failed to produce output." >&2
  else
    LINES=$(wc -l < "$FILE_PATH")
    echo "OK: $FILE_PATH written ($LINES lines)" >&2
  fi
fi
