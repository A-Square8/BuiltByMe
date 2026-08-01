# Contributing to BuiltByMe

Thank you for your interest in contributing to BuiltByMe! This guide will help you get set up and understand the project structure.

## Table of Contents

- [Development Setup](#development-setup)
- [Project Structure](#project-structure)
- [Adding a New LLM Provider](#adding-a-new-llm-provider)
- [Adding a New Tree-sitter Language](#adding-a-new-tree-sitter-language)
- [Adding a New Documentation Section](#adding-a-new-documentation-section)
- [Code Style](#code-style)
- [Submitting Changes](#submitting-changes)

---

## Development Setup

### Prerequisites

- Python 3.10 or higher
- pip (Python package manager)
- Git

### Getting Started

```bash
# Fork and clone
git clone https://github.com/A-Square8/BuiltByMe.git
cd BuiltByMe

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the development server
python3 main.py
```

The server starts at `http://localhost:5000` with Flask's debug mode enabled (auto-reload on code changes).

### First Run

On first run, the application will automatically:
1. Create a `my_projects/` directory for extracted project data
2. Generate a `.master.key` file for API key encryption
3. Create `config.json` for local configuration

These files are all gitignored and local to your machine.

---

## Project Structure

```
BuiltByMe/
├── main.py                    # Flask server — all routes + PDF generation
├── extraction/                # Core extraction engine
│   ├── pipeline.py            # ExtractionPipeline orchestrator
│   ├── github_fetcher.py      # GitHub REST API client
│   ├── extractors.py          # Per-language Tree-sitter extractors
│   ├── ts_parser.py           # Tree-sitter parser initialization
│   ├── language_detector.py   # File extension → language mapping
│   ├── file_filter.py         # Directory/file skip rules
│   ├── database.py            # SQLite ORM (ProjectDB class)
│   ├── llm_gateway.py         # Multi-provider LangChain LLM client
│   └── prompts.py             # Pydantic schemas + system prompts
└── ui/                        # Frontend (served as static files by Flask)
    ├── index.html             # Single-page application
    ├── app.js                 # Core UI logic
    ├── generator.js           # Radial generator interface
    ├── style.css              # Base design system
    └── generator.css          # Generator-specific styles
```

### Key Design Decisions

- **No frontend build step**: The UI is plain HTML/CSS/JS served directly by Flask. No npm, no bundler. This keeps the project simple and contributor-friendly.
- **Single `main.py`**: All Flask routes and PDF generation live in one file. While large, this avoids import complexity and makes the API surface immediately discoverable.
- **LangChain for LLM abstraction**: Providers are swapped by instantiating a different LangChain wrapper. Structured output uses `with_structured_output()` (or `PydanticOutputParser` for providers that don't support it natively).

---

## Adding a New LLM Provider

This is one of the most common contributions. Here's a step-by-step guide:

### Step 1: Install the LangChain Package

```bash
pip install langchain-anthropic   # Example: adding Anthropic Claude
```

Add it to `requirements.txt`:
```
langchain-anthropic>=0.1.0
```

### Step 2: Update `extraction/llm_gateway.py`

Add a new `elif` block in the `get_llm_client()` function:

```python
elif provider == 'anthropic':
    from langchain_anthropic import ChatAnthropic
    return ChatAnthropic(
        api_key=api_key,
        model="claude-sonnet-4-20250514",
        temperature=temperature
    )
```

### Step 3: Update the Frontend

In `ui/index.html`, add the option to **both** provider dropdowns:

```html
<!-- In the section panel (#genProvider) -->
<option value="anthropic">Anthropic</option>

<!-- In the config modal (#newKeyProvider) -->
<option value="anthropic">Anthropic</option>
```

### Step 4: Test

1. Run the server
2. Add your API key in Configuration
3. Generate a section using the new provider
4. Verify the structured output parses correctly

---

## Adding a New Tree-sitter Language

### Step 1: Install the Grammar Package

```bash
pip install tree-sitter-swift   # Example: adding Swift
```

Add it to `requirements.txt`:
```
tree-sitter-swift>=0.1.0
```

### Step 2: Register the Parser in `extraction/ts_parser.py`

Add the language to the `LANGUAGES` dictionary:

```python
import tree_sitter_swift as ts_swift

LANGUAGES = {
    # ... existing languages ...
    'swift': ts_swift.language(),
}
```

### Step 3: Add the Language Detector Mapping

In `extraction/language_detector.py`, add the file extension mapping:

```python
EXTENSION_MAP = {
    # ... existing mappings ...
    '.swift': 'swift',
}
```

### Step 4: Create an Extractor (Optional but Recommended)

For deep extraction, add a dedicated function in `extraction/extractors.py`:

```python
def extract_swift(source):
    tree = parse_code(source, 'swift')
    if not tree:
        return {}, []
    root = tree.root_node
    blocks = []
    # Extract imports, classes, functions, etc.
    # Use _walk_tree() and _node_text() helpers
    imports = [_node_text(n, source).strip() for n in _walk_tree(root, {'import_declaration'})]
    # ... (inspect the AST node types for Swift using tree-sitter playground)
    return {'imports': imports, 'functions': functions, 'classes': classes}, blocks
```

Register it in the `EXTRACTORS` dict at the bottom of the file:

```python
EXTRACTORS = {
    # ... existing entries ...
    'swift': extract_swift,
}
```

If you skip this step, the `extract_generic()` function will handle it with reasonable defaults.

### Tip: Inspecting AST Node Types

Use the [Tree-sitter Playground](https://tree-sitter.github.io/tree-sitter/playground) to explore the AST node types for your target language. This tells you exactly what node types to look for (e.g., `function_declaration`, `class_declaration`, `import_statement`).

---

## Adding a New Documentation Section

> **Note:** For users who want to add custom sections without writing code, BuiltByMe now supports **UI-based custom sections**. Go to **⋮ menu → Custom Sections** in the app to create custom documentation sections with neon-cyan radial nodes, AI generation, and export support — no code changes required.
>
> The steps below are for **developers** who want to add permanent, built-in sections to the core product.

### Step 1: Define the Pydantic Schema

In `extraction/prompts.py`, create a new Pydantic model:

```python
class Section15NewSection(BaseModel):
    overview: str
    items: list[dict]
    # ... define your schema
```

### Step 2: Write the System Prompt

Add a prompt constant and register both in the section maps:

```python
SECTION_15_PROMPT = """You are a technical documentation expert..."""

SECTION_SCHEMAS[15] = Section15NewSection
SECTION_PROMPTS[15] = SECTION_15_PROMPT
```

### Step 3: Add PDF Rendering

In `main.py`, inside the `generate_pdf()` function, add an `elif sid == 15:` block to render your section's HTML.

### Step 4: Update the UI

In `ui/generator.js`, add the section to the `SECTIONS` array to make it appear as a node on the radial generator.

---

## Code Style

- **Python**: Follow PEP 8. Use type hints where practical. Keep functions focused.
- **JavaScript**: Use `const`/`let` (no `var`). Use template literals for HTML generation.
- **HTML/CSS**: Use CSS custom properties (variables) defined in `style.css`. Follow the existing dark-theme design language.
- **Commits**: Use clear, descriptive commit messages. Mention what was added/changed/fixed.

---

## Submitting Changes

1. **Fork** the repository
2. **Create a feature branch**: `git checkout -b feature/add-anthropic-provider`
3. **Make your changes** with clear commits
4. **Test** your changes locally (run the server, generate a section, export a PDF)
5. **Push** your branch and open a **Pull Request**

### PR Checklist

- [ ] New dependencies added to `requirements.txt`
- [ ] Provider/language registered in all relevant files
- [ ] Tested with at least one real generation
- [ ] No hardcoded API keys or secrets
- [ ] Follows existing code patterns

---

## Questions?

Open an [issue](https://github.com/A-Square8/BuiltByMe/issues) and we'll be happy to help!

