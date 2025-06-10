from flask import Flask, request, jsonify
from flask_cors import CORS
from PIL import Image
import numpy as np
import tensorflow as tf
import mysql.connector
from datetime import datetime
import io
import os
import gdown

app = Flask(__name__)
CORS(app)

# === KONFIGURASI DATABASE ===
db = mysql.connector.connect(
    host="127.0.0.1",
    user="root",
    password="",  # Ganti sesuai password MySQL kamu
    database="mantapredict"
)
cursor = db.cursor()

# === KONFIGURASI MODEL ===
MODEL_PATH = "model/model_buah.h5"
DRIVE_ID = "1ZfRZXMj4qiBSRKookrB3SW5w_IWFrv-S"

# Cek dan download model jika belum ada
if not os.path.exists(MODEL_PATH):
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    print("Mengunduh model dari Google Drive...")
    gdown.download(f"https://drive.google.com/uc?id={DRIVE_ID}", MODEL_PATH, quiet=False)

# Load model
model = tf.keras.models.load_model(MODEL_PATH)

# === LABEL KELAS (sesuaikan dengan model) ===
labels = [
    'alpukat', 'anggur', 'apel', 'belimbing', 'blueberry', 'buah naga', 'ceri', 'delima', 'duku', 'durian',
    'jambu air', 'jambu biji', 'jeruk', 'kelapa', 'kiwi', 'kurma', 'leci', 'mangga', 'manggis', 'markisa',
    'melon', 'nanas', 'nangka', 'pepaya', 'pir', 'pisang', 'rambutan', 'salak', 'sawo', 'semangka',
    'sirsak', 'stroberi', 'tomat'
]

# === ROUTES ===

@app.route('/')
def index():
    return jsonify({"message": "API prediksi buah aktif!"})


@app.route('/predict', methods=['POST'])
def predict():
    if 'image' not in request.files:
        return jsonify({'error': 'No image uploaded'}), 400

    try:
        file = request.files['image']
        img = Image.open(file.stream).convert('RGB')
        img = img.resize((224, 224))  # Ukuran harus sesuai input model
        img_array = np.array(img) / 255.0
        img_array = np.expand_dims(img_array, axis=0)

        predictions = model.predict(img_array)
        class_index = int(np.argmax(predictions))
        confidence = float(np.max(predictions))
        predicted_label = labels[class_index]

        # Simpan ke database
        insert_query = "INSERT INTO predictions (label, confidence) VALUES (%s, %s)"
        cursor.execute(insert_query, (predicted_label, confidence))
        db.commit()

        return jsonify({
            'prediction': predicted_label,
            'confidence': confidence
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/history', methods=['GET'])
def history():
    cursor.execute("SELECT id, label, confidence, timestamp FROM predictions ORDER BY timestamp DESC")
    rows = cursor.fetchall()

    result = [
        {
            "id": row[0],
            "label": row[1],
            "confidence": row[2],
            "timestamp": row[3].isoformat()
        }
        for row in rows
    ]

    return jsonify(result)


# === MAIN ===
if __name__ == '__main__':
    app.run(debug=True)
