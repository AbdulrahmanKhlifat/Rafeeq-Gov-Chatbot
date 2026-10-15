# Project Phases — Rafeeq (رفيق) Gov Chatbot
**AI Future 26 Hackathon (42 Irbid & M.A.T Academy)**

---

## High-Level Project Roadmap

| Phase | Phase Name | Description & Focus | Primary Owner | Status |
| :--- | :--- | :--- | :--- | :--- |
| **Phase 0** | **Repo & Environment Bootstrap** | Git repository init, contracts (`src/types.py`), folder layout, base branch pushes. | Person 2 (Lead) | 🔄 In Progress |
| **Phase 1** | **Ollama & LLM Infrastructure** | Install Ollama, pull recommended ~7B model (`qwen2.5:7b`), build Python Ollama client with timeout/fallbacks. | Person 2 | 🔄 In Progress |
| **Phase 2** | **Data Ingestion & Dialect Engine** | Parse 12 raw files into structured representations; build keyword & Jordanian dialect routing; exact snippet extraction. | Person 1 | ⏳ Pending |
| **Phase 3** | **Prompt Engineering & Hallucination Guardrails** | Build Arabic prompts enforcing strict grounding in retrieved contexts; direct zero-shot refusal for out-of-scope; clarification prompts. | Person 2 | ⏳ Pending |
| **Phase 4** | **Evaluation Core & Multi-turn Memory (`main.py`)** | Implement official CLI entrypoint `python main.py questions.json` -> `answers.json`; multi-turn chat state tracking; exception protection. | Person 2 | ⏳ Pending |
| **Phase 5** | **Interactive Web UI Demo** | Streamlit chat interface with groundedness badge & context visualizer for judges' presentation. | Person 3 | ⏳ Pending |
| **Phase 6** | **Integration, Offline Hardening & Verification** | Pull all feature branches to `main`; benchmark against `answers_example.json`; test with Wi-Fi disabled. | All (Lead: P2) | ⏳ Pending |

---

## Detailed Breakdown for Person 2 (LLM Pipeline, Prompts & Evaluation Runner)

### Phase 0: Project Setup & Git Repository
- [x] Analyze `challenge_brief.pdf`, `questions.json`, `answers_example.json`, and sample data.
- [ ] Initialize Git repository locally in `participant_pack`.
- [ ] Connect remote `https://github.com/AbdulrahmanKhlifat/Rafeeq-Gov-Chatbot.git`.
- [ ] Create shared `.gitignore`, `requirements.txt`, and contract `src/types.py`.
- [ ] Push initial structure to `main` branch.
- [ ] Checkout working branch `feature/llm-evaluator`.

### Phase 1: Ollama Model Setup & Connection Harness
- [ ] Install Ollama on local machine.
- [ ] Start Ollama service (`ollama serve`).
- [ ] Pull target ~7B Arabic-capable model: `qwen2.5:7b` (recommended default for Arabic instruction following and fee reasoning).
- [ ] Create `src/generator.py` with direct HTTP API client to `http://localhost:11434/api/generate`.
- [ ] Configure deterministic parameters: `temperature=0.1`, `num_predict=256`, `num_ctx=2048`.
- [ ] Implement unit test verifying local offline inference works.

### Phase 2: Data Extraction & Dialect Engine (Coordinated with Person 1)
- [ ] Define the exact dictionary schema for the 12 services (Document $\times$ Situation $\times$ 9 fields).
- [ ] Ensure Person 1's `KnowledgeEngine.retrieve(question, history)` outputs the exact `RetrievalResult` contract.
- [ ] Verify mock retrieval outputs match the format of `answers_example.json`.

### Phase 3: Prompt Engineering & Guardrails
- [ ] System Prompt Design:
  - Strict grounding instruction: answers must come strictly from provided context.
  - Number & rule precision: exact age checks ($\ge 16$, $< 16$), duration checks ($< 180$ days, $> 180$ days), urgent fees ($+25$ JOD).
  - Tone & format: concise, direct Arabic without fluff.
- [ ] Guardrails (0ms bypass without LLM call):
  - **Out-of-Scope**: If `service_found == False`, immediately return standard refusal message with `contexts = []`.
  - **Ambiguity**: If `is_ambiguous == True`, prompt citizen to specify the document.
- [ ] Test prompts against hard test cases (fees for 17-year old with 3 months remaining, photos needed for ID vs passport).

### Phase 4: Evaluation CLI Engine (`main.py`)
- [ ] Implement CLI argument handling: `python main.py <questions_file>`.
- [ ] Implement conversation loop:
  - Process chats sequentially.
  - Maintain `history` buffer within each chat and reset across chats.
  - Add `"answer"` and `"contexts"` to every message dictionary.
- [ ] Add bulletproof error handling:
  - Enclose each message processing step in `try...except`.
  - On error, output graceful fallback answer, ensuring script **never crashes** and **all answers are scored**.
- [ ] Write output file `answers.json` in root with UTF-8 encoding (`ensure_ascii=False`).

### Phase 5: Team Integration & Merge
- [ ] Pull and review Person 1's `feature/retrieval-engine`.
- [ ] Connect real `KnowledgeEngine` to `main.py`.
- [ ] Merge `feature/llm-evaluator` into `main`.
- [ ] Assist Person 3 in hooking `src/app.py` to `KnowledgeEngine` and `ResponseGenerator`.

### Phase 6: Offline Testing & Final Delivery Checklist
- [ ] Disconnect Wi-Fi completely.
- [ ] Run `python main.py questions.json`.
- [ ] Verify `answers.json` structure against `answers_example.json`.
- [ ] Verify latency per question (must be $\le 3-5$ seconds).
- [ ] Ensure no broken Unicode characters in output.
- [ ] Prepare pitch walkthrough: explain data handling, routing mechanism, and hallucination prevention.
