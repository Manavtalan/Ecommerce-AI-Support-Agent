"""
RAG Configuration
Settings for vector database, embeddings, and retrieval
"""

import os
from dotenv import load_dotenv

load_dotenv()

# Qdrant Configuration
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", 6333))
QDRANT_GRPC_PORT = int(os.getenv("QDRANT_GRPC_PORT", 6334))

# Embedding Configuration
EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSIONS = 1536  # text-embedding-3-small dimension

# Chunking Configuration
CHUNK_SIZE = 500  # tokens per chunk
CHUNK_OVERLAP = 50  # token overlap between chunks

# Retrieval Configuration
DEFAULT_TOP_K = 3  # number of chunks to retrieve
SIMILARITY_THRESHOLD_HIGH = 0.85  # high confidence
SIMILARITY_THRESHOLD_MEDIUM = 0.65  # medium confidence
SIMILARITY_THRESHOLD_LOW = 0.50  # low confidence (escalate)

# Collection Naming
def get_collection_name(brand_name: str) -> str:
    """Get Qdrant collection name for brand"""
    return f"{brand_name}_knowledge"

# Document Types
DOCUMENT_TYPES = {
    "policy": ["shipping", "return", "refund", "cancellation", "exchange"],
    "faq": ["general", "brand_specific"],
    "product": ["catalog", "specifications"]
}
