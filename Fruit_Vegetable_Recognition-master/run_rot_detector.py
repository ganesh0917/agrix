"""
AGRIX Background Rot Detection Service
Runs continuously to classify images from ESP32 camera feed
Monitors directory and processes images in real-time
"""

import os
import time
import json
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.image import load_img, img_to_array
from pathlib import Path
from datetime import datetime
from threading import Thread
import queue
import logging
from PIL import Image

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('./Fruit_Vegetable_Recognition-master/logs/rot_detection_service.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class RotDetectionService:
    """Background service for real-time rot detection from ESP32 camera feed"""
    
    def __init__(self, model_path=None, watch_dir='./esp32_images/', output_dir='./detection_results/'):
        """
        Initialize service
        
        Args:
            model_path: Path to pre-trained model
            watch_dir: Directory to watch for incoming images
            output_dir: Directory to save detection results
        """
        self.model = None
        self.model_path = model_path
        self.watch_dir = Path(watch_dir)
        self.output_dir = Path(output_dir)
        self.classes = ['fresh', 'rotten']
        self.is_running = False
        self.detection_queue = queue.Queue()
        self.results = []
        
        # Create directories
        self.watch_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Load model
        self._load_model()
    
    def _load_model(self):
        """Load pre-trained model"""
        if self.model_path and os.path.exists(self.model_path):
            try:
                self.model = load_model(self.model_path)
                logger.info(f"✓ Model loaded: {self.model_path}")
            except Exception as e:
                logger.error(f"✗ Failed to load model: {e}")
                self._create_dummy_model()
        else:
            logger.warning("⚠️  Model not found. Creating dummy model for demo...")
            self._create_dummy_model()
    
    def _create_dummy_model(self):
        """Create a dummy model for testing purposes"""
        from tensorflow.keras import layers, models
        
        model = models.Sequential([
            layers.Input(shape=(224, 224, 3)),
            layers.Conv2D(32, 3, activation='relu'),
            layers.MaxPooling2D(),
            layers.Conv2D(64, 3, activation='relu'),
            layers.MaxPooling2D(),
            layers.Flatten(),
            layers.Dense(128, activation='relu'),
            layers.Dropout(0.5),
            layers.Dense(2, activation='softmax')
        ])
        
        model.compile(
            optimizer='adam',
            loss='categorical_crossentropy',
            metrics=['accuracy']
        )
        
        self.model = model
        logger.info("✓ Dummy model created for testing")
    
    def preprocess_image(self, image_path, target_size=(224, 224)):
        """Preprocess image for model"""
        try:
            img = load_img(image_path, target_size=target_size)
            img_array = img_to_array(img)
            img_array = img_array / 255.0
            img_array = np.expand_dims(img_array, axis=0)
            return img_array
        except Exception as e:
            logger.error(f"Error preprocessing image {image_path}: {e}")
            return None
    
    def classify_image(self, image_path):
        """Classify image for freshness"""
        if self.model is None:
            return None
        
        try:
            # Preprocess
            img_array = self.preprocess_image(image_path)
            if img_array is None:
                return None
            
            # Predict
            predictions = self.model.predict(img_array, verbose=0)
            class_idx = np.argmax(predictions[0])
            confidence = float(predictions[0][class_idx])
            class_label = self.classes[class_idx]
            
            result = {
                'image_path': str(image_path),
                'classification': class_label,
                'confidence': confidence,
                'probabilities': {
                    'fresh': float(predictions[0][0]),
                    'rotten': float(predictions[0][1])
                },
                'timestamp': datetime.now().isoformat(),
                'freshness_score': float(1 - predictions[0][1]) * 100  # 0-100 scale
            }
            
            return result
        
        except Exception as e:
            logger.error(f"Error classifying image {image_path}: {e}")
            return None
    
    def process_image(self, image_path):
        """Process single image and save results"""
        logger.info(f"Processing: {image_path}")
        
        # Classify
        result = self.classify_image(image_path)
        
        if result is None:
            logger.error(f"Failed to classify: {image_path}")
            return None
        
        # Save result
        result_filename = f"{Path(image_path).stem}_result.json"
        result_path = self.output_dir / result_filename
        
        with open(result_path, 'w') as f:
            json.dump(result, f, indent=2)
        
        # Log severity
        severity = "🔴 ROTTEN" if result['classification'] == 'rotten' else "🟢 FRESH"
        logger.info(f"{severity} - Confidence: {result['confidence']:.2%} - {image_path}")
        
        self.results.append(result)
        return result
    
    def watch_directory(self, interval=5):
        """Watch directory for new images and process them"""
        logger.info(f"👁️  Watching directory: {self.watch_dir}")
        logger.info(f"Scanning every {interval} seconds...")
        
        processed_files = set()
        
        while self.is_running:
            try:
                # Find new images
                image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff'}
                current_files = {
                    f for f in self.watch_dir.glob('*')
                    if f.is_file() and f.suffix.lower() in image_extensions
                }
                
                # Process new files
                new_files = current_files - processed_files
                
                for image_file in new_files:
                    if image_file.suffix.lower() in image_extensions:
                        result = self.process_image(image_file)
                        if result:
                            processed_files.add(image_file)
                            # Send to queue for external processing
                            self.detection_queue.put(result)
                
                if new_files:
                    logger.info(f"Processed {len(new_files)} new image(s)")
                
                time.sleep(interval)
            
            except Exception as e:
                logger.error(f"Error in watch loop: {e}")
                time.sleep(interval)
    
    def start(self, watch_interval=5):
        """Start the service"""
        if self.is_running:
            logger.warning("Service already running!")
            return
        
        self.is_running = True
        logger.info("🚀 Starting Rot Detection Service...")
        
        # Start watcher thread
        watcher_thread = Thread(
            target=self.watch_directory,
            args=(watch_interval,),
            daemon=True
        )
        watcher_thread.start()
        
        logger.info("✓ Service started successfully!")
        
        # Keep main thread alive
        try:
            while self.is_running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()
    
    def stop(self):
        """Stop the service"""
        self.is_running = False
        logger.info("⏹️  Stopping Rot Detection Service...")
        logger.info("✓ Service stopped!")
    
    def get_statistics(self):
        """Get detection statistics"""
        if not self.results:
            return None
        
        total = len(self.results)
        rotten_count = sum(1 for r in self.results if r['classification'] == 'rotten')
        fresh_count = total - rotten_count
        
        avg_confidence = np.mean([r['confidence'] for r in self.results])
        avg_freshness = np.mean([r['freshness_score'] for r in self.results])
        
        stats = {
            'total_processed': total,
            'fresh_count': fresh_count,
            'rotten_count': rotten_count,
            'fresh_percentage': (fresh_count / total * 100) if total > 0 else 0,
            'rotten_percentage': (rotten_count / total * 100) if total > 0 else 0,
            'average_confidence': float(avg_confidence),
            'average_freshness_score': float(avg_freshness),
            'timestamp': datetime.now().isoformat()
        }
        
        return stats
    
    def export_results(self, filename='detection_results.json'):
        """Export all results to JSON file"""
        export_path = self.output_dir / filename
        
        stats = self.get_statistics() or {}
        data = {
            'statistics': stats,
            'detections': self.results
        }
        
        with open(export_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"✓ Results exported to: {export_path}")
        return export_path


def run_background_service(model_path=None, watch_dir='./esp32_images/', watch_interval=5):
    """
    Run the detection service in background
    
    Usage:
        from run_rot_detector import run_background_service
        run_background_service(
            model_path='./models/agrix_rot_detection_v1.h5',
            watch_dir='./esp32_images/',
            watch_interval=5
        )
    """
    service = RotDetectionService(
        model_path=model_path,
        watch_dir=watch_dir
    )
    
    service.start(watch_interval=watch_interval)
    
    return service


if __name__ == "__main__":
    print("=" * 60)
    print("AGRIX Rotten Fruit Detection Background Service")
    print("=" * 60)
    print()
    
    # Find latest model
    model_dir = Path('./Fruit_Vegetable_Recognition-master/models/')
    latest_model = None
    
    if model_dir.exists():
        h5_models = list(model_dir.glob('*.h5'))
        if h5_models:
            latest_model = max(h5_models, key=os.path.getctime)
            print(f"✓ Found model: {latest_model}")
    
    # Start service
    service = RotDetectionService(
        model_path=str(latest_model) if latest_model else None,
        watch_dir='./esp32_images/',
        output_dir='./detection_results/'
    )
    
    print("\n📁 Directories:")
    print(f"   Watch: {service.watch_dir}")
    print(f"   Output: {service.output_dir}")
    print()
    print("Press Ctrl+C to stop the service")
    print()
    
    service.start(watch_interval=5)
