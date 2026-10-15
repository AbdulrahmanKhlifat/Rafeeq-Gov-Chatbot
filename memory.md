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

## Current Status
- **Current Phase**: Phase 0 (Git & Shared Contracts) & Phase 1 (Ollama Installation & Model Setup).
- **Environment**: Windows 11 Pro, Python 3.14.2, winget available. Ollama is not yet installed.

---

## Immediate Next Steps
1. **Initialize Git & Shared Files**:
   - Initialize git repo, create `.gitignore`, `requirements.txt`, and `src/types.py`.
   - Push initial commit to `https://github.com/AbdulrahmanKhlifat/Rafeeq-Gov-Chatbot.git`.
   - Checkout branch `feature/llm-evaluator`.
2. **Install Ollama & Download Model**:
   - Install Ollama via `winget install Ollama.Ollama` or download official installer.
   - Start Ollama server.
   - Pull target ~7B model (recommend `qwen2.5:7b` for superior Arabic comprehension and rule extraction).
3. **Build `src/generator.py`**:
   - Implement HTTP client to communicate with `http://localhost:11434/api/generate`.
   - Implement Arabic system prompts and zero-latency guardrail for out-of-scope queries.
   - Unit test inference on CPU.
