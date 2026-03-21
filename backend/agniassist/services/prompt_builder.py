import json

class PromptBuilder:
    def build_prompt(self, user_data: dict, prediction: str, retrieved_docs: str, query: str) -> str:
        # Streamlined context for FLAN-T5-small model processing to kill repetition loops
        return f"Answer the question purely based on the given context.\n\nContext:\n{retrieved_docs}\n\nQuestion: {query}\n\nAnswer:"

prompt_builder = PromptBuilder()
