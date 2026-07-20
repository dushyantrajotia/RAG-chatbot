from pathlib import Path
from typing import Dict, Any
from app.services.rag_service import get_embeddings

def ingest_file_to_faiss(file_path: str, index_path: str = "faiss_index") -> Dict[str, Any]:
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File '{file_path}' does not exist.")

    suffix = path.suffix.lower()
    
    from langchain_community.document_loaders import TextLoader, PyPDFLoader, Docx2txtLoader
    if suffix == ".txt":
        loader = TextLoader(str(path), encoding="utf-8")
    elif suffix == ".pdf":
        loader = PyPDFLoader(str(path))
    elif suffix == ".docx":
        loader = Docx2txtLoader(str(path))
    else:
        raise ValueError(f"Unsupported file format '{suffix}'. Supported formats are: .pdf, .docx, .txt")

    documents = loader.load()
    
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = text_splitter.split_documents(documents)
    
    if not chunks:
        return {
            "filename": path.name,
            "chunks_added": 0,
            "message": "No text content found to index."
        }

    embeddings = get_embeddings()
    index_dir = Path(index_path)
    
    from langchain_community.vectorstores import FAISS
    if index_dir.exists() and (index_dir / "index.faiss").exists():
        db = FAISS.load_local(str(index_dir), embeddings, allow_dangerous_deserialization=True)
        db.add_documents(chunks)
    else:
        db = FAISS.from_documents(chunks, embeddings)
        
    db.save_local(str(index_dir))
    
    return {
        "filename": path.name,
        "chunks_added": len(chunks),
        "index_path": str(index_dir.resolve())
    }
