import argparse
import sys
import os
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description="Query the local FAISS vector store for relevant chunks.")
    parser.add_argument("question", type=str, help="The query question to ask the database")
    parser.add_argument("--index", type=str, default="faiss_index", help="Path to the saved FAISS index directory (default: faiss_index)")
    args = parser.parse_args()
    
    index_path = Path(args.index)
    if not index_path.exists():
        print(f"Error: FAISS index directory '{index_path}' does not exist.", file=sys.stderr)
        sys.exit(1)
        
    # Load configuration settings
    try:
        from app.core.config import settings
        gemini_key = settings.GEMINI_API_KEY
        openai_key = settings.OPENAI_API_KEY
    except Exception as e:
        print(f"Warning: Could not load app.core.config: {e}. Falling back to standard environment variables.")
        gemini_key = os.getenv("GEMINI_API_KEY", "")
        openai_key = os.getenv("OPENAI_API_KEY", "")

    embeddings = None
    if gemini_key:
        print("Initializing Gemini embeddings...")
        try:
            from langchain_google_genai import GoogleGenerativeAIEmbeddings
            embeddings = GoogleGenerativeAIEmbeddings(
                model="models/embedding-001",
                google_api_key=gemini_key
            )
        except Exception as e:
            print(f"Error initializing Gemini embeddings: {e}", file=sys.stderr)
    
    if not embeddings and openai_key:
        print("Gemini API Key not set or failed to initialize. Trying OpenAI embeddings...")
        try:
            from langchain_openai import OpenAIEmbeddings
            embeddings = OpenAIEmbeddings(
                api_key=openai_key
            )
        except Exception as e:
            print(f"Error initializing OpenAI embeddings: {e}", file=sys.stderr)
            
    if not embeddings:
        print("Error: No valid embedding model could be initialized. Please set GEMINI_API_KEY or OPENAI_API_KEY.", file=sys.stderr)
        sys.exit(1)

    print(f"Loading FAISS index from: {index_path.resolve()}...")
    try:
        from langchain_community.vectorstores import FAISS
        db = FAISS.load_local(str(index_path), embeddings, allow_dangerous_deserialization=True)
    except Exception as e:
        print(f"Error loading FAISS index: {e}", file=sys.stderr)
        sys.exit(1)
        
    print(f"Retrieving top-4 relevant chunks for query: '{args.question}'...")
    try:
        results = db.similarity_search_with_score(args.question, k=4)
    except Exception as e:
        print(f"Error executing similarity search: {e}", file=sys.stderr)
        sys.exit(1)
        
    print(f"\nFound {len(results)} matches (lower score = higher similarity):\n")
    for i, (doc, score) in enumerate(results, start=1):
        print(f"--- Match {i} (Score/Distance: {score:.4f}) ---")
        print(doc.page_content.strip())
        print(f"Source: {doc.metadata.get('source', 'Unknown')}")
        print("-" * 50)

    # Initialize the LLM
    llm = None
    if gemini_key:
        print("Initializing Gemini LLM (gemini-1.5-flash)...")
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            llm = ChatGoogleGenerativeAI(
                model="gemini-1.5-flash",
                google_api_key=gemini_key,
                temperature=0.7
            )
        except Exception as e:
            print(f"Error initializing Gemini LLM: {e}", file=sys.stderr)
            
    if not llm and openai_key:
        print("Gemini key not set or failed to initialize LLM. Trying OpenAI LLM (gpt-4o-mini)...")
        try:
            from langchain_openai import ChatOpenAI
            llm = ChatOpenAI(
                model="gpt-4o-mini",
                api_key=openai_key,
                temperature=0.7
            )
        except Exception as e:
            print(f"Error initializing OpenAI LLM: {e}", file=sys.stderr)

    if not llm:
        print("Warning: No valid LLM could be initialized. Skipping answer generation. Please check GEMINI_API_KEY or OPENAI_API_KEY.", file=sys.stderr)
        return

    # Prepare context and template
    context = "\n\n".join([f"[Source: {doc.metadata.get('source', 'Unknown')}]\n{doc.page_content}" for doc, _ in results])
    
    from langchain_core.prompts import PromptTemplate
    
    template = """You are a helpful assistant. Answer the user's question using only the provided context. If the context does not contain the answer, say "I don't know based on the provided documents."
    
    Context:
    {context}
    
    Question: {question}
    
    Answer:"""
    
    prompt = PromptTemplate(
        template=template,
        input_variables=["context", "question"]
    )
    
    # Run prompt through LLM chain
    print("\nGenerating answer...")
    try:
        chain = prompt | llm
        response = chain.invoke({"context": context, "question": args.question})
        
        if hasattr(response, "content"):
            answer = response.content
        else:
            answer = str(response)
            
        print("\n=== Generated Answer ===")
        print(answer.strip())
        print("========================\n")
    except Exception as e:
        print(f"Error generating answer: {e}", file=sys.stderr)

if __name__ == "__main__":
    main()
