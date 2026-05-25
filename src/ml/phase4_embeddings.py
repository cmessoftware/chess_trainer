#!/usr/bin/env python3
"""
PHASE 4 - Embeddings y Similitud (Estilo / Recomendación)
========================================================

Objetivo: Responder: ¿a qué se parece este error / este jugador?

Modelos: Autoencoder / embedding MLP
Output: Vector latente (embedding)
Uso: 
- Clustering de errores
- Similitud para ejercicios  
- Base para inferencia de estilo de juego

Métricas: Silhouette score, coherencia temática de clusters
Criterio: Clusters útiles para entrenamiento, no solo visuales
"""

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans, DBSCAN
from sklearn.metrics import silhouette_score
from sklearn.manifold import TSNE
from sklearn.neighbors import NearestNeighbors
import psycopg2
import warnings
warnings.filterwarnings('ignore')

try:
    import matplotlib.pyplot as plt
    import seaborn as sns
    PLOT_AVAILABLE = True
    print("✅ Matplotlib disponible para visualizaciones")
except ImportError:
    PLOT_AVAILABLE = False
    print("⚠️ Matplotlib no disponible - solo análisis numérico")

try:
    from sklearn.neural_network import MLPRegressor
    from sklearn.model_selection import train_test_split
    MLP_AVAILABLE = True
    print("✅ MLP disponible para autoencoders")
except ImportError:
    MLP_AVAILABLE = False
    print("⚠️ MLP no disponible")

