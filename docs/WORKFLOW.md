# Workflow Codex + Git

## Regla de oro
- Scope mínimo, sin refactors masivos.
- Criterios de aceptación claros y verificables.
- Salida concreta: archivos tocados, cómo verificar, y link del PR.

## Cómo arrancar una tarea
1) Pegar contexto:
   - `git status -sb`
   - `git diff --name-only`
   - `git log -5 --oneline`
2) Confirmar branch actual.

## Cómo debe trabajar Codex
- Crear un branch por tarea.
- Commits cortos con mensaje breve.
- Push y PR a `main`.
- El usuario aprueba solo cuando Codex lo pide.

## Template de prompt (copiar/pegar)
```
PROMPT BASE
- Trabajamos paso a paso y sin refactors masivos.
- Respetá estrictamente el scope: SOLO tocá los archivos permitidos.
- No agregues cambios "de mas". Si ves algo mejorable fuera de scope, anotarlo en docs/STATUS_REPORT.md como "Backlog" y no lo implementes.
- Al finalizar: dejá git status limpio, hacé commit(s) con mensaje corto, push y abrí PR a main.
- Entregá salida concreta: (1) archivos tocados, (2) comandos para verificar, (3) link del PR.

SCOPE
- Archivos permitidos: <lista>

ACEPTACIÓN
- <criterios claros>

ARCHIVOS PERMITIDOS
- <lista exacta>
```

## Política de limpieza
- Si el working tree está sucio: decidir entre stash/commit/revert.
- Documentar la decision en `docs/STATUS_REPORT.md` antes de ejecutar cambios.

## Cómo retomar después
1) Leer `docs/STATUS_REPORT.md`.
2) Revisar PRs abiertos en GitHub.
3) Confirmar branch actual y últimos commits:
   - `git status -sb`
   - `git log -5 --oneline`
