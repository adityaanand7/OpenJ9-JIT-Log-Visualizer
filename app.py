from flask import Flask, render_template, abort
import os
import re
import glob
from collections import defaultdict, OrderedDict

app = Flask(__name__)
LOG_DIR = 'logs'

def get_canonical_key(filename):
    """
    Creates a consistent, sanitized key from a filename to handle variations.
    It strips the leading number for matching purposes.
    """
    key = filename.rsplit('.log', 1)[0]
    # Strip the leading number (e.g., "1_..._cfg" -> "..._cfg")
    key = re.sub(r'^\d+_', '', key)
    # Remove known suffixes and sanitize
    key = key.replace('_cfg', '').replace('_trees', '')
    key = re.sub(r'_', '', key).lower()
    return key

def find_log_pairs():
    """
    Finds and groups all log files into matched pairs using a sanitized key,
    and uses the numbered cfg filename as the final key.
    """
    paired_files = {}
    canonical_map = defaultdict(dict)
    all_logs = glob.glob(os.path.join(LOG_DIR, '*.log'))
    
    for log_path in all_logs:
        filename = os.path.basename(log_path)
        key = get_canonical_key(filename)
        if filename.endswith('_cfg.log'):
            canonical_map[key]['cfg'] = filename
        else:
            canonical_map[key]['trees'] = filename
            
    # Create the final dictionary with clean, numbered keys for the UI
    for key, files in canonical_map.items():
        if 'cfg' in files and 'trees' in files:
            display_name = files['cfg'].replace('_cfg.log', '')
            paired_files[display_name] = files
            
    return paired_files

def sort_log_pairs(pairs_dict):
    """Sorts a dictionary of log pairs naturally based on the leading number in the key."""
    def natural_sort_key(item):
        key_string = item[0]
        match = re.match(r'(\d+)_', key_string)
        if match:
            # Return the number as an integer for correct sorting
            return int(match.group(1))
        # If a file has no number, put it at the end
        return float('inf')

    sorted_items = sorted(pairs_dict.items(), key=natural_sort_key)
    return OrderedDict(sorted_items)

@app.route('/')
def index():
    """Lists all available log pairs in sorted order."""
    complete_pairs = find_log_pairs()
    sorted_pairs = sort_log_pairs(complete_pairs)
    return render_template('viewer.html', files=sorted_pairs, current_file=None)

@app.route('/view/<string:file_base>')
def view_log(file_base):
    """Displays a specific log pair, keeping the sidebar sorted."""
    complete_pairs = find_log_pairs()
    sorted_pairs = sort_log_pairs(complete_pairs)
    
    pair_info = sorted_pairs.get(file_base)
    if not pair_info:
        abort(404, "Log file pair not found.")
        
    cfg_filename = pair_info.get('cfg')
    trees_filename = pair_info.get('trees')

    if not cfg_filename or not trees_filename:
        abort(404, "Incomplete log pair.")

    # Process files...
    from cfg_to_svg import parse_cfg_to_dot, generate_svg_from_dot
    from trees_to_html import parse_trees_to_html
    
    with open(os.path.join(LOG_DIR, cfg_filename), 'r') as f:
        cfg_content = f.read()
    dot_string = parse_cfg_to_dot(cfg_content)
    svg_data = generate_svg_from_dot(dot_string)

    with open(os.path.join(LOG_DIR, trees_filename), 'r') as f:
        trees_content = f.read()
    trees_html = parse_trees_to_html(trees_content)

    return render_template(
        'viewer.html',
        files=sorted_pairs,
        current_file=file_base,
        svg_data=svg_data,
        trees_html=trees_html
    )

if __name__ == '__main__':
    if not os.path.isdir(LOG_DIR):
        print(f"Error: The '{LOG_DIR}' directory was not found.")
    else:
        app.run(debug=True)