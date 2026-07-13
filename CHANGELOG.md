# Changelog

All notable changes to BuiltByMe will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] — 2026-07-13

### Added

- **Repository Extraction Pipeline** — Clone and parse any public/private GitHub repository using the GitHub REST API.
- **Tree-sitter AST Parsing** — Local, privacy-first code intelligence for 12 languages: Python, JavaScript, TypeScript, Java, C, C++, Go, Rust, Ruby, PHP, C#, Kotlin.
- **Multi-Provider LLM Gateway** — Unified interface supporting Groq, Google Gemini, and Nvidia (via OpenAI-compatible endpoint) through LangChain.
- **14-Section Documentation Generator** — Structured, Pydantic-validated output for:
  1. Project Overview
  2. Tech Stack
  3. Architecture & Module Map
  4. Environment & Secrets
  5. Core Functions & Classes
  6. Technology Deep Dives (chunked per-framework generation)
  7. Design Decisions
  8. Failure Log & Learnings
  9. APIs & Interfaces
  10. Data Models & Storage
  11. Testing Strategy
  12. Scalability & Production
  13. Deployment & Infra
  14. Interview Question Bank
- **Intelligent Retrieval Strategies** — 1-pass (full dump) and 2-pass (skeleton → targeted retrieval) modes to optimize for token limits.
- **Premium PDF Export** — Styled HTML-to-PDF rendering via WeasyPrint with Mermaid.ink diagram support, colored badges, and dark headers.
- **Radial Generator UI** — Interactive, section-by-section generation interface with per-section settings (provider, key, detail level, skip/placeholder toggles).
- **API Key Vault** — Encrypted local storage of API keys using Fernet symmetric encryption with auto-generated master key.
- **Generate All** — Sequential batch generation across all 14 sections with global API key and strategy configuration.
- **In-App User Guide** — Comprehensive documentation covering every feature, customization option, and extensibility path.
- **GitHub PAT Management** — Persistent, encrypted storage for GitHub Personal Access Tokens.
- **Custom Ignore Patterns** — Glob-based file exclusion during extraction (e.g., `*.csv`, `node_modules`).

### Security

- All API keys are encrypted at rest using Fernet (AES-128-CBC).
- Repository parsing is entirely local — only targeted code chunks are sent to LLM providers.
- Master encryption key is auto-generated and excluded from version control via `.gitignore`.
