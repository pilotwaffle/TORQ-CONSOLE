"""
Configuration management for TORQ CONSOLE.
"""

import json
import os
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from pydantic import BaseModel, Field


class MCPEndpoint(BaseModel):
    """MCP endpoint configuration."""
    name: str
    url: str
    auth_type: str = "bearer"
    token: Optional[str] = None
    enabled: bool = True


class AIModelConfig(BaseModel):
    """AI model configuration."""
    provider: str = "openai"  # openai, anthropic, ollama
    model: str = "gpt-4o"
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 4096


class VoiceConfig(BaseModel):
    """Voice configuration."""
    enabled: bool = False
    engine: str = "whisper"  # whisper, google
    tts_engine: str = "pyttsx3"  # pyttsx3, elevenlabs
    language: str = "en-US"
    voice_rate: int = 200


class UIConfig(BaseModel):
    """UI configuration."""
    theme: str = "dark"
    enable_syntax_highlighting: bool = True
    enable_git_delta: bool = True
    enable_web_ui: bool = False
    web_ui_port: int = 8080


@dataclass
class TorqConfig:
    """Main TORQ CONSOLE configuration."""
    
    # Core settings
    project_root: Path = field(default_factory=lambda: Path.cwd())
    cache_dir: Path = field(default_factory=lambda: Path.home() / ".torq_cache")
    log_level: str = "INFO"
    telemetry_enabled: bool = False  # Privacy-first
    
    # AI Models
    ai_models: List[AIModelConfig] = field(default_factory=list)
    default_model: str = "gpt-4o"
    
    # MCP endpoints
    mcp_endpoints: List[MCPEndpoint] = field(default_factory=list)
    
    # Voice settings
    voice: VoiceConfig = field(default_factory=VoiceConfig)
    
    # UI settings
    ui: UIConfig = field(default_factory=UIConfig)
    
    # Repository settings
    watched_repos: List[str] = field(default_factory=list)
    auto_commit: bool = False
    auto_push: bool = False
    
    # Plugin settings
    plugins_dir: Path = field(default_factory=lambda: Path.home() / ".torq_plugins")
    enabled_plugins: List[str] = field(default_factory=list)

    @classmethod
    def load(cls, config_path: Optional[Path] = None) -> "TorqConfig":
        """Load configuration from file or create default."""
        if config_path is None:
            config_path = Path.home() / ".torq_config.json"
        
        if config_path.exists():
            with open(config_path, "r") as f:
                data = json.load(f)
            return cls.from_dict(data)
        else:
            # Create default config
            config = cls()
            config._add_default_endpoints()
            config._add_default_models()
            config.save(config_path)
            return config
    
    def save(self, config_path: Optional[Path] = None) -> None:
        """Save configuration to file."""
        if config_path is None:
            config_path = Path.home() / ".torq_config.json"
        
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, "w") as f:
            json.dump(self.to_dict(), f, indent=2, default=str)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "project_root": str(self.project_root),
            "cache_dir": str(self.cache_dir),
            "log_level": self.log_level,
            "telemetry_enabled": self.telemetry_enabled,
            "ai_models": [model.model_dump() for model in self.ai_models],
            "default_model": self.default_model,
            "mcp_endpoints": [endpoint.model_dump() for endpoint in self.mcp_endpoints],
            "voice": self.voice.model_dump(),
            "ui": self.ui.model_dump(),
            "watched_repos": self.watched_repos,
            "auto_commit": self.auto_commit,
            "auto_push": self.auto_push,
            "plugins_dir": str(self.plugins_dir),
            "enabled_plugins": self.enabled_plugins,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TorqConfig":
        """Create from dictionary."""
        config = cls()
        
        if "project_root" in data:
            config.project_root = Path(data["project_root"])
        if "cache_dir" in data:
            config.cache_dir = Path(data["cache_dir"])
        if "log_level" in data:
            config.log_level = data["log_level"]
        if "telemetry_enabled" in data:
            config.telemetry_enabled = data["telemetry_enabled"]
        if "default_model" in data:
            config.default_model = data["default_model"]
        if "watched_repos" in data:
            config.watched_repos = data["watched_repos"]
        if "auto_commit" in data:
            config.auto_commit = data["auto_commit"]
        if "auto_push" in data:
            config.auto_push = data["auto_push"]
        if "plugins_dir" in data:
            config.plugins_dir = Path(data["plugins_dir"])
        if "enabled_plugins" in data:
            config.enabled_plugins = data["enabled_plugins"]
        
        # Load complex objects
        if "ai_models" in data:
            config.ai_models = [AIModelConfig(**model) for model in data["ai_models"]]
        if "mcp_endpoints" in data:
            config.mcp_endpoints = [MCPEndpoint(**endpoint) for endpoint in data["mcp_endpoints"]]
        if "voice" in data:
            config.voice = VoiceConfig(**data["voice"])
        if "ui" in data:
            config.ui = UIConfig(**data["ui"])
        
        return config
    
    def _add_default_endpoints(self) -> None:
        """Add default MCP endpoints."""
        self.mcp_endpoints = [
            MCPEndpoint(
                name="github",
                url="mcp://github",
                auth_type="token",
                enabled=True
            ),
            MCPEndpoint(
                name="postgres",
                url="mcp://postgres",
                auth_type="connection_string",
                enabled=False
            ),
            MCPEndpoint(
                name="jenkins",
                url="mcp://jenkins",
                auth_type="api_key",
                enabled=False
            ),
        ]
    
    def _add_default_models(self) -> None:
        """Add default AI models."""
        self.ai_models = [
            AIModelConfig(
                provider="openai",
                model="gpt-4o",
                api_key=os.getenv("OPENAI_API_KEY"),
            ),
            AIModelConfig(
                provider="anthropic",
                model="claude-3-5-sonnet-20241022",
                api_key=os.getenv("ANTHROPIC_API_KEY"),
            ),
            AIModelConfig(
                provider="ollama",
                model="codellama:latest",
                base_url="http://localhost:11434",
            ),
        ]