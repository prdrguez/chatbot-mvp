# Dev Notes

Nota: este repo corre en Streamlit. Las secciones marcadas como "Legacy (Reflex)"
son solo referencia historica y no aplican al runtime actual.

## Streamlit (actual)

- UI en `streamlit_app/` (Inicio + pages).
- Logica en `chatbot_mvp/services` y `chatbot_mvp/data`.
- Estilos globales en `streamlit_app/assets/style.css`.

## Legacy (Reflex) - Convenciones y estilo

- Evitar logica en componentes; delegar a `state/` y `services/`.
- Reutilizar tokens en `chatbot_mvp/ui/tokens.py` y `ui/evaluacion_tokens.py`.
- `components/layout.py` aplica overrides globales via `ThemeState`.
- Preferir `rx.cond` para render condicional con `rx.Var`.

## Legacy (Reflex) - Reflex Vars: como evitar errores tipicos

- Mal:
  ```python
  if AdminState.has_data:
      ...
  ```
- Bien:
  ```python
  rx.cond(AdminState.has_data, on_true, on_false)
  ```

Reflex no permite evaluar `rx.Var` en un `if` de Python porque no es un bool real.

## Legacy (Reflex) - Como agregar un KPI nuevo (guia corta)

1) Contar el dato en `services/submissions_store.summarize`.
   - Agrega el bucket en `breakdowns` o una seccion nueva en `summary`.

2) Exponerlo en `state/admin_state.py`.
   - Crear `@rx.var` para `*_top_items`, `*_extra_count` y `*_chart`.
   - Reutilizar `_dict_to_items_sorted` y `_items_to_chart`.

3) Renderizar la card en `pages/admin.py`.
   - Agrega `_kpi_card("Nuevo KPI", ...)` al listado `cards`.
   - Mantener `height="100%"` y `min_height` en la card.

Ejemplo (estado):
```python
@rx.var
def nuevo_kpi_chart(self) -> list[dict[str, Any]]:
    data = self._breakdown("nuevo_kpi")
    items = _dict_to_items_sorted(data, limit=5)
    return _items_to_chart(items)
```

Ejemplo (page):
```python
_kpi_card(
    "Nuevo KPI",
    AdminState.nuevo_kpi_top_items,
    AdminState.nuevo_kpi_extra_count,
    chart_data=AdminState.nuevo_kpi_chart,
)
```
