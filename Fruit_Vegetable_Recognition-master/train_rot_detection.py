"""
AGRIX Rotten Fruit/Vegetable Classification Model
Train and deploy ML model for freshness detection
"""

import os
import numpy as np
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers, models
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.applications import MobileNetV2
import matplotlib.pyplot as plt
from datetime import datetime
import json
import cv2
from pathlib import Path

# Configuration
CONFIG = {
    'model_name': 'agrix_rot_detection_v1',
    'image_size': (224, 224),
    'batch_size': 32,
    'epochs': 50,
    'learning_rate': 0.001,
    'validation_split': 0.2,
    'test_split': 0.1,
    'classes': ['fresh', 'rotten'],
    'augmentation': True,
    'use_pretrained': True,  # Use MobileNetV2 transfer learning
    'freeze_base_layers': True,
    'output_dir': './Fruit_Vegetable_Recognition-master/models/',
    'logs_dir': './Fruit_Vegetable_Recognition-master/logs/',
    'dataset_dir': './Fruit_Vegetable_Recognition-master/dataset/rot_detection/',
}

class RotDetectionModelTrainer:
    """Train ML model for fresh/rotten fruit and vegetable classification"""
    
    def __init__(self, config=CONFIG):
        self.config = config
        self.model = None
        self.history = None
        self.training_log = []
        self._setup_directories()
        
    def _setup_directories(self):
        """Create necessary directories"""
        for directory in [self.config['output_dir'], self.config['logs_dir'], self.config['dataset_dir']]:
            Path(directory).mkdir(parents=True, exist_ok=True)
    
    def create_model(self):
        """Create the neural network model with transfer learning"""
        print("🏗️  Creating model architecture...")
        
        # Load pre-trained MobileNetV2
        base_model = MobileNetV2(
            input_shape=(*self.config['image_size'], 3),
            include_top=False,
            weights='imagenet'
        )
        
        # Freeze base model layers if specified
        if self.config['freeze_base_layers']:
            base_model.trainable = False
            print("✓ Base model layers frozen (transfer learning)")
        
        # Create new model
        model = models.Sequential([
            layers.Input(shape=(*self.config['image_size'], 3)),
            
            # Data augmentation layers
            layers.RandomFlip("horizontal"),
            layers.RandomRotation(0.2),
            layers.RandomZoom(0.2),
            layers.RandomBrightness(0.2),
            
            # Normalization
            layers.Rescaling(1./127.5, offset=-1),
            
            # Pre-trained base
            base_model,
            
            # Custom classification head
            layers.GlobalAveragePooling2D(),
            layers.Dense(512, activation='relu', name='dense_512'),
            layers.BatchNormalization(),
            layers.Dropout(0.4),
            
            layers.Dense(256, activation='relu', name='dense_256'),
            layers.BatchNormalization(),
            layers.Dropout(0.3),
            
            layers.Dense(128, activation='relu', name='dense_128'),
            layers.BatchNormalization(),
            layers.Dropout(0.2),
            
            # Output layer
            layers.Dense(len(self.config['classes']), activation='softmax', name='output')
        ])
        
        # Compile model
        optimizer = keras.optimizers.Adam(learning_rate=self.config['learning_rate'])
        model.compile(
            optimizer=optimizer,
            loss='categorical_crossentropy',
            metrics=['accuracy', keras.metrics.Precision(), keras.metrics.Recall()]
        )
        
        self.model = model
        print(f"✓ Model created with {model.count_params():,} parameters")
        return model
    
    def prepare_data_generators(self, dataset_dir):
        """Create data generators for training and validation"""
        print("📊 Setting up data generators...")
        
        # Training data augmentation
        train_datagen = ImageDataGenerator(
            rescale=1./255,
            rotation_range=20,
            width_shift_range=0.2,
            height_shift_range=0.2,
            horizontal_flip=True,
            zoom_range=0.2,
            shear_range=0.15,
            brightness_range=[0.8, 1.2],
            fill_mode='nearest',
            validation_split=self.config['validation_split']
        )
        
        # Validation data (minimal augmentation)
        val_datagen = ImageDataGenerator(
            rescale=1./255,
            validation_split=self.config['validation_split']
        )
        
        # Training generator
        train_generator = train_datagen.flow_from_directory(
            dataset_dir,
            target_size=self.config['image_size'],
            batch_size=self.config['batch_size'],
            class_mode='categorical',
            subset='training',
            classes=self.config['classes'],
            seed=42
        )
        
        # Validation generator
        validation_generator = val_datagen.flow_from_directory(
            dataset_dir,
            target_size=self.config['image_size'],
            batch_size=self.config['batch_size'],
            class_mode='categorical',
            subset='validation',
            classes=self.config['classes'],
            seed=42
        )
        
        print(f"✓ Training samples: {train_generator.samples}")
        print(f"✓ Validation samples: {validation_generator.samples}")
        
        return train_generator, validation_generator
    
    def train(self, train_generator, validation_generator):
        """Train the model"""
        print("\n🚀 Starting training...")
        
        # Callbacks
        callbacks = [
            keras.callbacks.EarlyStopping(
                monitor='val_loss',
                patience=5,
                restore_best_weights=True,
                verbose=1
            ),
            keras.callbacks.ReduceLROnPlateau(
                monitor='val_loss',
                factor=0.5,
                patience=3,
                min_lr=1e-6,
                verbose=1
            ),
            keras.callbacks.ModelCheckpoint(
                os.path.join(self.config['output_dir'], 'best_model.h5'),
                monitor='val_accuracy',
                save_best_only=True,
                verbose=1
            ),
            keras.callbacks.TensorBoard(
                log_dir=self.config['logs_dir'],
                histogram_freq=1,
                update_freq='epoch'
            )
        ]
        
        # Train model
        steps_per_epoch = train_generator.samples // self.config['batch_size']
        validation_steps = validation_generator.samples // self.config['batch_size']
        
        self.history = self.model.fit(
            train_generator,
            steps_per_epoch=steps_per_epoch,
            epochs=self.config['epochs'],
            validation_data=validation_generator,
            validation_steps=validation_steps,
            callbacks=callbacks,
            verbose=1
        )
        
        print("✓ Training completed!")
        return self.history
    
    def save_model(self):
        """Save trained model"""
        if self.model is None:
            print("❌ No model to save. Train first!")
            return False
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save in multiple formats
        model_path_h5 = os.path.join(self.config['output_dir'], f'{self.config["model_name"]}_H5_{timestamp}.h5')
        model_path_keras = os.path.join(self.config['output_dir'], f'{self.config["model_name"]}_{timestamp}.keras')
        
        # H5 format
        self.model.save(model_path_h5)
        print(f"✓ Model saved (H5): {model_path_h5}")
        
        # Keras format (recommended for TF 2.x)
        self.model.save(model_path_keras)
        print(f"✓ Model saved (Keras): {model_path_keras}")
        
        # Save config and metadata
        metadata = {
            'model_name': self.config['model_name'],
            'timestamp': timestamp,
            'classes': self.config['classes'],
            'image_size': self.config['image_size'],
            'epochs_trained': len(self.history.history['loss']),
            'final_train_accuracy': float(self.history.history['accuracy'][-1]),
            'final_val_accuracy': float(self.history.history['val_accuracy'][-1]),
            'final_train_loss': float(self.history.history['loss'][-1]),
            'final_val_loss': float(self.history.history['val_loss'][-1]),
        }
        
        metadata_path = os.path.join(self.config['output_dir'], f'{self.config["model_name"]}_metadata_{timestamp}.json')
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"✓ Metadata saved: {metadata_path}")
        return True
    
    def plot_training_history(self):
        """Plot training history"""
        if self.history is None:
            print("❌ No training history available")
            return
        
        fig, axes = plt.subplots(1, 2, figsize=(14, 5))
        
        # Accuracy
        axes[0].plot(self.history.history['accuracy'], label='Train Accuracy', linewidth=2)
        axes[0].plot(self.history.history['val_accuracy'], label='Val Accuracy', linewidth=2)
        axes[0].set_title('Model Accuracy', fontsize=14, fontweight='bold')
        axes[0].set_xlabel('Epoch')
        axes[0].set_ylabel('Accuracy')
        axes[0].legend()
        axes[0].grid(True, alpha=0.3)
        
        # Loss
        axes[1].plot(self.history.history['loss'], label='Train Loss', linewidth=2)
        axes[1].plot(self.history.history['val_loss'], label='Val Loss', linewidth=2)
        axes[1].set_title('Model Loss', fontsize=14, fontweight='bold')
        axes[1].set_xlabel('Epoch')
        axes[1].set_ylabel('Loss')
        axes[1].legend()
        axes[1].grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        # Save figure
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        plot_path = os.path.join(self.config['logs_dir'], f'training_history_{timestamp}.png')
        plt.savefig(plot_path, dpi=300, bbox_inches='tight')
        print(f"✓ Training history plot saved: {plot_path}")
        
        plt.show()
    
    def evaluate_model(self, test_generator):
        """Evaluate model on test set"""
        print("\n📊 Evaluating model...")
        results = self.model.evaluate(test_generator, verbose=1)
        
        eval_dict = {
            'loss': float(results[0]),
            'accuracy': float(results[1]),
            'precision': float(results[2]),
            'recall': float(results[3])
        }
        
        print(f"\n📈 Evaluation Results:")
        print(f"   Loss: {eval_dict['loss']:.4f}")
        print(f"   Accuracy: {eval_dict['accuracy']:.4f}")
        print(f"   Precision: {eval_dict['precision']:.4f}")
        print(f"   Recall: {eval_dict['recall']:.4f}")
        
        return eval_dict


