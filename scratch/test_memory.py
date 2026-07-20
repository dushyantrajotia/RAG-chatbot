import sys
sys.path.insert(0, r"c:\Users\nerdyxdr\Desktop\RAG-chatbot")

from app.services.memory import memory_manager

# Test Turn 1 for session_A
memory_manager.add_interaction("session_A", question="What is your name?", answer="I am RAG Bot.")
history_1 = memory_manager.get_history_string("session_A")
assert "User: What is your name?" in history_1
assert "Assistant: I am RAG Bot." in history_1

# Test Turn 2 for session_A
memory_manager.add_interaction("session_A", question="What can you do?", answer="I answer questions based on documents.")
history_2 = memory_manager.get_history_string("session_A")
assert "User: What can you do?" in history_2
assert "Assistant: I answer questions based on documents." in history_2

# Test multi-turn order
lines = history_2.split("\n")
assert len(lines) == 4, f"Expected 4 history lines, got {len(lines)}"

# Test session isolation (session_B should be empty)
history_B = memory_manager.get_history_string("session_B")
assert history_B == "", "Session B history should be empty"

# Test clearing session_A
memory_manager.clear_session("session_A")
history_cleared = memory_manager.get_history_string("session_A")
assert history_cleared == "", "Session A history should be cleared"

print("Verification SUCCESS: Multi-turn conversation memory, session isolation, and clearing verified!")
