document.addEventListener('DOMContentLoaded', () => {
    // Initialize map
    const map = L.map('map', {
        zoomControl: true,
        attributionControl: false,
        preferCanvas: true // Use Canvas renderer for better performance and screenshot compatibility
    }).setView([9.38, 76.57], 12);

    // State
    let currentLevel = 'AC'; // AC, MANDAL, PANCHAYAT, WARD
    let currentLayer = null;
    let history = []; // Stack to track navigation
    let currentFilter = null; // Track current filter for history
    let currentLabel = 'Thiruvalla AC'; // Track current label for breadcrumbs

    // UI Elements
    const backBtn = document.createElement('button');
    backBtn.className = 'back-btn hidden';
    backBtn.innerHTML = '← Back';
    document.getElementById('app').appendChild(backBtn);

    const downloadLevelSelect = document.getElementById('download-level');
    const previewBtn = document.getElementById('preview-btn');
    const downloadBtn = document.getElementById('download-btn');
    const breadcrumbsContainer = document.getElementById('breadcrumbs');
    const legendContainer = document.getElementById('legend');

    // Check data
    if (typeof thiruvallaData === 'undefined') {
        console.error('Data not loaded');
        return;
    }

    // Update total stats
    document.getElementById('total-wards').textContent = thiruvallaData.wards.features.length;

    // Colors
    const colors = {
        'AC': '#f97316', // Orange 500
        'Thiruvalla': '#0ea5e9', // Sky 500
        'Mallappally': '#f97316', // Orange 500
        'default': '#94a3b8'
    };

    // Panchayat Colors (Unique for each LSGD)
    const panchayatColors = {
        'Thiruvalla': '#ef4444', // Red
        'Kuttoor': '#f59e0b', // Amber
        'Kadapra': '#84cc16', // Lime
        'Nedumpuram': '#10b981', // Emerald
        'Niranam': '#06b6d4', // Cyan
        'Peringara': '#3b82f6', // Blue
        'Kaviyoor': '#8b5cf6', // Violet
        'Kunnathanam': '#d946ef', // Fuchsia
        'Anicadu': '#f43f5e', // Rose
        'Kallooppara': '#14b8a6', // Teal
        'Mallappally': '#6366f1', // Indigo
        'Puramattom': '#ec4899'  // Pink
    };

    // Ward Palette (Cycle through these)
    const wardPalette = [
        '#ef4444', '#f97316', '#f59e0b', '#84cc16', '#10b981',
        '#06b6d4', '#3b82f6', '#6366f1', '#8b5cf6', '#d946ef',
        '#f43f5e', '#14b8a6'
    ];

    function getColor(props, level = currentLevel) {
        if (level === 'AC') return colors['AC'];
        if (level === 'MANDAL') return colors[props.Mandal] || colors['default'];
        if (level === 'PANCHAYAT') return panchayatColors[props.LSGD] || colors['default'];

        // Ward Level - Cycle based on Ward No
        if (level === 'WARD') {
            const wardNo = parseInt(props.Ward_No) || 0;
            return wardPalette[wardNo % wardPalette.length];
        }

        return colors['default'];
    }

    // Render Function
    function renderLevel(level, filterFn = null, label = null) {
        if (currentLayer) {
            map.removeLayer(currentLayer);
        }

        currentFilter = filterFn;
        if (label) currentLabel = label;

        const safeFilter = filterFn || (() => true);

        let data;
        if (level === 'AC') {
            data = thiruvallaData.ac;
        } else if (level === 'MANDAL') {
            data = thiruvallaData.mandals;
        } else if (level === 'PANCHAYAT') {
            data = {
                type: 'FeatureCollection',
                features: thiruvallaData.panchayats.features.filter(safeFilter)
            };
        } else if (level === 'WARD') {
            data = {
                type: 'FeatureCollection',
                features: thiruvallaData.wards.features.filter(safeFilter)
            };
        }

        // Update Legend
        updateLegend(data.features, level);

        currentLayer = L.geoJson(data, {
            style: (feature) => ({
                fillColor: getColor(feature.properties, level),
                weight: 2,
                opacity: 1,
                color: 'white',
                dashArray: '',
                fillOpacity: level === 'AC' ? 1 : 0.8
            }),
            onEachFeature: (feature, layer) => {
                layer.on({
                    mouseover: (e) => {
                        const l = e.target;
                        l.setStyle({ weight: 4, color: '#333', fillOpacity: 1 });
                        l.bringToFront();
                        if (level === 'WARD') updateInfoPanel(feature.properties);
                    },
                    mouseout: (e) => {
                        currentLayer.resetStyle(e.target);
                    },
                    click: (e) => {
                        handleInteraction(feature, layer);
                    }
                });

                // Labels
                if (level === 'AC') {
                    layer.bindTooltip("Thiruvalla AC", { permanent: true, direction: "center", className: "label-style" });
                } else if (level === 'MANDAL') {
                    layer.bindTooltip(feature.properties.Mandal, { permanent: true, direction: "center", className: "label-style" });
                } else if (level === 'PANCHAYAT') {
                    layer.bindTooltip(feature.properties.LSGD, { permanent: true, direction: "center", className: "label-style" });
                } else if (level === 'WARD') {
                    // Permanent label for Ward Name with Number
                    const no = feature.properties.Ward_No;
                    const name = feature.properties.Ward_Name;
                    const label = no && name ? `${no}. ${name}` : (name || no || '');

                    // Show permanent label only if filtered (not showing all)
                    if (filterFn) {
                        layer.bindTooltip(label, {
                            permanent: true,
                            direction: "center",
                            className: "ward-label-style"
                        });
                    } else {
                        // In preview/all mode: Show on click (Popup) and hover (Tooltip)
                        layer.bindPopup(label);
                        layer.bindTooltip(label, {
                            permanent: false,
                            direction: "center",
                            className: "ward-label-style"
                        });
                    }
                }
            }
        }).addTo(map);

        map.fitBounds(currentLayer.getBounds());
        updateUI();
        updateBreadcrumbs();
    }

    // Interaction Handler
    function handleInteraction(feature, layer) {
        if (currentLevel === 'AC') {
            // Drill down to Mandals
            history.push({ level: 'AC', filter: null, label: 'Thiruvalla AC' });
            currentLevel = 'MANDAL';
            renderLevel('MANDAL', null, 'Mandals');
        } else if (currentLevel === 'MANDAL') {
            // Drill down to Panchayats of specific Mandal
            const mandal = feature.properties.Mandal;
            history.push({ level: 'MANDAL', filter: null, label: mandal });
            currentLevel = 'PANCHAYAT';
            renderLevel('PANCHAYAT', f => f.properties.Mandal === mandal, 'Panchayats');
        } else if (currentLevel === 'PANCHAYAT') {
            // Drill down to Wards of specific Panchayat
            const lsgd = feature.properties.LSGD;
            const mandal = feature.properties.Mandal;
            history.push({ level: 'PANCHAYAT', filter: f => f.properties.Mandal === mandal, label: lsgd });
            currentLevel = 'WARD';
            renderLevel('WARD', f => f.properties.LSGD === lsgd, 'Wards');
        }
    }

    // Back Button Logic
    backBtn.addEventListener('click', () => {
        if (history.length > 0) {
            const prevState = history.pop();
            currentLevel = prevState.level;
            renderLevel(currentLevel, prevState.filter, prevState.label);
        }
    });

    // Download and Preview Logic
    previewBtn.addEventListener('click', () => {
        const selectedLevel = downloadLevelSelect.value;
        
        // Push current state to history so we can go back
        history.push({ level: currentLevel, filter: currentFilter, label: currentLabel });
        
        currentLevel = selectedLevel;
        
        // Render the selected level without any filters (show all)
        let label = 'Preview: ' + selectedLevel;
        if (selectedLevel === 'AC') label = 'Thiruvalla AC';
        if (selectedLevel === 'MANDAL') label = 'All Mandals';
        if (selectedLevel === 'PANCHAYAT') label = 'All Panchayats';
        if (selectedLevel === 'WARD') label = 'All Wards';

        renderLevel(selectedLevel, null, label);
    });

    function updateBreadcrumbs() {
        breadcrumbsContainer.innerHTML = '';
        
        // Add history items
        history.forEach((state, index) => {
            const item = document.createElement('span');
            item.className = 'breadcrumb-item';
            item.textContent = state.label || state.level;
            item.onclick = () => {
                // Go back to this state
                // We need to pop everything after this index
                const targetState = history[index];
                // Remove items from history stack
                history = history.slice(0, index);
                currentLevel = targetState.level;
                renderLevel(targetState.level, targetState.filter, targetState.label);
            };
            breadcrumbsContainer.appendChild(item);

            const separator = document.createElement('span');
            separator.className = 'breadcrumb-separator';
            separator.textContent = '>';
            breadcrumbsContainer.appendChild(separator);
        });

        // Add current item
        const current = document.createElement('span');
        current.className = 'breadcrumb-current';
        current.textContent = currentLabel;
        breadcrumbsContainer.appendChild(current);
    }

    function updateLegend(features, level) {
        legendContainer.innerHTML = '';
        legendContainer.classList.remove('hidden');

        const title = document.createElement('div');
        title.className = 'legend-title';
        title.textContent = level === 'WARD' ? 'Ward Legend' : 'Legend';
        legendContainer.appendChild(title);

        // Deduplicate features based on unique property
        const uniqueFeatures = [];
        const seen = new Set();

        features.forEach(f => {
            let key;
            if (level === 'AC') key = f.properties.Name;
            else if (level === 'MANDAL') key = f.properties.Mandal;
            else if (level === 'PANCHAYAT') key = f.properties.LSGD;
            else if (level === 'WARD') key = f.properties.Ward_No + '-' + f.properties.Ward_Name; // Unique ward

            if (!seen.has(key)) {
                seen.add(key);
                uniqueFeatures.push(f);
            }
        });

        // Sort features
        uniqueFeatures.sort((a, b) => {
            if (level === 'WARD') {
                return (parseInt(a.properties.Ward_No) || 0) - (parseInt(b.properties.Ward_No) || 0);
            }
            return 0;
        });

        uniqueFeatures.forEach(f => {
            const item = document.createElement('div');
            item.className = 'legend-item';

            const colorBox = document.createElement('div');
            colorBox.className = 'legend-color';
            colorBox.style.backgroundColor = getColor(f.properties, level);

            const text = document.createElement('span');
            if (level === 'AC') text.textContent = f.properties.Name;
            else if (level === 'MANDAL') text.textContent = f.properties.Mandal;
            else if (level === 'PANCHAYAT') text.textContent = f.properties.LSGD;
            else if (level === 'WARD') text.textContent = `${f.properties.Ward_No}. ${f.properties.Ward_Name}`;

            item.appendChild(colorBox);
            item.appendChild(text);
            legendContainer.appendChild(item);
        });
    }


    downloadBtn.addEventListener('click', async () => {
        const mapElement = document.getElementById('map');
        const selectedLevel = downloadLevelSelect.value;
        
        try {
            downloadBtn.textContent = 'Generating PDF...';
            downloadBtn.disabled = true;

            // 1. Capture Map Image
            const canvas = await html2canvas(mapElement, {
                useCORS: true,
                allowTaint: true,
                logging: false,
                scale: 2,
                scrollX: 0,
                scrollY: 0,
                backgroundColor: '#ffffff',
                ignoreElements: (element) => {
                    // Ignore zoom controls and legend in the screenshot
                    return element.classList.contains('leaflet-control-zoom') || 
                           element.classList.contains('map-legend');
                }
            });

            // 2. Initialize PDF
            const { jsPDF } = window.jspdf;
            const doc = new jsPDF({
                orientation: 'landscape',
                unit: 'mm',
                format: 'a4'
            });

            const pageWidth = doc.internal.pageSize.getWidth();
            const pageHeight = doc.internal.pageSize.getHeight();

            // 3. Add Heading and Map Image to Page 1
            doc.setFontSize(18);
            doc.setTextColor(40);
            doc.text(`Map of Thiruvalla AC at ${selectedLevel} Level`, pageWidth / 2, 15, { align: 'center' });

            const imgData = canvas.toDataURL('image/png');
            const imgProps = doc.getImageProperties(imgData);
            const pdfWidth = pageWidth - 20; // 10mm margin each side
            const pdfHeight = (imgProps.height * pdfWidth) / imgProps.width;
            
            // Center image vertically if possible, or just place it below title
            doc.addImage(imgData, 'PNG', 10, 25, pdfWidth, pdfHeight);

            // 4. Prepare Data for Table
            let tableData = [];
            let columns = [];
            let dataFeatures = [];

            // Get the correct dataset based on selection
            if (selectedLevel === 'AC') {
                dataFeatures = thiruvallaData.ac.features;
                columns = ['Color', 'Name', 'Level'];
                tableData = dataFeatures.map(f => [
                    '', // Color placeholder
                    f.properties.Name, 
                    f.properties.Level
                ]);
            } else if (selectedLevel === 'MANDAL') {
                dataFeatures = thiruvallaData.mandals.features;
                columns = ['Color', 'Mandal Name', 'Level'];
                tableData = dataFeatures.map(f => [
                    '',
                    f.properties.Mandal, 
                    f.properties.Level
                ]);
            } else if (selectedLevel === 'PANCHAYAT') {
                dataFeatures = thiruvallaData.panchayats.features;
                columns = ['Color', 'LSGD Name', 'Type', 'Mandal'];
                tableData = dataFeatures.map(f => [
                    '',
                    f.properties.LSGD, 
                    f.properties.Lsgd_Type, 
                    f.properties.Mandal
                ]);
            } else if (selectedLevel === 'WARD') {
                dataFeatures = thiruvallaData.wards.features;
                columns = ['Color', 'Ward No', 'Ward Name', 'LSGD Name', 'Mandal', 'District'];
                // Sort by Ward No
                dataFeatures.sort((a, b) => (parseInt(a.properties.Ward_No) || 0) - (parseInt(b.properties.Ward_No) || 0));
                tableData = dataFeatures.map(f => [
                    '',
                    f.properties.Ward_No,
                    f.properties.Ward_Name,
                    f.properties.LSGD,
                    f.properties.Mandal,
                    f.properties.District
                ]);
            }

            // 5. Add Table on New Page
            doc.addPage();
            doc.text(`Data Table - ${selectedLevel}`, 10, 15);
            
            doc.autoTable({
                head: [columns],
                body: tableData,
                startY: 20,
                theme: 'grid',
                headStyles: { fillColor: [37, 99, 235] }, // Primary color
                styles: { fontSize: 10, valign: 'middle' },
                columnStyles: {
                    0: { cellWidth: 15 } // Width for color column
                },
                didDrawCell: (data) => {
                    if (data.section === 'body' && data.column.index === 0) {
                        const rowIndex = data.row.index;
                        const feature = dataFeatures[rowIndex];
                        const color = getColor(feature.properties, selectedLevel);
                        
                        // Draw color rectangle
                        doc.setFillColor(color);
                        doc.rect(data.cell.x + 2, data.cell.y + 2, 11, data.cell.height - 4, 'F');
                    }
                }
            });

            // 6. Save PDF
            doc.save(`thiruvalla-map-${selectedLevel.toLowerCase()}.pdf`);

        } catch (err) {
            console.error('PDF generation failed:', err);
            alert('Failed to generate PDF');
        } finally {
            downloadBtn.textContent = 'Download Map';
            downloadBtn.disabled = false;
        }
    });

    function updateUI() {
        backBtn.classList.toggle('hidden', currentLevel === 'AC');
        document.getElementById('info-panel').classList.add('hidden'); // Hide info panel on transition
    }

    // Initial Render
    renderLevel('AC');

    // Info Panel Logic
    const infoPanel = document.getElementById('info-panel');
    const closeBtn = document.getElementById('close-panel');

    function updateInfoPanel(props) {
        document.getElementById('lsgd-name').textContent = props.LSGD || '-';
        document.getElementById('lsgd-type').textContent = props.Lsgd_Type || '-';
        document.getElementById('ward-name').textContent = props.Ward_Name || '-';
        document.getElementById('ward-no').textContent = props.Ward_No || '-';
        document.getElementById('district').textContent = props.District || '-';

        // Mandal info
        let blockRow = document.getElementById('block-row');
        if (!blockRow) {
            const container = document.querySelector('.panel-content');
            blockRow = document.createElement('div');
            blockRow.className = 'detail-row';
            blockRow.id = 'block-row';
            blockRow.innerHTML = '<span class="label">Mandal</span><span class="value" id="block-name">-</span>';
            const lsgdTypeRow = document.getElementById('lsgd-type').parentNode;
            lsgdTypeRow.parentNode.insertBefore(blockRow, lsgdTypeRow.nextSibling);
        } else {
            // Update label if needed
            blockRow.querySelector('.label').textContent = 'Mandal';
        }
        document.getElementById('block-name').textContent = props.Mandal || '-';

        infoPanel.classList.remove('hidden');
    }

    closeBtn.addEventListener('click', () => {
        infoPanel.classList.add('hidden');
    });
});
