import re
import sys
import os

# Legacy tree-only extractor kept for quick CLI checks.
def extract_jit_trees(log_file_path, target_method):
    """
    Parses a JIT log file and extracts the content of all <trees>...</trees>
    blocks for a specified method, saving each to a separate, numbered file.
    """
    if not os.path.exists(log_file_path):
        print(f"Error: Log file not found at '{log_file_path}'")
        return

    print(f"--- JIT Tree Extractor ---")
    print(f"Reading log file: {log_file_path}")
    print(f"Target method: {target_method}")

    try:
        # Load the full log once so regex scans are straightforward.
        with open(log_file_path, 'r', encoding='utf-8', errors='ignore') as f:
            log_content = f.read()
    except Exception as e:
        print(f"Error reading file: {e}")
        return

    tree_block_pattern = re.compile(r'(<trees.*?)</trees>', re.DOTALL | re.IGNORECASE)
    attr_pattern = re.compile(r'title="(.*?)"\s+method="(.*?)"', re.DOTALL | re.IGNORECASE)

    found_trees = 0

    # Walk all tree blocks and keep only the requested method.
    for match in tree_block_pattern.finditer(log_content):
        trees_content_start = match.group(1).strip()
        full_trees_block = trees_content_start + '\n</trees>' 
        
        attr_match = attr_pattern.search(trees_content_start)
        
        if attr_match:
            title = attr_match.group(1).strip()
            method = attr_match.group(2).strip()

            if method == target_method:
                found_trees += 1

                safe_title = re.sub(r'[^\w\s-]', '', title).strip()
                safe_title = re.sub(r'[-\s]+', '_', safe_title)
                safe_method = re.sub(r'[^\w\s.]', '_', method).strip()
                
                # Prefix with a counter so files never overwrite each other.
                output_filename = f"{found_trees}_{safe_method}_{safe_title}.log"
                
                try:
                    with open(output_filename, 'w', encoding='utf-8') as outfile:
                        outfile.write(full_trees_block)
                    
                    print(f"Extracted phase '{title}' to file: {output_filename}")
                except Exception as e:
                    print(f"Error writing to file {output_filename}: {e}")
                
    if found_trees == 0:
        print(f"\nNo <trees> blocks found for method: {target_method}")
    else:
        print(f"\nSuccessfully extracted {found_trees} tree phase(s) for method: {target_method}")


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: python jit_tree_extractor.py <path_to_log_file> <method_name>")
        print("\nExample: python jit_tree_extractor.py example-withHCR.log Main.foo()V")
        print("The method name must be enclosed in quotes if it contains spaces or special shell characters.")
        sys.exit(1)

    log_file_path = sys.argv[1]
    target_method = sys.argv[2]
    
    extract_jit_trees(log_file_path, target_method)