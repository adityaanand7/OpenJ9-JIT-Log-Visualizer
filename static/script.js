document.addEventListener('DOMContentLoaded', () => {
    const svgContainer = document.querySelector('.svg-container');
    const codeContainer = document.querySelector('.code-container');
    const astView = document.querySelector('#ast-view');
    const astResetButton = document.querySelector('#ast-reset-btn');
    const prettyAstToggle = document.querySelector('#pretty-ast-toggle');
    let lastHighlightedTreeBlock = null;
    let lastHighlightedSvgNode = null;

    if (!svgContainer || !codeContainer || !astView) {
        // Home screen: no viewer panels yet.
        return;
    }

    function restoreRawTreeIL() {
        astView.hidden = true;
        astView.classList.remove('ast-active');
        astView.replaceChildren();
        codeContainer.hidden = false;
        if (astResetButton) astResetButton.hidden = true;
    }

    function createAstNode(node) {
        const item = document.createElement('li');
        item.className = 'ast-node';
        item.dataset.kind = node.kind;
        const depth = node.depth || 0;
        item.style.setProperty('--ast-depth', depth);

        const card = document.createElement('div');
        card.className = 'ast-node-card';
        card.style.marginLeft = `${depth * 32}px`;
        card.style.setProperty('--ast-branch-offset', `${Math.max(0, depth * 32 - 17)}px`);

        const badge = document.createElement('span');
        badge.className = 'ast-node-id';
        badge.textContent = node.id || 'ref';

        const operation = document.createElement('span');
        operation.className = 'ast-operation';
        operation.textContent = node.operation;

        const details = document.createElement('span');
        details.className = 'ast-details';
        details.textContent = node.details;

        card.append(badge, operation, details);
        card.dataset.astText = `${node.operation} ${node.details} ${node.metadata}`.toLowerCase();
        if (node.metadata) {
            card.classList.add('has-metadata');
            const tooltip = document.createElement('span');
            tooltip.className = 'ast-tooltip';
            tooltip.textContent = node.metadata;
            card.appendChild(tooltip);
        }
        item.appendChild(card);
        if (node.children.length) {
            const children = document.createElement('ul');
            children.className = 'ast-children';
            node.children.forEach((child) => children.appendChild(createAstNode(child)));
            item.appendChild(children);
        }
        if (node.footer) {
            const footer = document.createElement('div');
            footer.className = 'ast-footer';
            footer.textContent = `${node.footer.operation} ${node.footer.details}`.trim();
            item.appendChild(footer);
        }
        return item;
    }

    function parseTreeIL(text) {
        const rows = text.split(/\r?\n/)
            .map((line) => {
                const expanded = line.replace(/\t/g, '    ');
                const content = expanded.trim();
                const indent = expanded.length - expanded.trimStart().length;
                const marker = content.match(/^(n\d+n)\s+(.*)$/i);
                const body = marker ? marker[2] : content;
                const metadataStart = body.search(/\s+\[0x[0-9a-f]+\]/i);
                const statement = metadataStart >= 0 ? body.slice(0, metadataStart).trim() : body;
                const metadata = metadataStart >= 0 ? body.slice(metadataStart).trim() : '';
                const childCountMatch = metadata.match(/\bnc=(\d+)/i);
                const operationMatch = statement.match(/^(\S+)(?:\s+(.*))?$/);
                return {
                    indent,
                    id: marker ? marker[1] : '',
                    operation: operationMatch ? operationMatch[1] : body,
                    details: operationMatch && operationMatch[2] ? operationMatch[2] : '',
                    metadata,
                    childCount: childCountMatch ? Number(childCountMatch[1]) : null,
                    kind: /^(BBStart|BBEnd)$/i.test(operationMatch ? operationMatch[1] : '')
                        ? 'boundary'
                        : (/^==>/.test(operationMatch ? operationMatch[1] : '') ? 'reference' : 'operation'),
                    children: []
                };
            })
            .filter((row) => row.operation);

        const roots = [];
        let blockRoot = null;
        let blockRows = [];

        function makeTree(items) {
            const hasChildCounts = items.some((row) => row.childCount !== null);
            if (hasChildCounts) {
                const countRoots = [];
                const countStack = [];
                items.forEach((row) => {
                    while (countStack.length && countStack[countStack.length - 1].remaining === 0) {
                        countStack.pop();
                    }
                    row.depth = countStack.length + 1;
                    if (countStack.length) {
                        const parent = countStack[countStack.length - 1];
                        parent.node.children.push(row);
                        parent.remaining -= 1;
                    } else {
                        countRoots.push(row);
                    }
                    countStack.push({
                        node: row,
                        remaining: row.childCount === null ? 0 : row.childCount
                    });
                });
                return countRoots;
            }

            const indentationLevels = [...new Set(items.map((row) => row.indent))].sort((a, b) => a - b);
            const treeRoots = [];
            const stack = [];
            items.forEach((row) => {
                row.depth = indentationLevels.indexOf(row.indent) + 1;
                while (stack.length && row.depth <= stack[stack.length - 1].depth) stack.pop();
                if (stack.length) stack[stack.length - 1].children.push(row);
                else treeRoots.push(row);
                stack.push(row);
            });
            return treeRoots;
        }

        rows.forEach((row) => {
            const operation = row.operation.toLowerCase();
            if (operation === 'bbstart') {
                blockRoot = row;
                blockRows = [];
            } else if (operation === 'bbend') {
                if (blockRoot) {
                    blockRoot.children = makeTree(blockRows);
                    blockRoot.footer = row;
                    roots.push(blockRoot);
                } else {
                    roots.push(row);
                }
                blockRoot = null;
                blockRows = [];
            } else if (blockRoot) {
                blockRows.push(row);
            } else {
                roots.push(row);
            }
        });

        if (blockRoot) {
            blockRoot.children = makeTree(blockRows);
            roots.push(blockRoot);
        }
        return roots;
    }

    function showAstFor(targetElement) {
        const roots = parseTreeIL(targetElement.textContent || '');
        astView.replaceChildren();

        const heading = document.createElement('div');
        heading.className = 'ast-heading';
        heading.innerHTML = '<span>Basic block AST</span><small>Click another CFG block to switch</small>';
        astView.appendChild(heading);

        const tree = document.createElement('ul');
        tree.className = 'ast-tree';
        roots.forEach((root) => tree.appendChild(createAstNode(root)));
        astView.appendChild(tree);
        codeContainer.hidden = true;
        astView.hidden = false;
        astView.classList.add('ast-active');
        if (astResetButton) astResetButton.hidden = false;
        if (window.updateAstHighlights) {
            const active = Array.from(document.querySelectorAll('.highlight-opt:checked')).map((checkbox) => ({
                pattern: checkbox.getAttribute('data-pattern') || '',
                color: checkbox.getAttribute('data-color') || '',
                border: checkbox.getAttribute('data-border') || ''
            }));
            window.updateAstHighlights(active);
        }
    }

    window.updateAstHighlights = (active) => {
        astView.querySelectorAll('.ast-node-card').forEach((card) => {
            card.classList.remove('ast-highlight');
            card.style.removeProperty('background-color');
            card.style.removeProperty('border-left-color');
            const match = active.find((entry) => card.dataset.astText.indexOf(entry.pattern.toLowerCase()) !== -1);
            if (match) {
                card.classList.add('ast-highlight');
                card.style.backgroundColor = match.color;
                card.style.borderLeftColor = match.border;
            }
        });
    };

    if (astResetButton) astResetButton.addEventListener('click', restoreRawTreeIL);
    document.addEventListener('click', (event) => {
        if (!event.target.closest('.node') && !event.target.closest('#ast-view') && !event.target.closest('#ast-reset-btn')) {
            restoreRawTreeIL();
        }
    });

    svgContainer.addEventListener('click', (event) => {
        // Graphviz wraps each node in a <g class="node"> group.
        const nodeElement = event.target.closest('.node');

        if (!nodeElement) {
            return; // Exit if the click was not inside a node.
        }

        event.preventDefault(); // Keep URL clean when clicking SVG nodes.

        // Node ids are formatted as svg-node-for-0x..., which maps to Tree IL ids.
        const nodeId = nodeElement.id;
        if (nodeId && nodeId.startsWith('svg-node-for-')) {
            const address = nodeId.substring('svg-node-for-'.length);
            const targetId = `addr-${address}`;
            const targetElement = document.getElementById(targetId);

            // If there is a matching Tree IL block, highlight both sides.
            if (targetElement) {
                // Clear previous selection.
                if (lastHighlightedTreeBlock) {
                    lastHighlightedTreeBlock.classList.remove('highlight');
                }
                if (lastHighlightedSvgNode) {
                    lastHighlightedSvgNode.classList.remove('highlight-svg');
                }

                // Apply current selection.
                targetElement.classList.add('highlight');
                nodeElement.classList.add('highlight-svg');
                if (prettyAstToggle && prettyAstToggle.checked) {
                    showAstFor(targetElement);
                } else {
                    restoreRawTreeIL();
                }
                
                // Bring the selected block into view.
                targetElement.scrollIntoView({
                    behavior: 'smooth',
                    block: 'center'
                });

                // Keep references so the next click can clear highlights.
                lastHighlightedTreeBlock = targetElement;
                lastHighlightedSvgNode = nodeElement;

                // Parse basic metadata from Tree IL text into sidebar fields.
                try {
                    var treeText = (targetElement.textContent || '').trim();
                    // Block number: <block_7> => 7
                    var bbMatch = treeText.match(/<block_(\d+)>/i);
                    var bbNo = bbMatch ? bbMatch[1] : '';
                    // Frequency: (freq 0) or (freq: 0)
                    var freqMatch = treeText.match(/\(\s*freq\s*[:]?\s*(\d+)\s*\)/i);
                    var freq = freqMatch ? freqMatch[1] : '';
                    // Cold flag: either explicit (cold) or a cold token nearby.
                    var isCold = /\(\s*cold\s*\)|\bcold\b/i.test(treeText);

                    // Build a compact BCI range and treetop count.
                    var bciValues = [];
                    try{
                        var bciRe = /bci=\[([^\]]+)\]/gi;
                        var bm;
                        while((bm = bciRe.exec(treeText)) !== null){
                            var parts = bm[1].split(',').map(function(s){ return parseInt(s.trim(),10); }).filter(function(n){ return !isNaN(n); });
                            if(parts.length){
                                var mid = parts[Math.floor(parts.length/2)];
                                if(!isNaN(mid)) bciValues.push(mid);
                            }
                        }
                    }catch(e){ console.debug('BCI parse error', e); }

                    var bciRange = '-';
                    if(bciValues.length){
                        var mn = Math.min.apply(null, bciValues);
                        var mx = Math.max.apply(null, bciValues);
                        bciRange = (mn === mx) ? '[' + mn + ']' : '[' + mn + '-' + mx + ']';
                    }

                    var treetopCount = 0;
                    try{ treetopCount = (treeText.match(/treetop/gi) || []).length; }catch(e){}

                    // Push parsed values into the table.
                    function updateBBInfo(bb, frequency, coldFlag, bciRangeVal, treetopCnt){
                        var tbody = document.querySelector('.bbinfo table tbody');
                        if(!tbody) return;
                        var rows = tbody.querySelectorAll('tr');
                        // Expected order: BB_No, Frequency, Is_Cold, BCI_Range, TreeTop_Count.
                        if(rows.length >= 5){
                            try{ rows[0].children[2].textContent = bb || '-'; }catch(e){}
                            try{ rows[1].children[2].textContent = (frequency !== '') ? frequency : '-'; }catch(e){}
                            try{ rows[2].children[2].textContent = (coldFlag ? 'true' : 'false'); }catch(e){}
                            try{ rows[3].children[2].textContent = bciRangeVal || '-'; }catch(e){}
                            try{ rows[4].children[2].textContent = (typeof treetopCnt === 'number') ? String(treetopCnt) : '-'; }catch(e){}
                        } else if(rows.length >= 3){
                            // Fallback for older table layouts.
                            try{ rows[0].children[2].textContent = bb || '-'; }catch(e){}
                            try{ rows[1].children[2].textContent = (frequency !== '') ? frequency : '-'; }catch(e){}
                            try{ rows[2].children[2].textContent = (coldFlag ? 'true' : 'false'); }catch(e){}
                        }
                    }

                    updateBBInfo(bbNo, freq, isCold, bciRange, treetopCount);
                } catch (err) {
                    console.error('Failed to extract BB info from tree block', err);
                }
            }
        }

    });

    if (prettyAstToggle) {
        prettyAstToggle.addEventListener('change', () => {
            if (!prettyAstToggle.checked) {
                restoreRawTreeIL();
            } else if (lastHighlightedTreeBlock) {
                showAstFor(lastHighlightedTreeBlock);
            }
        });
    }
});
