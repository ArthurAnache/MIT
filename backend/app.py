from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
from generator import MusicGeneratorSession
from lastfm_top_artists import main_lastfm_top_artists
from lastfm_top_tracks import main_lastfm_top_tracks
from lastfm_top_tracks_descriptions import main_lastfm_top_tracks_descriptions



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
@app.route('/api/trending/artists', methods=['GET'])
def trending_artists():
    geo = request.args.get("geo")  # ex: "United States" (ou None)
    limit = int(request.args.get("limit", 20))

    items = main_lastfm_top_artists(geo=geo, limit=limit)
    return jsonify({"items": items})


@app.route('/api/trending/tracks', methods=['GET'])
def trending_tracks():
    geo = request.args.get("geo")
    limit = int(request.args.get("limit", 20))

    items = main_lastfm_top_tracks(geo=geo, limit=limit)
    return jsonify({"items": items})


@app.route('/api/trending/tracks/descriptions', methods=['GET'])
def trending_tracks_descriptions():
    geo = request.args.get("geo")
    limit = int(request.args.get("limit", 20))

    items = main_lastfm_top_tracks_descriptions(geo=geo, limit=limit)
    return jsonify({"items": items})

@app.route('/outputs/<path:filename>')
def serve_file(filename):
    return send_from_directory(OUTPUT_DIR, filename)

if __name__ == "__main__":
    app.run(port=5000, debug=True)