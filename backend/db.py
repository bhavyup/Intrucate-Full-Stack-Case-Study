import os

from pymongo import MongoClient

_client = None


def get_db():
    """One shared client for the process; MongoClient is thread-safe
    and already pools connections, so there's no reason to open
    new ones per request."""
    global _client
    if _client is None:
        _client = MongoClient(os.environ["MONGO_URI"])
    return _client[os.environ.get("MONGO_DB", "intucate")]
