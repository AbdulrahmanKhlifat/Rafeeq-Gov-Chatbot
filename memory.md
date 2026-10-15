# Project Memory & Execution Log — Rafeeq (رفيق) Gov Chatbot
**Role**: Person 2 (LLM Pipeline, Prompts & Evaluation Runner)  
**Repository**: https://github.com/AbdulrahmanKhlifat/Rafeeq-Gov-Chatbot.git  
**Last Updated**: 2026-10-15 11:45

---

## Log of Completed Actions

1. **Challenge Brief Analysis**:
   - Analyzed `challenge_brief.pdf` (Jordan Civil Status & Passports Chatbot).
   - Identified 12 target services (Passport, Family Book, Smart ID $\times$ First Issue, Renewal, Lost, Damaged).
   - Identified evaluation criteria: offline execution `python main.py questions.json`, exact output structure in `answers.json`, high penalty for wrong service or hallucination, bonus points for multi-turn chats.
   - Identified hardware specs: 13th Gen Intel Core i7-13620H (10 cores, 16 threads), 16GB RAM, Intel UHD Graphics (CPU inference).

2. **Team Architecture & Contracts Setup**:
   - Designed 3-person modular architecture (Person 1: Retrieval/Data, Person 2: LLM/CLI, Person 3: UI).
   - Defined zero-conflict git branch strategy: `feature/retrieval-engine`, `feature/llm-evaluator`, `feature/frontend-ui`.
   - Outlined `src/types.py` shared contract between all three components.

3. **Roadmap & Phase Tracking Documentation**:
   - Created `phases.md` with complete breakdown of phases 0 through 6.
   - Created `memory.md` to persist state, progress, and next steps.

---

4. **Repository Inception & Push to GitHub**:
   - Initialized Git repository and connected remote: `https://github.com/AbdulrahmanKhlifat/Rafeeq-Gov-Chatbot.git`.
   - Committed `.gitignore`, `requirements.txt`, `src/__init__.py`, `src/types.py`, `phases.md`, and `memory.md`.
   - Pushed `main` branch to remote GitHub repository.
   - Created and switched to working branch `feature/llm-evaluator`.

5. **LLM Generator Implementation (`src/generator.py`)**:
   - Implemented `ResponseGenerator` using Python standard library (`urllib.request`) to eliminate external offline package failures.
   - Configured deterministic sampling: `temperature=0.1`, `num_predict=256`, `num_ctx=2048`.
   - Built zero-latency refusal guardrail for out-of-scope queries (0ms LLM bypass).
   - Designed Arabic system prompt enforcing strict grounding in provided contexts.

6. **Knowledge Engine Baseline (`src/engine.py`)**:
   - Implemented 12-file text parser extracting sections (fees, documents, conditions, locations, time, notes).
   - Added keyword and Jordanian dialect mapping for documents, actions, and topics.
   - Added multi-turn conversational coreference resolution.

7. **Evaluation Pipeline (`main.py`)**:
   - Implemented official evaluation runner: `python main.py questions.json`.
   - Added per-message `try...except` fault tolerance.
   - Enforced UTF-8 file output to `answers.json` matching `answers_example.json` structure.
   - Verified end-to-end execution: 6 messages across 5 chats processed successfully.

8. **Phase 2 Implementation & Benchmark (`src/engine.py` & `tests/test_phase2.py`)**:
   - Parsed all 12 official government text files into structured schemas (`src/structured_services.json`).
   - Enhanced `KnowledgeEngine`:
     - Multi-service comparisons (e.g. lost vs. damaged passport fees).
     - Deep retrieval for facts hidden in "notes" (`ملاحظات`) such as head of family death rules.
     - Jordanian dialect mapping (`اهترى`, `خلص`, `قديش بدفع`, `شو بلزمني`, `الباسبور`, `الهوية`).
     - Coreference resolution across conversational turns (`history`).
     - Ambiguity detection (`is_ambiguous=True`).
   - Implemented `tests/test_phase2.py` testing 12 critical scenarios: **12/12 passed (100%)**.
   - Added health-check caching in `ResponseGenerator`, speeding up execution time from 20.6s to 3.07s.

---

## Current Status
- **Completed Phases**: Phase 0, Phase 1, Phase 2.
- **Current Phase**: Ready for Phase 3 (Prompt Tuning with Live LLM) & Phase 5 (Frontend for Person 3).
- **Benchmark Score**: 100% (12/12 test cases passing).
- **Evaluation Runner**: `python main.py questions.json` runs in 3.07 seconds and creates compliant `answers.json`.

---

## Immediate Next Steps
1. Push Phase 2 code and test suite to GitHub (`feature/llm-evaluator`).
2. Set up Ollama with a direct, reliable download or check if the user has an existing LLM/Ollama binary.
3. Prepare Person 3's Streamlit frontend (`src/app.py`).

