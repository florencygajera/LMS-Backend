import logging

logger = logging.getLogger("AgniAssist.LLM")

try:
    from transformers import pipeline, AutoTokenizer, AutoModelForSeq2SeqLM
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logger.warning("Optional 'transformers' library not found. LLM text generation will be disabled.")

class LLMService:
    def __init__(self):
        self.generator = None
        if TRANSFORMERS_AVAILABLE:
            try:
                # Fully standalone inside the python memory heap.
                # 'google/flan-t5-base' (1GB RAM) offers massively improved factual extraction 
                # over the extremely weak 'small' tier without requiring Ollama servers.
                model_name = "google/flan-t5-base"
                logger.info(f"Loading local isolated in-memory model: {model_name}...")
                
                self.tokenizer = AutoTokenizer.from_pretrained(model_name)
                self.model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
                
                self.generator = pipeline(
                    "text2text-generation",
                    model=self.model,
                    tokenizer=self.tokenizer,
                    max_length=1024,
                    truncation=True
                )
                logger.info("Local In-Memory Generation Model Successfully Booted.")
            except Exception as e:
                logger.error(f"Failed to mount local isolated model: {e}")

    async def generate_response(self, prompt: str) -> str:
        if not self.generator:
            return "Internal Error: System is running completely standalone, but the internal AI generation model failed to boot into memory. Please ensure the 'transformers' package is installed natively."
            
        try:
            # Prevent token-limit crash for dense RAG prompts
            if len(prompt.split()) > 1024:
                prompt = " ".join(prompt.split()[:1024])
                
            # Execute inference safely isolated natively on the local footprint
            result = self.generator(
                prompt,
                max_new_tokens=150,
                min_length=15,
                do_sample=False,
                repetition_penalty=1.8,
                early_stopping=True,
                truncation=True
            )
            
            raw_answer = result[0].get('generated_text', "System could not assemble a response.")
            
            # Post-Process: Brutally kill T5 hallucination loops by severing text if it repeats context tags
            cleaned = raw_answer.split("[BATTALION]")[0].split("[EXAM]")[0].split("[TRAINING")[0].strip()
            
            # If the model fails strictly based on constraints:
            if not cleaned or cleaned.isspace():
                return "The exact numerical or factual answer isn't clearly accessible currently."
            
            return cleaned
            
        except Exception as e:
            logger.error(f"Isolated Generation Pipeline failed: {e}")
            return "An internal generation crash occurred within the standalone pipeline."

llm_service = LLMService()
