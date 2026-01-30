import hashlib
import logging
import threading
import time
from collections import OrderedDict
from typing import Any, Dict, List, Optional, Iterator

from chatbot_mvp.config.settings import get_env_value, sanitize_env_value
from chatbot_mvp.data.evaluation_context import build_evaluation_feedback_prompt

logger = logging.getLogger(__name__)

_GEMINI_LOCK = threading.Lock()
_NEXT_ALLOWED_AT = 0.0
_RATE_LIMIT_BACKOFF = 0.0
_LAST_RATE_LIMIT_LOG = 0.0
_COOLDOWN_UNTIL = 0.0
_COOLDOWN_REASON = ""
_LAST_COOLDOWN_LOG = 0.0
_CACHE: "OrderedDict[str, tuple[float, str]]" = OrderedDict()

# Env config (no secrets logged):
# - GEMINI_MIN_INTERVAL_SECONDS (default 1.0)
# - GEMINI_CACHE_TTL_SECONDS (default 20)
# - GEMINI_CACHE_MAX_SIZE (default 128)
# - GEMINI_MAX_BACKOFF_SECONDS (default 8)
# - GEMINI_COOLDOWN_SECONDS (default 30)
# - GEMINI_MAX_COOLDOWN_SECONDS (default 120)


def _get_env_float(name: str, default: float) -> float:
    raw = get_env_value(name, "")
    if raw == "":
        return default
    try:
        return float(raw.strip())
    except (TypeError, ValueError):
        return default


def _get_env_int(name: str, default: int) -> int:
    raw = get_env_value(name, "")
    if raw == "":
        return default
    try:
        return int(raw.strip())
    except (TypeError, ValueError):
        return default


def _make_cache_key(model: str, prompt: str) -> str:
    payload = f"{model}\n{prompt}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _cache_get(key: str, now: float) -> Optional[str]:
    ttl = _get_env_float("GEMINI_CACHE_TTL_SECONDS", 20.0)
    entry = _CACHE.get(key)
    if not entry:
        return None
    created_at, value = entry
    if now - created_at > ttl:
        _CACHE.pop(key, None)
        return None
    _CACHE.move_to_end(key)
    return value


def _cache_set(key: str, value: str, now: float) -> None:
    _CACHE[key] = (now, value)
    _CACHE.move_to_end(key)
    max_size = _get_env_int("GEMINI_CACHE_MAX_SIZE", 128)
    while len(_CACHE) > max_size:
        _CACHE.popitem(last=False)


def _respect_min_interval() -> None:
    global _NEXT_ALLOWED_AT
    min_interval = _get_env_float("GEMINI_MIN_INTERVAL_SECONDS", 1.0)
    now = time.monotonic()
    if now < _NEXT_ALLOWED_AT:
        time.sleep(_NEXT_ALLOWED_AT - now)
    _NEXT_ALLOWED_AT = time.monotonic() + max(0.0, min_interval)


def _rate_limit_backoff() -> float:
    global _NEXT_ALLOWED_AT, _RATE_LIMIT_BACKOFF, _LAST_RATE_LIMIT_LOG
    max_backoff = _get_env_float("GEMINI_MAX_BACKOFF_SECONDS", 8.0)
    if _RATE_LIMIT_BACKOFF <= 0:
        _RATE_LIMIT_BACKOFF = 2.0
    else:
        _RATE_LIMIT_BACKOFF = min(max_backoff, _RATE_LIMIT_BACKOFF * 2)
    now = time.monotonic()
    _NEXT_ALLOWED_AT = max(_NEXT_ALLOWED_AT, now + _RATE_LIMIT_BACKOFF)
    if now - _LAST_RATE_LIMIT_LOG > 1.0:
        logger.warning("Gemini rate limit hit, backing off %.0fs", _RATE_LIMIT_BACKOFF)
        _LAST_RATE_LIMIT_LOG = now
    time.sleep(_RATE_LIMIT_BACKOFF)
    return _RATE_LIMIT_BACKOFF


