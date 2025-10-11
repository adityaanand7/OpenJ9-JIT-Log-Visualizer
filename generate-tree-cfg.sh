#!/bin/bash

# --- JIT Extractor Runner ---
# This script simplifies running the Python JIT extractor by taking the
# log filename and method name as arguments and constructing the full command.

# --- CONFIGURATION ---
# The fixed paths to your script and log directory.
SCRIPT_PATH="tree-cfg-extractor/jit_cfg_extractor.py"
LOG_DIR="complete_log_file"

# --- ARGUMENT VALIDATION ---
# Check if exactly two arguments were provided.
if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <log_file_name> \"<method_name>\""
    echo "--------------------------------------------------"
    echo "Example:"
    echo "  bash generate-tree-cfg log_File \"Main.foo()V\""
    exit 1
fi

# --- ASSIGN ARGUMENTS TO VARIABLES ---
LOG_FILE_NAME=$1
METHOD_NAME=$2
FULL_LOG_PATH="${LOG_DIR}/${LOG_FILE_NAME}"

# --- PRE-RUN CHECKS ---
# Check if the Python script exists
if [ ! -f "$SCRIPT_PATH" ]; then
    echo "Error: Python extractor not found at '$SCRIPT_PATH'"
    exit 1
fi

# Check if the log file exists
if [ ! -f "$FULL_LOG_PATH" ]; then
    echo "Error: Log file not found at '$FULL_LOG_PATH'"
    exit 1
fi

#Clean log file folder (logs)
rm -rf logs/*

# --- EXECUTE THE COMMANDS ---
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