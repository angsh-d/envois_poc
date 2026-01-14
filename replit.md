# H-34 Clinical Intelligence Platform

## Overview
The H-34 Clinical Intelligence Platform is a multi-agent AI system designed for clinical data analysis, risk assessment, and regulatory compliance specifically for the H-34 DELTA Revision Cup post-market clinical study. It features an Apple-inspired React frontend with comprehensive dashboards covering five key use cases: Regulatory Readiness, Safety Signals, Protocol Deviations, Patient Risk, and Executive Dashboard. The platform aims to provide deep insights into clinical study data, enhance regulatory compliance, and improve patient safety through advanced AI and data analytics.

## User Preferences
The user prefers an Apple-inspired design aesthetic, characterized by a clean, minimal interface with generous whitespace, SF Pro / Inter typography, a black/white/gray color palette with semantic accents, rounded corners, and smooth transitions/hover states.

## System Architecture
The application is structured as a full-stack project with a Python FastAPI backend and a React + Vite + Tailwind frontend.

**Frontend:**
- Developed using React 18, TypeScript, Vite 7 for building, Tailwind CSS 4 for styling, React Query for data fetching, Wouter for routing, and Lucide React for icons.
- Features comprehensive pages for each of the five use cases, a landing page, a digital protocol viewer, and a data & agents catalog.
- UI/UX decisions follow an Apple-inspired design system focusing on cleanliness, minimalism, and intuitive user experience.

**Backend:**
- Built with Python 3.11 and FastAPI.
- Utilizes LangChain for LLM orchestration and Google Gemini as the LLM provider for AI functionalities, including contextual AI chat.
- The core logic is organized into agents (e.g., data, protocol, literature), API routers, and business logic services.
- Data loading employs a hybrid approach, prioritizing PostgreSQL but falling back to local YAML files for seamless transitions.

**Feature Specifications:**
- **Regulatory Readiness (UC1):** Gap analysis and compliance monitoring.
- **Safety Signals (UC2):** Cross-source contextualization of safety signals with detailed provenance and transparency.
- **Protocol Deviations (UC3):** Document-as-Code detection of protocol deviations.
- **Patient Risk (UC4):** ML-powered patient risk stratification.
- **Executive Dashboard (UC5):** KPIs, readiness metrics, and safety signals overview.
- **Digital Protocol:** Interactive views for Statement of Work (SOA), Eligibility Criteria, and Domain-specific protocol details.
- **Data & Agents Catalog:** Visualization and documentation of data sources, AI/ML models, and agent architecture.
- **Simulation Studio:** Monte Carlo simulations for regulatory benchmark probability analysis with interactive what-if scenarios.
- **Code Generation Agent:** AI-powered code generation for ad-hoc statistical queries in R, Python, SQL, and C with domain knowledge of clinical research, the H-34 study data model, and database schema.

**System Design Choices:**
- **Multi-agent AI system:** Employs specialized AI agents for different clinical intelligence tasks.
- **Database-first approach:** All structured and vector data is stored in PostgreSQL, leveraging pgvector for vector embeddings with HNSW indexing for efficient RAG operations.
- **Containerized Deployment:** Designed for Autoscale deployment with stateless components.
- **API-driven:** Provides a clear API structure for interaction between frontend and backend components.

## External Dependencies
- **Google Gemini:** Large Language Model (LLM) provider for AI features and contextual chat.
- **PostgreSQL with pgvector:** Primary database for all structured data and vector embeddings.
- **FastAPI:** Python web framework for backend API.
- **React:** JavaScript library for building user interfaces.
- **Vite:** Next-generation frontend tooling for fast development.
- **Tailwind CSS:** Utility-first CSS framework for styling.
- **LangChain:** Framework for developing applications powered by language models.