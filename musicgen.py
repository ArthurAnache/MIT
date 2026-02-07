import torch
import torchaudio
from audiocraft.models import MusicGen
from audiocraft.data.audio import audio_write

def generate_music_from_text(prompt_text, duration_seconds):
    """
    Génère un fichier audio à partir d'un prompt textuel en utilisant MusicGen.
    """
    
    # 1. Vérification et gestion du matériel (GPU si disponible, sinon CPU)
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    print(f"Utilisation de l'appareil : {device}")

    # 2. Chargement du modèle MusicGen (version 'small' pour la rapidité du MVP)
    try:
        model = MusicGen.get_pretrained('facebook/musicgen-small', device=device)
    except Exception as e:
        print(f"Erreur lors du chargement du modèle : {e}")
        return

    # 3. Paramétrage de la durée de génération
    # Le modèle génère par défaut par morceaux, on fixe ici la limite
    model.set_generation_params(duration=duration_seconds)

    # 4. Échantillonnage / Génération
    print(f"Génération en cours pour : '{prompt_text}' ({duration_seconds}s)...")
    descriptions = [prompt_text]
    
    # generate() renvoie un tenseur [B, C, T] 
    # B=Batch, C=Channels (stéréo/mono), T=Time
    wav = model.generate(descriptions) 

    # 5. Sauvegarde du résultat
    # On itère sur le batch (ici une seule musique)
    for idx, one_wav in enumerate(wav):
        # audio_write ajoute automatiquement l'extension .wav
        # strategy='loudness' normalise le volume
        audio_write(
            f'generation_output_{idx}', 
            one_wav.cpu(), 
            model.sample_rate, 
            strategy="loudness"
        )
    
    print(f"Fichier 'generation_output_0.wav' sauvegardé avec succès.")

# --- Exemple d'utilisation ---
if __name__ == "__main__":
    mon_prompt = "A lo-fi hip hop beat with smooth piano and rain sounds, chill vibe"
    ma_duree = 10
    generate_music_from_text(mon_prompt, ma_duree)