def train_rot_detection_model(dataset_dir=None):
    """
    Main training function
    
    Dataset structure should be:
    dataset/rot_detection/
    ├── fresh/
    │   ├── image1.jpg
    │   ├── image2.jpg
    │   └── ...
    └── rotten/
        ├── image1.jpg
        ├── image2.jpg
        └── ...
    """
    
    if dataset_dir is None:
        dataset_dir = CONFIG['dataset_dir']
    
    # Check if dataset exists
    if not os.path.exists(dataset_dir):
        print(f"\n⚠️  Dataset directory not found: {dataset_dir}")
        print("📁 Creating dataset directory structure...")
        print(f"   Please add training images to:")
        print(f"   • {os.path.join(dataset_dir, 'fresh/')}")
        print(f"   • {os.path.join(dataset_dir, 'rotten/')}")
        Path(os.path.join(dataset_dir, 'fresh')).mkdir(parents=True, exist_ok=True)
        Path(os.path.join(dataset_dir, 'rotten')).mkdir(parents=True, exist_ok=True)
        print("✓ Directories created!")
        return None
    
    # Initialize trainer
    trainer = RotDetectionModelTrainer(CONFIG)
    
    # Create model
    trainer.create_model()
    
    # Prepare data
    train_gen, val_gen = trainer.prepare_data_generators(dataset_dir)
    
    # Train
    trainer.train(train_gen, val_gen)
    
    # Save model
    trainer.save_model()
    
    # Plot results
    trainer.plot_training_history()
    
    return trainer


if __name__ == "__main__":
    print("=" * 60)
    print("AGRIX Rotten Fruit/Vegetable Detection Model Training")
    print("=" * 60)
    
    trainer = train_rot_detection_model()
    
    if trainer:
        print("\n✅ Training completed successfully!")
    else:
        print("\n⚠️  Please add training data and run again.")
