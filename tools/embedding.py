from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams
from config.qdrantclient import qdrant_client
from langchain.embeddings import HuggingFaceEmbeddings

embeddings_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")

def check_collection_exists(collection_name):
    """
    Check if a collection exists in Qdrant.
    Args:
        collection_name (str): The name of the collection to check
    Returns:
        bool: True if the collection exists, False otherwise
    """
    return qdrant_client.collection_exists(collection_name)

def initialize_vector_store(collection_name):
    """
    Initialize the Qdrant vector store with the specified collection name and embedding model.
    Args:
        None
    Returns:
        QdrantVectorStore: Initialized vector store object        
    """
    if not qdrant_client.collection_exists(collection_name):
        qdrant_client.recreate_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=3072, distance=Distance.COSINE)
        )

    vector_store = QdrantVectorStore(
        client=qdrant_client,
        collection_name=collection_name,
        embedding= embeddings_model
    )

    return vector_store

def embed_documents(document_data,collection_name):
    """
    Embed documents using the Qdrant vector store.
    Args:
        document_data (dict): Metadata of the ingested document
    Returns:
        None
    """       
    vector_store = initialize_vector_store(collection_name)
    vector_store.add_documents(document_data)   
    return True
