"""
AGRIX ML Training & Deployment Manager
One-command launcher for training, testing, and serving
"""

import os
import sys
import argparse
from pathlib import Path
import subprocess
import json
from datetime import datetime

# Configuration
AGRIX_ROOT = Path(__file__).parent.parent
ML_DIR = Path(__file__).parent
MODELS_DIR = ML_DIR / 'models'
DATASET_DIR = ML_DIR / 'dataset' / 'rot_detection'
LOGS_DIR = ML_DIR / 'logs'

def ensure_directories():
    """Create necessary directories"""
    for directory in [MODELS_DIR, DATASET_DIR, LOGS_DIR]:
        directory.mkdir(parents=True, exist_ok=True)
    
    # Create subdirectories for fresh and rotten
    (DATASET_DIR / 'fresh').mkdir(parents=True, exist_ok=True)
    (DATASET_DIR / 'rotten').mkdir(parents=True, exist_ok=True)
    
    print("✓ Directories ready")


def check_dependencies():
    """Check if required packages are installed"""
    required = [
        'tensorflow',
        'keras',
        'numpy',
        'pillow',
        'flask',
        'opencv-python'
    ]
    
    missing = []
    for package in required:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing.append(package)
    
    if missing:
        print("⚠️  Missing packages. Install with:")
        print(f"   pip install {' '.join(missing)}")
        return False
    
    print("✓ All dependencies installed")
    return True


def train_model(dataset_dir=None, epochs=None, batch_size=None):
    """Train rot detection model"""
    print("\n" + "=" * 60)
    print("AGRIX Rot Detection Model - Training Mode")
    print("=" * 60)
    
    if dataset_dir is None:
        dataset_dir = str(DATASET_DIR)
    
    # Check dataset
    fresh_count = len(list(Path(dataset_dir).glob('fresh/*')))
    rotten_count = len(list(Path(dataset_dir).glob('rotten/*')))
    
    print(f"\n📊 Dataset Status:")
    print(f"   Fresh images: {fresh_count}")
    print(f"   Rotten images: {rotten_count}")
    print(f"   Total: {fresh_count + rotten_count}")
    
    if fresh_count < 50 or rotten_count < 50:
        print("\n⚠️  Dataset too small!")
        print("   Recommended: >100 images per class")
        print(f"\n📁 Add images to:")
        print(f"   • {dataset_dir}/fresh/")
        print(f"   • {dataset_dir}/rotten/")
        return False
    
    print("\n🚀 Starting training...")
    
    # Import and train
    try:
        from train_rot_detection import train_rot_detection_model
        
        trainer = train_rot_detection_model(dataset_dir=dataset_dir)
        
        if trainer:
            print("\n✅ Training completed successfully!")
            print(f"📁 Model saved to: {MODELS_DIR}")
            print(f"📊 Results saved to: {LOGS_DIR}")
            return True
        else:
            print("\n❌ Training failed")
            return False
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False


def run_api_server(port=5000):
    """Run REST API server"""
    print("\n" + "=" * 60)
    print("AGRIX Rot Detection API Server")
    print("=" * 60)
    
    # Check if model exists
    latest_model = None
    if MODELS_DIR.exists():
        h5_models = list(MODELS_DIR.glob('*.h5'))
        if h5_models:
            latest_model = max(h5_models, key=os.path.getctime)
    
    if not latest_model:
        print("\n⚠️  No trained model found!")
        print("   Run: python start.py --train (to train first)")
        return False
    
    print(f"\n✓ Model: {latest_model.name}")
    print(f"✓ API Server: http://localhost:{port}")
    print(f"\nEndpoints:")
    print(f"   POST   /classify        - Upload image")
    print(f"   POST   /classify-url    - Process from URL")
    print(f"   GET    /statistics      - Get metrics")
    print(f"   GET    /results         - Get results")
    print(f"   GET    /health          - Health check")
    print(f"\nPress Ctrl+C to stop")
    
    try:
        import rot_detection_api
        rot_detection_api.run_server(port=port, debug=False)
    except KeyboardInterrupt:
        print("\n✓ Server stopped")
        return True
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False


