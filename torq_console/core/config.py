"""
TORQ CONSOLE Configuration Management.

Handles configuration loading, validation, and management for TORQ CONSOLE.
Enhanced with .env file support and API key management.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging
from dataclasses import dataclass, asdict
from datetime import datetime

# Load environment variables from .env file
def load_env_file(env_path: Optional[Path] = None) -> None:
    """Load environment variables from .env file."""
    if env_path is None:
        env_path = Path(__file__).parent.parent.parent / ".env"

    if env_path.exists():
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    # Only set if not already in environment
                    if key not in os.environ:
                        os.environ[key] = value

# Load .env file on import
load_env_file()


@dataclass
class MCPServerConfig:
    """Configuration for an MCP server."""
    endpoint: str
    name: str
    enabled: bool = True
    auth_token: Optional[str] = None
    timeout: int = 30
    retry_count: int = 3


@dataclass
class AIModelConfig:
    """Configuration for AI models."""
    provider: str  # "openai", "anthropic", "ollama"
    model: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 4096


@dataclass
class VoiceConfig:
    """Configuration for voice features."""
    enabled: bool = False
    input_device: Optional[str] = None
    output_device: Optional[str] = None
    wake_word: str = "hey torq"
    language: str = "en-US"
    voice_model: str = "whisper-1"


@dataclass
class UIConfig:
    """Configuration for UI preferences."""
    theme: str = "dark"
    font_size: int = 14
    font_family: str = "Monaco"
    show_line_numbers: bool = True
    auto_save: bool = True
    auto_save_interval: int = 30  # seconds


@dataclass
class GitConfig:
    """Configuration for Git integration."""
    auto_commit: bool = False
    commit_message_template: str = "TORQ: {message}"
    diff_tool: str = "auto"
    merge_tool: str = "auto"


@dataclass
class TBSConfig:
    """Configuration for TBS (TORQ Business Solutions) specific settings."""
    fallback_mode: bool = False
    demo_data_source: str = "disabled"
    web_search_proxy: bool = True
    proxy_timeout: int = 30
    max_search_results: int = 10
    realtime_data: bool = True
    cache_enabled: bool = True
    cache_duration: int = 300
    retry_attempts: int = 3
    request_timeout: int = 30


class TorqConfig:
    """
    Main configuration class for TORQ CONSOLE.

    Manages all configuration aspects including MCP servers, AI models,
    voice settings, UI preferences, Git integration, and TBS settings.
    """

    def __init__(self):
        self.config_dir = self.get_config_directory()
        self.config_file = self.config_dir / "config.json"

        # Configuration sections
        self.mcp_servers: List[MCPServerConfig] = []
        self.ai_models: List[AIModelConfig] = []
        self.voice: VoiceConfig = VoiceConfig()
        self.ui: UIConfig = UIConfig()
        self.git: GitConfig = GitConfig()
        self.tbs: TBSConfig = TBSConfig()

        # API Keys from environment
        self.api_keys = self._load_api_keys()

        # General settings
        self.version: str = "0.70.0"
        self.debug: bool = self._get_env_bool("DEBUG_MODE", False)
        self.log_level: str = os.getenv("LOG_LEVEL", "INFO")
        self.environment: str = os.getenv("ENVIRONMENT", "development")
        self.auto_update: bool = True

        # Runtime settings
        self.current_model: Optional[str] = None
        self.session_timeout: int = 3600  # seconds
        self.max_file_size: int = 10 * 1024 * 1024  # 10MB

        self.logger = logging.getLogger(__name__)

    def _load_api_keys(self) -> Dict[str, Optional[str]]:
        """Load API keys from environment variables."""
        api_keys = {
            # Financial Data APIs
            'alpha_vantage': os.getenv('ALPHA_VANTAGE_API_KEY'),
            'fred': os.getenv('FRED_API_KEY'),

            # News APIs
            'news_api': os.getenv('NEWS_API_KEY'),

            # Search APIs
            'google_search': os.getenv('GOOGLE_SEARCH_API_KEY'),
            'brave_search': os.getenv('BRAVE_SEARCH_API_KEY'),

            # AI/LLM APIs
            'openai': os.getenv('OPENAI_API_KEY'),
            'anthropic': os.getenv('ANTHROPIC_API_KEY'),
            'deepseek': os.getenv('DEEPSEEK_API_KEY'),
        }

        # Check for demo values and warn
        demo_keys = []
        for key, value in api_keys.items():
            if value and value.lower() in ['demo', 'your_api_key_here', 'your_' + key.upper() + '_api_key_here']:
                demo_keys.append(key)

        if demo_keys:
            self.logger.warning(f"Demo API keys detected for: {', '.join(demo_keys)}. Please replace with real API keys for full functionality.")

        return api_keys

    def _get_env_bool(self, key: str, default: bool = False) -> bool:
        """Get boolean value from environment variable."""
        value = os.getenv(key, str(default)).lower()
        return value in ('true', '1', 'yes', 'on', 'enabled')

    def _load_tbs_config(self) -> TBSConfig:
        """Load TBS-specific configuration from environment."""
        return TBSConfig(
            fallback_mode=self._get_env_bool('TBS_FALLBACK_MODE', False),
            demo_data_source=os.getenv('TBS_DEMO_DATA_SOURCE', 'disabled'),
            web_search_proxy=self._get_env_bool('TBS_WEB_SEARCH_PROXY', True),
            proxy_timeout=int(os.getenv('TBS_PROXY_TIMEOUT', '30')),
            max_search_results=int(os.getenv('TBS_MAX_SEARCH_RESULTS', '10')),
            realtime_data=self._get_env_bool('TBS_REALTIME_DATA', True),
            cache_enabled=self._get_env_bool('TBS_CACHE_ENABLED', True),
            cache_duration=int(os.getenv('TBS_CACHE_DURATION', '300')),
            retry_attempts=int(os.getenv('TBS_RETRY_ATTEMPTS', '3')),
            request_timeout=int(os.getenv('TBS_REQUEST_TIMEOUT', '30'))
        )

    @classmethod
    def get_config_directory(cls) -> Path:
        """Get the configuration directory path."""
        if os.name == 'nt':  # Windows
            config_dir = Path.home() / "AppData" / "Local" / "TORQ-CONSOLE"
        else:  # Unix-like systems
            config_dir = Path.home() / ".config" / "torq-console"

        config_dir.mkdir(parents=True, exist_ok=True)
        return config_dir

    @classmethod
    def get_default_path(cls) -> Path:
        """Get the default configuration file path."""
        return cls.get_config_directory() / "config.json"

    @classmethod
    def load(cls, config_path: Optional[Path] = None) -> 'TorqConfig':
        """Load configuration from file."""
        instance = cls()

        if config_path is None:
            config_path = instance.config_file

        if config_path.exists():
            try:
                instance._load_from_file(config_path)
                instance.logger.info(f"Configuration loaded from {config_path}")
            except Exception as e:
                instance.logger.error(f"Failed to load config from {config_path}: {e}")
                instance.logger.info("Using default configuration")
        else:
            instance.logger.info("Configuration file not found, using defaults")
            instance._set_defaults()

        # Always load TBS config from environment
        instance.tbs = instance._load_tbs_config()

        return instance

    @classmethod
    def create_default(cls) -> 'TorqConfig':
        """Create a default configuration."""
        instance = cls()
        instance._set_defaults()
        instance.tbs = instance._load_tbs_config()
        return instance

    def _load_from_file(self, config_path: Path):
        """Load configuration from JSON file."""
        with open(config_path, 'r') as f:
            data = json.load(f)

        # Load MCP servers
        if 'mcp_servers' in data:
            self.mcp_servers = [
                MCPServerConfig(**server) for server in data['mcp_servers']
            ]

        # Load AI models
        if 'ai_models' in data:
            self.ai_models = [
                AIModelConfig(**model) for model in data['ai_models']
            ]

        # Load voice config
        if 'voice' in data:
            self.voice = VoiceConfig(**data['voice'])

        # Load UI config
        if 'ui' in data:
            self.ui = UIConfig(**data['ui'])

        # Load Git config
        if 'git' in data:
            self.git = GitConfig(**data['git'])

        # Load TBS config (if present in file, but environment takes precedence)
        if 'tbs' in data:
            file_tbs = TBSConfig(**data['tbs'])
            # Merge with environment settings (env takes precedence)
            self.tbs = self._load_tbs_config()

        # Load general settings
        self.version = data.get('version', self.version)
        self.auto_update = data.get('auto_update', self.auto_update)
        self.current_model = data.get('current_model', self.current_model)
        self.session_timeout = data.get('session_timeout', self.session_timeout)
        self.max_file_size = data.get('max_file_size', self.max_file_size)

    def _set_defaults(self):
        """Set default configuration values."""
        # Default MCP servers (integrate with existing King Flowers infrastructure)
        self.mcp_servers = [
            MCPServerConfig(
                endpoint="http://localhost:3100",
                name="Hybrid MCP Server",
                enabled=self._get_env_bool('MCP_SERVER_ENABLED', True)
            ),
            MCPServerConfig(
                endpoint="http://localhost:3101",
                name="N8N Proxy Server",
                enabled=True
            ),
            MCPServerConfig(
                endpoint="stdio://claude-memory-mcp",
                name="Claude Memory",
                enabled=True
            )
        ]

        # Default AI models with API keys from environment
        self.ai_models = [
            AIModelConfig(
                provider="anthropic",
                model="claude-3-5-sonnet-20241022",
                api_key=self.api_keys.get('anthropic')
            ),
            AIModelConfig(
                provider="openai",
                model="gpt-4",
                api_key=self.api_keys.get('openai')
            ),
            AIModelConfig(
                provider="ollama",
                model="codellama:7b",
                base_url="http://localhost:11434"
            )
        ]

        # Set current model
        if self.ai_models:
            self.current_model = f"{self.ai_models[0].provider}:{self.ai_models[0].model}"

    def save(self, config_path: Optional[Path] = None):
        """Save configuration to file."""
        if config_path is None:
            config_path = self.config_file

        try:
            # Ensure directory exists
            config_path.parent.mkdir(parents=True, exist_ok=True)

            # Prepare data for serialization
            data = {
                'version': self.version,
                'debug': self.debug,
                'log_level': self.log_level,
                'environment': self.environment,
                'auto_update': self.auto_update,
                'current_model': self.current_model,
                'session_timeout': self.session_timeout,
                'max_file_size': self.max_file_size,
                'mcp_servers': [asdict(server) for server in self.mcp_servers],
                'ai_models': [asdict(model) for model in self.ai_models],
                'voice': asdict(self.voice),
                'ui': asdict(self.ui),
                'git': asdict(self.git),
                'tbs': asdict(self.tbs),
                'last_updated': datetime.now().isoformat()
            }

            with open(config_path, 'w') as f:
                json.dump(data, f, indent=2)

            self.logger.info(f"Configuration saved to {config_path}")

        except Exception as e:
            self.logger.error(f"Failed to save config to {config_path}: {e}")
            raise

    def is_demo_mode(self) -> bool:
        """Check if system is running in demo mode."""
        return self.tbs.fallback_mode or self.tbs.demo_data_source != 'disabled'

    def has_valid_api_key(self, service: str) -> bool:
        """Check if a service has a valid (non-demo) API key."""
        key = self.api_keys.get(service)
        if not key:
            return False

        # Check for demo/placeholder values
        demo_values = ['demo', 'your_api_key_here', f'your_{service.upper()}_api_key_here']
        return key.lower() not in [v.lower() for v in demo_values]

    def get_service_mode(self, service: str) -> str:
        """
        Get the operational mode for a service.

        Returns:
            'api' - Service has valid API key
            'proxy' - Service will use web search proxy
            'demo' - Service is in demo/fallback mode
            'disabled' - Service is not available
        """
        if self.is_demo_mode():
            return 'demo'

        if self.has_valid_api_key(service):
            return 'api'

        if self.tbs.web_search_proxy and service in ['alpha_vantage', 'fred', 'news_api']:
            return 'proxy'

        return 'disabled'

    def add_mcp_server(self, endpoint: str, name: Optional[str] = None) -> bool:
        """Add a new MCP server to the configuration."""
        try:
            # Check if server already exists
            for server in self.mcp_servers:
                if server.endpoint == endpoint:
                    self.logger.warning(f"MCP server {endpoint} already exists")
                    return False

            # Create new server config
            server_config = MCPServerConfig(
                endpoint=endpoint,
                name=name or f"MCP Server {len(self.mcp_servers) + 1}"
            )

            self.mcp_servers.append(server_config)
            self.logger.info(f"Added MCP server: {endpoint}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to add MCP server {endpoint}: {e}")
            return False

    def remove_mcp_server(self, endpoint: str) -> bool:
        """Remove an MCP server from the configuration."""
        try:
            original_count = len(self.mcp_servers)
            self.mcp_servers = [
                server for server in self.mcp_servers
                if server.endpoint != endpoint
            ]

            if len(self.mcp_servers) < original_count:
                self.logger.info(f"Removed MCP server: {endpoint}")
                return True
            else:
                self.logger.warning(f"MCP server {endpoint} not found")
                return False

        except Exception as e:
            self.logger.error(f"Failed to remove MCP server {endpoint}: {e}")
            return False

    def get_mcp_server(self, endpoint: str) -> Optional[MCPServerConfig]:
        """Get MCP server configuration by endpoint."""
        for server in self.mcp_servers:
            if server.endpoint == endpoint:
                return server
        return None

    def add_ai_model(self, provider: str, model: str, **kwargs) -> bool:
        """Add a new AI model to the configuration."""
        try:
            # Check if model already exists
            for existing_model in self.ai_models:
                if existing_model.provider == provider and existing_model.model == model:
                    self.logger.warning(f"AI model {provider}:{model} already exists")
                    return False

            # Create new model config
            model_config = AIModelConfig(
                provider=provider,
                model=model,
                **kwargs
            )

            self.ai_models.append(model_config)
            self.logger.info(f"Added AI model: {provider}:{model}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to add AI model {provider}:{model}: {e}")
            return False

    def get_current_ai_model(self) -> Optional[AIModelConfig]:
        """Get the currently configured AI model."""
        if not self.current_model:
            return None

        try:
            provider, model = self.current_model.split(':', 1)
            for ai_model in self.ai_models:
                if ai_model.provider == provider and ai_model.model == model:
                    return ai_model
        except ValueError:
            pass

        return None

    def set_current_model(self, provider: str, model: str) -> bool:
        """Set the current AI model."""
        for ai_model in self.ai_models:
            if ai_model.provider == provider and ai_model.model == model:
                self.current_model = f"{provider}:{model}"
                self.logger.info(f"Set current model to {self.current_model}")
                return True

        self.logger.error(f"AI model {provider}:{model} not found")
        return False

    def validate(self) -> List[str]:
        """Validate the configuration and return any errors."""
        errors = []

        # Validate MCP servers
        for i, server in enumerate(self.mcp_servers):
            if not server.endpoint:
                errors.append(f"MCP server {i}: endpoint is required")

        # Validate AI models
        for i, model in enumerate(self.ai_models):
            if not model.provider:
                errors.append(f"AI model {i}: provider is required")
            if not model.model:
                errors.append(f"AI model {i}: model is required")

            # Check for API keys where required
            if model.provider in ["openai", "anthropic"] and not self.has_valid_api_key(model.provider):
                errors.append(f"AI model {i}: Valid API key required for {model.provider}")

        # Validate current model
        if self.current_model:
            current_model = self.get_current_ai_model()
            if not current_model:
                errors.append(f"Current model '{self.current_model}' not found in configured models")

        # Validate TBS configuration
        if self.is_demo_mode():
            errors.append("TBS is running in demo mode. Set TBS_FALLBACK_MODE=disabled and TBS_DEMO_DATA_SOURCE=disabled for full functionality")

        return errors

    def get_configuration_report(self) -> str:
        """Generate a comprehensive configuration report."""
        report = []
        report.append("TORQ CONSOLE Configuration Report")
        report.append("=" * 50)
        report.append(f"Version: {self.version}")
        report.append(f"Environment: {self.environment}")
        report.append(f"Debug Mode: {self.debug}")
        report.append(f"Log Level: {self.log_level}")
        report.append("")

        # TBS Configuration
        report.append("TBS Configuration:")
        report.append(f"  Demo Mode: {'ENABLED' if self.is_demo_mode() else 'DISABLED'}")
        report.append(f"  Fallback Mode: {self.tbs.fallback_mode}")
        report.append(f"  Demo Data Source: {self.tbs.demo_data_source}")
        report.append(f"  Web Search Proxy: {self.tbs.web_search_proxy}")
        report.append(f"  Real-time Data: {self.tbs.realtime_data}")
        report.append("")

        # API Keys Status
        report.append("API Keys Status:")
        for service, key in self.api_keys.items():
            status = self.get_service_mode(service)
            report.append(f"  {service.title()}: {status.upper()}")
        report.append("")

        # Service Modes
        report.append("Service Operational Modes:")
        services = ['alpha_vantage', 'fred', 'news_api', 'openai', 'anthropic']
        for service in services:
            mode = self.get_service_mode(service)
            report.append(f"  {service.replace('_', ' ').title()}: {mode.upper()}")
        report.append("")

        # Validation errors
        errors = self.validate()
        if errors:
            report.append("Configuration Issues:")
            for error in errors:
                report.append(f"  - {error}")
        else:
            report.append("Configuration Status: VALID")

        return "\n".join(report)

    def get_effective_config(self) -> Dict[str, Any]:
        """Get the effective configuration with environment variable overrides."""
        config = {
            'version': self.version,
            'debug': self.debug,
            'log_level': self.log_level,
            'environment': self.environment,
            'auto_update': self.auto_update,
            'current_model': self.current_model,
            'session_timeout': self.session_timeout,
            'max_file_size': self.max_file_size,
            'mcp_servers': [asdict(server) for server in self.mcp_servers],
            'ai_models': [asdict(model) for model in self.ai_models],
            'voice': asdict(self.voice),
            'ui': asdict(self.ui),
            'git': asdict(self.git),
            'tbs': asdict(self.tbs),
            'api_keys': self.api_keys,
            'demo_mode': self.is_demo_mode()
        }

        return config

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by key (dict-like interface for compatibility).

        This method provides dictionary-like access to configuration values
        to maintain compatibility with existing code that expects a dict-like config.

        Args:
            key: Configuration key to retrieve
            default: Default value if key is not found

        Returns:
            Configuration value or default
        """
        try:
            # Handle nested keys with dot notation (e.g., 'tbs.fallback_mode')
            if '.' in key:
                parts = key.split('.')
                value = self
                for part in parts:
                    if hasattr(value, part):
                        value = getattr(value, part)
                    else:
                        return default
                return value

            # Handle direct attribute access
            if hasattr(self, key):
                return getattr(self, key)

            # Handle special keys that map to existing attributes
            key_mapping = {
                'show_agent_performance': lambda: self.debug,
                'enhanced_mode': lambda: not self.is_demo_mode(),
                'web_search_proxy': lambda: self.tbs.web_search_proxy,
                'proxy_timeout': lambda: self.tbs.proxy_timeout,
                'max_search_results': lambda: self.tbs.max_search_results,
                'realtime_data': lambda: self.tbs.realtime_data,
                'cache_enabled': lambda: self.tbs.cache_enabled,
                'cache_duration': lambda: self.tbs.cache_duration,
                'retry_attempts': lambda: self.tbs.retry_attempts,
                'request_timeout': lambda: self.tbs.request_timeout
            }

            if key in key_mapping:
                return key_mapping[key]()

            # Handle API keys
            if key.endswith('_api_key') or key in ['openai_api_key', 'anthropic_api_key', 'deepseek_api_key']:
                # Check environment first (most current)
                env_key = key.upper()
                env_value = os.getenv(env_key)
                if env_value:
                    return env_value

                # Check stored API keys
                clean_key = key.replace('_api_key', '').replace('_', '')
                return self.api_keys.get(clean_key, default)

            # Fallback to default
            return default

        except Exception as e:
            self.logger.warning(f"Error accessing config key '{key}': {e}")
            return default

    def __str__(self) -> str:
        """String representation of the configuration."""
        mode = "DEMO" if self.is_demo_mode() else "PRODUCTION"
        return f"TorqConfig(version={self.version}, mode={mode}, mcp_servers={len(self.mcp_servers)}, ai_models={len(self.ai_models)})"