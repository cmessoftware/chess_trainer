# cluster.py - Agrupa puntos proyectados

from sklearn.cluster import KMeans

def cluster_points(Z, n_clusters=3):
    model = KMeans(n_clusters=n_clusters, random_state=42)
    labels = model.fit_predict(Z)
    return labels, model
