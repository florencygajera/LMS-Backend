"""
RAG (Retrieval-Augmented Generation) Service
Provides chatbot functionality using local documents
"""

import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
import re
import json

from agniassist.utils.vector_store import vector_store
from agniassist.utils.embeddings import embeddings_generator

logger = logging.getLogger("AgniAssist.RAG")


class RAGService:
    """RAG service for document-based chatbot"""
    
    def __init__(self):
        self.vector_store = vector_store
        self.embeddings = embeddings_generator
        self.documents_dir = Path("agniassist_data/documents")
        self.documents_dir.mkdir(exist_ok=True)
        self.is_initialized = False
    
    async def initialize(self):
        """Initialize the RAG service"""
        logger.info("Initializing RAG Service...")
        
        # Check if index exists
        index_path = self.documents_dir / "index"
        if index_path.exists():
            try:
                self.vector_store.load(index_path)
                logger.info("✅ Loaded existing vector index")
            except Exception as e:
                logger.warning(f"Could not load index: {e}")
        
        # If empty, create sample knowledge base
        if self.vector_store.is_empty():
            await self._create_sample_knowledge_base()
        
        self.is_initialized = True
        logger.info("✅ RAG Service ready")
    
    async def _create_sample_knowledge_base(self):
        """Create sample training manual content"""
        sample_documents = [
            {
                "title": "Physical Training Guidelines",
                "content": """
                Physical training is mandatory for all Agniveer personnel. 
                Daily schedule includes: Running (5km), Push-ups (50), Pull-ups (10), 
                Sit-ups (50), and Marching (2km). Performance is monitored weekly.
                Minimum fitness standards: 1.6km run in 7 minutes, 20 push-ups, 
                8 pull-ups. All personnel must pass the Physical Efficiency Test quarterly.
                """,
                "category": "training"
            },
            {
                "title": "Weapons Training Manual",
                "content": """
                Weapons training includes: Rifle (INSAS), LMG, Grenade throwing, 
                and Field tactics. Safety protocols must be followed at all times.
                Minimum qualifying score: 35/50 in marksmanship test.
                Weekly training sessions of 4 hours mandatory for all riflemen.
                """,
                "category": "weapons"
            },
            {
                "title": "Medical Standards",
                "content": """
                Medical fitness is critical for active duty. Regular health checkups 
                mandatory every 6 months. BMI must be between 18.5-25. Vision standards: 
                6/6 in both eyes. No communicable diseases. Height requirement: 170cm minimum.
                Weight proportional to height. Medical leave requires doctor's certificate.
                """,
                "category": "medical"
            },
            {
                "title": "Code of Conduct",
                "content": """
                All personnel must maintain discipline, punctuality, and professionalism.
                Duty hours: 0600-2000. Leave requests must be submitted 48 hours in advance.
                Uniform must be worn correctly at all times. Salute seniors. 
                Report any suspicious activity immediately. Maintain confidentiality.
                """,
                "category": "conduct"
            },
            {
                "title": "Emergency Protocols",
                "content": """
                In case of emergency: 1) Sound alarm 2) Report to commanding officer 
                3) Follow evacuation plan 4) Assemble at designated point.
                SOS signal: 3 short blasts. First aid kit locations: each barracks.
                Emergency contact: 100 (police), 102 (ambulance), 101 (fire).
                """,
                "category": "emergency"
            },
            {
                "title": "Leave Policy",
                "content": """
                Annual leave: 30 days. Sick leave: 15 days. Casual leave: 10 days.
                Leave request form must be submitted to commanding officer.
                Emergency leave may be granted with proper documentation.
                Long leave (>7 days) requires approval from higher command.
                """,
                "category": "administration"
            }
        ]
        
        # Add documents to vector store
        for doc in sample_documents:
            await self.add_document(doc["title"], doc["content"], doc["category"])
        
        # Save index
        self.vector_store.save(self.documents_dir / "index")
        logger.info(f"✅ Created knowledge base with {len(sample_documents)} documents")
    
    async def add_document(self, title: str, content: str, category: str = "general"):
        """Add a document to the knowledge base"""
        # Split into chunks
        chunks = self._split_into_chunks(content)
        
        # Create embeddings
        embeddings = self.embeddings.encode(chunks)
        
        # Add to vector store with metadata
        metadata = [
            {"title": title, "chunk": chunk, "category": category}
            for chunk in chunks
        ]
        
        self.vector_store.add_vectors(embeddings, metadata)
        
        # Save
        self.vector_store.save(self.documents_dir / "index")
        logger.info(f"Added document: {title} with {len(chunks)} chunks")
    
    def _split_into_chunks(self, text: str, chunk_size: int = 500) -> List[str]:
        """Split text into chunks"""
        # Clean text
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Split by sentences
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk) + len(sentence) < chunk_size:
                current_chunk += ". " + sentence if current_chunk else sentence
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = sentence
        
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks if chunks else [text[:chunk_size]]
    
    async def query(self, query_text: str, top_k: int = 3) -> Dict[str, Any]:
        """Query the RAG system"""
        if not self.is_initialized:
            await self.initialize()
        
        # Generate query embedding
        query_embedding = self.embeddings.encode(query_text)[0]
        
        # Search vector store
        results = self.vector_store.search(query_embedding, k=top_k)
        
        # Format response
        context = "\n\n".join([
            f"[{r[0].get('title', 'Unknown')}] {r[0].get('chunk', '')}"
            for r in results
        ])
        
        # Generate answer using local LLM or rule-based
        answer = await self._generate_answer(query_text, context)
        
        return {
            "answer": answer,
            "sources": [
                {
                    "title": r[0].get("title", "Unknown"),
                    "category": r[0].get("category", "general"),
                    "relevance_score": 1.0 / (r[1] + 1)
                }
                for r in results
            ],
            "context_used": bool(results)
        }
    
    async def _generate_answer(self, query: str, context: str) -> str:
        """Generate answer from context"""
        # Try local LLM first
        try:
            from agniassist.services.genai_service import genai_service
            answer = await genai_service.generate(
                prompt=f"Based on the following context, answer the question.\n\nContext:\n{context}\n\nQuestion: {query}\n\nAnswer:",
                max_tokens=200
            )
            return answer
        except:
            pass
        
        # Fallback: Rule-based answer generation
        query_lower = query.lower()
        
        # Simple keyword matching
        if any(kw in query_lower for kw in ["training", "fitness", "exercise", "run", "push"]):
            if "run" in query_lower or "running" in query_lower:
                return "Daily running schedule is 5km. Minimum standard is 1.6km in 7 minutes."
            if "push" in query_lower:
                return "Daily push-up requirement is 50. Minimum qualifying is 20."
            return "Physical training includes running, push-ups, pull-ups, sit-ups, and marching."
        
        if any(kw in query_lower for kw in ["weapon", "gun", "rifle", "shoot"]):
            return "Weapons training includes INSAS rifle, LMG, and grenade throwing. Minimum qualifying score is 35/50."
        
        if any(kw in query_lower for kw in ["medical", "health", "doctor", "hospital"]):
            return "Medical checkups are required every 6 months. BMI must be 18.5-25. Vision standard is 6/6."
        
        if any(kw in query_lower for kw in ["leave", "vacation", "holiday"]):
            return "Annual leave: 30 days, Sick leave: 15 days, Casual leave: 10 days. Submit forms 48 hours in advance."
        
        if any(kw in query_lower for kw in ["emergency", "sos", "danger", "alarm"]):
            return "In emergency: 1) Sound alarm 2) Report to CO 3) Evacuate 4) Assemble. SOS: 3 short blasts."
        
        # Default response
        if context:
            return f"I found relevant information in the training manual. {context[:200]}..."
        
        return "I don't have specific information about that. Please contact your commanding officer for details."


# Singleton instance
rag_service = RAGService()



