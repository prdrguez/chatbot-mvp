import reflex as rx
from typing import Any

from chatbot_mvp.services.chat_service import create_chat_service
from chatbot_mvp.services.chat_persistence import create_chat_persistence
from chatbot_mvp.services.openai_client import create_chat_client
from chatbot_mvp.services.gemini_client import create_gemini_client
from chatbot_mvp.config.settings import get_ai_provider

# Global service instances to avoid state variable issues
_chat_service_global = None
_chat_persistence_global = None


class ChatState(rx.State):
    messages: list[dict[str, str]] = []
    current_input: str = ""
    loading: bool = False
    typing: bool = False
    user_context: dict = {}
    session_id: str = ""
    session_list: list[dict[str, Any]] = []
    auto_save_enabled: bool = True
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._initialize_services()
    
    def _initialize_services(self):
        """Initialize global services if not already initialized."""
        global _chat_service_global, _chat_persistence_global
        
        if _chat_service_global is None:
            # Initialize appropriate AI client based on provider
            ai_client = None
            provider = get_ai_provider()
            
            if provider == "openai":
                ai_client = create_chat_client()
            elif provider == "gemini":
                ai_client = create_gemini_client()
            
            _chat_service_global = create_chat_service(ai_client)
            _chat_persistence_global = create_chat_persistence()
        
        # Generate session ID if not set
        if not self.session_id:
            import uuid
            import time
            self.session_id = f"{int(time.time())}-{uuid.uuid4().hex[:8]}"
    
    @rx.event
    def load_sessions(self) -> None:
        """Load recent sessions for the sidebar."""
        self.session_list = self.get_recent_sessions()

    def _get_chat_service(self):
        """Get chat service from global."""
        global _chat_service_global
        self._initialize_services()
        return _chat_service_global or create_chat_service()
    
    def _get_chat_persistence(self):
        """Get chat persistence from global."""
        global _chat_persistence_global
        self._initialize_services()
        return _chat_persistence_global or create_chat_persistence()

    def set_input(self, value: str) -> None:
        self.current_input = value

    @rx.event
    def handle_key_down(self, key: str) -> None:
        """Handle key down events."""
        if key == "Enter":
            self.send_message()

    def send_message(self) -> None:
        content = self.current_input.strip()
        if not content:
            return

        # Add user message immediately
        self.messages = [
            *self.messages,
            {"role": "user", "content": content},
        ]
        self.current_input = ""
        self.loading = True
        self.typing = True

        # Get response from chat service
        chat_service = self._get_chat_service()
        response = chat_service.send_message(
            message=content,
            conversation_history=self.messages,
            user_context=self.user_context,
        )

        # Add assistant response
        self.messages = [
            *self.messages,
            {"role": "assistant", "content": response},
        ]
        self.loading = False
        self.typing = False
        
        # Auto-save conversation
        if self.auto_save_enabled:
            self._save_conversation()

    def _save_conversation(self) -> None:
        """Save current conversation to persistent storage."""
        try:
            chat_persistence = self._get_chat_persistence()
            chat_persistence.save_session(
                session_id=self.session_id,
                messages=self.messages,
                user_context=self.user_context,
                metadata={
                    "auto_save": True,
                    "message_count": len(self.messages),
                }
            )
        except Exception:
            # Silently fail to avoid disrupting user experience
            pass

    def handle_quick_reply(self, reply: str) -> None:
        """Handle quick reply button clicks."""
        self.current_input = reply
        self.send_message()

    def clear_chat(self) -> None:
        self.messages = []
        self.current_input = ""
        self.loading = False
        self.typing = False
        
        # Create new session
        import uuid
        import time
        self.session_id = f"{int(time.time())}-{uuid.uuid4().hex[:8]}"
        
        # Reset services
        if hasattr(self, '_services_initialized'):
            delattr(self, '_services_initialized')

    def set_user_context(self, context: dict) -> None:
        """Set user context information."""
        self.user_context = context
        
    def get_chat_context(self) -> dict:
        """Get current chat context information."""
        chat_service = self._get_chat_service()
        return chat_service.get_context_summary()
    
    def load_session(self, session_id: str) -> bool:
        """Load a previous chat session."""
        try:
            chat_persistence = self._get_chat_persistence()
            session_data = chat_persistence.load_session(session_id)
            if session_data:
                self.session_id = session_id
                self.messages = session_data.get("messages", [])
                self.user_context = session_data.get("user_context", {})
                return True
            return False
        except Exception:
            return False
    
    def export_session(self, format_type: str = "json") -> str:
        """Export current session in specified format."""
        try:
            chat_persistence = self._get_chat_persistence()
            return chat_persistence.export_session(
                self.session_id, 
                format_type
            ) or "No data available for export"
        except Exception:
            return "Error exporting session"
    
    def get_recent_sessions(self, limit: int = 10) -> list:
        """Get recent chat sessions."""
        try:
            chat_persistence = self._get_chat_persistence()
            return chat_persistence.get_recent_sessions(limit)
        except Exception:
            return []
    
    def toggle_auto_save(self) -> None:
        """Toggle auto-save functionality."""
        self.auto_save_enabled = not self.auto_save_enabled
