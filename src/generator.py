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

DEFAULT_MODEL = "command-r7b-arabic:7b"
OLLAMA_API_URL = "http://localhost:11434/api/generate"

REFUSAL_MESSAGE = "عذراً، لا تتوفر لدي معلومات عن هذه الخدمة. أستطيع المساعدة في خدمات جواز السفر ودفتر العائلة والبطاقة الذكية فقط."
AMBIGUITY_MESSAGE = "يرجى توضيح المعاملة المطلوبة بالتحديد: هل تقصد جواز السفر، أم دفتر العائلة، أم البطاقة الذكية؟ وما هي الحالة (إصدار لأول مرة، تجديد، بدل فاقد، بدل تالف)؟"

SYSTEM_PROMPT = """أنت موظف استعلامات رسمي وخبير في دائرة الأحوال المدنية والجوازات الأردنية.
مهمتك الإجابة على استفسارات المواطنين بدقة متناهية واختصار ووضوح، باللغة العربية الفصحى.

القواعد الصارمة:
1. الالتزام المطلق بالمرجعية: اعتمد حصرياً على [المعلومات الرسمية المعتمدة] المرفقة أدناه. لا تخترع أو تفترض أي معلومة أو مبالغ غير مذكورة فيها.
2. الدقة في تطبيق القواعد والأرقام:
   - عند السؤال عن رسوم أو شروط مشروطة بالعمر (مثل: أقل من 16، فوق 16، فوق 18)، أو مدة الصلاحية (أقل أو أكثر من 180 يوماً)، أو صفة المواطن (عسكري، مدني، مقدسي، داخل/خارج المملكة)، طبق القاعدة المطابقة لحالة السائل بدقة واذكر المبلغ المناسب لحالته فقط.
   - في المقارنات (أيهما أغلى أو أكثر): قارن بين القيمتين بوضوح وبين أيهما أعلى أو أكثر تكلفة.
   - في تصحيح المفاهيم الخاطئة: إذا كان افتراض المواطن غير صحيح (مثل اشتراط موافقة الزوج)، بيّن الحكم الصحيح مباشرة من التعليمات.
   - عند وجود تفاصيل كثيرة أو قصة شخصية: ركز على السؤال الجوهري وأجب عنه بدقة وتجاهل التفاصيل الجانبية.
3. الإجابة المباشرة وبدون حشو: ممنوع نهائياً استخدام أي عبارات ترحيبية أو تمهيد أو مجاملات (مثل: مرحباً، أهلاً بك، يسعدني، طاب يومك، شكراً). ادخل في صلب الإجابة فوراً بالمعلومة المطلوبة.
4. الإيجاز: اجعل الإجابة مختصرة وشافية ومباشرة في حدود 1-3 جمل أو نقاط محددة."""


class ResponseGenerator:
    def __init__(self, model_name: str = DEFAULT_MODEL, api_url: str = OLLAMA_API_URL):
        self.model_name = model_name
        self.api_url = api_url
        self._checked_online = False
        self._is_online = False

    def _check_health(self) -> bool:
        if self._checked_online:
            return self._is_online
        try:
            req = urllib.request.Request("http://localhost:11434/api/tags", headers={"User-Agent": "RafeeqBot"})
            with urllib.request.urlopen(req, timeout=2.0) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8"))
                    models = [m.get("name", "") for m in data.get("models", [])]
                    if self.model_name not in models and models:
                        matching = [m for m in models if self.model_name.split(":")[0] in m]
                        if matching:
                            self.model_name = matching[0]
                        else:
                            self.model_name = models[0]
                    self._is_online = True
                else:
                    self._is_online = False
        except Exception:
            self._is_online = False
        self._checked_online = True
        return self._is_online

    def _call_ollama(self, prompt: str) -> Optional[str]:
        if not self._check_health():
            return None
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.1,      # Low temperature for factual consistency
                "top_p": 0.8,
                "num_predict": 128,       # Keep responses crisp and fast
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
            with urllib.request.urlopen(req, timeout=20) as response:
                if response.status == 200:
                    result = json.loads(response.read().decode("utf-8"))
                    return result.get("response", "").strip()
        except urllib.error.URLError:
            # Fallback if Ollama daemon is unreachable
            return None
        except Exception:
            return None

        return None

    def generate(self, question: str, retrieval: RetrievalResult) -> BotResponse:
        """
        Takes the user question and the structured retrieval result,
        and produces a strictly grounded BotResponse.
        """
        # Guardrail 1: Ambiguous query -> Clarification prompt with empty contexts
        if retrieval.is_ambiguous:
            return BotResponse(
                answer=AMBIGUITY_MESSAGE,
                contexts=[]
            )

        # Guardrail 2: Out-of-scope query -> Instant zero-latency refusal with empty contexts
        if not retrieval.service_found or not retrieval.contexts:
            return BotResponse(
                answer=REFUSAL_MESSAGE,
                contexts=[]
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
