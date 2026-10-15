import os
import re
from typing import List, Dict, Optional, Tuple
from src.types import RetrievalResult

# ---------------------------------------------------------
# Arabic Normalization Helper
# ---------------------------------------------------------
def normalize_arabic(text: str) -> str:
    """Normalize Arabic text for robust keyword and pattern matching."""
    if not text:
        return ""
    # Remove Arabic diacritics (Tashkeel)
    text = re.sub(r'[\u064B-\u0652\u0670]', '', text)
    # Remove Tatweel
    text = re.sub(r'\u0640', '', text)
    # Normalize Alef variations
    text = re.sub(r'[إأآا]', 'ا', text)
    # Normalize Teh Marbuta to Heh
    text = re.sub(r'ة', 'ه', text)
    # Normalize Yeh variations
    text = re.sub(r'[ىي]', 'ي', text)
    # Normalize punctuation & symbols
    text = re.sub(r'[؟?.,!،؛:()\[\]"\'\-]', ' ', text)
    # Collapse multiple whitespaces
    text = re.sub(r'\s+', ' ', text).strip()
    return text.lower()


class KnowledgeEngine:
    """
    Person 1 Knowledge & Retrieval Engine
    - Parses and cleans the 12 official Civil Status and Passports documents.
    - Handles Jordanian/Levantine Arabic dialects and intent classification.
    - Performs multi-turn context resolution from conversation history.
    - Detects out-of-scope questions and ambiguous questions.
    - Returns exact, grounded context snippets matching answers_example.json format.
    """

    KNOWN_HEADERS = [
        'الفئة المستفيدة',
        'أماكن تقديم الخدمة',
        'شروط تقديم الخدمة',
        'الوثائق المطلوبة',
        'إجراءات تقديم الخدمة',
        'الزمن المستغرق',
        'شركاء الخدمة',
        'ملاحظات',
        'الرسوم'
    ]

    HEADER_KEY_MAP = {
        'الفئة المستفيدة': 'target_group',
        'أماكن تقديم الخدمة': 'locations',
        'شروط تقديم الخدمة': 'conditions',
        'الوثائق المطلوبة': 'documents',
        'إجراءات تقديم الخدمة': 'procedures',
        'الزمن المستغرق': 'time',
        'شركاء الخدمة': 'partners',
        'ملاحظات': 'notes',
        'الرسوم': 'fees',
    }

    CANONICAL_DOC_TITLES = {
        ('passport', 'first_issue'): "جواز سفر ( عادي) لأول مرة",
        ('passport', 'renewal'): "تجديد جواز السفر",
        ('passport', 'lost'): "جواز سفر بدل فاقد",
        ('passport', 'damaged'): "جواز سفر بدل تالف",
        ('family_book', 'first_issue'): "الحصول على دفتر عائلة لأول مرة",
        ('family_book', 'renewal'): "تجديد دفتر العائلة",
        ('family_book', 'lost'): "دفتر عائلة بدل فاقد",
        ('family_book', 'damaged'): "دفتر عائلة بدل تالف",
        ('id_card', 'first_issue'): "إصدار البطاقة الذكية لأول مرة",
        ('id_card', 'renewal'): "تجديد بطاقة الأحوال المدنية الذكية",
        ('id_card', 'lost'): "بطاقة الأحوال المدنية الذكية بدل فاقد",
        ('id_card', 'damaged'): "بطاقة الأحوال المدنية الذكية بدل تالف",
    }

    # Clean display names for sections matching answers_example.json
    SECTION_DISPLAY_NAMES = {
        'time': 'الزمن المستغرق لتقديم الخدمة',
        'locations': 'أماكن تقديم الخدمة',
        'documents': 'الوثائق المطلوبة',
        'fees': 'الرسوم',
        'conditions': 'شروط تقديم الخدمة',
        'notes': 'ملاحظات',
        'procedures': 'إجراءات تقديم الخدمة',
        'target_group': 'الفئة المستفيدة',
        'partners': 'شركاء الخدمة'
    }

    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        # Structure: {(doc_type, situation): {section_key: content_str}}
        self.knowledge_base: Dict[Tuple[str, str], Dict[str, str]] = {}
        self.service_titles: Dict[Tuple[str, str], str] = {}
        self._load_and_parse_data()

    def _load_and_parse_data(self):
        """Loads and parses the 12 text files."""
        services = [
            ('passport', 'first_issue', 'passport_first_issue.txt'),
            ('passport', 'renewal', 'passport_renewal.txt'),
            ('passport', 'lost', 'passport_lost.txt'),
            ('passport', 'damaged', 'passport_damaged.txt'),
            ('family_book', 'first_issue', 'family_book_first_issue.txt'),
            ('family_book', 'renewal', 'family_book_renewal.txt'),
            ('family_book', 'lost', 'family_book_lost.txt'),
            ('family_book', 'damaged', 'family_book_damaged.txt'),
            ('id_card', 'first_issue', 'id_card_first_issue.txt'),
            ('id_card', 'renewal', 'id_card_renewal.txt'),
            ('id_card', 'lost', 'id_card_lost.txt'),
            ('id_card', 'damaged', 'id_card_damaged.txt'),
        ]

        for doc_type, sit, filename in services:
            filepath = os.path.join(self.data_dir, filename)
            if not os.path.exists(filepath):
                alt_path = os.path.join('participant_pack', 'data', filename)
                if os.path.exists(alt_path):
                    filepath = alt_path

            if not os.path.exists(filepath):
                continue

            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            parsed_sections, title = self._parse_single_file(content, doc_type, sit)
            key = (doc_type, sit)
            self.knowledge_base[key] = parsed_sections
            self.service_titles[key] = title

    def _parse_single_file(self, content: str, doc_type: str, sit: str) -> Tuple[Dict[str, str], str]:
        """
        Parses a single file, strips leftover website menus,
        and extracts the core 9 fields.
        """
        lines = [line.strip() for line in content.splitlines() if line.strip()]
        title = self.CANONICAL_DOC_TITLES.get((doc_type, sit), "الخدمة المطلوبة")

        sections: Dict[str, List[str]] = {}
        current_section = None

        for line in lines:
            # Check if this line starts a known header
            matched_header = None
            for h in self.KNOWN_HEADERS:
                if line.startswith(h):
                    matched_header = h
                    break

            if matched_header:
                current_section = self.HEADER_KEY_MAP[matched_header]
                if current_section not in sections:
                    sections[current_section] = []

                # Remainder of the line
                remainder = line[len(matched_header):].strip()
                # Clean prefix artifacts
                remainder = re.sub(r'^(للحصول على الخدمة|لتقديم الخدمة)[\s:\t]*', '', remainder).strip()
                remainder = remainder.lstrip(':\t- ')
                if remainder:
                    sections[current_section].append(remainder)
            elif current_section:
                sections[current_section].append(line)

        # Merge section lines cleanly
        cleaned_sections: Dict[str, str] = {}
        for sec_name, text_lines in sections.items():
            if sec_name == 'locations':
                cleaned_sections[sec_name] = '، '.join(text_lines).strip()
            else:
                cleaned_sections[sec_name] = ' '.join(text_lines).strip()

        return cleaned_sections, title

    # ---------------------------------------------------------
    # Intent, Dialect & Entity Extraction
    # ---------------------------------------------------------
    def _detect_documents(self, norm_text: str) -> List[str]:
        """Detect document types from normalized text with prefix tolerance."""
        docs = []

        # Smart ID Card (check first to avoid overlap)
        if re.search(r'(?:^|\s)(?:و|ف|ب|ل|ك|لل)?(?:ال)?بطاق[هة]\s+(?:و|ف|ب|ل|ك|لل)?(?:ال)?(?:ذكيه|شخصيه|احوال)', norm_text) \
           or any(w in norm_text for w in ['بطاقه ذكيه', 'بطاقه الاحوال', 'البطاقه الذكيه', 'هويه', 'الهويه', 'بطاقتي', 'بطاقه شخصيه']):
            docs.append('id_card')

        # Passport
        if re.search(r'(?:^|\s)(?:و|ف|ب|ل|ك|لل)?(?:ال)?(?:جواز|باسبور)', norm_text) \
           or any(w in norm_text for w in ['جواز', 'باسبور', 'الباسبور', 'جوازات', 'جواز سفر', 'جوازي', 'جوازه', 'جوازها']):
            docs.append('passport')

        # Family Book
        if re.search(r'(?:^|\s)(?:و|ف|ب|ل|ك|لل)?(?:ال)?دفتر\s+(?:و|ف|ب|ل|ك|لل)?(?:ال)?(?:عائله|عيله)', norm_text) \
           or any(w in norm_text for w in [
            'دفتر عائله', 'دفتر عيله', 'دفتر العائله', 'دفتر العيله', 'دفتر عيلتي', 'دفترنا',
            'رب الاسره', 'رب اسره', 'سجل مدني', 'قيد مدني'
        ]):
            docs.append('family_book')
        elif 'دفتر' in norm_text and 'خدمه العلم' not in norm_text:
            docs.append('family_book')

        # Contextual inference for death of parents or family registration
        if not docs and any(w in norm_text for w in ['توفي الاب والام', 'وفاه الاب والام', 'مين بصير رب']):
            docs.append('family_book')

        return list(dict.fromkeys(docs))

    def _detect_situations(self, norm_text: str) -> List[str]:
        """Detect situation (first_issue, renewal, lost, damaged)."""
        situations = []

        # Lost
        if any(w in norm_text for w in [
            'بدل فاقد', 'فاقد', 'ضايع', 'ضيعت', 'ضيعته', 'ضاع', 'سرق', 'انسرق', 'مفقود', 'فقدان'
        ]):
            situations.append('lost')

        # Damaged
        if any(w in norm_text for w in [
            'بدل تالف', 'تالف', 'خربان', 'ممزوع', 'اهترى', 'اهتري', 'مهتري', 'تلف', 'مشوه', 'مكسور', 'تلفان'
        ]):
            situations.append('damaged')

        # First issue
        if any(w in norm_text for w in [
            'اول مره', 'لاول مره', 'اصدار جديد', 'اصدار لاول مره', 'بدي اطلع جديد', 'جديد لاول مره', 'اصدار بطاقه'
        ]):
            situations.append('first_issue')

        # Renewal
        if any(w in norm_text for w in [
            'تجديد', 'اجدد', 'تجديده', 'تجديدها', 'خلص', 'منتهي', 'انتهت', 'انتهى', 'صلاحيه', 'جدد'
        ]):
            situations.append('renewal')

        return list(dict.fromkeys(situations))

    def _detect_sections(self, norm_text: str) -> List[str]:
        """Detect topic/section requested by the citizen."""
        sections = []

        # Fees
        if any(w in norm_text for w in [
            'رسوم', 'كم بكلف', 'قديش بكلف', 'قديش بدفع', 'كم بدفع', 'سعر', 'تكلفه', 'كم الرسوم',
            'دنانير', 'دينار', 'اغلى', 'ارخص', 'غرامه', 'كفاله'
        ]):
            sections.append('fees')

        # Time
        if any(w in norm_text for w in [
            'كم يستغرق', 'كم وقت', 'قديش بطول', 'قديش وقت', 'المده', 'كم دقيقه', 'كم يوم', 'الوقت المستغرق', 'الزمن'
        ]):
            sections.append('time')

        # Locations
        if any(w in norm_text for w in [
            'وين', 'اماكن', 'مكان', 'وين بقدر', 'وين اروح', 'مكتب', 'مكاتب', 'سفاره', 'سفارات', 'قنصليه',
            'برا البلد', 'خارج الاردن', 'خارج البلاد', 'المملكه'
        ]):
            sections.append('locations')

        # Documents
        if any(w in norm_text for w in [
            'اوراق', 'الاوراق', 'وثائق', 'الوثائق', 'شو اجيب', 'شو اخذ', 'صوره شخصيه', 'صور شخصيه',
            'قديش صوره', 'كم صوره', 'المطلوب لاصدار', 'المطلوب لتجديد', 'المطلوبه'
        ]):
            sections.append('documents')

        # Conditions
        if any(w in norm_text for w in [
            'شروط', 'شرط', 'موافقه', 'موافقه زوج', 'موافقه الزوج', 'العمر', 'سن', 'يقبل', 'حق'
        ]):
            sections.append('conditions')

        # Notes / Specific Edge Cases
        if any(w in norm_text for w in [
            'توفي', 'وفاه', 'رب الاسره', 'مقدسي', 'مقدسيه', 'مستعجل', 'مستعجله', 'كفاله'
        ]):
            sections.append('notes')

        # Procedures
        if any(w in norm_text for w in [
            'اجراءات', 'خطوات', 'كيف اقدم', 'طريقه التقديم'
        ]):
            sections.append('procedures')

        return list(dict.fromkeys(sections))

    def _is_out_of_scope(self, norm_text: str) -> bool:
        """Flags questions that are clearly outside the 12 civil services."""
        out_of_scope_keywords = [
            'طيران', 'تذكره طيران', 'طائره', 'دبي', 'سياحه', 'فندق',
            'جامعيه', 'شهاده جامعيه', 'تصديق شهاده', 'ترخيص', 'سواقه', 'رخصه سواقه',
            'مخالفات', 'مخالفه سير', 'مركبه', 'سياره', 'جمارك', 'ضريبه', 'مسقفات',
            'تقاعد', 'ضمان اجتماعي', 'بلديه', 'مستشفى', 'تأمين صحي', 'فيزا سياحيه',
            'شنغن', 'فيزا امريكا', 'قطار', 'باص عمان'
        ]
        return any(k in norm_text for k in out_of_scope_keywords)

    def _format_context_snippet(self, doc_type: str, sit: str, sec_key: str, question: str = "") -> str:
        """
        Formats exact Arabic context snippets matching official answer expectations.
        Example: "تجديد دفتر العائلة - الزمن المستغرق لتقديم الخدمة: 45 دقيقة"
        """
        key = (doc_type, sit)
        sec_dict = self.knowledge_base.get(key, {})
        title = self.service_titles.get(key, self.CANONICAL_DOC_TITLES.get(key, ""))
        raw_text = sec_dict.get(sec_key, "")

        if not raw_text:
            return ""

        display_sec = self.SECTION_DISPLAY_NAMES.get(sec_key, sec_key)

        # Specialized snippet extraction for photo questions (chat-04)
        norm_q = normalize_arabic(question)
        if sec_key == 'documents' and ('صوره' in norm_q or 'صور' in norm_q):
            # Look for photo item in documents
            photo_match = re.search(r'(\d+[\.\-]\s*صور.*?)(?=(?:\s+\d+\.\s+)|$)', raw_text)
            if photo_match:
                photo_item = photo_match.group(1).strip()
                return f"{title} - {display_sec}: ... {photo_item}"

        # Clean locations text
        if sec_key == 'locations':
            raw_text = re.sub(r'\s+', ' ', raw_text).strip()

        # Clean documents spacing after numbers
        if sec_key == 'documents':
            raw_text = re.sub(r'(\d+)\.\s*', r'\1. ', raw_text)
            raw_text = re.sub(r'\s+', ' ', raw_text).strip()

        return f"{title} - {display_sec}: {raw_text}"

    # ---------------------------------------------------------
    # Main Retrieval Method
    # ---------------------------------------------------------
    def retrieve(self, question: str, history: Optional[List[Dict[str, str]]] = None) -> RetrievalResult:
        """
        Extract intent, match document/situation/section, and return exact contexts.
        Complies strictly with the Person 1 technical contract.
        """
        if not question or not question.strip():
            return RetrievalResult(service_found=False, contexts=[])

        norm_q = normalize_arabic(question)

        # 1. Out of Scope Check
        if self._is_out_of_scope(norm_q):
            return RetrievalResult(service_found=False, contexts=[])

        # 2. Extract Entities
        detected_docs = self._detect_documents(norm_q)
        detected_sits = self._detect_situations(norm_q)
        detected_secs = self._detect_sections(norm_q)

        # 3. Multi-turn History Resolution
        if history:
            for turn in reversed(history):
                prev_q = normalize_arabic(turn.get("question", ""))
                prev_docs = self._detect_documents(prev_q)
                prev_sits = self._detect_situations(prev_q)

                if not detected_docs and prev_docs:
                    detected_docs = [prev_docs[0]]
                if not detected_sits and prev_sits:
                    detected_sits = [prev_sits[0]]

                if detected_docs and detected_sits:
                    break

        # 4. Handle Comparative Queries (e.g., chat-04: smart ID photos vs passport renewal photos)
        # or "أيهما أغلى: جواز بدل تالف ولا بدل فاقد؟"
        is_comparison = len(detected_docs) > 1 or len(detected_sits) > 1 or 'ايهما' in norm_q or 'مقارنه' in norm_q

        if is_comparison:
            contexts = []
            # Comparison between two situations of same doc (e.g., passport damaged vs passport lost)
            if len(detected_docs) <= 1 and len(detected_sits) >= 2:
                doc = detected_docs[0] if detected_docs else 'passport'
                sec = detected_secs[0] if detected_secs else 'fees'
                for sit in detected_sits:
                    snip = self._format_context_snippet(doc, sit, sec, question)
                    if snip:
                        contexts.append(snip)
                return RetrievalResult(
                    service_found=True,
                    document_type=doc,
                    situation=detected_sits[0],
                    section=sec,
                    contexts=contexts,
                    is_ambiguous=False
                )

            # Comparison across different documents (e.g. ID card first issue vs passport renewal)
            if len(detected_docs) >= 2:
                sec = detected_secs[0] if detected_secs else 'documents'
                for doc in detected_docs:
                    sit = None
                    if doc == 'id_card':
                        if any(w in norm_q for w in ['لاول مره', 'اول مره']):
                            sit = 'first_issue'
                        elif 'تجديد' in norm_q:
                            sit = 'renewal'
                    elif doc == 'passport':
                        if 'تجديد' in norm_q:
                            sit = 'renewal'
                        elif any(w in norm_q for w in ['لاول مره', 'اول مره']):
                            sit = 'first_issue'

                    if not sit:
                        sit = detected_sits[0] if detected_sits else 'first_issue'

                    snip = self._format_context_snippet(doc, sit, sec, question)
                    if snip:
                        contexts.append(snip)

                return RetrievalResult(
                    service_found=True,
                    document_type=detected_docs[0],
                    situation=detected_sits[0] if detected_sits else 'first_issue',
                    section=sec,
                    contexts=contexts,
                    is_ambiguous=False
                )

        # 5. Ambiguity Check
        if not detected_docs:
            if detected_sits or detected_secs:
                return RetrievalResult(
                    service_found=True,
                    is_ambiguous=True,
                    contexts=[]
                )
            else:
                return RetrievalResult(service_found=False, contexts=[])

        doc_type = detected_docs[0]

        # 6. Default Situation Inference
        situation = detected_sits[0] if detected_sits else None
        if not situation:
            if 'اصدار' in norm_q:
                situation = 'first_issue'
            else:
                situation = 'renewal'

        # 7. Section Selection
        section = detected_secs[0] if detected_secs else None
        if not section:
            if 'شروط' in norm_q or 'زوج' in norm_q:
                section = 'conditions'
            elif 'اوراق' in norm_q or 'مطلوب' in norm_q:
                section = 'documents'
            elif 'رسوم' in norm_q or 'دينار' in norm_q:
                section = 'fees'
            elif 'وقت' in norm_q or 'دقيقه' in norm_q:
                section = 'time'
            elif 'وين' in norm_q or 'مكان' in norm_q:
                section = 'locations'
            else:
                section = 'documents'

        # 8. Edge-cases in notes or conditions
        if ('وفاه' in norm_q or 'توفي' in norm_q or 'رب الاسره' in norm_q) and doc_type == 'family_book':
            section = 'notes'
        if ('زوجه' in norm_q or 'موافقه' in norm_q or 'زوج' in norm_q) and doc_type == 'passport':
            section = 'conditions'

        # 9. Format Context Snippets
        contexts = []
        snippet = self._format_context_snippet(doc_type, situation, section, question)
        if snippet:
            contexts.append(snippet)

        # If fees have special condition notes (like urgent counter +25 JOD in passport renewal),
        # also include notes snippet for completeness
        if section == 'fees' and (doc_type, situation) == ('passport', 'renewal'):
            notes_snip = self._format_context_snippet(doc_type, situation, 'notes', question)
            if notes_snip and 'مستعجل' in norm_q:
                contexts.append(notes_snip)

        return RetrievalResult(
            service_found=True,
            document_type=doc_type,
            situation=situation,
            section=section,
            contexts=contexts,
            is_ambiguous=False
        )


