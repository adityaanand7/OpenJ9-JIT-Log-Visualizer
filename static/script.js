document.addEventListener('DOMContentLoaded', () => {
    const svgContainer = document.querySelector('.svg-container');
    const codeContainer = document.querySelector('.code-container');
    let lastHighlightedTreeBlock = null;
    let lastHighlightedSvgNode = null;

    if (!svgContainer || !codeContainer) {
        // If the main elements aren't on the page, do nothing.
        return;
    }

    svgContainer.addEventListener('click', (event) => {
        // Find the parent <g> element which Graphviz creates for each node.
        const nodeElement = event.target.closest('.node');

        if (!nodeElement) {
            return; // Exit if the click was not inside a node.
        }

        event.preventDefault(); // Stop the link from adding '#' to the URL.

        // **THE FIX IS HERE**: We parse the address from the node's ID.
        const nodeId = nodeElement.id;
        if (nodeId && nodeId.startsWith('svg-node-for-')) {
            const address = nodeId.substring('svg-node-for-'.length);
            const targetId = `addr-${address}`;
            const targetElement = document.getElementById(targetId);

            // If we found a matching block in the trees panel...
            if (targetElement) {
                // 1. Remove previous highlights.
                if (lastHighlightedTreeBlock) {
                    lastHighlightedTreeBlock.classList.remove('highlight');
                }
                if (lastHighlightedSvgNode) {
                    lastHighlightedSvgNode.classList.remove('highlight-svg');
                }

                // 2. Add new highlights.
                targetElement.classList.add('highlight');
                nodeElement.classList.add('highlight-svg');
                
                // 3. Scroll the trees panel to the highlighted block.
                targetElement.scrollIntoView({
                    behavior: 'smooth',
                    block: 'center'
                });

                // 4. Remember the currently highlighted elements.
                lastHighlightedTreeBlock = targetElement;
                lastHighlightedSvgNode = nodeElement;
            }
        }
    });
});
