import os
import sqlite3
from flask import Flask, render_template, request, jsonify
from deepface import DeepFace
from werkzeug.utils import secure_filename
import numpy as np

# --- Flask App Setup ---
app = Flask(__name__)
UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# --- Database Setup ---
DB_NAME = "emotions.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS emotions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename TEXT,
                    dominant_emotion TEXT,
                    emotion_scores TEXT
                )''')
    conn.commit()
    conn.close()

init_db()

# --- Routes ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(filepath)

    try:
        # Analyze emotion using DeepFace
# Force DeepFace to use PyTorch backend
analysis = DeepFace.analyze(img_path=image_path, actions=['emotion'], enforce_detection=False, detector_backend='opencv')       
        dominant_emotion = analysis[0]['dominant_emotion']
        emotion_scores = {k: float(v) for k, v in analysis[0]['emotion'].items()}

        # Save result to database
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("INSERT INTO emotions (filename, dominant_emotion, emotion_scores) VALUES (?, ?, ?)",
                  (filename, dominant_emotion, str(emotion_scores)))
        conn.commit()
        conn.close()

        return jsonify({'dominant_emotion': dominant_emotion, 'scores': emotion_scores})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/records', methods=['GET'])
def records():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM emotions ORDER BY id DESC")
    rows = c.fetchall()
    conn.close()

    results = [{'id': row[0], 'filename': row[1], 'dominant_emotion': row[2], 'emotion_scores': row[3]} for row in rows]
    return jsonify(results)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
