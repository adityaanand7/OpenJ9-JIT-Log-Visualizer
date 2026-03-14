#!/bin/bash

# Convenience wrapper used by the web route and manual CLI runs.
# Inputs: dump filename + full method signature.

# Fixed locations used by this repository layout.
SCRIPT_PATH="tree-cfg-extractor/jit_cfg_extractor.py"
LOG_DIR="complete_log_file"

# Require exactly two args: file and method.
if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <log_file_name> \"<method_name>\""
    echo "--------------------------------------------------"
    echo "Example:"
    echo "  bash generate-tree-cfg log_File \"Main.foo()V\""
    exit 1
fi

LOG_FILE_NAME=$1
METHOD_NAME=$2
FULL_LOG_PATH="${LOG_DIR}/${LOG_FILE_NAME}"

# Basic safety checks before extraction.
if [ ! -f "$SCRIPT_PATH" ]; then
    echo "Error: Python extractor not found at '$SCRIPT_PATH'"
    exit 1
fi

if [ ! -f "$FULL_LOG_PATH" ]; then
    echo "Error: Log file not found at '$FULL_LOG_PATH'"
    exit 1
fi

# Clear old outputs so this run contains only the selected method.
rm -rf logs/*

# Run both extraction modes expected by the viewer.
echo "--- Running for Trees ---"
python3 "$SCRIPT_PATH" "$FULL_LOG_PATH" "$METHOD_NAME" "trees"
mv *.log logs/

echo "" # Add a newline for spacing
echo "--- Running for CFG ---"
python3 "$SCRIPT_PATH" "$FULL_LOG_PATH" "$METHOD_NAME" "cfg"
mv *.log logs/

echo ""
echo "Extraction complete."
echo "Files have been generated to the 'logs' directory."