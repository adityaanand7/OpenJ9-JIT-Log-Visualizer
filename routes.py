from flask import Flask, render_template, abort, request, redirect, url_for, current_app, session, jsonify
import os
import re
import glob
from flask import Blueprint
from collections import defaultdict, OrderedDict
import shutil
import subprocess
from werkzeug.utils import secure_filename

# Helpers that transform raw logs into renderable HTML/SVG.
from cfg_to_svg import parse_cfg_to_dot, generate_svg_from_dot
from trees_to_html import parse_trees_to_html

# Main blueprint for the log viewer UI.
log_viewer_bp = Blueprint(
    'log_viewer', 
    __name__, 
    template_folder='templates',
    static_folder='static'
)

LOG_DIR = os.path.join(os.path.dirname(__file__), 'logs')

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

def make_short_label(display_name):
    """
    Converts e.g. '1_Main.fooV_Pre_ILGenOpt_Trees' to '1. Pre ILGenOpt Trees'.
    Strips the leading number, removes the method part, and joins the rest
    with spaces for readability.
    """
    parts = display_name.split('_')
    if len(parts) < 3:
        return display_name
    number = parts[0]
    # parts[1] is the method name (e.g. Main.fooV), skip it
    pass_parts = parts[2:]
    pass_name = ' '.join(pass_parts)
    return f"{number}. {pass_name}"


def find_log_pairs():
    """
    Finds and groups all log files into matched pairs using a sanitized key,
    and uses the numbered cfg filename as the final key.
    """
    paired_files = {}
    canonical_map = defaultdict(dict)
    all_logs = glob.glob(os.path.join(LOG_DIR, '*.log'))
    # print(f"Found log files: {all_logs}")
    for log_path in all_logs:
        filename = os.path.basename(log_path)
        key = get_canonical_key(filename)
        if filename.endswith('_cfg.log'):
            canonical_map[key]['cfg'] = filename
        else:
            canonical_map[key]['trees'] = filename

    # Keep only complete pairs so the UI never shows half-generated passes.
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


def scan_methods_from_file(filepath):
    """Scans a JIT log file line-by-line for <compile> blocks,
    extracting method and hotness attributes. Returns a list of dicts.
    Works efficiently on multi-GB files since it never loads the whole file.
    """
    methods = []
    seen = set()
    in_compile = False
    block_lines = []

    with open(filepath, 'r', errors='replace') as f:
        for line in f:
            if '<compile' in line:
                in_compile = True
                block_lines = [line]
            elif in_compile:
                block_lines.append(line)

            if in_compile and '>' in line:
                block = ''.join(block_lines)
                in_compile = False
                block_lines = []

                mm = re.search(r'\bmethod\s*=\s*"([^"]+)"', block)
                if not mm:
                    continue
                method_name = mm.group(1).strip()
                hm = re.search(r'\bhotness\s*=\s*"([^"]+)"', block)
                hotness = hm.group(1).strip() if hm else 'unknown'
                entry = f"{method_name}-{hotness}"
                if entry not in seen:
                    seen.add(entry)
                    methods.append({'display': entry, 'method': method_name, 'hotness': hotness})

    methods.sort(key=lambda x: x['display'])
    return methods

@log_viewer_bp.route('/')
def index():
    """Lists all available log pairs in sorted order."""
    complete_pairs = find_log_pairs()
    sorted_pairs = sort_log_pairs(complete_pairs)
    uploaded_file = session.get('uploaded_file', '')
    opt_level = session.get('opt_level', '')
    return render_template('viewer.html', files=sorted_pairs, current_file=None,
                           short_label=make_short_label, uploaded_file=uploaded_file,
                           opt_level=opt_level)


@log_viewer_bp.route('/upload-file', methods=['POST'])
def upload_file_only():
    """AJAX endpoint: saves the uploaded file and scans it for methods.
    Returns JSON with the filename + methods list. Does NOT run the extractor.
    """
    uploads_dir = os.path.join(os.path.dirname(__file__), 'uploads')
    os.makedirs(uploads_dir, exist_ok=True)

    uploaded = request.files.get('dumpfile')
    if not uploaded or uploaded.filename == '':
        return jsonify({'error': 'No file provided'}), 400

    filename = secure_filename(uploaded.filename)
    saved_path = os.path.join(uploads_dir, filename)
    uploaded.save(saved_path)
    file_size = os.path.getsize(saved_path)
    current_app.logger.info(f"Uploaded file saved: {filename} ({file_size / 1024:.1f} KB)")

    # Also copy to complete_log_file/ for the extractor
    script_log_dir = os.path.join(os.path.dirname(__file__), 'complete_log_file')
    os.makedirs(script_log_dir, exist_ok=True)
    dest_path = os.path.join(script_log_dir, filename)
    current_app.logger.info(f"Copying {filename} to {script_log_dir}/ ...")
    shutil.copy2(saved_path, dest_path)
    current_app.logger.info(f"Copy complete: {dest_path}")

    # Scan for methods
    current_app.logger.info(f"Scanning {filename} for <compile> blocks ...")
    methods = scan_methods_from_file(saved_path)
    current_app.logger.info(f"Found {len(methods)} methods in {filename}")

    # Remember the filename in session
    session['uploaded_file'] = filename

    return jsonify({'filename': filename, 'size': file_size, 'methods': methods})


