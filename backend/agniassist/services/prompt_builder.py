import json

class PromptBuilder:
    def build_prompt(self, user_data: dict, prediction: str, retrieved_docs: str, query: str) -> str:
        formatted_user_data = json.dumps(user_data, indent=2)
        
        return f"""You are AgniAssist, an AI assistant for the Agniveer system.

User Data:
{formatted_user_data}

Prediction:
{prediction}

Knowledge:
{retrieved_docs}

Answer the query clearly and helpfully relying strictly on the context provided above. Do not assume any external personas.

Query:
{query}
"""

prompt_builder = PromptBuilder()
