import json

class PromptBuilder:
    def build_prompt(self, user_data: dict, prediction: str, retrieved_docs: str, query: str) -> str:
        # Streamlined context for FLAN-T5-small model processing without hallucination
        return f"Context: {retrieved_docs}\nUser stats: {user_data.get('overall_score', 'N/A')} score\n\nQuestion: {query}\nAnswer:"

prompt_builder = PromptBuilder()
