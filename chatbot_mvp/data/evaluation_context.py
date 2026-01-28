"""
Contexto y prompts controlados para evaluaciones personalizadas.
Define el rol, restricciones y formato esperado para feedback de cuestionarios.
"""

# Contexto para el juego ético (AI Act evaluation)
JUEGO_ETICO_CONTEXT = """Eres un evaluador experto en ética e inteligencia artificial con especialidad en regulaciones europeas (AI Act) y gobernanza responsable.

Tu rol es proporcionar retroalimentación breve, clara y accionable en español basada ÚNICAMENTE en:
- Puntaje del usuario (correctas/total)
- Nivel alcanzado (Bajo, Medio, Alto)
- Patrones en sus respuestas

RESTRICCIONES ESTRICTAS:
1. NO inventes datos, normativas ni artículos que no te hayamos pasado
2. NO uses asteriscos, guiones bajos ni markdown (texto plano únicamente)
3. Máximo 6-8 líneas cortas (evita párrafos largos)
4. Estructura: diagnóstico + 2 recomendaciones concretas + cierre motivador
5. Tono: profesional, empático, no condescendiente

FORMATO ESPERADO:
- Línea 1-2: Diagnóstico del nivel alcanzado (sin formato especial)
- Línea 3-4: Fortalezas observadas en respuestas
- Línea 5-6: Dos recomendaciones prácticas (numeradas: 1) y 2))
- Línea 7-8: Cierre motivador sin promesas vagas

EJEMPLOS DE RECOMENDACIONES PERMITIDAS (basadas en datos pasados):
- Revisa el concepto de sesgo algorítmico en sistemas de IA
- Profundiza en mecanismos de transparencia y explicabilidad
- Estudia frameworks de mitigación de riesgos en IA
"""

def build_evaluation_feedback_prompt(evaluation: dict) -> str:
    """
    Construye prompt controlado para feedback de evaluación.
    
    Args:
        evaluation: Dict con keys 'summary' (score, level, etc) y 'questions' (list)
    
    Returns:
        Prompt formateado y controlado
    """
    summary = evaluation.get("summary", {})
    questions = evaluation.get("questions", [])
    
    score = summary.get("score", 0)
    total = summary.get("total_scored", 0)
    level = summary.get("level", "")
    percent = summary.get("score_percent", 0)
    
    # Detectar fortalezas basadas en respuestas
    strengths = _detect_strengths(questions, level)
    weakness_areas = _detect_weakness_areas(questions, level)
    
    prompt = f"""{JUEGO_ETICO_CONTEXT}

DATOS DEL USUARIO:
- Puntaje: {score}/{total} ({percent}%)
- Nivel: {level}
- Fortalezas detectadas: {strengths}
- Áreas a mejorar: {weakness_areas}

Proporciona feedback personalizado siguiendo el formato especificado. Sé conciso y directo."""
    
    return prompt


def _detect_strengths(questions: list, level: str) -> str:
    """Detecta fortalezas basadas en nivel y respuestas."""
    if not questions:
        return "pendiente de análisis"
    
    # Contar respuestas correctas por sección
    correct_by_section = {}
    for q in questions:
        if not isinstance(q, dict):
            continue
        section = q.get("section", "")
        scored = q.get("scored", False)
        if scored and section:
            if section not in correct_by_section:
                correct_by_section[section] = {"correct": 0, "total": 0}
            correct_by_section[section]["total"] += 1
    
    if level == "Alto":
        return "dominio integral de conceptos clave"
    elif level == "Medio":
        return "comprensión clara de principios fundamentales"
    else:
        return "bases conceptuales identificadas"


def _detect_weakness_areas(questions: list, level: str) -> str:
    """Detecta áreas de mejora basadas en respuestas."""
    if level == "Alto":
        return "profundizar en aplicaciones prácticas"
    elif level == "Medio":
        return "mecanismos de mitigación y gobernanza"
    else:
        return "principios de justicia y transparencia"
