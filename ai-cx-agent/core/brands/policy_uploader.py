"""
Policy Uploader
Uploads and embeds brand policies into RAG system
"""

import os
from pathlib import Path
from typing import List, Dict
from core.brands.registry import get_brand_registry


class PolicyUploader:
    """Handles policy document uploading and embedding"""
    
    def __init__(self, brand_id: str):
        """
        Initialize policy uploader
        
        Args:
            brand_id: Brand identifier
        """
        registry = get_brand_registry()
        if not registry.validate_brand_id(brand_id):
            raise ValueError(f"Brand {brand_id} not found")
        
        self.brand_id = brand_id
        self.brand_config = registry.get_brand_by_id(brand_id)
        self.policies_dir = Path(f"test_data/brands/{brand_id}/policies")
    
    def get_policy_files(self) -> List[Path]:
        """
        Get all policy files for brand
        
        Returns:
            List of policy file paths
        """
        if not self.policies_dir.exists():
            return []
        
        # Get all .md files
        return list(self.policies_dir.glob("*.md"))
    
    def upload_policy(
        self,
        policy_type: str,
        file_path: str
    ) -> bool:
        """
        Upload a single policy file
        
        Args:
            policy_type: Type of policy (return, shipping, etc.)
            file_path: Path to policy file
        
        Returns:
            True if successful
        """
        source_path = Path(file_path)
        
        if not source_path.exists():
            raise FileNotFoundError(f"Policy file not found: {file_path}")
        
        # Ensure policies directory exists
        self.policies_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy to brand's policies directory
        dest_path = self.policies_dir / f"{policy_type}_policy.md"
        
        with open(source_path, 'r') as src:
            content = src.read()
        
        with open(dest_path, 'w') as dest:
            dest.write(content)
        
        print(f"✅ Uploaded {policy_type} policy to {dest_path}")
        
        return True
    
    def embed_policies(self) -> Dict:
        """
        Embed all policies into RAG system
        
        Returns:
            Dict with embedding results
        """
        policy_files = self.get_policy_files()
        
        if not policy_files:
            print(f"⚠️  No policy files found in {self.policies_dir}")
            return {"success": False, "reason": "No policy files"}
        
        print(f"📚 Found {len(policy_files)} policy files")
        
        try:
            # Try to use RAG system if available
            from core.rag.embedder import DocumentEmbedder
            from core.rag.chunker import DocumentChunker
            
            print("📄 Processing documents...")
            
            # Initialize components
            chunker = DocumentChunker()
            embedder = DocumentEmbedder()
            
            all_chunks = []
            
            # Process each policy file
            for policy_file in policy_files:
                print(f"  Processing: {policy_file.name}")
                
                # Read content
                with open(policy_file, 'r') as f:
                    content = f.read()
                
                # Chunk the document
                chunks = chunker.chunk_text(
                    text=content,
                    metadata={
                        "source": str(policy_file),
                        "brand_id": self.brand_id,
                        "policy_type": policy_file.stem.replace("_policy", "")
                    }
                )
                
                all_chunks.extend(chunks)
            
            print(f"✅ Created {len(all_chunks)} chunks")
            
            # Embed chunks
            print("🔮 Embedding chunks...")
            embedder.embed_documents(
                brand_id=self.brand_id,
                chunks=all_chunks
            )
            
            print(f"✅ Embedded {len(all_chunks)} chunks for {self.brand_id}")
            
            return {
                "success": True,
                "chunks": len(all_chunks),
                "files": len(policy_files)
            }
        
        except ImportError as e:
            print(f"⚠️  RAG system not fully available: {e}")
            print("   Policies uploaded but not embedded")
            return {
                "success": False,
                "reason": "RAG not available",
                "files_uploaded": len(policy_files)
            }
        
        except Exception as e:
            print(f"❌ Embedding failed: {e}")
            return {
                "success": False,
                "reason": str(e)
            }
    
    def create_brand_vector_index(self) -> str:
        """
        Create vector index for brand
        
        Returns:
            Collection name
        """
        collection_name = f"{self.brand_id}_knowledge"
        
        # This is handled by the embedder
        # Just return the collection name
        
        return collection_name
    
    def validate_policy_coverage(self) -> Dict[str, bool]:
        """
        Validate that all required policies are present
        
        Returns:
            Dict of policy_type -> exists
        """
        required_policies = [
            "return",
            "shipping",
            "refund",
            "cancellation",
            "exchange"
        ]
        
        coverage = {}
        
        for policy_type in required_policies:
            policy_file = self.policies_dir / f"{policy_type}_policy.md"
            coverage[policy_type] = policy_file.exists()
        
        return coverage
    
    def get_upload_status(self) -> Dict:
        """Get upload and embedding status"""
        policy_files = self.get_policy_files()
        coverage = self.validate_policy_coverage()
        
        return {
            "brand_id": self.brand_id,
            "policies_uploaded": len(policy_files),
            "policy_coverage": coverage,
            "all_required_present": all(coverage.values()),
            "ready_for_embedding": len(policy_files) > 0
        }


# Convenience functions
def upload_brand_policies(brand_id: str, policies_dir: str) -> bool:
    """
    Upload all policies from a directory
    
    Args:
        brand_id: Brand identifier
        policies_dir: Directory containing policy files
    
    Returns:
        True if successful
    """
    uploader = PolicyUploader(brand_id)
    
    source_dir = Path(policies_dir)
    if not source_dir.exists():
        raise FileNotFoundError(f"Policies directory not found: {policies_dir}")
    
    # Upload each .md file
    for policy_file in source_dir.glob("*.md"):
        policy_type = policy_file.stem.replace("_policy", "")
        uploader.upload_policy(policy_type, str(policy_file))
    
    return True


def embed_brand_policies(brand_id: str) -> Dict:
    """
    Embed all policies for a brand
    
    Args:
        brand_id: Brand identifier
    
    Returns:
        Embedding result
    """
    uploader = PolicyUploader(brand_id)
    return uploader.embed_policies()
