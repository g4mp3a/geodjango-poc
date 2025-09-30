document.addEventListener('DOMContentLoaded', function() {
    // Initialize map with OpenStreetMap tiles
    const href = "https://www.openstreetmap.org/copyright";
    const link = `© <a href='${href}'>OpenStreetMap</a>`;
    const tiles = "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png";
    const baseLayer = L.tileLayer(tiles, { attribution: link });
    const map = L.map("map", { layers: [baseLayer] });

    // Layer references for clearing between searches
    let markersLayer = null;
    let radiusCircle = null;

    // Default view (USA center)
    map.setView([39.8283, -98.5795], 4);

    // Reset button functionality moved here from template
    const resetButton = document.getElementById('reset-search');
    if (resetButton) {
        resetButton.addEventListener('click', function() {
            window.location.href = '/';
        });
    }

    // Expose a renderer to be called with the API response
    window.renderMapResults = function(response) {
        try {
            const geo = response && response.geoJSON ? response.geoJSON : null;
            const center = response && response.search_center ? response.search_center : null;
            const radiusKm = response && typeof response.radius_km !== 'undefined' ? response.radius_km : 0;

            // Clear previous layers
            if (markersLayer) {
                map.removeLayer(markersLayer);
                markersLayer = null;
            }
            if (radiusCircle) {
                map.removeLayer(radiusCircle);
                radiusCircle = null;
            }

            // Add markers if present
            if (geo && geo.features && geo.features.length > 0) {
                markersLayer = L.geoJSON(geo, {
                    pointToLayer: function(feature, latlng) { return L.marker(latlng); },
                    onEachFeature: function(feature, layer) {
                        if (feature.properties && feature.properties.name) {
                            layer.bindPopup(`<b>${feature.properties.name}</b>`);
                        }
                    }
                }).addTo(map);
            }

            // Draw search radius if center provided
            if (center && typeof center.lat === 'number' && typeof center.lng === 'number' && radiusKm > 0) {
                const radiusMeters = radiusKm * 1000;
                radiusCircle = L.circle([center.lat, center.lng], {
                    radius: radiusMeters,
                    color: '#3388ff',
                    fillColor: '#3388ff',
                    fillOpacity: 0.2,
                    weight: 2
                }).addTo(map);
            }

            // Fit map to content
            if (markersLayer) {
                map.fitBounds(markersLayer.getBounds().pad(0.1));
                map.setZoom(map.getZoom() - 3.5);
            } else if (radiusCircle) {
                map.fitBounds(radiusCircle.getBounds().pad(0.1));
            } else {
                map.setView([39.8283, -98.5795], 4);
            }
        } catch (err) {
            console.error('Failed to render map results:', err);
        }
    };
});

