"""
Generative AI Service
Text summarization using local LLM
"""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("AgniAssist.GenAI")

try:
    from transformers import pipeline, AutoTokenizer, AutoModelForSeq2SeqLM
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logger.warning("Transformers not available")


class GenAIService:
    """Generative AI service for text summarization"""
    
    def __init__(self):
        self.summarizer = None
        self.tokenizer = None
        self.model = None
        self._load_models()
    
    def _load_models(self):
        """Load summarization model"""
        if not TRANSFORMERS_AVAILABLE:
            return
        
        try:
            # Try FLAN-T5 (small, efficient)
            model_name = "google/flan-t5-small"
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
            self.summarizer = pipeline(
                "summarization",
                model=self.model,
                tokenizer=self.tokenizer
            )
            logger.info("✅ FLAN-T5 model loaded")
        except Exception as e:
            logger.warning(f"Could not load FLAN-T5: {e}")
            
            try:
                # Fallback to smaller model
                self.summarizer = pipeline(
                    "summarization",
                    model="sshleifer/distilbart-cnn-12-6"
                )
                logger.info("✅ DistilBART model loaded")
            except:
                logger.warning("Could not load summarization model")
    
    async def summarize(self, text: str, max_length: int = 150, min_length: int = 30) -> Dict[str, Any]:
        """Summarize text"""
        if not self.summarizer:
            # Use extractive summarization fallback
            return self._extractive_summarize(text, max_length)
        
        try:
            # Truncate if too long
            if len(text.split()) > 1024:
                text = " ".join(text.split()[:1024])
            
            result = self.summarizer(
                text,
                max_length=max_length,
                min_length=min_length,
                do_sample=False
            )
            
            summary = result[0]['summary_text']
            
            return {
                "success": True,
                "summary": summary,
                "original_length": len(text.split()),
                "summary_length": len(summary.split()),
                "compression_ratio": len(summary.split()) / len(text.split())
            }
        
        except Exception as e:
            logger.error(f"Summarization failed: {e}")
            return self._extractive_summarize(text, max_length)
    
    def _extractive_summarize(self, text: str, max_length: int = 150) -> Dict[str, Any]:
        """Fallback extractive summarization"""
        # Split into sentences
        import re
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if not sentences:
            return {
                "success": True,
                "summary": text[:max_length],
                "original_length": len(text.split()),
                "summary_length": len(text[:max_length].split()),
                "method": "truncation"
            }
        
        # Score sentences by word frequency
        from collections import Counter
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        word_freq = Counter(words)
        
        # Score each sentence
        scored_sentences = []
        for sent in sentences:
            sent_words = re.findall(r'\b[a-zA-Z]{3,}\b', sent.lower())
            score = sum(word_freq.get(w, 0) for w in sent_words)
            scored_sentences.append((sent, score))
        
        # Sort by score
        scored_sentences.sort(key=lambda x: x[1], reverse=True)
        
        # Take top sentences
        summary_sentences = []
        current_length = 0
        
        for sent, _ in scored_sentences:
            if current_length + len(sent.split()) <= max_length:
                summary_sentences.append(sent)
                current_length += len(sent.split())
            if current_length >= max_length:
                break
        
        summary = ". ".join(summary_sentences)
        if not summary.endswith('.'):
            summary += "."
        
        return {
            "success": True,
            "summary": summary,
            "original_length": len(text.split()),
            "summary_length": len(summary.split()),
            "method": "extractive"
        }
    
    async def generate(self, prompt: str, max_tokens: int = 200) -> str:
        """Generate text from prompt (simple text completion)"""
        if not self.model or not self.tokenizer:
            return self._rule_based_generate(prompt)
        
        try:
            inputs = self.tokenizer(prompt, return_tensors="pt", max_length=512, truncation=True)
            
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=max_tokens,
                num_beams=4,
                do_sample=True,
                temperature=0.7
            )
            
            response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            return response
        
        except Exception as e:
            logger.error(f"Generation failed: {e}")
            return self._rule_based_generate(prompt)
    
    def _rule_based_generate(self, prompt: str) -> str:
        """Simple rule-based response generation"""
        prompt_lower = prompt.lower()
        
        # Template responses
        if "training" in prompt_lower or "fitness" in prompt_lower:
            return "Regular physical training is essential. Daily schedule should include running, strength training, and endurance exercises. Maintain consistency for best results."
        
        if "medical" in prompt_lower or "health" in prompt_lower:
            return "Regular health checkups are important. Maintain BMI between 18.5-25. Report any health issues to medical staff immediately."
        
        if "weapon" in prompt_lower or "shoot" in prompt_lower:
            return "Weapons training requires discipline and practice. Follow all safety protocols. Minimum qualifying score is 35/50 in marksmanship."
        
        if "leave" in prompt_lower:
            return "Leave requests must be submitted 48 hours in advance. Annual leave: 30 days, Sick leave: 15 days, Casual leave: 10 days."
        
        if "emergency" in prompt_lower:
            return "In case of emergency, follow the protocol: 1) Sound alarm 2) Report to Commanding Officer 3) Evacuate if necessary 4) Assemble at designated point."
        
        # Default
        return "Please refer to the training manual for more information. Contact your commanding officer for specific queries."


# Singleton instance
genai_service = GenAIService()
