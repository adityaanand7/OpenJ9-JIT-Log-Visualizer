# OpenJ9 JIT Log Visualizer

A Flask-based web application for visualizing JIT (Just-In-Time) compiler logs produced by [Eclipse OpenJ9](https://github.com/eclipse-openj9/openj9). It parses raw JIT trace dump files, extracts per-method and per-optimization-pass data, and presents an interactive side-by-side view of the **Control Flow Graph (CFG)** and the **Tree Intermediate Language (Tree IL)** for each compiler pass.

## Features

- **Upload & Extract** — Upload a raw JIT dump file and specify a method name; the tool automatically extracts all optimization passes.
- **Side-by-Side View** — View the CFG (rendered as an interactive SVG) alongside the corresponding Tree IL for each pass.
- **Interactive Linking** — Click any node in the CFG to highlight and scroll to the matching basic block in the Tree IL panel.
- **Basic Block Info** — Sidebar table auto-populates with metadata (block number, frequency, cold flag, BCI range, treetop count) when a CFG node is selected.
- **Pattern Highlighting** — Toggle highlighting for specific IL patterns: object allocations (`jitNewObject`), heapification checks (`jitHeapifyStackObjectIfRequired`), and write barriers (`awrtbari`).
- **Resizable Panels** — Drag the divider between CFG and Tree IL panels to adjust their widths.
- **Collapsible Sidebar** — Hide/show the sidebar to maximize viewing area.

## Directory Structure

```
log_viewer/
├── app.py                        # Flask entry point (application factory)
├── routes.py                     # Blueprint with all routes and view logic
├── cfg_to_svg.py                 # Parses CFG logs → DOT → SVG via Graphviz
├── trees_to_html.py              # Parses Tree IL logs → annotated HTML
├── generate-tree-cfg.sh          # Shell script to orchestrate extraction
├── requirements.txt              # Python dependencies
├── .gitignore
│
├── tree-cfg-extractor/
│   ├── jit_cfg_extractor.py      # Extracts <trees> and <cfg> blocks from JIT dumps
│   └── jit_tree_extractor.py     # Alternative tree-only extractor (unused)
│
├── templates/
│   └── viewer.html               # Jinja2 template for the entire UI
│
├── static/
│   ├── style.css                 # Application styles
│   ├── script.js                 # Frontend interactivity (CFG↔Tree linking)
│   └── home-icon.svg             # Navigation icon
│
├── logs/                         # Generated per-pass log files (gitignored)
└── uploads/                      # User-uploaded JIT dump files (gitignored)
```

## Prerequisites

- **Python 3.8+**
- **Graphviz** — The `dot` command-line tool is required for rendering CFG graphs as SVG.

### Installing Graphviz

```bash
# Ubuntu/Debian
sudo apt install graphviz

# macOS
brew install graphviz

# Fedora/RHEL
sudo dnf install graphviz
```

## Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/adityaanand7/OpenJ9-JIT-Log-Visualizer.git
   cd OpenJ9-JIT-Log-Visualizer
   ```

2. **Create a virtual environment** (recommended)

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Verify Graphviz is available**

   ```bash
   dot -V
   ```

## Usage

### Starting the Application

```bash
python app.py
```

The server starts at `http://localhost:5000` in debug mode.

### Visualizing a JIT Dump

1. Open `http://localhost:5000` in your browser.
2. Click **Select file** and choose a raw OpenJ9 JIT trace dump file.
3. Select or type the full method signature (e.g., `Main.foo()V`) from the detected methods dropdown.
4. Click **Upload and Generate** — the extractor runs and populates the sidebar with all optimization passes.
5. Click any pass in the sidebar to view its CFG and Tree IL side by side.

Note: To generate log files use `-Xjit:traceFull,log=<log_name>` in your command line argument. 
### Interacting with the Viewer

- **Click a CFG node** to highlight and scroll to the corresponding basic block in the Tree IL panel. The Basic Block Info table in the sidebar updates with metadata.
- **Drag the divider** between CFG and Tree IL panels to resize them.
- **Use the Highlight dropdown** (top-right of Tree IL panel) to toggle pattern-based line highlighting.
- **Hide the sidebar** using the `✕` button to maximize the viewing area; bring it back with the `☰` button.


## License

This project is for research and educational purposes.
