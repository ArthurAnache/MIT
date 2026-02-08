from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
from generator import MusicGeneratorSession

app = Flask(__name__)
CORS(app) # Autorise React a parler a Python

# Dossier pour stocker les sons et images generes
OUTPUT_DIR = "outputs"
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

# Instance unique pour le test (ou gestion par session_id)
session = MusicGeneratorSession(session_id="default")

@app.route('/generate', methods=['POST'])
def generate():
    data = request.json
    user_input = data.get('user_input', '')
    
    # Appel de votre methode de generation
    result = session.advance_generation(user_input)
    
    # On renvoie les donnees au format JSON vers React
    return jsonify(result)

@app.route('/outputs/<path:filename>')
def serve_file(filename):
    return send_from_directory(OUTPUT_DIR, filename)

if __name__ == "__main__":
    app.run(port=5000, debug=True)