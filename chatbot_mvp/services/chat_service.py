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
import unicodedata
from typing import Any, Dict, List, Optional, Protocol, Iterator
from abc import ABC, abstractmethod

from chatbot_mvp.config.settings import get_runtime_ai_provider
from chatbot_mvp.knowledge import (
    KB_MODE_GENERAL,
    KB_MODE_STRICT,
    build_bm25_index,
    get_last_kb_debug as get_policy_kb_debug,
    infer_primary_entity,
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
_KB_GENERAL_NOTICE = "El documento cargado no menciona esto."
_KB_GENERAL_PROVIDER_INSTRUCTION = (
    "Nota: el documento cargado no menciona esta informacion; responde con conocimiento general "
    "sin atribuirla al documento ni a Securion. No uses frases sobre falta de acceso externo."
)
_KB_ORG_SPECIFIC_PREFIX = (
    "No encuentro esto en el documento cargado, asi que no puedo confirmar la politica interna."
)
_KB_ORG_SPECIFIC_FOLLOWUP = (
    "Si queres, subi el documento o el fragmento del apartado y lo reviso."
)
_KB_ORG_SPECIFIC_GUIDE = (
    "Guia general (no verificada por el documento):\n"
    "- Defini por escrito alcance, responsables y excepciones.\n"
    "- Establece criterios de cumplimiento y controles trazables.\n"
    "- Inclui un canal de consultas y actualizacion periodica.\n"
    "- Registra comunicacion, capacitacion y evidencias de aplicacion."
)
_KB_DEFAULT_TOP_K = 4
_KB_DEFAULT_MIN_SCORE = 0.0
_KB_DEFAULT_MAX_CONTEXT_CHARS = 3200
_ORG_SPECIFIC_PHRASES = (
    "en la empresa",
    "en securion",
    "nuestra empresa",
    "politica interna",
    "protocolo",
    "codigo de conducta",
    "regalos de clientes",
    "rrhh",
    "compliance",
    "area legal",
    "manual interno",
)
_ORG_POLICY_WORDS = (
    "politica",
    "protocolo",
    "interna",
    "interno",
    "procedimiento",
    "codigo",
    "conducta",
    "rrhh",
    "compliance",
    "regalos",
)
_GENERIC_QUERY_TERMS = {
    "politica",
    "politicas",
    "procedimiento",
    "procedimientos",
    "empresa",
    "empresas",
    "interna",
    "interno",
    "documento",
    "info",
    "informacion",
    "protocolo",
    "codigo",
    "conducta",
    "manual",
}
_QUERY_STOPWORDS = {
    "a",
    "al",
    "como",
    "con",
    "cual",
    "cuales",
    "de",
    "del",
    "el",
    "en",
    "es",
    "esta",
    "este",
    "hay",
    "la",
    "las",
    "lo",
    "los",
    "para",
    "por",
    "que",
    "se",
    "si",
    "sin",
    "sobre",
    "su",
    "sus",
    "un",
    "una",
    "y",
}
_ENTITY_SUFFIXES = ("corp", "inc", "ltd", "company", "co", "sa", "srl", "llc")
_ENTITY_EXCLUDED_TOKENS = {
    "cual",
    "que",
    "como",
    "politica",
    "interna",
    "protocolo",
    "codigo",
    "conducta",
    "regalos",
    "empresa",
}


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
            notice = str(prepared_user_context.get("kb_notice", "")).strip()
            if notice:
                response = self._sanitize_general_no_evidence_response(response)
            if notice:
                return self._prepend_notice(response, notice)
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
            notice = str(prepared_user_context.get("kb_notice", "")).strip()
            if notice:
                return self._stream_with_notice(stream, notice)
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
                "query_expanded": message,
                "intent": "",
                "tags": [],
                "chunks": [],
            }
            return message, base_context, [], None, []

        kb_text = kb_payload["kb_text"]
        kb_name = kb_payload["kb_name"]
        kb_mode = kb_payload["kb_mode"]
        kb_hash = kb_payload["kb_hash"]
        kb_chunks = kb_payload["kb_chunks"]
        kb_index = kb_payload["kb_index"]
        kb_primary_entity = kb_payload["kb_primary_entity"]
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
                "query_expanded": message,
                "intent": "",
                "tags": [],
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
        kb_primary_entity = kb_primary_entity or infer_primary_entity(kb_text)
        if not chunks:
            self.last_kb_debug = {
                "kb_name": kb_name,
                "kb_mode": kb_mode,
                "retrieved_count": 0,
                "used_context": False,
                "reason": "sin_chunks",
                "query": message,
                "query_expanded": message,
                "intent": "",
                "tags": [],
                "chunks": [],
            }
            if strict_mode:
                return message, base_context, [], _KB_EMPTY_RESPONSE, []
            return message, base_context, [], None, []

        index = self._resolve_kb_index(kb_text, kb_hash, kb_index, chunks)
        retrieved_chunks = retrieve(
            message,
            index,
            chunks,
            k=kb_top_k,
            kb_name=kb_name,
            min_score=kb_min_score,
        )
        self._log_kb_retrieval(kb_name, retrieved_chunks)
        policy_debug = get_policy_kb_debug()
        debug_chunks = self._normalize_debug_chunks(policy_debug.get("top_candidates", []))
        keyword_meta = self._extract_query_keywords(message)
        usable_chunks, gate_meta = self._filter_usable_evidence(
            retrieved_chunks,
            keyword_meta,
        )
        debug_chunks = self._enrich_debug_chunks(debug_chunks, gate_meta)
        org_specific = self.is_org_specific_query(message)
        query_entities = self._extract_query_entities(message)
        org_mismatch, mismatched_entities = self._detect_org_mismatch(
            kb_primary_entity,
            query_entities,
            org_specific,
        )

        if org_mismatch:
            mismatch_response = self._build_org_mismatch_response(
                kb_primary_entity=kb_primary_entity,
                mismatched_entities=mismatched_entities,
                evidence_chunks=usable_chunks,
                kb_top_k=kb_top_k,
            )
            self.last_kb_debug = {
                "kb_name": kb_name,
                "kb_mode": kb_mode,
                "retrieved_count": len(usable_chunks),
                "used_context": bool(usable_chunks),
                "reason": "org_mismatch",
                "query": str(policy_debug.get("query", message)),
                "query_expanded": str(policy_debug.get("query_expanded", message)),
                "intent": str(policy_debug.get("intent", "")),
                "tags": list(policy_debug.get("tags", [])),
                "chunks_total": int(policy_debug.get("chunks_total", len(chunks))),
                "min_score": float(policy_debug.get("min_score", kb_min_score)),
                "keyword_tokens": list(keyword_meta.get("keyword_tokens", [])),
                "keyword_required": int(keyword_meta.get("required_matches", 1)),
                "acronyms": list(keyword_meta.get("acronyms", [])),
                "query_entities": query_entities,
                "kb_primary_entity": kb_primary_entity,
                "org_mismatch": True,
                "mismatched_entities": mismatched_entities,
                "chunks": debug_chunks,
            }
            return message, base_context, [], mismatch_response, usable_chunks

        if not usable_chunks:
            intent = str(policy_debug.get("intent", ""))
            tags = list(policy_debug.get("tags", []))
            self.last_kb_debug = {
                "kb_name": kb_name,
                "kb_mode": kb_mode,
                "retrieved_count": len(retrieved_chunks),
                "used_context": False,
                "reason": str(gate_meta.get("reason", policy_debug.get("reason", "no_hits"))),
                "query": str(policy_debug.get("query", message)),
                "query_expanded": str(policy_debug.get("query_expanded", message)),
                "intent": intent,
                "tags": tags,
                "chunks_total": int(policy_debug.get("chunks_total", len(chunks))),
                "min_score": float(policy_debug.get("min_score", kb_min_score)),
                "keyword_tokens": list(keyword_meta.get("keyword_tokens", [])),
                "keyword_required": int(keyword_meta.get("required_matches", 1)),
                "acronyms": list(keyword_meta.get("acronyms", [])),
                "query_entities": query_entities,
                "kb_primary_entity": kb_primary_entity,
                "org_mismatch": False,
                "chunks": debug_chunks,
            }
            if strict_mode:
                return message, base_context, [], _KB_EMPTY_RESPONSE, retrieved_chunks
            if org_specific:
                fixed_response = self._build_org_specific_no_evidence_response()
                return message, base_context, [], fixed_response, retrieved_chunks

            prepared_context = dict(base_context)
            prepared_context["kb_notice"] = _KB_GENERAL_NOTICE
            prepared_context["kb_notice_required"] = True
            prepared_context["kb_notice_reason"] = "no_evidence_general"
            prepared_context["kb_notice_prompt"] = _KB_GENERAL_PROVIDER_INSTRUCTION
            prompt_with_notice = (
                f"{_KB_GENERAL_PROVIDER_INSTRUCTION}\n\n"
                f"Pregunta del usuario: {message}"
            )
            return prompt_with_notice, prepared_context, [], None, retrieved_chunks

        context_chunks = self._limit_context_chunks(usable_chunks, kb_max_context_chars)
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
        prepared_context["kb_primary_entity"] = kb_primary_entity
        self.last_kb_debug = {
            "kb_name": kb_name,
            "kb_mode": kb_mode,
            "retrieved_count": len(context_chunks),
            "used_context": True,
            "reason": str(policy_debug.get("reason", "contexto_inyectado")),
            "query": str(policy_debug.get("query", message)),
            "query_expanded": str(policy_debug.get("query_expanded", message)),
            "intent": str(policy_debug.get("intent", "")),
            "tags": list(policy_debug.get("tags", [])),
            "chunks_total": int(policy_debug.get("chunks_total", len(chunks))),
            "min_score": float(policy_debug.get("min_score", kb_min_score)),
            "keyword_tokens": list(keyword_meta.get("keyword_tokens", [])),
            "keyword_required": int(keyword_meta.get("required_matches", 1)),
            "acronyms": list(keyword_meta.get("acronyms", [])),
            "query_entities": query_entities,
            "kb_primary_entity": kb_primary_entity,
            "org_mismatch": False,
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
        kb_primary_entity = str(user_context.get("kb_primary_entity", "")).strip()
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
            maximum=10.0,
        )
        kb_max_context_chars = self._safe_int(
            user_context.get("kb_max_context_chars", _KB_DEFAULT_MAX_CONTEXT_CHARS),
            default=_KB_DEFAULT_MAX_CONTEXT_CHARS,
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
            "kb_primary_entity": kb_primary_entity,
            "kb_top_k": kb_top_k,
            "kb_min_score": kb_min_score,
            "kb_max_context_chars": kb_max_context_chars,
        }

    def _resolve_kb_index(
        self,
        kb_text: str,
        kb_hash: str,
        runtime_index: Dict[str, Any],
        chunks: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        if self._is_index_compatible(runtime_index, chunks):
            expected_hash = hashlib.sha256(kb_text.strip().encode("utf-8")).hexdigest()
            if not kb_hash or kb_hash == expected_hash:
                return runtime_index
            logger.info(
                "KB index hash mismatch detected. Rebuilding index from current kb_text."
            )
        return build_bm25_index(chunks)

    def _is_index_compatible(
        self, index: Dict[str, Any], chunks: List[Dict[str, Any]]
    ) -> bool:
        if not isinstance(index, dict):
            return False
        token_sets = index.get("token_sets")
        normalized = index.get("normalized_texts")
        if not isinstance(token_sets, (list, tuple)):
            return False
        if not isinstance(normalized, (list, tuple)):
            return False
        return len(token_sets) == len(chunks) and len(normalized) == len(chunks)

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
                    "score": float(row.get("score", 0.0)),
                    "overlap": int(row.get("overlap", 0)),
                    "match_type": str(row.get("match_type", "")),
                    "section": str(row.get("section", "")),
                    "preview": str(row.get("preview", row.get("snippet", ""))),
                    "snippet": str(row.get("snippet", "")),
                    "usable": bool(row.get("usable", False)),
                    "matched_keywords": list(row.get("matched_keywords", [])),
                    "matched_acronyms": list(row.get("matched_acronyms", [])),
                }
            )
        return normalized_rows

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

    def _strip_accents(self, value: str) -> str:
        normalized = unicodedata.normalize("NFD", value)
        return "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")

    def _normalize_for_match(self, text: str) -> str:
        lowered = self._strip_accents(str(text or "").lower())
        lowered = re.sub(r"[^\w\s]", " ", lowered)
        lowered = re.sub(r"\s+", " ", lowered).strip()
        return lowered

    def _extract_query_keywords(self, query: str) -> Dict[str, Any]:
        query_text = str(query or "")
        normalized = self._normalize_for_match(query_text)
        acronym_tokens: List[str] = []
        for raw in re.findall(r"\b[A-Z]{2,6}\b", query_text):
            acronym = raw.strip().lower()
            if acronym and acronym not in acronym_tokens:
                acronym_tokens.append(acronym)
        keywords: List[str] = []
        for token in re.findall(r"[a-z0-9]+", normalized):
            if len(token) < 3:
                continue
            if token in _QUERY_STOPWORDS:
                continue
            if token in _GENERIC_QUERY_TERMS:
                continue
            if token not in keywords:
                keywords.append(token)
        for acronym in acronym_tokens:
            if acronym not in keywords:
                keywords.append(acronym)
        required_matches = 2 if len(keywords) >= 5 else 1
        return {
            "keyword_tokens": keywords,
            "acronyms": acronym_tokens,
            "required_matches": required_matches,
        }

    def _filter_usable_evidence(
        self,
        retrieved_chunks: List[Dict[str, Any]],
        keyword_meta: Dict[str, Any],
    ) -> tuple[List[Dict[str, Any]], Dict[str, Any]]:
        if not retrieved_chunks:
            return [], {"reason": "no_retrieved_chunks", "by_chunk": {}}

        keyword_tokens = list(keyword_meta.get("keyword_tokens", []))
        acronyms = list(keyword_meta.get("acronyms", []))
        required_matches = max(1, int(keyword_meta.get("required_matches", 1)))
        by_chunk: Dict[Any, Dict[str, Any]] = {}
        usable_chunks: List[Dict[str, Any]] = []
        if not keyword_tokens:
            for chunk in retrieved_chunks:
                chunk_id = chunk.get("chunk_id")
                by_chunk[chunk_id] = {
                    "usable": False,
                    "matched_keywords": [],
                    "matched_acronyms": [],
                    "required_matches": required_matches,
                }
            return [], {"reason": "no_query_keywords", "by_chunk": by_chunk}

        for chunk in retrieved_chunks:
            chunk_text = str(chunk.get("text", ""))
            normalized_text = self._normalize_for_match(chunk_text)
            chunk_tokens = set(re.findall(r"[a-z0-9]+", normalized_text))
            matched_keywords = [
                token for token in keyword_tokens if token in chunk_tokens
            ]
            matched_acronyms = [
                acronym for acronym in acronyms if acronym in chunk_tokens
            ]
            acronym_ok = not acronyms or len(matched_acronyms) == len(acronyms)
            keyword_ok = len(matched_keywords) >= required_matches
            usable = bool(acronym_ok and keyword_ok)
            chunk_id = chunk.get("chunk_id")
            by_chunk[chunk_id] = {
                "usable": usable,
                "matched_keywords": matched_keywords,
                "matched_acronyms": matched_acronyms,
                "required_matches": required_matches,
            }
            if usable:
                enriched = dict(chunk)
                enriched["matched_keywords"] = matched_keywords
                enriched["matched_acronyms"] = matched_acronyms
                usable_chunks.append(enriched)

        if usable_chunks:
            return usable_chunks, {"reason": "keyword_gate_pass", "by_chunk": by_chunk}
        return [], {"reason": "keyword_gate_fail", "by_chunk": by_chunk}

    def _enrich_debug_chunks(
        self,
        debug_chunks: List[Dict[str, Any]],
        gate_meta: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        by_chunk = gate_meta.get("by_chunk", {})
        if not isinstance(by_chunk, dict):
            return debug_chunks
        enriched_rows: List[Dict[str, Any]] = []
        for row in debug_chunks:
            enriched = dict(row)
            chunk_id = row.get("chunk_id")
            gate_row = by_chunk.get(chunk_id, {})
            if isinstance(gate_row, dict) and gate_row:
                enriched["usable"] = bool(gate_row.get("usable", False))
                enriched["matched_keywords"] = list(
                    gate_row.get("matched_keywords", [])
                )
                enriched["matched_acronyms"] = list(
                    gate_row.get("matched_acronyms", [])
                )
            enriched_rows.append(enriched)
        return enriched_rows

    def _extract_query_entities(self, query: str) -> List[str]:
        text = str(query or "")
        entities: List[str] = []
        for match in re.finditer(
            r"\b([A-Z][A-Za-z0-9&.-]{1,}|[A-Z]{2,})\s+"
            r"(Corp|Inc|Ltd|Company|Co|SA|SRL|LLC)\b",
            text,
        ):
            entity = f"{match.group(1)} {match.group(2)}".strip()
            if entity not in entities:
                entities.append(entity)
        for token in re.findall(r"\b[A-Z]{2,10}\b", text):
            if token not in entities:
                entities.append(token)
        for match in re.finditer(
            r"\b[A-Z\u00c1\u00c9\u00cd\u00d3\u00da\u00d1]"
            r"[A-Za-z\u00c1\u00c9\u00cd\u00d3\u00da\u00d1\u00e1\u00e9\u00ed\u00f3\u00fa\u00f10-9_-]{3,}\b",
            text,
        ):
            if match.start() == 0:
                continue
            token = match.group(0).strip()
            normalized = self._normalize_entity_name(token)
            if normalized in _ENTITY_EXCLUDED_TOKENS:
                continue
            if token not in entities:
                entities.append(token)
        return entities

    def _normalize_entity_name(self, value: str) -> str:
        normalized = self._normalize_for_match(value)
        parts = [part for part in normalized.split(" ") if part]
        if not parts:
            return ""
        if len(parts) >= 2 and parts[-1] in _ENTITY_SUFFIXES:
            parts = parts[:-1]
        return " ".join(parts)

    def _detect_org_mismatch(
        self,
        kb_primary_entity: str,
        query_entities: List[str],
        org_specific: bool,
    ) -> tuple[bool, List[str]]:
        if not org_specific:
            return False, []
        primary_normalized = self._normalize_entity_name(kb_primary_entity)
        if not primary_normalized:
            return False, []
        mismatches: List[str] = []
        for entity in query_entities:
            entity_normalized = self._normalize_entity_name(entity)
            if not entity_normalized:
                continue
            if entity_normalized == primary_normalized:
                continue
            if entity not in mismatches:
                mismatches.append(entity)
        return bool(mismatches), mismatches

    def _build_org_mismatch_response(
        self,
        kb_primary_entity: str,
        mismatched_entities: List[str],
        evidence_chunks: List[Dict[str, Any]],
        kb_top_k: int,
    ) -> str:
        primary = kb_primary_entity or "el documento cargado"
        target = mismatched_entities[0] if mismatched_entities else "esa organizacion"
        response = (
            f"El documento cargado corresponde a {primary}. "
            f"No puedo confirmar politicas internas de {target} porque no estan en el documento."
        )
        if not evidence_chunks:
            followup = (
                "\n\nSi queres, subi el documento o el fragmento de "
                f"{target} y lo reviso."
            )
            return response + followup
        limited = self._limit_context_chunks(evidence_chunks, max_context_chars=900)
        excerpt_source = limited[0]
        text = re.sub(r"\s+", " ", str(excerpt_source.get("text", "")).strip())
        excerpt = text[:360] + ("..." if len(text) > 360 else "")
        response = (
            f"{response}\n\nLo que si dice el documento de {primary} sobre este tema:\n"
            f"- {excerpt}"
        )
        sources = self._extract_sources(limited, max_sources=kb_top_k)
        return self._append_sources(response, sources)

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
        clean_response = re.sub(
            r"(?:\n\s*)?Fuentes:\s*.+$",
            "",
            response.rstrip(),
            flags=re.IGNORECASE | re.DOTALL,
        ).rstrip()
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

    def _prepend_notice(self, response: str, notice: str) -> str:
        clean_notice = notice.strip()
        clean_response = response.strip()
        if not clean_notice:
            return clean_response
        if clean_response.lower().startswith(clean_notice.lower()):
            return clean_response
        if not clean_response:
            return clean_notice
        return f"{clean_notice}\n\nRespuesta general: {clean_response}"

    def _sanitize_general_no_evidence_response(self, response: str) -> str:
        clean = str(response or "")
        blocked_patterns = [
            r"(?i)\bno (?:tengo|cuento con) acceso a (?:internet|informacion externa|datos externos)\b\.?",
            r"(?i)\bno puedo acceder a (?:informacion en tiempo real|fuentes externas)\b\.?",
        ]
        for pattern in blocked_patterns:
            clean = re.sub(pattern, "", clean)
        clean = re.sub(r"\n{3,}", "\n\n", clean).strip()
        return clean or "No tengo una respuesta general util con el contexto actual."

    def _stream_with_notice(
        self,
        stream: Iterator[str],
        notice: str,
    ) -> Iterator[str]:
        def generator() -> Iterator[str]:
            chunks: List[str] = []
            for chunk in stream:
                chunks.append(chunk)
            clean_response = self._sanitize_general_no_evidence_response("".join(chunks))
            yield notice.strip() + "\n\nRespuesta general: " + clean_response

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
            clipped = dict(chunk)
            clipped["text"] = text[: max(120, remaining)].rstrip() + "..."
            limited.append(clipped)
            break
        return limited if limited else chunks[:1]

    def _build_org_specific_no_evidence_response(self) -> str:
        return (
            f"{_KB_ORG_SPECIFIC_PREFIX}\n\n"
            f"{_KB_ORG_SPECIFIC_FOLLOWUP}\n\n"
            f"{_KB_ORG_SPECIFIC_GUIDE}"
        )

    def is_org_specific_query(self, query: str) -> bool:
        normalized_query = self._normalize_query(query)
        if any(phrase in normalized_query for phrase in _ORG_SPECIFIC_PHRASES):
            return True
        has_policy_word = self._contains_policy_word(normalized_query)
        if has_policy_word and self._has_quoted_phrase(query):
            return True
        if has_policy_word and self._has_non_initial_proper_token(query):
            return True
        return False

    def _normalize_query(self, query: str) -> str:
        lowered = str(query or "").lower()
        return re.sub(r"\s+", " ", lowered).strip()

    def _contains_policy_word(self, normalized_query: str) -> bool:
        return any(term in normalized_query for term in _ORG_POLICY_WORDS)

    def _has_quoted_phrase(self, query: str) -> bool:
        return bool(re.search(r"['\"][^'\"]+['\"]", str(query or "")))

    def _has_non_initial_proper_token(self, query: str) -> bool:
        text = str(query or "")
        matches = re.finditer(r"\b[A-ZÁÉÍÓÚÑ][A-Za-zÁÉÍÓÚÑáéíóúñ0-9_-]{2,}\b", text)
        for match in matches:
            if match.start() > 0:
                return True
        return False

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
