# Changelog

All notable changes to BuiltByMe will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.0] — 2026-07-26

### Added

- **PDF Color Theme Selector** — 6 visual design theme presets (Sunrise, Ocean, Forest, Royal, Midnight, Obsidian) accessible via split-color circular swatches below the "Generate PDF" button in the project sidebar.
- **Dark Theme Page Fix** — Configured WeasyPrint `@page` background property to fill margin areas, eliminating white borders in dark mode exports (Midnight and Obsidian themes).
- **User Guide: Extensibility Tutorial** — Detailed Step-by-step developer tutorial in the User Guide Modal explaining how to add custom documentation sections (Section 15+) across Pydantic schemas, radial JS layout, and backend routes.

## [1.1.0] — 2026-07-14

### Added

- **Toast Notification System** — Glassmorphic, animated toast notifications replace all native `alert()` calls. Supports 4 types: success (green), error (red), info (blue), warning (amber). Toasts auto-dismiss after 4 seconds and can be clicked to dismiss early.
- **Dark/Light Theme Toggle** — Sun/moon toggle button in the header switches between dark and light modes. The light theme features cream/white surfaces with preserved orange accents. Theme preference is persisted in `localStorage` and restored on reload. Smooth 350ms CSS transitions on all theme properties.
- **Section Inline Preview** — "Formatted Preview" / "Raw JSON" tab toggle in the generated content viewer. Renders section JSON as styled cards with color-coded badges, key-value layouts, and nested object support. Includes dedicated rendering for Section 6 (Technology Deep Dives) with categorized concept cards (Basics, Directly Used, Indirect) and syntax-highlighted code snippets.
- **Project Search & Filter** — Search input inside the projects dropdown menu with real-time filtering. Accessible via `Ctrl+K` keyboard shortcut.
- **Keyboard Shortcuts** — Power-user keyboard shortcuts: `Ctrl+N` (New Project), `Ctrl+K` (Search Projects), `Ctrl+,` (Configuration), `Ctrl+G` (Generate PDF), `Ctrl+M` (Export Markdown), `Esc` (Close any modal). Shortcuts are disabled when typing in input fields. Documented in User Guide section 15.
- **Markdown Export** — New `POST /api/project/<name>/markdown` endpoint converts all generated sections to a structured Markdown file with table of contents, nested heading hierarchy, lists, and formatted key-value pairs. "Export Markdown" button added to the project sidebar. Respects skip/placeholder section states.
- **User Guide: Keyboard Shortcuts** — Section 15 added to the in-app User Guide documenting all keyboard shortcuts with styled key cap badges.

### Changed

- All `alert()` calls across `app.js` and `generator.js` replaced with `showToast()` for consistent, non-blocking feedback.
- Generated content viewer defaults to "Formatted Preview" tab instead of raw JSON when selecting a section.
- Architecture diagram in README updated to include Markdown Exporter component.



---

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
