"""
Chat service module for handling business logic and AI integration.

This module separates chat logic from UI state, implementing:
- Response generation strategies
- AI client integration (OpenAI, Gemini, Demo)
- Message processing
- Context management
"""

import time
import logging
import re
from typing import Any, Dict, List, Optional, Protocol, Iterator
from abc import ABC, abstractmethod

from chatbot_mvp.config.settings import get_runtime_ai_provider
from chatbot_mvp.knowledge.policy_kb import build_bm25_index, parse_policy, retrieve
from chatbot_mvp.services.openai_client import AIClientError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

_KB_EMPTY_RESPONSE = (
    "No encuentro eso en la politica cargada. Proba con otra pregunta o revisa el texto de la KB."
)
_KB_EMPTY_SOURCES = "Sin evidencia recuperada"


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

    def generate_response_stream(
        self, 
        message: str, 
        conversation_history: List[Dict[str, str]],
        user_context: Optional[Dict] = None
    ) -> Iterator[str]:
        """Generate a streaming response for given message."""
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

    def generate_response_stream(
        self, 
        message: str, 
        conversation_history: List[Dict[str, str]],
        user_context: Optional[Dict] = None
    ) -> Iterator[str]:
        """Generate a streaming response for given message. Default implementation acts as mock stream."""
        response = self.generate_response(message, conversation_history, user_context)
        yield response


class DemoResponseStrategy(BaseResponseStrategy):
    """Demo mode response strategy with hardcoded replies."""
    
    def generate_response(
        self, 
        message: str, 
        conversation_history: List[Dict[str, str]],
        user_context: Optional[Dict] = None
    ) -> str:
        """Generate demo response based on message content."""
        return self._get_demo_response(message)
        
    def generate_response_stream(
        self, 
        message: str, 
        conversation_history: List[Dict[str, str]],
        user_context: Optional[Dict] = None
    ) -> Iterator[str]:
        """Generate demo response stream."""
        response = self._get_demo_response(message)
        # Simulate typing effect
        for word in response.split(" "):
            yield word + " "
            time.sleep(0.05)

    def _get_demo_response(self, message: str) -> str:
        """Internal helper for demo responses."""
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


class StaticResponseStrategy(BaseResponseStrategy):
    """Static response strategy for configuration errors."""

    def __init__(self, message: str):
        self.message = message

    def generate_response(
        self,
        message: str,
        conversation_history: List[Dict[str, str]],
        user_context: Optional[Dict] = None,
    ) -> str:
        return self.message


class AIResponseStrategy(BaseResponseStrategy):
    """AI-powered response strategy using configurable AI client (OpenAI/Gemini/Groq)."""
    
    def __init__(self, ai_client):
        """
        Initialize AI response strategy.
        
        Args:
            ai_client: Configured AI client (OpenAI or Gemini)
        """
        self.ai_client = ai_client
        self.last_response_time = 0
    
    def generate_response(
        self, 
        message: str, 
        conversation_history: List[Dict[str, str]],
        user_context: Optional[Dict] = None
    ) -> str:
        """
        Generate AI response for given message.
        
        Args:
            message: User message
            conversation_history: Previous conversation messages
            user_context: Optional user context
            
        Returns:
            AI-generated response or error fallback
        """
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
            # Fallback to demo response on AI error
            logger.warning(f"AI response failed, using fallback: {exc}")
            if isinstance(exc, AIClientError) and str(exc):
                return str(exc)
            return "Lo siento, tuve un problema para responder. ¿Podrías reformular tu pregunta?"

    def generate_response_stream(
        self, 
        message: str, 
        conversation_history: List[Dict[str, str]],
        user_context: Optional[Dict] = None
    ) -> Iterator[str]:
        """
        Generate AI streaming response for given message.
        """
        try:
            if hasattr(self.ai_client, "generate_chat_response_stream"):
                stream = self.ai_client.generate_chat_response_stream(
                    message=message,
                    conversation_history=conversation_history,
                    user_context=user_context,
                    max_tokens=250,
                    temperature=0.7
                )
                for chunk in stream:
                    yield chunk
            else:
                # Fallback for clients without stream support
                response = self.ai_client.generate_chat_response(
                    message=message,
                    conversation_history=conversation_history,
                    user_context=user_context,
                )
                yield response
            
            self.last_response_time = time.time()
            
        except Exception as exc:
            logger.warning(f"AI stream response failed: {exc}")
            if isinstance(exc, AIClientError) and str(exc):
                yield str(exc)
            else:
                yield "Lo siento, tuve un problema para responder. ¿Podrías reformular tu pregunta?"


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
        """Process a message and return response."""
        # Add processing delay for better UX
        time.sleep(0.5)
        
        # Generate response using the configured strategy
        response = self.strategy.generate_response(
            message, 
            conversation_history, 
            user_context
        )
        
        return response

    def process_message_stream(
        self, 
        message: str, 
        conversation_history: List[Dict[str, str]],
        user_context: Optional[Dict] = None
    ) -> Iterator[str]:
        """Process a message and return streaming response."""
        # Generating response stream
        return self.strategy.generate_response_stream(
             message, 
             conversation_history, 
             user_context
        )
    
    def change_strategy(self, strategy: BaseResponseStrategy):
        """Change response strategy."""
        self.strategy = strategy