@log_viewer_bp.route('/scan-methods', methods=['GET'])
def scan_methods():
    """Returns methods for the currently uploaded file (from session)."""
    filename = session.get('uploaded_file', '')
    if not filename:
        return jsonify({'error': 'No file uploaded', 'methods': []}), 404

    uploads_dir = os.path.join(os.path.dirname(__file__), 'uploads')
    filepath = os.path.join(uploads_dir, filename)
    if not os.path.isfile(filepath):
        session.pop('uploaded_file', None)
        return jsonify({'error': 'File not found', 'methods': []}), 404

    methods = scan_methods_from_file(filepath)
    file_size = os.path.getsize(filepath)
    return jsonify({'filename': filename, 'size': file_size, 'methods': methods})

@log_viewer_bp.route('/view/<string:file_base>')
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

    # Render CFG first, then render Tree IL for the same pass.
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
        trees_html=trees_html,
        short_label=make_short_label,
        uploaded_file=session.get('uploaded_file', ''),
        opt_level=session.get('opt_level', '')
    )


@log_viewer_bp.route('/upload', methods=['POST'])
def upload_dump():
    """Handles method generation. If a file was previously uploaded (in session),
    it reuses that file. Otherwise expects a new file upload.
    Clears the logs folder and runs generate-tree-cfg.sh.
    """
    uploads_dir = os.path.join(os.path.dirname(__file__), 'uploads')
    os.makedirs(uploads_dir, exist_ok=True)

    # Clear the logs directory
    try:
        if os.path.isdir(LOG_DIR):
            for entry in os.listdir(LOG_DIR):
                path = os.path.join(LOG_DIR, entry)
                try:
                    if os.path.isfile(path) or os.path.islink(path):
                        os.unlink(path)
                    elif os.path.isdir(path):
                        shutil.rmtree(path)
                except Exception as e:
                    current_app.logger.exception(f"Failed to remove {path}: {e}")
    except Exception as e:
        current_app.logger.exception(f"Failed to clear logs directory: {e}")

    method = (request.form.get('method') or '').strip()
    hotness = (request.form.get('hotness') or '').strip()
    if not method:
        current_app.logger.warning('Upload failed: missing method')
        return redirect(url_for('log_viewer.index'))

    # Check if file was already uploaded (session) or if a new file is being sent
    uploaded = request.files.get('dumpfile')
    has_new_file = uploaded and uploaded.filename != ''

    if has_new_file:
        filename = secure_filename(uploaded.filename)
        saved_path = os.path.join(uploads_dir, filename)
        uploaded.save(saved_path)
        session['uploaded_file'] = filename

        # Copy to complete_log_file/
        script_log_dir = os.path.join(os.path.dirname(__file__), 'complete_log_file')
        os.makedirs(script_log_dir, exist_ok=True)
        dest_path = os.path.join(script_log_dir, filename)
        shutil.copy2(saved_path, dest_path)
    else:
        filename = session.get('uploaded_file', '')
        if not filename:
            current_app.logger.warning('Upload failed: no file in session')
            return redirect(url_for('log_viewer.index'))
        # Verify the file still exists in complete_log_file/
        script_log_dir = os.path.join(os.path.dirname(__file__), 'complete_log_file')
        if not os.path.isfile(os.path.join(script_log_dir, filename)):
            current_app.logger.warning(f'File {filename} not found in complete_log_file/')
            session.pop('uploaded_file', None)
            return redirect(url_for('log_viewer.index'))

    current_app.logger.info(f"Generating trees/cfg for method={method} (hotness={hotness}) from {filename}")
    session['opt_level'] = hotness

    # Run the generator script
    script_path = os.path.join(os.path.dirname(__file__), 'generate-tree-cfg.sh')
    try:
        proc = subprocess.run(
            ['bash', script_path, filename, method],
            cwd=os.path.dirname(__file__),
            capture_output=True,
            text=True,
            timeout=300
        )
        if proc.returncode != 0:
            current_app.logger.error(f"generate-tree-cfg failed: {proc.stderr}")
        else:
            current_app.logger.info(f"generate-tree-cfg output: {proc.stdout}")
    except Exception as e:
        current_app.logger.exception(f"Failed to run generator script: {e}")

    # After extraction, reload index so fresh pass files appear in sidebar.
    return redirect(url_for('log_viewer.index', generated=1))


@log_viewer_bp.route('/clear', methods=['POST'])
def clear_generated_files():
    """Clears files from the logs directory, uploads, complete_log_file, and session.
    Redirects to the log viewer index afterwards.
    """
    uploads_dir = os.path.join(os.path.dirname(__file__), 'uploads')
    complete_dir = os.path.join(os.path.dirname(__file__), 'complete_log_file')

    for dir_path in [LOG_DIR, uploads_dir, complete_dir]:
        try:
            if os.path.isdir(dir_path):
                for entry in os.listdir(dir_path):
                    path = os.path.join(dir_path, entry)
                    try:
                        if os.path.isfile(path) or os.path.islink(path):
                            os.unlink(path)
                        elif os.path.isdir(path):
                            shutil.rmtree(path)
                    except Exception:
                        current_app.logger.exception(f"Failed to remove {path}")
        except Exception:
            current_app.logger.exception(f"Failed to clear {dir_path}")

    session.pop('uploaded_file', None)
    return redirect(url_for('log_viewer.index'))

# if __name__ == '__main__':
#     if not os.path.isdir(LOG_DIR):
#         print(f"Error: The '{LOG_DIR}' directory was not found.")
#     else:
#         app.run(debug=True)
