# main.py
"""
Official Hackathon Evaluation Entrypoint for Rafeeq (رفيق) Gov Chatbot.
Owner: Person 2 (Evaluation Core & Pipeline Orchestrator)

Usage:
    python main.py questions.json
Output:
    answers.json (in the same directory)
"""

import sys
import os
import json
import time
from src.engine import KnowledgeEngine
from src.generator import ResponseGenerator


def run_evaluation(input_filepath: str, output_filepath: str = "answers.json"):
    print(f"[*] Starting Rafeeq (رفيق) Evaluation Pipeline...")
    print(f"[*] Loading input questions from: {input_filepath}")

    if not os.path.exists(input_filepath):
        print(f"[!] Error: File '{input_filepath}' not found.")
        sys.exit(1)

    start_time = time.time()

    # Initialize components
    engine = KnowledgeEngine(data_dir="data")
    generator = ResponseGenerator()

    # Load input questions strictly with UTF-8
    with open(input_filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    total_chats = len(data.get("chats", []))
    total_messages = 0
    successful_answers = 0

    print(f"[*] Processing {total_chats} chats...")

    for chat_idx, chat in enumerate(data.get("chats", []), 1):
        chat_id = chat.get("chat_id", f"chat-{chat_idx}")
        messages = chat.get("messages", [])
        
        # Reset conversation history for each new chat (citizen isolation)
        chat_history = []

        for msg in messages:
            total_messages += 1
            question = msg.get("question", "").strip()

            try:
                # 1. Retrieve relevant contexts and intent (Person 1's engine)
                retrieval = engine.retrieve(question, history=chat_history)

                # 2. Generate grounded answer (Person 2's generator)
                res = generator.generate(question, retrieval)

                # 3. Inject answers and contexts matching strict hackathon specification
                msg["answer"] = res.answer
                msg["contexts"] = res.contexts

                # 4. Update conversation state for subsequent questions in the same chat
                chat_history.append({
                    "question": question,
                    "answer": res.answer
                })
                successful_answers += 1

            except Exception as e:
                # Fault tolerance: catch per-message error to ensure complete file output
                print(f"[!] Warning on message {msg.get('message_id')}: {e}")
                msg["answer"] = "عذراً، حدث خطأ غير متوقع أثناء معالجة استفسارك."
                msg["contexts"] = []

    # Write output file strictly with UTF-8 and ensure_ascii=False
    with open(output_filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    elapsed = time.time() - start_time
    print(f"[+] Evaluation finished successfully in {elapsed:.2f}s!")
    print(f"[+] Total messages processed: {total_messages} ({successful_answers} successful)")
    print(f"[+] Answers saved to: {output_filepath}")


if __name__ == "__main__":
    input_file = sys.argv[1] if len(sys.argv) > 1 else "questions.json"
    run_evaluation(input_file)
