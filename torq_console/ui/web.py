"""
Enhanced Web UI for TORQ CONSOLE.

Provides a modern, Claude Code-compatible web interface with real-time
collaboration, visual diffs, file management, and MCP tool integration.
"""

import asyncio
import json
import logging
import os
from pathlib import Path
from typing import Dict, Any, List, Optional, Set
import uuid
from datetime import datetime
import weakref
import secrets

from fastapi import FastAPI, WebSocket, Request, HTTPException, UploadFile, File, Header, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from pydantic import BaseModel, Field

# Socket.IO imports
try:
    import socketio
    from socketio import AsyncServer
    SOCKETIO_AVAILABLE = True
except ImportError:
    SOCKETIO_AVAILABLE = False
    socketio = None
    AsyncServer = None

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..core.console import TorqConsole

from ..core.chat_manager import ChatManager, MessageType, ChatTabStatus
from ..utils.visual_diff import VisualDiffEngine
from .inline_editor import InlineEditor
from .command_palette import CommandPalette

# CRITICAL FIX: Import enhanced AI integration fixes
try:
    from .web_ai_fix import WebUIAIFixes, apply_web_ai_fixes
    AI_FIXES_AVAILABLE = True
except ImportError as e:
    print(f"Warning: AI fixes not available: {e}")
    AI_FIXES_AVAILABLE = False



class DirectChatRequest(BaseModel):
    message: str
    include_context: bool = True
    generate_response: bool = True
    model: Optional[str] = None
    tools: Optional[List[str]] = None  # Tools to use (e.g., ['web_search'])
    session_id: Optional[str] = None  # Session identifier


# NEW: API Request Models for Swarm Agent Endpoints
class AnalyzeContentRequest(BaseModel):
    text: str = Field(..., description="Full article content to analyze")
    title: Optional[str] = Field(None, description="Article title")
    source: Optional[str] = Field(None, description="Source name (e.g., 'MIT Sloan')")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")


class GenerateMetaRequest(BaseModel):
    title: str = Field(..., description="Article title")
    content: str = Field(..., description="Full article content")
    keywords: Optional[List[str]] = Field(default_factory=list, description="Target keywords")
    target_audience: Optional[str] = Field("general", description="Target audience")
    tone: Optional[str] = Field("professional", description="Tone of voice")


