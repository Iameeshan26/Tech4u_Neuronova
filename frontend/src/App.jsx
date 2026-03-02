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
          <div className="p-2 bg-blue-500/10 rounded-lg border border-blue-500/20">
            <Activity className="w-5 h-5 text-blue-400" />
          </div>
          <h1 className="text-lg font-bold tracking-tight">Neuronova<span className="text-blue-500">.</span>Pro</h1>
        </div>

        <div className="flex items-center gap-6">
          <div className="hidden md:flex items-center gap-4 text-[10px] font-bold uppercase tracking-widest text-slate-500">
            <div className="flex items-center gap-2">
              <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)]" />
              <span>API Gateway: Online</span>
            </div>
            <div className="flex items-center gap-2">
              <div className={`w-1.5 h-1.5 rounded-full ${status === 'optimizing' ? 'bg-blue-500 animate-pulse' : 'bg-slate-600'}`} />
              <span>Optimizer: {status === 'optimizing' ? 'Processing' : 'Standby'}</span>
            </div>
          </div>
          <div className="h-8 w-px bg-white/5" />
          <Settings className="w-5 h-5 text-slate-400 cursor-pointer hover:text-white transition-colors" />
        </div>
      </header>

      <main className="flex-1 relative flex flex-col p-4 gap-4">
        {/* Top Control Bar */}
        <div className="flex justify-between items-center px-2">
          <div>
            <h2 className="text-xl font-bold tracking-tight text-white uppercase italic">Fleet Overview</h2>
            <p className="text-[10px] text-slate-500 font-medium uppercase tracking-[0.2em]">Real-time logistics monitoring</p>
          </div>
          <button
            onClick={handleCheckJobs}
            disabled={status === 'optimizing'}
            className={`group relative px-8 py-4 overflow-hidden rounded-2xl font-black uppercase tracking-tighter text-sm transition-all duration-500 ${status === 'optimizing'
              ? 'bg-slate-800 text-slate-500 cursor-not-allowed'
              : 'bg-blue-600 text-white hover:bg-blue-500 hover:shadow-[0_0_30px_rgba(37,99,235,0.4)] active:scale-95'
              }`}
          >
            <div className="relative z-10 flex items-center gap-3">
              {status === 'optimizing' ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Sequencing...</span>
                </>
              ) : (
                <>
                  <Navigation className="w-4 h-4 group-hover:translate-x-1 group-hover:-translate-y-1 transition-transform" />
                  <span>Activate Optimizer</span>
                </>
              )}
            </div>
            {!status === 'optimizing' && <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent -translate-x-full group-hover:translate-x-full transition-transform duration-1000" />}
          </button>
        </div>

        {/* Map Container */}
        <div className="flex-1 relative rounded-3xl overflow-hidden shadow-[0_0_50px_rgba(0,0,0,0.5)] border border-white/5 bg-slate-900">
          <MapDisplay locations={locations} routes={routes} />

          {/* Dashboard Overlay */}
          <div className="absolute bottom-6 left-6 right-6 flex flex-col md:flex-row gap-4 pointer-events-none">
            {/* Stat Card 1 */}
            <div className="flex-1 bg-slate-950/80 backdrop-blur-xl border border-white/10 p-4 rounded-2xl pointer-events-auto shadow-2xl">
              <div className="flex items-center gap-3 mb-2">
                <Package className="w-4 h-4 text-blue-400" />
                <span className="text-[10px] font-black uppercase tracking-widest text-slate-500">Fleet Coverage</span>
              </div>
              <div className="flex items-baseline gap-2">
                <span className="text-3xl font-black tracking-tighter">{locations.length}</span>
                <span className="text-[10px] text-slate-400 font-bold uppercase">Nodes</span>
              </div>
              <div className="mt-2 h-1 w-full bg-white/5 rounded-full overflow-hidden">
                <div className="h-full bg-blue-500 w-3/4 shadow-[0_0_10px_rgba(59,130,246,0.5)]" />
              </div>
            </div>

            {/* Stat Card 2 */}
            <div className="flex-1 bg-slate-950/80 backdrop-blur-xl border border-white/10 p-4 rounded-2xl pointer-events-auto shadow-2xl">
              <div className="flex items-center gap-3 mb-2">
                <Activity className="w-4 h-4 text-emerald-400" />
                <span className="text-[10px] font-black uppercase tracking-widest text-slate-500">Efficiency Index</span>
              </div>
              <div className="flex items-baseline gap-2">
                <span className="text-3xl font-black tracking-tighter">{status === 'completed' ? '98.4' : '--.-'}</span>
                <span className="text-[10px] text-slate-400 font-bold uppercase">% Optimal</span>
              </div>
              <div className="mt-2 h-1 w-full bg-white/5 rounded-full overflow-hidden">
                <div className={`h-full ${status === 'completed' ? 'bg-emerald-500' : 'bg-slate-700'} w-full transition-all duration-1000`} />
              </div>
            </div>

            {/* Stat Card 3: AI Terminal */}
            <div className="flex-[1.5] bg-slate-950/80 backdrop-blur-xl border border-white/10 p-4 rounded-2xl pointer-events-auto shadow-2xl relative overflow-hidden">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-3">
                  <div className="w-2 h-2 rounded-full bg-blue-500 animate-pulse" />
                  <span className="text-[10px] font-black uppercase tracking-widest text-slate-500">System Intelligence</span>
                </div>
                <span className="text-[8px] font-mono text-blue-500/50">#X-99_LOG</span>
              </div>
              <div className="space-y-1 font-mono text-[9px] text-slate-400 leading-tight">
                <p className="text-emerald-500/70">{">"} Initializing node discovery...</p>
                <p>{status === 'optimizing' ? "> Processing demand matrix (OR-Tools)..." : "> Standby for sequence command."}</p>
                {status === 'completed' && <p className="text-blue-400">{">"} Optimization complete. Routes flushed to UI.</p>}
              </div>
              <div className="absolute top-0 right-0 p-2 opacity-5 pointer-events-none">
                <Activity className="w-20 h-20" />
              </div>
            </div>
          </div>
        </div>
      </main>

      <footer className="h-16 bg-slate-950 border-t border-white/5 flex items-center justify-between px-10">
        <div className="flex items-center gap-8 text-slate-600 italic font-black text-xs uppercase tracking-tighter">
          <span className="text-blue-500 underline decoration-2 underline-offset-4">Fleet</span>
          <span className="hover:text-slate-400 cursor-pointer">Matrix</span>
          <span className="hover:text-slate-400 cursor-pointer">Sensors</span>
        </div>
        <div className="text-[10px] font-mono text-slate-700 uppercase tracking-widest">
          © 2026 Neuronova Intelligence Systems // End_Transmission
        </div>
      </footer>
    </div>
  );
}

export default App;
