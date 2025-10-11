import re
import sys
import os

def clean_filename(text):
    """Creates a safe filename from a string."""
    safe_text = re.sub(r'[^\w\s.-]', '', text).strip()
    return re.sub(r'[-\s]+', '_', safe_text)

def extract_jit_data(log_file_path, target_method, block_type):
    """
    Parses a JIT log by finding the method's true boundaries ('=======>')
    and extracting either <trees> or <cfg> blocks within it.
    """
    if not os.path.exists(log_file_path):
        print(f"Error: Log file not found at '{log_file_path}'")
        return

    try:
        with open(log_file_path, 'r', encoding='utf-8', errors='ignore') as f:
            log_content = f.read()
    except Exception as e:
        print(f"Error reading file: {e}")
        return

    print(f"--- JIT {block_type.upper()} Extractor (Numbered Output) ---")
    print(f"Reading log file: {log_file_path}")
    print(f"Target method: {target_method}")

    start_marker = f"=======>{target_method}"
    start_index = log_content.find(start_marker)
    if start_index == -1:
        print(f"\nError: Could not find start marker for the method.")
        return

    end_index = log_content.find('=======>', start_index + len(start_marker))
    method_block = log_content[start_index:end_index] if end_index != -1 else log_content[start_index:]
    safe_method_name = clean_filename(target_method)

    if block_type == 'trees':
        extract_trees_from_block(method_block, safe_method_name)
    elif block_type == 'cfg':
        extract_cfgs_from_block(method_block, safe_method_name)

def extract_trees_from_block(method_block, safe_method_name):
    """Extracts all <trees> blocks from the given method block."""
    tree_pattern = re.compile(r'(<trees\s+title="([^"]+)".*?</trees>)', re.DOTALL)
    matches = tree_pattern.findall(method_block)
    if not matches:
        print(f"\nNo <trees> blocks found in this section.")
        return

    # Use enumerate to get a counter (i) starting from 0
    for i, (full_block, title) in enumerate(matches):
        safe_title = clean_filename(title)
        
        # --- MODIFIED LINE ---
        # Prepend the counter (i + 1) to the filename
        output_filename = f"{i + 1}_{safe_method_name}_{safe_title}_trees.log"
        
        try:
            with open(output_filename, 'w', encoding='utf-8') as outfile:
                outfile.write(full_block)
            print(f"Extracted phase '{title}' to file: {output_filename}")
        except Exception as e:
            print(f"Error writing file {output_filename}: {e}")
    print(f"\nSuccessfully extracted {len(matches)} <trees> block(s).")

def extract_cfgs_from_block(method_block, safe_method_name):
    """Extracts all <cfg> blocks, correctly named and without overwrites."""
    phase_pattern = re.compile(r'<trees\s+title="([^"]+)"')
    cfg_pattern = re.compile(r'(<cfg>.*?</cfg>)', re.DOTALL)

    phases = [(match.start(), match.group(1)) for match in phase_pattern.finditer(method_block)]
    cfgs = [(match.start(), match.group(1)) for match in cfg_pattern.finditer(method_block)]

    if not cfgs:
        print(f"\nNo <cfg> blocks found in this section.")
        return

    # Use enumerate to get a counter (i) starting from 0
    for i, (cfg_start, cfg_block) in enumerate(cfgs):
        current_phase_name = "Untitled"
        for phase_start, phase_title in phases:
            if phase_start < cfg_start:
                current_phase_name = phase_title
            else:
                break
        
        safe_phase_name = clean_filename(current_phase_name)
        
        # --- MODIFIED LINE ---
        # Prepend the counter (i + 1) to the filename
        output_filename = f"{i + 1}_{safe_method_name}_{safe_phase_name}_cfg.log"

        try:
            with open(output_filename, 'w', encoding='utf-8') as outfile:
                outfile.write(cfg_block)
            print(f"Extracted CFG for phase '{current_phase_name}' to file: {output_filename}")
        except Exception as e:
            print(f"Error writing file {output_filename}: {e}")

    print(f"\nSuccessfully extracted {len(cfgs)} <cfg> block(s).")


if __name__ == '__main__':
    if len(sys.argv) != 4:
        print("\nUsage: python jit_extractor.py <path_to_log_file> \"<method_name>\" <type>")
        print("       <type> can be 'trees' or 'cfg'")
        sys.exit(1)
    
    log_file_path, target_method, block_type = sys.argv[1], sys.argv[2], sys.argv[3].lower()

    if block_type not in ['trees', 'cfg']:
        print(f"Error: Invalid type '{block_type}'. Please choose 'trees' or 'cfg'.")
        sys.exit(1)
        
    extract_jit_data(log_file_path, target_method, block_type)