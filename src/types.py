# src/types.py
"""
Shared data contracts for Rafeeq (رفيق) Gov Chatbot.
Used by:
- Person 1 (src/engine.py)
- Person 2 (src/generator.py, main.py)
- Person 3 (src/app.py)
DO NOT MODIFY without team alignment.
"""

from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class RetrievalResult:
    service_found: bool                           # True if question relates to the 12 services; False if out-of-scope
    document_type: Optional[str] = None           # 'passport' | 'family_book' | 'id_card'
    situation: Optional[str] = None               # 'first_issue' | 'renewal' | 'lost' | 'damaged'
    section: Optional[str] = None                 # 'fees' | 'documents' | 'conditions' | 'locations' | 'notes' | 'time'
    contexts: List[str] = field(default_factory=list) # Exact formatted Arabic snippets from documents
    is_ambiguous: bool = False                    # True if question is too vague (e.g., "بدي أجدد شو المطلوب؟")

@dataclass
class BotResponse:
    answer: str                                   # Final Arabic response text for citizen
    contexts: List[str]                           # The exact reference snippets used
