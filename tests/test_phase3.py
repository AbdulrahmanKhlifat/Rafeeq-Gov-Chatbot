# tests/test_phase3.py
"""
Phase 3 Validation Suite: Prompt Engineering, Grounding & Zero-Hallucination Guardrails.
Validates:
1. Strict factual grounding and zero fluff (no greetings / filler).
2. Numerical accuracy for conditional fees (age, remaining validity, urgent fee).
3. Correction of false assumptions (e.g. spouse permission).
4. Head of family rules hidden in notes.
5. Comparisons across services.
6. Zero-latency out-of-scope refusals (driving license, property tax, criminal record).
7. Ambiguity clarification with zero contexts.
8. Multi-turn coreference continuity.
9. Distractor-heavy citizen stories.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.engine import KnowledgeEngine
from src.generator import ResponseGenerator, REFUSAL_MESSAGE, AMBIGUITY_MESSAGE


def run_phase3_tests():
    engine = KnowledgeEngine(data_dir="data")
    generator = ResponseGenerator()
    passed = 0
    total = 0

    test_cases = [
        # 1. Zero Fluff & Simple Fact
        {
            "name": "Zero-fluff simple fact (Family book renewal time)",
            "q": "كم يستغرق تجديد دفتر العائلة؟",
            "history": [],
            "expected_substr": "45 دقيقة",
            "forbidden_substr": ["مرحبا", "يسعدني", "أهلاً", "طاب يومك"]
        },
        # 2. Conditional Fee: 17 yrs old, 3 months left
        {
            "name": "Conditional Fee (17 yrs old, 3 months left)",
            "q": "عمري 17 وجوازي باقي عليه 3 شهور، كم رسوم التجديد؟",
            "history": [],
            "expected_substr": "50",
            "expected_doc": "passport",
            "expected_sit": "renewal"
        },
        # 3. Wrong Assumption Correction
        {
            "name": "Wrong assumption correction (Wife passport without husband approval)",
            "q": "الزوجة لازم تجيب موافقة جوزها عشان تطلع جواز، صح؟",
            "history": [],
            "expected_substr": "دون موافقة",
            "expected_doc": "passport"
        },
        # 4. Hidden in Notes: Eldest child becomes head of family
        {
            "name": "Hidden in notes (Death of parents -> Eldest child)",
            "q": "إذا توفى الأب والأم، مين بصير رب الأسرة؟",
            "history": [],
            "expected_substr": "اكبر الأبناء سنا"
        },
        # 5. Service Comparison: Damaged vs Lost Passport
        {
            "name": "Comparison: Damaged vs Lost passport fees",
            "q": "أيهما أغلى: جواز بدل تالف ولا بدل فاقد؟",
            "history": [],
            "expected_substr": "فاقد"
        },
        # 6. Zero-latency Out-of-Scope: Driving License
        {
            "name": "Out-of-scope refusal: Driving license renewal",
            "q": "بدي أجدد رخصة القيادة الخصوصي، كم الرسوم؟",
            "history": [],
            "is_out_of_scope": True
        },
        # 7. Zero-latency Out-of-Scope: Non-Criminal Record
        {
            "name": "Out-of-scope refusal: Non-criminal record certificate",
            "q": "كيف بقدر أطلع شهادة عدم محكومية من المحكمة؟",
            "history": [],
            "is_out_of_scope": True
        },
        # 8. Zero-latency Out-of-Scope: Property tax
        {
            "name": "Out-of-scope refusal: Property tax",
            "q": "كم ضريبة المسقفات المترتبة على البيت؟",
            "history": [],
            "is_out_of_scope": True
        },
        # 9. Ambiguous query clarification
        {
            "name": "Ambiguous query clarification",
            "q": "بدي أجدد، شو المطلوب؟",
            "history": [],
            "is_ambiguous": True
        },
        # 10. Multi-turn Conversation (3 turns)
        {
            "name": "Multi-turn continuity (Turn 2: locations)",
            "q": "وبقدر أقدّم الطلب من السفارة إذا كنت برا البلد؟",
            "history": [
                {"question": "شو الأوراق المطلوبة لتجديد دفتر العائلة؟", "answer": "..."}
            ],
            "expected_doc": "family_book",
            "expected_sit": "renewal",
            "expected_substr": "السفارات"
        },
        # 11. Long Citizen Story with Irrelevant Distractors
        {
            "name": "Long citizen story with irrelevant details",
            "q": "أنا مواطن أردني اسمي أحمد وعندي ولدين وبنت، وسافرت على العقبة الأسبوع الماضي، وبدي أجدد دفتر العائلة القديم لأنه صارله شهر منتهي، شو الأوراق اللي لازم أجهزها وأخذها معي؟",
            "history": [],
            "expected_doc": "family_book",
            "expected_sit": "renewal",
            "expected_substr": "دفتر العائلة المراد تجديده"
        },
        # 12. Smart ID First Issue with delay fine rule
        {
            "name": "Smart ID first issue delay penalty rule",
            "q": "عمري 19 سنة ولسة ما طلعت هوية شخصية بالمرة، كم بكلفني إصدارها؟",
            "history": [],
            "expected_doc": "id_card",
            "expected_sit": "first_issue",
            "expected_substr": "دينار"
        }
    ]

    print("=" * 65)
    print("RUNNING PHASE 3 PROMPT ENGINEERING & GUARDRAILS BENCHMARK")
    print("=" * 65)

    for case in test_cases:
        total += 1
        q = case["q"]
        hist = case.get("history", [])
        ret = engine.retrieve(q, hist)
        resp = generator.generate(q, ret)

        ok = True
        err_msg = ""

        if case.get("is_out_of_scope"):
            if ret.service_found or len(resp.contexts) > 0 or resp.answer != REFUSAL_MESSAGE:
                ok = False
                err_msg = f"Expected instant refusal with empty contexts. Got service_found={ret.service_found}, contexts={resp.contexts}"
        elif case.get("is_ambiguous"):
            if not ret.is_ambiguous or len(resp.contexts) > 0 or resp.answer != AMBIGUITY_MESSAGE:
                ok = False
                err_msg = f"Expected ambiguity clarification. Got is_ambiguous={ret.is_ambiguous}, contexts={resp.contexts}"
        else:
            if not ret.service_found:
                ok = False
                err_msg = "Expected service_found=True"
            elif case.get("expected_doc") and ret.document_type != case["expected_doc"]:
                ok = False
                err_msg = f"Expected doc={case['expected_doc']}, got {ret.document_type}"
            elif case.get("expected_sit") and ret.situation != case["expected_sit"]:
                ok = False
                err_msg = f"Expected sit={case['expected_sit']}, got {ret.situation}"
            elif case.get("expected_substr"):
                all_text = resp.answer + " " + " ".join(resp.contexts)
                if case["expected_substr"] not in all_text:
                    ok = False
                    err_msg = f"Expected substring '{case['expected_substr']}' missing in answer: '{resp.answer[:80]}...'"

            if ok and case.get("forbidden_substr"):
                for forbidden in case["forbidden_substr"]:
                    if forbidden in resp.answer:
                        ok = False
                        err_msg = f"Found forbidden conversational fluff '{forbidden}' in answer: '{resp.answer[:60]}...'"
                        break

        status_str = "PASS" if ok else "FAIL"
        print(f"[{status_str}] {case['name']}")
        if not ok:
            print(f"       -> Reason: {err_msg}")
        else:
            passed += 1

    print("=" * 65)
    print(f"PHASE 3 RESULTS: {passed}/{total} Passed ({(passed/total)*100:.1f}%)")
    print("=" * 65)
    return passed == total


if __name__ == "__main__":
    success = run_phase3_tests()
    sys.exit(0 if success else 1)