if __name__ == "__main__":
    engine = KnowledgeEngine()

    print("--- Running Person 1 Independent Verification Tests ---")

    # Test 1: Dialect renewal
    res1 = engine.retrieve("الباسبور خلص شو أعمل؟")
    assert res1.service_found is True
    assert res1.document_type == "passport" and res1.situation == "renewal"
    print("Test 1 (Dialect renewal) PASSED")

    # Test 2: Out of scope
    res2 = engine.retrieve("كم سعر تذكرة الطيران إلى دبي؟")
    assert res2.service_found is False and len(res2.contexts) == 0
    print("Test 2 (Out of scope) PASSED")

    # Test 3: Ambiguous question
    res3 = engine.retrieve("بدي أجدد شو المطلوب؟")
    assert res3.is_ambiguous is True and len(res3.contexts) == 0
    print("Test 3 (Ambiguous detection) PASSED")

    # Test 4: Time query (from questions.json chat-01)
    res4 = engine.retrieve("كم يستغرق تجديد دفتر العائلة؟")
    assert res4.document_type == "family_book" and res4.situation == "renewal"
    assert any("45 دقيقة" in c for c in res4.contexts)
    print("Test 4 (Time query) PASSED")

    # Test 5: Location query (from questions.json chat-02)
    res5 = engine.retrieve("وين بقدر أطلع جواز سفر بدل فاقد؟")
    assert res5.document_type == "passport" and res5.situation == "lost"
    assert any("السفارات" in c for c in res5.contexts)
    print("Test 5 (Locations query) PASSED")

    # Test 6: Multi-turn chat (from questions.json chat-03)
    history = [{"question": "شو الأوراق المطلوبة لتجديد دفتر العائلة؟", "answer": "..."}]
    res6 = engine.retrieve("وبقدر أقدّم الطلب من السفارة إذا كنت برا البلد؟", history=history)
    assert res6.document_type == "family_book" and res6.situation == "renewal"
    assert any("السفارات" in c for c in res6.contexts)
    print("Test 6 (Multi-turn inheritance) PASSED")

    # Test 7: Multi-entity comparison (from questions.json chat-04)
    res7 = engine.retrieve("قديش صورة شخصية بحتاج للبطاقة الذكية لأول مرة، وقديش لتجديد جواز السفر؟")
    assert len(res7.contexts) == 2
    print("Test 7 (Comparative photo counts) PASSED")

    # Test 8: Notes edge-case (death of parents)
    res8 = engine.retrieve("إذا توفي الأب والأم، مين بصير رب الأسرة؟")
    assert res8.document_type == "family_book"
    assert any("أكبر الأبناء" in c or "اكبر الابناء" in normalize_arabic(c) for c in res8.contexts)
    print("Test 8 (Hidden in notes) PASSED")

    # Test 9: Damaged dialect
    res9 = engine.retrieve("الباسبور اهترى وش أسوي؟")
    assert res9.document_type == "passport" and res9.situation == "damaged"
    print("Test 9 (Damaged dialect) PASSED")

    print("\nAll Person 1 tests passed successfully!")
