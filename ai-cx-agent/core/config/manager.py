"""
Configuration Manager
Centralized configuration management for all environments
Supports: Development, Staging, Production
"""

import os
from typing import Any, Optional, Dict
from pathlib import Path
from dotenv import load_dotenv


class ConfigManager:
    """Centralized configuration management"""
    
    def __init__(self, environment: Optional[str] = None):
        """
        Load configuration for environment
        
        Args:
            environment: dev/staging/production (auto-detected if not provided)
        """
        self.environment = environment or os.getenv('ENVIRONMENT', 'development')
        self._config_cache: Dict[str, Any] = {}
        self._load_config()
    
    def _load_config(self):
        """Load environment-specific config"""
        # Try to load from config directory
        config_file = Path(f"config/{self.environment}.env")
        
        if config_file.exists():
            load_dotenv(config_file)
            print(f"✅ Loaded config from: {config_file}")
        else:
            # Fallback to .env in root
            root_env = Path(".env")
            if root_env.exists():
                load_dotenv(root_env)
                print(f"✅ Loaded config from: {root_env}")
            else:
                print(f"⚠️  No config file found for {self.environment}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value
        
        Args:
            key: Configuration key
            default: Default value if key not found
        
        Returns:
            Configuration value
        """
        # Check cache first
        if key in self._config_cache:
            return self._config_cache[key]
        
        # Get from environment
        value = os.getenv(key, default)
        
        # Cache it
        self._config_cache[key] = value
        
        return value
    
    def get_bool(self, key: str, default: bool = False) -> bool:
        """
        Get boolean config value
        
        Args:
            key: Configuration key
            default: Default boolean value
        
        Returns:
            Boolean value
        """
        value = self.get(key, str(default))
        
        if isinstance(value, bool):
            return value
        
        return str(value).lower() in ('true', '1', 'yes', 'on')
    
    def get_int(self, key: str, default: int = 0) -> int:
        """
        Get integer config value
        
        Args:
            key: Configuration key
            default: Default integer value
        
        Returns:
            Integer value
        """
        value = self.get(key, default)
        
        try:
            return int(value)
        except (ValueError, TypeError):
            return default
    
    def get_float(self, key: str, default: float = 0.0) -> float:
        """
        Get float config value
        
        Args:
            key: Configuration key
            default: Default float value
        
        Returns:
            Float value
        """
        value = self.get(key, default)
        
        try:
            return float(value)
        except (ValueError, TypeError):
            return default
    
    def get_list(self, key: str, separator: str = ',', default: list = None) -> list:
        """
        Get list config value (comma-separated by default)
        
        Args:
            key: Configuration key
            separator: List separator
            default: Default list value
        
        Returns:
            List value
        """
        value = self.get(key)
        
        if value is None:
            return default or []
        
        if isinstance(value, list):
            return value
        
        return [item.strip() for item in str(value).split(separator) if item.strip()]
    
    def require(self, key: str) -> Any:
        """
        Get required configuration value (raises error if not found)
        
        Args:
            key: Configuration key
        
        Returns:
            Configuration value
        
        Raises:
            ValueError: If key not found
        """
        value = self.get(key)
        
        if value is None:
            raise ValueError(f"Required configuration '{key}' not found")
        
        return value
    
    @property
    def is_production(self) -> bool:
        """Check if running in production"""
        return self.environment == 'production'
    
    @property
    def is_staging(self) -> bool:
        """Check if running in staging"""
        return self.environment == 'staging'
    
    @property
    def is_development(self) -> bool:
        """Check if running in development"""
        return self.environment == 'development'
    
    def get_openai_config(self) -> Dict[str, Any]:
        """Get OpenAI configuration"""
        return {
            'api_key': self.require('OPENAI_API_KEY'),
            'model': self.get('OPENAI_MODEL', 'gpt-4o-mini'),
            'max_tokens': self.get_int('MAX_TOKENS', 500)
        }
    
    def get_database_config(self) -> Dict[str, Any]:
        """Get database configuration"""
        return {
            'url': self.get('DATABASE_URL', 'sqlite:///data/ai_agent.db')
        }
    
    def get_monitoring_config(self) -> Dict[str, Any]:
        """Get monitoring configuration"""
        return {
            'enable_metrics': self.get_bool('ENABLE_METRICS', True),
            'enable_analytics': self.get_bool('ENABLE_ANALYTICS', True),
            'sentry_dsn': self.get('SENTRY_DSN'),
            'posthog_api_key': self.get('POSTHOG_API_KEY')
        }
    
    def get_rate_limits(self) -> Dict[str, int]:
        """Get rate limiting configuration"""
        return {
            'max_requests_per_minute': self.get_int('MAX_REQUESTS_PER_MINUTE', 60),
            'max_conversations_per_hour': self.get_int('MAX_CONVERSATIONS_PER_HOUR', 100)
        }
    
    def get_all_config(self) -> Dict[str, Any]:
        """
        Get all configuration (for debugging)
        NOTE: Excludes sensitive keys
        """
        sensitive_keys = ['API_KEY', 'SECRET', 'PASSWORD', 'TOKEN', 'DSN']
        
        all_config = {}
        
        for key, value in os.environ.items():
            # Skip sensitive keys
            if any(sensitive in key.upper() for sensitive in sensitive_keys):
                all_config[key] = '***REDACTED***'
            else:
                all_config[key] = value
        
        return all_config
    
    def validate_config(self) -> Dict[str, Any]:
        """
        Validate configuration
        
        Returns:
            Validation results
        """
        errors = []
        warnings = []
        
        # Check required keys
        required_keys = ['OPENAI_API_KEY', 'ENVIRONMENT']
        
        for key in required_keys:
            if not self.get(key):
                errors.append(f"Missing required config: {key}")
        
        # Check OpenAI key format
        api_key = self.get('OPENAI_API_KEY', '')
        if api_key and not api_key.startswith('sk-'):
            warnings.append("OPENAI_API_KEY doesn't look valid (should start with 'sk-')")
        
        # Check log level
        log_level = self.get('LOG_LEVEL', 'INFO')
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if log_level not in valid_levels:
            warnings.append(f"Invalid LOG_LEVEL: {log_level} (should be one of {valid_levels})")
        
        # Check production settings
        if self.is_production:
            if self.get('LOG_LEVEL') == 'DEBUG':
                warnings.append("DEBUG logging enabled in production")
            
            if not self.get('SENTRY_DSN'):
                warnings.append("No SENTRY_DSN configured for production")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'environment': self.environment
        }
    
    def __repr__(self) -> str:
        return f"ConfigManager(environment={self.environment})"


# Global config instance
config = ConfigManager()

# LLM constants — single source of truth for model configuration
LLM_MODEL = "gpt-4o-mini"
LLM_TEMPERATURE_INTENT = 0.1
LLM_TEMPERATURE_RESPONSE = 0.7
LLM_MAX_TOKENS_INTENT = 300
LLM_MAX_TOKENS_RESPONSE = 500