def _rate_limit_message(backoff_seconds: float) -> str:
    suggestions = [
        "Estoy recibiendo muchas solicitudes. Probá en %ss.",
        "Hay mucho tráfico ahora mismo. Intentá de nuevo en %ss.",
        "Estoy limitado por cuota momentáneamente. Reintentá en %ss.",
    ]
    idx = int(time.monotonic()) % len(suggestions)
    return suggestions[idx] % max(1, int(backoff_seconds))


def _extract_retry_after_seconds(exc: Exception) -> Optional[float]:
    for attr in ("response", "resp", "_response"):
        resp = getattr(exc, attr, None)
        headers = getattr(resp, "headers", None) if resp else None
        if headers:
            raw = headers.get("Retry-After") or headers.get("retry-after")
            if raw is None:
                continue
            try:
                return float(raw)
            except (TypeError, ValueError):
                return None
    return None


def _compute_cooldown_seconds(exc: Exception) -> float:
    base = _get_env_float("GEMINI_COOLDOWN_SECONDS", 30.0)
    max_cooldown = _get_env_float("GEMINI_MAX_COOLDOWN_SECONDS", 120.0)
    retry_after = _extract_retry_after_seconds(exc)
    if retry_after is not None:
        return min(max_cooldown, max(1.0, retry_after))
    return min(max_cooldown, max(1.0, base))


def _set_cooldown(seconds: float, reason: str = "rate_limit") -> None:
    global _COOLDOWN_UNTIL, _COOLDOWN_REASON, _LAST_COOLDOWN_LOG
    now = time.monotonic()
    _COOLDOWN_UNTIL = max(_COOLDOWN_UNTIL, now + seconds)
    _COOLDOWN_REASON = reason
    if now - _LAST_COOLDOWN_LOG > 1.0:
        logger.warning("Gemini rate limited: cooling down %ss", int(seconds))
        _LAST_COOLDOWN_LOG = now


def _cooldown_remaining() -> int:
    now = time.monotonic()
    remaining = int(_COOLDOWN_UNTIL - now)
    return max(0, remaining)


def get_gemini_api_key() -> str:
    api_key = get_env_value("GEMINI_API_KEY")
    if api_key:
        return api_key
    return get_env_value("GOOGLE_API_KEY")


# Import AIClientError from openai_client to maintain consistency
from chatbot_mvp.services.openai_client import AIClientError


