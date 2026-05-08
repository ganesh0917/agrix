"""
AGRIX Rot Detection API Server
REST API for rot detection integrated with Dashboard
Connects ESP32 camera feed to ML model
"""

from flask import Flask, request, jsonify, send_file
from werkzeug.utils import secure_filename
import os
import json
from datetime import datetime
from pathlib import Path
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.image import load_img, img_to_array
from PIL import Image
import io
import firebase_admin
from firebase_admin import credentials, db, storage
import threading
import logging

# Setup Flask app
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = './uploads/'
app.config['RESULTS_FOLDER'] = './detection_results/'

# Setup directories
Path(app.config['UPLOAD_FOLDER']).mkdir(parents=True, exist_ok=True)
Path(app.config['RESULTS_FOLDER']).mkdir(parents=True, exist_ok=True)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('./Fruit_Vegetable_Recognition-master/logs/api_server.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Global model
MODEL = None
MODEL_PATH = './Fruit_Vegetable_Recognition-master/models/agrix_rot_detection_v1.h5'
CLASSES = ['fresh', 'rotten']

# Configuration
FIREBASE_CONFIG = {
    'apiKey': "YOUR_API_KEY",
    'authDomain': "agrix-3703d.firebaseapp.com",
    'databaseURL': "https://agrix-3703d-default-rtdb.firebaseio.com",
    'projectId': "agrix-3703d",
    'storageBucket': "agrix-3703d.appspot.com",
    'messagingSenderId': "YOUR_MESSAGING_ID",
    'appId': "YOUR_APP_ID"
}


def load_ml_model():
    """Load pre-trained model"""
    global MODEL
    
    if MODEL is not None:
        return MODEL
    
    if os.path.exists(MODEL_PATH):
        try:
            MODEL = load_model(MODEL_PATH)
            logger.info(f"✓ Model loaded: {MODEL_PATH}")
            return MODEL
        except Exception as e:
            logger.error(f"✗ Failed to load model: {e}")
            return None
    else:
        logger.warning(f"⚠️  Model not found at {MODEL_PATH}")
        return None


def preprocess_image(image_path, target_size=(224, 224)):
    """Preprocess image for model"""
    try:
        img = load_img(image_path, target_size=target_size)
        img_array = img_to_array(img)
        img_array = img_array / 255.0
        img_array = np.expand_dims(img_array, axis=0)
        return img_array
    except Exception as e:
        logger.error(f"Error preprocessing image: {e}")
        return None


def classify_image(image_path):
    """Classify image for freshness"""
    model = load_ml_model()
    
    if model is None:
        return {'error': 'Model not loaded'}
    
    try:
        # Preprocess
        img_array = preprocess_image(image_path)
        if img_array is None:
            return {'error': 'Failed to preprocess image'}
        
        # Predict
        predictions = model.predict(img_array, verbose=0)
        class_idx = np.argmax(predictions[0])
        confidence = float(predictions[0][class_idx])
        class_label = CLASSES[class_idx]
        
        result = {
            'success': True,
            'classification': class_label,
            'confidence': confidence,
            'freshness_score': float((1 - predictions[0][1]) * 100),
            'probabilities': {
                'fresh': float(predictions[0][0]),
                'rotten': float(predictions[0][1])
            },
            'timestamp': datetime.now().isoformat(),
            'recommendation': 'Consume immediately' if class_label == 'fresh' else 'Discard or use for processing'
        }
        
        return result
    
    except Exception as e:
        logger.error(f"Error classifying image: {e}")
        return {'error': str(e)}


@app.route('/', methods=['GET'])
def index():
    """API status and info"""
    return jsonify({
        'service': 'AGRIX Rot Detection API',
        'version': '1.0.0',
        'status': 'running',
        'model_loaded': MODEL is not None,
        'endpoints': {
            'POST /classify': 'Upload image and get rot detection',
            'POST /classify-url': 'Classify image from URL',
            'GET /health': 'Health check',
            'GET /statistics': 'Get detection statistics',
            'GET /results': 'Get all detection results'
        }
    })


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'model_loaded': MODEL is not None,
        'timestamp': datetime.now().isoformat()
    })


