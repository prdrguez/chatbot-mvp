from chatbot_mvp.services.submissions_store import summarize


def test_summarize_empty():
    result = summarize([])
    assert result["total"] == 0
    assert result["avg_correct"] == 0
    assert result["avg_total"] == 0
    assert result["avg_percent"] == 0
    assert result["by_level"] == {}
    assert result["emociones"] == {}
    assert result["questionnaire_mode"] == {}
    for key in [
        "edad",
        "genero",
        "ciudad",
        "frecuencia_ia",
        "nivel_educativo",
        "ocupacion",
        "area",
    ]:
        assert result["breakdowns"][key] == {}


def test_summarize_basic():
    submissions = [
        {
            "questionnaire_id": "juego_etico",
            "questionnaire_version": 1,
            "schema_version": 1,
            "level": "Medio",
            "correct_count": 10,
            "total_scored": 15,
            "score_percent": 66,
            "answers": {
                "demo_age": "18 - 25",
                "demo_gender": "Femenino",
                "context_city": "Buenos Aires",
                "context_frequency": "Frecuentemente",
                "context_education": "Universitario",
                "context_role": "Estudiante",
                "context_area": "Tecnología",
                "context_emotions": ["Curiosidad", "Esperanza"],
            },
        },
        {
            "questionnaire_id": "juego_etico",
            "questionnaire_version": 1,
            "schema_version": 1,
            "level": "Bajo",
            "correct_count": 5,
            "total_scored": 15,
            "score_percent": 33,
            "answers": {
                "demo_age": "26 - 40",
                "demo_gender": "Masculino",
                "context_city": "Córdoba",
                "context_frequency": "A veces",
                "context_education": "Universitario",
                "context_role": "Empleado/a",
                "context_area": "Humanidades",
                "context_emotions": ["Miedo"],
            },
        },
    ]

    result = summarize(submissions)

    assert result["total"] == 2
    assert result["avg_correct"] == 7.5
    assert result["avg_total"] == 15
    assert result["avg_percent"] == 49.5
    assert result["by_level"] == {"Bajo": 1, "Medio": 1}

    breakdowns = result["breakdowns"]
    assert breakdowns["edad"]["18 - 25"] == 1
    assert breakdowns["edad"]["26 - 40"] == 1
    assert breakdowns["genero"]["Femenino"] == 1
    assert breakdowns["genero"]["Masculino"] == 1
    assert breakdowns["ciudad"]["Buenos Aires"] == 1
    assert breakdowns["ciudad"]["Córdoba"] == 1
    assert breakdowns["frecuencia_ia"]["Frecuentemente"] == 1
    assert breakdowns["frecuencia_ia"]["A veces"] == 1
    assert breakdowns["nivel_educativo"]["Universitario"] == 2
    assert breakdowns["ocupacion"]["Estudiante"] == 1
    assert breakdowns["ocupacion"]["Empleado/a"] == 1
    assert breakdowns["area"]["Tecnología"] == 1
    assert breakdowns["area"]["Humanidades"] == 1

    emociones = result["emociones"]
    assert emociones["Curiosidad"] == 1
    assert emociones["Esperanza"] == 1
    assert emociones["Miedo"] == 1

    mode = result["questionnaire_mode"]
    assert mode["questionnaire_id"] == "juego_etico"
    assert mode["questionnaire_version"] == 1
    assert mode["schema_version"] == 1