class GeminiChatClient:
    """
    Google Gemini client following OpenAI interface pattern.
    
    Handles rate limits for free tier (5-15 RPM) and provides
    fallback to demo mode on API failures.
    """
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        api_key_value = sanitize_env_value(api_key) if isinstance(api_key, str) else ""
        self.api_key = api_key_value or get_gemini_api_key()
        model_value = sanitize_env_value(model) if isinstance(model, str) else ""
        self.model = model_value or get_env_value("GEMINI_MODEL", "gemini-2.0-flash")
        self.client = None
        self._initialized = False
        self.retry_count = 0
        
        if self.api_key:
            self._initialize_client()
    
    def _initialize_client(self) -> bool:
        """
        Initialize the Gemini client.
        
        Returns:
            True if initialization successful, False otherwise
        """
        if self._initialized:
            return True
            
        try:
            from google import genai
            self.client = genai.Client(api_key=self.api_key)
            self._initialized = True
            logger.info(f"Gemini client initialized successfully with model: {self.model}")
            return True
        except ImportError as exc:
            logger.error(f"Google GenAI SDK not installed: {exc}")
            raise AIClientError(f"SDK de Google GenAI no instalado: {exc}")
        except Exception as exc:
            logger.error(f"Failed to initialize Gemini client: {exc}")
            raise AIClientError(f"Error al inicializar cliente Gemini: {exc}")
    
    def generate_chat_response(
        self, 
        message: str, 
        conversation_history: List[Dict[str, str]],
        user_context: Optional[Dict] = None,
        max_tokens: int = 150,
        temperature: float = 0.7
    ) -> str:
        """
        Generate chat response using Gemini API.
        
        Args:
            message: Current user message
            conversation_history: Previous messages for context
            user_context: Optional user metadata
            max_tokens: Response length limit (token optimization)
            temperature: Response creativity (0.0-1.0)
            
        Returns:
            Generated response text or fallback message
            
        Raises:
            AIClientError: When API fails and fallback unavailable
        """
        if not self._initialized:
            raise AIClientError("Cliente Gemini no inicializado")
        
        try:
            # Build messages for API
            prompt = self._build_chat_prompt(
                message, conversation_history, user_context
            )
            
            # Generate response with retries
            return self._generate_text(
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            
        except Exception as exc:
            logger.error(f"Error generating Gemini response: {exc}")
            raise AIClientError(f"Error al generar respuesta: {exc}")

    def generate_chat_response_stream(
        self, 
        message: str, 
        conversation_history: List[Dict[str, str]],
        user_context: Optional[Dict] = None,
        max_tokens: int = 150,
        temperature: float = 0.7
    ) -> Iterator[str]:
        """
        Generate streaming chat response using Gemini API.
        
        Args:
            message: Current user message
            conversation_history: Previous messages for context
            user_context: Optional user metadata
            max_tokens: Response length limit
            temperature: Response creativity
            
        Yields:
            Chunks of generated response text
        """
        if not self._initialized:
            raise AIClientError("Cliente Gemini no inicializado")
            
        try:
            prompt = self._build_chat_prompt(
                message, conversation_history, user_context
            )
            
            # Note: Streaming doesn't use the simple cache/retry wrapper 
            # effectively without buffering, so we call client directly but 
            # should respect rate limits.
            
            with _GEMINI_LOCK:
                _respect_min_interval()
                
            stream = self.client.models.generate_content_stream(
                model=self.model,
                contents=prompt,
                config={
                    'max_output_tokens': max_tokens,
                    'temperature': temperature,
                }
            )
            
            for chunk in stream:
                if chunk.text:
                    # Split into words for smoother typing effect
                    words = chunk.text.split(' ')
                    for i, word in enumerate(words):
                        if i < len(words) - 1:
                            yield word + ' '
                        else:
                            yield word
                        time.sleep(0.02) # Small delay for natural feel
                    
        except Exception as exc:
            logger.error(f"Error generating Gemini stream: {exc}")
            # Map common errors to user friendly messages if possible
            yield f"Error al generar respuesta: {str(exc)}"
    
    def _build_chat_prompt(
        self, 
        message: str, 
        conversation_history: List[Dict[str, str]],
        user_context: Optional[Dict] = None
    ) -> str:
        """
        Build prompt for Gemini API from conversation history.
        
        Args:
            message: Current user message
            conversation_history: List of previous messages
            user_context: Optional user context information
            
        Returns:
            Formatted prompt string for Gemini API
        """
        # Start with system prompt
        prompt_parts = [self._build_system_prompt(user_context)]
        
        # Add conversation history (last 10 messages to avoid token limits)
        prompt_parts.append("\n\nConversación anterior:")
        recent_history = conversation_history[-10:]
        for msg in recent_history:
            role_name = "Usuario" if msg["role"] == "user" else "Asistente"
            prompt_parts.append(f"{role_name}: {msg['content']}")
        
        # Add current message
        prompt_parts.append(f"\nUsuario: {message}")
        prompt_parts.append("\nAsistente:")
        
        return "\n".join(prompt_parts)
    
    def _build_system_prompt(self, user_context: Optional[Dict] = None) -> str:
        """
        Build system prompt based on user context.
        
        Args:
            user_context: Optional user context information
            
        Returns:
            System prompt string
        """
        base_prompt = (
            "Eres un asistente útil y amigable que responde en español. "
            "Sé conciso pero informativo. Mantén un tono profesional pero cercano. "
            "Si no sabes algo, admítelo claramente."
        )
        
        if user_context:
            context_info = []
            if "demografia" in user_context:
                demografia = user_context["demografia"]
                if demografia.get("edad"):
                    context_info.append(f"Edad: {demografia['edad']}")
                if demografia.get("ocupacion"):
                    context_info.append(f"Ocupación: {demografia['ocupacion']}")
                if demografia.get("nivel_conocimiento_ia"):
                    context_info.append(f"Nivel conocimiento IA: {demografia['nivel_conocimiento_ia']}")
            
            if context_info:
                base_prompt += f"\n\nContexto del usuario:\n" + "\n".join(context_info)
        
        return base_prompt
    
    def _generate_with_retry(
        self, 
        prompt: str, 
        max_tokens: int, 
        temperature: float,
        max_retries: int = 3
    ) -> Dict:
        """
        Generate response with retry logic for rate limit handling.
        
        Args:
            prompt: Formatted prompt string
            max_tokens: Maximum response length
            temperature: Response creativity
            max_retries: Maximum retry attempts
            
        Returns:
            Gemini API response
        """
        global _RATE_LIMIT_BACKOFF
        for attempt in range(max_retries):
            with _GEMINI_LOCK:
                remaining = _cooldown_remaining()
            if remaining > 0:
                raise AIClientError(_rate_limit_message(remaining))
            try:
                self.retry_count = attempt
                with _GEMINI_LOCK:
                    _respect_min_interval()
                    response = self.client.models.generate_content(
                        model=self.model,
                        contents=prompt,
                        config={
                            'max_output_tokens': max_tokens,
                            'temperature': temperature,
                        }
                    )
                _RATE_LIMIT_BACKOFF = 0.0
                return response
                
            except Exception as exc:
                # Handle rate limit specifically for Gemini
                cooldown_seconds = self._handle_rate_limit(exc)
                if cooldown_seconds is not None:
                    raise AIClientError(_rate_limit_message(cooldown_seconds))
                elif attempt == max_retries - 1:
                    raise
                    
                # General exponential backoff for other errors
                wait_time = min(60, 2 ** attempt)  # Max 60s wait for Gemini strict limits
                logger.warning(f"Attempt {attempt + 1} failed, retrying in {wait_time}s: {exc}")
                time.sleep(wait_time)
    
    def _handle_rate_limit(self, response) -> Optional[float]:
        """
        Handle rate limit errors with backoff strategy for Gemini.
        
        Args:
            response: Error response from API
            
        Returns:
            Cooldown seconds if rate limited, None otherwise
        """
        error_str = str(response).lower()
        
        # Check for rate limit indicators
        if any(keyword in error_str for keyword in [
            "ratelimitexceeded", "rate limit", "too many requests", 
            "quota exceeded", "429"
        ]):
            cooldown_seconds = _compute_cooldown_seconds(response)
            with _GEMINI_LOCK:
                _set_cooldown(cooldown_seconds)
            self.retry_count += 1
            return cooldown_seconds
        
        return None
    
    def _extract_response_text(self, response: Dict) -> str:
        """
        Extract text from Gemini response.
        
        Args:
            response: Gemini API response
            
        Returns:
            Extracted text content
        """
        try:
            # Gemini response structure: response.text
            if hasattr(response, 'text') and response.text:
                return response.text.strip()
            
            # Alternative response structure
            if hasattr(response, 'candidates') and response.candidates:
                content = response.candidates[0].content
                if hasattr(content, 'parts') and content.parts:
                    return content.parts[0].text.strip()
            
            logger.error("Failed to extract response text from Gemini response")
            raise AIClientError("Respuesta vacía o malformed")
            
        except (AttributeError, IndexError, KeyError) as exc:
            logger.error(f"Failed to extract response text: {exc}")
            raise AIClientError("Respuesta vacía o malformed")
    
    def _generate_text(self, prompt: str, max_tokens: int, temperature: float) -> str:
        cache_key = _make_cache_key(self.model, prompt)
        now = time.monotonic()
        with _GEMINI_LOCK:
            remaining = _cooldown_remaining()
            if remaining > 0:
                raise AIClientError(_rate_limit_message(remaining))
            cached = _cache_get(cache_key, now)
        if cached is not None:
            logger.info("Gemini cache hit")
            return cached

        response = self._generate_with_retry(
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        text = self._extract_response_text(response)
        with _GEMINI_LOCK:
            _cache_set(cache_key, text, time.monotonic())
        return text

    def generate_evaluation(self, answers: Dict[str, Any]) -> str:
        """
        Generate evaluation feedback based on questionnaire answers.
        
        Args:
            answers: Dictionary of questionnaire answers
            
        Returns:
            Generated evaluation text
        """
        if not self._initialized:
            raise AIClientError("Cliente Gemini no inicializado")
        
        try:
            prompt = self._build_evaluation_prompt(answers)
            return self._generate_text(prompt, max_tokens=800, temperature=0.7)
        except Exception as exc:
            logger.error(f"Error generating Gemini evaluation: {exc}")
            raise AIClientError(f"Error al generar evaluación: {exc}")

    def _build_evaluation_prompt(self, answers: Dict[str, Any]) -> str:
        """
        Build prompt for evaluation feedback based on answers.
        
        Args:
            answers: User answers dictionary
            
        Returns:
            Formatted prompt string
        """
        lines = [
            "Eres un evaluador experto en ética e inteligencia artificial. "
            "Da una evaluación personalizada, completa y útil en español basada en las siguientes respuestas a un cuestionario de ética.",
            "\nRespuestas del usuario:"
        ]
        
        for key, value in answers.items():
            if value:
                # Convert list values (for multi-choice) to string
                val_str = ", ".join(value) if isinstance(value, list) else str(value)
                lines.append(f"- {key}: {val_str}")
        
        lines.append(
            "\nPor favor entrega un análisis detallado (aprox 150-200 palabras) con un tono profesional, claro y accionable. "
            "Enfócate en consejos prácticos basados en sus respuestas específicas. "
            "Usa parrafos claros."
        )
        return "\n".join(lines)

    def generate_evaluation_feedback(self, evaluation: Dict[str, Any]) -> str:
        """
        Generate evaluation feedback based on scored results and answers.
        
        Args:
            evaluation: Structured evaluation payload (summary + questions)
            
        Returns:
            Generated evaluation text
        """
        if not self._initialized:
            raise AIClientError("Cliente Gemini no inicializado")
        
        try:
            prompt = build_evaluation_feedback_prompt(evaluation)
            return self._generate_text(prompt, max_tokens=800, temperature=0.7)
        except Exception as exc:
            logger.error(f"Error generating Gemini evaluation feedback: {exc}")
            raise AIClientError(f"Error al generar evaluación: {exc}")


    def is_available(self) -> bool:
        """
        Check if the client is available.
        
        Returns:
            True if client is initialized and ready
        """
        return self._initialized and self.client is not None


# Factory function for creating Gemini clients
def create_gemini_client() -> Optional[GeminiChatClient]:
    """
    Factory function to create a Gemini chat client.
    
    Returns:
        GeminiChatClient instance if configured, None otherwise
    """
    try:
        client = GeminiChatClient()
        return client if client.is_available() else None
    except Exception as exc:
        logger.warning(f"Failed to create Gemini chat client: {exc}")
        return None

def generate_evaluation(answers: Dict[str, Any]) -> str:
    """
    Top-level helper to generate evaluation feedback.
    
    Args:
        answers: Dictionary of questionnaire answers
        
    Returns:
        Evaluation text or fallback message
    """
    client = create_gemini_client()
    if not client:
        logger.warning("Gemini client not available for evaluation.")
        return "Modo demo: No se pudo conectar con Gemini para evaluación en tiempo real."
    
    try:
        return client.generate_evaluation(answers)
    except Exception as exc:
        logger.error(f"Generate evaluation helper failed: {exc}")
        return "Error al generar evaluación con Gemini. Por favor intenta de nuevo."


def generate_evaluation_feedback(evaluation: Dict[str, Any]) -> str:
    """
    Top-level helper to generate evaluation feedback with summary + Q/A.
    
    Args:
        evaluation: Structured evaluation payload
        
    Returns:
        Evaluation text or fallback message
    """
    client = create_gemini_client()
    if not client:
        logger.warning("Gemini client not available for evaluation feedback.")
        return "Modo demo: No se pudo conectar con Gemini para evaluación en tiempo real."
    
    try:
        return client.generate_evaluation_feedback(evaluation)
    except Exception as exc:
        logger.error(f"Generate evaluation feedback helper failed: {exc}")
        return "Error al generar evaluación con Gemini. Por favor intenta de nuevo."
