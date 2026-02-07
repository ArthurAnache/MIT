import torch
import cv2
import pygame
import os
import scipy.io.wavfile as wavfile
from PIL import Image
from transformers import (
    MusicgenForConditionalGeneration, 
    AutoProcessor, 
    BlipProcessor, 
    BlipForConditionalGeneration
)

# Configuration de l'appareil (GPU/CUDA ou CPU)
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"--- Initialisation sur : {device.upper()} ---")

class MusicGenMVP:
    def __init__(self):
        # Chargement de MusicGen (Audio)
        print("Chargement de MusicGen (facebook/musicgen-large)...")
        self.audio_processor = AutoProcessor.from_pretrained("facebook/musicgen-large")
        self.audio_model = MusicgenForConditionalGeneration.from_pretrained("facebook/musicgen-large").to(device)
        
        # Chargement de BLIP (Vision)
        print("Chargement de l'analyseur visuel (Salesforce/blip)...")
        self.vision_processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
        self.vision_model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base").to(device)

    def analyze_media_to_text(self, path):
        """Prend une image ou une vidéo et retourne une description textuelle."""
        if not os.path.exists(path):
            return "A calm ambient melody"

        # Si c'est une vidéo, on extrait la frame du milieu
        if path.lower().endswith(('.mp4', '.avi', '.mov')):
            cap = cv2.VideoCapture(path)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            cap.set(cv2.CAP_PROP_POS_FRAMES, total_frames // 2)
            ret, frame = cap.read()
            cap.release()
            if not ret: return "cinematic orchestral music"
            image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        else:
            image = Image.open(path).convert("RGB")

        # Analyse Vision
        inputs = self.vision_processor(image, return_tensors="pt").to(device)
        out = self.vision_model.generate(**inputs)
        caption = self.vision_processor.decode(out[0], skip_special_tokens=True)
        
        # On enrichit le texte pour MusicGen
        return f"{caption}, cinematic background music, high quality, 4k"

    def generate_music_from_text(self, prompt_text, duration_seconds=10):
        """Génère la musique selon la documentation transformers."""
        print(f"Génération audio pour : {prompt_text}")
        
        inputs = self.audio_processor(
            text=[prompt_text],
            padding=True,
            return_tensors="pt",
        ).to(device)

        # Calcul des tokens (MusicGen génère 50 tokens par seconde environ)
        max_new_tokens = int(duration_seconds * 50)

        # Génération
        audio_values = self.audio_model.generate(**inputs, max_new_tokens=max_new_tokens)
        
        # Post-traitement et sauvegarde
        sampling_rate = self.audio_model.config.audio_encoder.sampling_rate
        # On détache du GPU et on convertit en numpy
        audio_data = audio_values[0, 0].cpu().numpy()
          
        output_file = "mvp_output.wav"
        wavfile.write(output_file, rate=sampling_rate, data=audio_data)
        print(f"✅ Musique sauvegardée sous : {output_file}")
        return output_file

def play_audio(file_path):
    """Fonction utilitaire pour jouer le fichier généré."""
    if not os.path.exists(file_path): return
    pygame.mixer.init()
    pygame.mixer.music.load(file_path)
    pygame.mixer.music.play()
    print("🎶 Lecture en cours... (Appuyez sur Ctrl+C pour arrêter)")
    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(10)

# --- TEST DU MOTEUR ---
if __name__ == "__main__":
    mvp = MusicGenMVP()
    
    # Étape 1 : Analyse (Remplace par le chemin d'une image ou vidéo réelle)
    # prompt = mvp.analyze_media_to_text("ma_video.mp4")
    prompt = "A sunset over a futuristic city, synthwave style"
    
    # Étape 2 : Génération (on demande 5 secondes pour le test)
    audio_file = mvp.generate_music_from_text(prompt, duration_seconds=5)
    
    # Étape 3 : Lecture
    play_audio(audio_file)