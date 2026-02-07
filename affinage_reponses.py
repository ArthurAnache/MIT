# Input: audio, text. A small LLM handles 
# generating relevant questions.
# Goal: transform the audio to match the user's desires.

import os
# Fix TensorFlow/oneDNN message
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

from transformers import pipeline, AutoProcessor, MusicgenForConditionalGeneration
import torch
from PIL import Image
import scipy.io.wavfile as wavfile

# Image Generation imports
try:
    from diffusers import StableDiffusionPipeline
    HAS_DIFFUSERS = True
except (ImportError, AttributeError, Exception):
    HAS_DIFFUSERS = False

# Configuration and Constants
AUDIO_GENERE_PATH = "audio_genere.wav"
DEFAULT_INPUT_TEXT = "PARTY VIBE, upbeat tempo, synths, catchy melody, 8-bit style"

# Model cache to avoid reloading multiple times
MODELS_CACHE = {
    "music_model": None,
    "music_processor": None,
    "sd_pipe": None,
    "llm_pipe": None
}

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
DTYPE = torch.float16 if DEVICE == "cuda" else torch.float32

def get_music_model():
    if MODELS_CACHE["music_model"] is None:
        model_id = "facebook/musicgen-large"
        print(f"Loading FLAGSHIP MusicGen model ({model_id}) on {DEVICE}...")
        MODELS_CACHE["music_processor"] = AutoProcessor.from_pretrained(model_id)
        MODELS_CACHE["music_model"] = MusicgenForConditionalGeneration.from_pretrained(
            model_id, torch_dtype=DTYPE
        ).to(DEVICE)
    return MODELS_CACHE["music_model"], MODELS_CACHE["music_processor"]

def generate_initial_audio(texte, filename="audio_genere.wav"):
    """
    Generates music via MusicGen from a user-provided text.
    """
    model, processor = get_music_model()
    print(f"--- High Quality MusicGen Generation ({DEVICE}): {texte} ---")
    
    inputs = processor(text=[texte], padding=True, return_tensors="pt").to(DEVICE)

    # Audio sample generation (approx 10-15s)
    with torch.no_grad():
        audio_values = model.generate(**inputs, do_sample=True, guidance_scale=4, max_new_tokens=512)
    
    # Save to wav
    sampling_rate = model.config.audio_encoder.sampling_rate
    audio_data = audio_values[0, 0].cpu().numpy()
    
    wavfile.write(filename, rate=sampling_rate, data=audio_data)
    print(f"Music saved to: {filename}")
    return filename

def get_llm_pipe():
    if MODELS_CACHE["llm_pipe"] is None:
        model_id = "Qwen/Qwen2.5-0.5B-Instruct"
        print(f"Loading ultra-light LLM ({model_id}) on {DEVICE}...")
        MODELS_CACHE["llm_pipe"] = pipeline(
            "text-generation", 
            model=model_id, 
            torch_dtype=DTYPE,
            device_map="auto" if DEVICE == "cuda" else None
        )
    return MODELS_CACHE["llm_pipe"]

def extract_refinement_questions(audio_path, texte_initial):
    """
    Uses the LLM to generate relevant questions based on the produced audio and initial text.
    """
    pipe = get_llm_pipe()
    
    prompt = (
        f"The user provided the following text: '{texte_initial}'.\n"
        f"A music file was generated (file: {audio_path}).\n"
        "Ask 3 specific questions to the user to refine the musical aspects "
        "(tempo, instruments, emotion, structure) to improve the result. "
        "Be creative and vary your questions every time."
    )
    
    messages = [{"role": "user", "content": prompt}]
    result = pipe(messages, max_new_tokens=150, do_sample=True, temperature=0.9)
    return result[0]['generated_text']

def merge_musical_aspects(aspect_a, aspect_b, ratio=0.5):
    """
    Merges two descriptions or musical aspects.
    """
    return f"Mix of ({aspect_a}) and ({aspect_b}) with {ratio*100}% influence"

def extract_specific_frequencies(audio_path, bande="bass"):
    """
    Simulates extraction of a frequency band.
    """
    print(f"Extracting {bande} band from {audio_path}")
    return f"Stem_{bande}_{audio_path}"

def mix_stems(stem_melodie, stem_rythme, volume_rythme=1.0):
    """
    Merges specific musical components (Stems).
    """
    return f"Final Mix [Melody: {stem_melodie}, Rhythm: {stem_rythme} (vol:{volume_rythme})]"

