#!/usr/bin/env python3
"""
PHASE 5A - CNN Board Position Analysis
=====================================

Objective: Surpass Phase 3 record (F1=0.9988) using Convolutional Neural Networks
Target: F1 > 0.995 through spatial chess pattern recognition

Architecture:
- Input: 8x8x12 board representation (piece types × colors)  
- CNN: Multiple conv blocks with increasing filters
- Global pooling + dense layers for classification
- Advanced techniques: Data augmentation, regularization
"""
import os
import sys
import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow.keras.models import Model
from tensorflow.keras.layers import (
    Input, Conv2D, BatchNormalization, Activation, MaxPooling2D,
    GlobalAveragePooling2D, Dense, Dropout, Concatenate
)
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau, ModelCheckpoint
from tensorflow.keras.utils import to_categorical
from sklearn.model_selection import train_test_split, StratifiedKFold
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import f1_score, accuracy_score, classification_report
from sklearn.utils.class_weight import compute_class_weight
from sqlalchemy import create_engine
import warnings
warnings.filterwarnings('ignore')

# Configure encoding for Windows
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# GPU configuration
physical_devices = tf.config.experimental.list_physical_devices('GPU')
if len(physical_devices) > 0:
    tf.config.experimental.set_memory_growth(physical_devices[0], True)
    print("✅ GPU detectada y configurada")
else:
    print("ℹ️ Usando CPU - considera GPU para mejor rendimiento")

def create_board_representation():
    """Create synthetic chess board representations for demonstration"""
    print("[+] Generando representaciones de tablero sintéticas...")
    
    np.random.seed(42)
    n_positions = 5000  # Reduced for demonstration
    
    # Piece encoding: [empty, pawn, rook, knight, bishop, queen, king] × [white, black]
    # 12 channels total: 6 piece types × 2 colors
    board_positions = []
    labels = []
    
    # Error types with different board characteristics
    error_patterns = {
        'good': {'material_balance': 0, 'king_safety': 0.8, 'piece_activity': 0.7},
        'inaccuracy': {'material_balance': -0.5, 'king_safety': 0.6, 'piece_activity': 0.6},
        'mistake': {'material_balance': -1.5, 'king_safety': 0.4, 'piece_activity': 0.4},
        'blunder': {'material_balance': -3.0, 'king_safety': 0.2, 'piece_activity': 0.3}
    }
    
    for i in range(n_positions):
        # Randomly choose error type
        error_type = np.random.choice(list(error_patterns.keys()), 
                                    p=[0.6, 0.25, 0.1, 0.05])  # Realistic distribution
        pattern = error_patterns[error_type]
        
        # Create 8x8x12 board representation
        board = np.zeros((8, 8, 12), dtype=np.float32)
        
        # Add pieces based on error pattern (simplified simulation)
        # White pieces (channels 0-5), Black pieces (channels 6-11)
        
        # King positions (always present)
        white_king_pos = (np.random.randint(0, 8), np.random.randint(0, 8))
        black_king_pos = (np.random.randint(0, 8), np.random.randint(0, 8))
        board[white_king_pos[0], white_king_pos[1], 5] = 1.0  # White king
        board[black_king_pos[0], black_king_pos[1], 11] = 1.0  # Black king
        
        # Add random pieces influenced by error pattern
        n_pieces = max(8, int(16 + pattern['material_balance'] * 2))
        
        for _ in range(n_pieces):
            pos = (np.random.randint(0, 8), np.random.randint(0, 8))
            if board[pos[0], pos[1]].sum() == 0:  # Empty square
                piece_type = np.random.randint(0, 5)  # Pawn to queen
                is_white = np.random.choice([True, False])
                channel = piece_type + (0 if is_white else 6)
                board[pos[0], pos[1], channel] = 1.0
        
        # Add noise based on king safety and piece activity
        noise_factor = 1.0 - pattern['king_safety']
        if np.random.random() < noise_factor:
            # Add "unsafe" patterns near kings
            for dx, dy in [(-1,-1), (-1,0), (-1,1), (0,-1), (0,1), (1,-1), (1,0), (1,1)]:
                kx, ky = white_king_pos
                nx, ny = kx + dx, ky + dy
                if 0 <= nx < 8 and 0 <= ny < 8:
                    # Reduced piece activity near king (vulnerability)
                    board[nx, ny] *= pattern['piece_activity']
        
        board_positions.append(board)
        labels.append(error_type)
    
    X = np.array(board_positions)
    y = np.array(labels)
    
    print(f"[OK] {len(X)} posiciones de tablero generadas")
    print(f"[INFO] Board shape: {X.shape}")
    print(f"[INFO] Distribución de etiquetas:")
    unique, counts = np.unique(y, return_counts=True)
    for label, count in zip(unique, counts):
        print(f"   {label:12}: {count:4} ({count/len(y)*100:5.1f}%)")
    
    return X, y

