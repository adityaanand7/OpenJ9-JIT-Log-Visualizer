import re
import sys
import html

# Convert Tree IL text into HTML blocks addressable from CFG clicks.
def parse_trees_to_html(trees_content):
    """
    Parses a trees log, correctly escaping HTML and wrapping each BBStart..BBEnd 
    block in a uniquely identifiable div for precise highlighting.
    """
    
    # Escape log text first so Tree IL symbols are shown literally in the browser.
    escaped_content = html.escape(trees_content)

    # Match each BBStart...BBEnd region and capture its address for linking.
    block_pattern = re.compile(
        r'(n\d+n\s+BBStart.*?\[(0x[0-9a-f]+)\].*?n\d+n\s+BBEnd.*?)',
        re.DOTALL
    )

    def replace_with_div(match):
        """Wrap a BB block in a div with a stable id derived from its address."""
        block_text = match.group(1)
        address = match.group(2)
        return f'</div><div class="code-block" id="addr-{address}"><pre><code>{block_text}</code></pre></div><div class="code-block-unlinked"><pre><code>'

    # Replace each block and keep everything else in a plain unlinked container.
    processed_content = block_pattern.sub(replace_with_div, escaped_content)
    
    # Include any header text that appears before the first BBStart section.
    final_html = f'<div class="code-block-unlinked"><pre><code>{processed_content}</code></pre></div>'
    
    return final_html

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python trees_to_html.py <path_to_trees_log>")
        sys.exit(1)
        
    filepath = sys.argv[1]
    with open(filepath, 'r') as f:
        content = f.read()
        
    html_output = parse_trees_to_html(content)
    
    output_file = filepath.replace('.log', '.html')
    with open(output_file, 'w') as f:
        f.write(html_output)
    print(f"Successfully generated linkable HTML: {output_file}")
