from app.db.mongodb_utils import get_db
from app.core.config import logger


class MongoCollectionsCleaner:
    def __init__(self):
        self.db = get_db()

    def clear_all_collections(self):
        collection_names = self.db.list_collection_names()
        for name in collection_names:
            result = self.db[name].delete_many({})
            logger.info(
                f"Cleared {result.deleted_count} documents from collection '{name}'"
            )


if __name__ == "__main__":
    cleaner = MongoCollectionsCleaner()
    cleaner.clear_all_collections()
