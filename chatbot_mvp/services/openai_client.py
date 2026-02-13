import os
import time
import logging
from typing import Dict, List, Optional, Iterator

from chatbot_mvp.config.settings import is_demo_mode

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AIClientError(Exception):
    """Custom exception for AI client errors."""
    pass


class OpenAIChatClient:
    """Enhanced OpenAI client for chat interactions."""
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "").strip()
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip()
        self.client = None
        self._initialized = False
        
        if self.api_key:
            self._initialize_client()
    
    def _initialize_client(self) -> bool:
        """Initialize the OpenAI client."""
        if self._initialized:
            return True
            
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=self.api_key)
            self._initialized = True
            logger.info("OpenAI client initialized successfully")
            return True
        except ImportError as exc:
            logger.error(f"OpenAI SDK not installed: {exc}")
            raise AIClientError(f"SDK de OpenAI no instalado: {exc}")
        except Exception as exc:
            logger.error(f"Failed to initialize OpenAI client: {exc}")
            raise AIClientError(f"Error al inicializar cliente OpenAI: {exc}")
    
    def generate_chat_response(
        self, 
        message: str, 
        conversation_history: List[Dict[str, str]],
        user_context: Optional[Dict] = None,
        max_tokens: int = 150,
        temperature: float = 0.7
    ) -> str:
        """
        Generate a chat response using OpenAI.
        
        Args:
            message: Current user message
            conversation_history: List of previous messages
            user_context: Optional user context information
            max_tokens: Maximum response length
            temperature: Response randomness (0-1)
            
        Returns:
            Generated response text
        """
        if not self._initialized:
            raise AIClientError("Cliente OpenAI no inicializado")
        
        try:
            # Build messages for API
            messages = self._build_chat_messages(
                message, conversation_history, user_context
            )
            
            # Generate response with retries
            response = self._generate_with_retry(
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            return self._extract_response_text(response)
            
        except Exception as exc:
            logger.error(f"Error generating chat response: {exc}")
            raise AIClientError(f"Error al generar respuesta: {exc}")
    
    def _build_chat_messages(
        self, 
        message: str, 
        conversation_history: List[Dict[str, str]],
        user_context: Optional[Dict] = None
    ) -> List[Dict]:
        """Build message list for OpenAI API."""
        messages = [
            {
                "role": "system",
                "content": self._build_system_prompt(user_context)
            }
        ]
        
        # Add conversation history (last 10 messages to avoid token limits)
        recent_history = conversation_history[-10:]
        for msg in recent_history:
            messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        
        # Add current message
        messages.append({
            "role": "user", 
            "content": message
        })
        
        return messages
    
    def _build_system_prompt(self, user_context: Optional[Dict] = None) -> str:
        """Build system prompt based on user context."""
        base_prompt = (
            "Eres un asistente util y amigable que responde en espanol. "
            "Se conciso pero informativo. Manten un tono profesional pero cercano. "
            "Si no sabes algo, admitalo claramente."
        )

        if user_context:
            context_info = []
            if "demografia" in user_context:
                demografia = user_context["demografia"]
                if demografia.get("edad"):
                    context_info.append(f"Edad: {demografia['edad']}")
                if demografia.get("ocupacion"):
                    context_info.append(f"Ocupacion: {demografia['ocupacion']}")
                if demografia.get("nivel_conocimiento_ia"):
                    context_info.append(
                        f"Nivel conocimiento IA: {demografia['nivel_conocimiento_ia']}"
                    )

            if context_info:
                base_prompt += "\n\nContexto del usuario:\n" + "\n".join(context_info)

            kb_context = user_context.get("kb_context_block")
            if kb_context:
                if user_context.get("kb_strict"):
                    base_prompt += (
                        "\n\nResponde SOLO usando la evidencia provista en <context>. "
                        "Si no esta en el contexto, di claramente que no esta en la politica cargada. "
                        "Si preguntan por articulo o item, indica la fuente exacta."
                    )
                else:
                    base_prompt += (
                        "\n\nSi el contexto de la KB es relevante, usalo como fuente principal "
                        "y evita contradecirlo."
                    )
                base_prompt += f"\n\n<context>\n{kb_context}\n</context>"

        return base_prompt
    
    def _generate_with_retry(
        self, 
        messages: List[Dict], 
        max_tokens: int, 
        temperature: float,
        max_retries: int = 3
    ) -> Dict:
        """Generate response with retry logic."""
        for attempt in range(max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    timeout=30
                )
                return response
                
            except Exception as exc:
                if attempt == max_retries - 1:
                    raise
                
                wait_time = 2 ** attempt  # Exponential backoff
                logger.warning(f"Attempt {attempt + 1} failed, retrying in {wait_time}s: {exc}")
                time.sleep(wait_time)
    
    def _extract_response_text(self, response: Dict) -> str:
        """Extract text from OpenAI response."""
        try:
            return response.choices[0].message.content.strip()
        except (AttributeError, IndexError, KeyError) as exc:
            logger.error(f"Failed to extract response text: {exc}")
            raise AIClientError("Respuesta vacía o malformed")
    
    def is_available(self) -> bool:
        """Check if the client is available."""
        return self._initialized and self.client is not None


# Legacy functions for evaluation compatibility
def _demo_text(answers: Dict[str, str]) -> str:
    answered = sum(1 for value in answers.values() if value.strip())
    lines = [
        "Modo demo: resultado generado sin OpenAI.",
        f"Respuestas consideradas: {answered}.",
        "Clarifica tus objetivos principales y el alcance.",
        "Prioriza una funcionalidad clave para el primer release.",
        "Define tu publico objetivo con ejemplos concretos.",
        "Identifica riesgos y como mitigarlos pronto.",
        "Establece un criterio de exito medible y realista.",
    ]
    return "\n".join(lines)


def _build_prompt(answers: Dict[str, str]) -> str:
    lines = ["Eres un evaluador. Da una evaluacion breve y util en espanol."]
    lines.append("Respuestas:")
    for key, value in answers.items():
        cleaned = value.strip()
        if cleaned:
            lines.append(f"- {key}: {cleaned}")
    lines.append("Entrega 6-10 lineas, con tono claro y accionable.")
    return "\n".join(lines)


def _extract_output_text(response: object) -> str:
    output = getattr(response, "output", None)
    if not output:
        return ""

    parts = []
    for item in output:
        if getattr(item, "type", "") != "message":
            continue
        for content in getattr(item, "content", []) or []:
            if getattr(content, "type", "") == "output_text":
                parts.append(getattr(content, "text", ""))
    return "\n".join(part for part in parts if part)


def generate_evaluation(answers: Dict[str, str]) -> str:
    if is_demo_mode():
        return _demo_text(answers)

    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        return _demo_text(answers)

    try:
        from openai import OpenAI
    except Exception as exc:  # pragma: no cover - optional dependency
        return f"Error al generar con IA: SDK de OpenAI no instalado ({exc})."

    model = os.getenv("OPENAI_MODEL", "gpt-4.1-mini").strip() or "gpt-4.1-mini"
    prompt = _build_prompt(answers)

    try:
        client = OpenAI(api_key=api_key)
        response = client.responses.create(
            model=model,
            input=prompt,
            max_output_tokens=250,
        )
        text = getattr(response, "output_text", "") or _extract_output_text(response)
        text = text.strip()
        if not text:
            return "Error al generar con IA: respuesta vacia."
        return text
    except Exception as exc:
        return f"Error al generar con IA: {exc}"


# Factory function for creating chat clients
def create_chat_client() -> Optional[OpenAIChatClient]:
    """
    Factory function to create a chat client.
    
    Returns:
        OpenAIChatClient instance if configured, None otherwise
    """
    try:
        client = OpenAIChatClient()
        return client if client.is_available() else None
    except Exception as exc:
        logger.warning(f"Failed to create chat client: {exc}")
        return None
