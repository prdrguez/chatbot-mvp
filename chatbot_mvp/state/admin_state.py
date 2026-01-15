from __future__ import annotations

from typing import Any

import reflex as rx

from chatbot_mvp.services.submissions_store import (
    export_csv,
    export_json,
    read_submissions,
    summarize,
)


def _dict_to_items(data: dict[str, int]) -> list[dict[str, Any]]:
    return [{"label": key, "count": data[key]} for key in sorted(data.keys())]


class AdminState(rx.State):
    loading: bool = False
    error: str = ""
    summary: dict[str, Any] = {}
    export_message: str = ""
    export_error: str = ""

    @rx.var
    def has_data(self) -> bool:
        return bool(self.summary.get("total", 0))

    @rx.var
    def total(self) -> int:
        return int(self.summary.get("total", 0))

    @rx.var
    def avg_percent(self) -> float:
        return float(self.summary.get("avg_percent", 0))

    @rx.var
    def by_level_items(self) -> list[dict[str, Any]]:
        return _dict_to_items(self.summary.get("by_level", {}))

    @rx.var
    def edad_items(self) -> list[dict[str, Any]]:
        return _dict_to_items(self._breakdown("edad"))

    @rx.var
    def genero_items(self) -> list[dict[str, Any]]:
        return _dict_to_items(self._breakdown("genero"))

    @rx.var
    def ciudad_items(self) -> list[dict[str, Any]]:
        return _dict_to_items(self._breakdown("ciudad"))

    @rx.var
    def frecuencia_ia_items(self) -> list[dict[str, Any]]:
        return _dict_to_items(self._breakdown("frecuencia_ia"))

    @rx.var
    def nivel_educativo_items(self) -> list[dict[str, Any]]:
        return _dict_to_items(self._breakdown("nivel_educativo"))

    @rx.var
    def ocupacion_items(self) -> list[dict[str, Any]]:
        return _dict_to_items(self._breakdown("ocupacion"))

    @rx.var
    def area_items(self) -> list[dict[str, Any]]:
        return _dict_to_items(self._breakdown("area"))

    @rx.var
    def emociones_items(self) -> list[dict[str, Any]]:
        return _dict_to_items(self.summary.get("emociones", {}))

    @rx.var
    def questionnaire_label(self) -> str:
        info = self.summary.get("questionnaire_mode")
        if not isinstance(info, dict):
            return ""
        questionnaire_id = info.get("questionnaire_id", "")
        if not questionnaire_id:
            return ""
        questionnaire_version = info.get("questionnaire_version")
        if not isinstance(questionnaire_version, int):
            questionnaire_version = 0
        schema_version = info.get("schema_version")
        if not isinstance(schema_version, int):
            schema_version = 0
        return (
            f"Cuestionario: {questionnaire_id} v{questionnaire_version} / "
            f"Schema v{schema_version}"
        )

    def _breakdown(self, key: str) -> dict[str, int]:
        breakdowns = self.summary.get("breakdowns", {})
        if not isinstance(breakdowns, dict):
            return {}
        data = breakdowns.get(key)
        return data if isinstance(data, dict) else {}

    @rx.event(background=True)
    async def load_summary(self) -> None:
        async with self:
            self.loading = True
            self.error = ""
            self.summary = {}

        try:
            submissions = read_submissions()
            summary = summarize(submissions)
        except Exception as exc:  # pragma: no cover - fallback to avoid UI crash.
            summary = {}
            error = f"Error al leer submissions: {exc}"
        else:
            error = ""

        async with self:
            self.summary = summary
            self.error = error
            self.loading = False

    @rx.event(background=True)
    async def do_export_json(self) -> None:
        async with self:
            self.export_message = ""
            self.export_error = ""

        try:
            submissions = read_submissions()
            path = export_json(submissions)
        except Exception as exc:  # pragma: no cover - fallback to avoid UI crash.
            message = ""
            error = f"Error al exportar JSON: {exc}"
        else:
            message = f"Exportado JSON: {path}"
            error = ""

        async with self:
            self.export_message = message
            self.export_error = error

    @rx.event(background=True)
    async def do_export_csv(self) -> None:
        async with self:
            self.export_message = ""
            self.export_error = ""

        try:
            submissions = read_submissions()
            path = export_csv(submissions)
        except Exception as exc:  # pragma: no cover - fallback to avoid UI crash.
            message = ""
            error = f"Error al exportar CSV: {exc}"
        else:
            message = f"Exportado CSV: {path}"
            error = ""

        async with self:
            self.export_message = message
            self.export_error = error
