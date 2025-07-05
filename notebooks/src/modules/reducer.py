# reducer.py - Aplica PCA

from sklearn.decomposition import PCA

def apply_pca(X, n_components=2):
    pca = PCA(n_components=n_components)
    Z = pca.fit_transform(X)
    return pca, Z
