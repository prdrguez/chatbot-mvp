import reflex as rx

from chatbot_mvp.config.settings import is_demo_mode


class ChatState(rx.State):
    messages: list[dict[str, str]] = []
    current_input: str = ""
    loading: bool = False
    typing: bool = False

    def set_input(self, value: str) -> None:
        self.current_input = value

    def send_message(self) -> None:
        content = self.current_input.strip()
        if not content:
            return

        # Add user message immediately
        self.messages = [
            *self.messages,
            {"role": "user", "content": content},
        ]
        self.current_input = ""
        self.loading = True
        self.typing = True

        # Simulate processing delay for better UX
        import time
        time.sleep(0.5)

        lower = content.lower()
        if "hola" in lower or "buenas" in lower:
            reply = "Hola! Contame cual es tu objetivo principal."
        elif "precio" in lower:
            if is_demo_mode():
                reply = "Esto es un demo. Pronto se conectara a IA para dar precios."
            else:
                reply = (
                    "Aun no hay modulo de precios. Contame que necesitas "
                    "y lo armamos."
                )
        else:
            reply = "Entendido. Contame un poco mas para ayudarte mejor."

        # Add assistant response
        self.messages = [
            *self.messages,
            {"role": "assistant", "content": reply},
        ]
        self.loading = False
        self.typing = False

    def clear_chat(self) -> None:
        self.messages = []
        self.current_input = ""
        self.loading = False
