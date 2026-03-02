import React, { useEffect, useCallback } from 'react';
import { useAppStore } from './store/useAppStore';
import { Activity, Settings, Package, Navigation, Loader2 } from 'lucide-react';
import { optimizeApi } from './api';
import MapDisplay from './components/MapDisplay';

function App() {
  const {
    locations, setLocations,
    status, setStatus,
    currentCity,
    routes,
    setRoutes,
    setOptimizationJob
  } = useAppStore();

  useEffect(() => {
    const fetchLocations = async () => {
      try {
        const response = await optimizeApi.getLocations();
        setLocations(response.data);
      } catch (err) {
        console.error('Failed to fetch locations:', err);
      }
    };
    fetchLocations();
  }, [setLocations]);

  const pollJobStatus = useCallback(async (jobId) => {
    const interval = setInterval(async () => {
      try {
        const response = await optimizeApi.getJobStatus(jobId);
        const { status: jobStatus, result } = response.data;

        if (jobStatus === 'completed') {
          clearInterval(interval);
          setRoutes(result.routes);
          setStatus('completed');
        } else if (jobStatus === 'failed') {
          clearInterval(interval);
          setStatus('error');
        }
      } catch (err) {
        clearInterval(interval);
        setStatus('error');
      }
    }, 2000);
  }, [setRoutes, setStatus]);

  const handleCheckJobs = async () => {
    if (locations.length === 0) return;
    setStatus('optimizing');
    try {
      const response = await optimizeApi.createJob(currentCity, locations);
      const { job_id } = response.data;
      setOptimizationJob(job_id);
      pollJobStatus(job_id);
    } catch (err) {
      setStatus('error');
    }
  };

  return (
    <div className="flex flex-col h-screen w-full bg-slate-950 overflow-hidden font-sans text-white">
      <header className="h-16 flex items-center justify-between px-6 border-b border-white/5 bg-slate-900/50 backdrop-blur-md z-40">
        <div className="flex items-center gap-3">
          <Activity className="w-5 h-5 text-blue-400" />
          <h1 className="text-lg font-bold tracking-tight">Neuronova<span className="text-blue-500">.</span>Pro</h1>
        </div>
        <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-white/5 border border-white/10">
          <div className={`w-2 h-2 rounded-full ${status === 'optimizing' ? 'bg-blue-500 animate-pulse' : status === 'completed' ? 'bg-emerald-500' : 'bg-slate-500'}`} />
          <span className="text-[10px] font-bold uppercase tracking-widest text-slate-400">{status}</span>
        </div>
        <Settings className="w-5 h-5 text-slate-400" />
      </header>

      <main className="flex-1 relative flex flex-col p-4">
        <div className="flex-1 relative rounded-2xl overflow-hidden shadow-2xl border border-white/5">
          <MapDisplay locations={locations} routes={routes} />
        </div>

        {/* Bottom Drawer Overlay */}
        <div className="absolute bottom-10 inset-x-10 h-28 bg-slate-900/90 backdrop-blur-2xl border border-white/10 rounded-3xl p-5 flex items-center gap-5 z-30 shadow-2xl transition-all hover:bg-slate-800/90">
          <div className="w-16 h-16 rounded-2xl bg-blue-500/10 flex items-center justify-center border border-blue-500/20">
            <Package className="w-8 h-8 text-blue-400" />
          </div>
          <div className="flex-1">
            <h3 className="font-bold text-white text-sm">Fleet Status</h3>
            <p className="text-xs text-slate-400 mt-1">
              {status === 'optimizing' ? 'Calculating routes...' :
                status === 'completed' ? `${routes.length} Optimized Routes Found` :
                  `${locations.length} Locations detected`}
            </p>
          </div>
          <button
            onClick={handleCheckJobs}
            disabled={status === 'optimizing'}
            className="px-6 py-3 bg-blue-600 hover:bg-blue-500 disabled:bg-slate-800 text-white font-bold rounded-2xl shadow-lg transition-all text-xs flex items-center gap-2"
          >
            {status === 'optimizing' && <Loader2 className="w-4 h-4 animate-spin" />}
            Check Jobs
          </button>
        </div>
      </main>

      <footer className="h-20 bg-slate-900 border-t border-white/5 flex items-center justify-around px-8">
        <Navigation className="w-6 h-6 text-blue-500" />
        <Package className="w-6 h-6 text-slate-500" />
      </footer>
    </div>
  );
}

export default App;