def run_background_service(watch_interval=5):
    """Run background monitoring service"""
    print("\n" + "=" * 60)
    print("AGRIX Rot Detection - Background Service")
    print("=" * 60)
    
    # Check if model exists
    latest_model = None
    if MODELS_DIR.exists():
        h5_models = list(MODELS_DIR.glob('*.h5'))
        if h5_models:
            latest_model = max(h5_models, key=os.path.getctime)
    
    if not latest_model:
        print("\n⚠️  No trained model found!")
        print("   Run: python start.py --train (to train first)")
        return False
    
    watch_dir = ML_DIR / 'esp32_images'
    output_dir = ML_DIR / 'detection_results'
    
    print(f"\n✓ Model: {latest_model.name}")
    print(f"✓ Watching: {watch_dir}")
    print(f"✓ Output: {output_dir}")
    print(f"✓ Interval: {watch_interval}s")
    print(f"\nPress Ctrl+C to stop")
    
    # Create directories
    watch_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        from run_rot_detector import RotDetectionService
        
        service = RotDetectionService(
            model_path=str(latest_model),
            watch_dir=str(watch_dir),
            output_dir=str(output_dir)
        )
        
        service.start(watch_interval=watch_interval)
    
    except KeyboardInterrupt:
        print("\n✓ Service stopped")
        return True
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False


def show_statistics():
    """Show detection statistics"""
    print("\n" + "=" * 60)
    print("AGRIX Rot Detection - Statistics")
    print("=" * 60)
    
    results_dir = ML_DIR / 'detection_results'
    
    if not results_dir.exists():
        print("\n⚠️  No results found!")
        print("   Run background service or API server first")
        return
    
    # Load all results
    all_results = []
    for result_file in results_dir.glob('*.json'):
        try:
            with open(result_file, 'r') as f:
                all_results.append(json.load(f))
        except:
            pass
    
    if not all_results:
        print("\n⚠️  No detection results available")
        return
    
    # Calculate statistics
    import numpy as np
    
    total = len(all_results)
    rotten_count = sum(1 for r in all_results if r.get('classification') == 'rotten')
    fresh_count = total - rotten_count
    
    confidences = [r['confidence'] for r in all_results]
    freshness_scores = [r.get('freshness_score', 0) for r in all_results]
    
    print(f"\n📊 Overall Statistics:")
    print(f"   Total Processed: {total}")
    print(f"   🟢 Fresh: {fresh_count} ({fresh_count/total*100:.1f}%)")
    print(f"   🔴 Rotten: {rotten_count} ({rotten_count/total*100:.1f}%)")
    print(f"\n📈 Quality Metrics:")
    print(f"   Avg Confidence: {np.mean(confidences):.2%}")
    print(f"   Avg Freshness: {np.mean(freshness_scores):.1f}%")
    print(f"   Min Confidence: {np.min(confidences):.2%}")
    print(f"   Max Confidence: {np.max(confidences):.2%}")
    print(f"\n📁 Results stored in: {results_dir}")


def show_help():
    """Show help message"""
    print("\n" + "=" * 60)
    print("AGRIX ML Rot Detection Manager")
    print("=" * 60)
    print("\nUsage: python start.py [COMMAND] [OPTIONS]")
    print("\nCommands:")
    print("  --train              Train model (needs dataset)")
    print("  --api [PORT]         Run REST API server (default: 5000)")
    print("  --service [INTERVAL] Run background service (default: 5s)")
    print("  --stats              Show detection statistics")
    print("  --check              Check setup & dependencies")
    print("  --help               Show this help")
    print("\nExamples:")
    print("  python start.py --train")
    print("  python start.py --api 5000")
    print("  python start.py --service 3")
    print("  python start.py --stats")
    print("\nGuide:")
    print("  1. Collect dataset in dataset/rot_detection/{fresh,rotten}/")
    print("  2. Run: python start.py --train")
    print("  3. Run: python start.py --api (or --service)")
    print("  4. Check: python start.py --stats")
    print()


def main():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--train', action='store_true')
    parser.add_argument('--api', nargs='?', const=5000, type=int)
    parser.add_argument('--service', nargs='?', const=5, type=int)
    parser.add_argument('--stats', action='store_true')
    parser.add_argument('--check', action='store_true')
    parser.add_argument('--help', action='store_true')
    
    args = parser.parse_args()
    
    if not any(vars(args).values()) or args.help:
        show_help()
        return
    
    # Setup
    ensure_directories()
    
    if args.check:
        print("\n" + "=" * 60)
        print("System Check")
        print("=" * 60)
        check_dependencies()
        print("✓ Setup is ready!\n")
        return
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Route commands
    if args.train:
        success = train_model()
        sys.exit(0 if success else 1)
    
    elif args.api is not None:
        success = run_api_server(port=args.api)
        sys.exit(0 if success else 1)
    
    elif args.service is not None:
        success = run_background_service(watch_interval=args.service)
        sys.exit(0 if success else 1)
    
    elif args.stats:
        show_statistics()
        sys.exit(0)


if __name__ == "__main__":
    main()
