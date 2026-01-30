import logging
from typing import Any, Dict, List, Optional, Iterator

from chatbot_mvp.config.settings import get_env_value, sanitize_env_value
from chatbot_mvp.services.openai_client import AIClientError
from chatbot_mvp.data.evaluation_context import build_evaluation_feedback_prompt

logger = logging.getLogger(__name__)

_DEFAULT_GROQ_MODEL = "openai/gpt-oss-20b"
_GROQ_BASE_URL = "https://api.groq.com/openai/v1"


def get_groq_api_key() -> str:
    return get_env_value("GROQ_API_KEY")


class GroqChatClient:
    """Groq client using OpenAI SDK with Groq base_url."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        api_key_value = sanitize_env_value(api_key) if isinstance(api_key, str) else ""
        self.api_key = api_key_value or get_groq_api_key()
        model_value = sanitize_env_value(model) if isinstance(model, str) else ""
        self.model = model_value or get_env_value("GROQ_MODEL", _DEFAULT_GROQ_MODEL)
        self.client = None
        self._initialized = False

        if self.api_key:
            self._initialize_client()

    def _initialize_client(self) -> bool:
        if self._initialized:
            return True

        try:
            from openai import OpenAI

            self.client = OpenAI(api_key=self.api_key, base_url=_GROQ_BASE_URL)
            self._initialized = True
            logger.info("Groq client initialized successfully with model: %s", self.model)
            return True
        except ImportError as exc:
            logger.error("OpenAI SDK not installed: %s", exc)
            raise AIClientError(f"SDK de OpenAI no instalado para Groq: {exc}")
        except Exception as exc:
            logger.error("Failed to initialize Groq client: %s", exc)
            raise AIClientError(f"Error al inicializar cliente Groq: {exc}")

    def generate(
        self,
        prompt: str,
        max_tokens: int = 150,
        temperature: float = 0.7,
    ) -> str:
        if not self._initialized:
            raise AIClientError("Cliente Groq no inicializado")

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=temperature,
        )
        return self._extract_response_text(response)

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

    def generate_chat_response_stream(
        self,
        message: str,
        conversation_history: List[Dict[str, str]],
        user_context: Optional[Dict] = None,
        max_tokens: int = 150,
        temperature: float = 0.7,
    ) -> Iterator[str]:
        if not self._initialized:
            raise AIClientError("Cliente Groq no inicializado")

        messages = self._build_chat_messages(message, conversation_history, user_context)
        try:
            stream = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                stream=True,
            )
            for chunk in stream:
                text = self._extract_response_text(chunk)
                if text:
                    yield text
        except Exception as exc:
            logger.error("Error streaming Groq response: %s", exc)
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

        return base_prompt

    def generate_evaluation(self, answers: Dict[str, Any]) -> str:
        if not self._initialized:
            raise AIClientError("Cliente Groq no inicializado")

        try:
            prompt = self._build_evaluation_prompt(answers)
            return self.generate(prompt, max_tokens=300, temperature=0.4)
        except Exception as exc:
            logger.error("Error generating Groq evaluation: %s", exc)
            raise AIClientError(f"Error al generar evaluacion: {exc}")

    def _build_evaluation_prompt(self, answers: Dict[str, Any]) -> str:
        lines = [
            "Eres un evaluador experto en etica e inteligencia artificial. "
            "Da una evaluacion personalizada, breve y util en espanol basada en las siguientes respuestas a un cuestionario de etica.",
            "\nRespuestas del usuario:",
        ]

        for key, value in answers.items():
            if value:
                val_str = ", ".join(value) if isinstance(value, list) else str(value)
                lines.append(f"- {key}: {val_str}")

        lines.append(
            "\nPor favor entrega 6-10 lineas con un tono profesional, claro y accionable. "
            "Enfocate en consejos practicos basados en sus respuestas especificas. "
            "No uses formato markdown excesivo, prefiere texto plano."
        )
        return "\n".join(lines)

    def generate_evaluation_feedback(self, evaluation: Dict[str, Any]) -> str:
        if not self._initialized:
            raise AIClientError("Cliente Groq no inicializado")

        try:
            prompt = build_evaluation_feedback_prompt(evaluation)
            return self.generate(prompt, max_tokens=250, temperature=0.5)
        except Exception as exc:
            logger.error("Error generating Groq evaluation feedback: %s", exc)
            raise AIClientError(f"Error al generar evaluacion: {exc}")

    def _extract_response_text(self, response: Any) -> str:
        if response is None:
            return ""

        output_text = getattr(response, "output_text", None)
        if isinstance(output_text, str) and output_text.strip():
            return output_text.strip()

        choices = getattr(response, "choices", None)
        if choices:
            first = choices[0]
            delta = getattr(first, "delta", None)
            if delta and getattr(delta, "content", None):
                return str(delta.content)
            message = getattr(first, "message", None)
            if message and getattr(message, "content", None):
                return str(message.content).strip()
            text = getattr(first, "text", None)
            if isinstance(text, str) and text.strip():
                return text.strip()

        return ""

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


def generate_evaluation(answers: Dict[str, Any]) -> str:
    client = create_groq_client()
    if not client:
        logger.warning("Groq client not available for evaluation.")
        return "Falta GROQ_API_KEY para usar Groq en la evaluacion."
    try:
        return client.generate_evaluation(answers)
    except Exception as exc:
        logger.error("Generate evaluation helper failed: %s", exc)
        return "Error al generar evaluacion con Groq. Por favor intenta de nuevo."


def generate_evaluation_feedback(evaluation: Dict[str, Any]) -> str:
    client = create_groq_client()
    if not client:
        logger.warning("Groq client not available for evaluation feedback.")
        return "Falta GROQ_API_KEY para usar Groq en la evaluacion."
    try:
        return client.generate_evaluation_feedback(evaluation)
    except Exception as exc:
        logger.error("Generate evaluation feedback helper failed: %s", exc)
        return "Error al generar evaluacion con Groq. Por favor intenta de nuevo."