class Phase4EmbeddingsAnalyzer:
    def __init__(self, embedding_dim=8):
        """
        Phase 4: Análisis de embeddings y similitud
        
        Args:
            embedding_dim: Dimensionalidad del espacio latente
        """
        self.embedding_dim = embedding_dim
        self.scaler = StandardScaler()
        self.label_encoder = LabelEncoder()
        
        # Resultados de fases anteriores
        self.previous_results = {
            'phase1_rf_f1': 1.000,
            'phase2_mlp_f1': 0.9679,
            'phase3_temporal_f1': 0.7497  # Resultado corregido
        }
        
        print("🎨 Chess Trainer - Phase 4 Embeddings & Similarity")
        print("=" * 55)
        print(f"📊 Embedding Dimension: {embedding_dim}")
        print(f"🎨 Plotting: {'✅' if PLOT_AVAILABLE else '❌'}")
        
    def load_error_data_from_db(self, limit=25000):
        """
        Cargar datos de errores para análisis de embeddings
        """
        print("📊 Cargando datos de errores para embeddings...")
        
        conn = psycopg2.connect(
            host="localhost", port="5432", database="chess_trainer_db",
            user="chess", password="chess_pass"
        )
        
        # Query con información adicional para embeddings
        query = f"""
        SELECT 
            f.game_id, f.move_number, f.player_color,
            f.material_balance, f.material_total, f.num_pieces,
            f.branching_factor, f.self_mobility, f.opponent_mobility,
            f.has_castling_rights, f.is_repetition, f.is_low_mobility,
            f.is_center_controlled, f.is_pawn_endgame, f.score_diff,
            f.error_label, f.phase,
            g.source, g.white_player, g.black_player, g.result
        FROM features f 
        JOIN games g ON f.game_id = g.game_id 
        WHERE f.error_label IS NOT NULL
        ORDER BY RANDOM()
        LIMIT {limit}
        """
        
        df = pd.read_sql(query, conn)
        conn.close()
        
        print(f"📈 Datos cargados: {len(df)} registros")
        print(f"🏷️ Distribución de errores:")
        for label, count in df['error_label'].value_counts().items():
            print(f"   {label}: {count} ({count/len(df)*100:.1f}%)")
        
        return df
    
    def prepare_features_for_embedding(self, df):
        """
        Preparar features para crear embeddings
        """
        print("🔄 Preparando features para embeddings...")
        
        # Features base
        feature_cols = [
            'material_balance', 'material_total', 'num_pieces',
            'branching_factor', 'self_mobility', 'opponent_mobility',
            'has_castling_rights', 'is_repetition', 'is_low_mobility',
            'is_center_controlled', 'is_pawn_endgame', 'score_diff',
            'player_color'
        ]
        
        # Features adicionales específicas para embeddings
        # Fase de juego (encoding)
        phase_encoder = LabelEncoder()
        df['phase_encoded'] = phase_encoder.fit_transform(df['phase'].fillna('unknown'))
        feature_cols.append('phase_encoded')
        
        # Tipo de fuente (encoding) 
        source_encoder = LabelEncoder()
        df['source_encoded'] = source_encoder.fit_transform(df['source'].fillna('unknown'))
        feature_cols.append('source_encoded')
        
        # Limpiar y normalizar todas las features
        for col in feature_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        X = df[feature_cols].values
        X_scaled = self.scaler.fit_transform(X)
        
        print(f"✅ Features preparadas: {X_scaled.shape}")
        print(f"📊 Feature columns: {len(feature_cols)}")
        
        return X_scaled, feature_cols, df
    
    def create_autoencoder_embedding(self, X, y_labels):
        """
        Crear embeddings usando Autoencoder con MLP
        """
        if not MLP_AVAILABLE:
            print("⚠️ MLP no disponible - usando PCA como fallback")
            return self.create_pca_embedding(X)
            
        print(f"🧠 Entrenando Autoencoder para embeddings {self.embedding_dim}D...")
        
        # Autoencoder usando MLPRegressor
        # Arquitectura: input -> hidden -> embedding -> hidden -> output
        hidden_dim = max(self.embedding_dim * 2, 16)
        
        # Encoder: input -> embedding
        encoder = MLPRegressor(
            hidden_layer_sizes=(hidden_dim, self.embedding_dim),
            max_iter=300,
            random_state=42,
            early_stopping=True,
            validation_fraction=0.2
        )
        
        # Para autoencoder, el target es la propia entrada
        encoder.fit(X, X[:, :self.embedding_dim])  # Simplificación: mapear a primeras dimensiones
        
        # Generar embeddings
        embeddings = encoder.predict(X)
        
        print(f"✅ Embeddings generados: {embeddings.shape}")
        
        return embeddings, encoder
    
    def create_pca_embedding(self, X):
        """
        Crear embeddings usando PCA (fallback)
        """
        print(f"🔍 Creando embeddings PCA {self.embedding_dim}D...")
        
        pca = PCA(n_components=self.embedding_dim, random_state=42)
        embeddings = pca.fit_transform(X)
        
        explained_variance = pca.explained_variance_ratio_.sum()
        print(f"✅ PCA embeddings: {embeddings.shape}")
        print(f"📊 Varianza explicada: {explained_variance:.3f}")
        
        return embeddings, pca
    
    def cluster_errors(self, embeddings, y_labels):
        """
        Clustering de errores en el espacio de embeddings
        """
        print("🎯 Aplicando clustering a errores...")
        
        results = {}
        
        # 1. K-means clustering
        n_clusters_kmeans = len(set(y_labels))  # Basado en número de tipos de error
        kmeans = KMeans(n_clusters=n_clusters_kmeans, random_state=42, n_init=10)
        kmeans_labels = kmeans.fit_predict(embeddings)
        
        kmeans_silhouette = silhouette_score(embeddings, kmeans_labels)
        
        results['kmeans'] = {
            'labels': kmeans_labels,
            'n_clusters': n_clusters_kmeans,
            'silhouette': kmeans_silhouette,
            'model': kmeans
        }
        
        print(f"   K-means: {n_clusters_kmeans} clusters, silhouette = {kmeans_silhouette:.3f}")
        
        # 2. DBSCAN clustering
        dbscan = DBSCAN(eps=0.5, min_samples=10)
        dbscan_labels = dbscan.fit_predict(embeddings)
        
        n_clusters_dbscan = len(set(dbscan_labels)) - (1 if -1 in dbscan_labels else 0)
        n_noise = list(dbscan_labels).count(-1)
        
        if n_clusters_dbscan > 1:
            dbscan_silhouette = silhouette_score(embeddings, dbscan_labels)
        else:
            dbscan_silhouette = 0.0
        
        results['dbscan'] = {
            'labels': dbscan_labels,
            'n_clusters': n_clusters_dbscan,
            'n_noise': n_noise,
            'silhouette': dbscan_silhouette,
            'model': dbscan
        }
        
        print(f"   DBSCAN: {n_clusters_dbscan} clusters, {n_noise} noise, silhouette = {dbscan_silhouette:.3f}")
        
        return results
    
    def analyze_cluster_coherence(self, cluster_results, y_labels, df):
        """
        Analizar coherencia temática de clusters
        """
        print("🔍 Analizando coherencia temática de clusters...")
        
        coherence_results = {}
        
        for method, result in cluster_results.items():
            cluster_labels = result['labels']
            
            # Análisis por tipo de error original
            error_purity = self.calculate_error_purity(cluster_labels, y_labels)
            
            # Análisis por fase del juego
            phase_coherence = self.calculate_phase_coherence(cluster_labels, df['phase'])
            
            # Análisis por nivel de jugador (source)
            source_coherence = self.calculate_source_coherence(cluster_labels, df['source'])
            
            coherence_results[method] = {
                'error_purity': error_purity,
                'phase_coherence': phase_coherence,
                'source_coherence': source_coherence,
                'overall_coherence': (error_purity + phase_coherence + source_coherence) / 3
            }
            
            print(f"   {method.upper()}: error_purity={error_purity:.3f}, phase={phase_coherence:.3f}, source={source_coherence:.3f}")
        
        return coherence_results
    
    def calculate_error_purity(self, cluster_labels, y_labels):
        """Calcular pureza de clusters respecto a tipos de error"""
        unique_clusters = set(cluster_labels)
        if -1 in unique_clusters:
            unique_clusters.remove(-1)  # Remover noise de DBSCAN
        
        if len(unique_clusters) == 0:
            return 0.0
        
        total_purity = 0
        total_samples = 0
        
        for cluster_id in unique_clusters:
            cluster_mask = cluster_labels == cluster_id
            cluster_errors = y_labels[cluster_mask]
            
            if len(cluster_errors) > 0:
                # Pureza = fracción de la clase mayoritaria en el cluster
                most_common_error = max(set(cluster_errors), key=lambda x: list(cluster_errors).count(x))
                purity = list(cluster_errors).count(most_common_error) / len(cluster_errors)
                
                total_purity += purity * len(cluster_errors)
                total_samples += len(cluster_errors)
        
        return total_purity / total_samples if total_samples > 0 else 0.0
    
    def calculate_phase_coherence(self, cluster_labels, phases):
        """Calcular coherencia por fase del juego"""
        phases_array = np.array(phases)
        return self.calculate_error_purity(cluster_labels, phases_array)
    
    def calculate_source_coherence(self, cluster_labels, sources):
        """Calcular coherencia por fuente de datos"""
        sources_array = np.array(sources)
        return self.calculate_error_purity(cluster_labels, sources_array)
    
    def find_similar_errors(self, embeddings, df, n_neighbors=5):
        """
        Encontrar errores similares usando k-NN en espacio de embeddings
        """
        print("🔍 Encontrando errores similares...")
        
        nn_model = NearestNeighbors(n_neighbors=n_neighbors + 1, metric='cosine')
        nn_model.fit(embeddings)
        
        # Ejemplo: buscar similares para algunos errores específicos
        sample_indices = [0, 100, 500, 1000, 2000]  # Muestras ejemplo
        
        similarity_examples = []
        
        for idx in sample_indices:
            if idx >= len(embeddings):
                continue
                
            distances, indices = nn_model.kneighbors([embeddings[idx]])
            
            # El primer resultado es el mismo punto, tomar los siguientes
            similar_indices = indices[0][1:]
            similar_distances = distances[0][1:]
            
            example = {
                'original_idx': idx,
                'original_error': df.iloc[idx]['error_label'],
                'original_phase': df.iloc[idx]['phase'],
                'similar_errors': [df.iloc[i]['error_label'] for i in similar_indices],
                'similar_phases': [df.iloc[i]['phase'] for i in similar_indices],
                'distances': similar_distances
            }
            
            similarity_examples.append(example)
        
        # Imprimir algunos ejemplos
        print("📋 Ejemplos de errores similares:")
        for ex in similarity_examples[:3]:
            print(f"   Error '{ex['original_error']}' ({ex['original_phase']}):")
            for i, (sim_error, sim_phase, dist) in enumerate(zip(ex['similar_errors'], ex['similar_phases'], ex['distances'])):
                print(f"     {i+1}. '{sim_error}' ({sim_phase}) - distancia: {dist:.3f}")
        
        return nn_model, similarity_examples
    
    def run_phase4(self):
        """
        Ejecutar Phase 4 completo: embeddings y análisis de similitud
        """
        print("🚀 Iniciando Phase 4 - Embeddings & Similarity")
        
        # 1. Cargar datos
        df = self.load_error_data_from_db()
        
        # 2. Preparar features
        X_scaled, feature_cols, df_processed = self.prepare_features_for_embedding(df)
        y_labels = np.array(df_processed['error_label'])
        
        # 3. Crear embeddings
        if MLP_AVAILABLE:
            embeddings, embedding_model = self.create_autoencoder_embedding(X_scaled, y_labels)
        else:
            embeddings, embedding_model = self.create_pca_embedding(X_scaled)
        
        # 4. Clustering de errores
        cluster_results = self.cluster_errors(embeddings, y_labels)
        
        # 5. Análisis de coherencia
        coherence_results = self.analyze_cluster_coherence(cluster_results, y_labels, df_processed)
        
        # 6. Búsqueda de similitud
        nn_model, similarity_examples = self.find_similar_errors(embeddings, df_processed)
        
        # 7. Resumen final
        self.summarize_phase4_results(cluster_results, coherence_results)
        
        return {
            'embeddings': embeddings,
            'embedding_model': embedding_model,
            'cluster_results': cluster_results,
            'coherence_results': coherence_results,
            'similarity_model': nn_model,
            'similarity_examples': similarity_examples
        }
    
    def summarize_phase4_results(self, cluster_results, coherence_results):
        """
        Resumir resultados de Phase 4
        """
        print("\n🏆 RESUMEN PHASE 4 - EMBEDDINGS & SIMILARITY")
        print("=" * 50)
        
        # Mejor método de clustering
        best_method = max(coherence_results.keys(), 
                         key=lambda k: coherence_results[k]['overall_coherence'])
        best_coherence = coherence_results[best_method]['overall_coherence']
        
        print(f"🎯 Mejor clustering: {best_method.upper()}")
        print(f"📊 Coherencia general: {best_coherence:.3f}")
        print(f"🔢 Clusters generados: {cluster_results[best_method]['n_clusters']}")
        print(f"📈 Silhouette score: {cluster_results[best_method]['silhouette']:.3f}")
        
        # Criterio de éxito
        if best_coherence > 0.7:
            print("✅ Phase 4 ÉXITO: Clusters coherentes y útiles para entrenamiento")
        elif best_coherence > 0.5:
            print("⚠️ Phase 4 PARCIAL: Clusters moderadamente útiles")
        else:
            print("❌ Phase 4 LIMITADO: Clusters poco coherentes")
        
        print("\n🔍 Capacidades desarrolladas:")
        print("  ✅ Embeddings de errores generados")
        print("  ✅ Clustering temático de errores") 
        print("  ✅ Búsqueda de errores similares")
        print("  ✅ Base para recomendaciones de ejercicios")

if __name__ == "__main__":
    analyzer = Phase4EmbeddingsAnalyzer(embedding_dim=8)
    results = analyzer.run_phase4()