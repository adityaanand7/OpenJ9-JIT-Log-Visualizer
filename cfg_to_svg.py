import re
import sys
import subprocess

# Convert OpenJ9 CFG text dumps into clickable DOT/SVG.
def parse_cfg_to_dot(cfg_content):
    """
    Robustly parses CFG log content by analyzing it block-by-block,
    ensuring all nodes with addresses are correctly identified and made clickable.
    """
    
    # Each chunk starts at a basic-block header like: "7 [0x....]".
    block_chunks = re.split(r'^\s*(?=\d+\s+\[0x)', cfg_content, flags=re.MULTILINE)

    nodes = {}
    edges = []

    for chunk in block_chunks:
        if not chunk.strip():
            continue

        # Every chunk should begin with a numeric block id.
        id_match = re.search(r'^\s*(\d+)', chunk)
        if not id_match:
            continue
        node_id = id_match.group(1)
        
        # If we have a BBStart address, use it to link CFG nodes to Tree IL blocks.
        address_match = re.search(r'BBStart at (0x[0-9a-f]+)', chunk)
        if address_match:
            address = address_match.group(1)
            nodes[node_id] = {'address': address, 'label': f"Block {node_id}"}
        else:
            # Special nodes (entry/exit) do not have a BBStart address.
            type_match = re.search(r'\]\s*(entry|exit)', chunk)
            if type_match:
                node_type = type_match.group(1)
                nodes[node_id] = {'address': None, 'label': node_type}
            else:
                # Fallback for unknown node shapes.
                nodes[node_id] = {'address': None, 'label': f"Node {node_id}"}

        # Pull outgoing edges from the "out=[...]" section.
        out_match = re.search(r'out\s*=\s*\[(.*?)\]', chunk, re.DOTALL)
        if out_match:
            edge_pattern = re.compile(r'(\d+)\(\d+\)')
            for edge_match in edge_pattern.finditer(out_match.group(1)):
                edges.append((node_id, edge_match.group(1)))

    # Build a DOT graph with colors tuned for readability in the UI.
    dot_lines = [
        'digraph CFG {',
        '    rankdir="TB";',
        '    splines=true;',
        '    nodesep=0.6;',
        '    ranksep=0.5;',
        '    bgcolor="transparent";',
        '    pad=0.3;',
        '',
        '    // Default node style',
        '    node [shape=box, style="rounded,filled", fontname="Inter, Segoe UI, Roboto, sans-serif",',
        '          fontsize=11, fillcolor="#f8fafc", color="#94a3b8", penwidth=1.5,',
        '          margin="0.15,0.08"];',
        '',
        '    // Default edge style',
        '    edge [color="#94a3b8", arrowsize=0.7, penwidth=1.2,',
        '          fontname="Inter, Segoe UI, Roboto, sans-serif", fontsize=9];',
    ]

    for node_id, data in nodes.items():
        label = data.get('label')
        address = data.get('address')

        if address:
            # Regular block nodes.
            dot_lines.append(
                f'    "{node_id}" [label="{label}", id="svg-node-for-{address}", href="#",'
                f' fillcolor="#eff6ff", color="#3b82f6", fontcolor="#1e3a5f"];'
            )
        else:
            # Entry/exit nodes are styled separately so control flow is easier to scan.
            node_label = label.lower() if label else ''
            if node_label == 'entry':
                dot_lines.append(
                    f'    "{node_id}" [label="{label}", id="svg-node-special-{node_id}",'
                    f' shape=oval, fillcolor="#ecfdf5", color="#10b981", fontcolor="#065f46",'
                    f' style="filled", penwidth=2];'
                )
            elif node_label == 'exit':
                dot_lines.append(
                    f'    "{node_id}" [label="{label}", id="svg-node-special-{node_id}",'
                    f' shape=oval, fillcolor="#fef2f2", color="#ef4444", fontcolor="#991b1b",'
                    f' style="filled", penwidth=2];'
                )
            else:
                dot_lines.append(
                    f'    "{node_id}" [label="{label}", id="svg-node-special-{node_id}",'
                    f' fillcolor="#f5f3ff", color="#8b5cf6", fontcolor="#5b21b6"];'
                )

    for start_node, end_node in edges:
        if start_node in nodes and end_node in nodes:
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
