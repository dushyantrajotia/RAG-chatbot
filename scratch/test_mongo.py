import sys
sys.path.insert(0, r"c:\Users\nerdyxdr\Desktop\RAG-chatbot")
from unittest.mock import MagicMock

# Mock dotenv
sys.modules['dotenv'] = MagicMock()

# Mock pymongo
mock_pymongo = MagicMock()
mock_client = MagicMock()
mock_db = MagicMock()

existing_collections = []
def mock_create_collection(name):
    existing_collections.append(name)
    return MagicMock()

mock_db.list_collection_names.side_effect = lambda: existing_collections
mock_db.create_collection.side_effect = mock_create_collection
mock_db.__getitem__.side_effect = lambda name: f"collection_{name}"

mock_client.__getitem__.return_value = mock_db
mock_pymongo.MongoClient.return_value = mock_client
sys.modules['pymongo'] = mock_pymongo
sys.modules['pymongo.database'] = MagicMock()
sys.modules['pymongo.collection'] = MagicMock()

# Mock config settings
mock_settings = MagicMock()
mock_settings.MONGO_URI = "mongodb://localhost:27017/rag_chatbot"
mock_config_module = MagicMock()
mock_config_module.settings = mock_settings
sys.modules['app.core.config'] = mock_config_module

# Import mongo module
import app.db.mongo as mongo_mod

# Test connect_to_mongo
db = mongo_mod.connect_to_mongo()
assert db == mock_db, "connect_to_mongo should return database instance"

# Verify required collections were created
required = ["users", "conversations", "leads", "documents"]
for coll in required:
    assert coll in existing_collections, f"Collection '{coll}' should be initialized"

# Test collection getter helpers
assert mongo_mod.get_users_collection() == "collection_users"
assert mongo_mod.get_conversations_collection() == "collection_conversations"
assert mongo_mod.get_leads_collection() == "collection_leads"
assert mongo_mod.get_documents_collection() == "collection_documents"

# Test closing connection
mongo_mod.close_mongo_connection()
assert mongo_mod.mongo_manager.client is None

print("Verification SUCCESS: PyMongo database connection, collection creation (users, conversations, leads, documents), and helper getters verified!")
