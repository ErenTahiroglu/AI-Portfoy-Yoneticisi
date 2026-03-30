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
