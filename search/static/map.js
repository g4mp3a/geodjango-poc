document.addEventListener('DOMContentLoaded', function() {
    // Initialize map with OpenStreetMap tiles
    const href = "https://www.openstreetmap.org/copyright";
    const link = `© <a href='${href}'>OpenStreetMap</a>`;
    const tiles = "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png";
    const layer = L.tileLayer(tiles, { attribution: link });
    const map = L.map("map", { layers: [layer] });
    
    // Parse markers data
    const markersData = JSON.parse(document.getElementById("markers").textContent);

    // Add markers if they exist
    if (markersData.features && markersData.features.length > 0) {
        const markers = L.geoJSON(markersData, {
            pointToLayer: function(feature, latlng) {
                return L.marker(latlng);
            },
            onEachFeature: function(feature, layer) {
                if (feature.properties && feature.properties.name) {
                    layer.bindPopup(`<b>${feature.properties.name}</b>`);
                }
            }
        }).addTo(map);

        // If we have search parameters, add a circle to show the search area
        if (window.SEARCH_CENTER && window.SEARCH_RADIUS_KM) {
            const center = L.latLng(window.SEARCH_CENTER.lat, window.SEARCH_CENTER.lng);
            const radius = window.SEARCH_RADIUS_KM * 1000; // Convert km to meters

            L.circle(center, {
                radius: radius,
                color: '#3388ff',
                fillColor: '#3388ff',
                fillOpacity: 0.2,
                weight: 2
            }).addTo(map);
        }
        map.fitBounds(markers.getBounds().pad(0.1));
        map.setZoom(map.getZoom() - 3.5);
    } else {
        // No markers, set default view
        map.setView([39.8283, -98.5795], 4); // Center of US
    }
});
