import pymongo
from app.core.config import settings, logger
from typing import Any, Dict, Optional

# Global MongoDB client instance
mongo_client: Optional[pymongo.MongoClient] = None


def get_mongo_client() -> pymongo.MongoClient:
    global mongo_client
    if mongo_client is None:
        try:
            mongo_client = pymongo.MongoClient(
                settings.MONGODB_URI, serverSelectionTimeoutMS=5000
            )
            mongo_client.admin.command("ping")  # Verify connection
            logger.info("Successfully connected to MongoDB.")
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise  # Re-raise exception to handle during startup or first access
    return mongo_client


def get_db():
    client = get_mongo_client()
    return client[settings.MONGODB_DATABASE_NAME]


def get_users_collection():
    db = get_db()
    users_coll = db[settings.MONGODB_USERS_COLLECTION]
    # Ensure indexes (idempotent operation)
    users_coll.create_index(
        [("google_id", pymongo.ASCENDING)], unique=True, background=True
    )
    users_coll.create_index(
        [("email", pymongo.ASCENDING)], unique=True, background=True
    )
    return users_coll


def get_chat_collection():
    db = get_db()
    chat_coll = db["chat_conversations"]
    # Ensure indexes for chat queries
    chat_coll.create_index(
        [
            ("user_id", pymongo.ASCENDING),
            ("map_id", pymongo.ASCENDING),
            ("node_id", pymongo.ASCENDING),
        ],
        unique=True,
        background=True,
    )
    chat_coll.create_index([("user_id", pymongo.ASCENDING)], background=True)
    chat_coll.create_index([("updated_at", pymongo.DESCENDING)], background=True)
    chat_coll.create_index([("is_deleted", pymongo.ASCENDING)], background=True)
    return chat_coll


def mongo_to_pydantic(doc: Dict[str, Any], model_class):
    if doc and "_id" in doc:
        doc["id"] = str(doc["_id"])
    return model_class(**doc)


# Call this during app startup to initialize client and log connection status
def init_mongodb():
    get_mongo_client()  # Initializes and pings
