"""
Chat service module for handling business logic and AI integration.

This module separates chat logic from UI state, implementing:
- Response generation strategies
- AI client integration (OpenAI, Gemini, Demo)
- Message processing
- Context management
"""

import hashlib
import time
import logging
import re
from typing import Any, Dict, List, Optional, Protocol, Iterator
from abc import ABC, abstractmethod

from chatbot_mvp.config.settings import get_runtime_ai_provider
from chatbot_mvp.knowledge import (
    KB_MODE_GENERAL,
    KB_MODE_STRICT,
    build_bm25_index,
    get_last_kb_debug as get_policy_kb_debug,
    normalize_kb_mode,
    parse_policy,
    retrieve,
)
from chatbot_mvp.services.openai_client import AIClientError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

_KB_EMPTY_RESPONSE = (
    "No encuentro eso en el documento cargado. Si me indicas el apartado/titulo o pegas el fragmento, lo reviso."
)
_KB_DEFAULT_TOP_K = 4
_KB_DEFAULT_MIN_SCORE = 0.12
_KB_DEFAULT_MAX_CONTEXT_CHARS = 3200
_KB_DEFAULT_MAX_CONTEXT_CHARS_LARGE = 6000
_KB_LARGE_TEXT_THRESHOLD = 40000
_GROQ_KB_MAX_TOKENS_DEFAULT = 700


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

    def _is_groq_client(self) -> bool:
        module_name = str(getattr(self.ai_client.__class__, "__module__", "")).lower()
        class_name = str(getattr(self.ai_client.__class__, "__name__", "")).lower()
        return "groq" in module_name or "groq" in class_name

    def _resolve_max_tokens(
        self,
        user_context: Optional[Dict],
        streaming: bool = False,
    ) -> int:
        default_tokens = 250 if streaming else 150
        if not isinstance(user_context, dict):
            return default_tokens

        kb_context_block = str(user_context.get("kb_context_block", "")).strip()
        if not kb_context_block:
            return default_tokens

        requested_tokens = user_context.get("kb_response_max_tokens")
        try:
            resolved_requested = int(requested_tokens)
        except (TypeError, ValueError):
            resolved_requested = _GROQ_KB_MAX_TOKENS_DEFAULT

        if self._is_groq_client():
            return max(default_tokens, max(400, resolved_requested))
        return default_tokens
    
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
                max_tokens=self._resolve_max_tokens(user_context, streaming=False),
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
                    max_tokens=self._resolve_max_tokens(user_context, streaming=True),
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
        self.last_kb_debug: Dict[str, Any] = {}
    
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
        prepared_message, prepared_user_context, sources, no_evidence_response, retrieved_chunks = (
            self._prepare_kb_prompt(message, user_context)
        )
        self._update_context(conversation_history, prepared_user_context)
        if no_evidence_response:
            return no_evidence_response

        if sources and isinstance(self.processor.strategy, DemoResponseStrategy):
            return self._build_demo_kb_answer(retrieved_chunks, sources)

        response = self.processor.process_message(
            prepared_message,
            conversation_history,
            prepared_user_context,
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
        prepared_message, prepared_user_context, sources, no_evidence_response, retrieved_chunks = (
            self._prepare_kb_prompt(message, user_context)
        )
        self._update_context(conversation_history, prepared_user_context)
        if no_evidence_response:
            return self._single_chunk_stream(no_evidence_response)

        if sources and isinstance(self.processor.strategy, DemoResponseStrategy):
            demo_answer = self._build_demo_kb_answer(retrieved_chunks, sources)
            return self._single_chunk_stream(demo_answer)

        stream = self.processor.process_message_stream(
            prepared_message,
            conversation_history,
            prepared_user_context,
        )

        if not sources:
            return stream
        return self._stream_with_sources(stream, sources)

    def _prepare_kb_prompt(
        self, message: str, user_context: Optional[Dict]
    ) -> tuple[str, Dict[str, Any], list[str], Optional[str], list[Dict[str, Any]]]:
        base_context: Dict[str, Any] = dict(user_context or {})
        kb_payload = self._extract_kb_payload(user_context)
        if not kb_payload:
            self.last_kb_debug = {
                "kb_name": "",
                "kb_mode": KB_MODE_GENERAL,
                "retrieved_count": 0,
                "used_context": False,
                "reason": "kb_inactiva",
                "query": message,
                "query_original": message,
                "query_expanded": message,
                "expansion_notes": [],
                "retrieval_method": "hybrid",
                "context_chars_budget": 0,
                "context_chars_used": 0,
                "chunks_added_by_stitching": [],
                "stitching_added_count": 0,
                "chunks": [],
            }
            return message, base_context, [], None, []

        kb_text = kb_payload["kb_text"]
        kb_name = kb_payload["kb_name"]
        kb_mode = kb_payload["kb_mode"]
        kb_hash = kb_payload["kb_hash"]
        kb_chunks = kb_payload["kb_chunks"]
        kb_index = kb_payload["kb_index"]
        kb_updated_at = kb_payload["kb_updated_at"]
        kb_top_k = kb_payload["kb_top_k"]
        kb_min_score = kb_payload["kb_min_score"]
        kb_max_context_chars = kb_payload["kb_max_context_chars"]
        kb_large_default_applied = bool(kb_payload.get("kb_large_default_applied", False))
        strict_mode = kb_mode == KB_MODE_STRICT
        if not kb_text.strip():
            self.last_kb_debug = {
                "kb_name": kb_name,
                "kb_mode": kb_mode,
                "retrieved_count": 0,
                "used_context": False,
                "reason": "kb_vacia",
                "query": message,
                "query_original": message,
                "query_expanded": message,
                "expansion_notes": [],
                "retrieval_method": "hybrid",
                "context_chars_budget": kb_max_context_chars,
                "context_chars_used": 0,
                "chunks_added_by_stitching": [],
                "stitching_added_count": 0,
                "chunks": [],
            }
            if strict_mode:
                return message, base_context, [], _KB_EMPTY_RESPONSE, []
            return message, base_context, [], None, []

        expected_hash = hashlib.sha256(kb_text.strip().encode("utf-8")).hexdigest()
        runtime_chunks_valid = bool(kb_chunks) and (not kb_hash or kb_hash == expected_hash)
        if kb_chunks and not runtime_chunks_valid:
            logger.info("KB chunks hash mismatch detected. Rebuilding chunks from current kb_text.")
        base_chunks = kb_chunks if runtime_chunks_valid else parse_policy(kb_text)
        chunks = self._prefix_chunk_sources(kb_name, base_chunks)
        if not chunks:
            self.last_kb_debug = {
                "kb_name": kb_name,
                "kb_mode": kb_mode,
                "retrieved_count": 0,
                "used_context": False,
                "reason": "sin_chunks",
                "query": message,
                "query_original": message,
                "query_expanded": message,
                "expansion_notes": [],
                "retrieval_method": "hybrid",
                "context_chars_budget": kb_max_context_chars,
                "context_chars_used": 0,
                "chunks_added_by_stitching": [],
                "stitching_added_count": 0,
                "chunks": [],
            }
            if strict_mode:
                return message, base_context, [], _KB_EMPTY_RESPONSE, []
            return message, base_context, [], None, []

        index = self._resolve_kb_index(
            kb_text,
            kb_hash,
            kb_index,
            chunks,
            kb_updated_at=kb_updated_at,
        )
        retrieval_result = retrieve(
            message,
            index,
            chunks,
            k=kb_top_k,
            kb_name=kb_name,
            min_score=kb_min_score,
            max_context_chars=kb_max_context_chars,
        )
        self._log_kb_retrieval(kb_name, retrieval_result)
        policy_debug = get_policy_kb_debug()
        query_original = str(policy_debug.get("query_original", message))
        query_expanded = str(policy_debug.get("query_expanded", message))
        expansion_notes = list(policy_debug.get("expansion_notes", []))
        retrieval_method = str(policy_debug.get("retrieval_method", "hybrid"))
        chunks_final = self._limit_context_chunks(retrieval_result, kb_max_context_chars)
        debug_chunks = self._build_debug_chunks(chunks_final)
        stitched_debug_chunks = self._normalize_debug_chunks(
            policy_debug.get("chunks_added_by_stitching", [])
        )
        context_chars_used = sum(len(str(chunk.get("text", "")).strip()) for chunk in chunks_final)
        if context_chars_used <= 0:
            context_chars_used = int(policy_debug.get("context_chars_used", 0) or 0)
        if not self._has_sufficient_evidence(chunks_final):
            self.last_kb_debug = {
                "kb_name": kb_name,
                "kb_mode": kb_mode,
                "retrieved_count": len(chunks_final),
                "used_context": False,
                "reason": "insufficient_evidence",
                "query": query_original,
                "query_original": query_original,
                "query_expanded": query_expanded,
                "expansion_notes": expansion_notes,
                "retrieval_method": retrieval_method,
                "chunks_total": int(policy_debug.get("chunks_total", len(chunks))),
                "context_chars_budget": kb_max_context_chars,
                "context_chars_used": context_chars_used,
                "chunks_added_by_stitching": stitched_debug_chunks,
                "stitching_added_count": int(policy_debug.get("stitching_added_count", 0) or 0),
                "kb_large_default_applied": kb_large_default_applied,
                "chunks": [],
            }
            if strict_mode:
                return message, base_context, [], _KB_EMPTY_RESPONSE, []
            return message, base_context, [], None, []

        sources = self._extract_sources(chunks_final, max_sources=kb_top_k)
        context_block = self._build_kb_context_block(kb_name, chunks_final)
        if strict_mode:
            guidance = (
                "Instrucciones obligatorias:\n"
                "- Responde SOLO usando la evidencia provista dentro de <context>.\n"
                "- Si la respuesta no aparece en la evidencia, responde exactamente: "
                '"No encuentro eso en el documento cargado. Proba con otras palabras o indicame el apartado/articulo."\n'
                "- Si te piden articulo o item, cita el articulo exacto.\n"
            )
        else:
            guidance = (
                "Instrucciones:\n"
                "- Usa primero la evidencia recuperada de la Base de Conocimiento.\n"
                "- Si la evidencia no alcanza, podes responder de forma general sin inventar datos del documento.\n"
                "- Si usas evidencia, menciona articulo, seccion o fragmento cuando corresponda.\n"
            )
        prepared_message = (
            f"<context>\n{context_block}\n</context>\n\n{guidance}\nPregunta del usuario: {message}"
        )
        prepared_context = dict(base_context)
        prepared_context["kb_strict_mode"] = strict_mode
        prepared_context["kb_mode"] = kb_mode
        prepared_context["kb_context_used"] = True
        prepared_context["kb_context_block"] = context_block
        prepared_context["kb_sources"] = sources
        prepared_context["kb_default_reply"] = _KB_EMPTY_RESPONSE
        prepared_context["kb_hash"] = kb_hash
        prepared_context["kb_top_k"] = kb_top_k
        prepared_context["kb_min_score"] = kb_min_score
        prepared_context["kb_max_context_chars"] = kb_max_context_chars
        prepared_context["kb_response_max_tokens"] = _GROQ_KB_MAX_TOKENS_DEFAULT
        prepared_context["kb_text_len"] = len(kb_text or "")
        prepared_context["kb_large_default_applied"] = kb_large_default_applied
        self.last_kb_debug = {
            "kb_name": kb_name,
            "kb_mode": kb_mode,
            "retrieved_count": len(chunks_final),
            "used_context": True,
            "reason": str(policy_debug.get("reason", "contexto_inyectado")),
            "query": query_original,
            "query_original": query_original,
            "query_expanded": query_expanded,
            "expansion_notes": expansion_notes,
            "retrieval_method": retrieval_method,
            "chunks_total": int(policy_debug.get("chunks_total", len(chunks))),
            "context_chars_budget": kb_max_context_chars,
            "context_chars_used": context_chars_used,
            "chunks_added_by_stitching": stitched_debug_chunks,
            "stitching_added_count": int(policy_debug.get("stitching_added_count", 0) or 0),
            "kb_large_default_applied": kb_large_default_applied,
            "chunks": debug_chunks,
        }
        return prepared_message, prepared_context, sources, None, chunks_final

    def _extract_kb_payload(self, user_context: Optional[Dict]) -> Optional[Dict[str, Any]]:
        if not user_context:
            return None
        has_kb_keys = "kb_text" in user_context or "kb_name" in user_context
        if not has_kb_keys:
            return None
        kb_text = str(user_context.get("kb_text", ""))
        kb_name = str(user_context.get("kb_name", "KB cargada")).strip() or "KB cargada"
        kb_mode = normalize_kb_mode(user_context.get("kb_mode", KB_MODE_GENERAL))
        kb_hash = str(user_context.get("kb_hash", "")).strip()
        kb_chunks = user_context.get("kb_chunks")
        kb_index = user_context.get("kb_index")
        kb_updated_at = str(user_context.get("kb_updated_at", "")).strip()
        kb_text_len = len(kb_text or "")
        kb_top_k = self._safe_int(
            user_context.get("kb_top_k", _KB_DEFAULT_TOP_K),
            default=_KB_DEFAULT_TOP_K,
            minimum=1,
            maximum=8,
        )
        kb_min_score = self._safe_float(
            user_context.get("kb_min_score", _KB_DEFAULT_MIN_SCORE),
            default=_KB_DEFAULT_MIN_SCORE,
            minimum=0.0,
            maximum=5.0,
        )
        kb_max_context_user_set = (
            "kb_max_context_chars" in user_context
            and user_context.get("kb_max_context_chars") not in (None, "")
        )
        max_context_default = _KB_DEFAULT_MAX_CONTEXT_CHARS
        kb_large_default_applied = False
        if kb_text_len > _KB_LARGE_TEXT_THRESHOLD and not kb_max_context_user_set:
            max_context_default = _KB_DEFAULT_MAX_CONTEXT_CHARS_LARGE
            kb_large_default_applied = True
        kb_max_context_chars = self._safe_int(
            user_context.get("kb_max_context_chars", max_context_default),
            default=max_context_default,
            minimum=800,
            maximum=20000,
        )
        return {
            "kb_text": kb_text,
            "kb_name": kb_name,
            "kb_mode": kb_mode,
            "kb_hash": kb_hash,
            "kb_chunks": kb_chunks if isinstance(kb_chunks, list) else [],
            "kb_index": kb_index if isinstance(kb_index, dict) else {},
            "kb_updated_at": kb_updated_at,
            "kb_top_k": kb_top_k,
            "kb_min_score": kb_min_score,
            "kb_max_context_chars": kb_max_context_chars,
            "kb_text_len": kb_text_len,
            "kb_large_default_applied": kb_large_default_applied,
        }

    def _resolve_kb_index(
        self,
        kb_text: str,
        kb_hash: str,
        runtime_index: Dict[str, Any],
        chunks: List[Dict[str, Any]],
        kb_updated_at: str = "",
    ) -> Dict[str, Any]:
        if self._is_index_compatible(runtime_index, chunks):
            expected_hash = hashlib.sha256(kb_text.strip().encode("utf-8")).hexdigest()
            if not kb_hash or kb_hash == expected_hash:
                return runtime_index
            logger.info(
                "KB index hash mismatch detected. Rebuilding index from current kb_text."
            )
        return build_bm25_index(
            chunks,
            kb_hash=kb_hash,
            kb_updated_at=kb_updated_at,
        )

    def _is_index_compatible(
        self, index: Dict[str, Any], chunks: List[Dict[str, Any]]
    ) -> bool:
        if not isinstance(index, dict):
            return False
        token_sets = index.get("token_sets")
        normalized = index.get("normalized_texts")
        token_freqs = index.get("token_freqs")
        if not isinstance(token_sets, (list, tuple)):
            return False
        if not isinstance(normalized, (list, tuple)):
            return False
        if not isinstance(token_freqs, (list, tuple)):
            return False
        return (
            len(token_sets) == len(chunks)
            and len(normalized) == len(chunks)
            and len(token_freqs) == len(chunks)
        )

    def _normalize_debug_chunks(self, rows: Any) -> List[Dict[str, Any]]:
        normalized_rows: List[Dict[str, Any]] = []
        if not isinstance(rows, list):
            return normalized_rows
        for row in rows:
            if not isinstance(row, dict):
                continue
            source = str(row.get("source") or row.get("source_label") or "").strip()
            normalized_rows.append(
                {
                    "chunk_id": row.get("chunk_id"),
                    "source": source,
                    "source_label": source,
                    "section": str(row.get("section", "")).strip(),
                    "score": float(row.get("score", 0.0)),
                    "overlap": int(row.get("overlap", 0)),
                    "match_type": str(row.get("match_type", "")),
                    "strong_match": bool(row.get("strong_match", False)),
                    "added_by_stitching": bool(row.get("added_by_stitching", False)),
                    "stitch_anchor_chunk_id": row.get("stitch_anchor_chunk_id"),
                    "snippet": str(row.get("snippet", "")),
                }
            )
        return normalized_rows

    def _build_debug_chunks(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        rows: List[Dict[str, Any]] = []
        for chunk in chunks:
            source = str(chunk.get("source_label") or chunk.get("source") or "").strip()
            text = re.sub(r"\s+", " ", str(chunk.get("text", "")).strip())
            rows.append(
                {
                    "chunk_id": chunk.get("chunk_id"),
                    "source": source,
                    "source_label": source,
                    "section": str(chunk.get("section_id", "")).strip(),
                    "score": round(float(chunk.get("score", 0.0)), 4),
                    "overlap": int(chunk.get("overlap", 0)),
                    "match_type": str(chunk.get("match_type", "")),
                    "strong_match": bool(chunk.get("strong_match", False)),
                    "added_by_stitching": bool(chunk.get("added_by_stitching", False)),
                    "stitch_anchor_chunk_id": chunk.get("stitch_anchor_chunk_id"),
                    "score_components": dict(chunk.get("score_components", {})),
                    "snippet": text[:220],
                }
            )
        return rows

    def _prefix_chunk_sources(
        self, kb_name: str, chunks: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        prefixed_chunks: List[Dict[str, Any]] = []
        for idx, chunk in enumerate(chunks, start=1):
            source = str(chunk.get("source_label", "")).strip() or f"Chunk {idx}"
            prefixed = dict(chunk)
            prefixed["chunk_id"] = int(chunk.get("chunk_id") or idx)
            prefix = f"{kb_name} | "
            prefixed["source_label"] = (
                source if source.startswith(prefix) else f"{prefix}{source}"
            )
            prefixed["source"] = prefixed["source_label"]
            prefixed_chunks.append(prefixed)
        return prefixed_chunks

    def _has_sufficient_evidence(self, retrieved_chunks: List[Dict[str, Any]]) -> bool:
        if not retrieved_chunks:
            return False
        ranked = sorted(
            retrieved_chunks,
            key=lambda chunk: float(chunk.get("score", 0.0)),
            reverse=True,
        )
        top_score = float(ranked[0].get("score", 0.0))
        combined_score = sum(float(chunk.get("score", 0.0)) for chunk in ranked[:2])
        has_strong_match = any(bool(chunk.get("strong_match", False)) for chunk in ranked)
        has_stitched_context = any(bool(chunk.get("added_by_stitching", False)) for chunk in ranked)
        has_heading_or_exact = any(
            ("heading" in str(chunk.get("match_type", "")).lower())
            or ("exact" in str(chunk.get("match_type", "")).lower())
            for chunk in ranked
        )
        if has_heading_or_exact and top_score >= 0.18:
            return True
        if has_stitched_context and top_score >= 0.16:
            return True
        if has_strong_match and top_score >= 0.20:
            return True
        if combined_score >= 0.85:
            return True
        return top_score >= 0.58

    def _log_kb_retrieval(self, kb_name: str, retrieved_chunks: List[Dict[str, Any]]) -> None:
        chunk_refs = []
        for chunk in retrieved_chunks:
            chunk_id = chunk.get("chunk_id", "?")
            source = chunk.get("source_label", "")
            score = float(chunk.get("score", 0.0))
            match_type = str(chunk.get("match_type", ""))
            chunk_refs.append(f"{chunk_id}:{source}:{score:.3f}:{match_type}")
        logger.info(
            "KB retrieval | kb=%s | retrieved=%s | refs=%s",
            kb_name,
            len(retrieved_chunks),
            chunk_refs,
        )

    def _build_kb_context_block(self, kb_name: str, retrieved_chunks: List[Dict[str, Any]]) -> str:
        lines = [f"Base de Conocimiento: {kb_name}", "Evidencia recuperada:"]
        for idx, chunk in enumerate(retrieved_chunks, start=1):
            source = chunk.get("source_label") or f"Fragmento {idx}"
            text = str(chunk.get("text", "")).strip()
            lines.append(f"[{idx}] Fuente: {source}")
            lines.append(text)
        return "\n".join(lines)

    def _extract_sources(
        self,
        retrieved_chunks: List[Dict[str, Any]],
        max_sources: int = 4,
    ) -> list[str]:
        seen = set()
        ordered_sources: list[str] = []
        limit = max(1, int(max_sources))
        for chunk in retrieved_chunks:
            source = str(chunk.get("source_label", "")).strip()
            if not source or source in seen:
                continue
            seen.add(source)
            ordered_sources.append(source)
            if len(ordered_sources) >= limit:
                break
        return ordered_sources

    def _append_sources(self, response: str, sources: List[str]) -> str:
        if not sources:
            return response
        lines = response.rstrip().splitlines()
        if lines and lines[-1].strip().lower().startswith("fuentes:"):
            lines = lines[:-1]
        clean_response = "\n".join(lines).rstrip()
        sources_text = ", ".join(sources)
        return f"{clean_response}\n\nFuentes: {sources_text}"

    def _build_demo_kb_answer(
        self, retrieved_chunks: List[Dict[str, Any]], sources: List[str]
    ) -> str:
        if not retrieved_chunks:
            return _KB_EMPTY_RESPONSE
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
            full_response = ""
            for chunk in stream:
                full_response += chunk
                yield chunk
            if re.search(r"(^|\n)\s*Fuentes\s*:", full_response, flags=re.IGNORECASE):
                return
            yield f"\n\nFuentes: {', '.join(sources)}"

        return generator()

    def _limit_context_chunks(
        self,
        chunks: List[Dict[str, Any]],
        max_context_chars: int,
    ) -> List[Dict[str, Any]]:
        if not chunks:
            return []
        char_budget = max(300, int(max_context_chars))
        used = 0
        limited: List[Dict[str, Any]] = []
        for chunk in chunks:
            text = str(chunk.get("text", "")).strip()
            if not text:
                continue
            remaining = char_budget - used
            if remaining <= 0:
                break
            if len(text) <= remaining:
                limited.append(chunk)
                used += len(text)
                continue
            if not limited:
                clipped_text = self._truncate_at_sentence_boundary(text, max(180, remaining))
                if clipped_text:
                    clipped = dict(chunk)
                    clipped["text"] = clipped_text
                    limited.append(clipped)
            break
        return limited if limited else chunks[:1]

    def _truncate_at_sentence_boundary(self, text: str, limit: int) -> str:
        content = str(text or "").strip()
        if not content:
            return ""
        if len(content) <= limit:
            return content
        snippet = content[:limit]
        sentence_boundary = max(
            snippet.rfind(". "),
            snippet.rfind("! "),
            snippet.rfind("? "),
            snippet.rfind(".\n"),
            snippet.rfind("!\n"),
            snippet.rfind("?\n"),
        )
        if sentence_boundary >= 120:
            return snippet[: sentence_boundary + 1].strip()
        word_boundary = snippet.rfind(" ")
        if word_boundary >= 120:
            return snippet[:word_boundary].strip()
        return snippet.strip()

    def _safe_int(self, value: Any, default: int, minimum: int, maximum: int) -> int:
        try:
            parsed = int(value)
        except (TypeError, ValueError):
            parsed = default
        return max(minimum, min(maximum, parsed))

    def _safe_float(
        self,
        value: Any,
        default: float,
        minimum: float,
        maximum: float,
    ) -> float:
        try:
            parsed = float(value)
        except (TypeError, ValueError):
            parsed = default
        return max(minimum, min(maximum, parsed))

    def _single_chunk_stream(self, message: str) -> Iterator[str]:
        def generator() -> Iterator[str]:
            yield message

        return generator()

    def get_last_kb_debug(self) -> Dict[str, Any]:
        return dict(self.last_kb_debug)
    
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
