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
from chatbot_mvp.knowledge import (
    KB_DEFAULT_MAX_CONTEXT_CHARS,
    KB_DEFAULT_MIN_SCORE,
    KB_DEFAULT_TOP_K,
    KB_MODE_GENERAL,
    KB_MODE_STRICT,
    build_kb_index,
    get_last_kb_debug as get_policy_kb_debug,
    normalize_kb_mode,
    retrieve_evidence,
)
from chatbot_mvp.services.openai_client import AIClientError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

_KB_EMPTY_RESPONSE = (
    "No encuentro eso en el documento cargado. Si me indicas el apartado/titulo o pegas el fragmento, lo reviso."
)


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
                "chunks": [],
            }
            return message, base_context, [], None, []

        kb_text = kb_payload["kb_text"]
        kb_name = kb_payload["kb_name"]
        kb_mode = kb_payload["kb_mode"]
        kb_hash = kb_payload["kb_hash"]
        kb_top_k = kb_payload["kb_top_k"]
        kb_min_score = kb_payload["kb_min_score"]
        kb_max_context_chars = kb_payload["kb_max_context_chars"]
        strict_mode = kb_mode == KB_MODE_STRICT
        if not kb_text.strip():
            self.last_kb_debug = {
                "kb_name": kb_name,
                "kb_mode": kb_mode,
                "retrieved_count": 0,
                "used_context": False,
                "reason": "kb_vacia",
                "query": message,
                "chunks": [],
            }
            if strict_mode:
                return message, base_context, [], _KB_EMPTY_RESPONSE, []
            return message, base_context, [], None, []

        kb_bundle = self._resolve_kb_bundle(kb_payload)
        chunks = kb_bundle.get("chunks", [])
        index = kb_bundle.get("index", {})
        kb_hash = str(kb_bundle.get("kb_hash", kb_hash))
        if not chunks:
            self.last_kb_debug = {
                "kb_name": kb_name,
                "kb_mode": kb_mode,
                "retrieved_count": 0,
                "used_context": False,
                "reason": "sin_chunks",
                "query": message,
                "chunks": [],
            }
            if strict_mode:
                return message, base_context, [], _KB_EMPTY_RESPONSE, []
            return message, base_context, [], None, []

        retrieved_chunks = retrieve_evidence(
            query=message,
            index=index,
            top_k=kb_top_k,
            min_score=kb_min_score,
            kb_name=kb_name,
        )
        self._log_kb_retrieval(kb_name, retrieved_chunks)
        policy_debug = get_policy_kb_debug()
        debug_chunks = self._normalize_debug_chunks(policy_debug.get("top_candidates", []))
        if not retrieved_chunks:
            self.last_kb_debug = {
                "kb_name": kb_name,
                "kb_mode": kb_mode,
                "retrieved_count": len(retrieved_chunks),
                "used_context": False,
                "reason": str(policy_debug.get("reason", "no_hits")),
                "query": str(policy_debug.get("query", message)),
                "chunks_total": int(policy_debug.get("chunks_total", len(chunks))),
                "top_k": kb_top_k,
                "min_score": kb_min_score,
                "max_context_chars": kb_max_context_chars,
                "index_build_count": int(policy_debug.get("index_build_count", 0)),
                "chunks": debug_chunks,
            }
            if strict_mode:
                return message, base_context, [], _KB_EMPTY_RESPONSE, retrieved_chunks
            return message, base_context, [], None, retrieved_chunks

        context_chunks, context_truncated = self._select_context_chunks(
            retrieved_chunks, kb_max_context_chars
        )
        sources = self._extract_sources(context_chunks, max_sources=kb_top_k)
        context_block = self._build_kb_context_block(kb_name, context_chunks)
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
        prepared_context["kb_context_truncated"] = context_truncated
        prepared_context["kb_evidence_count"] = len(context_chunks)
        self.last_kb_debug = {
            "kb_name": kb_name,
            "kb_mode": kb_mode,
            "retrieved_count": len(context_chunks),
            "used_context": True,
            "reason": str(policy_debug.get("reason", "contexto_inyectado")),
            "query": str(policy_debug.get("query", message)),
            "chunks_total": int(policy_debug.get("chunks_total", len(chunks))),
            "top_k": kb_top_k,
            "min_score": kb_min_score,
            "max_context_chars": kb_max_context_chars,
            "context_truncated": context_truncated,
            "index_build_count": int(policy_debug.get("index_build_count", 0)),
            "chunks": debug_chunks,
        }
        return prepared_message, prepared_context, sources, None, context_chunks

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
        kb_top_k = self._coerce_positive_int(
            user_context.get("kb_top_k"),
            KB_DEFAULT_TOP_K,
            minimum=1,
            maximum=8,
        )
        kb_min_score = self._coerce_positive_float(
            user_context.get("kb_min_score"),
            KB_DEFAULT_MIN_SCORE,
            minimum=0.0,
            maximum=10.0,
        )
        kb_max_context_chars = self._coerce_positive_int(
            user_context.get("kb_max_context_chars"),
            KB_DEFAULT_MAX_CONTEXT_CHARS,
            minimum=300,
            maximum=12000,
        )
        return {
            "kb_text": kb_text,
            "kb_name": kb_name,
            "kb_mode": kb_mode,
            "kb_hash": kb_hash,
            "kb_updated_at": kb_updated_at,
            "kb_top_k": kb_top_k,
            "kb_min_score": kb_min_score,
            "kb_max_context_chars": kb_max_context_chars,
            "kb_chunks": kb_chunks if isinstance(kb_chunks, list) else [],
            "kb_index": kb_index if isinstance(kb_index, dict) else {},
        }

    def _resolve_kb_bundle(self, kb_payload: Dict[str, Any]) -> Dict[str, Any]:
        runtime_index = kb_payload.get("kb_index")
        runtime_chunks = kb_payload.get("kb_chunks")
        runtime_hash = str(kb_payload.get("kb_hash", "")).strip()
        if self._is_index_compatible(runtime_index, runtime_hash):
            index_chunks = runtime_index.get("chunks")
            if isinstance(index_chunks, list) and index_chunks:
                return {
                    "kb_hash": runtime_hash or str(runtime_index.get("kb_hash", "")),
                    "chunks": index_chunks,
                    "index": runtime_index,
                }
            if isinstance(runtime_chunks, list) and runtime_chunks:
                patched_index = dict(runtime_index)
                patched_index["chunks"] = runtime_chunks
                return {
                    "kb_hash": runtime_hash or str(runtime_index.get("kb_hash", "")),
                    "chunks": runtime_chunks,
                    "index": patched_index,
                }

        logger.info("KB cache miss. Rebuilding index bundle from KB text.")
        rebuilt = build_kb_index(
            text=kb_payload.get("kb_text", ""),
            kb_name=kb_payload.get("kb_name", "KB cargada"),
            kb_updated_at=kb_payload.get("kb_updated_at", ""),
        )
        return {
            "kb_hash": str(rebuilt.get("kb_hash", "")),
            "chunks": rebuilt.get("chunks", []),
            "index": rebuilt.get("index", {}),
        }

    def _is_index_compatible(
        self, index: Dict[str, Any], kb_hash: str = ""
    ) -> bool:
        if not isinstance(index, dict):
            return False
        required = ("tf_docs", "doc_len", "df", "avgdl")
        if any(key not in index for key in required):
            return False
        if not isinstance(index.get("tf_docs"), list):
            return False
        if not isinstance(index.get("doc_len"), list):
            return False
        if not isinstance(index.get("df"), dict):
            return False
        if kb_hash and index.get("kb_hash") and str(index.get("kb_hash")) != kb_hash:
            return False
        return True

    def _normalize_debug_chunks(self, rows: Any) -> List[Dict[str, Any]]:
        normalized_rows: List[Dict[str, Any]] = []
        if not isinstance(rows, list):
            return normalized_rows
        for row in rows:
            if not isinstance(row, dict):
                continue
            source = str(row.get("source") or row.get("source_label") or "").strip()
            preview = str(row.get("preview") or row.get("snippet") or "")
            section = str(row.get("section") or row.get("title") or "").strip()
            normalized_rows.append(
                {
                    "chunk_id": row.get("chunk_id"),
                    "source": source,
                    "source_label": source,
                    "score": float(row.get("score", 0.0)),
                    "overlap": int(row.get("overlap", 0)),
                    "match_type": str(row.get("match_type", "")),
                    "section": section,
                    "preview": preview,
                    "snippet": preview,
                }
            )
        return normalized_rows

    def _coerce_positive_int(
        self,
        value: Any,
        default: int,
        minimum: int,
        maximum: int,
    ) -> int:
        try:
            parsed = int(value)
        except (TypeError, ValueError):
            parsed = default
        return max(minimum, min(maximum, parsed))

    def _coerce_positive_float(
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

    def _select_context_chunks(
        self,
        retrieved_chunks: List[Dict[str, Any]],
        max_context_chars: int,
    ) -> tuple[List[Dict[str, Any]], bool]:
        if not retrieved_chunks:
            return [], False
        limit = max(300, int(max_context_chars))
        selected: List[Dict[str, Any]] = []
        used_chars = 0
        truncated = False

        for chunk in retrieved_chunks:
            text = str(chunk.get("text", "")).strip()
            if not text:
                continue
            remaining = limit - used_chars
            if remaining <= 0:
                truncated = True
                break
            if len(text) <= remaining:
                selected.append(chunk)
                used_chars += len(text)
                continue

            truncated = True
            # Keep at least one chunk even if the first evidence is larger than the limit.
            if not selected or remaining >= 120:
                trimmed_chunk = dict(chunk)
                trimmed_chunk["text"] = text[: max(40, remaining)].rstrip() + "..."
                selected.append(trimmed_chunk)
            break

        return selected, truncated

    def _build_kb_context_block(self, kb_name: str, retrieved_chunks: List[Dict[str, Any]]) -> str:
        lines = [f"Base de Conocimiento: {kb_name}", "Evidencia recuperada:"]
        for idx, chunk in enumerate(retrieved_chunks, start=1):
            source = chunk.get("source_label") or f"Fragmento {idx}"
            section = str(chunk.get("section", "")).strip()
            text = str(chunk.get("text", "")).strip()
            lines.append(f"[{idx}] Fuente: {source}")
            if section:
                lines.append(f"Seccion: {section}")
            lines.append(text)
        return "\n".join(lines)

    def _extract_sources(
        self,
        retrieved_chunks: List[Dict[str, Any]],
        max_sources: int = 8,
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
            for chunk in stream:
                yield chunk
            yield f"\n\nFuentes: {', '.join(sources)}"

        return generator()

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
