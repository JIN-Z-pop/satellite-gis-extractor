/**
 * Satellite GIS Extractor - Main Application
 * Minimal version for WorldCover land cover extraction
 */

// Global state
let map = null;
let drawingManager = null;
let currentPolygon = null;

// Land cover classes
const LANDCOVER_CLASSES = {
    forest: { name: 'Forest', color: '#006400' },
    agriculture: { name: 'Agriculture', color: '#ffb432' },
    water: { name: 'Water', color: '#0064c8' },
    urban: { name: 'Urban', color: '#fa0000' },
    grassland: { name: 'Grassland', color: '#ffff00' },
    bare: { name: 'Bare land', color: '#b4b4b4' }
};

/**
 * Initialize the map (called by Google Maps API callback)
 */
function initMap() {
    // Default center (Tokyo)
    const center = { lat: 35.6762, lng: 139.6503 };

    map = new google.maps.Map(document.getElementById('map'), {
        center: center,
        zoom: 12,
        mapTypeId: 'hybrid',
        mapTypeControl: true,
        mapTypeControlOptions: {
            style: google.maps.MapTypeControlStyle.DROPDOWN_MENU,
            position: google.maps.ControlPosition.TOP_RIGHT
        }
    });

    // Drawing manager
    drawingManager = new google.maps.drawing.DrawingManager({
        drawingMode: google.maps.drawing.OverlayType.POLYGON,
        drawingControl: true,
        drawingControlOptions: {
            position: google.maps.ControlPosition.TOP_CENTER,
            drawingModes: [
                google.maps.drawing.OverlayType.POLYGON,
                google.maps.drawing.OverlayType.RECTANGLE
            ]
        },
        polygonOptions: {
            fillColor: '#3498db',
            fillOpacity: 0.3,
            strokeColor: '#2980b9',
            strokeWeight: 2,
            editable: true
        },
        rectangleOptions: {
            fillColor: '#3498db',
            fillOpacity: 0.3,
            strokeColor: '#2980b9',
            strokeWeight: 2,
            editable: true
        }
    });

    drawingManager.setMap(map);

    // Handle drawing complete
    google.maps.event.addListener(drawingManager, 'overlaycomplete', function(event) {
        // Remove previous polygon
        if (currentPolygon) {
            currentPolygon.setMap(null);
        }

        currentPolygon = event.overlay;
        drawingManager.setDrawingMode(null);

        updateStatus('Area selected. Click "Extract" to process.');
        document.getElementById('extract-btn').disabled = false;
    });

    updateStatus('Draw an area on the map to begin.');
}

// Alias for Google Maps callback
window.initializeIntegratedGIS = initMap;

/**
 * Get coordinates from the current polygon
 */
function getPolygonCoordinates() {
    if (!currentPolygon) return null;

    let path;
    if (currentPolygon.getPath) {
        // Polygon
        path = currentPolygon.getPath();
    } else if (currentPolygon.getBounds) {
        // Rectangle
        const bounds = currentPolygon.getBounds();
        const ne = bounds.getNorthEast();
        const sw = bounds.getSouthWest();
        return [
            [sw.lng(), sw.lat()],
            [ne.lng(), sw.lat()],
            [ne.lng(), ne.lat()],
            [sw.lng(), ne.lat()],
            [sw.lng(), sw.lat()]
        ];
    }

    const coords = [];
    path.forEach(function(latLng) {
        coords.push([latLng.lng(), latLng.lat()]);
    });

    // Close the polygon
    if (coords.length > 0 &&
        (coords[0][0] !== coords[coords.length-1][0] ||
         coords[0][1] !== coords[coords.length-1][1])) {
        coords.push(coords[0]);
    }

    return coords;
}

/**
 * Get selected classes
 */
function getSelectedClasses() {
    const checkboxes = document.querySelectorAll('.class-checkbox:checked');
    return Array.from(checkboxes).map(cb => cb.value);
}

/**
 * Extract land cover data
 */
async function extractData() {
    const coordinates = getPolygonCoordinates();
    if (!coordinates) {
        alert('Please draw an area on the map first.');
        return;
    }

    const classes = getSelectedClasses();
    if (classes.length === 0) {
        alert('Please select at least one land cover class.');
        return;
    }

    const outputFormat = document.querySelector('input[name="format"]:checked').value;

    showLoading(true);
    updateStatus('Processing... This may take a moment.');

    try {
        const response = await fetch(CONFIG.API_BASE_URL + '/gis_extraction_worldcover', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                coordinates: coordinates,
                classes: classes,
                output_format: outputFormat
            })
        });

        const data = await response.json();

        if (data.error) {
            throw new Error(data.error);
        }

        // Display statistics
        displayStatistics(data.statistics);

        // Show download button
        if (data.download_url) {
            const downloadBtn = document.getElementById('download-btn');
            // Construct full URL from API base
            const baseUrl = CONFIG.API_BASE_URL.replace('/api', '');
            downloadBtn.href = baseUrl + data.download_url;
            downloadBtn.style.display = 'inline-block';
            downloadBtn.textContent = `Download ${outputFormat.toUpperCase()}`;
        }

        updateStatus(`Extraction complete! Found ${data.feature_count} features.`);

    } catch (error) {
        console.error('Extraction error:', error);
        alert('Error: ' + error.message);
        updateStatus('Extraction failed. Please try again.');
    } finally {
        showLoading(false);
    }
}

