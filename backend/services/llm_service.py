"""
LLM Service Module (Groq Llama Integration).

Why it is needed:
Receives authorized context chunks and the user question, constructs a strict anti-hallucination prompt,
and calls the Groq Llama 3.3 70B API to generate a factual, grounded answer.

Interview Concept:
1. Grounded Generation: We instruct the LLM to rely EXCLUSIVELY on the provided context.
2. Low Temperature: Setting temperature to 0.1 minimizes creative variation and hallucination.
3. Fallback Handling: If context is missing or LLM cannot find the answer in context, it returns a standard fallback response.
"""

import logging
from typing import List
from backend.config import settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are SecureRAG, an intelligent permission-aware document assistant.
Your sole job is to answer user questions STRICTLY using only the provided document context.

STRICT INSTRUCTIONS:
1. Answer ONLY using facts explicitly stated in the provided context below.
2. Do NOT use outside knowledge, assumptions, or external information.
3. If the context does not contain enough information to answer the question, return EXACTLY:
   "I couldn't find this information in the authorized documents."
4. Do NOT hallucinate, guess, or synthesize facts not present in the context.
5. Keep your answer concise, accurate, and professional.
"""

USER_PROMPT_TEMPLATE = """Document Context:
{context}

User Question:
{question}

Answer:"""

class LLMService:
    def __init__(self):
        self.model_name = settings.GROQ_MODEL
        self.fallback_model = "qwen/qwen3.8-27b"

    def _get_groq_client(self):
        api_key = settings.GROQ_API_KEY
        if not api_key or api_key == "mock_key_for_testing":
            raise ValueError("GROQ_API_KEY is not configured in .env file.")
        
        from groq import Groq
        return Groq(api_key=api_key)

    def generate_answer(self, question: str, context: str) -> str:
        """
        Sends the grounded prompt template + context to Groq Llama model and returns generated response text.
        """
        if not context or not context.strip():
            return "I couldn't find this information in the authorized documents."

        try:
            client = self._get_groq_client()
        except ValueError as e:
            logger.warning(f"Groq API Key warning: {e}")
            raise e

        prompt = USER_PROMPT_TEMPLATE.format(context=context, question=question)

        # Attempt primary model (llama-3.3-70b-versatile)
        try:
            response = client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=1024
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.warning(f"Primary model '{self.model_name}' error: {e}. Trying fallback '{self.fallback_model}'")
            try:
                response = client.chat.completions.create(
                    model=self.fallback_model,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.1,
                    max_tokens=1024
                )
                return response.choices[0].message.content.strip()
            except Exception as fallback_err:
                logger.error(f"Groq LLM invocation failed: {fallback_err}")
                raise RuntimeError(f"Groq API Error: {str(e)}")

# Global singleton LLM service instance
llm_service = LLMService()
