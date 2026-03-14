document.addEventListener('DOMContentLoaded', () => {
    const svgContainer = document.querySelector('.svg-container');
    const codeContainer = document.querySelector('.code-container');
    let lastHighlightedTreeBlock = null;
    let lastHighlightedSvgNode = null;

    if (!svgContainer || !codeContainer) {
        // Home screen: no viewer panels yet.
        return;
    }

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
});
