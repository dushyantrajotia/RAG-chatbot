import sys
sys.path.insert(0, r"c:\Users\nerdyxdr\Desktop\RAG-chatbot")
from unittest.mock import MagicMock

# Create mock modules
sys.modules['dotenv'] = MagicMock()
sys.modules['langchain_community'] = MagicMock()
sys.modules['langchain_community.document_loaders'] = MagicMock()
sys.modules['langchain_community.vectorstores'] = MagicMock()
sys.modules['langchain_text_splitters'] = MagicMock()
sys.modules['langchain_google_genai'] = MagicMock()
sys.modules['langchain_openai'] = MagicMock()

# Mock config settings
mock_settings = MagicMock()
mock_settings.GEMINI_API_KEY = "mock-gemini-key"
mock_settings.OPENAI_API_KEY = ""
mock_config_module = MagicMock()
mock_config_module.settings = mock_settings
sys.modules['app.core.config'] = mock_config_module

# Stub loaders
mock_loaders = MagicMock()
sys.modules['langchain_community.document_loaders'].TextLoader = mock_loaders.TextLoader
sys.modules['langchain_community.document_loaders'].PyPDFLoader = mock_loaders.PyPDFLoader
sys.modules['langchain_community.document_loaders'].Docx2txtLoader = mock_loaders.Docx2txtLoader

# Setup splitters mock
mock_split = MagicMock()
mock_split.split_documents.return_value = ["chunk1", "chunk2", "chunk3"]
mock_splitters = MagicMock()
mock_splitters.RecursiveCharacterTextSplitter.return_value = mock_split
sys.modules['langchain_text_splitters'].RecursiveCharacterTextSplitter = mock_splitters.RecursiveCharacterTextSplitter

# Mocking GoogleGenerativeAIEmbeddings and OpenAIEmbeddings
mock_google_embeddings = MagicMock()
sys.modules['langchain_google_genai'].GoogleGenerativeAIEmbeddings = mock_google_embeddings

mock_openai_embeddings = MagicMock()
sys.modules['langchain_openai'].OpenAIEmbeddings = mock_openai_embeddings

# Mocking FAISS vector store
mock_faiss_db = MagicMock()
mock_faiss = MagicMock()
mock_faiss.from_documents.return_value = mock_faiss_db
sys.modules['langchain_community.vectorstores'].FAISS = mock_faiss

# Mocking loader instances
mock_loader_instance = MagicMock()
mock_loader_instance.load.return_value = ["dummy document page content"]
mock_loaders.TextLoader.return_value = mock_loader_instance
mock_loaders.PyPDFLoader.return_value = mock_loader_instance
mock_loaders.Docx2txtLoader.return_value = mock_loader_instance

# Setup sys.argv to simulate running the script
import tempfile
import shutil
from pathlib import Path

with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
    f.write(b"Hello world")
    temp_name = f.name

temp_dir = tempfile.mkdtemp()

try:
    # Set sys.argv with a custom output path
    sys.argv = ["scripts/ingest.py", temp_name, "--output", temp_dir]
    
    # Import and run main (reload module to apply new mocks if needed)
    if 'scripts.ingest' in sys.modules:
        del sys.modules['scripts.ingest']
    import scripts.ingest as ingest
    ingest.main()
    
    # Check that loader, splitter, embeddings, and FAISS were called correctly
    mock_loaders.TextLoader.assert_called_once_with(temp_name, encoding="utf-8")
    mock_splitters.RecursiveCharacterTextSplitter.assert_called_once_with(chunk_size=500, chunk_overlap=50)
    mock_google_embeddings.assert_called_once_with(model="models/embedding-001", google_api_key="mock-gemini-key")
    mock_faiss.from_documents.assert_called_once_with(["chunk1", "chunk2", "chunk3"], mock_google_embeddings.return_value)
    mock_faiss_db.save_local.assert_called_once_with(temp_dir)
    
    print("Verification SUCCESS: Embeddings and FAISS storage logic completely verified!")
finally:
    Path(temp_name).unlink(missing_ok=True)
    shutil.rmtree(temp_dir, ignore_errors=True)
