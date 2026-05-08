# AGRIX ML Rotten Fruit & Vegetable Detection - Implementation Guide

## 📋 Overview

This implementation provides a complete machine learning pipeline for detecting rotten fruits and vegetables in real-time. It includes:

1. **Train Script** (`train_rot_detection.py`) - Train ML model from scratch
2. **Background Service** (`run_rot_detector.py`) - Continuous monitoring and classification
3. **REST API Server** (`rot_detection_api.py`) - Web service for integration with dashboard
4. **Integration** - Connects ESP32 camera feed to ML processing pipeline

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    ESP32-CAM                                │
│              (Captures fruit/veg images)                    │
└────────────────────┬────────────────────────────────────────┘
                     │ HTTP Stream
                     ▼
┌─────────────────────────────────────────────────────────────┐
│          AGRIX Dashboard (Web Interface)                    │
│         Shows real-time detection results                   │
└────────┬───────────────────────────────────────────┬────────┘
         │                                           │
         │ Image Upload / API Call                   │ Query Results
         ▼                                           ▼
┌─────────────────────────────────────────────────────────────┐
│       REST API Server (rot_detection_api.py)               │
│  • /classify - Upload & classify images                    │
│  • /classify-url - Process ESP32 stream                    │
│  • /statistics - Get detection metrics                     │
│  • /health - Service status                                │
└────────────────────┬────────────────────────────────────────┘
                     │
         ┌───────────┴────────────┐
         ▼                        ▼
    ┌─────────┐          ┌──────────────────┐
    │ ML Model│          │ Background Service│
    │(TF/Keras)          │ (Continuous Proc)│
    └─────────┘          └──────────────────┘
         │                        │
         └───────────┬────────────┘
                     ▼
            ┌────────────────────┐
            │ Results Storage    │
            │ (JSON Files, DB)   │
            └────────────────────┘
```

---

## 🚀 Quick Start (3 Steps)

### Step 1: Prepare Dataset
```bash
# Create directory structure
mkdir -p Fruit_Vegetable_Recognition-master/dataset/rot_detection/{fresh,rotten}

# Add training images:
# - Place ~100+ fresh fruit/veg images in: dataset/rot_detection/fresh/
# - Place ~100+ rotten fruit/veg images in: dataset/rot_detection/rotten/
```

### Step 2: Train Model
```bash
cd Fruit_Vegetable_Recognition-master
python train_rot_detection.py
```

### Step 3: Run Background Service (Choose One)

**Option A: Background Service (File Monitoring)**
```bash
python run_rot_detector.py
# Watches ./esp32_images/ directory for new images
```

**Option B: REST API Server (Web Integration)**
```bash
python rot_detection_api.py
# Starts server on http://localhost:5000
```

---

## 📚 Detailed Usage

### Training the Model

#### Dataset Structure
```
dataset/rot_detection/
├── fresh/
│   ├── apple_1.jpg
│   ├── apple_2.jpg
│   ├── banana_1.jpg
│   └── ...
└── rotten/
    ├── rotten_apple_1.jpg
    ├── rotten_apple_2.jpg
    ├── rotten_banana_1.jpg
    └── ...
```

#### Start Training
```python
from train_rot_detection import train_rot_detection_model

# Train with default configuration
trainer = train_rot_detection_model(
    dataset_dir='./dataset/rot_detection/'
)

# Or use custom config
from train_rot_detection import RotDetectionModelTrainer, CONFIG

custom_config = CONFIG.copy()
custom_config['epochs'] = 100
custom_config['batch_size'] = 16

trainer = RotDetectionModelTrainer(custom_config)
trainer.create_model()
train_gen, val_gen = trainer.prepare_data_generators('./dataset/rot_detection/')
trainer.train(train_gen, val_gen)
trainer.save_model()
trainer.plot_training_history()
```

#### Output
```
models/
├── agrix_rot_detection_v1_20260508_152301.h5
├── agrix_rot_detection_v1_20260508_152301.keras
└── agrix_rot_detection_v1_metadata_20260508_152301.json

