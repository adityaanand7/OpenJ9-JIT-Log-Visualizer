import re
import sys
import html

def parse_trees_to_html(trees_content):
    """
    Parses a trees log, correctly escaping HTML and wrapping each BBStart..BBEnd 
    block in a uniquely identifiable div for precise highlighting.
    """
    
    # 1. Escape all HTML special characters (<, >, &) in the entire log first.
    # This prevents the browser from interpreting log syntax as HTML tags.
    escaped_content = html.escape(trees_content)

    # 2. Use a robust regex to find each complete block from BBStart to BBEnd.
    # - re.DOTALL allows '.' to match newlines.
    # - The '?' makes the '.*?' non-greedy, so it stops at the first BBEnd.
    # - It captures the memory address from the BBStart line.
    block_pattern = re.compile(
        r'(n\d+n\s+BBStart.*?\[(0x[0-9a-f]+)\].*?n\d+n\s+BBEnd.*?)',
        re.DOTALL
    )

    def replace_with_div(match):
        """A helper function to wrap a matched block with a div."""
        block_text = match.group(1)
        address = match.group(2)
        # This creates a self-contained div for each block.
        return f'</div><div class="code-block" id="addr-{address}"><pre><code>{block_text}</code></pre></div><div class="code-block-unlinked"><pre><code>'

    # 3. Apply the replacement to the escaped content.
    # We wrap everything in <pre><code> tags for proper formatting.
    processed_content = block_pattern.sub(replace_with_div, escaped_content)
    
    # Start with an opening tag for any content before the first block.
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
