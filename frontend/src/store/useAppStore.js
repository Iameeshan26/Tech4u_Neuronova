import { create } from 'zustand';

export const useAppStore = create((set) => ({
    activeJob: null,
    currentCity: 'berlin',
    isMapReady: false,
    setActiveJob: (job) => set({ activeJob: job }),
    setCity: (city) => set({ currentCity: city }),
    setMapReady: (ready) => set({ isMapReady: ready }),
}));
