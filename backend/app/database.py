"""Database connection and session management for MongoDB."""

import mongoengine
from app.config import settings

def connect_db(url: str = None, db_name: str = None, **kwargs):
    """Establish connection to MongoDB if not already established."""
    url = url or settings.MONGODB_URL
    db_name = db_name or settings.MONGODB_DB_NAME
    try:
        return mongoengine.connection.get_connection("default")
    except Exception:
        pass
    return mongoengine.connect(
        db=db_name,
        host=url,
        alias="default",
        **kwargs
    )

def disconnect_db(alias: str = "default"):
    """Disconnect from MongoDB."""
    try:
        mongoengine.disconnect(alias=alias)
    except Exception:
        pass

def get_db():
    """Dependency for obtaining MongoDB database per request."""
    try:
        db = mongoengine.connection.get_db()
    except Exception:
        db = None
    try:
        yield db
    finally:
        pass
