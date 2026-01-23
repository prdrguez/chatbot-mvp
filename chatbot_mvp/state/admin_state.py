from __future__ import annotations

import math
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


def _dict_to_items_sorted(
    data: dict[str, int], limit: int | None = None
) -> list[dict[str, Any]]:
    items = sorted(data.items(), key=lambda entry: (-entry[1], entry[0]))
    sliced = items if limit is None else items[:limit]
    return [{"label": key, "count": value} for key, value in sliced]


def _items_to_chart(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{"name": item["label"], "value": item["count"]} for item in items]


def _extra_count(data: dict[str, int], limit: int) -> int:
    return max(len(data) - limit, 0)


def _top_with_others(data: dict[str, int], limit: int) -> list[dict[str, Any]]:
    items = sorted(data.items(), key=lambda entry: (-entry[1], entry[0]))
    top_items = items[:limit]
    others_items = items[limit:]
    result = [{"label": key, "count": value} for key, value in top_items]
    if others_items:
        others_total = sum(value for _, value in others_items)
        result.append({"label": "Otros", "count": others_total})
    return result


def _top_items_with_others(
    items: list[dict[str, Any]], limit: int
) -> list[dict[str, Any]]:
    sorted_items = sorted(
        items,
        key=lambda item: (
            -int(item.get("count", 0)),
            str(item.get("label", "")),
        ),
    )
    top_items = sorted_items[:limit]
    others_total = sum(int(item.get("count", 0)) for item in sorted_items[limit:])
    result = [
        {"label": item.get("label", ""), "count": int(item.get("count", 0))}
        for item in top_items
    ]
    if others_total > 0:
        result.append({"label": "Otros", "count": others_total})
    return result


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
    def avg_percent_float(self) -> float:
        try:
            value = float(self.summary.get("avg_percent", 0))
        except (TypeError, ValueError):
            value = 0.0
        if value < 0:
            return 0.0
        if value > 100:
            return 100.0
        return value

    @rx.var
    def avg_percent_value(self) -> float:
        return self.avg_percent_float

    @rx.var
    def avg_percent_int(self) -> int:
        return int(self.avg_percent_value)

    @rx.var
    def avg_percent_display(self) -> str:
        return f"{self.avg_percent_value:.0f}%"

    @rx.var
    def avg_percent_width(self) -> str:
        return f"{self.avg_percent_value:.0f}%"

    @rx.var
    def avg_level_label(self) -> str:
        value = self.avg_percent_value
        if value >= 70:
            return "Alto"
        if value >= 40:
            return "Medio"
        return "Bajo"

    @rx.var
    def avg_level_color(self) -> str:
        value = self.avg_percent_value
        if value >= 70:
            return "var(--green-9)"
        if value >= 40:
            return "var(--amber-9)"
        return "var(--red-9)"

    @rx.var
    def gauge_arc_len(self) -> float:
        radius = 70.0
        return math.pi * radius

    @rx.var
    def gauge_track_dasharray(self) -> str:
        arc_len = self.gauge_arc_len
        return f"{arc_len} {arc_len}"

    @rx.var
    def gauge_progress_dasharray(self) -> str:
        arc_len = self.gauge_arc_len
        progress_len = arc_len * (self.avg_percent_value / 100.0)
        return f"{progress_len} {arc_len}"

    @rx.var
    def by_level_items(self) -> list[dict[str, Any]]:
        return _dict_to_items(self.summary.get("by_level", {}))

    @rx.var
    def by_level_top_items(self) -> list[dict[str, Any]]:
        data = self.summary.get("by_level", {})
        return _dict_to_items_sorted(data if isinstance(data, dict) else {}, limit=5)

    @rx.var
    def by_level_extra_count(self) -> int:
        data = self.summary.get("by_level", {})
        return _extra_count(data if isinstance(data, dict) else {}, 5)

    @rx.var
    def by_level_chart(self) -> list[dict[str, Any]]:
        data = self.summary.get("by_level", {})
        items = _dict_to_items_sorted(data if isinstance(data, dict) else {}, limit=5)
        return _items_to_chart(items)

    @rx.var
    def edad_items(self) -> list[dict[str, Any]]:
        return _dict_to_items(self._breakdown("edad"))

    @rx.var
    def edad_top_items(self) -> list[dict[str, Any]]:
        data = self._breakdown("edad")
        return _dict_to_items_sorted(data, limit=5)

    @rx.var
    def edad_extra_count(self) -> int:
        data = self._breakdown("edad")
        return _extra_count(data, 5)

    @rx.var
    def edad_chart(self) -> list[dict[str, Any]]:
        data = self._breakdown("edad")
        items = _dict_to_items_sorted(data, limit=5)
        return _items_to_chart(items)

    @rx.var
    def genero_items(self) -> list[dict[str, Any]]:
        return _dict_to_items(self._breakdown("genero"))

    @rx.var
    def genero_top_items(self) -> list[dict[str, Any]]:
        data = self._breakdown("genero")
        return _dict_to_items_sorted(data, limit=5)

    @rx.var
    def genero_extra_count(self) -> int:
        data = self._breakdown("genero")
        return _extra_count(data, 5)

    @rx.var
    def genero_chart(self) -> list[dict[str, Any]]:
        data = self._breakdown("genero")
        items = _dict_to_items_sorted(data, limit=5)
        return _items_to_chart(items)

    @rx.var
    def ciudad_items(self) -> list[dict[str, Any]]:
        data = self._breakdown("ciudad")
        items = _dict_to_items_sorted(data)
        items = _top_items_with_others(items, 8)
        return _items_to_chart(items)

    @rx.var
    def ciudad_top_items(self) -> list[dict[str, Any]]:
        data = self._breakdown("ciudad")
        return _dict_to_items_sorted(data, limit=5)

    @rx.var
    def ciudad_chart_items(self) -> list[dict[str, Any]]:
        data = self._breakdown("ciudad")
        items = _dict_to_items_sorted(data)
        return _top_items_with_others(items, 8)

    @rx.var
    def ciudad_extra_count(self) -> int:
        return 0

    @rx.var
    def ciudad_chart(self) -> list[dict[str, Any]]:
        data = self._breakdown("ciudad")
        items = _dict_to_items_sorted(data)
        items = _top_items_with_others(items, 8)
        return _items_to_chart(items)

    @rx.var
    def frecuencia_ia_items(self) -> list[dict[str, Any]]:
        return _dict_to_items(self._breakdown("frecuencia_ia"))

    @rx.var
    def frecuencia_ia_top_items(self) -> list[dict[str, Any]]:
        data = self._breakdown("frecuencia_ia")
        return _dict_to_items_sorted(data, limit=5)

    @rx.var
    def frecuencia_ia_extra_count(self) -> int:
        data = self._breakdown("frecuencia_ia")
        return _extra_count(data, 5)

    @rx.var
    def frecuencia_ia_chart(self) -> list[dict[str, Any]]:
        data = self._breakdown("frecuencia_ia")
        items = _dict_to_items_sorted(data, limit=5)
        return _items_to_chart(items)

    @rx.var
    def nivel_educativo_items(self) -> list[dict[str, Any]]:
        return _dict_to_items(self._breakdown("nivel_educativo"))

    @rx.var
    def nivel_educativo_top_items(self) -> list[dict[str, Any]]:
        data = self._breakdown("nivel_educativo")
        return _dict_to_items_sorted(data, limit=5)

    @rx.var
    def nivel_educativo_extra_count(self) -> int:
        data = self._breakdown("nivel_educativo")
        return _extra_count(data, 5)

    @rx.var
    def nivel_educativo_chart(self) -> list[dict[str, Any]]:
        data = self._breakdown("nivel_educativo")
        items = _dict_to_items_sorted(data, limit=5)
        return _items_to_chart(items)

    @rx.var
    def ocupacion_items(self) -> list[dict[str, Any]]:
        return _dict_to_items(self._breakdown("ocupacion"))

    @rx.var
    def ocupacion_top_items(self) -> list[dict[str, Any]]:
        data = self._breakdown("ocupacion")
        return _dict_to_items_sorted(data, limit=5)

    @rx.var
    def ocupacion_extra_count(self) -> int:
        data = self._breakdown("ocupacion")
        return _extra_count(data, 5)

    @rx.var
    def ocupacion_chart(self) -> list[dict[str, Any]]:
        data = self._breakdown("ocupacion")
        items = _dict_to_items_sorted(data, limit=5)
        return _items_to_chart(items)

    @rx.var
    def area_items(self) -> list[dict[str, Any]]:
        return _dict_to_items(self._breakdown("area"))

    @rx.var
    def area_top_items(self) -> list[dict[str, Any]]:
        data = self._breakdown("area")
        return _dict_to_items_sorted(data, limit=5)

    @rx.var
    def area_extra_count(self) -> int:
        data = self._breakdown("area")
        return _extra_count(data, 5)

    @rx.var
    def area_chart(self) -> list[dict[str, Any]]:
        data = self._breakdown("area")
        items = _dict_to_items_sorted(data, limit=5)
        return _items_to_chart(items)

    @rx.var
    def emociones_items(self) -> list[dict[str, Any]]:
        return _dict_to_items(self.summary.get("emociones", {}))

    @rx.var
    def emociones_top_items(self) -> list[dict[str, Any]]:
        data = self.summary.get("emociones", {})
        return _dict_to_items_sorted(data if isinstance(data, dict) else {}, limit=5)

    @rx.var
    def emociones_extra_count(self) -> int:
        data = self.summary.get("emociones", {})
        return _extra_count(data if isinstance(data, dict) else {}, 5)

    @rx.var
    def emociones_chart(self) -> list[dict[str, Any]]:
        data = self.summary.get("emociones", {})
        items = _dict_to_items_sorted(data if isinstance(data, dict) else {}, limit=5)
        return _items_to_chart(items)

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
    @rx.event(background=True)
    async def reset_data(self) -> None:
        """Clear all submissions and reset the summary."""
        async with self:
            self.loading = True
        
        try:
            from pathlib import Path
            from chatbot_mvp.services.submissions_store import SUBMISSIONS_PATH
            path = Path(SUBMISSIONS_PATH)
            if path.exists():
                path.unlink()
            
            # Re-initialize summary
            async with self:
                self.summary = {}
                self.error = "Datos eliminados correctamente."
        except Exception as exc:
            async with self:
                self.error = f"Error al eliminar datos: {exc}"
        
        async with self:
            self.loading = False
            await self.load_summary()

    @rx.event
    def logout_admin(self) -> None:
        """Logout and redirect."""
        from chatbot_mvp.state.auth_state import AuthState
        return rx.redirect("/login")