logs/
├── training_history_20260508_152301.png
└── ...
```

---

### Background Service (File Monitoring)

#### How It Works
- Continuously watches a directory for new images
- Automatically classifies each image as "fresh" or "rotten"
- Saves results in JSON format
- Logs all activities

#### Configuration
Edit `run_rot_detector.py`:
```python
CONFIG = {
    'model_path': './models/agrix_rot_detection_v1.h5',
    'watch_dir': './esp32_images/',           # Watch this directory
    'output_dir': './detection_results/',      # Save results here
    'watch_interval': 5,                       # Check every 5 seconds
}
```

#### Start Service
```bash
# Standard run
python run_rot_detector.py

# Or programmatically
from run_rot_detector import RotDetectionService

service = RotDetectionService(
    model_path='./models/agrix_rot_detection_v1.h5',
    watch_dir='./esp32_images/',
    output_dir='./detection_results/'
)

service.start(watch_interval=5)
```

#### Example Output
```json
{
  "image_path": "./esp32_images/capture_001.jpg",
  "classification": "fresh",
  "confidence": 0.9834,
  "probabilities": {
    "fresh": 0.9834,
    "rotten": 0.0166
  },
  "timestamp": "2026-05-08T15:30:45.123456",
  "freshness_score": 98.34
}
```

#### Get Statistics
```python
# While service is running
stats = service.get_statistics()
print(stats)

# Output:
# {
#     'total_processed': 150,
#     'fresh_count': 127,
#     'rotten_count': 23,
#     'fresh_percentage': 84.67,
#     'rotten_percentage': 15.33,
#     'average_confidence': 0.9456,
#     'average_freshness_score': 81.23
# }
```

---

### REST API Server

#### Start Server
```bash
python rot_detection_api.py
# Server runs on http://localhost:5000
```

#### Endpoints

##### 1. Upload and Classify Image
```bash
curl -X POST -F "file=@fruit.jpg" http://localhost:5000/classify

# Response:
{
  "success": true,
  "classification": "fresh",
  "confidence": 0.9456,
  "freshness_score": 94.56,
  "probabilities": {
    "fresh": 0.9456,
    "rotten": 0.0544
  },
  "recommendation": "Consume immediately",
  "timestamp": "2026-05-08T15:35:20.123456"
}
```

##### 2. Classify from ESP32 URL
```bash
curl -X POST -H "Content-Type: application/json" \
     -d '{"url": "http://192.168.1.100:80/capture"}' \
     http://localhost:5000/classify-url

# Response: (same as above)
```

##### 3. Get Statistics
```bash
curl http://localhost:5000/statistics

# Response:
{
  "statistics": {
    "total_processed": 542,
    "fresh_count": 456,
    "rotten_count": 86,
    "fresh_percentage": 84.13,
    "rotten_percentage": 15.87,
    "average_confidence": 0.9234,
    "average_freshness_score": 82.45
  }
}
```

##### 4. Get Recent Results
```bash
# Get last 20 results
curl "http://localhost:5000/results?limit=20"

# Response:
{
  "results": [
    {...}, {...}, ...
  ]
}
```

##### 5. Health Check
```bash
curl http://localhost:5000/health

# Response:
{
  "status": "healthy",
  "model_loaded": true,
  "timestamp": "2026-05-08T15:40:00.123456"
}
```

##### 6. API Info
```bash
curl http://localhost:5000/

# Response:
{
  "service": "AGRIX Rot Detection API",
  "version": "1.0.0",
  "status": "running",
  "model_loaded": true,
  "endpoints": {...}
}
```

---

## 🔗 Integration with Dashboard

### Method 1: Direct API Calls from Dashboard JavaScript

```javascript
// Add to dashboard.html in Reports modal

