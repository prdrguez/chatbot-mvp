from __future__ import annotations

from typing import Any

import reflex as rx

from chatbot_mvp.services.submissions_store import read_submissions, summarize


def _dict_to_items(data: dict[str, int]) -> list[dict[str, Any]]:
    return [{"label": key, "count": data[key]} for key in sorted(data.keys())]


class AdminState(rx.State):
    loading: bool = False
    error: str = ""
    summary: dict[str, Any] = {}

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
