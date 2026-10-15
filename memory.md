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

8. **AI Model & Ollama Setup**:
   - Initiated Ollama download and installation via `winget`.

---

## Current Status
- **Current Phase**: Phase 1 (Ollama Installation & Model Pull).
- **Branch**: `feature/llm-evaluator`
- **Verification Status**: End-to-end pipeline tested on `questions.json`; generated `answers.json` structurally identical to `answers_example.json`.

---

## Immediate Next Steps
1. Complete Ollama setup and verify daemon (`ollama serve` / `ollama list`).
2. Pull `qwen2.5:7b` (or provided hackathon model) locally.
3. Test end-to-end inference through Ollama with the 7B model.
4. Push `feature/llm-evaluator` updates to GitHub so teammates can see the working generator and `main.py`.

