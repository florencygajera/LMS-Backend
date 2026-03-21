import os
import glob
from .rag_service import rag_service

def load_all_documents():
    docs_dir = "agniassist_data/documents"
    categories = ["training", "medical", "recruitment"]
    
    for category in categories:
        cat_path = os.path.join(docs_dir, category)
        if not os.path.exists(cat_path):
            os.makedirs(cat_path)
            continue
            
        for file_path in glob.glob(f"{cat_path}/**/*.txt", recursive=True):
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if content:
                    rag_service.integrate_document(f"[{category.upper()}] " + content)
                    
if __name__ == "__main__":
    load_all_documents()
    print("Local RAG intelligence integration complete.")
