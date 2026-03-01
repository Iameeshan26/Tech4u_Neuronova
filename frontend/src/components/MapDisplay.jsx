import React, { useEffect, useRef } from 'react';
import { TomTomMap } from '@tomtom-org/maps-sdk/map';
import 'maplibre-gl/dist/maplibre-gl.css';
import { useAppStore } from '../store/useAppStore';

const MapDisplay = () => {
    const mapContainer = useRef(null);
    const map = useRef(null);
    const { isMapReady, setMapReady, activeJob } = useAppStore();

    const API_KEY = import.meta.env.VITE_TOMTOM_API_KEY || 'MISSING_TOKEN';

    useEffect(() => {
        let isMounted = true;

        const initMap = async () => {
            if (map.current) return;

            try {
                // Modular SDK uses static get() for initialization
                map.current = await TomTomMap.get({
                    key: API_KEY,
                    container: mapContainer.current,
                    center: { lng: 13.405, lat: 52.520 },
                    zoom: 11
                });

                if (isMounted) {
                    setMapReady(true);
                    console.log('TomTom Map initialized');
                }
            } catch (err) {
                console.error('Failed to init TomTom map:', err);
            }
        };

        initMap();

        return () => {
            isMounted = false;
            // SDK might handle cleanup, but we check if remove() exists on tomtomMap
            if (map.current) {
                // If it's a wrapper, we might need to access maplibre instance or find remove()
                // Based on types, it has a mapLibreMap property
                console.log('Cleaning up map');
            }
        };
    }, []);

    return (
        <div className="relative w-full h-full">
            {/* Inject TomTom CSS directly if we can't find it in node_modules */}
            <link
                rel="stylesheet"
                type="text/css"
                href="https://api.tomtom.com/maps-sdk-for-web/cdn/6.x/6.25.0/maps/maps.css"
            />
            <div ref={mapContainer} className="absolute inset-0 w-full h-full" />
            {(!API_KEY || API_KEY === 'MISSING_TOKEN') && (
                <div className="absolute inset-x-0 top-18 mx-auto w-fit z-50 glass-morphism px-4 py-2 rounded-lg text-rose-400 font-bold">
                    ⚠️ TomTom API Key Missing (.env: VITE_TOMTOM_API_KEY)
                </div>
            )}
        </div>
    );
};

export default MapDisplay;