class ChatService:
    """Main service for chat functionality."""
    
    def __init__(self, ai_client=None):
        # Initialize appropriate strategy based on provider configuration
        strategy = self._create_strategy(ai_client)
        self.processor = MessageProcessor(strategy)
        self.conversation_context: Dict = {}
    
    def _create_strategy(self, ai_client=None) -> BaseResponseStrategy:
        """
        Create appropriate response strategy based on configuration.
        
        Args:
            ai_client: Optional AI client instance
            
        Returns:
            Configured response strategy
        """
        provider = get_runtime_ai_provider()
        
        if provider == "demo":
            logger.info("Using demo response strategy")
            return DemoResponseStrategy()
        elif provider == "openai" and ai_client:
            logger.info("Using OpenAI response strategy")
            return AIResponseStrategy(ai_client)
        elif provider == "gemini":
            if not ai_client:
                from chatbot_mvp.services.gemini_client import (
                    create_gemini_client,
                    get_gemini_api_key,
                )

                api_key = get_gemini_api_key()
                if api_key:
                    try:
                        ai_client = create_gemini_client()
                    except Exception as exc:
                        logger.warning(f"Gemini client init failed: {exc}")
                if not ai_client:
                    if api_key:
                        logger.warning(
                            "Gemini API key detected (GEMINI_API_KEY/GOOGLE_API_KEY) but client unavailable, falling back to demo"
                        )
                    else:
                        logger.warning(
                            "Gemini API key missing (set GEMINI_API_KEY or GOOGLE_API_KEY), falling back to demo"
                        )
                    return DemoResponseStrategy()
            logger.info("Using provider: gemini")
            return AIResponseStrategy(ai_client)
        elif provider == "groq":
            if not ai_client:
                from chatbot_mvp.services.groq_client import (
                    create_groq_client,
                    get_groq_api_key,
                )

                api_key = get_groq_api_key()
                if not api_key:
                    logger.warning(
                        "Groq API key missing (set GROQ_API_KEY), falling back to demo"
                    )
                    return DemoResponseStrategy()
                try:
                    ai_client = create_groq_client()
                except Exception as exc:
                    logger.warning(f"Groq client init failed: {exc}")
                    return DemoResponseStrategy()
                if not ai_client:
                    logger.warning("Groq client unavailable, falling back to demo")
                    return DemoResponseStrategy()
            logger.info("Using provider: groq")
            return AIResponseStrategy(ai_client)
        else:
            logger.warning(f"Provider {provider} not available, falling back to demo")
            return DemoResponseStrategy()
    
    def send_message(
        self, 
        message: str, 
        conversation_history: List[Dict[str, str]],
        user_context: Optional[Dict] = None
    ) -> str:
        """
        Send a message and get response.
        
        Args:
            message: The user's message
            conversation_history: List of previous messages
            user_context: Optional user context information
            
        Returns:
            The assistant's response
        """
        # Update conversation context
        self._update_context(conversation_history, user_context)

        prepared_message, sources, no_evidence_response, retrieved_chunks = self._prepare_kb_prompt(
            message, user_context
        )
        if no_evidence_response:
            return no_evidence_response

        if sources and isinstance(self.processor.strategy, DemoResponseStrategy):
            return self._build_demo_kb_answer(retrieved_chunks, sources)

        response = self.processor.process_message(
            prepared_message,
            conversation_history,
            user_context,
        )

        if not sources:
            return response
        return self._append_sources(response, sources)

    def send_message_stream(
        self, 
        message: str, 
        conversation_history: List[Dict[str, str]],
        user_context: Optional[Dict] = None
    ) -> Iterator[str]:
        """
        Send a message and get streaming response.
        """
        # Update conversation context
        self._update_context(conversation_history, user_context)

        prepared_message, sources, no_evidence_response, retrieved_chunks = self._prepare_kb_prompt(
            message, user_context
        )
        if no_evidence_response:
            return self._single_chunk_stream(no_evidence_response)

        if sources and isinstance(self.processor.strategy, DemoResponseStrategy):
            demo_answer = self._build_demo_kb_answer(retrieved_chunks, sources)
            return self._single_chunk_stream(demo_answer)

        stream = self.processor.process_message_stream(
            prepared_message,
            conversation_history,
            user_context,
        )

        if not sources:
            return stream
        return self._stream_with_sources(stream, sources)

    def _prepare_kb_prompt(
        self, message: str, user_context: Optional[Dict]
    ) -> tuple[str, list[str], Optional[str], list[Dict[str, Any]]]:
        kb_payload = self._extract_kb_payload(user_context)
        if not kb_payload:
            return message, [], None, []

        kb_text = kb_payload["kb_text"]
        kb_name = kb_payload["kb_name"]
        chunks = parse_policy(kb_text)
        if not chunks:
            return message, [], self._append_sources(_KB_EMPTY_RESPONSE, []), []

        index = build_bm25_index(chunks)
        retrieved_chunks = retrieve(message, index, chunks, k=4)
        sources = self._extract_sources(retrieved_chunks)
        if not retrieved_chunks:
            return message, [], self._append_sources(_KB_EMPTY_RESPONSE, []), []

        context_block = self._build_kb_context_block(kb_name, retrieved_chunks)
        strict_instruction = (
            "Instrucciones obligatorias:\n"
            "- Responde SOLO usando la evidencia provista.\n"
            "- Si la respuesta no aparece en la evidencia, responde exactamente: "
            '"No encuentro eso en la politica cargada."\n'
            "- Si te piden articulo o item, cita el articulo exacto.\n"
        )
        prepared_message = (
            f"{context_block}\n\n{strict_instruction}\nPregunta del usuario: {message}"
        )
        return prepared_message, sources, None, retrieved_chunks

    def _extract_kb_payload(self, user_context: Optional[Dict]) -> Optional[Dict[str, str]]:
        if not user_context:
            return None
        kb_text = str(user_context.get("kb_text", "")).strip()
        if not kb_text:
            return None
        kb_name = str(user_context.get("kb_name", "KB cargada")).strip() or "KB cargada"
        return {"kb_text": kb_text, "kb_name": kb_name}

    def _build_kb_context_block(self, kb_name: str, retrieved_chunks: List[Dict[str, Any]]) -> str:
        lines = [f"Base de Conocimiento: {kb_name}", "Evidencia recuperada:"]
        for idx, chunk in enumerate(retrieved_chunks, start=1):
            source = chunk.get("source_label") or f"Fragmento {idx}"
            text = str(chunk.get("text", "")).strip()
            lines.append(f"[{idx}] Fuente: {source}")
            lines.append(text)
        return "\n".join(lines)

    def _extract_sources(self, retrieved_chunks: List[Dict[str, Any]]) -> list[str]:
        seen = set()
        ordered_sources: list[str] = []
        for chunk in retrieved_chunks:
            source = str(chunk.get("source_label", "")).strip()
            if not source or source in seen:
                continue
            seen.add(source)
            ordered_sources.append(source)
            if len(ordered_sources) >= 4:
                break
        return ordered_sources

    def _append_sources(self, response: str, sources: List[str]) -> str:
        lines = response.rstrip().splitlines()
        if lines and lines[-1].strip().lower().startswith("fuentes:"):
            lines = lines[:-1]
        clean_response = "\n".join(lines).rstrip()
        sources_text = ", ".join(sources[:4]) if sources else _KB_EMPTY_SOURCES
        return f"{clean_response}\n\nFuentes: {sources_text}"

    def _build_demo_kb_answer(
        self, retrieved_chunks: List[Dict[str, Any]], sources: List[str]
    ) -> str:
        if not retrieved_chunks:
            return self._append_sources(_KB_EMPTY_RESPONSE, [])
        first_chunk = retrieved_chunks[0]
        source = str(first_chunk.get("source_label", "Fragmento 1")).strip()
        raw_text = str(first_chunk.get("text", "")).strip()
        compact_text = re.sub(r"\s+", " ", raw_text)
        excerpt = compact_text[:420]
        if len(compact_text) > 420:
            excerpt += "..."
        response = f"Segun {source}, {excerpt}"
        return self._append_sources(response, sources)

    def _stream_with_sources(
        self, stream: Iterator[str], sources: List[str]
    ) -> Iterator[str]:
        def generator() -> Iterator[str]:
            for chunk in stream:
                yield chunk
            yield f"\n\nFuentes: {', '.join(sources[:4])}"

        return generator()

    def _single_chunk_stream(self, message: str) -> Iterator[str]:
        def generator() -> Iterator[str]:
            yield message

        return generator()
    
    def _update_context(
        self, 
        conversation_history: List[Dict[str, str]], 
        user_context: Optional[Dict]
    ):
        """Update internal conversation context."""
        self.conversation_context = {
            "message_count": len(conversation_history),
            "last_message_time": time.time(),
            "user_context": user_context or {},
        }
    
    def get_context_summary(self) -> Dict:
        """Get a summary of current conversation context."""
        return self.conversation_context.copy()
    
    def change_response_strategy(self, strategy: BaseResponseStrategy):
        """Change response strategy used by the service."""
        self.processor.change_strategy(strategy)


# Factory function for creating chat service instances
def create_chat_service(ai_client=None) -> ChatService:
    """
    Factory function to create a ChatService instance.
    
    This function now determines the AI provider automatically based on
    environment configuration and creates the appropriate service.
    
    Args:
        ai_client: Optional AI client for AI responses
        
    Returns:
        Configured ChatService instance
    """
    return ChatService(ai_client)
