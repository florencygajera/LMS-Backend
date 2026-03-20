"""
Text Embeddings using local models
"""

import numpy as np
from typing import List, Union
import logging

logger = logging.getLogger("AgniAssist.Embeddings")


class EmbeddingsGenerator:
    """Generate text embeddings using local models"""
    
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """Load the embedding model"""
        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(self.model_name)
            logger.info(f"✅ Loaded embedding model: {self.model_name}")
        except ImportError:
            logger.warning("sentence-transformers not available, using TF-IDF fallback")
            self.model = "tfidf"
        except Exception as e:
            logger.warning(f"Failed to load model: {e}, using TF-IDF fallback")
            self.model = "tfidf"
    
    def encode(self, texts: Union[str, List[str]], **kwargs) -> np.ndarray:
        """Generate embeddings for text"""
        if isinstance(texts, str):
            texts = [texts]
        
        if self.model == "tfidf":
            return self._tfidf_encode(texts)
        
        try:
            embeddings = self.model.encode(texts, **kwargs)
            return embeddings
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            return self._tfidf_encode(texts)
    
    def _tfidf_encode(self, texts: List[str]) -> np.ndarray:
        """Fallback TF-IDF encoding"""
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            vectorizer = TfidfVectorizer(max_features=384)
            return vectorizer.fit_transform(texts).toarray()
        except:
            # Last resort: random embeddings
            return np.random.randn(len(texts), 384)
    
    def get_embedding_dimension(self) -> int:
        """Get embedding dimension"""
        if self.model == "tfidf":
            return 384
        return self.model.get_sentence_embedding_dimension()


# Singleton instance
embeddings_generator = EmbeddingsGenerator()





