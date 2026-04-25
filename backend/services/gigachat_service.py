from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()

# We'll use the gigachat library for API calls
# For now, create a mock service that can be replaced with real implementation

class GigaChatService:
    def __init__(self):
        self.credentials = os.getenv("GIGACHAT_CREDENTIALS")
        # Initialize GigaChat client when credentials are available
        self.client = None
    
    def _get_client(self):
        """Initialize GigaChat client if not already done"""
        if self.client is None and self.credentials:
            try:
                from gigachat import GigaChat
                self.client = GigaChat(credentials=self.credentials, verify_ssl_certs=False)
            except Exception as e:
                print(f"Failed to initialize GigaChat client: {e}")
        return self.client
    
    async def evaluate_answer(self, question_text: str, answer_hint: str, user_answer: str) -> str:
        """
        Evaluate a user's answer to a question.
        Returns a short response with evaluation and "NEXT" keyword.
        """
        prompt = f"""Вопрос: {question_text}
Эталонный ответ: {answer_hint}
Ответ кандидата: {user_answer}

Оцени ответ кандидата. Если правильный — похвали и скажи "NEXT".
Если неточный — укажи на ошибку коротко (1-2 предложения) и скажи "NEXT".
Если совсем неверный — объясни кратко и скажи "NEXT".
"""
        return await self._call_gigachat(prompt)
    
    async def generate_final_report(self, transcript: str) -> str:
        """
        Generate a final interview report as JSON.
        Returns JSON with score, pros, cons, and recommendations.
        """
        prompt = f"""Ты — опытный технический ментор. Ниже полный транскрипт технического интервью.

{transcript}

Составь структурированный отчёт строго в JSON:
{{
  "score": 0-100,
  "pros": ["список сильных сторон"],
  "cons": ["список ошибок"],
  "recommendations": [{{"topic": "...", "description": "..."}}]
}}
Верни только JSON, без пояснений.
"""
        return await self._call_gigachat(prompt)
    
    async def _call_gigachat(self, prompt: str) -> str:
        """Make a call to GigaChat API"""
        client = self._get_client()
        
        if client is None:
            # Fallback for development without GigaChat credentials
            return self._mock_response(prompt)
        
        try:
            response = client.chat(
                messages=[{"role": "user", "content": prompt}],
                model="GigaChat"
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"GigaChat API error: {e}")
            return self._mock_response(prompt)
    
    def _mock_response(self, prompt: str) -> str:
        """Return mock response for development/testing"""
        if "NEXT" in prompt:
            return "Хороший ответ! NEXT"
        
        # Mock final report
        return """{
  "score": 75,
  "pros": ["Хорошее знание базовых концепций", "Уверенные ответы на лёгкие вопросы"],
  "cons": ["Недостаточная глубина в сложных темах", "Пропущены некоторые детали"],
  "recommendations": [{"topic": "Углублённое изучение GIL", "description": "Рекомендуем изучить документацию Python по многопоточности"}]
}"""


# Singleton instance
gigachat_service = GigaChatService()
