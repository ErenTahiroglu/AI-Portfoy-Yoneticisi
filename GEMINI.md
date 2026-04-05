# 🏛️ GEMINI Context & Instructions: AI-Portfoy-Yoneticisi

Welcome to the AI-Portföy-Yöneticisi project. This document provides essential context and instructions to help you work effectively within this codebase.

## 📖 Project Overview

AI-Portföy-Yöneticisi is an AI-powered portfolio management and risk analysis platform. It uses a multi-agent AI orchestration (CIO Orchestrator) to analyze stocks, investment funds, and crypto assets.

## 🛠️ Core Technologies

- **Backend:** Python 3.x, FastAPI, LangGraph (for AI agents), LangChain.
- **Frontend:** Vanilla JS, HTML5, CSS3 (Strictly NO frameworks like React, Vue, Tailwind).
- **Database:** Supabase (PostgreSQL), Redis (Upstash) for caching/rate-limiting.
- **Deployment:** Vercel (Frontend), Render (Backend).
- **Testing:** Pytest, Puppeteer (UI tests).

## 🏗️ Architectural Patterns

- **Three-Tier Architecture:** Frontend (Presentation), Backend (Logic), Supabase/Redis (Data).
- **Puzzle Framework:** A modular approach used in both backend (`backend/nodes/`, `backend/engine/`) and frontend (`frontend/js/components/`).
- **Zero-Trust SRE:** Strict network isolation during tests (`pytest-socket`) and LLM mocking.

## 📜 Critical Development Rules

1. **Frontend Constraints:** Do NOT use React, Vue, Tailwind, Bootstrap, or any other JS/CSS frameworks. Stick to Vanilla JS and plain CSS.
2. **DOM Integrity:** Preserve existing `id` and `data-*` attributes in HTML. The JS logic in `frontend/js/` depends on them.
3. **Design Language:** Maintain a professional, dark-themed financial dashboard aesthetic inspired by `frontend/logo.png`.
4. **Security:**
   - Always use PII Sanitization before sending data to LLMs.
   - Use XML tags (e.g., `<news_item>`) to isolate external data in prompts.
   - Ensure all new API endpoints are protected by JWT and Rate Limiting.
   - **Requirements Proxy Rule:** The root `requirements.txt` file must ALWAYS remain a proxy (`-r backend/requirements.txt`). Do NOT add packages to the root `requirements.txt`. All backend dependencies must be placed in `backend/requirements.txt`.
5. **Testing:**
   - Add tests for new features.
   - Respect the `pytest-socket` isolation; use mocks for any external network calls.
   - Run `npm run test:ui` to verify frontend changes.

## 📂 Key Directories

- `/backend`: FastAPI application, AI agents, and business logic.
- `/frontend`: Static assets and Vanilla JS components.
- `/infrastructure`: Deployment and setup scripts.
- `/tests`: Python and Puppeteer test suites.

## 🚀 Common Commands

- **Run Backend:** `uvicorn backend.main:app --reload` (or use Docker)
- **Run Frontend:** Serve `frontend/` directory (e.g., `python -m http.server 3000`)
- **Docker Compose:** `docker-compose up --build`
- **Run Tests:** `pytest` (Backend), `npm run test:ui` (Frontend)

Refer to `README.md` and `ARCHITECTURE.md` for more detailed information.

## Communication Style

- I give terse directives. "go", "yes", "1" mean proceed immediately.
- "too much" / "too little" means adjust the last change by ~30%.
- I iterate visually -- expect 3-10 rounds of refinement on UI changes.
- Don't ask for confirmation on visual tweaks, just make the change.
- When I paste an error, fix it. Don't explain what went wrong unless asked.
- Keep responses short. Don't narrate what you're about to do.
- Speak like caveman. Short 3-6 word sentences. No filler, no pleasantries.
- Run tools first, show results, then stop. No narration on actions.
- Drop articles (a, an, the). Say "me fix code" not "I will fix the code".
- Shorter response always better. Concise descriptions only.
- Execute function calls/tools silently. Output raw data from tools, nothing else.
