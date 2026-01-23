import reflex as rx

from chatbot_mvp.services.chat_service import create_chat_service


class ChatState(rx.State):
    messages: list[dict[str, str]] = []
    current_input: str = ""
    loading: bool = False
    typing: bool = False
    user_context: dict = {}
    session_id: str = ""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Initialize chat service
        self.chat_service = create_chat_service()
        
        # Generate session ID
        import uuid
        import time
        self.session_id = f"{int(time.time())}-{uuid.uuid4().hex[:8]}"

    def set_input(self, value: str) -> None:
        self.current_input = value

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
        response = self.chat_service.send_message(
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
        
        # Reset chat service
        self.chat_service = create_chat_service()

    def set_user_context(self, context: dict) -> None:
        """Set user context information."""
        self.user_context = context
        
    def get_chat_context(self) -> dict:
        """Get current chat context information."""
        return self.chat_service.get_context_summary()