/**
 * Display statistics in floating panel
 */
function displayStatistics(stats) {
    console.log('📊 Displaying statistics:', stats);

    const panel = document.getElementById('statistics-panel');
    const content = document.getElementById('stats-content');

    // Also update sidebar statistics
    const sidebarStats = document.getElementById('statistics');

    if (!panel || !content) {
        console.error('Statistics panel elements not found');
        return;
    }

    if (!stats || Object.keys(stats).length === 0) {
        content.innerHTML = '<p style="color: #666; text-align: center;">No data available</p>';
        panel.classList.add('visible');
        return;
    }

    let html = '';
    let totalAreaHa = 0;
    let totalAreaKm2 = 0;

    // Calculate total area
    for (const [className, classData] of Object.entries(stats)) {
        if (typeof classData === 'object' && classData.area_ha !== undefined) {
            totalAreaHa += classData.area_ha || 0;
        }
    }
    totalAreaKm2 = totalAreaHa / 100;

    // Summary section
    if (totalAreaHa > 0) {
        html += `
            <div class="stats-summary">
                <div class="stats-summary-label">Total Area</div>
                <div class="stats-summary-value">${totalAreaKm2.toFixed(2)} km²</div>
                <div class="stats-summary-sub">(${totalAreaHa.toFixed(2)} ha)</div>
            </div>
        `;
    }

    // Class breakdown
    for (const [className, classData] of Object.entries(stats)) {
        if (typeof classData !== 'object') continue;

        const classInfo = LANDCOVER_CLASSES[className] || {};
        const color = classInfo.color || '#666';
        const displayName = classInfo.name || className;
        const areaHa = classData.area_ha || 0;
        const areaKm2 = areaHa / 100;
        const percentage = classData.percentage || 0;

        html += `
            <div class="stat-item" style="border-left-color: ${color};">
                <div class="stat-item-header">
                    <span class="stat-item-name">${displayName}</span>
                    <span class="stat-item-percentage">${percentage.toFixed(1)}%</span>
                </div>
                <div class="stat-item-details">
                    <div class="stat-detail">
                        <strong>${areaKm2.toFixed(3)} km²</strong>
                    </div>
                    <div class="stat-detail">
                        <strong>${areaHa.toFixed(2)} ha</strong>
                    </div>
                </div>
            </div>
        `;
    }

    content.innerHTML = html;
    panel.classList.add('visible');

    // Also update sidebar (simpler table format)
    if (sidebarStats) {
        let tableHtml = '<h3>Land Cover Statistics</h3><table><tr><th>Class</th><th>Area (ha)</th><th>%</th></tr>';
        for (const [className, classData] of Object.entries(stats)) {
            if (typeof classData !== 'object') continue;
            const classInfo = LANDCOVER_CLASSES[className] || {};
            tableHtml += `<tr>
                <td>${classInfo.name || className}</td>
                <td>${(classData.area_ha || 0).toFixed(2)}</td>
                <td>${(classData.percentage || 0).toFixed(1)}%</td>
            </tr>`;
        }
        tableHtml += '</table>';
        sidebarStats.innerHTML = tableHtml;
        sidebarStats.style.display = 'block';
    }
}

/**
 * Toggle statistics panel minimize state
 */
function toggleStatsMinimize() {
    const panel = document.getElementById('statistics-panel');
    if (panel) {
        panel.classList.toggle('minimized');
    }
}

/**
 * Close statistics panel
 */
function closeStats() {
    const panel = document.getElementById('statistics-panel');
    if (panel) {
        panel.classList.remove('visible');
    }
}

/**
 * Clear the current selection
 */
function clearSelection() {
    if (currentPolygon) {
        currentPolygon.setMap(null);
        currentPolygon = null;
    }

    document.getElementById('extract-btn').disabled = true;
    document.getElementById('download-btn').style.display = 'none';
    document.getElementById('statistics').style.display = 'none';

    // Close floating statistics panel
    const statsPanel = document.getElementById('statistics-panel');
    if (statsPanel) {
        statsPanel.classList.remove('visible');
    }

    drawingManager.setDrawingMode(google.maps.drawing.OverlayType.POLYGON);
    updateStatus('Draw an area on the map to begin.');
}

/**
 * Update status message
 */
function updateStatus(message) {
    document.getElementById('status').textContent = message;
}

/**
 * Show/hide loading indicator
 */
function showLoading(show) {
    document.getElementById('loading').style.display = show ? 'flex' : 'none';
    document.getElementById('extract-btn').disabled = show;
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Event listeners
    document.getElementById('extract-btn').addEventListener('click', extractData);
    document.getElementById('clear-btn').addEventListener('click', clearSelection);
});
