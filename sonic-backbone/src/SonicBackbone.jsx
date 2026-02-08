import React, { useState, useRef, useEffect } from 'react';
import WaveSurfer from 'wavesurfer.js';
import { Upload, Play, Pause, Music, Activity, Cpu, Zap, Download, Mic, FileVideo, Sparkles, Command } from 'lucide-react';

/* --- COMPOSANTS INTERNES --- */

const MetricCard = ({ label, value, trend }) => (
    <div className="glass-panel p-6 rounded-2xl flex flex-col justify-between hover:bg-white/10 transition-colors duration-500 group">
        <div className="flex justify-between items-start mb-4">
            <span className="text-zinc-400 text-xs uppercase tracking-widest font-medium group-hover:text-white transition-colors">{label}</span>
            {trend && <span className="text-emerald-400 text-xs font-mono">{trend}</span>}
        </div>
        <div className="flex items-baseline gap-2">
            <span className="text-4xl font-light text-white tracking-tight text-glow">{value}</span>
        </div>
    </div>
);

const WaveformPlayer = ({ audioUrl }) => {
    const containerRef = useRef(null);
    const waveSurferRef = useRef(null);
    const [isPlaying, setIsPlaying] = useState(false);
    const [status, setStatus] = useState('loading'); // 'loading', 'ready', ou 'error'

    useEffect(() => {
        if (!containerRef.current) return;

        waveSurferRef.current = WaveSurfer.create({
            container: containerRef.current,
            waveColor: 'rgba(255, 255, 255, 0.2)',
            progressColor: '#a78bfa',
            cursorColor: '#ffffff',
            barWidth: 2,
            barGap: 4,
            responsive: true,
            height: 60,
            normalize: true,
            backend: 'WebAudio',
        });

        waveSurferRef.current.load(audioUrl);

        // Evenement : Succes
        waveSurferRef.current.on('ready', () => {
            setStatus('ready');
        });

        // Evenement : Erreur (Tres important pour deboguer)
        waveSurferRef.current.on('error', (err) => {
            console.error("Erreur WaveSurfer:", err);
            setStatus('error');
        });

        waveSurferRef.current.on('play', () => setIsPlaying(true));
        waveSurferRef.current.on('pause', () => setIsPlaying(false));

        return () => {
            if (waveSurferRef.current) waveSurferRef.current.destroy();
        };
    }, [audioUrl]);

    const togglePlay = () => {
        if (waveSurferRef.current && status === 'ready') {
            waveSurferRef.current.playPause();
        }
    };

    return (
        <div className="glass-panel rounded-3xl p-8 backdrop-blur-2xl border border-white/10">
            <div className="flex items-center justify-between mb-8">
                <div className="flex items-center gap-3">
                    <div className={`w-2 h-2 rounded-full ${status === 'ready' ? 'bg-emerald-500' :
                            status === 'error' ? 'bg-red-500' : 'bg-violet-500 animate-pulse'
                        }`}></div>
                    <h3 className="text-zinc-400 text-xs tracking-[0.2em] uppercase">
                        {status === 'ready' ? "Signal Ready" :
                            status === 'error' ? "Signal Error (Check Console)" : "Loading Signal..."}
                    </h3>
                </div>
            </div>

            <div ref={containerRef} className="w-full mb-8" />

            <div className="flex justify-center">
                <button
                    onClick={togglePlay}
                    disabled={status !== 'ready'}
                    className={`w-16 h-16 rounded-full flex items-center justify-center transition-all duration-300 ${status === 'ready' ? "bg-white text-black hover:scale-110" : "bg-zinc-800 text-zinc-600"
                        }`}
                >
                    {isPlaying ? <Pause size={28} fill="currentColor" /> : <Play size={28} fill="currentColor" className="ml-1" />}
                </button>
            </div>
        </div>
    );
};

const InputZone = ({ onGenerate, isGenerating }) => {
    const [dragActive, setDragActive] = useState(false);

    const handleDrag = (e) => {
        e.preventDefault();
        e.stopPropagation();
        if (e.type === "dragenter" || e.type === "dragover") {
            setDragActive(true);
        } else if (e.type === "dragleave") {
            setDragActive(false);
        }
    };

    return (
        <div className="space-y-6">
            <div
                onDragEnter={handleDrag}
                onDragLeave={handleDrag}
                onDragOver={handleDrag}
                onDrop={(e) => { e.preventDefault(); setDragActive(false); }}
                className={`group relative h-64 rounded-3xl transition-all duration-500 flex flex-col items-center justify-center cursor-pointer overflow-hidden border ${dragActive ? "border-violet-500 bg-violet-500/10" : "border-white/5 bg-white/5 hover:border-white/20 hover:bg-white/10"}`}
            >
                <div className="absolute inset-0 bg-gradient-to-br from-violet-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500" />

                <div className="relative z-10 flex flex-col items-center gap-4 p-8 text-center transition-transform duration-500 group-hover:scale-105">
                    <div className="w-16 h-16 rounded-full bg-white/5 flex items-center justify-center backdrop-blur-md mb-2 group-hover:shadow-[0_0_30px_rgba(139,92,246,0.3)] transition-shadow">
                        <Upload size={24} className="text-zinc-300 group-hover:text-white" />
                    </div>
                    <div>
                        <p className="text-lg font-light text-white mb-1">Drop Signals</p>
                        <p className="text-zinc-500 text-sm font-mono">MP4 . MOV . WAV</p>
                    </div>
                </div>
            </div>

            <div className="glass-panel rounded-2xl p-1">
                <div className="relative">
                    <div className="absolute left-4 top-4 text-zinc-500">
                        <Command size={16} />
                    </div>
                    <textarea
                        className="w-full bg-transparent text-white placeholder-zinc-600 focus:outline-none resize-none h-16 pl-10 pt-3 text-sm"
                        placeholder="Contextual parameters..."
                    ></textarea>
                </div>
            </div>

            <button
                onClick={onGenerate}
                disabled={isGenerating}
                className={`w-full py-5 rounded-2xl font-medium tracking-wider text-sm uppercase transition-all duration-500 flex items-center justify-center gap-3 relative overflow-hidden group ${isGenerating ? "bg-zinc-800 text-zinc-500 cursor-not-allowed" : "bg-white text-black"}`}
            >
                {isGenerating ? (
                    <> <Cpu className="animate-spin" size={18} /> Processing </>
                ) : (
                    <>
                        <span className="relative z-10 flex items-center gap-2">
                            Generate Backbone <Sparkles size={16} />
                        </span>
                        <div className="absolute inset-0 bg-violet-200 translate-y-full group-hover:translate-y-0 transition-transform duration-300" />
                    </>
                )}
            </button>
        </div>
    );
};