async function detectProduceRot(imageFile) {
    const formData = new FormData();
    formData.append('file', imageFile);
    
    try {
        const response = await fetch('http://localhost:5000/classify', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (result.success) {
            // Show detection result
            displayRotDetectionResult(result);
        }
    } catch (error) {
        console.error('Detection error:', error);
    }
}

function displayRotDetectionResult(result) {
    const freshness = result.freshness_score;
    
    let statusColor = freshness > 80 ? '#52b788' : freshness > 50 ? '#ffa500' : '#ff6b6b';
    let statusText = freshness > 80 ? '✅ FRESH' : freshness > 50 ? '⚠️ WARNING' : '❌ ROTTEN';
    
    alert(`
        ${statusText}
        Freshness Score: ${freshness.toFixed(2)}%
        Confidence: ${(result.confidence * 100).toFixed(2)}%
        Recommendation: ${result.recommendation}
    `);
}
```

### Method 2: ESP32 Camera Direct Feed

```python
# Processing script
import requests
import json

ESP32_IP = "192.168.1.100"
API_SERVER = "http://localhost:5000"

def process_esp32_feed():
    """Continuously process ESP32 camera feed"""
    while True:
        try:
            # Get frame from ESP32
            response = requests.post(
                f"{API_SERVER}/classify-url",
                json={"url": f"http://{ESP32_IP}:80/capture"},
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Save to Firebase
                send_to_firebase(result)
                
                # Log result
                status = "🟢 FRESH" if result['classification'] == 'fresh' else "🔴 ROTTEN"
                print(f"{status} - {result['freshness_score']:.1f}% fresh")
            
            time.sleep(5)  # Process every 5 seconds
        
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(5)

process_esp32_feed()
```

---

## 🎛️ Configuration & Customization

### Training Configuration
Edit `train_rot_detection.py`:

```python
CONFIG = {
    'model_name': 'agrix_rot_detection_v1',
    'image_size': (224, 224),     # Input image size
    'batch_size': 32,              # Batch size
    'epochs': 50,                  # Training epochs
    'learning_rate': 0.001,        # Learning rate
    'validation_split': 0.2,       # 20% for validation
    'test_split': 0.1,             # 10% for testing
    'classes': ['fresh', 'rotten'],
    'augmentation': True,          # Enable data augmentation
    'use_pretrained': True,        # Use transfer learning (MobileNetV2)
    'freeze_base_layers': True,    # Freeze base model
}
```

### Model Architecture

```
Input (224x224x3)
    ↓
Data Augmentation
    ↓
MobileNetV2 (Pre-trained, Frozen)
    ↓
Global Average Pooling
    ↓
Dense(512) + BatchNorm + Dropout(0.4)
    ↓
Dense(256) + BatchNorm + Dropout(0.3)
    ↓
Dense(128) + BatchNorm + Dropout(0.2)
    ↓
Dense(2, softmax)  ← Output [fresh, rotten]
```

---

## 📊 Performance Metrics

### Expected Accuracy
- **Fresh/Rotten Classification**: 85-95% accuracy
- **Confidence Threshold**: > 80% recommended for production
- **Processing Speed**: ~100-200 images/minute (depending on hardware)

### Hardware Requirements
- **Minimum**: 4GB RAM, any CPU
- **Recommended**: 8GB+ RAM, GPU (NVIDIA, etc.)
- **Training Time**: 30 minutes - 2 hours (depending on dataset size)
- **Model Size**: ~40-60MB

---

## 🔍 Monitoring & Logging

### Log Files
```
logs/
├── api_server.log          # API server activity
├── rot_detection_service.log   # Background service logs
└── training_history_*.png  # Training graphs
```

### View Logs in Real-Time
```bash
# API Server
tail -f ./Fruit_Vegetable_Recognition-master/logs/api_server.log

# Background Service
tail -f ./Fruit_Vegetable_Recognition-master/logs/rot_detection_service.log
```

### Example Log Format
```
2026-05-08 15:35:20,123 - INFO - 🟢 FRESH - Confidence: 98.34% - ./esp32_images/capture_001.jpg
2026-05-08 15:35:25,456 - INFO - 🔴 ROTTEN - Confidence: 92.11% - ./esp32_images/capture_002.jpg
2026-05-08 15:35:30,789 - INFO - Processing: 2 new image(s)
```

---

## ⚠️ Troubleshooting

### Issue: Model Not Loading
**Solution**: Check file path and permissions
```bash
# Verify model exists
ls -la ./Fruit_Vegetable_Recognition-master/models/*.h5

# Check permissions
chmod 644 ./Fruit_Vegetable_Recognition-master/models/*.h5
```

### Issue: Out of Memory During Training
**Solution**: Reduce batch size
```python
CONFIG['batch_size'] = 8  # Reduced from 32
```

### Issue: Low Detection Accuracy
**Solution**: Add more training data
```bash
# Collect more images
# Ensure balanced dataset (equal fresh and rotten images)
# Try data augmentation settings
```

### Issue: API Server Connection Refused
**Solution**: Check port availability
```bash
# Check if port 5000 is in use
lsof -i :5000

# Use alternative port
python rot_detection_api.py --port 8000
```

---

## 🚀 Advanced Usage

### Custom Model Training

```python
from train_rot_detection import RotDetectionModelTrainer

config = {
    'epochs': 100,
    'batch_size': 16,
    'learning_rate': 0.0005,
    'freeze_base_layers': False  # Fine-tune all layers
}

trainer = RotDetectionModelTrainer(config)
trainer.create_model()
train_gen, val_gen = trainer.prepare_data_generators('./dataset/')
trainer.train(train_gen, val_gen)
trainer.save_model()
```

### Using Different Pre-trained Models

```python
# In train_rot_detection.py, change base_model:
from tensorflow.keras.applications import ResNet50, InceptionV3

# ResNet50
base_model = ResNet50(input_shape=(...), include_top=False, weights='imagenet')

# InceptionV3
base_model = InceptionV3(input_shape=(...), include_top=False, weights='imagenet')
```

### Deploy to Production

```bash
# Use production WSGI server instead of Flask dev server
pip install gunicorn

# Run with Gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 rot_detection_api:app

# Or use uWSGI
pip install uwsgi
uwsgi --http :5000 --wsgi-file rot_detection_api.py --callable app --processes 4 --threads 2
```

---

## 📈 Next Steps

1. **Collect Dataset** - Gather ~200+ images each (fresh & rotten)
2. **Train Model** - Run training script with your data
3. **Test Results** - Verify accuracy on test set
4. **Deploy Service** - Choose background service or API server
5. **Integrate Dashboard** - Add detection results to web interface
6. **Monitor Performance** - Track statistics and refine model

---

## 📝 Files Created

| File | Purpose |
|------|---------|
| `train_rot_detection.py` | Train ML model from scratch |
| `run_rot_detector.py` | Background service for continuous classification |
| `rot_detection_api.py` | REST API server for web integration |
| `models/` | Store trained models |
| `logs/` | Training and service logs |
| `detection_results/` | Classification results (JSON) |
| `uploads/` | Uploaded images for classification |
| `dataset/rot_detection/` | Training dataset (fresh & rotten) |

---

## 🎓 Learning Resources

- [TensorFlow Transfer Learning](https://www.tensorflow.org/tutorials/images/transfer_learning)
- [MobileNetV2 Documentation](https://keras.io/api/applications/mobilenetv2/)
- [Keras Data Augmentation](https://keras.io/api/preprocessing/image/)
- [Flask REST API](https://flask.palletsprojects.com/)

---

## 💡 Tips for Best Results

1. **Balanced Dataset**: Equal number of fresh and rotten samples
2. **Image Variety**: Different fruits, vegetables, lighting conditions
3. **High Resolution**: Use 224x224 or higher quality images
4. **Data Augmentation**: Enable for small datasets (<500 images)
5. **Monitor Validation**: Watch for overfitting
6. **Use GPU**: Significantly faster training (10-20x speedup)
7. **Regular Updates**: Retrain with new data periodically

---

**Version**: 1.0  
**Last Updated**: May 2026  
**AGRIX - Smart Agricultural Management Platform**
