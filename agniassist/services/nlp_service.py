"""
NLP Service for Entity Extraction
Extracts entities from text using local models
"""

import logging
import re
from typing import Dict, Any, List, Set
from pathlib import Path

logger = logging.getLogger("AgniAssist.NLP")

try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False
    logger.warning("SpaCy not available")


class NLPService:
    """NLP service for entity extraction and text processing"""
    
    def __init__(self):
        self.nlp = None
        self._load_models()
    
    def _load_models(self):
        """Load NLP models"""
        if SPACY_AVAILABLE:
            try:
                self.nlp = spacy.load("en_core_web_sm")
                logger.info("✅ SpaCy model loaded")
            except:
                try:
                    # Try to download
                    import subprocess
                    subprocess.run(["python", "-m", "spacy", "download", "en_core_web_sm"])
                    self.nlp = spacy.load("en_core_web_sm")
                except:
                    logger.warning("Could not load SpaCy model")
        
        if not self.nlp:
            logger.info("Using rule-based NLP")
    
    async def extract_entities(self, text: str) -> Dict[str, Any]:
        """Extract named entities from text"""
        entities = {
            "persons": [],
            "organizations": [],
            "locations": [],
            "dates": [],
            "numbers": [],
            "military_terms": []
        }
        
        if self.nlp:
            try:
                doc = self.nlp(text)
                
                # Extract named entities
                for ent in doc.ents:
                    if ent.label_ == "PERSON":
                        entities["persons"].append(ent.text)
                    elif ent.label_ == "ORG":
                        entities["organizations"].append(ent.text)
                    elif ent.label_ in ["GPE", "LOC"]:
                        entities["locations"].append(ent.text)
                    elif ent.label_ == "DATE":
                        entities["dates"].append(ent.text)
                    elif ent.label_ == "CARDINAL":
                        entities["numbers"].append(ent.text)
            except Exception as e:
                logger.error(f"Entity extraction failed: {e}")
        
        # Rule-based extraction as fallback/supplement
        entities = self._rule_based_extraction(text, entities)
        
        # Extract military-specific terms
        entities["military_terms"] = self._extract_military_terms(text)
        
        return {
            "success": True,
            "entities": entities,
            "text_length": len(text)
        }
    
    def _rule_based_extraction(self, text: str, entities: Dict) -> Dict:
        """Rule-based entity extraction"""
        
        # Extract dates (various formats)
        date_patterns = [
            r'\d{1,2}[-/]\d{1,2}[-/]\d{2,4}',
            r'\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}',
            r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4}'
        ]
        for pattern in date_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            entities["dates"].extend(matches)
        
        # Extract phone numbers
        phone_pattern = r'\+?\d{1,3}[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
        phones = re.findall(phone_pattern, text)
        entities["numbers"].extend(phones[:3])
        
        # Extract Aadhaar (12 digits)
        aadhaar = re.findall(r'\b\d{12}\b', text)
        if aadhaar:
            entities["numbers"].extend(aadhaar)
        
        # Extract PIN codes
        pins = re.findall(r'\b\d{6}\b', text)
        entities["locations"].extend(pins)
        
        # Extract emails
        emails = re.findall(r'\b[\w.-]+@[\w.-]+\.\w+\b', text)
        entities["organizations"].extend(emails)
        
        # Remove duplicates
        for key in entities:
            entities[key] = list(set(entities[key]))[:10]  # Limit to 10
        
        return entities
    
    def _extract_military_terms(self, text: str) -> List[str]:
        """Extract military-specific terminology"""
        military_terms = [
            "INSAS", "LMG", "Rifle", "AK-47", "Grenade",
            "Battalion", "Regiment", "Division", "Corps",
            "Sepoy", "Lance Naik", "Naik", "Havildar",
            "CO", "XO", "OC", "PI", "VQ",
            "PT", "Battle", "Drill", "March", "Deployment",
            "SOS", "Alert", "Emergency", "Roll Call",
            "RTO", "MR", "Medical", "Fitness", "Training"
        ]
        
        found = []
        text_upper = text.upper()
        
        for term in military_terms:
            if term.upper() in text_upper:
                found.append(term)
        
        return found[:10]
    
    async def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """Analyze sentiment of text"""
        # Simple rule-based sentiment
        positive_words = [
            "good", "great", "excellent", "outstanding", "success", "pass",
            "qualified", "fit", "healthy", "improved", "better", "best"
        ]
        negative_words = [
            "bad", "poor", "fail", "failed", "sick", "ill", "injury",
            "weak", "worst", "risk", "danger", "warning", "concern"
        ]
        
        text_lower = text.lower()
        
        positive_count = sum(1 for w in positive_words if w in text_lower)
        negative_count = sum(1 for w in negative_words if w in text_lower)
        
        if positive_count > negative_count:
            sentiment = "positive"
        elif negative_count > positive_count:
            sentiment = "negative"
        else:
            sentiment = "neutral"
        
        return {
            "success": True,
            "sentiment": sentiment,
            "positive_score": positive_count,
            "negative_score": negative_count
        }
    
    async def extract_keywords(self, text: str, top_n: int = 10) -> List[str]:
        """Extract keywords from text"""
        # Remove stopwords
        stopwords = {
            "the", "a", "an", "is", "are", "was", "were", "be", "been",
            "being", "have", "has", "had", "do", "does", "did", "will",
            "would", "could", "should", "may", "might", "must", "shall",
            "can", "need", "dare", "ought", "used", "to", "of", "in",
            "for", "on", "with", "at", "by", "from", "as", "into",
            "through", "during", "before", "after", "above", "below",
            "between", "under", "again", "further", "then", "once"
        }
        
        # Tokenize and clean
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        words = [w for w in words if w not in stopwords]
        
        # Count frequency
        from collections import Counter
        word_freq = Counter(words)
        
        # Get top N
        return [word for word, _ in word_freq.most_common(top_n)]


# Singleton instance
nlp_service = NLPService()
