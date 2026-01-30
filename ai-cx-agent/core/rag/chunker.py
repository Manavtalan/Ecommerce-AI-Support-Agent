"""
Document Chunker
Splits documents into chunks with overlap for better retrieval
"""

import tiktoken
from typing import List, Dict
from pathlib import Path


class DocumentChunker:
    """Chunks documents intelligently for embedding"""
    
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        """
        Initialize chunker
        
        Args:
            chunk_size: Target tokens per chunk
            chunk_overlap: Overlapping tokens between chunks
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.encoding = tiktoken.get_encoding("cl100k_base")
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text"""
        return len(self.encoding.encode(text))
    
    def chunk_text(self, text: str, metadata: Dict = None) -> List[Dict]:
        """
        Chunk text into overlapping segments
        
        Args:
            text: Text to chunk
            metadata: Optional metadata to attach to each chunk
        
        Returns:
            List of chunks with metadata
        """
        # Tokenize
        tokens = self.encoding.encode(text)
        
        chunks = []
        start = 0
        
        while start < len(tokens):
            # Get chunk
            end = start + self.chunk_size
            chunk_tokens = tokens[start:end]
            
            # Decode back to text
            chunk_text = self.encoding.decode(chunk_tokens)
            
            # Create chunk object
            chunk = {
                "text": chunk_text.strip(),
                "token_count": len(chunk_tokens),
                "chunk_index": len(chunks),
                "start_token": start,
                "end_token": end,
                "metadata": metadata or {}
            }
            
            chunks.append(chunk)
            
            # Move to next chunk with overlap
            start += self.chunk_size - self.chunk_overlap
        
        return chunks
    
    def chunk_markdown_file(self, file_path: Path, brand_name: str) -> List[Dict]:
        """
        Chunk a markdown file (policy document)
        
        Args:
            file_path: Path to markdown file
            brand_name: Brand name for metadata
        
        Returns:
            List of chunks with metadata
        """
        # Read file
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract metadata
        metadata = {
            "source": file_path.name,
            "brand": brand_name,
            "type": "policy",
            "category": file_path.stem.replace("_policy", "")
        }
        
        # Chunk
        chunks = self.chunk_text(content, metadata)
        
        return chunks
    
    def chunk_all_policies(self, brand_name: str) -> List[Dict]:
        """
        Chunk all policy documents for a brand
        
        Args:
            brand_name: Brand name (e.g., 'fashionhub')
        
        Returns:
            All chunks from all policy documents
        """
        policy_dir = Path(f"test_data/policies/{brand_name}")
        
        if not policy_dir.exists():
            raise ValueError(f"Policy directory not found: {policy_dir}")
        
        all_chunks = []
        
        # Get all markdown files
        policy_files = list(policy_dir.glob("*.md"))
        
        print(f"📄 Found {len(policy_files)} policy documents")
        
        for policy_file in policy_files:
            print(f"   Processing: {policy_file.name}")
            chunks = self.chunk_markdown_file(policy_file, brand_name)
            all_chunks.extend(chunks)
            print(f"      → {len(chunks)} chunks created")
        
        print(f"✅ Total chunks: {len(all_chunks)}")
        
        return all_chunks


# Helper function
def chunk_documents(brand_name: str, chunk_size: int = 500, chunk_overlap: int = 50) -> List[Dict]:
    """
    Convenience function to chunk all documents for a brand
    
    Args:
        brand_name: Brand name
        chunk_size: Tokens per chunk
        chunk_overlap: Overlapping tokens
    
    Returns:
        All document chunks
    """
    chunker = DocumentChunker(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    return chunker.chunk_all_policies(brand_name)
