# BuiltByMe API Documentation

Base URL: `http://localhost:5000`

All endpoints return JSON unless otherwise noted. Request bodies should be `Content-Type: application/json`.

---

## Table of Contents

- [Projects](#projects)
- [Repository Extraction](#repository-extraction)
- [Configuration](#configuration)
- [Section Generation](#section-generation)
- [Generated Content](#generated-content)
- [PDF Export](#pdf-export)

---

## Projects

### List All Projects

```
GET /api/projects
```

Returns a list of all extracted projects.

**Response** `200 OK`
```json
[
  {
    "name": "flask",
    "info": {
      "name": "flask",
      "full_name": "pallets/flask",
      "description": "The Python Micro Framework",
      "language": "Python",
      "stars": 68000,
      "forks": 16200
    },
    "extraction_status": "completed"
  }
]
```

---

### Get Project Details

```
GET /api/project/<project_name>
```

Returns full project data including files, commits, and code blocks.

**Response** `200 OK`
```json
{
  "info": { "name": "...", "full_name": "...", ... },
  "files": [
    {
      "id": 1,
      "path": "src/app.py",
      "language": "python",
      "size": 4200,
      "metadata": { "imports": [...], "classes": [...], "functions": [...] },
      "blocks": [
        {
          "block_type": "function",
          "name": "create_app",
          "parent_name": null,
          "start_line": 10,
          "end_line": 45,
          "content": "def create_app(config):\n    ..."
        }
      ]
    }
  ],
  "commits": [
    { "sha": "a1b2c3d", "message": "Initial commit", "author": "dev", "date": "2026-01-01T00:00:00Z" }
  ],
  "extraction_status": { "status": "completed", ... }
}
```

---

### Delete Project

```
DELETE /api/project/<project_name>/delete
```

Permanently deletes the project directory and all associated data.

**Response** `200 OK`
```json
{ "message": "Deleted" }
```

---

## Repository Extraction

### Start Extraction

```
POST /api/extract
```

Begins asynchronous repository extraction in a background thread.

**Request Body**
```json
{
  "repo_url": "https://github.com/pallets/flask",
  "token": "ghp_xxxx",
  "ignore_patterns": "*.csv, docs/, test*"
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `repo_url` | string | ✅ | GitHub repository URL |
| `token` | string | ❌ | GitHub PAT (falls back to saved PAT) |
| `ignore_patterns` | string | ❌ | Comma-separated glob patterns to exclude |

**Response** `200 OK`
```json
{ "message": "Extraction started", "project_name": "flask" }
```

**Error Responses**
- `400` — Missing or invalid repository URL
- `409` — Extraction already in progress for this repo

---

### Poll Extraction Status

```
GET /api/extract/status/<project_name>
```

Returns the current extraction progress. Poll this endpoint at ~1s intervals.

**Response** `200 OK`
```json
{
  "status": "extracting",
  "total": 150,
  "processed": 42,
  "current_file": "src/core/app.py",
  "errors": []
}
```

**Status Values**: `starting`, `fetching_info`, `fetching_commits`, `fetching_tree`, `extracting`, `completed`, `failed`

---

## Configuration

### GitHub PAT

#### Get Saved PAT

```
GET /api/config/pat
```

Returns the saved PAT (masked for security).

**Response** `200 OK`
```json
{ "pat": "************************************abcd", "has_pat": true }
```

#### Save PAT

```
POST /api/config/pat
```

**Request Body**
```json
{ "pat": "ghp_xxxxxxxxxxxxxxxxxxxx" }
```

Send an empty string to clear the saved PAT.

---

### LLM API Keys

#### List Saved Keys

```
GET /api/config/llm_keys
```

Returns all saved keys (values are masked).

**Response** `200 OK`
```json
[
  { "name": "My Groq Key", "provider": "groq", "key": "********abcd" },
  { "name": "Gemini Free", "provider": "gemini", "key": "********efgh" }
]
```

#### Add a Key

```
POST /api/config/llm_keys
```

**Request Body**
```json
{
  "name": "My Groq Key",
  "provider": "groq",
  "key": "gsk_xxxxxxxxxxxx"
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `name` | string | ✅ | Display name for the key |
| `provider` | string | ✅ | One of: `groq`, `gemini`, `nvidia` |
| `key` | string | ✅ | The API key value |

#### Delete a Key

```
DELETE /api/config/llm_keys/<index>
```

Deletes the key at the specified index (0-based).

---

## Section Generation

### Generate a Section (1–5, 7–14)

```
POST /api/project/<project_name>/generate
```

Generates a single documentation section using the specified LLM.

**Request Body**
```json
{
  "section_id": 3,
  "provider": "gemini",
  "api_key": "saved_0",
  "strategy": "2_pass",
  "detail_level": 2,
  "custom_instructions": "Focus on the Flask routing layer"
}
```

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `section_id` | int | ✅ | — | Section number (1–14, except 6) |
| `provider` | string | ✅ | — | `groq`, `gemini`, or `nvidia` |
| `api_key` | string | ✅ | — | Raw API key or `saved_N` reference |
| `strategy` | string | ❌ | `1_pass` | `1_pass` or `2_pass` |
| `detail_level` | int | ❌ | `1` | 0=Short, 1=Medium, 2=Detailed |
| `custom_instructions` | string | ❌ | `""` | Additional context for the LLM |

**Note on `api_key`**: Use `"saved_0"`, `"saved_1"`, etc. to reference keys saved in Configuration (by index). The server decrypts and resolves the actual key + provider.

**Response** `200 OK`
```json
{
  "message": "Success",
  "content": { ... },
  "passes": [
    { "pass": 1, "info": "LLM analyzed skeleton and requested 8 files", "reasoning": "..." },
    { "pass": 2, "info": "Retrieved 8 files for focused generation" }
  ]
}
```

---

### Generate Section 6 (Technology Deep Dives)

```
POST /api/project/<project_name>/generate_s6
```

Section 6 uses a chunked, multi-phase generation approach.

#### Phase 1: Discovery

**Request Body**
```json
{
  "provider": "gemini",
  "api_key": "saved_0",
  "phase": "discovery"
}
```

**Response** `200 OK`
```json
{
  "message": "Discovery complete",
  "phase": "discovery",
  "frameworks": [
    { "name": "Flask", "category": "Web Framework", "relevant_files": ["main.py", "..."] },
    { "name": "Tree-sitter", "category": "Parser", "relevant_files": ["extraction/ts_parser.py", "..."] }
  ],
  "total": 5,
  "completed": ["Flask"],
  "remaining": [{ "name": "Tree-sitter", ... }]
}
```

#### Phase 2: Deep Dive (per framework)

**Request Body**
```json
{
  "provider": "gemini",
  "api_key": "saved_0",
  "phase": "deep_dive",
  "framework_index": 1,
  "detail_level": 2
}
```

**Response** `200 OK`
```json
{
  "message": "Tree-sitter deep dive complete",
  "phase": "deep_dive",
  "framework_name": "Tree-sitter",
  "framework_index": 1,
  "content": { "framework_name": "Tree-sitter", "basics": [...], ... },
  "progress": { "completed": 2, "total": 5 }
}
```

---

## Generated Content

### List Generated Sections

```
GET /api/project/<project_name>/generated
```

Returns all generated sections for a project.

**Response** `200 OK`
```json
[
  {
    "section_id": 1,
    "name": "Project Overview",
    "content": { "summary": "...", "purpose": "...", ... },
    "generated_at": "2026-07-13T10:30:00"
  },
  {
    "section_id": 3,
    "name": "Architecture & Module Map",
    "content": { "folder_tree": "...", "modules": [...], ... },
    "generated_at": "2026-07-13T10:35:00"
  }
]
```

---

### Delete a Generated Section

```
DELETE /api/project/<project_name>/generated/<section_id>
```

Deletes the generated content for a specific section. The section can then be regenerated.

**Response** `200 OK`
```json
{ "message": "Deleted successfully" }
```

---

## PDF Export

### Generate PDF

```
POST /api/project/<project_name>/pdf
```

Generates a styled PDF from all generated sections and returns it as a downloadable file.

**Request Body** (optional)
```json
{
  "skip_sections": [11, 12],
  "placeholder_sections": [8]
}
```

| Field | Type | Description |
|---|---|---|
| `skip_sections` | int[] | Section IDs to exclude entirely from the PDF |
| `placeholder_sections` | int[] | Section IDs to include as heading-only placeholders |

**Response** `200 OK` — Binary PDF file (`application/pdf`)

Also supports `GET /api/project/<project_name>/pdf` (no skip/placeholder config).

**Error Responses**
- `404` — Project not found
- `500` — PDF dependencies not installed (WeasyPrint, markdown2)

---

## Error Handling

All error responses follow this format:

```json
{
  "error": "Human-readable error message"
}
```

Some endpoints include additional debugging info:

```json
{
  "error": "Error during content generation: ...",
  "traceback": "Traceback (most recent call last):\n  ..."
}
```

Common HTTP status codes:
- `400` — Invalid request (missing fields, bad format)
- `404` — Project or resource not found
- `409` — Conflict (e.g., extraction already running)
- `500` — Server error (LLM failure, missing dependencies)
