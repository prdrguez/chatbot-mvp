import os
from typing import Dict


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