def get_sd_pipe():
    if MODELS_CACHE["sd_pipe"] is None:
        model_id = "segmind/tiny-sd"
        print(f"Loading Tiny-SD ({model_id}) on {DEVICE}...")
        MODELS_CACHE["sd_pipe"] = StableDiffusionPipeline.from_pretrained(
            model_id, 
            torch_dtype=DTYPE
        ).to(DEVICE)
    return MODELS_CACHE["sd_pipe"]

def propose_visual_choices(prompt_musical):
    """
    Uses Stable Diffusion to generate images representing the musical mood.
    """
    print(f"--- Generating visuals for mood: {prompt_musical} ---")
    
    directions = {
        "1": {"label": "Urban/Dark", "prompt": f"Urban dark mood, cinematic, neon lights, 8k, inspired by {prompt_musical}"},
        "2": {"label": "Nature/Aerial", "prompt": f"Aerial nature landscape, ethereal, bright, wide angle, 8k, inspired by {prompt_musical}"},
    }

    if not HAS_DIFFUSERS:
        print("[Warning] 'diffusers' is not installed. Simulating display...")
        return directions["2"]["label"]

    pipe = get_sd_pipe()

    generated_paths = []
    for key, info in directions.items():
        print(f"Generating option {key}: {info['label']}...")
        image = pipe(info["prompt"], num_inference_steps=15).images[0]
        path = f"visual_choice_{key}.png"
        image.save(path)
        generated_paths.append(path)
        
        # Show image
        image.show()

    print("\nLook at the displayed images.")
    choix = input("Which mood does the user choose? (1 or 2): ")
    return directions.get(choix, directions["1"])["label"]

def refine_frequencies_and_instruments(musique_path, preferer_basse=False, instruments_favoris=[]):
    """
    Allows selecting or filtering certain aspects for the final mix.
    """
    instruments_str = ", ".join(instruments_favoris) if instruments_favoris else "standard mix"
    accent = "reinforced bass" if preferer_basse else "neutral balance"
    return f"Processed Audio ({musique_path}) - Instruments: {instruments_str} - {accent}"

def music_creation_pipeline(texte_entree):
    """
    Main pipeline: Text -> Audio -> Questions -> Feedback -> Visual Choice -> Fusion -> Final Audio
    """
    # 1. Initial Generation
    audio_brut = generate_initial_audio(texte_entree)
    
    # 2. Refinement Questions (LLM)
    print("\n[Step 2] Analyzing audio and preparing refinement questions...")
    # Now calling the real function
    questions = extract_refinement_questions(audio_brut, texte_entree)
    print(f"Generated Questions:\n{questions}")
    
    # User feedback simulation/request
    print(f"\nQuestions for you: \n{questions}")
    feedback_user = input("Your answer to refine the audio: ")
    if not feedback_user:
        feedback_user = "Add a synthesizer pad and slow down the tempo slightly."
    
    # 3. Visual Choice (Real Image Generation)
    direction_esthetique = propose_visual_choices(texte_entree)
    
    # 4. Fusion of feedback
    prompt_combine = f"{texte_entree}, {feedback_user}, {direction_esthetique} mood"
    print(f"\n[Step 4] New combined prompt: {prompt_combine}")
    
    # 5. Regeneration with full profile
    audio_raffine = generate_initial_audio(prompt_combine, filename="audio_raffine.wav")
    
    # 6. Final Selection/Filtering
    audio_final_info = refine_frequencies_and_instruments(
        audio_raffine, 
        preferer_basse=True, 
        instruments_favoris=["Piano", "Synthesizer"]
    )
    
    return audio_final_info

if __name__ == "__main__":
    print("=== STARTING HYBRID MUSICAL CREATION PIPELINE ===")
    resultat = music_creation_pipeline(DEFAULT_INPUT_TEXT)
    
    print("\n[Step 7] Technical Post-processing...")
    melodie = extract_specific_frequencies(AUDIO_GENERE_PATH, bande="high")
    rythme = extract_specific_frequencies(AUDIO_GENERE_PATH, bande="low")
    
    mix_final = mix_stems(melodie, rythme, volume_rythme=0.8)
    
    print(f"\n[FINAL RESULT]")
    print(f"Music Info: {resultat}")
    print(f"Technical Mix: {mix_final}")
    print("==========================================================")