def create_cnn_model(input_shape=(8, 8, 12), num_classes=4):
    """Create advanced CNN architecture for board position analysis"""
    
    inputs = Input(shape=input_shape, name='board_input')
    
    # First conv block - detect basic patterns
    x = Conv2D(32, (3, 3), padding='same')(inputs)
    x = BatchNormalization()(x)
    x = Activation('relu')(x)
    x = Conv2D(32, (3, 3), padding='same')(x)
    x = BatchNormalization()(x)
    x = Activation('relu')(x)
    x = MaxPooling2D((2, 2))(x)
    x = Dropout(0.25)(x)
    
    # Second conv block - piece interactions
    x = Conv2D(64, (3, 3), padding='same')(x)
    x = BatchNormalization()(x)
    x = Activation('relu')(x)
    x = Conv2D(64, (3, 3), padding='same')(x)
    x = BatchNormalization()(x)
    x = Activation('relu')(x)
    x = MaxPooling2D((2, 2))(x)
    x = Dropout(0.25)(x)
    
    # Third conv block - complex patterns
    x = Conv2D(128, (3, 3), padding='same')(x)
    x = BatchNormalization()(x)
    x = Activation('relu')(x)
    x = Conv2D(128, (3, 3), padding='same')(x)
    x = BatchNormalization()(x)
    x = Activation('relu')(x)
    x = Dropout(0.25)(x)
    
    # Global pooling and classification head
    x = GlobalAveragePooling2D()(x)
    x = Dense(256, activation='relu')(x)
    x = Dropout(0.5)(x)
    x = Dense(128, activation='relu')(x)
    x = Dropout(0.5)(x)
    
    # Output layer
    outputs = Dense(num_classes, activation='softmax', name='predictions')(x)
    
    model = Model(inputs=inputs, outputs=outputs, name='ChessCNN')
    
    return model

def train_cnn_model(X, y, test_size=0.2, epochs=50):
    """Train CNN model with advanced techniques"""
    
    print("\n[+] Preparando datos para entrenamiento...")
    
    # Encode labels
    label_encoder = LabelEncoder()
    y_encoded = label_encoder.fit_transform(y)
    y_categorical = to_categorical(y_encoded, num_classes=len(label_encoder.classes_))
    
    # Train/validation split
    X_train, X_val, y_train, y_val = train_test_split(
        X, y_categorical, test_size=test_size, random_state=42, 
        stratify=y_encoded
    )
    
    print(f"[OK] Train: {len(X_train)}, Validation: {len(X_val)}")
    
    # Class weights for imbalanced data
    class_weights = compute_class_weight(
        'balanced', 
        classes=np.arange(len(label_encoder.classes_)), 
        y=y_encoded
    )
    class_weight_dict = dict(enumerate(class_weights))
    
    print("[INFO] Class weights:", {label_encoder.classes_[i]: f"{w:.2f}" 
                                   for i, w in class_weight_dict.items()})
    
    # Create model
    print("\n[+] Creando modelo CNN...")
    model = create_cnn_model(input_shape=X.shape[1:], num_classes=len(label_encoder.classes_))
    
    # Compile model
    model.compile(
        optimizer=Adam(learning_rate=0.001),
        loss='categorical_crossentropy',
        metrics=['accuracy']
    )
    
    print(f"[OK] Modelo compilado: {model.count_params():,} parámetros")
    
    # Callbacks
    callbacks = [
        EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True),
        ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=5, min_lr=1e-7),
        ModelCheckpoint('phase5_cnn_best.h5', monitor='val_loss', save_best_only=True)
    ]
    
    # Train model
    print(f"\n[+] Entrenando CNN por {epochs} épocas...")
    
    history = model.fit(
        X_train, y_train,
        validation_data=(X_val, y_val),
        epochs=epochs,
        batch_size=32,
        class_weight=class_weight_dict,
        callbacks=callbacks,
        verbose=1
    )
    
    return model, history, label_encoder

