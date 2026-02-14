# CHANGELOG RECENT

Ultimos commits (git log --oneline -25):

- `07c4e26` fix: sidebar + KB integrated
- `b384e34` fix: chat flex layout + admin toast + gemini streaming
- `be7c6c0` feat: chat bubbles + admin toast + gemini fuller replies
- `f469bc7` fix: provider config only in Admin + strict lazy init
- `c22e99b` feat: Groq via OpenAI SDK + provider switch + no re-stream
- `69f959b` Docs: status report + Streamlit entrypoint
- `f10eff0` fix: import missing function in Admin.py and ensure consistent layout
- `6a94eea` fix: gemini 404, unify page widths, persistent provider switching, fixed sidebar footer
- `1db7df5` polish: final UI/UX cleanup, fix typing effect, fix sidebar logo position, fix Gemini model name
- `40cd8df` fix: remove chat history, fix sidebar positioning, fix all deprecations, correct Gemini model name
- `15224ad` feat: reorganize UI (logo/badge at bottom), unify CSS, improve typing effect, update .env docs
- `b660991` polish: fix deprecations, reduce badge size, add typing effect to feedback
- `b7e6b20` fix: add static feedback templates for evaluation results (Bajo, Medio, Alto)
- `5aec628` feat: complete migration to Streamlit with Admin 2.0 and Branding
- `8a4d4d3` fix: eval typewriter stable (#14)
- `a9284f8` fix: mark stream active immediately and add quick fallback to reveal text if stream is cancelled
- `8d54713` fix: schedule streaming only from finish(), add logs for show_loading and scheduling
- `1bbcfc7` fix: schedule clear_loading_timeout from finish() to ensure loading fallback
- `05211fb` fix: handle cancelled streaming and add fallback timeout to clear loading spinner
- `e43d2d0` chore: add debug logs for evaluation streaming progress
- `deb9776` fix: remove unused trigger method, use direct event invocation
- `ac0acde` fix: always disable show_loading after 2s, add debug logs
- `150a43f` fix: ensure show_loading state update before streaming
- `68e5621` fix: remove duplicate width in loading_analysis_view
- `776184b` feat: loading screen with 2s wait + visible typewriter effect