/* --- COMPOSANT PRINCIPAL --- */

const SonicBackbone = () => {
    const [hasGenerated, setHasGenerated] = useState(false);
    const [isGenerating, setIsGenerating] = useState(false);

    // Audio de demonstration
    const DEMO_AUDIO = "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3";

    const handleGenerate = () => {
        setIsGenerating(true);
        setTimeout(() => {
            setIsGenerating(false);
            setHasGenerated(true);
        }, 3000);
    };

    return (
        <div className="min-h-screen relative overflow-hidden bg-transparent selection:bg-violet-500/30 flex items-center justify-center">
            {/* Dynamic Background */}
            <div className="absolute inset-0 z-0 pointer-events-none">
                <div className="absolute top-[-10%] left-[-10%] w-[50%] h-[50%] bg-violet-900/20 rounded-full blur-[120px] animate-float opacity-60" />
                <div className="absolute bottom-[-10%] right-[-10%] w-[50%] h-[50%] bg-blue-900/10 rounded-full blur-[120px] animate-float-delayed opacity-60" />
                <div className="absolute top-[20%] right-[20%] w-[30%] h-[30%] bg-indigo-500/5 rounded-full blur-[100px]" />
            </div>

            <div className="relative z-10 w-full max-w-5xl mx-auto px-6 py-12">
                <header className="mb-16 flex flex-col items-center text-center">
                    <div className="mb-8 p-px bg-gradient-to-r from-transparent via-white/10 to-transparent w-full max-w-xs mx-auto" />
                    <h1 className="text-6xl md:text-8xl font-thin tracking-tighter mb-6 text-transparent bg-clip-text bg-gradient-to-b from-white via-white to-white/40 select-none">
                        SONIC AI
                    </h1>
                    <p className="text-zinc-500 text-lg font-light tracking-wide max-w-lg mx-auto">
                        Infrastructural sound generation from visual signals.
                    </p>
                </header>

                <main className="grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
                    <div className="lg:col-span-4 space-y-6">
                        <InputZone onGenerate={handleGenerate} isGenerating={isGenerating} />
                    </div>

                    <div className="lg:col-span-8 space-y-8">
                        {/* Metrics Grid */}
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                            <MetricCard label="Coherence" value={hasGenerated ? "98.4" : "0.0"} trend={hasGenerated ? "+4.2%" : null} />
                            <MetricCard label="Resonance" value={hasGenerated ? "100x" : "0x"} trend={hasGenerated ? "OPTIMAL" : null} />
                            <MetricCard label="Alignment" value={hasGenerated ? "A+" : "-"} />
                        </div>

                        {/* Result Section */}
                        <div className={`transition-all duration-1000 ease-out ${hasGenerated ? 'opacity-100 translate-y-0' : 'opacity-60 translate-y-4 hue-rotate-180 grayscale blur-sm'}`}>
                            {hasGenerated ? (
                                <WaveformPlayer audioUrl={DEMO_AUDIO} />
                            ) : (
                                <div className="glass-panel h-48 rounded-3xl flex flex-col items-center justify-center text-zinc-600 border-dashed border-zinc-800/50 relative overflow-hidden group">
                                    <div className="absolute inset-0 bg-gradient-to-tr from-transparent via-white/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-700 pointer-events-none" />
                                    <Activity className="w-6 h-6 opacity-20 mb-3 animate-pulse" />
                                    <p className="text-[10px] font-mono uppercase tracking-[0.3em] text-zinc-700">Waiting for signals...</p>
                                </div>
                            )}
                        </div>
                    </div>
                </main>

                <footer className="mt-20 text-center pointer-events-none opacity-50">
                    <p className="text-zinc-800 text-[10px] uppercase tracking-[0.4em] hover:text-zinc-600 transition-colors">System v2.0 // Ready</p>
                </footer>
            </div>
        </div>
    );
};

export default SonicBackbone;