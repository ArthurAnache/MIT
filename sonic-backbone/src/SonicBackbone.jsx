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

        // Configuration de l'instance
        const ws = WaveSurfer.create({
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

        waveSurferRef.current = ws;

        // Chargement sécurisé avec gestion d'erreur
        const loadAudio = async () => {
            try {
                await ws.load(audioUrl);
            } catch (err) {
                // On ignore l'erreur si elle vient d'une interruption volontaire (changement de page/composant)
                if (err.name === 'AbortError') {
                    console.log("Chargement audio annulé");
                } else {
                    console.error("Erreur WaveSurfer:", err);
                    setStatus('error');
                }
            }
        };

        loadAudio();

        // Evenement : Succes
        ws.on('ready', () => {
            if (waveSurferRef.current) setStatus('ready');
        });

        // Evenement : Erreur
        ws.on('error', (err) => {
            // Filtrage des erreurs d'annulation
            if (err.name !== 'AbortError') {
                console.error("Erreur WaveSurfer (on error):", err);
                setStatus('error');
            }
        });

        ws.on('play', () => setIsPlaying(true));
        ws.on('pause', () => setIsPlaying(false));

        // Nettoyage lors du démontage
        return () => {
            if (waveSurferRef.current) {
                try {
                    waveSurferRef.current.destroy();
                    waveSurferRef.current = null;
                } catch (e) {
                    // Ignore les erreurs lors de la destruction
                }
            }
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

const InputZone = ({ onGenerate, isGenerating, textInput, setTextInput }) => {
    const [dragActive, setDragActive] = useState(false);
    const [selectedFile, setSelectedFile] = useState(null); // Pour stocker le fichier
    const fileInputRef = useRef(null); // Pour ouvrir l'explorateur au clic

    const handleDrag = (e) => {
        e.preventDefault();
        e.stopPropagation();
        if (e.type === "dragenter" || e.type === "dragover") setDragActive(true);
        else if (e.type === "dragleave") setDragActive(false);
    };

    const handleDrop = (e) => {
        e.preventDefault();
        setDragActive(false);
        const file = e.dataTransfer.files[0];
        if (file) setSelectedFile(file);
    };

    const handleFileChange = (e) => {
        const file = e.target.files[0];
        if (file) setSelectedFile(file);
    };

    return (
        <div className="space-y-6">
            {/* Zone de Drop / Clic */}
            <div
                onDragEnter={handleDrag}
                onDragLeave={handleDrag}
                onDragOver={handleDrag}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current.click()} // Ouvre l'explorateur
                className={`group relative h-64 rounded-3xl transition-all duration-500 flex flex-col items-center justify-center cursor-pointer overflow-hidden border ${dragActive || selectedFile
                    ? "border-violet-500 bg-violet-500/10"
                    : "border-white/5 bg-white/5 hover:border-white/20 hover:bg-white/10"
                    }`}
            >
                <input
                    type="file"
                    ref={fileInputRef}
                    onChange={handleFileChange}
                    className="hidden"
                    accept="image/*,video/*,audio/*"
                />

                <div className="relative z-10 flex flex-col items-center gap-4 p-8 text-center transition-transform duration-500 group-hover:scale-105">
                    <div className="w-16 h-16 rounded-full bg-white/5 flex items-center justify-center backdrop-blur-md mb-2 group-hover:shadow-[0_0_30px_rgba(139,92,246,0.3)] transition-shadow">
                        <Upload size={24} className={selectedFile ? "text-violet-400" : "text-zinc-300"} />
                    </div>
                    <div>
                        <p className="text-lg font-light text-white mb-1">
                            {selectedFile ? "Signal Captured" : "Drop Signals"}
                        </p>
                        <p className="text-zinc-500 text-sm font-mono">
                            {selectedFile ? selectedFile.name : "JPG . PNG . MP4 . WAV"}
                        </p>
                    </div>
                </div>
            </div>

            {/* Zone de Texte (Textarea contrôlé) */}
            <div className="glass-panel rounded-2xl p-1 bg-white/5 border border-white/5">
                <div className="relative">
                    <div className="absolute left-4 top-4 text-zinc-500">
                        <Command size={16} />
                    </div>
                    <textarea
                        value={textInput}
                        onChange={(e) => setTextInput(e.target.value)}
                        className="w-full bg-transparent text-white placeholder-zinc-600 focus:outline-none resize-none h-16 pl-10 pt-3 text-sm"
                        placeholder="Contextual parameters..."
                    ></textarea>
                </div>
            </div>

            {/* Bouton de génération */}
            <button
                onClick={() => onGenerate(selectedFile)} // On envoie le fichier au parent
                disabled={isGenerating}
                className={`w-full py-5 rounded-2xl font-medium tracking-wider text-sm uppercase transition-all duration-500 flex items-center justify-center gap-3 relative overflow-hidden group ${isGenerating ? "bg-zinc-800 text-zinc-500 cursor-not-allowed" : "bg-white text-black"
                    }`}
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

const RefinementPanel = ({ questions, onSelect, disabled }) => {
    if (questions.length === 0) return null;

    return (
        <div className="mt-8 space-y-4 animate-in fade-in slide-in-from-bottom-4 duration-1000">
            <p className="text-zinc-500 text-[10px] uppercase tracking-[0.2em] mb-4">Refine Infrastructure</p>
            <div className="flex flex-wrap gap-3">
                {questions.map((q, i) => (
                    <button
                        key={i}
                        onClick={() => onSelect(q)}
                        disabled={disabled}
                        className="px-4 py-2 rounded-full border border-white/10 bg-white/5 text-zinc-300 text-sm hover:bg-violet-500/20 hover:border-violet-500/50 hover:text-white transition-all duration-300 disabled:opacity-50"
                    >
                        {q}
                    </button>
                ))}
            </div>
        </div>
    );
};

/* --- COMPOSANT PRINCIPAL --- */

const SonicBackbone = () => {
    const [questions, setQuestions] = useState([]);
    const [currentStep, setCurrentStep] = useState(0);
    const [audioUrl, setAudioUrl] = useState(null);
    const [hasGenerated, setHasGenerated] = useState(false);
    const [isGenerating, setIsGenerating] = useState(false);
    const [textInput, setTextInput] = useState("");

    // On indique simplement le nom du fichier avec un "/" devant. 
    // Vite comprend automatiquement qu'il doit chercher dans le dossier 'public'.
    const DEMO_AUDIO = "/musique.mp3";

    const handleGenerate = async (userInput = "") => {
        setIsGenerating(true);

        // CORRECTION : On s'assure que userInput est bien une chaîne de caractères.
        // Si userInput est un événement (objet), on utilise la valeur du state 'textInput' à la place.
        const cleanPrompt = typeof userInput === 'string' && userInput.length > 0
            ? userInput
            : textInput; // 'textInput' est votre variable d'état du textarea

        try {
            const response = await fetch('http://localhost:5000/generate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ user_input: cleanPrompt }),
            });

            const data = await response.json();

            if (data.questions) {
                let rawQuestions = "";

                // SECURITÉ : On vérifie si c'est du texte ou un objet
                if (typeof data.questions === 'string') {
                    rawQuestions = data.questions;
                } else if (typeof data.questions === 'object' && data.questions.content) {
                    rawQuestions = data.questions.content;
                }

                // On ne tente le .split() que si on a bien du texte
                if (rawQuestions) {
                    const qArray = rawQuestions
                        .split(/\d\./)
                        .filter(q => q.trim().length > 5)
                        .map(q => q.trim());
                    setQuestions(qArray);
                }
            }

            if (data.audio_url) {
                // On construit l'URL complète vers le serveur Flask
                // Le ?t= force le navigateur à recharger le son sans utiliser le cache
                setAudioUrl(`http://localhost:5000/${data.audio_url}?t=${Date.now()}`);

                // On récupère les questions découpées
                if (data.questions) {
                    const qArray = data.questions
                        .split(/\d\./)
                        .filter(q => q.trim().length > 5)
                        .map(q => q.trim());
                    setQuestions(qArray);
                }

                setHasGenerated(true);
                setCurrentStep(data.step);
            }
        } catch (error) {
            console.error("Erreur Backend:", error);
        } finally {
            setIsGenerating(false);
        }
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
                        <InputZone
                            onGenerate={handleGenerate}
                            isGenerating={isGenerating}
                            textInput={textInput}
                            setTextInput={setTextInput}
                        />
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
                                <div className="space-y-6">
                                    {/* Le lecteur audio */}
                                    <WaveformPlayer audioUrl={audioUrl} />

                                    {/* Nouveau : Les boutons de questions IA qui apparaissent sous le lecteur */}
                                    <RefinementPanel
                                        questions={questions}
                                        onSelect={(selectedQuestion) => handleGenerate(selectedQuestion)}
                                        disabled={isGenerating}
                                    />
                                </div>
                            ) : (
                                /* Ce qui s'affiche avant la génération */
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