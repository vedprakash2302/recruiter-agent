from qdrant_client import QdrantClient
import os

qdrant_client = QdrantClient(url=os.getenv("QDRANT_URL"))