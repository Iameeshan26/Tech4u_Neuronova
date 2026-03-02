import { create } from 'zustand';

export const useAppStore = create((set) => ({
    activeJob: null,
    currentCity: 'berlin',
    isMapReady: false,
    locations: [],
    optimizationJob: null,
    routes: [],
    status: 'idle', // idle, loading, optimizing, completed, error

    setActiveJob: (job) => set({ activeJob: job }),
    setCity: (city) => set({ currentCity: city }),
    setMapReady: (ready) => set({ isMapReady: ready }),
    setLocations: (locations) => set({ locations }),
    setOptimizationJob: (job) => set({ optimizationJob: job }),
    setRoutes: (routes) => set({ routes }),
    setStatus: (status) => set({ status }),
}));
