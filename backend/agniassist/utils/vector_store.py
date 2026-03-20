"""
Vector Store using FAISS for RAG
"""

import numpy as np
from typing import List, Tuple, Optional
import pickle
from pathlib import Path


class VectorStore:
    """FAISS-based vector store for document embeddings"""
    
    def __init__(self, dimension: int = 384):
        self.dimension = dimension
        self.embeddings = None
        self.metadata = []
        self.index = None
        self._faiss = None
        self._load_faiss()
    
    def _load_faiss(self):
        """Load FAISS library"""
        try:
            import faiss
            self._faiss = faiss
            self.index = faiss.IndexFlatL2(self.dimension)
        except ImportError:
            # Fallback to simple numpy implementation
            self._faiss = None
            self.embeddings = np.array([])
    
    def add_vectors(self, vectors: np.ndarray, metadata: List[dict]):
        """Add vectors with metadata"""
        if self._faiss is not None:
            # Use FAISS
            vectors = np.array(vectors).astype('float32')
            self.index.add(vectors)
            self.metadata.extend(metadata)
        else:
            # Fallback: store as numpy array
            if self.embeddings is None or len(self.embeddings) == 0:
                self.embeddings = np.array(vectors).astype('float32')
            else:
                self.embeddings = np.vstack([self.embeddings, vectors])
            self.metadata.extend(metadata)
    
    def search(self, query_vector: np.ndarray, k: int = 5) -> List[Tuple[dict, float]]:
        """Search for top k similar vectors"""
        if self._faiss is not None and self.index is not None and self.index.ntotal > 0:
            query = np.array([query_vector]).astype('float32')
            distances, indices = self.index.search(query, min(k, self.index.ntotal))
            
            results = []
            for idx, dist in zip(indices[0], distances[0]):
                if idx < len(self.metadata):
                    results.append((self.metadata[idx], float(dist)))
            return results
        elif self.embeddings is not None and len(self.embeddings) > 0:
            # Fallback: simple cosine similarity
            query = np.array(query_vector).astype('float32')
            similarities = np.dot(self.embeddings, query) / (
                np.linalg.norm(self.embeddings, axis=1) * np.linalg.norm(query) + 1e-8
            )
            top_k = np.argsort(similarities)[-k:][::-1]
            
            results = []
            for idx in top_k:
                if idx < len(self.metadata):
                    results.append((self.metadata[idx], float(1 - similarities[idx])))
            return results
        
        return []
    
    def save(self, path: Path):
        """Save vector store to disk"""
        if self._faiss is not None and self.index is not None:
            self._faiss.write_index(self.index, str(path / "index.faiss"))
        
        with open(path / "metadata.pkl", 'wb') as f:
            pickle.dump(self.metadata, f)
        
        if self.embeddings is not None:
            np.save(path / "embeddings.npy", self.embeddings)
    
    def load(self, path: Path):
        """Load vector store from disk"""
        if self._faiss is not None:
            try:
                self.index = self._faiss.read_index(str(path / "index.faiss"))
            except:
                pass
        
        try:
            with open(path / "metadata.pkl", 'rb') as f:
                self.metadata = pickle.load(f)
        except:
            self.metadata = []
        
        try:
            self.embeddings = np.load(path / "embeddings.npy")
        except:
            pass
    
    def is_empty(self) -> bool:
        """Check if store is empty"""
        if self._faiss is not None and self.index is not None:
            return self.index.ntotal == 0
        return self.embeddings is None or len(self.embeddings) == 0


# Singleton instance
vector_store = VectorStore()
