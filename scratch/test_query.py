import sys
sys.path.insert(0, r"c:\Users\nerdyxdr\Desktop\RAG-chatbot")
from unittest.mock import MagicMock

# Create mock modules
sys.modules['dotenv'] = MagicMock()
sys.modules['langchain_community'] = MagicMock()
sys.modules['langchain_community.vectorstores'] = MagicMock()
sys.modules['langchain_google_genai'] = MagicMock()
sys.modules['langchain_openai'] = MagicMock()
sys.modules['langchain_core'] = MagicMock()
sys.modules['langchain_core.prompts'] = MagicMock()

# Mock config settings
mock_settings = MagicMock()
mock_settings.GEMINI_API_KEY = "mock-gemini-key"
mock_settings.OPENAI_API_KEY = ""
mock_config_module = MagicMock()
mock_config_module.settings = mock_settings
sys.modules['app.core.config'] = mock_config_module

# Mocking GoogleGenerativeAIEmbeddings and OpenAIEmbeddings
mock_google_embeddings = MagicMock()
sys.modules['langchain_google_genai'].GoogleGenerativeAIEmbeddings = mock_google_embeddings

mock_openai_embeddings = MagicMock()
sys.modules['langchain_openai'].OpenAIEmbeddings = mock_openai_embeddings

# Mocking ChatGoogleGenerativeAI and ChatOpenAI
mock_chat_gemini = MagicMock()
sys.modules['langchain_google_genai'].ChatGoogleGenerativeAI = mock_chat_gemini

mock_chat_openai = MagicMock()
sys.modules['langchain_openai'].ChatOpenAI = mock_chat_openai

# Mocking FAISS vector store
class MockDocument:
    def __init__(self, content, source):
        self.page_content = content
        self.metadata = {"source": source}

mock_faiss_db = MagicMock()
mock_faiss_db.similarity_search_with_score.return_value = [
    (MockDocument("This is chunk 1 of relevant text.", "test_doc.txt"), 0.1500),
    (MockDocument("Here is another matched segment of information.", "test_doc.txt"), 0.2840),
]

mock_faiss = MagicMock()
mock_faiss.load_local.return_value = mock_faiss_db
sys.modules['langchain_community.vectorstores'].FAISS = mock_faiss

# Mocking PromptTemplate and LCEL OR operator (|)
mock_chain = MagicMock()
mock_response = MagicMock()
mock_response.content = "This is the generated answer from the RAG chatbot."
mock_chain.invoke.return_value = mock_response

mock_prompt_template_class = MagicMock()
mock_prompt_template_instance = MagicMock()
mock_prompt_template_instance.__or__.return_value = mock_chain
mock_prompt_template_class.return_value = mock_prompt_template_instance
sys.modules['langchain_core.prompts'].PromptTemplate = mock_prompt_template_class

# Setup sys.argv to simulate running the query script
import tempfile
import shutil
from pathlib import Path

temp_dir = tempfile.mkdtemp()

try:
    sys.argv = ["scripts/query.py", "What is RAG?", "--index", temp_dir]
    
    # Import and run main
    if 'scripts.query' in sys.modules:
        del sys.modules['scripts.query']
    import scripts.query as query
    query.main()
    
    # Check assertions
    mock_faiss.load_local.assert_called_once_with(temp_dir, mock_google_embeddings.return_value, allow_dangerous_deserialization=True)
    mock_faiss_db.similarity_search_with_score.assert_called_once_with("What is RAG?", k=4)
    mock_chat_gemini.assert_called_once_with(model="gemini-1.5-flash", google_api_key="mock-gemini-key", temperature=0.7)
    mock_chain.invoke.assert_called_once()
    
    print("Verification SUCCESS: Complete RAG query and LLM answer generation flow verified!")
finally:
    shutil.rmtree(temp_dir, ignore_errors=True)