@app.route('/classify', methods=['POST'])
def classify_upload():
    """
    Upload image and classify for freshness
    
    Usage:
        curl -X POST -F "file=@image.jpg" http://localhost:5000/classify
    """
    
    try:
        # Check if file was uploaded
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if file and allowed_file(file.filename):
            # Save uploaded file
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_")
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], timestamp + filename)
            file.save(filepath)
            
            logger.info(f"File uploaded: {filepath}")
            
            # Classify
            result = classify_image(filepath)
            
            if 'error' in result:
                return jsonify(result), 500
            
            # Save result
            result['file_path'] = filepath
            result_filename = f"{timestamp}{Path(filename).stem}_result.json"
            result_path = os.path.join(app.config['RESULTS_FOLDER'], result_filename)
            
            with open(result_path, 'w') as f:
                json.dump(result, f, indent=2)
            
            # Send to Firebase (optional)
            send_to_firebase(result)
            
            logger.info(f"Classification result: {result['classification']} ({result['confidence']:.2%})")
            
            return jsonify(result), 200
        
        else:
            return jsonify({'error': 'Invalid file format'}), 400
    
    except Exception as e:
        logger.error(f"Error in /classify: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/classify-url', methods=['POST'])
def classify_from_url():
    """
    Classify image from URL (e.g., ESP32 camera stream)
    
    Usage:
        curl -X POST -H "Content-Type: application/json" \
             -d '{"url": "http://esp32:80/capture"}' \
             http://localhost:5000/classify-url
    """
    
    try:
        data = request.get_json()
        
        if not data or 'url' not in data:
            return jsonify({'error': 'URL not provided'}), 400
        
        url = data['url']
        
        # Download image
        import requests
        response = requests.get(url, timeout=10)
        
        if response.status_code != 200:
            return jsonify({'error': 'Failed to download image'}), 400
        
        # Save image
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_")
        filename = f"{timestamp}esp32_capture.jpg"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        with open(filepath, 'wb') as f:
            f.write(response.content)
        
        logger.info(f"Image downloaded from {url}")
        
        # Classify
        result = classify_image(filepath)
        
        if 'error' in result:
            return jsonify(result), 500
        
        result['source_url'] = url
        result['file_path'] = filepath
        
        # Save result
        result_filename = f"{timestamp}esp32_result.json"
        result_path = os.path.join(app.config['RESULTS_FOLDER'], result_filename)
        
        with open(result_path, 'w') as f:
            json.dump(result, f, indent=2)
        
        # Send to Firebase
        send_to_firebase(result)
        
        return jsonify(result), 200
    
    except Exception as e:
        logger.error(f"Error in /classify-url: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/statistics', methods=['GET'])
def get_statistics():
    """Get detection statistics"""
    try:
        results_dir = Path(app.config['RESULTS_FOLDER'])
        
        if not results_dir.exists():
            return jsonify({'error': 'No results available'}), 404
        
        # Load all results
        all_results = []
        for result_file in results_dir.glob('*.json'):
            with open(result_file, 'r') as f:
                all_results.append(json.load(f))
        
        if not all_results:
            return jsonify({'statistics': {}}), 200
        
        # Calculate statistics
        total = len(all_results)
        rotten_count = sum(1 for r in all_results if r.get('classification') == 'rotten')
        fresh_count = total - rotten_count
        
        stats = {
            'total_processed': total,
            'fresh_count': fresh_count,
            'rotten_count': rotten_count,
            'fresh_percentage': (fresh_count / total * 100) if total > 0 else 0,
            'rotten_percentage': (rotten_count / total * 100) if total > 0 else 0,
            'average_confidence': float(np.mean([r['confidence'] for r in all_results])),
            'average_freshness_score': float(np.mean([r.get('freshness_score', 0) for r in all_results])),
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify({'statistics': stats}), 200
    
    except Exception as e:
        logger.error(f"Error in /statistics: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/results', methods=['GET'])
def get_results():
    """Get all detection results"""
    try:
        limit = request.args.get('limit', 50, type=int)
        results_dir = Path(app.config['RESULTS_FOLDER'])
        
        if not results_dir.exists():
            return jsonify({'results': []}), 200
        
        # Load results sorted by timestamp
        result_files = sorted(
            results_dir.glob('*.json'),
            key=os.path.getctime,
            reverse=True
        )[:limit]
        
        results = []
        for result_file in result_files:
            with open(result_file, 'r') as f:
                results.append(json.load(f))
        
        return jsonify({'results': results}), 200
    
    except Exception as e:
        logger.error(f"Error in /results: {e}")
        return jsonify({'error': str(e)}), 500


def send_to_firebase(result):
    """Send detection result to Firebase (optional)"""
    try:
        # Initialize Firebase (if credentials are set)
        if not firebase_admin._apps:
            # cred = credentials.Certificate('serviceAccountKey.json')
            # firebase_admin.initialize_app(cred, {
            #     'databaseURL': FIREBASE_CONFIG['databaseURL']
            # })
            pass
        
        # Send data
        # ref = db.reference('rot_detections')
        # ref.child(datetime.now().isoformat()).set(result)
        
        logger.info("Result sent to Firebase")
    
    except Exception as e:
        logger.warning(f"Could not send to Firebase: {e}")


def allowed_file(filename):
    """Check if file is allowed"""
    ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'bmp', 'tiff', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.errorhandler(404)
def not_found(error):
    """404 error handler"""
    return jsonify({'error': 'Endpoint not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    """500 error handler"""
    return jsonify({'error': 'Internal server error'}), 500


def run_server(host='0.0.0.0', port=5000, debug=False):
    """Run the API server"""
    logger.info("=" * 60)
    logger.info("AGRIX Rot Detection API Server")
    logger.info("=" * 60)
    logger.info(f"Starting server on {host}:{port}")
    logger.info(f"Model: {MODEL_PATH}")
    logger.info("=" * 60)
    
    # Load model on startup
    load_ml_model()
    
    # Run server
    app.run(host=host, port=port, debug=debug, threaded=True)


if __name__ == "__main__":
    run_server(host='0.0.0.0', port=5000, debug=True)
