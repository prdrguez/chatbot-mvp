# Workflow Codex + Git

## Regla de oro
- Scope minimo, sin refactors masivos.
- Criterios de aceptacion claros y verificables.
- Salida concreta: archivos tocados, como verificar y link del PR.

## Inicio de cada tarea (PowerShell)
1. Ejecutar:
   - `git status -sb`
   - `git diff --name-only`
   - `git log -10 --oneline`
2. Confirmar branch actual.
3. Confirmar archivos permitidos.

## Como trabaja Codex en este repo
- Crea branch por tarea.
- Aplica cambios dentro del scope.
- Ejecuta verificaciones pedidas.
- Hace commit(s) cortos.
- Hace push del branch.
- Abre PR a `main`.
- Usuario solo aprueba (no tiene que ejecutar pasos tecnicos).

## Commits y PR
- Commits: mensaje muy corto, una linea.
- PR body: texto plano.
- No usar backticks ni bloques de codigo en el body del PR.
- Incluir checklist de verificacion en el PR.

## Comandos y snippets
- Usar siempre PowerShell en cualquier "Como verificar" o bloque de comandos.

## Template de prompt (copiar/pegar)
PROMPT BASE
- Trabajamos paso a paso y sin refactors masivos.
- Respetar estrictamente el scope: SOLO tocar archivos permitidos.
- No agregar cambios de mas. Si aparece mejora fuera de scope, anotar en docs/STATUS_REPORT.md como Backlog y no implementarla.
- Al finalizar: dejar git status limpio, hacer commit(s) cortos, push y abrir PR a main.
- Entregar salida concreta: (1) archivos tocados, (2) comandos para verificar en PowerShell, (3) link del PR.
- IMPORTANTE: body del PR en texto plano, sin backticks ni bloques.

SCOPE
- Archivos permitidos: <lista exacta>

ACEPTACION
- <criterios claros y medibles>

PASOS (Codex)
1) Confirmar estado del repo.
2) Implementar cambios en scope.
3) Verificar.
4) Commit + push + PR.
5) Reportar salida final.

## Como retomar una tarea
1. Leer `docs/STATUS_REPORT.md`.
2. Revisar PRs abiertos.
3. Confirmar estado local:
   - `git status -sb`
   - `git log -10 --oneline`
