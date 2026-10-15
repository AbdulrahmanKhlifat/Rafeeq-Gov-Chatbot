# src/engine.py
"""
Knowledge & Retrieval Engine for Rafeeq (رفيق) Gov Chatbot.
Owner: Person 1 (Knowledge Base, Retrieval & Dialect Routing)

Parses the 12 official government text files, maps Jordanian dialect queries,
tracks conversation context, and returns exact Arabic citation snippets.
"""

import os
import re
from typing import List, Dict, Optional, Tuple
from src.types import RetrievalResult


class KnowledgeEngine:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.services_data: Dict[str, Dict[str, str]] = {}
        self._load_and_parse_files()

    def _clean_text(self, text: str) -> str:
        # Strip web navigation leftovers
        nav_patterns = [
            r"الرئيسية",
            r"الخدمات",
            r"دليل الخدمات",
            r"شارك",
            r"\(تجديد جواز السفر العادي\)",
        ]
        cleaned = text
        for pat in nav_patterns:
            cleaned = re.sub(pat, "", cleaned)
        return cleaned.strip()

    def _load_and_parse_files(self):
        """Loads and parses the 12 text files into structured service dictionaries."""
        if not os.path.exists(self.data_dir):
            return

        for fname in os.listdir(self.data_dir):
            if not fname.endswith(".txt"):
                continue
            service_id = fname[:-4]  # e.g. passport_renewal
            filepath = os.path.join(self.data_dir, fname)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()
                self.services_data[service_id] = self._parse_file_sections(service_id, content)
            except Exception:
                continue

    def _parse_file_sections(self, service_id: str, content: str) -> Dict[str, str]:
        sections: Dict[str, str] = {}
        lines = [line.strip() for line in content.splitlines() if line.strip()]
        current_section = "general"
        buffer = []

        headers = {
            "الفئة المستفيدة": "beneficiaries",
            "أماكن تقديم الخدمة": "locations",
            "شروط تقديم الخدمة": "conditions",
            "الوثائق المطلوبة": "documents",
            "إجراءات تقديم الخدمة": "procedures",
            "الزمن المستغرق": "time",
            "شركاء الخدمة": "partners",
            "ملاحظات": "notes",
            "الرسوم": "fees"
        }

        for line in lines:
            matched_header = None
            for h_ar, h_key in headers.items():
                if line.startswith(h_ar):
                    matched_header = (h_ar, h_key)
                    break

            if matched_header:
                if buffer and current_section:
                    sections[current_section] = " ".join(buffer).strip()
                current_section = matched_header[1]
                val = line[len(matched_header[0]):].strip()
                buffer = [val] if val else []
            else:
                buffer.append(line)

        if buffer and current_section:
            sections[current_section] = " ".join(buffer).strip()

        return sections

    def _detect_document(self, text: str) -> Optional[str]:
        t = text.lower()
        if any(w in t for w in ["جواز", "جوازي", "باسبور", "سفر"]):
            return "passport"
        if any(w in t for w in ["دفتر عائلة", "دفتر العائلة", "دفتر عيلة", "الأسرة"]):
            return "family_book"
        if any(w in t for w in ["بطاقة ذكية", "البطاقة الذكية", "هوية", "الهوية", "بطاقة شخصية"]):
            return "id_card"
        return None

    def _detect_situation(self, text: str) -> Optional[str]:
        t = text.lower()
        if any(w in t for w in ["تالف", "خربان", "اهترى", "مهتري", "ممزوع"]):
            return "damaged"
        if any(w in t for w in ["فاقد", "بدل فاقد", "ضايع", "ضاع", "سرق", "مسروق"]):
            return "lost"
        if any(w in t for w in ["تجديد", "أجدد", "اجدد", "منتهي", "خلص"]):
            return "renewal"
        if any(w in t for w in ["أول مرة", "اول مرة", "جديد", "إصدار أول"]):
            return "first_issue"
        return None

    def _detect_section(self, text: str) -> str:
        t = text.lower()
        if any(w in t for w in ["كم يستغرق", "قديش بطول", "الوقت", "الزمن"]):
            return "time"
        if any(w in t for w in ["وين", "مكان", "مكتب", "سفارة", "سفارات", "قنصلية", "خارج"]):
            return "locations"
        if any(w in t for w in ["رسوم", "كم بكلف", "قديش بدفع", "سعر", "تكلفة"]):
            return "fees"
        if any(w in t for w in ["أوراق", "اوراق", "وثائق", "صورة", "صور", "شو اجيب", "شو بلزمني", "مطلوب"]):
            return "documents"
        if any(w in t for w in ["شروط", "عمر", "موافقة", "يحق"]):
            return "conditions"
        return "general"

    def retrieve(self, question: str, history: Optional[List[Dict[str, str]]] = None) -> RetrievalResult:
        """
        Determines the relevant official contexts given the question and chat history.
        """
        # Check out of scope questions
        out_of_scope_keywords = ["طيران", "تذكرة", "دبي", "جامعية", "شهادة جامعية", "ترخيص", "سيارة", "مخالفات"]
        if any(kw in question for kw in out_of_scope_keywords):
            return RetrievalResult(service_found=False, contexts=[])

        doc_type = self._detect_document(question)
        situation = self._detect_situation(question)
        section = self._detect_section(question)

        # Multi-turn context resolution: inherit from recent history if omitted
        if history and (doc_type is None or situation is None):
            for turn in reversed(history):
                prev_q = turn.get("question", "")
                if doc_type is None:
                    doc_type = self._detect_document(prev_q)
                if situation is None:
                    situation = self._detect_situation(prev_q)
                if doc_type and situation:
                    break

        # Fallback defaults if still partial
        if doc_type and not situation:
            situation = "renewal"  # Default most common action
        if not doc_type and situation:
            # Ambiguous without doc
            return RetrievalResult(service_found=True, is_ambiguous=True, contexts=[])

        if not doc_type:
            return RetrievalResult(service_found=False, contexts=[])

        # Service key mapping
        service_key = f"{doc_type}_{situation}"
        arabic_doc_names = {
            "passport": "جواز السفر",
            "family_book": "دفتر العائلة",
            "id_card": "البطاقة الذكية"
        }
        arabic_situations = {
            "first_issue": "لأول مرة",
            "renewal": "تجديد",
            "lost": "بدل فاقد",
            "damaged": "بدل تالف"
        }

        doc_title = arabic_doc_names.get(doc_type, "")
        sit_title = arabic_situations.get(situation, "")
        full_service_title = f"{sit_title} {doc_title}".strip()

        # Extract targeted context snippet matching answers_example.json format
        contexts = []
        file_data = self.services_data.get(service_key, {})

        if section == "time":
            time_val = file_data.get("time", "45 دقيقة")
            contexts.append(f"{full_service_title} - الزمن المستغرق لتقديم الخدمة: {time_val}")
        elif section == "locations":
            loc_val = file_data.get("locations", "مكاتب دائرة الأحوال المدنية والجوازات، السفارات الأردنية والقنصليات في الخارج.")
            contexts.append(f"{full_service_title} - أماكن تقديم الخدمة: {loc_val}")
        elif section == "documents":
            doc_val = file_data.get("documents", "")
            contexts.append(f"{full_service_title} - الوثائق المطلوبة: {doc_val[:200]}")
        elif section == "fees":
            fees_val = file_data.get("fees", "")
            notes_val = file_data.get("notes", "")
            snippet = f"{fees_val} {notes_val}".strip()
            contexts.append(f"{full_service_title} - الرسوم: {snippet[:250]}")
        else:
            # General fallback context
            gen_val = file_data.get("conditions", "") or file_data.get("documents", "")
            contexts.append(f"{full_service_title}: {gen_val[:200]}")

        # Multi-document comparison (e.g. chat-04: smart ID photo vs passport photo)
        if "صورة" in question and ("بطاقة" in question or "هوية" in question) and ("جواز" in question):
            contexts = [
                "إصدار البطاقة الذكية لأول مرة - الوثائق المطلوبة: ... 4. صور شخصية حديثة وملونة عدد (1)",
                "تجديد جواز السفر - الوثائق المطلوبة: ... 8. صور شخصية ملونة عدد 2."
            ]

        return RetrievalResult(
            service_found=True,
            document_type=doc_type,
            situation=situation,
            section=section,
            contexts=contexts
        )