def evaluate_model(model, X_val, y_val, label_encoder):
    """Comprehensive model evaluation"""
    
    print("\n[+] Evaluando modelo CNN...")
    
    # Predictions
    y_pred_proba = model.predict(X_val, verbose=0)
    y_pred_classes = np.argmax(y_pred_proba, axis=1)
    
    # Convert back to original labels
    y_true_labels = label_encoder.inverse_transform(np.argmax(y_val, axis=1))
    y_pred_labels = label_encoder.inverse_transform(y_pred_classes)
    
    # Calculate metrics
    f1_macro = f1_score(y_true_labels, y_pred_labels, average='macro')
    accuracy = accuracy_score(y_true_labels, y_pred_labels)
    
    print(f"\n[RESULTS] CNN Performance:")
    print(f"F1 Macro: {f1_macro:.6f}")
    print(f"Accuracy: {accuracy:.6f}")
    
    # Detailed classification report
    print(f"\n[DETAILED REPORT]")
    print(classification_report(y_true_labels, y_pred_labels))
    
    return f1_macro, accuracy

# Main execution
if __name__ == "__main__":
    print("="*70)
    print("  PHASE 5A - CNN BOARD POSITION ANALYSIS")
    print("="*70)
    
    # Phase baselines for comparison
    PHASE3_BASELINE = 0.9988
    PHASE5_TARGET = 0.9995
    
    print(f"\n[BASELINE] Phase 3 Temporal: F1={PHASE3_BASELINE:.4f}")
    print(f"[TARGET] Phase 5A CNN: F1>{PHASE5_TARGET:.4f}")
    
    try:
        # 1. Generate synthetic board data
        X_board, y_board = create_board_representation()
        
        # 2. Train CNN model
        model, history, label_encoder = train_cnn_model(X_board, y_board, epochs=30)
        
        # 3. Final evaluation
        _, y_encoded = np.unique(y_board, return_inverse=True)
        y_categorical = to_categorical(y_encoded)
        
        # Use validation set for final evaluation
        X_train, X_val, y_train, y_val = train_test_split(
            X_board, y_categorical, test_size=0.2, random_state=42, stratify=y_encoded
        )
        
        f1_final, acc_final = evaluate_model(model, X_val, y_val, label_encoder)
        
        # 4. Compare with baselines
        print(f"\n" + "="*50)
        print("  PHASE 5A RESULTS SUMMARY")
        print("="*50)
        
        print(f"✅ CNN F1 Score: {f1_final:.6f}")
        print(f"✅ CNN Accuracy: {acc_final:.6f}")
        
        improvement = f1_final - PHASE3_BASELINE
        success = f1_final > PHASE5_TARGET
        
        if success:
            print(f"🎉 PHASE 5A SUCCESSFUL! (+{improvement:.4f} vs Phase 3)")
            print("📈 CNN supera el target establecido")
            if f1_final >= 0.999:
                print("🏆 MILESTONE: 99.9%+ accuracy achieved!")
        else:
            print(f"⚠️ Phase 5A target not met (need {PHASE5_TARGET:.4f})")
            print(f"💡 Consider: more data, architecture changes, or hypertuning")
        
        print(f"\n📊 Next: Implement LSTM temporal model for Phase 5B")
        print(f"🎯 Ultimate goal: Ensemble F1 > 0.999")
        
    except Exception as e:
        print(f"[ERROR] Phase 5A failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)