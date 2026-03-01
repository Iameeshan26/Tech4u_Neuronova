import React from 'react';
import MapDisplay from './components/MapDisplay';
import { MapPin, Navigation, Package, Settings, Activity } from 'lucide-react';

function App() {
  return (
    <div className="flex flex-col h-screen w-full bg-slate-950 overflow-hidden font-sans">
      {/* Top Navigation / Status */}
      <header className="fixed top-0 inset-x-0 h-16 glass-morphism flex items-center justify-between px-6 z-40">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-blue-600/20 flex items-center justify-center border border-blue-500/50 shadow-[0_0_15px_rgba(59,130,246,0.3)]">
            <Activity className="w-5 h-5 text-blue-400" />
          </div>
          <div>
            <h1 className="text-lg font-bold tracking-tight text-white/90">Neuronova<span className="text-blue-500">.</span>Pro</h1>
            <p className="text-[10px] text-slate-400 font-medium tracking-widest uppercase">Mobile Fleet Portal</p>
          </div>
        </div>
        <button className="p-2.5 rounded-xl hover:bg-white/5 transition-colors border border-white/10 group">
          <Settings className="w-5 h-5 text-slate-400 group-hover:text-blue-400 transition-colors" />
        </button>
      </header>

      {/* Main Map View */}
      <main className="flex-1 w-full relative">
        <MapDisplay />

        {/* Floating overlays for Mobile-first look */}
        <div className="absolute bottom-32 right-6 flex flex-col gap-3">
          <button className="w-12 h-12 glass-morphism rounded-2xl flex items-center justify-center hover:scale-105 active:scale-95 transition-all">
            <Navigation className="w-5 h-5 text-blue-400" />
          </button>
        </div>

        {/* Bottom Drawer Overlay */}
        <div className="absolute bottom-6 inset-x-6 h-28 glass-morphism rounded-3xl p-5 flex items-center gap-5 transition-transform">
          <div className="w-16 h-16 rounded-2xl bg-emerald-500/20 flex items-center justify-center border border-emerald-500/50">
            <Package className="w-8 h-8 text-emerald-400" />
          </div>
          <div className="flex-1">
            <h3 className="font-bold text-white tracking-wide">Ready for Dispatch</h3>
            <p className="text-sm text-slate-400">Waiting for next optimized route...</p>
          </div>
          <button className="px-6 py-3 bg-blue-600 hover:bg-blue-500 text-white font-bold rounded-2xl shadow-[0_4px_20px_rgba(37,99,235,0.4)] transition-all hover:-translate-y-0.5 active:translate-y-0 text-sm">
            Check Jobs
          </button>
        </div>
      </main>

      {/* Bottom Bar Mobile tabs */}
      <footer className="h-20 bg-slate-900 border-t border-white/5 flex items-center justify-around px-8">
        <MapPin className="w-6 h-6 text-blue-500" />
        <Navigation className="w-6 h-6 text-slate-500 opacity-60" />
        <div className="w-1.5 h-1.5 rounded-full bg-blue-500 mt-6 absolute" />
      </footer>
    </div>
  );
}

export default App;
