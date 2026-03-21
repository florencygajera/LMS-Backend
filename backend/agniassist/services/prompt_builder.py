import json

class PromptBuilder:
    def build_prompt(self, user_data: dict, prediction: str, retrieved_docs: str, query: str) -> str:
        # Modified context for FLAN-T5-base to enforce complete, conversational sentences instead of single words
        return f"Provide a detailed and complete sentence explaining the answer purely based on the given context.\n\nContext:\n{retrieved_docs}\n\nQuestion: {query}\n\nDetailed Answer:"

prompt_builder = PromptBuilder()
