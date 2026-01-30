"""
Brand Registry
Central registry for all brand configurations
"""

import os
import yaml
from typing import Dict, List, Optional
from pathlib import Path


class BrandRegistry:
    """Manages all brand configurations"""
    
    def __init__(self, brands_dir: str = "test_data/brands"):
        """
        Initialize brand registry
        
        Args:
            brands_dir: Directory containing brand configurations
        """
        self.brands_dir = Path(brands_dir)
        self.brands: Dict[str, Dict] = {}
        self._load_all_brands()
    
    def _load_all_brands(self):
        """Load all brand configurations from directory"""
        if not self.brands_dir.exists():
            print(f"⚠️  Brands directory not found: {self.brands_dir}")
            return
        
        # Scan for brand directories
        for brand_dir in self.brands_dir.iterdir():
            if brand_dir.is_dir():
                config_file = brand_dir / "brand_config.yaml"
                
                if config_file.exists():
                    try:
                        brand_config = self._load_config(config_file)
                        brand_id = brand_config.get("brand_id", brand_dir.name)
                        self.brands[brand_id] = brand_config
                        print(f"✅ Loaded brand: {brand_id}")
                    except Exception as e:
                        print(f"❌ Failed to load {brand_dir.name}: {e}")
    
    def _load_config(self, config_file: Path) -> Dict:
        """Load brand configuration from YAML file"""
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
        
        # Set defaults
        config.setdefault("brand_id", config_file.parent.name)
        config.setdefault("name", config_file.parent.name.title())
        config.setdefault("industry", "general")
        config.setdefault("active", True)
        
        return config
    
    def get_brand_by_id(self, brand_id: str) -> Optional[Dict]:
        """
        Get brand configuration by ID
        
        Args:
            brand_id: Brand identifier
        
        Returns:
            Brand configuration dict or None
        """
        return self.brands.get(brand_id)
    
    def get_brand_by_domain(self, domain: str) -> Optional[Dict]:
        """
        Get brand by domain name
        
        Args:
            domain: Domain to search for
        
        Returns:
            Brand configuration or None
        """
        for brand_id, config in self.brands.items():
            brand_domain = config.get("domain", "")
            if brand_domain == domain:
                return config
        
        return None
    
    def list_brands(self) -> List[str]:
        """
        List all registered brand IDs
        
        Returns:
            List of brand IDs
        """
        return list(self.brands.keys())
    
    def list_active_brands(self) -> List[str]:
        """
        List only active brand IDs
        
        Returns:
            List of active brand IDs
        """
        return [
            brand_id for brand_id, config in self.brands.items()
            if config.get("active", True)
        ]
    
    def register_brand(self, config: Dict) -> bool:
        """
        Register a new brand
        
        Args:
            config: Brand configuration dict
        
        Returns:
            True if successful
        """
        brand_id = config.get("brand_id")
        
        if not brand_id:
            raise ValueError("brand_id is required")
        
        if brand_id in self.brands:
            raise ValueError(f"Brand {brand_id} already exists")
        
        self.brands[brand_id] = config
        
        # Save to file
        brand_dir = self.brands_dir / brand_id
        brand_dir.mkdir(parents=True, exist_ok=True)
        
        config_file = brand_dir / "brand_config.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)
        
        print(f"✅ Registered brand: {brand_id}")
        return True
    
    def get_brand_count(self) -> int:
        """Get total number of registered brands"""
        return len(self.brands)
    
    def validate_brand_id(self, brand_id: str) -> bool:
        """Check if brand ID exists"""
        return brand_id in self.brands
    
    def __repr__(self) -> str:
        return f"BrandRegistry(brands={len(self.brands)})"


# Singleton instance
_registry = None

def get_brand_registry() -> BrandRegistry:
    """Get global brand registry instance"""
    global _registry
    if _registry is None:
        _registry = BrandRegistry()
    return _registry
