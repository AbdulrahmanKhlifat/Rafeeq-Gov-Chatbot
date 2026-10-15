# src/generator.py
"""
LLM Response Generator for Rafeeq (رفيق) Gov Chatbot.
Owner: Person 2 (LLM Pipeline, Prompts & Evaluator)

Connects to local Ollama instance (default port 11434) and enforces
strict grounding, conditional fee rules, and zero-shot out-of-scope refusal.
"""

import json
import urllib.request
import urllib.error
from typing import Optional
from src.types import RetrievalResult, BotResponse

DEFAULT_MODEL = "qwen2.5:7b"
OLLAMA_API_URL = "http://localhost:11434/api/generate"

REFUSAL_MESSAGE = "عذراً، لا تتوفر لدي معلومات عن هذه الخدمة. أستطيع المساعدة في خدمات جواز السفر ودفتر العائلة والبطاقة الذكية فقط."
AMBIGUITY_MESSAGE = "يرجى توضيح المعاملة المطلوبة بالتحديد: هل تقصد جواز السفر، أم دفتر العائلة، أم البطاقة الذكية؟ وما هي الحالة (إصدار لأول مرة، تجديد، بدل فاقد، بدل تالف)؟"

SYSTEM_PROMPT = """أنت موظف استعلامات رسمي في دائرة الأحوال المدنية والجوازات الأردنية.
مهمتك الإجابة على استفسارات المواطنين بدقة واختصار ووضوح، باللغة العربية الفصحى.

القواعد الصارمة:
1. اعتمد فقط وحصرياً على "المعلومات الرسمية" المرفقة في الأسفل.
2. لا تخترع أو تفترض أي معلومة أو مبالغ غير مذكورة في المراجع.
3. إذا سأل المواطن عن رسوم أو شروط تعتمد على العمر أو مدة انتهاء الوثيقة أو المكان (داخل الأردن / بالخارج)، طبق القاعدة المطابقة لحالته بدقة.
4. اجعل الإجابة مباشرة ومفيدة دون مقدمات مطولة."""


class ResponseGenerator:
    def __init__(self, model_name: str = DEFAULT_MODEL, api_url: str = OLLAMA_API_URL):
        self.model_name = model_name
        self.api_url = api_url

    def _call_ollama(self, prompt: str) -> Optional[str]:
        """
        Sends generation request to local Ollama daemon using standard library urllib.
        Zero external dependencies required.
        """
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.1,      # Low temperature for factual consistency
                "top_p": 0.8,
                "num_predict": 256,       # Keep responses crisp and fast
                "num_ctx": 2048,          # Adequate context window
                "stop": ["المواطن:", "السؤال:", "\n\n\n"]
            }
        }
        
        req = urllib.request.Request(
            self.api_url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        
        try:
            with urllib.request.urlopen(req, timeout=45) as response:
                if response.status == 200:
                    result = json.loads(response.read().decode("utf-8"))
                    return result.get("response", "").strip()
        except urllib.error.URLError as e:
            # Fallback if Ollama daemon is temporarily unreachable or busy
            return None
        except Exception:
            return None

        return None

    def generate(self, question: str, retrieval: RetrievalResult) -> BotResponse:
        """
        Takes the user question and the structured retrieval result,
        and produces a strictly grounded BotResponse.
        """
        # Guardrail 1: Out-of-scope query -> Instant zero-latency refusal with empty contexts
        if not retrieval.service_found or not retrieval.contexts:
            return BotResponse(
                answer=REFUSAL_MESSAGE,
                contexts=[]
            )

        # Guardrail 2: Ambiguous query -> Clarification prompt
        if retrieval.is_ambiguous:
            return BotResponse(
                answer=AMBIGUITY_MESSAGE,
                contexts=retrieval.contexts
            )

        # Build Grounded Prompt with Contexts
        formatted_context = "\n".join([f"- {c}" for c in retrieval.contexts])
        prompt = (
            f"{SYSTEM_PROMPT}\n\n"
            f"[المعلومات الرسمية المعتمدة]:\n"
            f"{formatted_context}\n\n"
            f"سؤال المواطن: {question}\n"
            f"الإجابة المباشرة الدقيقة:"
        )

        llm_answer = self._call_ollama(prompt)

        # If LLM is offline or fails, synthesize a direct answer from the first context
        if not llm_answer:
            # Fallback direct answer derived safely from contexts
            first_ctx = retrieval.contexts[0]
            if ":" in first_ctx:
                content = first_ctx.split(":", 1)[1].strip()
                llm_answer = content
            else:
                llm_answer = first_ctx

        return BotResponse(
            answer=llm_answer,
            contexts=retrieval.contexts
        )
