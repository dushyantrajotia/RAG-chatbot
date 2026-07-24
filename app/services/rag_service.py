import os
from pathlib import Path
from typing import Dict, Any, List
from app.core.config import settings

def get_embeddings():
    gemini_key = settings.GEMINI_API_KEY
    openai_key = settings.OPENAI_API_KEY

    if gemini_key:
        try:
            from langchain_google_genai import GoogleGenerativeAIEmbeddings
            return GoogleGenerativeAIEmbeddings(
                model="models/gemini-embedding-001",
                google_api_key=gemini_key
            )
        except Exception as e:
            print(f"Error initializing Gemini embeddings: {e}")
    
    if openai_key:
        try:
            from langchain_openai import OpenAIEmbeddings
            return OpenAIEmbeddings(
                api_key=openai_key
            )
        except Exception as e:
            print(f"Error initializing OpenAI embeddings: {e}")

    raise ValueError("No valid embedding provider available. Please configure GEMINI_API_KEY or OPENAI_API_KEY.")

def get_llm():
    gemini_key = settings.GEMINI_API_KEY
    openai_key = settings.OPENAI_API_KEY

    if gemini_key:
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            return ChatGoogleGenerativeAI(
                model="gemini-3.1-flash-lite",
                google_api_key=gemini_key,
                temperature=0.7
            )
        except Exception as e:
            print(f"Error initializing Gemini LLM: {e}")

    if openai_key:
        try:
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(
                model="gpt-4o-mini",
                api_key=openai_key,
                temperature=0.7
            )
        except Exception as e:
            print(f"Error initializing OpenAI LLM: {e}")

    raise ValueError("No valid LLM provider available. Please configure GEMINI_API_KEY or OPENAI_API_KEY.")

from app.services.memory import memory_manager

def query_rag_pipeline(query: str, session_id: str = None, index_path: str = "faiss_index", k: int = 4) -> Dict[str, Any]:
    path = Path(index_path)
    if not path.exists():
        return {
            "answer": f"Vector index directory '{index_path}' not found. Please ingest documents first.",
            "sources": []
        }

    embeddings = get_embeddings()
    
    from langchain_community.vectorstores import FAISS
    db = FAISS.load_local(str(path), embeddings, allow_dangerous_deserialization=True)
    
    results = db.similarity_search_with_score(query, k=k)
    
    sources: List[Dict[str, Any]] = []
    for doc, score in results:
        sources.append({
            "source": doc.metadata.get("source", "Unknown"),
            "content": doc.page_content.strip(),
            "score": round(float(score), 4)
        })
        
    context = "\n\n".join([f"[Source: {s['source']}]\n{s['content']}" for s in sources])
    
    chat_history = memory_manager.get_history_string(session_id) if session_id else ""
    
    from langchain_core.prompts import PromptTemplate
    
    template = """You are a helpful assistant. Answer the user's question using the conversation history and provided context. If the answer cannot be determined, say "I don't know based on the provided documents."

Conversation History:
{chat_history}

Context:
{context}

Question: {question}

Answer:"""

    prompt = PromptTemplate(template=template, input_variables=["chat_history", "context", "question"])
    llm = get_llm()
    
    chain = prompt | llm
    response = chain.invoke({
        "chat_history": chat_history,
        "context": context,
        "question": query
    })
    
    answer = response.content if hasattr(response, "content") else str(response)
    if isinstance(answer, list):
        text_parts = []
        for part in answer:
            if isinstance(part, str):
                text_parts.append(part)
            elif isinstance(part, dict) and "text" in part:
                text_parts.append(part["text"])
        answer = "".join(text_parts)
    answer_str = answer.strip()
    
    if session_id:
        memory_manager.add_interaction(session_id=session_id, question=query, answer=answer_str)

    return {
        "answer": answer_str,
        "sources": sources
    }

