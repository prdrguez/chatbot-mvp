import os
import time
import logging
from typing import Dict, List, Optional, Iterator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Import AIClientError from openai_client to maintain consistency
from chatbot_mvp.services.openai_client import AIClientError


class GeminiChatClient:
    """
    Google Gemini client following OpenAI interface pattern.
    
    Handles rate limits for free tier (5-15 RPM) and provides
    fallback to demo mode on API failures.
    """
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY", "").strip()
        self.model = model or os.getenv("GEMINI_MODEL", "gemini-2.0-flash").strip()
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
            response = self._generate_with_retry(
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            return self._extract_response_text(response)
            
        except Exception as exc:
            logger.error(f"Error generating Gemini response: {exc}")
            raise AIClientError(f"Error al generar respuesta: {exc}")
    
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
        for attempt in range(max_retries):
            try:
                self.retry_count = attempt
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=prompt,
                    config={
                        'max_output_tokens': max_tokens,
                        'temperature': temperature,
                    }
                )
                return response
                
            except Exception as exc:
                # Handle rate limit specifically for Gemini
                if self._handle_rate_limit(exc):
                    if attempt == max_retries - 1:
                        raise AIClientError("Rate limit exceeded after retries")
                    continue
                elif attempt == max_retries - 1:
                    raise
                    
                # General exponential backoff for other errors
                wait_time = min(60, 2 ** attempt)  # Max 60s wait for Gemini strict limits
                logger.warning(f"Attempt {attempt + 1} failed, retrying in {wait_time}s: {exc}")
                time.sleep(wait_time)
    
    def _handle_rate_limit(self, response) -> bool:
        """
        Handle rate limit errors with backoff strategy for Gemini.
        
        Args:
            response: Error response from API
            
        Returns:
            True if should retry, False otherwise
        """
        error_str = str(response).lower()
        
        # Check for rate limit indicators
        if any(keyword in error_str for keyword in [
            "ratelimitexceeded", "rate limit", "too many requests", 
            "quota exceeded", "429"
        ]):
            wait_time = min(60, 2 ** self.retry_count)  # Conservative for free tier
            logger.warning(f"Gemini rate limit hit, waiting {wait_time}s")
            time.sleep(wait_time)
            self.retry_count += 1
            return True
        
        return False
    
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