import os
import faiss
import numpy as np
from typing import List

class RAGService:
    def __init__(self):
        self.vector_dim = 384
        self.index_path = "agniassist_data/vector_store/faiss_index/index.faiss"
        self.doc_mapping_path = "agniassist_data/vector_store/faiss_index/doc_map.npy"
        
        try:
            from sentence_transformers import SentenceTransformer
            self.embedder = SentenceTransformer('all-MiniLM-L6-v2') 
        except ImportError:
            self.embedder = None
            
        os.makedirs(os.path.dirname(self.index_path), exist_ok=True)
        
        if os.path.exists(self.index_path):
            self.index = faiss.read_index(self.index_path)
            self.doc_map = np.load(self.doc_mapping_path, allow_pickle=True).item()
        else:
            self.index = faiss.IndexFlatL2(self.vector_dim)
            self.doc_map = {}

    async def retrieve_context(self, query: str, top_k: int = 3) -> str:
        if self.index.ntotal == 0 or not self.embedder:
            return "No institutional knowledge base documents available."
            
        query_vector = self.embedder.encode([query], convert_to_numpy=True)
        distances, indices = self.index.search(query_vector, top_k)
        
        retrieved_texts = []
        for idx in indices[0]:
            if idx != -1 and idx in self.doc_map:
                retrieved_texts.append(self.doc_map[idx])
                
        return "\n\n".join(retrieved_texts)

    def integrate_document(self, text: str):
        if not self.embedder: return
        vector = self.embedder.encode([text], convert_to_numpy=True)
        current_id = self.index.ntotal
        self.index.add(vector)
        self.doc_map[current_id] = text
        
        faiss.write_index(self.index, self.index_path)
        np.save(self.doc_mapping_path, self.doc_map)

rag_service = RAGService()
