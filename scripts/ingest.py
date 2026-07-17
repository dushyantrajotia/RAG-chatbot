import argparse
import sys
import os
from pathlib import Path
from langchain_community.document_loaders import TextLoader, PyPDFLoader, Docx2txtLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

def main():
    parser = argparse.ArgumentParser(description="Ingest a PDF, DOCX, or TXT file, split it, embed chunks, and save to FAISS.")
    parser.add_argument("file_path", type=str, help="Path to the file to ingest")
    parser.add_argument("--output", type=str, default="faiss_index", help="Directory path to save the FAISS index (default: faiss_index)")
    args = parser.parse_args()
    
    file_path = Path(args.file_path)
    if not file_path.exists():
        print(f"Error: File '{file_path}' does not exist.", file=sys.stderr)
        sys.exit(1)
    
    suffix = file_path.suffix.lower()
    
    print(f"Loading {file_path}...")
    try:
        if suffix == ".txt":
            loader = TextLoader(str(file_path), encoding="utf-8")
        elif suffix == ".pdf":
            loader = PyPDFLoader(str(file_path))
        elif suffix == ".docx":
            loader = Docx2txtLoader(str(file_path))
        else:
            print(f"Error: Unsupported file extension '{suffix}'. Supported formats are: .pdf, .docx, .txt", file=sys.stderr)
            sys.exit(1)
            
        documents = loader.load()
    except Exception as e:
        print(f"Error loading file: {e}", file=sys.stderr)
        sys.exit(1)
        
    print(f"Loaded {len(documents)} document section(s)/page(s).")
    
    # Split using RecursiveCharacterTextSplitter
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )
    
    chunks = text_splitter.split_documents(documents)
    print(f"Split into {len(chunks)} chunks.")
    
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

    print("Generating embeddings and creating FAISS index...")
    try:
        from langchain_community.vectorstores import FAISS
        db = FAISS.from_documents(chunks, embeddings)
        
        output_path = Path(args.output)
        db.save_local(str(output_path))
        print(f"FAISS index successfully saved to: {output_path.resolve()}")
    except Exception as e:
        print(f"Error creating/saving FAISS index: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
