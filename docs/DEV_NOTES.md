# DEV NOTES

Notas tecnicas vigentes del repo.

## Estado actual (runtime)
- Stack productivo: Python + Streamlit.
- Entry point: `streamlit_app/Inicio.py`.
- UI multipage en `streamlit_app/`.
- Logica de negocio en `chatbot_mvp/`.

## Paginas activas
- `streamlit_app/Inicio.py`
- `streamlit_app/pages/1_Evaluacion.py`
- `streamlit_app/pages/2_Chat.py`
- `streamlit_app/pages/3_Admin.py`

## Providers
- Default: Gemini.
- Selector en Admin: solo `gemini` y `groq`.
- Persistencia de override: `chatbot_mvp/data/app_settings.json`.
- `demo` existe y se usa como fallback.
- `openai` existe en config/env pero no esta conectado end-to-end en UI actual.

## Base de Conocimiento (KB)
- Carga desde Admin (`.txt`, `.md`, un archivo por vez).
- Runtime en `st.session_state` (`kb_text`, `kb_name`, `kb_chunks`, `kb_index`, etc.).
- Modo `general` y `strict`.
- Debug opcional de retrieval visible en Chat.

### General vs Strict (flujo vigente)
- `Strict`:
  - Usa solo evidencia recuperada.
  - Si no hay evidencia suficiente, responde fijo `No encuentro eso...` y no llama provider.
- `General`:
  - Si hay evidencia suficiente, responde grounded y agrega `Fuentes` (una sola vez, sin duplicados).
  - Si no hay evidencia y la consulta no es interna, responde en modo general con aviso explicito: `El documento cargado no menciona esto.`
  - Si no hay evidencia y la consulta parece politica/procedimiento interno de una organizacion, bloquea invencion de politicas: no llama provider, pide documento/fragmento y devuelve guia general no verificada.

### Evidence quality gate (anti match tangencial)
- Antes de usar contexto, `ChatService` valida evidencia real por keywords de la consulta:
  - Normaliza texto (`lower`, sin acentos).
  - Filtra stopwords y terminos genericos (`politica`, `empresa`, `procedimiento`, etc.).
  - Mantiene tokens de 3+ caracteres y siglas en mayusculas (2-6 chars, por ejemplo `NFL`).
- Reglas de uso de evidencia:
  - Debe existir match literal de al menos 1 keyword en el chunk (2 si la consulta trae muchas keywords).
  - Si hay siglas, se exige match exacto de esa sigla en el chunk.
- Si no pasa el gate:
  - `used_context=False`.
  - No se inyecta contexto KB.
  - No se agrega `Fuentes`.

### Org mismatch en modo General
- `policy_kb.load_kb` infiere `kb_primary_entity` con una heuristica simple (token capitalizado mas frecuente).
- En `ChatService` se detectan entidades en la query (ALLCAPS, capitalized, sufijos corporativos).
- Si la consulta es de politica interna y menciona otra entidad distinta de `kb_primary_entity`:
  - No se llama provider para inventar politicas de terceros.
  - Respuesta fija de mismatch: el documento corresponde a la entidad de la KB y no puede confirmar politicas internas de la otra organizacion.
  - Si hay evidencia usable del tema en la KB, se puede anexar resumen de esa evidencia con `Fuentes`.

### Ejemplos esperados (General + securin.txt)
- `que es la NFL?`:
  - Sin evidencia usable.
  - Aviso de que el documento no lo menciona.
  - Respuesta general sin `Fuentes`.
- `cual es la politica interna de ACME Corp sobre regalos?`:
  - Mismatch de organizacion.
  - No inventa politicas de ACME.
  - No llama provider para ese contenido interno.
- `se pueden recibir regalos?`:
  - Evidencia usable (politica de obsequios).
  - Respuesta grounded con `Fuentes`.

### Query expansion y debug
- `policy_kb.expand_query` normaliza el formato de consulta para retrieval/debug y deja campos estables:
  - `query_original`
  - `query_expanded`
  - `intent`
  - `tags`
- En esta etapa la expansion es rule-based minima (sin embeddings) para mantener latencia y complejidad bajas.
- Adicionalmente, `policy_kb.detect_intent_and_expand` detecta intenciones implicitas y expande SIEMPRE la query antes de retrieval.
  - Caso implementado: `child_labor`.
  - Reglas minimas: menciones de menor/niño/adolescente/trabajo infantil o edad <= 15 + raiz `trabaj`.
  - Expansion forzada: `trabajo infantil`, `esclavitud moderna`, `trabajo forzado`, `menores`, `edad minima`, `derechos humanos`.
- Retrieval ahora es `hybrid` (token overlap + BM25 con normalizacion y dedup), con boost explicito para chunks sobre trabajo infantil/esclavitud moderna/trabajo forzado.
- En intent `child_labor`, si no aparece evidencia relevante en top-k, se aplica fallback por match exacto de esas frases para no perder la Seccion 12 cuando corresponde.
- Debug KB se alinea con evidencia real usada:
  - muestra query original/expandida, intent/tags y `retrieval_method`;
  - lista final de chunks usados (los mismos que alimentan contexto y `Fuentes`).

### Strict gating especifico
- En `Solo KB (estricto)` + intent `child_labor`:
  - sin evidencia relevante: respuesta fija `No encuentro eso...` sin `Fuentes`;
  - con evidencia relevante: respuesta grounded fija (`rechaza trabajo infantil`) + aclaracion de que no hay edad minima explicita, con `Fuentes` de los chunks usados.
- En consultas que piden edad minima exacta en strict, si la evidencia no trae una edad explicita (ej. `X años`), se responde con fallback estricto sin `Fuentes`.

### Heuristica org-specific (anti alucinacion en General)
- Implementada en `ChatService.is_org_specific_query`.
- Señales:
  - Frases directas (`en la empresa`, `politica interna`, `codigo de conducta`, `RRHH`, `compliance`, etc.).
  - Nombre propio no inicial + terminos de politica/procedimiento.
  - Frase entre comillas + terminos de politica/procedimiento.

## Persistencia de datos
- Evaluaciones: `data/submissions.jsonl`.
- Override provider: `chatbot_mvp/data/app_settings.json`.

## Testing
- Suite principal: `python -m pytest`.
- Existe un test legacy de Reflex marcado como skipped (`tests/test_auth_state.py`).

## Legacy (Reflex)
El runtime actual no usa Reflex.

Restos legacy que aun existen en repo:
- `chatbot_mvp/components/` (archivos con dependencias historicas de Reflex)
- `.states/` (cache/artefactos legacy)
- `tests/test_auth_state.py` (skippeado)

Mantener estas referencias solo como contexto historico hasta su limpieza definitiva.
