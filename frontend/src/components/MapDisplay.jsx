import React, { useEffect, useRef } from 'react';
import maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';

const MapDisplay = ({ locations = [], routes = [] }) => {
    const mapElement = useRef(null);
    const map = useRef(null);
    const markers = useRef([]);
    const routeLayers = useRef([]);

    useEffect(() => {
        if (!mapElement.current || map.current) return;

        const apiKey = import.meta.env.VITE_TOMTOM_API_KEY;
        if (!apiKey) {
            console.error('TomTom API Key is missing');
            return;
        }

        console.log('Initializing MapLibre GL Map...');

        // Using a high-quality open style to ensure tiles are displayed correctly
        const styleUrl = 'https://tiles.openfreemap.org/styles/liberty';

        try {
            const mglMap = new maplibregl.Map({
                container: mapElement.current,
                style: styleUrl,
                center: [13.405, 52.52], // Default to Berlin
                zoom: 11,
                attributionControl: false
            });

            mglMap.addControl(new maplibregl.NavigationControl(), 'top-right');
            mglMap.addControl(new maplibregl.AttributionControl({ compact: true }));

            map.current = mglMap;
        } catch (error) {
            console.error('Failed to initialize MapLibre map:', error);
        }

        return () => {
            if (map.current) {
                console.log('Cleaning up MapLibre Map...');
                map.current.remove();
                map.current = null;
            }
        };
    }, []);

    // Update Markers
    useEffect(() => {
        if (!map.current) return;

        // Clear existing markers
        markers.current.forEach(marker => marker.remove());
        markers.current = [];

        if (locations.length > 0) {
            const bounds = new maplibregl.LngLatBounds();

            locations.forEach((loc) => {
                try {
                    const popup = new maplibregl.Popup({ offset: 25 })
                        .setHTML(`<b>Location ${loc.id}</b><br>Demand: ${loc.demand}`);

                    const marker = new maplibregl.Marker()
                        .setLngLat([loc.lon, loc.lat])
                        .setPopup(popup)
                        .addTo(map.current);

                    markers.current.push(marker);
                    bounds.extend([loc.lon, loc.lat]);
                } catch (err) {
                    console.error('Error adding marker:', err);
                }
            });

            if (!bounds.isEmpty()) {
                map.current.fitBounds(bounds, { padding: 50 });
            }
        }
    }, [locations]);

    // Update Routes
    useEffect(() => {
        if (!map.current || !routes || routes.length === 0) return;

        // Clear existing route layers and sources
        routeLayers.current.forEach(layerId => {
            if (map.current.getLayer(layerId)) map.current.removeLayer(layerId);
            if (map.current.getSource(layerId)) map.current.removeSource(layerId);
        });
        routeLayers.current = [];

        const colors = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899'];

        routes.forEach((route, index) => {
            if (!route.path || route.path.length === 0) return;

            const layerId = `route-${index}`;
            const color = colors[index % colors.length];

            // GeoJSON coordinates [lon, lat]
            const coordinates = route.path.map(point => [point[1], point[0]]);

            try {
                map.current.addSource(layerId, {
                    'type': 'geojson',
                    'data': {
                        'type': 'Feature',
                        'properties': {},
                        'geometry': {
                            'type': 'LineString',
                            'coordinates': coordinates
                        }
                    }
                });

                map.current.addLayer({
                    'id': layerId,
                    'type': 'line',
                    'source': layerId,
                    'layout': {
                        'line-join': 'round',
                        'line-cap': 'round'
                    },
                    'paint': {
                        'line-color': color,
                        'line-width': 4,
                        'line-opacity': 0.8
                    }
                });

                routeLayers.current.push(layerId);
            } catch (err) {
                console.error('Error adding route layer:', err);
            }
        });
    }, [routes]);

    return (
        <div
            ref={mapElement}
            className="w-full h-[600px] min-h-[600px] bg-slate-900 rounded-2xl overflow-hidden border-2 border-blue-500/10 shadow-inner"
        />
    );
};

export default MapDisplay;
