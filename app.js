document.addEventListener('DOMContentLoaded', () => {
    // Initialize map
    const map = L.map('map', {
        zoomControl: true,
        attributionControl: false
    }).setView([9.38, 76.57], 12);

    // State
    let currentLevel = 'AC'; // AC, MANDAL, PANCHAYAT, WARD
    let currentLayer = null;
    let history = []; // Stack to track navigation

    // UI Elements
    const backBtn = document.createElement('button');
    backBtn.className = 'back-btn hidden';
    backBtn.innerHTML = '← Back';
    document.getElementById('app').appendChild(backBtn);

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

    function getColor(props) {
        if (currentLevel === 'AC') return colors['AC'];
        if (currentLevel === 'MANDAL') return colors[props.Mandal] || colors['default'];
        if (currentLevel === 'PANCHAYAT') return panchayatColors[props.LSGD] || colors['default'];

        // Ward Level - Cycle based on Ward No
        if (currentLevel === 'WARD') {
            const wardNo = parseInt(props.Ward_No) || 0;
            return wardPalette[wardNo % wardPalette.length];
        }

        return colors['default'];
    }

    // Render Function
    function renderLevel(level, filterFn = null) {
        if (currentLayer) {
            map.removeLayer(currentLayer);
        }

        let data;
        if (level === 'AC') {
            data = thiruvallaData.ac;
        } else if (level === 'MANDAL') {
            data = thiruvallaData.mandals;
        } else if (level === 'PANCHAYAT') {
            data = {
                type: 'FeatureCollection',
                features: thiruvallaData.panchayats.features.filter(filterFn)
            };
        } else if (level === 'WARD') {
            data = {
                type: 'FeatureCollection',
                features: thiruvallaData.wards.features.filter(filterFn)
            };
        }

        currentLayer = L.geoJson(data, {
            style: (feature) => ({
                fillColor: getColor(feature.properties),
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

                    layer.bindTooltip(label, {
                        permanent: true,
                        direction: "center",
                        className: "ward-label-style"
                    });
                }
            }
        }).addTo(map);

        map.fitBounds(currentLayer.getBounds());
        updateUI();
    }

    // Interaction Handler
    function handleInteraction(feature, layer) {
        if (currentLevel === 'AC') {
            // Drill down to Mandals
            history.push({ level: 'AC', filter: null });
            currentLevel = 'MANDAL';
            renderLevel('MANDAL');
        } else if (currentLevel === 'MANDAL') {
            // Drill down to Panchayats of specific Mandal
            const mandal = feature.properties.Mandal;
            history.push({ level: 'MANDAL', filter: null });
            currentLevel = 'PANCHAYAT';
            renderLevel('PANCHAYAT', f => f.properties.Mandal === mandal);
        } else if (currentLevel === 'PANCHAYAT') {
            // Drill down to Wards of specific Panchayat
            const lsgd = feature.properties.LSGD;
            const mandal = feature.properties.Mandal;
            history.push({ level: 'PANCHAYAT', filter: f => f.properties.Mandal === mandal });
            currentLevel = 'WARD';
            renderLevel('WARD', f => f.properties.LSGD === lsgd);
        }
    }

    // Back Button Logic
    backBtn.addEventListener('click', () => {
        if (history.length > 0) {
            const prevState = history.pop();
            currentLevel = prevState.level;
            renderLevel(currentLevel, prevState.filter);
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