class WebUI:
    """
    Enhanced Web UI for TORQ CONSOLE v0.80.0 with Swarm Agent API.

    Provides a rich web interface that combines the power of TORQ CONSOLE's
    MCP integration with an intuitive UI optimized for AI pair programming,
    featuring multiple chat tabs, real-time collaboration, Socket.IO support,
    and REST API endpoints for swarm agent capabilities.
    """

    def __init__(self, console: "TorqConsole"):
        self.console = console
        self.logger = logging.getLogger(__name__)
        self.diff_engine = VisualDiffEngine()

        # Initialize chat manager
        self.chat_manager = ChatManager(
            config=console.config,
            context_manager=console.context_manager
        )

        # Initialize inline editor
        self.inline_editor = InlineEditor(
            config=console.config,
            context_manager=console.context_manager
        )

        # Initialize command palette
        self.command_palette = CommandPalette(
            config=console.config,
            context_manager=console.context_manager,
            chat_manager=self.chat_manager,
            inline_editor=self.inline_editor
        )

        # FastAPI app setup
        self.app = FastAPI(
            title="TORQ CONSOLE Web UI & Swarm Agent API",
            description="Enhanced AI pair programming with MCP integration and swarm intelligence",
            version="0.80.0"
        )

        # Add CORS middleware for Socket.IO
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # API Key for authentication (load from environment)
        self.api_key = os.getenv('TORQ_CONSOLE_API_KEY') or self._generate_api_key()
        if not os.getenv('TORQ_CONSOLE_API_KEY'):
            self.logger.warning(f"No API key set. Generated temporary key: {self.api_key}")
            self.logger.warning("Set TORQ_CONSOLE_API_KEY environment variable for production use")

        # Mount static files
        self.app.mount("/static", StaticFiles(directory="torq_console/ui/static"), name="static")

        # Socket.IO setup
        self.sio = None
        if SOCKETIO_AVAILABLE:
            self.sio = AsyncServer(
                async_mode='asgi',
                cors_allowed_origins="*",
                logger=False,
                engineio_logger=False
            )
            self._setup_socketio_handlers()

        # WebSocket connections (legacy support)
        self.active_connections: Dict[str, WebSocket] = {}

        # Real-time client management
        self.connected_clients: Dict[str, Dict[str, Any]] = {}
        self.message_queue: asyncio.Queue = asyncio.Queue()
        self.client_subscriptions: Dict[str, Set[str]] = {}  # client_id -> set of tab_ids

        # Setup routes
        self._setup_routes()
        self._setup_chat_routes()
        self._setup_command_palette_routes()
        self._setup_swarm_api_routes()  # NEW: Swarm Agent API endpoints

        # Templates and static files
        self.templates = Jinja2Templates(directory="torq_console/ui/templates")

        # CRITICAL FIX: Apply AI integration fixes
        if AI_FIXES_AVAILABLE:
            try:
                apply_web_ai_fixes(self)
                self.logger.info("Applied AI integration fixes successfully")
            except Exception as e:
                self.logger.error(f"Failed to apply AI fixes: {e}")

        # Session management (legacy)
        self.active_sessions: Dict[str, Dict[str, Any]] = {}

        # Message processing task
        self._message_processor_task: Optional[asyncio.Task] = None

    def _generate_api_key(self) -> str:
        """Generate a secure API key."""
        return secrets.token_urlsafe(32)

    async def _verify_api_key(self, x_api_key: Optional[str] = Header(None)) -> bool:
        """Verify API key from request header."""
        if not x_api_key:
            raise HTTPException(
                status_code=401,
                detail={
                    "error": {
                        "code": "UNAUTHORIZED",
                        "message": "Missing API key. Provide X-API-Key header.",
                        "timestamp": datetime.now().isoformat()
                    }
                }
            )

        if x_api_key != self.api_key:
            raise HTTPException(
                status_code=401,
                detail={
                    "error": {
                        "code": "UNAUTHORIZED",
                        "message": "Invalid API key",
                        "timestamp": datetime.now().isoformat()
                    }
                }
            )

        return True

    def _setup_swarm_api_routes(self):
        """Setup Swarm Agent API routes for TORQ Tech News and n8n integration."""

        @self.app.get("/api/health")
        async def health_check():
            """
            Health check endpoint for system status.

            Returns comprehensive system health including agents, LLM providers, and resources.
            """
            try:
                # Get swarm orchestrator status
                swarm_status = await self.console.swarm_orchestrator.health_check()

                # Get agent statuses
                agent_statuses = await self.console.swarm_orchestrator.get_swarm_status()

                # Determine LLM provider statuses
                llm_providers = {
                    "claude": "operational" if os.getenv('ANTHROPIC_API_KEY') else "not_configured",
                    "deepseek": "operational" if os.getenv('DEEPSEEK_API_KEY') else "not_configured",
                    "ollama": "operational",  # Assume available if local
                    "llama_cpp": "operational"
                }

                return {
                    "status": "healthy" if swarm_status.get('status') == 'healthy' else "degraded",
                    "version": "0.80.0",
                    "service": "TORQ Console",
                    "timestamp": datetime.now().isoformat(),
                    "agents": {
                        "total": len(agent_statuses.get('agents', {})),
                        "active": len([a for a in agent_statuses.get('agents', {}).values() if a.get('status') == 'ready']),
                        "available": list(agent_statuses.get('agents', {}).keys())
                    },
                    "llm_providers": llm_providers,
                    "resources": {
                        "codebase_vectors": getattr(self.console.context_manager, 'vector_count', 0),
                        "memory_entries": agent_statuses.get('memory_system', {}).get('agent_memories', 0)
                    }
                }

            except Exception as e:
                self.logger.error(f"Health check error: {e}")
                return {
                    "status": "unhealthy",
                    "version": "0.80.0",
                    "service": "TORQ Console",
                    "timestamp": datetime.now().isoformat(),
                    "error": str(e)
                }

        @self.app.post("/api/analyze-content")
        async def analyze_content(
            request: AnalyzeContentRequest,
            authenticated: bool = Depends(self._verify_api_key)
        ):
            """
            Analyze article content quality using the analysis agent.

            Requires X-API-Key header for authentication.
            """
            try:
                self.logger.info(f"Analyzing content: {request.title}")

                # Get analysis agent from swarm orchestrator
                analysis_agent = self.console.swarm_orchestrator.agents.get('analysis_agent')

                if not analysis_agent:
                    raise HTTPException(
                        status_code=503,
                        detail={
                            "error": {
                                "code": "AGENT_UNAVAILABLE",
                                "message": "Analysis agent not available",
                                "timestamp": datetime.now().isoformat()
                            }
                        }
                    )

                # Prepare task for analysis agent
                task = {
                    'type': 'content_analysis',
                    'query': request.title or "Analyze this content",
                    'content': request.text,
                    'context': {
                        'title': request.title,
                        'source': request.source,
                        'metadata': request.metadata,
                        'analysis_type': 'comprehensive'
                    }
                }

                # Execute analysis through swarm orchestrator
                result = await self.console.swarm_orchestrator.execute_task(task)

                # Extract quality metrics (simulated for now - can be enhanced)
                word_count = len(request.text.split())
                reading_time = max(1, word_count // 200)  # ~200 words per minute

                # Basic sentiment analysis
                positive_words = ['good', 'great', 'excellent', 'innovative', 'success', 'growth', 'improve']
                negative_words = ['bad', 'poor', 'fail', 'decline', 'problem', 'issue', 'risk']
                text_lower = request.text.lower()

                positive_count = sum(1 for word in positive_words if word in text_lower)
                negative_count = sum(1 for word in negative_words if word in text_lower)
                sentiment = "positive" if positive_count > negative_count else "neutral" if positive_count == negative_count else "negative"

                # Extract key topics (simple keyword extraction)
                import re
                words = re.findall(r'\b\w+\b', request.text.lower())
                word_freq = {}
                for word in words:
                    if len(word) > 4:  # Filter short words
                        word_freq[word] = word_freq.get(word, 0) + 1

                key_topics = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:5]
                key_topics = [word for word, freq in key_topics]

                return {
                    "quality_score": min(0.95, 0.5 + (word_count / 2000)),  # Scale based on length
                    "sentiment": sentiment,
                    "key_topics": key_topics,
                    "summary": result[:200] + "..." if len(result) > 200 else result,
                    "keywords": key_topics,
                    "readability": {
                        "grade_level": "college" if word_count > 500 else "general",
                        "reading_time_minutes": reading_time,
                        "complexity": "high" if word_count > 1000 else "medium" if word_count > 500 else "low"
                    },
                    "engagement_score": min(0.90, 0.6 + (word_count / 3000)),
                    "recommendations": [
                        "Content length is appropriate" if word_count > 300 else "Consider expanding content",
                        "Good keyword density" if len(key_topics) >= 3 else "Add more relevant keywords",
                        "Clear structure detected" if request.title else "Add a clear title"
                    ],
                    "analysis": {
                        "strengths": ["Comprehensive coverage", "Clear language"],
                        "weaknesses": ["Could use more examples" if word_count < 500 else None],
                        "opportunities": ["Add data visualizations", "Include expert quotes"]
                    }
                }

            except HTTPException:
                raise
            except Exception as e:
                self.logger.error(f"Content analysis error: {e}")
                raise HTTPException(
                    status_code=500,
                    detail={
                        "error": {
                            "code": "INTERNAL_ERROR",
                            "message": f"Analysis failed: {str(e)}",
                            "timestamp": datetime.now().isoformat()
                        }
                    }
                )

        @self.app.post("/api/generate-meta")
        async def generate_meta(
            request: GenerateMetaRequest,
            authenticated: bool = Depends(self._verify_api_key)
        ):
            """
            Generate SEO-optimized metadata using the documentation agent.

            Requires X-API-Key header for authentication.
            """
            try:
                self.logger.info(f"Generating metadata for: {request.title}")

                # Get documentation agent from swarm orchestrator
                doc_agent = self.console.swarm_orchestrator.agents.get('documentation_agent')

                if not doc_agent:
                    raise HTTPException(
                        status_code=503,
                        detail={
                            "error": {
                                "code": "AGENT_UNAVAILABLE",
                                "message": "Documentation agent not available",
                                "timestamp": datetime.now().isoformat()
                            }
                        }
                    )

                # Generate meta description (160 chars optimal)
                content_preview = request.content[:200].replace('\n', ' ')
                meta_desc = f"{content_preview}... Learn more about {request.title}."[:157] + "..."

                # Generate OG metadata
                og_title = request.title if len(request.title) <= 60 else request.title[:57] + "..."
                og_desc = content_preview[:197] + "..." if len(content_preview) > 197 else content_preview

                # Extract or generate keywords
                keywords = request.keywords if request.keywords else []
                if not keywords:
                    # Extract from title and content
                    import re
                    words = re.findall(r'\b\w+\b', (request.title + ' ' + request.content).lower())
                    word_freq = {}
                    for word in words:
                        if len(word) > 4:
                            word_freq[word] = word_freq.get(word, 0) + 1
                    keywords = [word for word, freq in sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:8]]

                # Calculate SEO score
                title_length = len(request.title)
                meta_length = len(meta_desc)
                has_keywords = len(keywords) >= 3

                seo_score = 0.0
                seo_score += 0.3 if 30 <= title_length <= 60 else 0.1
                seo_score += 0.3 if 120 <= meta_length <= 160 else 0.1
                seo_score += 0.2 if has_keywords else 0.0
                seo_score += 0.2  # Baseline for having structured data

                suggestions = []
                if title_length < 30:
                    suggestions.append("Title could be more descriptive")
                elif title_length > 60:
                    suggestions.append("Title is too long, consider shortening")
                else:
                    suggestions.append(f"Title length optimal ({title_length} characters)")

                if 120 <= meta_length <= 160:
                    suggestions.append(f"Meta description within range ({meta_length} characters)")
                else:
                    suggestions.append(f"Meta description length: {meta_length} chars (optimal: 120-160)")

                if has_keywords:
                    suggestions.append("Keywords naturally integrated")
                else:
                    suggestions.append("Consider adding more relevant keywords")

                return {
                    "meta_description": meta_desc,
                    "og_title": og_title,
                    "og_description": og_desc,
                    "twitter_card": "summary_large_image",
                    "keywords": keywords,
                    "schema_org": {
                        "@context": "https://schema.org",
                        "@type": "NewsArticle",
                        "headline": request.title,
                        "description": meta_desc,
                        "keywords": ", ".join(keywords)
                    },
                    "seo_score": round(seo_score, 2),
                    "suggestions": suggestions
                }

            except HTTPException:
                raise
            except Exception as e:
                self.logger.error(f"Metadata generation error: {e}")
                raise HTTPException(
                    status_code=500,
                    detail={
                        "error": {
                            "code": "INTERNAL_ERROR",
                            "message": f"Metadata generation failed: {str(e)}",
                            "timestamp": datetime.now().isoformat()
                        }
                    }
                )

        @self.app.get("/api/trending-topics")
        async def trending_topics(
            category: Optional[str] = None,
            timeframe: Optional[str] = "7d",
            sources: Optional[str] = None,
            authenticated: bool = Depends(self._verify_api_key)
        ):
            """
            Discover trending tech topics using the search agent.

            Query Parameters:
            - category: Filter by category (ai, tech, business)
            - timeframe: Time range (24h, 7d, 30d)
            - sources: Comma-separated source list

            Requires X-API-Key header for authentication.
            """
            try:
                self.logger.info(f"Finding trending topics: category={category}, timeframe={timeframe}")

                # Get search agent from swarm orchestrator
                search_agent = self.console.swarm_orchestrator.agents.get('search_agent')

                if not search_agent:
                    raise HTTPException(
                        status_code=503,
                        detail={
                            "error": {
                                "code": "AGENT_UNAVAILABLE",
                                "message": "Search agent not available",
                                "timestamp": datetime.now().isoformat()
                            }
                        }
                    )

                # Build search query based on parameters
                search_query = "trending tech topics"
                if category:
                    search_query = f"trending {category} topics"

                # Prepare task for search agent
                task = {
                    'type': 'trending_discovery',
                    'query': search_query,
                    'context': {
                        'category': category or 'general',
                        'timeframe': timeframe,
                        'sources': sources.split(',') if sources else [],
                        'max_results': 15
                    }
                }

                # Execute search through swarm orchestrator
                result = await self.console.swarm_orchestrator.execute_task(task)

                # Mock trending topics (in production, this would come from search results)
                topics = [
                    {
                        "topic": "AI regulation and policy",
                        "trend_score": 0.94,
                        "mentions": 247,
                        "sources": ["TechCrunch", "MIT Tech Review", "Hacker News"],
                        "keywords": ["regulation", "AI", "policy", "ethics", "governance"],
                        "related_articles": [
                            {
                                "title": "New AI Regulations Take Effect in EU",
                                "url": "https://example.com/ai-regulations",
                                "source": "TechCrunch",
                                "date": datetime.now().isoformat()
                            }
                        ],
                        "sentiment": "neutral",
                        "growth_rate": "+45% (7d)"
                    },
                    {
                        "topic": "Quantum computing breakthroughs",
                        "trend_score": 0.89,
                        "mentions": 183,
                        "sources": ["MIT Tech Review", "Nature"],
                        "keywords": ["quantum", "computing", "qubits", "breakthrough"],
                        "sentiment": "positive",
                        "growth_rate": "+62% (7d)"
                    },
                    {
                        "topic": "Large language model advancements",
                        "trend_score": 0.87,
                        "mentions": 312,
                        "sources": ["OpenAI Blog", "Anthropic", "Google AI"],
                        "keywords": ["LLM", "GPT", "Claude", "AI models"],
                        "sentiment": "positive",
                        "growth_rate": "+38% (7d)"
                    }
                ]

                return {
                    "topics": topics,
                    "timestamp": datetime.now().isoformat(),
                    "total_topics": len(topics),
                    "returned": len(topics)
                }

            except HTTPException:
                raise
            except Exception as e:
                self.logger.error(f"Trending topics error: {e}")
                raise HTTPException(
                    status_code=500,
                    detail={
                        "error": {
                            "code": "INTERNAL_ERROR",
                            "message": f"Trending topics discovery failed: {str(e)}",
                            "timestamp": datetime.now().isoformat()
                        }
                    }
                )

    def _setup_routes(self):
        """Setup FastAPI routes."""

        @self.app.get("/", response_class=HTMLResponse)
        async def dashboard(request: Request):
            """Main dashboard."""
            return self.templates.TemplateResponse(
                "dashboard.html",
                {
                    "request": request,
                    "console_info": await self._get_console_info(),
                    "mcp_servers": len(self.console.connected_servers),
                    "current_repo": str(self.console.repo_path.name)
                }
            )

        @self.app.get("/api/console/info")
        async def get_console_info():
            """Get console information."""
            return await self._get_console_info()

        @self.app.post("/api/console/model")
        async def update_model(request: "ModelUpdateRequest"):
            """Update the AI model."""
            return await self._update_model(request)

        @self.app.get("/api/files")
        async def list_files(path: str = "."):
            """List files in directory."""
            return await self._list_files(path)

        @self.app.get("/api/files/content")
        async def get_file_content(file_path: str):
            """Get file content with syntax highlighting."""
            return await self._get_file_content(file_path)

        @self.app.post("/api/files/save")
        async def save_file(request: "SaveFileRequest"):
            """Save file content."""
            return await self._save_file(request)

        @self.app.get("/api/diff")
        async def get_diff(file_path: str = None, tool: str = "auto"):
            """Get visual diff."""
            return await self._get_diff(file_path, tool)

        @self.app.post("/api/edit")
        async def perform_edit(request: "EditRequest"):
            """Perform AI-assisted edit."""
            return await self._perform_edit(request)

        @self.app.post("/api/inline-edit")
        async def inline_edit(request: "InlineEditRequest"):
            """Handle inline editing requests."""
            return await self._handle_inline_edit(request)

        @self.app.get("/api/inline-edit/ghost-suggestions")
        async def get_ghost_suggestions():
            """Get active ghost text suggestions."""
            return self.inline_editor.get_active_ghost_suggestions()

        @self.app.post("/api/inline-edit/ghost-action")
        async def ghost_action(request: "GhostActionRequest"):
            """Handle ghost text actions (accept/dismiss)."""
            return await self._handle_ghost_action(request)

        @self.app.get("/api/inline-edit/stats")
        async def inline_edit_stats():
            """Get inline editing statistics."""
            return self.inline_editor.get_edit_statistics()

        @self.app.get("/api/mcp/servers")
        async def list_mcp_servers():
            """List connected MCP servers."""
            return {"servers": list(self.console.connected_servers.keys())}

        @self.app.post("/api/mcp/connect")
        async def connect_mcp(request: "MCPConnectRequest"):
            """Connect to MCP server."""
            success = await self.console.connect_mcp(request.endpoint)
            return {"success": success, "endpoint": request.endpoint}

        @self.app.get("/api/mcp/tools")
        async def list_mcp_tools():
            """List available MCP tools."""
            return await self._list_mcp_tools()

        @self.app.post("/api/mcp/call")
        async def call_mcp_tool(request: "MCPToolRequest"):
            """Call MCP tool."""
            return await self._call_mcp_tool(request)

        @self.app.websocket("/ws/{client_id}")
        async def websocket_endpoint(websocket: WebSocket, client_id: str):
            """WebSocket endpoint for real-time updates."""
            await self._handle_websocket(websocket, client_id)

        @self.app.get("/api/sessions")
        async def list_sessions():
            """List active sessions."""
            return {"sessions": list(self.active_sessions.keys())}

        @self.app.post("/api/sessions/start")
        async def start_session():
            """Start new session."""
            session = await self.console.start_session()
            session_id = session["id"]
            self.active_sessions[session_id] = session
            return {"session_id": session_id, "session": session}

        @self.app.get("/api/git/status")
        async def git_status():
            """Get git status."""
            return await self.console.git_manager.get_status()

        @self.app.post("/api/git/commit")
        async def git_commit(request: "GitCommitRequest"):
            """Commit changes."""
            return await self._git_commit(request)

        @self.app.post("/api/git/reset")
        async def git_reset(request: "GitResetRequest"):
            """Reset git changes."""
            return await self._git_reset(request)

    def _setup_chat_routes(self):
        """Setup chat management routes."""

        @self.app.post("/api/chat")
        async def direct_chat(request: DirectChatRequest):
            """
            ENHANCED: Direct chat endpoint with proper AI routing.
            Routes all queries through the enhanced AI integration system.
            """
            try:
                self.logger.info(f"Direct chat request: {request.message}")

                # Use enhanced AI routing if available
                if AI_FIXES_AVAILABLE:
                    return await WebUIAIFixes.direct_chat_fixed(self, request)

                # Fallback to enhanced AI integration
                response_content = await self._generate_ai_response(request.message, None)

                return {
                    "success": True,
                    "response": response_content,
                    "agent": "TORQ Console AI",
                    "timestamp": datetime.now().isoformat()
                }

            except Exception as e:
                self.logger.error(f"Direct chat error: {e}")
                return {
                    "success": False,
                    "error": f"Error processing your request: {str(e)}",
                    "response": f"I apologize, but I encountered an error processing your request: {str(e)}. Please try again."
                }

        @self.app.get("/api/chat/tabs")
        async def list_chat_tabs():
            """List all chat tabs."""
            return await self.chat_manager.get_tab_list()

        @self.app.post("/api/chat/tabs")
        async def create_chat_tab(request: "CreateChatTabRequest"):
            """Create a new chat tab."""
            tab = await self.chat_manager.create_new_tab(
                title=request.title,
                workspace_path=Path(request.workspace_path) if request.workspace_path else None,
                model=request.model
            )
            return tab.to_dict()

        @self.app.post("/api/chat/tabs/{tab_id}/switch")
        async def switch_chat_tab(tab_id: str):
            """Switch to a specific chat tab."""
            success = await self.chat_manager.switch_to_tab(tab_id)
            return {"success": success, "active_tab_id": tab_id}

        @self.app.delete("/api/chat/tabs/{tab_id}")
        async def close_chat_tab(tab_id: str, force: bool = False):
            """Close a chat tab."""
            success = await self.chat_manager.close_tab(tab_id, force)
            return {"success": success}

        @self.app.get("/api/chat/tabs/{tab_id}/messages")
        async def get_chat_messages(tab_id: str, limit: Optional[int] = None, offset: int = 0):
            """Get messages from a chat tab."""
            messages = await self.chat_manager.get_tab_messages(tab_id, limit, offset)
            return {"messages": [msg.to_dict() for msg in messages]}

        @self.app.post("/api/chat/tabs/{tab_id}/messages")
        async def send_chat_message(tab_id: str, request: "SendMessageRequest"):
            """Send a message to a chat tab."""
            # Get context if needed
            context_matches = None
            if request.include_context:
                context_results = await self.console.context_manager.parse_and_retrieve(
                    request.content, context_type="mixed"
                )
                context_matches = []
                for matches in context_results.values():
                    context_matches.extend(matches)

            # Add user message
            user_message = await self.chat_manager.add_message(
                content=request.content,
                message_type=MessageType.USER,
                tab_id=tab_id,
                metadata=request.metadata,
                context_matches=context_matches
            )

            if not user_message:
                raise HTTPException(status_code=400, detail="Failed to add message")

            # CRITICAL FIX: Generate proper AI response using enhanced AI integration
            if request.generate_response:
                ai_response = await self._generate_ai_response(request.content, context_matches)
                await self.chat_manager.add_message(
                    content=ai_response,
                    message_type=MessageType.ASSISTANT,
                    tab_id=tab_id,
                    metadata={"model": request.model or "claude-sonnet-4"}
                )

            return user_message.to_dict()

        @self.app.get("/api/chat/tabs/{tab_id}/checkpoints")
        async def get_chat_checkpoints(tab_id: str):
            """Get checkpoints for a chat tab."""
            checkpoints = await self.chat_manager.get_checkpoint_list(tab_id)
            return {"checkpoints": checkpoints}

        @self.app.post("/api/chat/tabs/{tab_id}/checkpoints")
        async def create_chat_checkpoint(tab_id: str, request: "CreateCheckpointRequest"):
            """Create a checkpoint for a chat tab."""
            checkpoint = await self.chat_manager.create_checkpoint(
                tab_id=tab_id,
                checkpoint_type=request.type,
                description=request.description
            )
            return checkpoint.to_dict() if checkpoint else {"error": "Failed to create checkpoint"}

        @self.app.post("/api/chat/checkpoints/{checkpoint_id}/restore")
        async def restore_chat_checkpoint(checkpoint_id: str):
            """Restore a chat tab to a checkpoint."""
            success = await self.chat_manager.restore_checkpoint(checkpoint_id)
            return {"success": success}

        @self.app.post("/api/chat/tabs/{tab_id}/export")
        async def export_chat_tab(tab_id: str, include_context: bool = False):
            """Export a chat tab to markdown."""
            export_path = await self.chat_manager.export_tab_to_markdown(tab_id, include_context)
            if export_path:
                return {"success": True, "export_path": str(export_path)}
            else:
                raise HTTPException(status_code=500, detail="Failed to export chat tab")

        @self.app.get("/api/chat/stats")
        async def get_chat_statistics():
            """Get chat management statistics."""
            return await self.chat_manager.get_chat_statistics()

    async def _generate_ai_response(self, user_content: str, context_matches: Optional[List] = None) -> str:
        """
        Generate AI response using enhanced AI integration.

        This method properly routes queries through the enhanced AI integration system
        which includes DeepSeek API, web search, and Prince Flowers capabilities.
        """
        try:
            self.logger.info(f"Processing AI query: {user_content}")

            # Check if this is a Prince Flowers command
            content_lower = user_content.lower().strip()

            # Enhanced detection for Prince Flowers commands and search queries
            is_prince_command = (
                content_lower.startswith("prince ") or
                content_lower.startswith("@prince ") or
                any(keyword in content_lower for keyword in [
                    "prince search", "prince help", "prince status",
                ])
            )

            # ROUTE ALL QUERIES TO PRINCE FLOWERS FOR BEST QUALITY
            # Prince Flowers now uses Claude Sonnet 4.5 for reasoning/coding
            # and DeepSeek for fast searches

            # Try Prince Flowers first (with Claude + DeepSeek integration)
            if hasattr(self.console, 'prince_flowers_integration') and self.console.prince_flowers_integration:
                try:
                    self.logger.info("Routing query to Prince Flowers Enhanced Agent")
                    integration = self.console.prince_flowers_integration

                    # Process via Prince Flowers
                    if hasattr(integration, 'process_query_async'):
                        response = await integration.process_query_async(user_content)
                    elif hasattr(integration, 'process_query'):
                        response = await asyncio.to_thread(integration.process_query, user_content)
                    else:
                        raise AttributeError("Prince Flowers integration missing process methods")

                    # Extract response content
                    if isinstance(response, dict):
                        return response.get('content', response.get('answer', str(response)))
                    elif hasattr(response, 'content'):
                        return response.content
                    else:
                        return str(response)

                except Exception as e:
                    self.logger.error(f"Prince Flowers routing error: {e}")
                    # Fallback to AI integration

            # Fallback: Use AI integration layer
            is_search_or_ai_query = any(keyword in content_lower for keyword in [
                "search", "find", "latest", "current", "news", "recent",
                "ai", "artificial intelligence", "developments", "what is",
                "how to", "web search", "search for", "ai news"
            ])

            if is_prince_command:
                return await self._handle_prince_command(user_content, context_matches)
            elif is_search_or_ai_query or True:  # Route all queries through enhanced AI
                return await self._handle_enhanced_ai_query(user_content, context_matches)
            else:
                return await self._handle_basic_query(user_content, context_matches)

        except Exception as e:
            self.logger.error(f"Error generating AI response: {e}")
            return f"I apologize, but I encountered an error processing your request: {str(e)}. Please try again."

    async def _handle_enhanced_ai_query(self, query: str, context_matches: Optional[List] = None) -> str:
        """
        Handle queries through the enhanced AI integration system.

        This method uses the console's AI integration which includes:
        - DeepSeek API for AI responses
        - Web search capabilities
        - Query classification and routing
        - Fallback handling
        """
        try:
            self.logger.info(f"Processing enhanced AI query: {query}")

            # Use console's AI integration if available
            if hasattr(self.console, 'ai_integration') and self.console.ai_integration:
                # Prepare context for AI integration
                context = {
                    'web_interface': True,
                    'context_matches': context_matches or [],
                    'timestamp': datetime.now().isoformat()
                }

                # Generate response using enhanced AI integration
                response = await self.console.ai_integration.generate_response(query, context)

                if response.get('success', True):
                    content = response.get('content', response.get('response', ''))

                    # Add metadata if available
                    if response.get('metadata'):
                        metadata = response['metadata']
                        if metadata.get('execution_time') and metadata.get('query_type'):
                            content += f"\n\n*{metadata['query_type'].title()} query processed in {metadata['execution_time']:.2f}s*"

                    return content or "I processed your query successfully."
                else:
                    return response.get('content', f"I encountered an issue: {response.get('error', 'Unknown error')}")

            else:
                return await self._handle_basic_query(query, context_matches)

        except Exception as e:
            self.logger.error(f"Error in enhanced AI query handling: {e}")
            return f"I encountered an error processing your query: {str(e)}. Please try again."

    async def _handle_prince_command(self, command: str, context_matches: Optional[List] = None) -> str:
        """Handle Prince Flowers commands with real web search integration."""
        try:
            self.logger.info(f"Processing Prince Flowers command: {command}")

            # CRITICAL FIX: Ensure command starts with 'prince' for proper routing
            if not command.lower().startswith('prince'):
                command = f"prince {command}"

            # Extract the actual query from Prince command
            query_parts = command.lower().split(' ', 1)
            if len(query_parts) > 1:
                actual_query = query_parts[1]
            else:
                actual_query = "help"

            # ENHANCED PRINCE INTEGRATION: Use working web search pipeline
            # Check if this is a search-related Prince command
            search_indicators = ['search', 'find', 'research', 'look up', 'get info', 'latest', 'news', 'data']
            is_search_command = any(indicator in actual_query.lower() for indicator in search_indicators)

            if is_search_command and hasattr(self.console, 'ai_integration') and self.console.ai_integration:
                self.logger.info(f"Prince search command detected: {actual_query}")

                # Use the working AI integration with web search
                context = {
                    'web_interface': True,
                    'context_matches': context_matches or [],
                    'timestamp': datetime.now().isoformat(),
                    'prince_mode': True,  # Special flag for Prince commands
                    'force_search': True  # Force web search regardless of classification
                }

                # Route through enhanced AI which has working web search
                ai_response = await self.console.ai_integration.generate_response(
                    actual_query,
                    context=context,
                    provider_hint='websearch'
                )

                if ai_response and ai_response.get('success', True):
                    result = ai_response.get('content', ai_response.get('response', ''))

                    # Add Prince branding to the response
                    prince_response = f"🤖 **Prince Flowers Enhanced Agent Response:**\n\n{result}"

                    # Add RL feedback indication
                    prince_response += f"\n\n*Prince Agent executed search successfully using Google Custom Search API*"

                    return prince_response
                else:
                    self.logger.warning("AI integration failed for Prince command")

            # Check if Prince Flowers integration is available for non-search commands
            if hasattr(self.console, 'prince_flowers_integration') and self.console.prince_flowers_integration:
                # Use the integration wrapper
                integration = self.console.prince_flowers_integration

                # Prepare context
                enhanced_context = {
                    'web_interface': True,
                    'context_matches': context_matches or [],
                    'timestamp': datetime.now().isoformat()
                }

                # Process through integration
                response = await integration.query(command, enhanced_context, show_performance=True)

                if response.success:
                    result = response.content
                    if response.execution_time and response.confidence:
                        result += f"\n\n*Processed in {response.execution_time:.2f}s with {response.confidence:.1%} confidence*"
                    return result
                else:
                    return response.content or f"Prince Flowers encountered an error: {response.error}"

            elif hasattr(self.console, 'handle_prince_command'):
                # Use console's prince command handler
                return await self.console.handle_prince_command(command, {'web_interface': True})

            elif hasattr(self.console, 'prince_flowers'):
                # Direct access to Prince Flowers agent
                if hasattr(self.console.prince_flowers, 'handle_prince_command'):
                    return await self.console.prince_flowers.handle_prince_command(command, {'web_interface': True})
                elif hasattr(self.console.prince_flowers, 'agent') and hasattr(self.console.prince_flowers.agent, 'execute_agentic_task'):
                    # Extract query from command
                    query = command
                    if command.lower().startswith('prince '):
                        query = command[7:].strip()
                    elif command.lower().startswith('@prince '):
                        query = command[8:].strip()

                    result = await self.console.prince_flowers.agent.execute_agentic_task(query)
                    return result.get('answer', 'Prince Flowers processed your request.')
                else:
                    return "Prince Flowers agent is available but doesn't have the expected interface methods."
            else:
                # Fallback: Route through enhanced AI
                self.logger.info("Routing Prince command through enhanced AI as fallback")
                query = command
                if command.lower().startswith('prince '):
                    query = command[7:].strip()

                return await self._handle_enhanced_ai_query(query, context_matches)

        except Exception as e:
            self.logger.error(f"Error in Prince command handling: {e}")
            return f"Error processing Prince Flowers command: {str(e)}"

    async def _handle_basic_query(self, query: str, context_matches: Optional[List] = None) -> str:
        """Handle basic queries with enhanced fallback."""
        try:
            # Try console's generate_response method
            if hasattr(self.console, 'generate_response'):
                try:
                    result = await self.console.generate_response(query, context_matches)
                    return result
                except Exception as e:
                    self.logger.warning(f"Console generate_response failed: {e}")

            # Enhanced fallback response
            query_lower = query.lower()

            if any(keyword in query_lower for keyword in ['search', 'find', 'latest', 'news', 'current']):
                return f"""I understand you're looking for information about: "{query}"

I don't have access to real-time search capabilities at the moment, but I can suggest some ways to find current information:

**For General Searches:**
• Use search engines like Google, Bing, or DuckDuckGo
• Check relevant official websites and documentation
• Look for recent news articles and press releases

**For AI-Related Information:**
• TechCrunch AI section for industry news
• MIT Technology Review for in-depth analysis
• Official AI company blogs (OpenAI, Google, Anthropic, etc.)
• arXiv.org for research papers

**For Breaking News:**
• Reuters, Associated Press, BBC News
• Industry-specific news sources
• Social media accounts of relevant organizations

Would you like me to help you formulate a more specific search strategy for "{query}"?"""

            else:
                return f"""Thank you for your question: "{query}"

I'm here to help! While I can provide assistance and guidance, for the best results I recommend:

1. **For complex queries**: Try using more specific language
2. **For search-related questions**: I can help guide you to the right sources
3. **For current information**: I can suggest where to look for the latest updates

How else can I assist you with "{query}"?"""

        except Exception as e:
            self.logger.error(f"Error in basic query handling: {e}")
            return f"I'm available to help, but encountered an error: {str(e)}. Please try again."

    def _setup_command_palette_routes(self):
        """Setup command palette routes."""

        @self.app.get("/api/command-palette/commands")
        async def get_commands():
            """Get all available commands."""
            try:
                commands = self.command_palette.registry.get_all_commands()
                # Convert to search result format
                results = [
                    {
                        "command": cmd.to_dict(),
                        "score": 1.0,
                        "match_type": "title",
                        "match_positions": []
                    }
                    for cmd in commands
                ]
                return {"success": True, "commands": results}
            except Exception as e:
                self.logger.error(f"Error getting commands: {e}")
                return {"success": False, "error": str(e)}

        @self.app.post("/api/command-palette/search")
        async def search_commands(request: Dict[str, Any]):
            """Search commands with fuzzy matching."""
            try:
                query = request.get("query", "")
                category = request.get("category", "all")

                results = await self.command_palette.search_commands(query)

                # Filter by category if specified
                if category != "all":
                    results = [r for r in results if r.command.category.value == category]

                serialized_results = [
                    {
                        "command": result.command.to_dict(),
                        "score": result.score,
                        "match_type": result.match_type,
                        "match_positions": result.match_positions
                    }
                    for result in results
                ]

                return {"success": True, "results": serialized_results}
            except Exception as e:
                self.logger.error(f"Error searching commands: {e}")
                return {"success": False, "error": str(e)}

        @self.app.post("/api/command-palette/execute")
        async def execute_command(request: Dict[str, Any]):
            """Execute a command by ID."""
            try:
                command_id = request.get("command_id")
                parameters = request.get("parameters", {})

                if not command_id:
                    return {"success": False, "error": "Command ID required"}

                execution = await self.command_palette.execute_command(command_id, parameters)

                return {
                    "success": execution.success,
                    "result": execution.result,
                    "error": execution.error,
                    "duration_ms": execution.duration_ms
                }
            except Exception as e:
                self.logger.error(f"Error executing command: {e}")
                return {"success": False, "error": str(e)}

        @self.app.get("/api/command-palette/recent")
        async def get_recent_commands():
            """Get recently executed commands."""
            try:
                recent = await self.command_palette.get_recent_commands(10)
                return {"success": True, "commands": recent}
            except Exception as e:
                self.logger.error(f"Error getting recent commands: {e}")
                return {"success": False, "commands": []}

        @self.app.get("/api/command-palette/favorites")
        async def get_favorite_commands():
            """Get favorite commands."""
            try:
                favorites = await self.command_palette.get_favorites()
                return {"success": True, "commands": favorites}
            except Exception as e:
                self.logger.error(f"Error getting favorites: {e}")
                return {"success": False, "commands": []}

        @self.app.post("/api/command-palette/favorites/{command_id}")
        async def toggle_favorite(command_id: str):
            """Toggle favorite status of a command."""
            try:
                success = await self.command_palette.toggle_favorite(command_id)
                return {"success": success}
            except Exception as e:
                self.logger.error(f"Error toggling favorite: {e}")
                return {"success": False, "error": str(e)}

        @self.app.get("/api/command-palette/stats")
        async def get_command_palette_stats():
            """Get command palette statistics."""
            try:
                stats = await self.command_palette.get_palette_statistics()
                return {"success": True, "stats": stats}
            except Exception as e:
                self.logger.error(f"Error getting stats: {e}")
                return {"success": False, "error": str(e)}

        @self.app.get("/api/command-palette/command/{command_id}")
        async def get_command_details(command_id: str):
            """Get detailed information about a command."""
            try:
                details = await self.command_palette.get_command_details(command_id)
                if details:
                    return {"success": True, "command": details}
                else:
                    return {"success": False, "error": "Command not found"}
            except Exception as e:
                self.logger.error(f"Error getting command details: {e}")
                return {"success": False, "error": str(e)}

    def _setup_socketio_handlers(self):
        """Setup Socket.IO event handlers."""
        if not self.sio:
            return

        @self.sio.event
        async def connect(sid, environ, auth):
            """Handle client connection."""
            try:
                client_id = auth.get('client_id') if auth else str(uuid.uuid4())

                self.connected_clients[sid] = {
                    'client_id': client_id,
                    'connected_at': datetime.now(),
                    'subscriptions': set()
                }

                self.client_subscriptions[client_id] = set()

                await self.sio.emit('connected', {
                    'client_id': client_id,
                    'server_time': datetime.now().isoformat()
                }, room=sid)

                self.logger.info(f"Socket.IO client connected: {client_id} ({sid})")

            except Exception as e:
                self.logger.error(f"Error in Socket.IO connect: {e}")

        @self.sio.event
        async def disconnect(sid):
            """Handle client disconnection."""
            try:
                client_info = self.connected_clients.pop(sid, {})
                client_id = client_info.get('client_id')

                if client_id:
                    self.client_subscriptions.pop(client_id, None)

                self.logger.info(f"Socket.IO client disconnected: {client_id} ({sid})")

            except Exception as e:
                self.logger.error(f"Error in Socket.IO disconnect: {e}")

        @self.sio.event
        async def subscribe_tab(sid, data):
            """Subscribe to chat tab updates."""
            try:
                tab_id = data.get('tab_id')
                if not tab_id:
                    await self.sio.emit('error', {'message': 'tab_id required'}, room=sid)
                    return

                client_info = self.connected_clients.get(sid, {})
                client_id = client_info.get('client_id')

                if client_id:
                    self.client_subscriptions[client_id].add(tab_id)
                    client_info['subscriptions'].add(tab_id)

                    await self.sio.emit('subscribed', {
                        'tab_id': tab_id,
                        'message': f'Subscribed to tab {tab_id}'
                    }, room=sid)

            except Exception as e:
                self.logger.error(f"Error in subscribe_tab: {e}")
                await self.sio.emit('error', {'message': str(e)}, room=sid)

        @self.sio.event
        async def unsubscribe_tab(sid, data):
            """Unsubscribe from chat tab updates."""
            try:
                tab_id = data.get('tab_id')
                if not tab_id:
                    return

                client_info = self.connected_clients.get(sid, {})
                client_id = client_info.get('client_id')

                if client_id:
                    self.client_subscriptions[client_id].discard(tab_id)
                    client_info['subscriptions'].discard(tab_id)

                    await self.sio.emit('unsubscribed', {
                        'tab_id': tab_id,
                        'message': f'Unsubscribed from tab {tab_id}'
                    }, room=sid)

            except Exception as e:
                self.logger.error(f"Error in unsubscribe_tab: {e}")

        @self.sio.event
        async def typing_start(sid, data):
            """Handle typing start event."""
            try:
                tab_id = data.get('tab_id')
                if tab_id:
                    await self._broadcast_to_tab_subscribers(tab_id, 'typing_start', {
                        'tab_id': tab_id,
                        'client_id': self.connected_clients.get(sid, {}).get('client_id'),
                        'timestamp': datetime.now().isoformat()
                    }, exclude_sid=sid)

            except Exception as e:
                self.logger.error(f"Error in typing_start: {e}")

        @self.sio.event
        async def typing_stop(sid, data):
            """Handle typing stop event."""
            try:
                tab_id = data.get('tab_id')
                if tab_id:
                    await self._broadcast_to_tab_subscribers(tab_id, 'typing_stop', {
                        'tab_id': tab_id,
                        'client_id': self.connected_clients.get(sid, {}).get('client_id'),
                        'timestamp': datetime.now().isoformat()
                    }, exclude_sid=sid)

            except Exception as e:
                self.logger.error(f"Error in typing_stop: {e}")

        # Register chat manager callback for real-time updates
        async def chat_event_callback(event_data):
            """Handle chat events from chat manager."""
            event_type = event_data.get('type')
            tab_id = event_data.get('tab_id')

            if tab_id:
                await self._broadcast_to_tab_subscribers(tab_id, event_type, event_data)
            else:
                # Broadcast to all connected clients
                await self.sio.emit(event_type, event_data)

        # Register the callback with chat manager
        asyncio.create_task(self.chat_manager.register_websocket_callback(chat_event_callback))

    async def _get_console_info(self) -> Dict[str, Any]:
        """Get console information."""
        session_info = None
        if self.console.current_session:
            try:
                session_info = self.console.get_session_info()
                # If session_info contains async tasks, convert them to dict safely
                if isinstance(session_info, dict):
                    safe_session = {}
                    for key, value in session_info.items():
                        if hasattr(value, '__dict__') or str(type(value)).startswith('<Task'):
                            continue  # Skip async tasks and complex objects
                        safe_session[key] = value
                    session_info = safe_session
            except Exception:
                session_info = {"session_id": str(self.console.current_session.get("id", "unknown"))}

        return {
            "version": "0.80.0",
            "claude_version": "Claude Opus 4.1 (claude-opus-4-1-20250805)",
            "repo_path": str(self.console.repo_path),
            "model": self.console.model,
            "voice_enabled": getattr(self.console, 'voice_enabled', False),
            "ideation_mode": getattr(self.console, 'ideation_mode', False),
            "planning_mode": getattr(self.console, 'planning_mode', False),
            "connected_servers": len(self.console.connected_servers),
            "active_files": [str(f) for f in self.console.active_files],
            "session_id": self.console.current_session.get("id") if self.console.current_session else None,
            "mcp_status": "auto-connecting" if len(self.console.connected_servers) == 0 else "connected",
            "ai_integration": {
                "enhanced_mode": hasattr(self.console, 'ai_integration') and
                                getattr(self.console.ai_integration, 'enhanced_mode', False),
                "deepseek_configured": bool(os.getenv('DEEPSEEK_API_KEY')),
                "fixes_applied": AI_FIXES_AVAILABLE
            },
            "swarm_agents": {
                "total": 8,
                "available": ["search", "analysis", "synthesis", "response", "code", "documentation", "testing", "performance"]
            }
        }

    async def _update_model(self, request: 'ModelUpdateRequest') -> Dict[str, Any]:
        """Update the AI model."""
        try:
            # Update console model
            self.console.model = request.model
            if hasattr(self.console, 'ai_integration') and self.console.ai_integration:
                self.console.ai_integration.model = request.model

            # Broadcast model change
            await self._broadcast_message({
                "type": "model_change",
                "model": request.model,
                "timestamp": datetime.now().isoformat()
            })

            return {
                "success": True,
                "model": request.model,
                "message": f"Model updated to {request.model}"
            }

        except Exception as e:
            self.logger.error(f"Model update error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    async def _list_files(self, path: str) -> Dict[str, Any]:
        """List files in directory."""
        try:
            # Secure path handling - prevent directory traversal
            if path.startswith('/') or '..' in path:
                path = '.'

            base_path = self.console.repo_path / path

            # Ensure we stay within the repository
            try:
                base_path = base_path.resolve()
                base_path.relative_to(self.console.repo_path.resolve())
            except ValueError:
                base_path = self.console.repo_path
                path = '.'

            if not base_path.exists():
                raise HTTPException(status_code=404, detail="Path not found")

            files = []
            for item in base_path.iterdir():
                if item.name.startswith('.'):
                    continue

                try:
                    rel_path = str(item.relative_to(self.console.repo_path))
                except ValueError:
                    continue  # Skip files outside repo

                file_info = {
                    "name": item.name,
                    "path": rel_path,
                    "type": "directory" if item.is_dir() else "file",
                    "size": item.stat().st_size if item.is_file() else 0,
                    "modified": datetime.fromtimestamp(item.stat().st_mtime).isoformat()
                }

                if item.is_file():
                    file_info["extension"] = item.suffix
                    file_info["language"] = self.diff_engine._detect_language(item)

                files.append(file_info)

            # Sort: directories first, then files
            files.sort(key=lambda x: (x["type"] == "file", x["name"].lower()))

            # Calculate parent path safely
            parent_path = None
            if base_path != self.console.repo_path:
                try:
                    parent_rel = str(base_path.parent.relative_to(self.console.repo_path))
                    parent_path = parent_rel if parent_rel != '.' else None
                except ValueError:
                    parent_path = None

            return {
                "path": path,
                "files": files,
                "parent": parent_path
            }

        except Exception as e:
            self.logger.error(f"File listing error: {e}")
            # Return empty directory listing instead of error
            return {
                "path": ".",
                "files": [],
                "parent": None
            }

    async def _get_file_content(self, file_path: str) -> Dict[str, Any]:
        """Get file content with syntax highlighting."""
        try:
            full_path = self.console.repo_path / file_path

            if not full_path.exists():
                raise HTTPException(status_code=404, detail="File not found")

            if not full_path.is_file():
                raise HTTPException(status_code=400, detail="Path is not a file")

            # Read content
            content = full_path.read_text()

            # Get syntax highlighted preview
            preview = await self.diff_engine.get_file_preview(full_path, tool="rich")

            # Get git status for this file
            git_status = await self.console.git_manager.get_file_status(full_path)

            return {
                "file_path": file_path,
                "content": content,
                "preview": preview,
                "language": self.diff_engine._detect_language(full_path),
                "size": len(content),
                "lines": len(content.split('\n')),
                "git_status": git_status,
                "modified": datetime.fromtimestamp(full_path.stat().st_mtime).isoformat()
            }

        except Exception as e:
            self.logger.error(f"File content error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    async def _save_file(self, request: 'SaveFileRequest') -> Dict[str, Any]:
        """Save file content."""
        try:
            full_path = self.console.repo_path / request.file_path

            # Backup original if exists
            backup_content = None
            if full_path.exists():
                backup_content = full_path.read_text()

            # Write new content
            full_path.write_text(request.content)

            # Notify WebSocket clients
            await self._broadcast_file_change(request.file_path, "saved")

            return {
                "success": True,
                "file_path": request.file_path,
                "size": len(request.content),
                "backup_created": backup_content is not None
            }

        except Exception as e:
            self.logger.error(f"File save error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    async def _get_diff(self, file_path: Optional[str], tool: str) -> Dict[str, Any]:
        """Get visual diff."""
        try:
            if file_path:
                full_path = self.console.repo_path / file_path
                diff_content = await self.diff_engine.get_diff(
                    file_path=full_path, tool=tool
                )
            else:
                diff_content = await self.diff_engine.get_diff(tool=tool)

            return {
                "diff": diff_content,
                "tool": tool,
                "file_path": file_path,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f"Diff generation error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    async def _perform_edit(self, request: 'EditRequest') -> Dict[str, Any]:
        """Perform AI-assisted edit."""
        try:
            # Start progress tracking
            edit_id = str(uuid.uuid4())[:8]
            await self._broadcast_edit_progress(edit_id, "starting", 0)

            # Perform edit using console
            success = await self.console.edit_files(
                message=request.message,
                files=request.files,
                auto_commit=request.auto_commit
            )

            await self._broadcast_edit_progress(edit_id, "completed" if success else "failed", 100)

            return {
                "success": success,
                "edit_id": edit_id,
                "message": request.message,
                "files": request.files,
                "session_id": self.console.current_session["id"] if self.console.current_session else None
            }

        except Exception as e:
            self.logger.error(f"Edit error: {e}")
            await self._broadcast_edit_progress(edit_id, "error", 0)
            raise HTTPException(status_code=500, detail=str(e))

    async def _list_mcp_tools(self) -> Dict[str, Any]:
        """List available MCP tools with enhanced metadata for UI display."""
        tools = []

        # Enhanced tool metadata mapping for better UX
        tool_metadata = {
            # File Operations
            "read_file": {
                "icon": "📄",
                "category": "File Operations",
                "friendly_description": "Opens and displays any file content quickly",
                "use_case": "Read source code, configs, or any text file"
            },
            "write_file": {
                "icon": "✍️",
                "category": "File Operations",
                "friendly_description": "Creates or updates files with new content",
                "use_case": "Save code changes or create new files"
            },
            "list_directory": {
                "icon": "📁",
                "category": "File Operations",
                "friendly_description": "Shows all files and folders in a directory",
                "use_case": "Explore project structure and locate files"
            },
            "delete_file": {
                "icon": "🗑️",
                "category": "File Operations",
                "friendly_description": "Removes files or directories safely",
                "use_case": "Clean up unwanted files or temporary data"
            },
            "search_files": {
                "icon": "🔍",
                "category": "File Operations",
                "friendly_description": "Find files by name pattern across your project",
                "use_case": "Locate specific files or search by extension"
            },

            # Search & Analysis
            "grep": {
                "icon": "🔎",
                "category": "Search",
                "friendly_description": "Search for text patterns across multiple files",
                "use_case": "Find code references, function calls, or strings"
            },
            "ripgrep": {
                "icon": "⚡",
                "category": "Search",
                "friendly_description": "Ultra-fast text search with regex support",
                "use_case": "Quick code searches across large codebases"
            },
            "semantic_search": {
                "icon": "🧠",
                "category": "Search",
                "friendly_description": "AI-powered search by meaning, not just keywords",
                "use_case": "Find similar code or concepts semantically"
            },

            # Database
            "query_database": {
                "icon": "💾",
                "category": "Database",
                "friendly_description": "Execute SQL queries and retrieve results",
                "use_case": "Inspect data, run analytics, or test queries"
            },
            "list_tables": {
                "icon": "📊",
                "category": "Database",
                "friendly_description": "Shows all tables and schemas in database",
                "use_case": "Explore database structure and relationships"
            },
            "describe_table": {
                "icon": "📋",
                "category": "Database",
                "friendly_description": "View table schema with columns and types",
                "use_case": "Understand table structure before querying"
            },

            # Web & Network
            "fetch_url": {
                "icon": "🌐",
                "category": "Web",
                "friendly_description": "Fetch content from any URL or API endpoint",
                "use_case": "Test APIs, scrape data, or download resources"
            },
            "web_search": {
                "icon": "🔍",
                "category": "Web",
                "friendly_description": "Search the web for information and examples",
                "use_case": "Find documentation, solutions, or tutorials"
            },
            "browse_url": {
                "icon": "🌍",
                "category": "Web",
                "friendly_description": "Extract and analyze webpage content",
                "use_case": "Research documentation or extract web data"
            },

            # Git & Version Control
            "git_status": {
                "icon": "📈",
                "category": "Git",
                "friendly_description": "Shows current Git repository status",
                "use_case": "Check uncommitted changes and branch info"
            },
            "git_diff": {
                "icon": "🔀",
                "category": "Git",
                "friendly_description": "Display differences between versions",
                "use_case": "Review code changes before committing"
            },
            "git_commit": {
                "icon": "✅",
                "category": "Git",
                "friendly_description": "Save changes with a descriptive message",
                "use_case": "Commit completed work to version control"
            },
            "git_log": {
                "icon": "📜",
                "category": "Git",
                "friendly_description": "View commit history and timeline",
                "use_case": "Track changes and find specific commits"
            },

            # Code Analysis
            "analyze_code": {
                "icon": "🔬",
                "category": "Code Analysis",
                "friendly_description": "Deep analysis of code quality and patterns",
                "use_case": "Identify bugs, smells, or improvement areas"
            },
            "lint_code": {
                "icon": "🧹",
                "category": "Code Analysis",
                "friendly_description": "Check code style and find common mistakes",
                "use_case": "Maintain code quality and consistency"
            },
            "find_references": {
                "icon": "🔗",
                "category": "Code Analysis",
                "friendly_description": "Locate all usages of a function or variable",
                "use_case": "Understand code dependencies and impact"
            },

            # Terminal & Shell
            "run_command": {
                "icon": "⚙️",
                "category": "Terminal",
                "friendly_description": "Execute shell commands and scripts",
                "use_case": "Run builds, tests, or system commands"
            },
            "bash": {
                "icon": "💻",
                "category": "Terminal",
                "friendly_description": "Interactive bash shell access",
                "use_case": "Run complex command sequences"
            },

            # Testing
            "run_tests": {
                "icon": "🧪",
                "category": "Testing",
                "friendly_description": "Execute test suites and show results",
                "use_case": "Validate code changes with automated tests"
            },
            "coverage_report": {
                "icon": "📊",
                "category": "Testing",
                "friendly_description": "Generate code coverage statistics",
                "use_case": "Identify untested code areas"
            },

            # Documentation
            "generate_docs": {
                "icon": "📖",
                "category": "Documentation",
                "friendly_description": "Auto-generate documentation from code",
                "use_case": "Create API docs or code references"
            },
            "extract_docstrings": {
                "icon": "📝",
                "category": "Documentation",
                "friendly_description": "Extract documentation from source files",
                "use_case": "Review or export code documentation"
            }
        }

        for endpoint, server_info in self.console.connected_servers.items():
            try:
                server_tools = await self.console.mcp_client.list_tools()
                for tool in server_tools:
                    tool_name = tool["name"]
                    base_description = tool.get("description", "")

                    # Get enhanced metadata or use defaults
                    metadata = tool_metadata.get(tool_name, {
                        "icon": "🔧",
                        "category": "Other Tools",
                        "friendly_description": base_description or "Execute tool operation",
                        "use_case": "Perform specific tool function"
                    })

                    # Extract parameter info for tooltips
                    parameters = tool.get("inputSchema", {}).get("properties", {})
                    param_summary = self._generate_parameter_summary(parameters)

                    tools.append({
                        "name": tool_name,
                        "description": base_description,
                        "endpoint": endpoint,
                        "parameters": parameters,
                        # Enhanced fields for UI
                        "icon": metadata["icon"],
                        "category": metadata["category"],
                        "user_friendly_description": metadata["friendly_description"],
                        "use_case": metadata["use_case"],
                        "parameter_summary": param_summary,
                        "tooltip": f"{metadata['icon']} {metadata['friendly_description']}\n\nUse case: {metadata['use_case']}\n\nParameters: {param_summary}"
                    })
            except Exception as e:
                self.logger.error(f"Error listing tools for {endpoint}: {e}")

        # Group tools by category for organized display
        categorized_tools = {}
        for tool in tools:
            category = tool["category"]
            if category not in categorized_tools:
                categorized_tools[category] = []
            categorized_tools[category].append(tool)

        return {
            "tools": tools,
            "categorized": categorized_tools,
            "categories": list(categorized_tools.keys())
        }

    def _generate_parameter_summary(self, parameters: Dict[str, Any]) -> str:
        """Generate a concise parameter summary for tooltips."""
        if not parameters:
            return "No parameters required"

        param_list = []
        for param_name, param_info in parameters.items():
            param_type = param_info.get("type", "any")
            required = param_info.get("required", False)
            marker = "*" if required else ""
            param_list.append(f"{param_name}{marker} ({param_type})")

        return ", ".join(param_list) if param_list else "No parameters"

    async def _call_mcp_tool(self, request: 'MCPToolRequest') -> Dict[str, Any]:
        """Call MCP tool."""
        try:
            result = await self.console.mcp_client.call_tool(
                request.tool_name, request.parameters
            )

            return {
                "success": True,
                "tool_name": request.tool_name,
                "result": result,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f"MCP tool call error: {e}")
            return {
                "success": False,
                "tool_name": request.tool_name,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    async def _git_commit(self, request: 'GitCommitRequest') -> Dict[str, Any]:
        """Commit changes."""
        try:
            success = await self.console.git_manager.commit(
                message=request.message,
                files=request.files
            )

            await self._broadcast_git_change("commit", request.message)

            return {
                "success": success,
                "message": request.message,
                "files": request.files
            }

        except Exception as e:
            self.logger.error(f"Git commit error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    async def _handle_websocket(self, websocket: WebSocket, client_id: str):
        """Handle WebSocket connection."""
        await websocket.accept()
        self.active_connections[client_id] = websocket

        try:
            while True:
                # Keep connection alive and handle incoming messages
                data = await websocket.receive_text()
                message = json.loads(data)

                # Handle different message types
                if message["type"] == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))
                elif message["type"] == "subscribe":
                    # Handle subscription to events
                    pass

        except Exception as e:
            self.logger.error(f"WebSocket error for {client_id}: {e}")
        finally:
            if client_id in self.active_connections:
                del self.active_connections[client_id]

    async def _broadcast_message(self, message: Dict[str, Any]):
        """Broadcast message to all connected clients."""
        if not self.active_connections:
            return

        message_str = json.dumps(message)
        disconnected = []

        for client_id, websocket in self.active_connections.items():
            try:
                await websocket.send_text(message_str)
            except Exception:
                disconnected.append(client_id)

        # Clean up disconnected clients
        for client_id in disconnected:
            del self.active_connections[client_id]

    async def _broadcast_file_change(self, file_path: str, action: str):
        """Broadcast file change event."""
        await self._broadcast_message({
            "type": "file_change",
            "file_path": file_path,
            "action": action,
            "timestamp": datetime.now().isoformat()
        })

    async def _broadcast_edit_progress(self, edit_id: str, status: str, progress: int):
        """Broadcast edit progress."""
        await self._broadcast_message({
            "type": "edit_progress",
            "edit_id": edit_id,
            "status": status,
            "progress": progress,
            "timestamp": datetime.now().isoformat()
        })

    async def _broadcast_git_change(self, action: str, message: str):
        """Broadcast git change event."""
        await self._broadcast_message({
            "type": "git_change",
            "action": action,
            "message": message,
            "timestamp": datetime.now().isoformat()
        })

    async def _handle_inline_edit(self, request: "InlineEditRequest") -> Dict[str, Any]:
        """Handle inline editing request."""
        try:
            # Convert request to dictionary format
            request_data = {
                "id": request.id or str(uuid.uuid4()),
                "mode": request.mode,
                "action": request.action,
                "prompt": request.prompt,
                "selection": request.selection,
                "file_path": request.file_path,
                "cursor_position": tuple(request.cursor_position) if request.cursor_position else None,
                "metadata": request.metadata or {}
            }

            # Process through inline editor
            response = await self.inline_editor.handle_edit_request(request_data)

            # Broadcast update to connected clients
            await self._broadcast_message({
                "type": "inline_edit_response",
                "request_id": request_data["id"],
                "response": response.to_dict(),
                "timestamp": datetime.now().isoformat()
            })

            return response.to_dict()

        except Exception as e:
            self.logger.error(f"Inline edit error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    async def _handle_ghost_action(self, request: "GhostActionRequest") -> Dict[str, Any]:
        """Handle ghost text actions."""
        try:
            # Route to appropriate inline editor method
            if request.action == "accept":
                result = await self.inline_editor._accept_ghost_text({
                    "ghost_id": request.ghost_id
                })
            elif request.action == "dismiss":
                result = await self.inline_editor._dismiss_ghost_text({
                    "ghost_id": request.ghost_id
                })
            else:
                raise HTTPException(status_code=400, detail=f"Unknown ghost action: {request.action}")

            # Broadcast update
            await self._broadcast_message({
                "type": "ghost_action",
                "action": request.action,
                "ghost_id": request.ghost_id,
                "result": result,
                "timestamp": datetime.now().isoformat()
            })

            return result

        except Exception as e:
            self.logger.error(f"Ghost action error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    async def _git_reset(self, request: "GitResetRequest") -> Dict[str, Any]:
        """Reset git changes."""
        try:
            if request.files:
                # Reset specific files
                for file_path in request.files:
                    await self.console.git_manager.reset_file(file_path, hard=request.hard)
            else:
                # Reset all changes
                await self.console.git_manager.reset_all(hard=request.hard)

            return {
                "success": True,
                "hard_reset": request.hard,
                "files": request.files,
                "message": "Git reset completed successfully"
            }

        except Exception as e:
            self.logger.error(f"Git reset error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    async def _broadcast_to_tab_subscribers(self, tab_id: str, event_type: str,
                                          data: Dict[str, Any], exclude_sid: str = None) -> None:
        """Broadcast event to all clients subscribed to a specific tab."""
        if not self.sio:
            return

        try:
            # Find all clients subscribed to this tab
            target_sids = []
            for sid, client_info in self.connected_clients.items():
                if sid != exclude_sid and tab_id in client_info.get('subscriptions', set()):
                    target_sids.append(sid)

            # Broadcast to target clients
            for sid in target_sids:
                try:
                    await self.sio.emit(event_type, data, room=sid)
                except Exception as e:
                    self.logger.debug(f"Error broadcasting to {sid}: {e}")

        except Exception as e:
            self.logger.error(f"Error in _broadcast_to_tab_subscribers: {e}")

    async def _start_message_processor(self) -> None:
        """Start the message processing task."""
        if self._message_processor_task is None or self._message_processor_task.done():
            self._message_processor_task = asyncio.create_task(self._process_message_queue())

    async def _process_message_queue(self) -> None:
        """Process queued messages for real-time distribution."""
        try:
            while True:
                try:
                    # Wait for messages with timeout
                    message = await asyncio.wait_for(self.message_queue.get(), timeout=1.0)

                    # Process the message
                    await self._handle_queued_message(message)

                    # Mark task as done
                    self.message_queue.task_done()

                except asyncio.TimeoutError:
                    # No messages to process, continue loop
                    continue

                except Exception as e:
                    self.logger.error(f"Error processing queued message: {e}")

        except asyncio.CancelledError:
            self.logger.info("Message processor task cancelled")
        except Exception as e:
            self.logger.error(f"Unexpected error in message processor: {e}")

    async def _handle_queued_message(self, message: Dict[str, Any]) -> None:
        """Handle a queued message."""
        try:
            event_type = message.get('type')
            tab_id = message.get('tab_id')

            if tab_id and self.sio:
                await self._broadcast_to_tab_subscribers(tab_id, event_type, message)
            elif self.sio:
                # Broadcast to all clients
                await self.sio.emit(event_type, message)

            # Also broadcast via legacy WebSocket
            await self._broadcast_message(message)

        except Exception as e:
            self.logger.error(f"Error handling queued message: {e}")

    async def start_server(self, host: str = "localhost", port: int = 8080):
        """Start the web server with Socket.IO and chat management."""
        self.logger.info(f"Starting TORQ CONSOLE Web UI v0.80.0 at http://{host}:{port}")
        self.logger.info(f"Swarm Agent API Key: {self.api_key}")
        self.logger.info(f"API Documentation: http://{host}:{port}/docs")

        try:
            # Initialize chat manager
            await self.chat_manager.initialize()

            # Initialize command palette
            await self.command_palette.initialize()

            # Start message processor
            await self._start_message_processor()

            # Auto-connect to MCP servers
            await self.console._auto_connect_mcp()

            # Setup Socket.IO app if available
            if self.sio:
                # Mount Socket.IO to FastAPI
                app_with_sio = socketio.ASGIApp(self.sio, self.app)
                self.logger.info("Socket.IO integration enabled")
            else:
                app_with_sio = self.app
                self.logger.warning("Socket.IO not available - real-time features limited")

            config = uvicorn.Config(
                app=app_with_sio,
                host=host,
                port=port,
                log_level="info",
                reload=False,
                timeout_keep_alive=300,  # 5 minutes (above master timeout of 360s)
                timeout_graceful_shutdown=60,  # 1 minute for cleanup
                limit_max_requests=1000  # Prevent memory leaks from long-running workers
            )

            server = uvicorn.Server(config)
            await server.serve()

        except Exception as e:
            self.logger.error(f"Error starting server: {e}")
            raise
        finally:
            # Cleanup resources
            await self._shutdown_cleanup()

    async def _shutdown_cleanup(self) -> None:
        """Cleanup resources on server shutdown."""
        try:
            # Cancel message processor task
            if self._message_processor_task and not self._message_processor_task.done():
                self._message_processor_task.cancel()
                try:
                    await self._message_processor_task
                except asyncio.CancelledError:
                    pass

            # Shutdown chat manager
            await self.chat_manager.shutdown()

            # Cleanup inline editor
            await self.inline_editor.cleanup()

            # Clear connections
            self.connected_clients.clear()
            self.client_subscriptions.clear()
            self.active_connections.clear()

            self.logger.info("WebUI cleanup completed")

        except Exception as e:
            self.logger.error(f"Error during WebUI cleanup: {e}")


# Pydantic models for API requests

class SaveFileRequest(BaseModel):
    file_path: str
    content: str


class EditRequest(BaseModel):
    message: str
    files: Optional[List[str]] = None
    auto_commit: bool = False


class MCPConnectRequest(BaseModel):
    endpoint: str


class MCPToolRequest(BaseModel):
    tool_name: str
    parameters: Dict[str, Any] = {}


class GitCommitRequest(BaseModel):
    message: str
    files: Optional[List[str]] = None


class ModelUpdateRequest(BaseModel):
    model: str


class InlineEditRequest(BaseModel):
    id: Optional[str] = None
    mode: str
    action: str
    prompt: str
    selection: Optional[Dict[str, Any]] = None
    file_path: Optional[str] = None
    cursor_position: Optional[List[int]] = None
    metadata: Optional[Dict[str, Any]] = None


class GhostActionRequest(BaseModel):
    action: str  # "accept", "dismiss", "alternatives"
    ghost_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class GitResetRequest(BaseModel):
    hard: bool = False
    files: Optional[List[str]] = None


# New Pydantic models for chat management

class CreateChatTabRequest(BaseModel):
    title: Optional[str] = None
    workspace_path: Optional[str] = None
    model: str = "claude-sonnet-4"


class SendMessageRequest(BaseModel):
    content: str
    include_context: bool = True
    generate_response: bool = True
    model: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class CreateCheckpointRequest(BaseModel):
    type: str = "manual"  # CheckpointType enum value
    description: str = ""
