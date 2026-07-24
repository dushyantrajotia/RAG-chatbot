import os
from typing import Optional
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.collection import Collection
from app.core.config import settings

class MongoManager:
    """Singleton MongoDB client and database connection manager."""
    client: Optional[MongoClient] = None
    db: Optional[Database] = None

mongo_manager = MongoManager()

def connect_to_mongo() -> Database:
    """Establishes connection to MongoDB and creates required collections if they do not exist."""
    if mongo_manager.db is not None:
        return mongo_manager.db

    mongo_uri = settings.MONGO_URI
    mongo_manager.client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
    
    # Extract database name from MONGO_URI, default to 'rag_chatbot'
    parts = mongo_uri.rstrip("/").split("/")
    db_name = parts[-1].split("?")[0] if len(parts) > 3 and parts[-1] else "rag_chatbot"
    
    mongo_manager.db = mongo_manager.client[db_name]
    
    # Ensure required collections exist
    existing_collections = mongo_manager.db.list_collection_names()
    required_collections = ["users", "conversations", "leads", "documents", "feedback"]
    for collection in required_collections:
        if collection not in existing_collections:
            mongo_manager.db.create_collection(collection)
            
    return mongo_manager.db

def get_database() -> Database:
    """Returns active MongoDB database instance, initializing if needed."""
    if mongo_manager.db is None:
        return connect_to_mongo()
    return mongo_manager.db

def close_mongo_connection():
    """Closes the MongoDB client connection."""
    if mongo_manager.client is not None:
        mongo_manager.client.close()
        mongo_manager.client = None
        mongo_manager.db = None

# Collection helpers
def get_users_collection() -> Collection:
    return get_database()["users"]

def get_conversations_collection() -> Collection:
    return get_database()["conversations"]

def get_leads_collection() -> Collection:
    return get_database()["leads"]

from datetime import datetime, timezone

def get_documents_collection() -> Collection:
    return get_database()["documents"]

def save_conversation_turn(session_id: str, message: str, answer: str) -> Optional[str]:
    """Persists a conversation turn (session_id, message, answer, timestamp) to MongoDB conversations collection."""
    try:
        conversations = get_conversations_collection()
        turn_doc = {
            "session_id": session_id,
            "message": message,
            "answer": answer,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        result = conversations.insert_one(turn_doc)
        return str(result.inserted_id) if hasattr(result, "inserted_id") else None
    except Exception as e:
        print(f"Warning: Failed to save conversation turn to MongoDB: {e}")
        return None

def save_feedback(conversation_id: str, rating: str) -> bool:
    """Stores the feedback linked to the conversation in MongoDB."""
    try:
        from bson import ObjectId
        db = get_database()
        
        # 1. Store in feedback collection
        feedback_coll = db["feedback"]
        feedback_doc = {
            "conversation_id": conversation_id,
            "rating": rating,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        feedback_coll.insert_one(feedback_doc)
        
        # 2. Link by updating conversations collection directly
        conversations = get_conversations_collection()
        try:
            obj_id = ObjectId(conversation_id)
            conversations.update_one({"_id": obj_id}, {"$set": {"feedback": rating}})
        except Exception:
            # If not an ObjectId, fallback to session_id
            conversations.update_many({"session_id": conversation_id}, {"$set": {"feedback": rating}})
            
        return True
    except Exception as e:
        print(f"Warning: Failed to save feedback to MongoDB: {e}")
        return False


