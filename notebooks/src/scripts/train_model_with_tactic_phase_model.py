
import pandas as pd
import numpy as np
import tensorflow as tf
from tensorflow.keras import layers
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
import seaborn as sns
import matplotlib.pyplot as plt

# --- Custom ConditionalBatchNorm ---
class ConditionalBatchNorm(layers.Layer):
    def __init__(self, num_features, num_conditions):
        super().__init__()
        self.bn = layers.BatchNormalization(center=False, scale=False)
        self.gamma = layers.Embedding(num_conditions, num_features)
        self.beta = layers.Embedding(num_conditions, num_features)

    def call(self, x, condition):
        norm = self.bn(x)
        gamma = self.gamma(condition)
        beta = self.beta(condition)
        return gamma * norm + beta

# --- Modelo personalizado ---
class TacticPhaseModel(tf.keras.Model):
    def __init__(self, input_dim, num_phases, num_elo_bins, elo_embed_dim=4):
        super().__init__()
        self.elo_embedding = layers.Embedding(input_dim=num_elo_bins, output_dim=elo_embed_dim)
        self.dense1 = layers.Dense(64)
        self.bn = ConditionalBatchNorm(64, num_phases)
        self.relu = layers.ReLU()
        self.dense2 = layers.Dense(32, activation='relu')
        self.output_layer = layers.Dense(1, activation='sigmoid')

    def call(self, inputs):
        x, phase_id, elo_id = inputs
        elo_vec = self.elo_embedding(elo_id)
        elo_vec = tf.reshape(elo_vec, [tf.shape(x)[0], -1])
        x = tf.concat([x, elo_vec], axis=1)
        x = self.dense1(x)
        x = self.bn(x, phase_id)
        x = self.relu(x)
        x = self.dense2(x)
        return self.output_layer(x)

# --- Carga y preprocesamiento ---
df = pd.read_parquet("training_dataset.parquet")
df = df.dropna(subset=["error_label", "phase", "player_color", "standardized_elo"])

le_phase = LabelEncoder()
df["phase_id"] = le_phase.fit_transform(df["phase"])

le_color = LabelEncoder()
df["color_id"] = le_color.fit_transform(df["player_color"])

elo_bins = [0, 1200, 1400, 1600, 1800, 2000, 2200, 2400, 3000]
df["elo_bin_id"] = pd.cut(df["standardized_elo"], bins=elo_bins, labels=False)
df = df.dropna(subset=["elo_bin_id"])
df["elo_bin_id"] = df["elo_bin_id"].astype(int)

features = ["branching_factor", "self_mobility", "opponent_mobility",
            "is_low_mobility", "material_total", "num_pieces",
            "has_castling_rights", "is_center_controlled", "is_pawn_endgame",
            "is_repetition", "threatens_mate", "is_forced_move",
            "is_tactical_sequence", "standardized_elo", "color_id"]

X = df[features]
y = df["error_label"]
phase_ids = df["phase_id"]
elo_ids = df["elo_bin_id"]

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

X_train, X_test, y_train, y_test, phase_train, phase_test, elo_train, elo_test = train_test_split(
    X_scaled, y, phase_ids, elo_ids, test_size=0.2, random_state=42
)

# --- Instanciar y entrenar modelo ---
model = TacticPhaseModel(
    input_dim=X_train.shape[1],
    num_phases=len(le_phase.classes_),
    num_elo_bins=8
)
model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])

model.fit(
    x=(X_train, phase_train, elo_train),
    y=y_train,
    batch_size=32,
    epochs=10,
    validation_data=((X_test, phase_test, elo_test), y_test)
)

# --- Evaluación ---
y_pred = model.predict((X_test, phase_test, elo_test))
y_pred_bin = (y_pred > 0.5).astype(int)
print(classification_report(y_test, y_pred_bin))
sns.heatmap(confusion_matrix(y_test, y_pred_bin), annot=True)
plt.title("Matriz de confusión")
plt.show()
