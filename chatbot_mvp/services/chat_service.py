"""
Chat service module for handling business logic and AI integration.

This module separates chat logic from UI state, implementing:
- Response generation strategies
- AI client integration
- Message processing
- Context management
"""

import time
from typing import Dict, List, Optional, Protocol
from abc import ABC, abstractmethod

from chatbot_mvp.config.settings import is_demo_mode


class ResponseStrategy(Protocol):
    """Protocol for response generation strategies."""
    
    def generate_response(
        self, 
        message: str, 
        conversation_history: List[Dict[str, str]],
        user_context: Optional[Dict] = None
    ) -> str:
        """Generate a response for given message."""
        ...


class BaseResponseStrategy(ABC):
    """Base class for response strategies."""
    
    @abstractmethod
    def generate_response(
        self, 
        message: str, 
        conversation_history: List[Dict[str, str]],
        user_context: Optional[Dict] = None
    ) -> str:
        """Generate a response for given message."""
        pass


class DemoResponseStrategy(BaseResponseStrategy):
    """Demo mode response strategy with hardcoded replies."""
    
    def generate_response(
        self, 
        message: str, 
        conversation_history: List[Dict[str, str]],
        user_context: Optional[Dict] = None
    ) -> str:
        """Generate demo response based on message content."""
        lower = message.lower()
        
        if "hola" in lower or "buenas" in lower:
            return "Hola! Contame cual es tu objetivo principal."
        elif "precio" in lower:
            return "Esto es un demo. Pronto se conectara a IA para dar precios."
        elif "servicio" in lower or "ayuda" in lower:
            return "Entendido. Contame un poco mas para ayudarte mejor."
        elif "gracias" in lower:
            return "De nada! Si necesitas algo más, estoy aquí para ayudarte."
        elif "chau" in lower or "adiós" in lower:
            return "Hasta luego! Vuelve cuando necesites asistencia."
        else:
            return "Entendido. Contame un poco mas para ayudarte mejor."


class AIResponseStrategy(BaseResponseStrategy):
    """AI-powered response strategy using OpenAI."""
    
    def __init__(self, ai_client):
        self.ai_client = ai_client
        self.last_response_time = 0
    
    def generate_response(
        self, 
        message: str, 
        conversation_history: List[Dict[str, str]],
        user_context: Optional[Dict] = None
    ) -> str:
        """Generate AI response for the given message."""
        try:
            response = self.ai_client.generate_chat_response(
                message=message,
                conversation_history=conversation_history,
                user_context=user_context,
                max_tokens=150,
                temperature=0.7
            )
            self.last_response_time = time.time()
            return response
            
        except Exception as exc:
            # Fallback to demo response on error
            return f"Error con IA: {str(exc)}. Por favor, intenta de nuevo."


class MessageProcessor:
    """Processes chat messages and manages conversation flow."""
    
    def __init__(self, strategy: BaseResponseStrategy):
        self.strategy = strategy
    
    def process_message(
        self, 
        message: str, 
        conversation_history: List[Dict[str, str]],
        user_context: Optional[Dict] = None
    ) -> str:
        """Process a message and return the response."""
        # Add processing delay for better UX
        time.sleep(0.5)
        
        # Generate response using the configured strategy
        response = self.strategy.generate_response(message, conversation_history, user_context)
        
        return response
    
    def change_strategy(self, strategy: BaseResponseStrategy):
        """Change the response strategy."""
        self.strategy = strategy
    
    def process_message(
        self, 
        message: str, 
        conversation_history: List[Dict[str, str]],
        user_context: Optional[Dict] = None
    ) -> str:
        """Process a message and return the response."""
        # Add processing delay for better UX
        time.sleep(0.5)
        
        # Generate response using the configured strategy
        response = self.strategy.generate_response(message, user_context)
        
        return response
    
    def change_strategy(self, strategy: ResponseStrategy):
        """Change the response strategy."""
        self.strategy = strategy


class ChatService:
    """Main service for chat functionality."""
    
    def __init__(self, ai_client=None):
        # Initialize appropriate strategy based on configuration
        if is_demo_mode():
            strategy = DemoResponseStrategy()
        else:
            strategy = AIResponseStrategy(ai_client) if ai_client else DemoResponseStrategy()
        
        self.processor = MessageProcessor(strategy)
        self.conversation_context: Dict = {}
    
    def send_message(
        self, 
        message: str, 
        conversation_history: List[Dict[str, str]],
        user_context: Optional[Dict] = None
    ) -> str:
        """
        Send a message and get the response.
        
        Args:
            message: The user's message
            conversation_history: List of previous messages
            user_context: Optional user context information
            
        Returns:
            The assistant's response
        """
        # Update conversation context
        self._update_context(conversation_history, user_context)
        
        # Process the message
        response = self.processor.process_message(message, conversation_history, user_context)
        
        return response
    
    def _update_context(
        self, 
        conversation_history: List[Dict[str, str]], 
        user_context: Optional[Dict]
    ):
        """Update the internal conversation context."""
        self.conversation_context = {
            "message_count": len(conversation_history),
            "last_message_time": time.time(),
            "user_context": user_context or {},
        }
    
    def get_context_summary(self) -> Dict:
        """Get a summary of the current conversation context."""
        return self.conversation_context.copy()
    
    def change_response_strategy(self, strategy: BaseResponseStrategy):
        """Change the response strategy used by the service."""
        self.processor.change_strategy(strategy)


# Factory function for creating chat service instances
def create_chat_service(ai_client=None) -> ChatService:
    """
    Factory function to create a ChatService instance.
    
    Args:
        ai_client: Optional AI client for AI responses
        
    Returns:
        Configured ChatService instance
    """
    return ChatService(ai_client)