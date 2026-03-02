import * as tt from '@tomtom-org/maps-sdk/map';
import 'maplibre-gl/dist/maplibre-gl.css';

const MapDisplay = ({ locations = [], routes = [] }) => {
    const mapElement = useRef(null);
    const map = useRef(null);
    const markers = useRef([]);
    const routeLayers = useRef([]);

    useEffect(() => {
        const apiKey = import.meta.env.VITE_TOMTOM_API_KEY;
        if (!apiKey) {
            console.error('TomTom API Key is missing');
            return;
        }

        const ttMap = tt.map({
            key: apiKey,
            container: mapElement.current,
            center: [13.405, 52.52], // Default to Berlin
            zoom: 11,
            stylesVisibility: {
                trafficIncidents: true,
                trafficFlow: true
            }
        });

        ttMap.addControl(new tt.NavigationControl());
        map.current = ttMap;

        return () => ttMap.remove();
    }, []);

    // Update Markers
    useEffect(() => {
        if (!map.current) return;

        // Clear existing markers
        markers.current.forEach(marker => marker.remove());
        markers.current = [];

        if (locations.length > 0) {
            const bounds = new tt.LngLatBounds();

            locations.forEach((loc) => {
                const marker = new tt.Marker()
                    .setLngLat([loc.lon, loc.lat])
                    .setPopup(new tt.Popup({ offset: 35 }).setHTML(`<b>Location ${loc.id}</b><br>Demand: ${loc.demand}`))
                    .addTo(map.current);

                markers.current.push(marker);
                bounds.extend([loc.lon, loc.lat]);
            });

            if (!bounds.isEmpty()) {
                map.current.fitBounds(bounds, { padding: 50 });
            }
        }
    }, [locations]);

    // Update Routes
    useEffect(() => {
        if (!map.current || !routes || routes.length === 0) return;

        // Clear existing route layers
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

            // TomTom SDK expects [lon, lat] for Geospatial data in GeoJSON
            const coordinates = route.path.map(point => [point[1], point[0]]);

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
        });
    }, [routes]);

    return (
        <div
            ref={mapElement}
            className="w-full h-full bg-slate-900 rounded-2xl overflow-hidden border border-white/5"
            style={{ minHeight: '400px' }}
        />
    );
};

export default MapDisplay;
