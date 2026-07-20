from typing import Dict, List, Any

class SimpleMemoryStore:
    """Fallback in-memory conversation store for multi-turn chat."""
    def __init__(self):
        self.history: List[Dict[str, str]] = []

    def add_user_message(self, message: str):
        self.history.append({"role": "User", "content": message})

    def add_ai_message(self, message: str):
        self.history.append({"role": "Assistant", "content": message})

    def get_history_string(self) -> str:
        if not self.history:
            return ""
        return "\n".join([f"{item['role']}: {item['content']}" for item in self.history])

    def clear(self):
        self.history.clear()

class SessionMemoryManager:
    """Manages multi-turn conversation memories keyed by session_id."""
    def __init__(self):
        self._stores: Dict[str, Any] = {}

    def get_store(self, session_id: str):
        if session_id not in self._stores:
            try:
                from langchain.memory import ConversationBufferMemory
                memory = ConversationBufferMemory(
                    memory_key="chat_history",
                    return_messages=True,
                    output_key="answer",
                    input_key="question"
                )
                self._stores[session_id] = memory
            except Exception:
                self._stores[session_id] = SimpleMemoryStore()
        return self._stores[session_id]

    def add_interaction(self, session_id: str, question: str, answer: str):
        store = self.get_store(session_id)
        if hasattr(store, "save_context"):
            store.save_context({"question": question}, {"answer": answer})
        elif hasattr(store, "add_user_message"):
            store.add_user_message(question)
            store.add_ai_message(answer)

    def get_history_string(self, session_id: str) -> str:
        store = self.get_store(session_id)
        if hasattr(store, "chat_memory"):
            messages = store.chat_memory.messages
            if not messages:
                return ""
            lines = []
            for msg in messages:
                role = "User" if getattr(msg, "type", "") in ["human", "user"] else "Assistant"
                lines.append(f"{role}: {getattr(msg, 'content', '')}")
            return "\n".join(lines)
        elif hasattr(store, "get_history_string"):
            return store.get_history_string()
        return ""

    def clear_session(self, session_id: str):
        if session_id in self._stores:
            del self._stores[session_id]

memory_manager = SessionMemoryManager()
