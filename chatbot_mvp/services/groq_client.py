import logging
from typing import Dict, List, Optional

from chatbot_mvp.config.settings import get_env_value, sanitize_env_value
from chatbot_mvp.services.openai_client import AIClientError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

_DEFAULT_GROQ_MODEL = "llama-3.1-8b-instant"


def get_groq_api_key() -> str:
    return get_env_value("GROQ_API_KEY")


class GroqChatClient:
    """Groq client for chat interactions."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = sanitize_env_value(api_key) if isinstance(api_key, str) else ""
        if not self.api_key:
            self.api_key = get_groq_api_key()
        self.model = sanitize_env_value(model) if isinstance(model, str) else ""
        if not self.model:
            self.model = get_env_value("GROQ_MODEL", _DEFAULT_GROQ_MODEL)
        self.client = None
        self._initialized = False

        if self.api_key:
            self._initialize_client()

    def _initialize_client(self) -> bool:
        if self._initialized:
            return True

        try:
            from groq import Groq

            self.client = Groq(api_key=self.api_key)
            self._initialized = True
            logger.info("Groq client initialized successfully with model: %s", self.model)
            return True
        except ImportError as exc:
            logger.error("Groq SDK not installed: %s", exc)
            raise AIClientError(f"SDK de Groq no instalado: {exc}")
        except Exception as exc:
            logger.error("Failed to initialize Groq client: %s", exc)
            raise AIClientError(f"Error al inicializar cliente Groq: {exc}")

    def generate_chat_response(
        self,
        message: str,
        conversation_history: List[Dict[str, str]],
        user_context: Optional[Dict] = None,
        max_tokens: int = 150,
        temperature: float = 0.7,
    ) -> str:
        if not self._initialized:
            raise AIClientError("Cliente Groq no inicializado")

        try:
            messages = self._build_chat_messages(
                message, conversation_history, user_context
            )
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            return self._extract_response_text(response)
        except Exception as exc:
            logger.error("Error generating Groq response: %s", exc)
            raise AIClientError(f"Error al generar respuesta: {exc}")

    def _build_chat_messages(
        self,
        message: str,
        conversation_history: List[Dict[str, str]],
        user_context: Optional[Dict] = None,
    ) -> List[Dict]:
        messages = [
            {
                "role": "system",
                "content": self._build_system_prompt(user_context),
            }
        ]

        recent_history = conversation_history[-10:]
        for msg in recent_history:
            messages.append({
                "role": msg["role"],
                "content": msg["content"],
            })

        messages.append({
            "role": "user",
            "content": message,
        })

        return messages

    def _build_system_prompt(self, user_context: Optional[Dict] = None) -> str:
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
                    context_info.append(
                        f"Nivel conocimiento IA: {demografia['nivel_conocimiento_ia']}"
                    )

            if context_info:
                base_prompt += "\n\nContexto del usuario:\n" + "\n".join(context_info)

        return base_prompt

    def _extract_response_text(self, response: Dict) -> str:
        try:
            return response.choices[0].message.content.strip()
        except (AttributeError, IndexError, KeyError) as exc:
            logger.error("Failed to extract Groq response text: %s", exc)
            raise AIClientError("Respuesta vacía o malformed")

    def is_available(self) -> bool:
        return self._initialized and self.client is not None


def create_groq_client(
    api_key: Optional[str] = None, model: Optional[str] = None
) -> Optional[GroqChatClient]:
    try:
        client = GroqChatClient(api_key=api_key, model=model)
        return client if client.is_available() else None
    except Exception as exc:
        logger.warning("Failed to create Groq client: %s", exc)
        raise
