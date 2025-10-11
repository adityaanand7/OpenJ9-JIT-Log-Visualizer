import re
import sys
import subprocess

def parse_cfg_to_dot(cfg_content):
    """
    Robustly parses CFG log content by analyzing it block-by-block,
    ensuring all nodes with addresses are correctly identified and made clickable.
    """
    
    # Split the log into chunks, one for each block definition.
    # A block starts with a number, a space, and a bracketed hex address.
    block_chunks = re.split(r'^\s*(?=\d+\s+\[0x)', cfg_content, flags=re.MULTILINE)

    nodes = {}
    edges = []

    for chunk in block_chunks:
        if not chunk.strip():
            continue

        # --- 1. Find the Node ID for this chunk ---
        id_match = re.search(r'^\s*(\d+)', chunk)
        if not id_match:
            continue
        node_id = id_match.group(1)
        
        # --- 2. Check for a BBStart address to make it clickable ---
        address_match = re.search(r'BBStart at (0x[0-9a-f]+)', chunk)
        if address_match:
            address = address_match.group(1)
            nodes[node_id] = {'address': address, 'label': f"Block {node_id}"}
        else:
            # --- 3. If no address, check if it's a special type like 'entry' or 'exit' ---
            type_match = re.search(r'\]\s*(entry|exit)', chunk)
            if type_match:
                node_type = type_match.group(1)
                nodes[node_id] = {'address': None, 'label': node_type}
            else:
                # Fallback for any other kind of node
                nodes[node_id] = {'address': None, 'label': f"Node {node_id}"}

        # --- 4. Find all outgoing edges for this block ---
        out_match = re.search(r'out\s*=\s*\[(.*?)\]', chunk, re.DOTALL)
        if out_match:
            edge_pattern = re.compile(r'(\d+)\(\d+\)')
            for edge_match in edge_pattern.finditer(out_match.group(1)):
                edges.append((node_id, edge_match.group(1)))

    # --- Generate DOT file content ---
    dot_lines = ['digraph CFG {', '    rankdir="TB";', '    node [shape=box, style=rounded, fontname="sans-serif"];']
    
    for node_id, data in nodes.items():
        label = data.get('label')
        address = data.get('address')
        
        if address:
            # Make clickable nodes
            dot_lines.append(f'    "{node_id}" [label="{label}", id="svg-node-for-{address}", href="#"];')
        else:
            # Non-clickable nodes (like 'entry' and 'exit')
            dot_lines.append(f'    "{node_id}" [label="{label}", id="svg-node-special-{node_id}"];')

    for start_node, end_node in edges:
        if start_node in nodes and end_node in nodes: # Ensure edge is valid
             dot_lines.append(f'    "{start_node}" -> "{end_node}";')
    
    dot_lines.append('}')
    return "\n".join(dot_lines)


def generate_svg_from_dot(dot_string):
    """Uses the 'dot' command to convert a DOT string to an SVG string."""
    try:
        process = subprocess.run(
            ['dot', '-Tsvg'], input=dot_string, capture_output=True, text=True, check=True
        )
        svg_content = process.stdout
        svg_content = re.sub(r'<\?xml.*?\?>\n', '', svg_content)
        svg_content = re.sub(r'\n', '', svg_content)
        return svg_content
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("\n---")
        print("Error: Could not run the 'dot' command.")
        print("Please make sure Graphviz is installed and that its 'bin' directory is in your system's PATH.")
        print("---\n")
        return None

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python cfg_to_svg.py <path_to_cfg_log>")
        sys.exit(1)
    with open(sys.argv[1], 'r') as f:
        content = f.read()
    dot_graph = parse_cfg_to_dot(content)
    if dot_graph:
        svg_output = generate_svg_from_dot(dot_graph)
        if svg_output:
            output_file = sys.argv[1].replace('.log', '.svg')
            with open(output_file, 'w') as f: f.write(svg_output)
            print(f"Successfully generated clickable SVG: {output_file}")
