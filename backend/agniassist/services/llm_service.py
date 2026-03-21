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
                # 'google/flan-t5-small' is an offline instruction-tuned model. No servers. No APIs.
                model_name = "google/flan-t5-small"
                logger.info(f"Loading local isolated in-memory model: {model_name}...")
                
                self.tokenizer = AutoTokenizer.from_pretrained(model_name)
                self.model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
                
                self.generator = pipeline(
                    "text2text-generation",
                    model=self.model,
                    tokenizer=self.tokenizer,
                    max_length=512,
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
                
            # Execute inference isolated natively on the local CPU/GPU footprint
            result = self.generator(
                prompt,
                max_length=200,
                min_length=10,
                do_sample=False,
                truncation=True
            )
            
            return result[0].get('generated_text', "System could not assemble a response.")
            
        except Exception as e:
            logger.error(f"Isolated Generation Pipeline failed: {e}")
            return "An internal generation crash occurred within the standalone pipeline."

llm_service = LLMService()
