import os
import torch
import scipy.io.wavfile as wavfile
from transformers import pipeline, AutoProcessor, MusicgenForConditionalGeneration
from diffusers import StableDiffusionXLPipeline # Direct import to avoid MT5Tokenizer issue
from PIL import Image
from transformers import BlipProcessor, BlipForConditionalGeneration

# On garde le cache en dehors ou en attribut de classe pour ne pas recharger les modèles
MODELS_CACHE = {"music_model": None, "music_processor": None, "llm_pipe": None}
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
DTYPE = torch.float16 if DEVICE == "cuda" else torch.float32

class MusicGeneratorSession:
    def __init__(self, session_id):
        self.session_id = session_id
        self.step_counter = 0
        self.current_prompt = ""
        self.history = []
        self.last_audio_path = f"audio_{session_id}.wav"
        self.last_visual_options = []

        self.response_data = {
            "session_id": self.session_id,
            "audio_url": None,
            "questions": None,
            "image_choices": None,
            "step": self.step_counter,
            "message": ""
        }

        self.image=None
        
        # Chargement unique des modèles via la classe
        self._bootstrap_models()

    def _bootstrap_models(self):
        """Charge les modèles dans le cache s'ils ne sont pas présents."""
        if MODELS_CACHE["music_model"] is None:
            model_id = "facebook/musicgen-large"
            MODELS_CACHE["music_processor"] = AutoProcessor.from_pretrained(model_id)
            MODELS_CACHE["music_model"] = MusicgenForConditionalGeneration.from_pretrained(
                model_id, torch_dtype=DTYPE
            ).to(DEVICE)
            
        if MODELS_CACHE["llm_pipe"] is None:
            llm_id = "Qwen/Qwen2.5-0.5B-Instruct"
            MODELS_CACHE["llm_pipe"] = pipeline(
                "text-generation", model=llm_id, torch_dtype=DTYPE, device_map="auto"
            )
        
        if MODELS_CACHE.get("sd_pipe") is None:
            # Utilisation de SD-Turbo pour une génération quasi-instantanée
            MODELS_CACHE["sd_pipe"] = StableDiffusionXLPipeline.from_pretrained(
                "stabilityai/sdxl-turbo", torch_dtype=DTYPE, variant="fp16"
            ).to(DEVICE)

        if MODELS_CACHE.get("blip_model") is None:
            blip_id = "Salesforce/blip-image-captioning-base" # Modèle léger
            MODELS_CACHE["blip_processor"] = BlipProcessor.from_pretrained(blip_id)
            MODELS_CACHE["blip_model"] = BlipForConditionalGeneration.from_pretrained(
            blip_id, torch_dtype=DTYPE
        ).to(DEVICE)
    
    def analyze_image_symbolism(self, image_path):
        """
        Prend une image, la décrit, puis demande au LLM d'en extraire une symbolique musicale et émotionnelle.
        """

        model = MODELS_CACHE["blip_model"]
        processor = MODELS_CACHE["blip_processor"]
        llm = MODELS_CACHE["llm_pipe"] # On réutilise votre LLM Qwen
        
        # 1. Génération de la description factuelle (Captioning)
        raw_image = Image.open(image_path).convert('RGB')
        inputs = processor(raw_image, return_tensors="pt").to(DEVICE, DTYPE)
        
        out = model.generate(**inputs)
        description_visuelle = processor.decode(out[0], skip_special_tokens=True)
        
        # 2. Transformation en symbolique via le LLM
        prompt_symbolique = (
            f"Base description: '{description_visuelle}'. "
            "Provide a short symbolic interpretation of this image (emotion and musical mood). "
            "Format: Symbolism: [text] | Music Mood: [text]"
        )
        
        messages = [{"role": "user", "content": prompt_symbolique}]
        res = llm(messages, max_new_tokens=100, do_sample=True)
        interpretation = res[0]['generated_text']
        
        return description_visuelle + interpretation
    
    def generate_audio(self, prompt):
        """Appel au modèle MusicGen"""
        model = MODELS_CACHE["music_model"]
        processor = MODELS_CACHE["music_processor"]
        
        inputs = processor(text=[prompt], padding=True, return_tensors="pt").to(DEVICE)
        with torch.no_grad():
            audio_values = model.generate(**inputs, do_sample=True, guidance_scale=4, max_new_tokens=512)
        
        sampling_rate = model.config.audio_encoder.sampling_rate
        audio_data = audio_values[0, 0].cpu().numpy()
        wavfile.write(self.last_audio_path, rate=sampling_rate, data=audio_data)
        return self.last_audio_path

    def get_refinement_questions(self, prompt_actuel):
        """Appel au LLM pour générer des questions"""
        pipe = MODELS_CACHE["llm_pipe"]
        system_prompt = (
            f"The user wants: '{prompt_actuel}'. Ask 3 short, specific questions "
            "to refine tempo, instruments, or mood. Be concise."
        )
        messages = [{"role": "user", "content": system_prompt}]
        result = pipe(messages, max_new_tokens=100, do_sample=True)
        return result[0]['generated_text']
    
    def generate_visual_choices(self, music_prompt):
        """Génère 3 ambiances visuelles basées sur le prompt musical"""
        pipe = MODELS_CACHE["sd_pipe"]
        
        # On définit deux directions opposées pour donner du choix
        styles = [
            f"Abstract digital art, vibrant colors, energetic, representing {music_prompt}",
            f"Minimalist cinematic photography, moody, dark atmosphere, representing {music_prompt}",
            f"Stylized illustration, soft pastel tones, dreamy, representing {music_prompt}"
        ]
        
        image_paths = []
        for i, style_prompt in enumerate(styles):
            # 1 seul step suffit avec SD-Turbo pour un aperçu
            image = pipe(prompt=style_prompt, num_inference_steps=1, guidance_scale=0.0).images[0]
            path = f"static/choice_{self.session_id}_{i}.png"
            image.save(path)
            image_paths.append(path)
        
        self.last_visual_options = image_paths
        return image_paths
    
    def choose_visual_option(self, choice_index,images_paths):
        """L'utilisateur choisit une des options visuelles, on l'analyse pour affiner le prompt."""
        if 0 <= choice_index < len(images_paths):
            return images_paths[choice_index]
        else:
            raise ValueError("Invalid choice index")

    def advance_generation(self, user_input, image_path=None):#recupere image_path avec choose_visual_option issu de generate_visual_choices
        """
        Méthode principale : fait progresser le projet selon le compteur.
        """
        if self.step_counter == 0:
            # PREMIÈRE GÉNÉRATION
            if image_path:
                self.current_prompt = self.analyze_image_symbolism(image_path)+user_input
            else:
                self.current_prompt = user_input

            audio_path = self.generate_audio(self.current_prompt)
            questions = self.get_refinement_questions(self.current_prompt)
            
            self.step_counter += 1

            self.response_data.update({
                "audio_url": audio_path,
                "questions": questions,
                "step": self.step_counter,
                "message": "Première version générée. Répondez aux questions pour affiner."
            })

        elif self.step_counter >= 1:
            # AMÉLIORATION CONTINUE
            self.history.append(self.current_prompt)

            # On enrichit le prompt avec le feedback
            current_input=None
            if image_path:
                current_input = self.analyze_image_symbolism(image_path)+user_input
            else:
                current_input = user_input

            self.current_prompt = f"{self.current_prompt}, modified by: {current_input}"
            
            audio_path = self.generate_audio(self.current_prompt)
            # On peut décider de générer de nouvelles questions ou d'arrêter
            questions = self.get_refinement_questions(self.current_prompt)
            
            self.step_counter += 1
            self.response_data.update({
                "audio_url": audio_path,
                "questions": questions,
                "image_choices": self.generate_visual_choices(self.current_prompt) if self.step_counter == 2 else None,
                "step": self.step_counter,
                "message": f"Version {self.step_counter} prête !"
            })

        return self.response_data
    
if __name__ == "__main__":
    # Test rapide
    session = MusicGeneratorSession(session_id=1)
    result = session.advance_generation("I want a calm, relaxing music with piano and soft strings.")
    print(result)