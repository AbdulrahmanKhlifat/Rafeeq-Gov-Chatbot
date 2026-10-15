# tests/test_phase2.py
"""
Phase 2 Validation Suite: Dialect, Intent Routing & Retrieval Precision.
Tests look-alike services, conditional fees, dialect phrasing,
notes extraction, multi-turn memory, comparisons, and out-of-scope refusal.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.engine import KnowledgeEngine
from src.generator import ResponseGenerator


def run_tests():
    engine = KnowledgeEngine(data_dir="data")
    generator = ResponseGenerator()
    passed = 0
    total = 0

    test_cases = [
        # 1. Simple Fact (Time)
        {
            "name": "Time for family book renewal",
            "q": "كم يستغرق تجديد دفتر العائلة؟",
            "history": [],
            "expected_doc": "family_book",
            "expected_sit": "renewal",
            "expected_kw_in_ctx": "45 دقيقة",
            "out_of_scope": False
        },
        # 2. Location (Lost Passport)
        {
            "name": "Location for lost passport",
            "q": "وين بقدر أطلع جواز سفر بدل فاقد؟",
            "history": [],
            "expected_doc": "passport",
            "expected_sit": "lost",
            "expected_kw_in_ctx": "السفارات",
            "out_of_scope": False
        },
        # 3. Dialect: Damaged
        {
            "name": "Dialect: Damaged passport (اهترى)",
            "q": "الباسبور اهترى وممزوع شو أعمل؟",
            "history": [],
            "expected_doc": "passport",
            "expected_sit": "damaged",
            "expected_kw_in_ctx": "بدل تالف",
            "out_of_scope": False
        },
        # 4. Dialect: Expired / Renewal
        {
            "name": "Dialect: Expired passport (خلص)",
            "q": "الباسبور خلص، شو بلزمني أوراق لأجدده؟",
            "history": [],
            "expected_doc": "passport",
            "expected_sit": "renewal",
            "expected_kw_in_ctx": "الوثائق المطلوبة",
            "out_of_scope": False
        },
        # 5. Conditional Fee (Age 17, 3 months left)
        {
            "name": "Conditional Fee for Passport Renewal",
            "q": "عمري 17 وجوازي باقي عليه 3 شهور، كم رسوم التجديد؟",
            "history": [],
            "expected_doc": "passport",
            "expected_sit": "renewal",
            "expected_kw_in_ctx": "50 دينار",
            "out_of_scope": False
        },
        # 6. Hidden in Notes: Death of parents -> Head of family
        {
            "name": "Hidden in notes: death of parents",
            "q": "إذا توفى الأب والأم، مين بصير رب الأسرة؟",
            "history": [],
            "expected_doc": "family_book",
            "expected_sit": "renewal",
            "expected_kw_in_ctx": "اكبر الأبناء سنا",
            "out_of_scope": False
        },
        # 7. Comparison: Lost vs Damaged Passport
        {
            "name": "Comparison: Damaged vs Lost passport fees",
            "q": "أيهما أغلى: جواز بدل تالف ولا بدل فاقد؟",
            "history": [],
            "is_comparison": True,
            "out_of_scope": False
        },
        # 8. Wrong Assumption: Wife passport without husband approval
        {
            "name": "Wrong assumption: Wife passport approval",
            "q": "الزوجة لازم تجيب موافقة جوزها عشان تطلع جواز، صح؟",
            "history": [],
            "expected_doc": "passport",
            "expected_kw_in_ctx": "دون موافقة زوجها",
            "out_of_scope": False
        },
        # 9. Out of Scope: Flight Ticket
        {
            "name": "Out of scope: Flight ticket",
            "q": "كم سعر تذكرة الطيران من عمان إلى دبي؟",
            "history": [],
            "out_of_scope": True
        },
        # 10. Out of Scope: University Degree
        {
            "name": "Out of scope: University attestation",
            "q": "كم رسوم تصديق الشهادة الجامعية؟",
            "history": [],
            "out_of_scope": True
        },
        # 11. Multi-turn Follow-up
        {
            "name": "Multi-turn context inheritance",
            "q": "وبقدر أقدّم الطلب من السفارة إذا كنت برا البلد؟",
            "history": [
                {"question": "شو الأوراق المطلوبة لتجديد دفتر العائلة؟", "answer": "..."}
            ],
            "expected_doc": "family_book",
            "expected_sit": "renewal",
            "expected_kw_in_ctx": "السفارات",
            "out_of_scope": False
        },
        # 12. Ambiguous Query
        {
            "name": "Ambiguous: baddi ajaddid without doc",
            "q": "بدي أجدد، شو المطلوب؟",
            "history": [],
            "is_ambiguous": True,
            "out_of_scope": False
        }
    ]

    print("=" * 60)
    print("RUNNING PHASE 2 RETRIEVAL & INTENT BENCHMARK")
    print("=" * 60)

    for case in test_cases:
        total += 1
        q = case["q"]
        hist = case.get("history", [])
        ret = engine.retrieve(q, hist)
        resp = generator.generate(q, ret)

        ok = True
        err_msg = ""

        if case.get("out_of_scope"):
            if ret.service_found or len(ret.contexts) > 0:
                ok = False
                err_msg = f"Expected out of scope, but got service_found={ret.service_found}, contexts={ret.contexts}"
        elif case.get("is_ambiguous"):
            if not ret.is_ambiguous:
                ok = False
                err_msg = "Expected is_ambiguous=True"
        elif case.get("is_comparison"):
            if len(ret.contexts) < 2:
                ok = False
                err_msg = f"Expected multiple contexts for comparison, got {len(ret.contexts)}"
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
            elif case.get("expected_kw_in_ctx"):
                all_ctx = " ".join(ret.contexts)
                if case["expected_kw_in_ctx"] not in all_ctx:
                    ok = False
                    err_msg = f"Keyword '{case['expected_kw_in_ctx']}' not found in contexts: {all_ctx[:100]}..."

        status_str = "PASS" if ok else "FAIL"
        print(f"[{status_str}] {case['name']}")
        if not ok:
            print(f"       -> Reason: {err_msg}")
        else:
            passed += 1

    print("=" * 60)
    print(f"RESULTS: {passed}/{total} Passed ({(passed/total)*100:.1f}%)")
    print("=" * 60)


if __name__ == "__main__":
    run_tests()
