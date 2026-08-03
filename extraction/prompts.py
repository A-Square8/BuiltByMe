from pydantic import BaseModel, Field
from typing import List

class ProjectOverview(BaseModel):
    project_name: str = Field(
        ..., 
        description="The formal name of the project. If not explicitly stated, infer from the repository name."
    )
    one_liner: str = Field(
        ..., 
        description="A concise, high-impact single sentence describing what the project is and what it does."
    )
    domain: str = Field(
        ..., 
        description="The industry or technical domain (e.g., AI/ML, Backend, Data, FinTech, E-commerce)."
    )
    tech_stack: str = Field(
        ..., 
        description="The primary programming languages used (e.g., Python, TypeScript, Go)."
    )
    detected_ide: str = Field(
        ..., 
        description="The primary IDE or environment detected (e.g., VSCode, IntelliJ, Generic)."
    )
    problem_solved: str = Field(
        ..., 
        description="A paragraph (Medium detail) explaining the core problem the software solves and the friction it eliminates."
    )
    core_user_flow: str = Field(
        ..., 
        description="A paragraph (Medium detail) explaining exactly how a user interacts with the system from start to finish."
    )
    scale_and_deployment: str = Field(
        ..., 
        description="A paragraph explaining where it is deployed, how it scales, and the infrastructure used (e.g., Render, AWS, Redis)."
    )
    technically_interesting: str = Field(
        ..., 
        description="A paragraph highlighting the most complex, non-trivial, or impressive technical aspects of the architecture."
    )
    current_limitation: str = Field(
        ..., 
        description="A paragraph outlining current bottlenecks, technical debt, or limitations of the system."
    )
    complexity: str = Field(
        ..., 
        description="A single word or short phrase describing the difficulty (e.g., Beginner, Intermediate, Advanced)."
    )
    sixty_second_pitch: str = Field(
        ..., 
        description="A cohesive 60-second elevator pitch written in the first person ('I built...') summarizing the problem, solution, tech stack, and why it's impressive."
    )


SECTION_1_SYSTEM_PROMPT = """You are an expert Principal Software Engineer and Technical Recruiter analyzing a codebase. 
Your goal is to extract a comprehensive "Project Overview" that a software engineer can use to confidently talk about their project in a senior-level technical interview.

You will be provided with raw files, documentation, and metadata extracted from the project's repository.

# Instructions
1. Analyze the provided codebase context and extract the structural and high-level details of the project.
2. Fill out the requested JSON structure exactly. Do not leave any fields blank; if a piece of information is missing from the context, logically infer it based on the surrounding code, or state a reasonable assumption.
3. Detail Level: MEDIUM. Provide ample detail for the paragraph fields (`problem_solved`, `core_user_flow`, `scale_and_deployment`, `technically_interesting`, `current_limitation`). Aim for 3-5 sentences per paragraph.
4. The `sixty_second_pitch` MUST be written in the first person (e.g., "I built...", "I designed..."). It should read like a passionate engineer pitching their project to a hiring manager, summarizing the problem, the technical solution, and the architecture in about 150-200 words.

# Rules
- Do not hallucinate external libraries that are not in the codebase.
- Be highly technical but concise. Focus on the "Why" and "How" rather than just listing features.
"""

class TechStackItem(BaseModel):
    technology: str = Field(
        ..., 
        description="Name of the technology, library, or framework"
    )
    category: str = Field(
        ..., 
        description="The domain/category of the tech (e.g., 'Backend Framework', 'State Management', 'Database')"
    )
    why_used: str = Field(
        ..., 
        description="Explain like you're telling an interviewer: 'I picked Flask because...' — conversational, first-person, not a textbook definition."
    )
    alternatives_considered: List[str] = Field(
        ..., 
        description="A list of alternative technologies that compete in the same space"
    )
    why_alternatives_rejected: str = Field(
        ..., 
        description="Explain like an interviewer asked 'Why not Django?' — give a real, opinionated answer with specific trade-offs, not a generic comparison."
    )
    scenarios_for_alternatives: str = Field(
        ..., 
        description="Answer like an interviewer asked 'When WOULD you switch to Django?' — give concrete scenarios, not vague generalities."
    )

class Section2TechStack(BaseModel):
    core_stack: List[TechStackItem] = Field(
        ..., 
        description="An exhaustive list of the core technologies identified from the project's imports"
    )
    architecture_summary: str = Field(
        ..., 
        description="A 2-3 sentence summary of the tech stack, written like you're opening a conversation: 'So the project is basically a Python backend that...' — natural and opinionated."
    )

SECTION_2_SYSTEM_PROMPT = """You are a senior engineer helping someone prepare for a technical interview about their project.
Your goal is to analyze the tech stack and help them explain their technology choices confidently.

You will be provided with a list of all imports across the entire repository.

# Instructions
1. Analyze the imports and identify the core frameworks, libraries, and tools.
2. For each technology, explain WHY it was chosen — write like you're coaching someone to answer "Why did you use X?"
3. For alternatives, write like you're preparing them for "Why not Y instead?" — give real, opinionated trade-off answers.
4. For scenarios, prepare them for "When WOULD you use Y?" — concrete, specific answers.

# CRITICAL — Writing Style
- Write like you are EXPLAINING to an interviewer, NOT writing a Wikipedia article.
- Use first person: "I chose Flask because...", "The reason I went with SQLite here is..."
- Be opinionated and specific. Say "Flask is lighter than Django and I didn't need an ORM" NOT "Flask is a micro-framework that provides flexibility."
- Sound like a real engineer talking, not a textbook. Short punchy sentences. Real trade-offs.
- Every field should sound like something you'd actually SAY out loud in an interview.

# Rules
- Do not hallucinate external libraries that are not suggested by the imports.
- Only focus on CORE technologies, not standard library imports or minor utilities.
"""

class FileRetrievalRequest(BaseModel):
    """Schema for Pass 1 of 2-pass retrieval: LLM requests specific files."""
    reasoning: str = Field(
        ...,
        description="Brief explanation of why these files are needed to generate the requested section."
    )
    requested_files: List[str] = Field(
        ...,
        description="List of file paths (exactly as provided in the skeleton) that you need to see the full source code of to generate the section. Select only the most relevant files. Maximum 15 files."
    )

FILE_RETRIEVAL_PROMPT = """You are a code analysis assistant performing the FIRST PASS of a two-pass retrieval strategy.

You are given a SKELETON of a codebase: file paths, sizes, languages, and metadata summaries (imports, class/function names). You do NOT have the actual source code yet.

Your task is to select which files you need to see the full source code of in order to generate a specific documentation section.

# Instructions
1. Analyze the file skeleton and metadata carefully.
2. Select ONLY the files that are most relevant to the requested section topic.
3. Prefer files that are likely to contain core logic, configurations, or documentation relevant to the section.
4. You may request UP TO 15 files. Be selective — do not request every file.
5. Return the exact file paths as they appear in the skeleton.
6. Provide a brief reasoning for your selection.

# Rules
- Do NOT request binary files, images, or lock files.
- Prioritize source code files over configuration files unless the section is specifically about configuration.
- If the project is small (< 15 files), you may request all source files.
"""

# ===== Section 3: Architecture & Module Map =====

class ModuleInfo(BaseModel):
    folder_or_file: str = Field(
        ...,
        description="The folder name or file name (e.g., 'extraction/', 'main.py', 'ui/')."
    )
    purpose: str = Field(
        ...,
        description="Explain this module like you're walking an interviewer through: 'So this folder handles all the...' — 1-2 sentences, conversational."
    )
    key_files: List[str] = Field(
        ...,
        description="Most important files inside this module with brief descriptions (e.g., 'pipeline.py - this is the main orchestrator that kicks off the whole extraction')."
    )

class DataFlowStep(BaseModel):
    step_number: int = Field(
        ...,
        description="Sequential step number (1, 2, 3, ...)."
    )
    description: str = Field(
        ...,
        description="Describe what happens at this step like you're explaining it: 'First, the user pastes a GitHub URL and hits extract...' — natural and clear."
    )
    modules_involved: List[str] = Field(
        ...,
        description="Which modules/files are involved in this step."
    )

class Section3Architecture(BaseModel):
    folder_tree: str = Field(
        ...,
        description="A clean ASCII folder tree showing the project structure. Use tree characters like |, --, and indentation. Only show important folders and files, not every single file."
    )
    modules: List[ModuleInfo] = Field(
        ...,
        description="A list of top-level modules/folders with their purpose and key files."
    )
    entry_points: List[str] = Field(
        ...,
        description="List of entry points, explained naturally (e.g., 'main.py — this is where the Flask server boots up and all routes are defined')."
    )
    data_flow: List[DataFlowStep] = Field(
        ...,
        description="Step-by-step description of how data flows through the system."
    )
    architecture_diagram: str = Field(
        ...,
        description="""A Mermaid flowchart diagram showing the main components and how they connect.
Use Mermaid graph syntax. Keep it clean with 4-8 nodes max. Use proper shapes:
- Rectangles for services/components: A[Flask API]
- Rounded rectangles for user-facing: A(Browser)
- Cylinders for databases: A[(SQLite DB)]
- Diamonds for decisions: A{Has Cache?}

Example:
graph LR
    A(Browser) --> B[Flask API]
    B --> C[(SQLite DB)]
    B --> D[LLM Gateway]
    D --> E((Groq/Gemini))
"""
    )
    data_flow_diagram: str = Field(
        ...,
        description="""A Mermaid flowchart showing the data flow through the system with decision points.
Use Mermaid graph syntax with TD (top-down) direction. Include diamond decision nodes where the flow branches.

Example:
graph TD
    A[User submits URL] --> B[Extract repo metadata]
    B --> C{Files extracted?}
    C -->|Yes| D[Parse with Tree-sitter]
    C -->|No| E[Show error]
    D --> F[Store in SQLite]
    F --> G[Ready for generation]
"""
    )
    architecture_style: str = Field(
        ...,
        description="Describe the pattern like you're answering 'What's the architecture?' in an interview — e.g., 'It's basically a monolithic Flask app with a pipeline pattern — request comes in, gets processed through stages, and stored in SQLite.'"
    )
    layer_breakdown: str = Field(
        ...,
        description="Describe layers conversationally: 'At the top you've got the browser UI, that talks to a Flask REST API, which delegates to the extraction pipeline and LLM gateway, and everything gets persisted in SQLite.'"
    )

SECTION_3_SYSTEM_PROMPT = """You are a senior engineer helping someone explain their project's architecture in a technical interview.

You will be provided with the project's source code, file structure, and metadata.

# Instructions
1. Create a clean folder tree of the important project structure.
2. Describe each module/folder — what it does and why it exists.
3. Identify entry points.
4. Map the data flow step-by-step.
5. Create TWO Mermaid diagrams:
   a. Architecture diagram — a clean flowchart showing how the main components connect (use graph LR or graph TD).
   b. Data flow diagram — a flowchart with DECISION DIAMONDS showing how data moves through the system, including branching paths.
6. Describe the architectural style and layers.

# Mermaid Diagram Rules
- Use valid Mermaid `graph` syntax (graph LR for architecture, graph TD for data flow).
- Use proper shapes: rectangles [text], rounded (text), cylinders [(text)], diamonds {text}.
- Keep architecture diagram to 4-8 nodes. Show the big picture.
- Data flow diagram should include at least 2-3 decision points (diamond nodes) showing where the flow branches.
- Use descriptive but SHORT labels inside nodes.
- Connect with arrows: --> for normal flow, -->|label| for labeled edges.
- Do NOT wrap the diagram in markdown code fences — just output the raw Mermaid syntax starting with `graph`.

# CRITICAL — Writing Style
- Write ALL text fields like you're explaining to an interviewer face-to-face.
- Use first person: "So the way I structured this is...", "The main entry point is main.py, that's where..."
- Be specific and opinionated, not generic. Say what things DO, not what they "are responsible for."
- Short, punchy sentences. Not academic paragraphs.

# Rules
- Be accurate — only describe modules and files that actually exist.
- Do not hallucinate files or modules not present in the codebase.
"""

# ===== Section 4: Environment & Secrets =====

class EnvVariable(BaseModel):
    name: str = Field(
        ...,
        description="The environment variable name (e.g., 'DATABASE_URL', 'API_KEY', 'DEBUG')."
    )
    purpose: str = Field(
        ...,
        description="Explain like: 'This stores the database connection string' — simple and direct."
    )
    required: bool = Field(
        ...,
        description="Whether this variable is required for the app to run."
    )
    example_value: str = Field(
        ...,
        description="An example value (use dummy/placeholder values, never real secrets)."
    )
    where_used: str = Field(
        ...,
        description="Which file(s) or module(s) reference this variable."
    )

class ConfigFile(BaseModel):
    file_path: str = Field(
        ...,
        description="Path to the configuration file."
    )
    purpose: str = Field(
        ...,
        description="Explain like: 'This is the main config file — it stores API keys, GitHub PAT, and saved LLM provider settings.'"
    )
    format: str = Field(
        ...,
        description="File format (e.g., 'JSON', 'YAML', 'TOML', '.env')."
    )
    key_settings: List[str] = Field(
        ...,
        description="Most important settings with brief descriptions, explained naturally."
    )

class SecretInfo(BaseModel):
    name: str = Field(
        ...,
        description="Name or type of the secret (e.g., 'GitHub PAT', 'LLM API Key')."
    )
    how_stored: str = Field(
        ...,
        description="Explain like answering 'How do you store secrets?': 'I encrypt them using Fernet symmetric encryption and store the ciphertext in config.json.'"
    )
    how_accessed: str = Field(
        ...,
        description="Explain like: 'At runtime, the app reads the encrypted value from config.json and decrypts it using the master key.'"
    )
    rotation_strategy: str = Field(
        ...,
        description="Explain like: 'The user can rotate keys through the UI config modal — it re-encrypts and saves automatically.'"
    )

class Section4Environment(BaseModel):
    env_variables: List[EnvVariable] = Field(
        ...,
        description="List of all environment variables used or expected by the application."
    )
    config_files: List[ConfigFile] = Field(
        ...,
        description="List of configuration files in the project."
    )
    secrets: List[SecretInfo] = Field(
        ...,
        description="List of secrets the application handles."
    )
    dev_vs_prod: str = Field(
        ...,
        description="Explain like an interviewer asked 'How does your dev setup differ from prod?' — be specific: 'In dev I run with Flask debug=True on localhost:5000, and secrets are stored locally. In production you'd want to...'"
    )
    setup_steps: List[str] = Field(
        ...,
        description="Setup steps written like you're onboarding a teammate: 'First, clone the repo. Then create a venv and pip install -r requirements.txt. After that, you need to...'"
    )
    security_considerations: str = Field(
        ...,
        description="Answer like the interviewer asked 'What about security?' — be honest about what's good and what could improve: 'So the secrets are encrypted with Fernet which is solid, but the master key is stored on disk which means...'"
    )

SECTION_4_SYSTEM_PROMPT = """You are a senior engineer helping someone prepare to answer interview questions about their project's configuration and secrets management.

You will be provided with the project's source code, configuration files, and metadata.

# Instructions
1. Find ALL environment variables (os.environ, os.getenv, process.env, dotenv, etc.).
2. List configuration files and what they control.
3. Explain how secrets are stored, accessed, and managed.
4. Describe dev vs prod differences.
5. Write setup instructions like you're onboarding a new teammate.
6. Assess security honestly — what's good, what could improve.

# CRITICAL — Writing Style
- Write like you're answering interview questions out loud. NOT writing documentation.
- Use first person: "I store secrets encrypted in config.json using Fernet...", "To set this up, you'd first..."
- Be specific and honest. Say "the master key is stored on disk, which isn't ideal for production — you'd want a vault" NOT "security could be improved."
- Short, direct sentences. Sound like a real engineer, not a textbook.
- For setup_steps, write like you're telling a new teammate what to do, not writing an install guide.

# Rules
- NEVER include real API keys, tokens, or passwords. Use placeholders.
- Be thorough — check every file for env vars, config loading, and secrets.
- If encryption is used, explain the mechanism conversationally.
- If there are no env variables, say so and explain the alternative approach.
"""

# ===== Section 5: Core Functions & Classes =====

class CoreFunctionItem(BaseModel):
    name: str = Field(
        ...,
        description="The function or class name (e.g., 'ExtractionPipeline', 'generate_content', 'extract_python')."
    )
    kind: str = Field(
        ...,
        description="Whether this is a 'function', 'class', or 'method'. Be precise."
    )
    file_location: str = Field(
        ...,
        description="The file path where this function/class is defined (e.g., 'extraction/pipeline.py')."
    )
    line_range: str = Field(
        ...,
        description="Approximate line range (e.g., 'L19-L121'). Use the line numbers from the source code if available."
    )
    purpose: str = Field(
        ...,
        description="Explain like you're telling an interviewer: 'This is the main orchestrator — it takes a GitHub URL, fetches files, parses them, and stores everything in SQLite.' 2-3 sentences, conversational."
    )
    inputs: str = Field(
        ...,
        description="Describe the inputs/parameters naturally: 'It takes a repo URL, a GitHub token, and a base directory. The token is optional — if you don't pass one, it falls back to the saved PAT.'"
    )
    outputs: str = Field(
        ...,
        description="Describe what it returns: 'Returns a dict with success status, project name, files processed count, and any errors that happened during extraction.'"
    )
    why_important: str = Field(
        ...,
        description="Why this is a core piece — like: 'This is the backbone of the whole app. Every extraction goes through this pipeline. If this breaks, nothing works.'"
    )
    called_by: str = Field(
        ...,
        description="What calls this function/class: 'Called by the /api/extract endpoint in main.py when the user hits the Extract button.' If unknown, say 'Called internally' or 'Entry point'."
    )
    complexity_note: str = Field(
        default="",
        description="Optional: Any interesting complexity, edge cases, or design patterns used. Like: 'Uses a progress callback pattern so the frontend can show real-time extraction status.'"
    )

class Section5CoreFunctions(BaseModel):
    core_items: List[CoreFunctionItem] = Field(
        ...,
        description="A list of 5-15 core functions, classes, or methods that are the backbone of the project. Ordered by importance — the most critical first."
    )
    summary: str = Field(
        ...,
        description="A 2-3 sentence overview: 'The project revolves around a pipeline pattern where GitHub repos get fetched, parsed with Tree-sitter, and stored in SQLite. The LLM gateway then generates interview-prep documentation from the extracted code.' Conversational, first-person."
    )
    interaction_map: str = Field(
        ...,
        description="Describe how these core functions interact: 'So the flow is: ExtractionPipeline calls GitHubFetcher to get files, then extract_python/extract_javascript parse them, ProjectDB stores everything, and generate_content talks to the LLM.' 3-5 sentences."
    )

SECTION_5_SYSTEM_PROMPT = """You are a senior engineer helping someone prepare to explain the core functions and classes of their project in a technical interview.

You will be provided with the project's source code, file structure, and metadata.

# Instructions
1. Identify the 5-15 most important functions, classes, and methods in the codebase.
2. For each, document the file location, purpose, inputs, outputs, and why it matters.
3. Focus on the BACKBONE of the application — the pieces that make the system work.
4. Order by importance: the most critical functions first.
5. Include a summary and interaction map showing how they connect.

# What to Include
- Entry point functions (e.g., main(), app routes)
- Core business logic (pipelines, processors, handlers)
- Data layer (database classes, models)
- Integration points (API clients, LLM gateways, external services)
- Utility functions ONLY if they are architecturally significant

# What to SKIP
- Trivial getters/setters
- Standard boilerplate (import statements, __init__ with no logic)
- Test helpers
- Frontend rendering functions (unless they contain significant logic)

# CRITICAL — Writing Style
- Write like you're walking someone through the code in a pair programming session.
- Use first person: "So this is the main pipeline class — it takes a GitHub URL and does the whole extraction..."
- Be specific about WHAT things do, not just WHAT they are. Say "it fetches each file via the GitHub API, parses it with Tree-sitter, and stores the AST blocks in SQLite" NOT "it processes files."
- Short, punchy sentences. Sound like a real engineer, not documentation.
- For inputs/outputs, be practical: mention types, defaults, and edge cases.

# Rules
- Only document functions/classes that ACTUALLY EXIST in the codebase.
- Use exact file paths from the provided code.
- If line numbers are available from code blocks, use them.
- Scale the count based on project size: small projects (5-8 items), medium (8-12), large (12-15).
"""

# ===== Section 6: Technology Deep Dives =====

# Phase 0: Framework Discovery
class FrameworkInfo(BaseModel):
    name: str = Field(
        ...,
        description="The name of the framework or library (e.g., 'LangChain', 'FastAPI', 'TensorFlow')."
    )
    category: str = Field(
        ...,
        description="The domain category (e.g., 'AI/LLM Framework', 'Web Framework', 'Database ORM', 'ML Library')."
    )
    priority: int = Field(
        ...,
        description="Priority rank for the deep dive. 1 = most important to the project."
    )
    relevant_files: List[str] = Field(
        ...,
        description="File paths from the project that import or heavily use this framework."
    )

class FrameworkDiscovery(BaseModel):
    frameworks: List[FrameworkInfo] = Field(
        ...,
        description="An ordered list of frameworks and libraries that deserve a dedicated deep dive, sorted by priority."
    )

FRAMEWORK_DISCOVERY_PROMPT = """You are an expert software engineer analyzing a codebase to identify which frameworks and libraries deserve a dedicated technical deep dive for interview preparation.

You will be given the project's file structure, imports, and optionally an existing Tech Stack analysis.

# Instructions
1. Identify all MAJOR frameworks, libraries, and tools used in the project.
2. Only include technologies that are substantial enough to warrant a full deep dive (core frameworks, not utility packages like 'os' or 'json').
3. For each framework, list the files that import or use it.
4. Order them by priority — the most central framework to the project should be first.
5. Aim for 3-8 frameworks. Do not include more than 10.
6. Include both direct dependencies (e.g., FastAPI) and significant sub-dependencies that the developer should know (e.g., Pydantic if used with FastAPI).

# Rules
- Do NOT include standard library modules (os, sys, json, etc.) unless they are used in a remarkably advanced way.
- Do NOT include build tools, linters, or dev-only utilities.
- DO include ML/AI frameworks, web frameworks, database libraries, state management, API clients, etc.
"""

# Phase 1: Per-Framework Deep Dive
class Concept(BaseModel):
    title: str = Field(
        ...,
        description="The name of the concept or topic."
    )
    explanation: str = Field(
        ...,
        description="A thorough explanation written in natural spoken English. Cover WHAT it is, HOW it works under the hood, and WHY it's used this way. Should be comprehensive enough that after reading this, someone can confidently explain it in an interview. Use simple vocabulary but don't sacrifice depth — 4-8 sentences."
    )
    real_world_analogy: str = Field(
        default="",
        description="A simple real-world analogy that makes this concept click instantly. Example for middleware: 'Think of middleware like airport security checkpoints — every request passes through them in order before reaching your actual route handler, and each checkpoint can inspect, modify, or reject the request.' Empty string if no good analogy exists."
    )
    why_it_matters: str = Field(
        default="",
        description="A 1-2 sentence 'interview angle' — why an interviewer might ask about this, or how to frame your answer. Example: 'Interviewers love asking about this because it shows you understand async patterns, not just syntax.' Empty string if not applicable."
    )
    code_snippet: str = Field(
        default="",
        description="Relevant code snippet for revision. For directly-used concepts, this MUST be from the actual project code. For indirect concepts, provide a realistic example. Empty string only if no code is relevant."
    )

class FrameworkDeepDive(BaseModel):
    framework_name: str = Field(
        ...,
        description="The name of the framework or library being analyzed."
    )
    category: str = Field(
        ...,
        description="The domain category of this framework."
    )
    one_liner: str = Field(
        ...,
        description="A single sentence that explains what this framework is and why it exists. This is your elevator pitch — what you'd say if an interviewer asks 'What is X?' Example: 'Flask is a lightweight Python web framework — it gives you routing, request handling, and templating without the heavy opinions of Django.'"
    )
    how_it_works_internally: str = Field(
        ...,
        description="A 3-5 sentence explanation of how this framework works under the hood. Not surface-level — explain the core architecture, key abstractions, and execution model. Example for Flask: 'So Flask is built on top of Werkzeug for the WSGI layer and Jinja2 for templating. When a request comes in, Werkzeug parses it into a Request object, Flask matches it against your route decorators, calls your view function, and wraps the return value into a Response object. The app context and request context are pushed onto thread-local stacks, which is how you can access things like `request` and `g` as globals without passing them around.'"
    )
    basics: List[Concept] = Field(
        ...,
        description="5-7 foundational concepts that form the bedrock of this technology. These are the concepts you MUST know before anything else — the 'Chapter 1' stuff. Cover: what it is, core philosophy, key abstractions, lifecycle/execution model, ecosystem positioning, comparison with alternatives, and versioning/history if relevant."
    )
    directly_used_concepts: List[Concept] = Field(
        ...,
        description="EXHAUSTIVE list of EVERY concept, feature, API, pattern, or mechanism from this framework that is DIRECTLY USED in the project code. Do NOT skip anything — if the project imports it, configures it, calls it, or relies on it, it MUST be here. Each concept gets a thorough explanation with a code snippet from the actual project. This is the 'I actually used this' section — leave nothing out."
    )
    indirect_concepts: List[Concept] = Field(
        ...,
        description="A comprehensive list of the most important concepts from this framework that are NOT directly used in the project but are ESSENTIAL interview knowledge. Provide MANY topics — for major interview-heavy technologies (complex frameworks, AI/ML libraries, databases, cloud services), include a large number of concepts covering the full breadth of the technology. For simpler utility libraries, include fewer but still cover all the essentials. The goal is that the reader can handle ANY reasonable interview question about this framework. Each concept should be thorough enough for confident interview answers."
    )
    common_pitfalls: List[str] = Field(
        default_factory=list,
        description="5-8 common mistakes, gotchas, and 'I wish someone told me' moments that developers encounter with this framework. Include both beginner mistakes AND subtle production-level gotchas. Written conversationally: 'A classic Flask mistake is forgetting that the development server is single-threaded — if you make a blocking call to an LLM API, your whole server freezes until it responds.'"
    )
    interview_quickfire: List[str] = Field(
        default_factory=list,
        description="8-12 rapid-fire Q&A pairs formatted as 'Q: ... A: ...' that cover the most commonly asked interview questions about this framework. Mix basic, intermediate, and advanced questions. These should be snappy, confident answers — the kind that make an interviewer nod. Example: 'Q: What is Flask? A: Flask is a micro web framework for Python — micro means it doesn't force an ORM or form validation on you, it lets you pick your own tools.'"
    )
    vs_alternatives: str = Field(
        default="",
        description="A 3-5 sentence comparison of this framework against its main alternatives. What would you say if an interviewer asks 'Why X over Y?' Example for Flask: 'Flask vs Django — Django gives you everything out of the box: ORM, admin, auth, migrations. Flask gives you nothing — you pick your own tools. For this project Flask was the right call because I didn't need Django's ORM overhead, and I wanted full control over the request pipeline. If I was building a CRUD-heavy admin app, I'd go Django in a heartbeat.' Empty string if not applicable."
    )

FRAMEWORK_DEEP_DIVE_PROMPT = """You are a senior engineer helping someone prepare to CONFIDENTLY and THOROUGHLY discuss a specific framework in a technical interview.

You are analyzing how a framework is used in a real project. You have the actual source code. Your job is to produce content so comprehensive that after reading it, the person can honestly say "I know this technology well."

# Instructions

## Part 1: One-Liner & Internals
- Write a crisp one-liner that answers "What is [framework]?" — this is the first thing you'd say in an interview.
- Then explain how it works internally — not surface-level marketing speak, but actual architecture. What happens under the hood? What are the key abstractions? How does the execution model work?

## Part 2: Basics (3-5 concepts)
- Cover the foundational concepts that EVERY user of this framework must know.
- These are the "if you don't know these, you don't really know the framework" concepts.
- Examples: For Flask — WSGI, routing, request/response cycle, app context. For React — Virtual DOM, JSX, component lifecycle, hooks.
- Write thorough explanations — not just definitions, but HOW and WHY.

## Part 3: Directly Used Concepts (EXHAUSTIVE — every single one)
- Go through the provided source code and identify EVERY feature, API, pattern, class, decorator, configuration, or mechanism from this framework that the project uses.
- Do NOT skip anything. If the code imports something from this framework, it goes here.
- For EACH concept, explain:
  - What it is and how it works
  - How it's specifically used in THIS project
  - Why it matters (the interview angle)
- Include actual code snippets FROM the project for each concept.
- This section should be COMPLETE — a reviewer should not be able to find any framework usage in the code that isn't covered here.

## Part 4: Indirect Concepts (Important Interview Knowledge)
- Cover concepts from this framework that the project DOESN'T use, but that an interviewer will expect you to know.
- The NUMBER of indirect concepts should scale based on how important this technology is in interviews:
  - For major, interview-heavy technologies (complex frameworks, AI/ML libraries, cloud services, databases) — cover more concepts comprehensively. These are technologies where interviewers go deep.
  - For simpler, utility-style technologies (templating libraries, simple CLI tools, formatters) — cover fewer but still essential concepts.
- Use your judgment about what an interviewer would realistically ask about.
- For each concept, explain it thoroughly enough that the reader can answer follow-up questions, not just parrot a definition.
- Include example code snippets where they add clarity.

## Part 5: Common Pitfalls (3-5)
- List the most common mistakes, gotchas, and "I wish someone told me" moments for this framework.
- Frame them as real engineering experience: "A classic mistake with X is..."

## Part 6: Interview Quickfire (5-8 Q&A pairs)
- Write the most commonly asked interview questions about this framework and provide confident, concise answers.
- Format as "Q: [question] A: [answer]"
- These should be snappy — the kind of answers that make an interviewer nod and move on.

# CRITICAL — Writing Style
- Sound like a real person explaining things, NOT a documentation page.
- WRONG: "Flask is a framework for developing web applications in Python."
- RIGHT: "Flask is basically a lightweight web framework for Python — it gives you routing, request handling, and templating without forcing an ORM or admin panel on you like Django does."
- Use "basically", "so", "the idea is", "what this does is" — natural speech patterns.
- Be technically accurate but explain simply. Use correct terms but wrap them in plain English.
- Explanations should be THOROUGH — not walls of text, but comprehensive enough that the reader genuinely understands the concept.
- For the why_it_matters field, think like an interviewer: "They ask about this because it shows you understand X..."

# CRITICAL — Completeness Rules
- For directly_used_concepts: COMPLETENESS IS MANDATORY. Scan every line of the provided code. Every import, every method call, every configuration, every pattern from this framework MUST be covered. Missing a directly-used concept is a failure.
- For indirect_concepts: Use your professional judgment to determine the right scope based on the technology's interview significance. The goal is that the reader can handle ANY reasonable interview question about this framework after reading your output.

# Rules
- Do NOT hallucinate features not in the provided code for "Directly Used Concepts."
- Code snippets for directly_used_concepts MUST come from the actual project code.
- Code snippets for indirect_concepts should be realistic, correct, and self-contained examples.
- Every explanation should pass the "could I say this in an interview?" test.
"""

# ===== Section 7: Design Decisions =====

class DesignDecisionItem(BaseModel):
    title: str = Field(
        ...,
        description="A short title for the decision (e.g., 'Monolithic Flask over Microservices', 'SQLite over PostgreSQL', 'Tree-sitter for AST Parsing')."
    )
    context: str = Field(
        ...,
        description="Explain the situation: 'I needed a way to parse code from multiple languages reliably. Regex was too fragile, and building a custom parser for each language would take forever.' 2-3 sentences."
    )
    decision: str = Field(
        ...,
        description="What you chose and why: 'I went with Tree-sitter because it gives you a proper AST for like 40+ languages out of the box. It's fast, battle-tested, and used by GitHub itself.' 2-3 sentences."
    )
    alternatives_considered: List[str] = Field(
        ...,
        description="List of alternatives you considered (e.g., ['Regex-based parsing', 'Python ast module only', 'LibCST'])."
    )
    trade_offs: str = Field(
        ...,
        description="Be honest about trade-offs: 'The downside is Tree-sitter requires language-specific bindings — each language needs its own pip package. But the accuracy trade-off is worth it.' 2-3 sentences."
    )
    outcome: str = Field(
        ...,
        description="How did this decision play out: 'It worked really well — I can parse Python, JavaScript, Java, Go, Rust, and more. The AST extraction gives me clean class/function signatures for the LLM to analyze.' 1-2 sentences."
    )
    interview_angle: str = Field(
        ...,
        description="How to frame this in an interview: 'If an interviewer asks about this, I'd frame it as a build-vs-buy decision — I evaluated custom parsing, regex, and existing tools, and Tree-sitter was the best fit for multi-language support at this scale.' 1-2 sentences."
    )

class Section7DesignDecisions(BaseModel):
    decisions: List[DesignDecisionItem] = Field(
        ...,
        description="A list of 5-8 key engineering decisions. Include both architecture-level decisions (monolith vs microservices) and implementation-level decisions (which library to use)."
    )
    architectural_pattern: str = Field(
        ...,
        description="Describe the overall architectural pattern: 'The project follows a pipeline architecture — data flows through discrete stages (fetch → parse → store → generate). I kept it as a monolith because the scale doesn't justify microservices overhead.' 3-4 sentences."
    )
    design_principles: List[str] = Field(
        ...,
        description="3-5 design principles that guided the project. Explain naturally: 'Separation of concerns — I kept extraction, LLM interaction, and UI as separate modules so changes in one don't break others.'"
    )

SECTION_7_SYSTEM_PROMPT = """You are a senior engineer helping someone prepare to discuss the design decisions behind their project in a technical interview.

You will be provided with the project's source code, architecture, and metadata.

# Instructions
1. Identify 5-8 key engineering and design decisions visible in the codebase.
2. For each decision, explain the context, what was chosen, alternatives, trade-offs, and outcome.
3. Include both high-level architectural decisions AND implementation-level choices.
4. Describe the overall architectural pattern and guiding design principles.

# Types of Decisions to Look For
- Architecture pattern choices (monolith, microservices, pipeline, event-driven)
- Database/storage choices (SQL vs NoSQL, which specific database)
- Framework selections (why this web framework, why this ORM)
- API design choices (REST vs GraphQL, sync vs async)
- Security approaches (how secrets are managed, authentication strategy)
- Code organization (module structure, separation of concerns)
- Performance trade-offs (caching strategy, lazy loading, pagination)
- Error handling strategy (how errors propagate, retry mechanisms)

# CRITICAL — Improvisation Rule
If the codebase does not provide conclusive evidence for all 5-8 decisions, IMPROVISE. Look at the code patterns, infer the reasoning, and present 5-8 realistic, well-reasoned decisions that an engineer would ACTUALLY make when building this kind of project. Frame them as thoughtful engineering choices even if the code doesn't have explicit documentation about why things were done a certain way.

# CRITICAL — Writing Style
- Write like you're answering "Walk me through your key design decisions" in an interview.
- Use first person: "I chose SQLite because...", "The reason I went with a pipeline pattern is..."
- Be opinionated. Real engineers have opinions. Say "I picked Flask over Django because I didn't need the ORM overhead" NOT "Flask was selected for its lightweight nature."
- Mention real trade-offs. Every decision has downsides — acknowledge them.
- Short, punchy sentences. Sound confident and experienced.

# Rules
- Ground decisions in the actual codebase where possible.
- If inferring, make reasonable assumptions based on the code structure.
- Always include at least one security-related decision and one scalability-related decision.
"""

# ===== Section 8: Failure Log & Learnings =====

class FailureItem(BaseModel):
    title: str = Field(
        ...,
        description="A concise title for the failure/problem (e.g., 'SVG Diagrams Breaking in PDF Export', 'Token Limit Exceeded on Large Repos', 'Race Condition in Concurrent Extractions')."
    )
    what_happened: str = Field(
        ...,
        description="Describe the problem like you're telling a colleague: 'So I was generating PDF reports with Mermaid diagrams, and everything looked fine in the browser. But when WeasyPrint rendered them, all the text labels in the SVG disappeared because foreignObject isn't supported.' 3-4 sentences."
    )
    initial_approach: str = Field(
        ...,
        description="What you tried first: 'My first instinct was to try inline styles on the SVG text elements. I spent like 2 hours tweaking CSS, but the root issue was that WeasyPrint just doesn't handle foreignObject at all.' 2-3 sentences."
    )
    root_cause: str = Field(
        ...,
        description="The actual root cause: 'The issue was that Mermaid generates SVGs using foreignObject for text labels, which is a browser-specific feature. WeasyPrint's rendering engine can't handle it, so all text just vanished.' 2-3 sentences."
    )
    solution: str = Field(
        ...,
        description="How you fixed it: 'I switched to using mermaid.ink API to render diagrams as PNG images instead of inline SVGs. Now the diagrams are raster images that WeasyPrint handles perfectly.' 2-3 sentences."
    )
    lesson_learned: str = Field(
        ...,
        description="The takeaway: 'Always test the full output pipeline early. I assumed if it looked right in the browser, it would look right in the PDF. Now I always render a test PDF before calling a feature done.' 1-2 sentences."
    )
    category: str = Field(
        ...,
        description="Category of failure: 'integration', 'performance', 'security', 'architecture', 'debugging', 'deployment', 'data', or 'tooling'."
    )

class Section8FailureLog(BaseModel):
    failures: List[FailureItem] = Field(
        ...,
        description="A list of 5-8 failures, bugs, or problems encountered during development. Include both real issues visible in the code and realistic inferred challenges."
    )
    biggest_lesson: str = Field(
        ...,
        description="The single biggest takeaway from building this project: 'The biggest thing I learned is that LLM integrations are inherently unreliable — you need structured output parsing, retry logic, and graceful degradation at every layer. You can't just call an API and hope for the best.' 3-4 sentences."
    )
    what_id_do_differently: str = Field(
        ...,
        description="If you started over: 'If I built this again, I'd start with async everywhere — the GitHub API calls and LLM requests are all I/O bound, and right now they're blocking. I'd also add proper request queuing instead of fire-and-forget threads.' 3-5 sentences."
    )
    growth_areas: List[str] = Field(
        ...,
        description="3-5 specific skills or areas you grew in. Written naturally: 'Got way more comfortable with AST manipulation — before this project I'd never used Tree-sitter, now I can write custom extractors for any language.'"
    )

SECTION_8_SYSTEM_PROMPT = """You are a senior engineer helping someone prepare to answer "What problems did you run into?" and "What did you learn?" in a technical interview.

You will be provided with the project's source code, commit history, and metadata.

# Instructions
1. Identify 5-8 failures, bugs, challenges, or problems that likely occurred during development.
2. For each, describe what happened, what was tried, the root cause, the solution, and the lesson learned.
3. Include the biggest overall lesson, what you'd do differently, and growth areas.

# Where to Find Evidence of Failures
- Look at error handling code — extensive try/catch suggests past failures
- Check for workarounds, TODO comments, fallback logic
- Look at commit messages for "fix", "bug", "workaround", "revert"
- Notice defensive programming patterns (null checks, validation, retries)
- Check for configuration complexity that suggests past configuration issues
- Look for multiple approaches to the same problem (e.g., switching libraries)

# CRITICAL — Improvisation Rule
If the codebase does not have clear evidence of all 5-8 failures, IMPROVISE with realistic, common problems that engineers face when building this type of project. These should be:
- Technically plausible for this specific project type and tech stack
- Common enough that an interviewer would find them believable
- Specific enough to show real engineering experience (not generic "bugs happened")
- Include a mix of categories: at least one integration issue, one performance issue, one debugging challenge

Examples of realistic improvised failures:
- API rate limiting from GitHub when extracting large repos
- LLM returning malformed JSON that breaks structured output parsing
- Memory issues when parsing very large files with Tree-sitter
- CORS issues when the frontend and backend were on different ports during dev
- Database locking with SQLite when multiple extractions run concurrently

# CRITICAL — Writing Style
- Write like you're answering "Tell me about a tough bug you dealt with" in an interview.
- Use first person: "So what happened was...", "I spent like 3 hours on this before I realized..."
- Be vulnerable and honest. Interviewers LOVE hearing about real failures because it shows maturity.
- Show your debugging process — how you narrowed it down, what tools you used.
- The lesson_learned should feel like genuine wisdom, not textbook advice.
- Short, conversational sentences. Tell a story.

# Rules
- Mix real evidence-based failures with plausible inferred ones.
- Each failure should teach something different — don't repeat the same lesson.
- Categories should be diverse — don't make all failures about the same type of issue.
- Frame everything positively — failures are learning opportunities.
"""

# ===== Section 9: APIs & Interfaces =====

class APIEndpoint(BaseModel):
    method: str = Field(
        ...,
        description="HTTP method (GET, POST, PUT, DELETE, PATCH)."
    )
    path: str = Field(
        ...,
        description="The URL path (e.g., '/api/project/<project_name>/generate')."
    )
    purpose: str = Field(
        ...,
        description="Explain like: 'This is the main endpoint for generating documentation sections. The frontend calls this when you hit the Generate button.' 2-3 sentences."
    )
    request_body: str = Field(
        ...,
        description="Describe the request format: 'Takes a JSON body with section_id, provider, api_key, and strategy. The api_key can be a raw key or a saved_N reference.' If no body, say 'No request body.' 2-3 sentences."
    )
    response_format: str = Field(
        ...,
        description="Describe the response: 'Returns JSON with a message field and the generated content. On error, returns a JSON error message with a 500 status code.' 2-3 sentences."
    )
    auth_required: str = Field(
        ...,
        description="Authentication details: 'No auth — the API key is passed in the request body, not as a header. This is a local-only tool.' 1-2 sentences."
    )
    error_handling: str = Field(
        ...,
        description="How errors are handled: 'Catches exceptions and returns them as JSON with a 500 status code. The frontend shows these in the terminal logger.' 1-2 sentences."
    )

class APIDesignPattern(BaseModel):
    pattern: str = Field(
        ...,
        description="Name of the API design pattern (e.g., 'RESTful Resource Routing', 'RPC-style Endpoints', 'Request-Response with Background Jobs')."
    )
    description: str = Field(
        ...,
        description="Explain the pattern: 'The API follows a RESTful-ish pattern — GET for reads, POST for writes, DELETE for removals. But the generate endpoints are more RPC-style since they trigger actions rather than CRUD operations.' 2-4 sentences."
    )
    examples: List[str] = Field(
        ...,
        description="2-3 endpoint examples that demonstrate this pattern."
    )

class Section9APIs(BaseModel):
    api_overview: str = Field(
        ...,
        description="High-level overview: 'The app exposes a REST API with about 15 endpoints. Most are standard CRUD — list projects, get project details, delete sections. The interesting ones are the generation endpoints that orchestrate LLM calls.' 3-5 sentences."
    )
    endpoints: List[APIEndpoint] = Field(
        ...,
        description="List of ALL API endpoints in the application. Be comprehensive — include every route."
    )
    design_patterns: List[APIDesignPattern] = Field(
        ...,
        description="1-3 API design patterns used in the project."
    )
    error_strategy: str = Field(
        ...,
        description="Overall error handling strategy: 'Errors are caught at the route level and returned as JSON with appropriate HTTP status codes. I use try/finally to ensure database connections are always closed. The frontend parses error responses and shows them in the terminal.' 3-5 sentences."
    )
    rate_limiting: str = Field(
        ...,
        description="Rate limiting approach: 'There's no rate limiting currently since it's a local tool. For production, I'd add Flask-Limiter with per-endpoint limits — especially on the generate endpoints to prevent runaway LLM costs.' 2-4 sentences."
    )
    versioning: str = Field(
        ...,
        description="API versioning strategy: 'No versioning right now — all endpoints are under /api/. If I needed versioning, I'd prefix with /api/v1/ and use header-based versioning for breaking changes.' 2-3 sentences."
    )
    interview_tips: str = Field(
        ...,
        description="Tips for discussing this API in interviews: 'Key talking points: mention RESTful design, JSON request/response, error handling patterns, and what you'd add for production (rate limiting, auth, versioning).' 2-4 sentences."
    )

SECTION_9_SYSTEM_PROMPT = """You are a senior API engineer helping someone prepare to discuss their project's APIs and interfaces in a technical interview.

You will be provided with the project's source code, route definitions, and metadata.

# Instructions
1. Identify ALL API endpoints/routes in the application.
2. For each endpoint, document the HTTP method, path, purpose, request/response format, and error handling.
3. Identify API design patterns used.
4. Describe the overall error handling strategy.
5. Cover rate limiting, versioning, and authentication approaches (or what you'd add).

# CRITICAL — Writing Style
- Write like you're answering "Walk me through your API design" in an interview.
- Use first person: "I designed the API around RESTful principles...", "The generate endpoint takes a JSON body with..."
- Be specific: mention actual endpoints, status codes, and payload structures from the code.
- Short, confident sentences. Sound like a real backend engineer.

# CRITICAL — Improvisation Rule
If some aspects are missing (rate limiting, versioning, auth), describe what EXISTS and then what you'd ADD for production. Frame it as: "Currently there's no rate limiting since it's local-only, but for production I'd..."

# Rules
- Document EVERY route/endpoint visible in the codebase.
- Be accurate about HTTP methods, paths, and payloads.
- Don't hallucinate endpoints that don't exist.
- Include both current state and production recommendations.
"""

# ===== Section 10: Data Models & Storage =====

class DataModel(BaseModel):
    name: str = Field(
        ...,
        description="Name of the data model/table/collection (e.g., 'files', 'code_blocks', 'generated_sections', 'repo_info')."
    )
    storage_type: str = Field(
        ...,
        description="Where it's stored (e.g., 'SQLite table', 'JSON file', 'In-memory dict', 'File system')."
    )
    purpose: str = Field(
        ...,
        description="Explain like: 'This table stores every file extracted from the GitHub repo — path, language, size, and parsed metadata like imports and class names.' 2-3 sentences."
    )
    fields: List[str] = Field(
        ...,
        description="Key fields/columns with brief descriptions (e.g., 'id (INTEGER PRIMARY KEY)', 'path (TEXT) — the file path relative to repo root', 'language (TEXT) — detected programming language')."
    )
    relationships: str = Field(
        ...,
        description="How this model relates to others: 'Each file has many code_blocks — that's a one-to-many relationship keyed on file_id.' 1-3 sentences. If standalone, say 'Standalone — no foreign key relationships.'"
    )
    access_patterns: str = Field(
        ...,
        description="How the data is typically accessed: 'Most queries are by file_id to get blocks for a specific file. The generated_sections table is queried by section_id when rendering the output viewer.' 2-3 sentences."
    )

class StorageDecision(BaseModel):
    decision: str = Field(
        ...,
        description="The storage choice made (e.g., 'SQLite for project data', 'JSON for configuration', 'File system for PDFs')."
    )
    reasoning: str = Field(
        ...,
        description="Why this choice: 'I went with SQLite because each project is self-contained — one .db file per project. Easy to back up, easy to delete, no server to manage. For a single-user local tool, it's perfect.' 3-4 sentences."
    )
    trade_offs: str = Field(
        ...,
        description="Honest trade-offs: 'The downside is SQLite doesn't handle concurrent writes well. If I ever make this multi-user, I'd need to switch to PostgreSQL. But for now, the simplicity is worth it.' 2-3 sentences."
    )
    production_alternative: str = Field(
        ...,
        description="What you'd use in production: 'For a multi-user SaaS version, I'd use PostgreSQL with connection pooling via pgbouncer, and store generated PDFs in S3 instead of the local filesystem.' 2-3 sentences."
    )

class Section10DataModels(BaseModel):
    data_overview: str = Field(
        ...,
        description="High-level overview: 'The app uses a per-project SQLite database to store everything — repo metadata, extracted files, parsed code blocks, and generated documentation sections. Config is stored in a JSON file. It's a simple but effective schema.' 3-5 sentences."
    )
    models: List[DataModel] = Field(
        ...,
        description="List of ALL data models/tables in the application. Be comprehensive."
    )
    storage_decisions: List[StorageDecision] = Field(
        ...,
        description="2-4 key storage decisions with reasoning and trade-offs."
    )
    schema_diagram: str = Field(
        ...,
        description="""A Mermaid erDiagram showing the data model relationships. Use proper ER diagram syntax.

Example:
erDiagram
    FILES ||--o{ CODE_BLOCKS : contains
    FILES {
        int id PK
        text path
        text language
    }
    CODE_BLOCKS {
        int id PK
        int file_id FK
        text block_type
        text content
    }

Keep it clean with the main tables only. Use proper cardinality notation."""
    )
    indexing_strategy: str = Field(
        ...,
        description="Indexing approach: 'SQLite auto-indexes primary keys. I don't have explicit secondary indexes, which is fine for the data volumes I'm dealing with. If queries got slow, I'd add indexes on file_id in code_blocks and section_id in generated_sections.' 2-4 sentences."
    )
    data_lifecycle: str = Field(
        ...,
        description="How data flows through the system: 'Data enters when a repo is extracted — files and blocks get written. Then during generation, the LLM output gets saved as generated sections. The user can delete individual sections or nuke the whole project.' 3-5 sentences."
    )
    migration_strategy: str = Field(
        ...,
        description="Database migration approach: 'Currently no migration system — the schema is created fresh when a new project is extracted. If I needed to evolve the schema, I'd add Alembic for SQLite migrations or just version the schema in the database module.' 2-3 sentences."
    )

SECTION_10_SYSTEM_PROMPT = """You are a senior database engineer helping someone prepare to discuss their project's data models and storage in a technical interview.

You will be provided with the project's source code, database modules, and metadata.

# Instructions
1. Identify ALL data models/tables/storage mechanisms in the application.
2. For each model, document the fields, relationships, and access patterns.
3. Create a Mermaid ER diagram showing relationships.
4. Describe storage decisions with reasoning and trade-offs.
5. Cover indexing, data lifecycle, and migration strategies.

# Mermaid ER Diagram Rules
- Use valid Mermaid `erDiagram` syntax.
- Show proper cardinality: ||--o{ (one-to-many), ||--|| (one-to-one), }o--o{ (many-to-many).
- Include key fields (PK, FK) inside entity blocks.
- Keep it to the main tables — don't include every field.
- Do NOT wrap in markdown code fences — just raw Mermaid starting with `erDiagram`.

# CRITICAL — Writing Style
- Write like you're answering "Tell me about your data model" in an interview.
- Use first person: "I store each project in its own SQLite database...", "The schema is pretty straightforward..."
- Be specific about actual table names, column types, and query patterns from the code.
- Short, confident sentences.

# CRITICAL — Improvisation Rule
If the codebase doesn't have explicit schema documentation, analyze the database module code to infer the schema. Look at CREATE TABLE statements, INSERT queries, and SELECT queries to understand the models.

# Rules
- Document EVERY storage mechanism (databases, files, in-memory stores).
- Be accurate about column names and types.
- Include both current state and production recommendations.
- Don't hallucinate tables or columns that don't exist.
"""

# ===== Section 11: Testing Strategy =====

class TestCase(BaseModel):
    name: str = Field(
        ...,
        description="Name of the test or test category (e.g., 'ExtractionPipeline Integration Test', 'LLM Gateway Unit Test', 'API Endpoint Tests')."
    )
    test_type: str = Field(
        ...,
        description="Type: 'unit', 'integration', 'e2e', 'performance', or 'security'."
    )
    what_it_tests: str = Field(
        ...,
        description="What this test covers: 'Tests that the extraction pipeline correctly fetches files from GitHub, parses them with Tree-sitter, and stores the results in SQLite.' 2-3 sentences."
    )
    how_to_implement: str = Field(
        ...,
        description="How you'd implement it: 'I'd mock the GitHub API responses using responses library, run the pipeline against the mock data, then assert the database contains the expected files and code blocks.' 2-4 sentences."
    )
    priority: str = Field(
        ...,
        description="Priority level: 'High', 'Medium', or 'Low'."
    )

class TestFrameworkChoice(BaseModel):
    framework: str = Field(
        ...,
        description="Testing framework name (e.g., 'pytest', 'unittest', 'Jest', 'Cypress')."
    )
    why_chosen: str = Field(
        ...,
        description="Why this framework: 'I'd use pytest because it's the standard for Python projects — clean syntax, great fixture system, and excellent plugin ecosystem. parametrize is amazing for testing multiple inputs.' 2-3 sentences."
    )
    key_features_used: List[str] = Field(
        ...,
        description="Key features you'd leverage (e.g., 'Fixtures for database setup/teardown', 'parametrize for testing multiple file types', 'conftest.py for shared test config')."
    )

class Section11Testing(BaseModel):
    testing_overview: str = Field(
        ...,
        description="Current state of testing: 'Honestly, the test coverage is minimal right now — this was built as a portfolio project and I prioritized features over tests. But here's my testing strategy and what I'd implement.' Be honest. 3-5 sentences."
    )
    current_tests: List[str] = Field(
        ...,
        description="List of any existing tests, or be honest: 'No formal test suite exists yet. Testing has been manual through the UI.' Include any test files found in the codebase."
    )
    proposed_test_plan: List[TestCase] = Field(
        ...,
        description="8-12 test cases you would implement, ordered by priority. Cover unit tests, integration tests, and E2E tests."
    )
    framework_choices: List[TestFrameworkChoice] = Field(
        ...,
        description="1-3 testing frameworks you'd use with reasoning."
    )
    mocking_strategy: str = Field(
        ...,
        description="How you'd handle mocking: 'The two big things to mock are the GitHub API and the LLM providers. For GitHub, I'd use the responses library to mock HTTP calls. For LLMs, I'd create a mock provider that returns predefined Pydantic objects so I can test the pipeline without burning API credits.' 3-5 sentences."
    )
    ci_integration: str = Field(
        ...,
        description="How tests would fit into CI: 'I'd set up GitHub Actions to run pytest on every push. Unit tests would run on every PR, integration tests nightly. I'd add a coverage badge to the README — aiming for 80% on core modules.' 2-4 sentences."
    )
    testing_philosophy: str = Field(
        ...,
        description="Your testing philosophy for interviews: 'I believe in testing the critical path first — the extraction pipeline and LLM gateway are the backbone, so they get tests first. I'd rather have 20 meaningful integration tests than 200 trivial unit tests.' 3-5 sentences."
    )
    coverage_gaps: List[str] = Field(
        ...,
        description="3-5 honest coverage gaps: 'No tests for the PDF generation pipeline', 'LLM response parsing is untested — if Groq changes their response format, we'd find out in production', 'No load testing for concurrent extractions'."
    )

SECTION_11_SYSTEM_PROMPT = """You are a senior QA engineer and testing advocate helping someone prepare to discuss their testing strategy in a technical interview.

You will be provided with the project's source code, any test files, and metadata.

# Instructions
1. Honestly assess the current state of testing in the project.
2. Design a comprehensive test plan with 8-12 specific test cases.
3. Recommend testing frameworks with reasoning.
4. Describe mocking strategies for external dependencies.
5. Cover CI integration, testing philosophy, and coverage gaps.

# CRITICAL — Honesty First
Most portfolio projects have minimal testing. That's FINE. The interview strategy is:
1. Be honest: "Test coverage is low — I focused on shipping features first."
2. Show you KNOW what to test: "Here's my testing plan and priority order."
3. Demonstrate testing knowledge: "I'd use pytest with fixtures, mock the GitHub API with responses..."
4. Frame it positively: "If I had another sprint, the extraction pipeline would get integration tests first."

# CRITICAL — Writing Style
- Write like you're answering "What's your testing strategy?" in an interview.
- Use first person: "I'd start by testing the extraction pipeline because...", "My approach to mocking would be..."
- Be honest about gaps but show you know how to fill them.
- Sound like an engineer who values testing but is pragmatic about priorities.
- Short, direct sentences.

# Test Categories to Cover
1. **Unit Tests**: Individual functions/methods in isolation.
2. **Integration Tests**: Multiple components working together (e.g., pipeline → database).
3. **API/E2E Tests**: Full request/response cycles through the Flask API.
4. **Edge Cases**: Large files, malformed input, missing API keys, network failures.
5. **Performance Tests**: Large repos, concurrent extractions.

# Rules
- Check for actual test files in the codebase — document what exists.
- Proposed tests should be specific to THIS project, not generic.
- Include actual test function names and assertions you'd write.
- Be realistic about what you'd test first (critical path) vs. later (nice-to-have).
"""

# ===== Section 12: Scalability & Production =====

class Bottleneck(BaseModel):
    area: str = Field(
        ...,
        description="Where the bottleneck is (e.g., 'GitHub API Rate Limiting', 'Synchronous LLM Calls', 'SQLite Write Locking', 'Single-threaded Flask')."
    )
    description: str = Field(
        ...,
        description="Explain the bottleneck: 'Right now, LLM calls are synchronous and blocking. When you generate a section, the Flask worker is locked up waiting for the LLM to respond — which can take 30-60 seconds. During that time, no other requests can be served on that worker.' 3-4 sentences."
    )
    impact: str = Field(
        ...,
        description="Impact level and explanation: 'High impact for multi-user — a single generation request blocks the entire server. For single-user, it's acceptable since you're only doing one thing at a time.' 2-3 sentences."
    )
    solution: str = Field(
        ...,
        description="How to fix it: 'Move LLM calls to a background task queue like Celery with Redis as the broker. The API would return a job ID immediately, and the frontend would poll for completion. This decouples request handling from LLM processing.' 3-4 sentences."
    )

class CodeSmell(BaseModel):
    smell: str = Field(
        ...,
        description="Name of the code smell (e.g., 'God Object in main.py', 'No Input Validation', 'Hardcoded Configuration')."
    )
    location: str = Field(
        ...,
        description="Where it occurs — use module/component names, not file paths: 'The main application module — it has all routes, business logic, and PDF generation in one place.' 1-2 sentences."
    )
    severity: str = Field(
        ...,
        description="Severity: 'Low', 'Medium', or 'High'."
    )
    fix: str = Field(
        ...,
        description="How to fix it: 'Break the monolithic route file into a Flask Blueprint per feature — one for project CRUD, one for generation, one for PDF export, one for config management.' 2-3 sentences."
    )

class SecurityItem(BaseModel):
    area: str = Field(
        ...,
        description="Security area (e.g., 'Input Validation', 'Secret Storage', 'CORS Configuration', 'SQL Injection')."
    )
    current_state: str = Field(
        ...,
        description="Current state: 'CORS is wide open — I'm using flask-cors with default settings, which allows any origin. Fine for local dev, dangerous for production.' 2-3 sentences."
    )
    recommendation: str = Field(
        ...,
        description="What to improve: 'Lock down CORS to specific origins. Add request validation with something like marshmallow or Pydantic. Implement rate limiting on generation endpoints to prevent API key abuse.' 2-3 sentences."
    )

class Section12Scalability(BaseModel):
    scalability_overview: str = Field(
        ...,
        description="High-level assessment: 'The app is built for single-user local use, so scalability wasn't a primary concern. But if I were to scale this, the main bottlenecks would be synchronous LLM calls, SQLite limitations, and the single-process Flask server.' 3-5 sentences."
    )
    bottlenecks: List[Bottleneck] = Field(
        ...,
        description="4-6 bottlenecks identified in the system, ordered by severity."
    )
    code_smells: List[CodeSmell] = Field(
        ...,
        description="3-5 code smells or technical debt items."
    )
    security_audit: List[SecurityItem] = Field(
        ...,
        description="3-5 security considerations with current state and recommendations."
    )
    scaling_strategy: str = Field(
        ...,
        description="Overall scaling plan: 'To handle 100 concurrent users, I'd need: (1) async LLM calls with Celery, (2) PostgreSQL instead of SQLite, (3) Gunicorn with multiple workers behind Nginx, (4) Redis for caching generated sections, (5) S3 for PDF storage.' 4-6 sentences."
    )
    monitoring_gaps: List[str] = Field(
        ...,
        description="3-5 monitoring gaps: 'No request logging beyond Flask's default', 'No metrics on LLM call latency or success rate', 'No alerting for failed extractions', 'No health check endpoint'."
    )
    performance_optimizations: List[str] = Field(
        ...,
        description="3-5 performance optimizations possible: 'Cache generated sections to avoid redundant LLM calls', 'Use streaming responses for LLM output', 'Implement lazy loading for large project file lists', 'Add database connection pooling'."
    )
    production_architecture: str = Field(
        ...,
        description="""Describe the ideal production architecture: 'For production, I'd go with: Nginx as reverse proxy → Gunicorn with 4+ workers → Flask app → Celery workers for async LLM calls → PostgreSQL for data → Redis for caching and task queue → S3 for PDF storage. I'd deploy the whole thing on AWS ECS or Railway with auto-scaling based on CPU utilization.' 4-6 sentences."""
    )

SECTION_12_SYSTEM_PROMPT = """You are a senior SRE and performance engineer helping someone prepare to discuss scalability and production readiness in a technical interview.

You will be provided with the project's source code, architecture, and metadata.

# Instructions
1. Identify 4-6 performance bottlenecks with concrete solutions.
2. Find 3-5 code smells or technical debt items.
3. Perform a security audit with 3-5 findings.
4. Design a scaling strategy for production.
5. Identify monitoring gaps and performance optimization opportunities.
6. Describe the ideal production architecture.

# CRITICAL — Writing Style
- Write like you're answering "How would you scale this?" in an interview.
- Use first person: "The biggest bottleneck is the synchronous LLM calls...", "If I needed to handle 100 users, I'd..."
- Be honest about current limitations but show you know how to fix them.
- Sound like an engineer who's actually thought about production systems.
- Short, direct sentences. Be specific about technologies and numbers.

# CRITICAL — No File Paths
- Do NOT mention file paths in descriptions. Use component/module names instead.
- WRONG: "main.py is a God Object with 1200 lines"
- RIGHT: "The main application module is a God Object — all routes, business logic, and PDF generation live in one place."

# CRITICAL — Improvisation Rule
For portfolio projects, the honest answer is "it's not production-ready." That's fine. The interview strategy is:
1. Acknowledge current limitations honestly.
2. Show you understand what WOULD need to change.
3. Demonstrate knowledge of production best practices.
4. Give specific, actionable improvements — not vague "make it better" suggestions.

# Rules
- Ground analysis in the actual codebase.
- Be specific about bottleneck causes and solutions.
- Include concrete numbers (e.g., "SQLite handles ~500 writes/sec", "Gunicorn with 4 workers").
- Security findings should be realistic and actionable.
- Don't over-engineer — propose infrastructure appropriate for realistic scale.
"""

# ===== Section 13: Deployment & Infra =====

class DeploymentEnvironment(BaseModel):
    name: str = Field(
        ...,
        description="Environment name (e.g., 'Local Development', 'Staging', 'Production')."
    )
    description: str = Field(
        ...,
        description="Explain like: 'Local dev is just Flask running on localhost:5000 with debug mode on. No containerization, no reverse proxy — just raw Flask.' 2-3 sentences."
    )
    how_to_run: str = Field(
        ...,
        description="Step-by-step commands or instructions: 'Clone the repo, create a venv, pip install requirements, then python main.py. That's it.' 2-3 sentences."
    )
    differences: str = Field(
        ...,
        description="What's different about this environment: 'In dev, debug=True so you get auto-reload and the debugger PIN. In prod, you'd want Gunicorn with multiple workers and debug off.' 2-3 sentences."
    )

class CICDStep(BaseModel):
    name: str = Field(
        ...,
        description="Name of the CI/CD step or pipeline stage (e.g., 'Lint & Format', 'Unit Tests', 'Build Docker Image', 'Deploy to Render')."
    )
    description: str = Field(
        ...,
        description="Explain like: 'This step runs flake8 and black to check code style. If anything fails, the pipeline stops and you get a notification.' 2-3 sentences."
    )
    tools_used: List[str] = Field(
        ...,
        description="Tools or services involved (e.g., ['GitHub Actions', 'pytest', 'Docker', 'Render'])."
    )

class InfraComponent(BaseModel):
    component: str = Field(
        ...,
        description="Name of the infrastructure component (e.g., 'Web Server', 'Database', 'Reverse Proxy', 'Container Runtime')."
    )
    technology: str = Field(
        ...,
        description="Specific technology used (e.g., 'Gunicorn', 'SQLite', 'Nginx', 'Docker')."
    )
    purpose: str = Field(
        ...,
        description="Explain like an interviewer asked 'Why do you need this?': 'Gunicorn gives me multiple worker processes so the app can handle concurrent requests. Flask's built-in server is single-threaded and would choke under load.' 2-3 sentences."
    )
    configuration_notes: str = Field(
        default="",
        description="Any important configuration details: 'I'd run Gunicorn with 4 workers and a 120-second timeout because LLM calls can take a while.' 1-2 sentences."
    )

class Section13Deployment(BaseModel):
    deployment_overview: str = Field(
        ...,
        description="High-level overview answering 'How is this deployed?': 'Right now it's a local-only Flask app — you clone it, install deps, and run main.py. For production, I'd containerize it with Docker and deploy to Render or Railway.' 3-5 sentences."
    )
    environments: List[DeploymentEnvironment] = Field(
        ...,
        description="List of deployment environments (dev, staging, prod). Include at least dev and a proposed production setup even if the project is local-only."
    )
    infra_components: List[InfraComponent] = Field(
        ...,
        description="Infrastructure components needed to run the application. Include both current (e.g., SQLite) and recommended production components (e.g., PostgreSQL)."
    )
    cicd_pipeline: List[CICDStep] = Field(
        ...,
        description="CI/CD pipeline steps. If no pipeline exists, describe what an ideal pipeline would look like for this project."
    )
    containerization: str = Field(
        ...,
        description="Explain the containerization strategy: 'I'd use a multi-stage Docker build — first stage installs deps and compiles Tree-sitter bindings, second stage copies the built app for a slim runtime image. The Dockerfile would expose port 5000 and run Gunicorn.' 3-5 sentences. If Docker isn't used, describe what a Dockerfile would look like."
    )
    monitoring_and_logging: str = Field(
        ...,
        description="Describe the monitoring/logging approach: 'Right now logging is basic — Flask logs to stdout. In production, I'd add structured logging with Python's logging module, ship logs to something like Datadog or CloudWatch, and set up health check endpoints.' 3-5 sentences."
    )
    disaster_recovery: str = Field(
        ...,
        description="Explain backup/recovery: 'Since the data is in SQLite files per project, backup is just copying the .db files. In production with PostgreSQL, I'd set up automated daily backups and point-in-time recovery.' 2-4 sentences."
    )
    cost_analysis: str = Field(
        ...,
        description="Rough cost estimate: 'On Render's free tier, this would run fine for personal use. For a team, a $7/month starter instance would handle it. The main cost driver is LLM API calls — Groq is free tier, Gemini has a generous free quota.' 2-4 sentences."
    )
    production_readiness_checklist: List[str] = Field(
        ...,
        description="A checklist of what's needed for production: 'Add HTTPS termination', 'Switch from SQLite to PostgreSQL', 'Add rate limiting on API endpoints', 'Set up health check endpoint at /health'. 5-10 items."
    )
    interview_talking_points: str = Field(
        ...,
        description="Key points to mention in an interview about deployment: 'If asked about deployment, I'd walk them through the local setup first, then explain how I'd productionize it — Docker, Gunicorn, PostgreSQL, CI/CD with GitHub Actions. I'd mention I chose SQLite for dev simplicity but know the trade-offs for production.' 3-5 sentences."
    )

SECTION_13_SYSTEM_PROMPT = """You are a senior DevOps engineer and SRE helping someone prepare to discuss their project's deployment and infrastructure in a technical interview.

You will be provided with the project's source code, configuration files, and metadata.

# Instructions
1. Analyze the deployment setup — how the app is currently run, configured, and would be deployed.
2. Describe deployment environments (dev, staging, prod) — even if only dev exists, describe what prod SHOULD look like.
3. List infrastructure components both current and recommended.
4. Design a CI/CD pipeline appropriate for this project.
5. Cover containerization strategy, monitoring, disaster recovery, and cost.
6. Provide a production readiness checklist.

# CRITICAL — Improvisation Rule
Most personal/portfolio projects don't have full deployment pipelines. That's fine. Your job is to:
- Accurately describe the CURRENT setup (usually local dev)
- Then propose a REALISTIC production deployment that the developer could actually implement
- Make the proposals specific to THIS project's tech stack and requirements
- Include enough detail that the developer could answer "How would you deploy this?" confidently

# CRITICAL — Writing Style
- Write like you're answering "Walk me through your deployment setup" in an interview.
- Use first person: "I run it locally with Flask's dev server, but for production I'd...", "The way I'd set up CI/CD is..."
- Be specific: mention actual services (Render, Railway, AWS ECS), actual tools (Gunicorn, Nginx, GitHub Actions), actual configs.
- Short, confident sentences. Sound like someone who's actually deployed things.
- If the project is local-only, own it: "Right now it's local-only, but here's how I'd productionize it..."

# Rules
- Ground everything in the actual codebase.
- Don't over-engineer: propose infrastructure appropriate for the project's scale.
- Include both current state and recommended improvements.
- Be honest about what exists vs. what's proposed.
"""

# ===== Section 14: Interview Question Bank =====

class FollowUpItem(BaseModel):
    question: str = Field(
        ...,
        description="A follow-up question an interviewer might ask after hearing the main answer (e.g., 'What would you do differently at 10x scale?')."
    )
    talking_points: str = Field(
        ...,
        description="1-2 sentence talking points — quick hints on how to answer this follow-up. Like: 'Mention switching to PostgreSQL for concurrent writes, adding Redis for caching, and using Celery for background LLM calls.' Keep it as bullet-style hints, not a full answer."
    )

class InterviewQuestion(BaseModel):
    question: str = Field(
        ...,
        description="A specific, technical interview question about this project. Should sound like something a real interviewer would ask (e.g., 'Why did you choose SQLite over PostgreSQL?', 'How does your extraction pipeline handle large repos?', 'Walk me through how a request flows from the UI to the LLM and back.')."
    )
    difficulty: str = Field(
        ...,
        description="One of: 'Basic', 'Intermediate', 'Advanced'."
    )
    category: str = Field(
        ...,
        description="Category of the question: 'architecture', 'design_decisions', 'tech_stack', 'performance', 'security', 'testing', 'deployment', 'debugging', 'system_design', 'behavioral', or 'deep_dive'."
    )
    model_answer: str = Field(
        ...,
        description="A comprehensive model answer written in first person, as if the developer is answering in an interview. Should be conversational, specific, and technically accurate. Do NOT mention file paths or file names in the answer — speak about components, modules, and concepts naturally without referencing exact paths. 4-8 sentences for Basic, 6-12 sentences for Intermediate, 8-15 sentences for Advanced."
    )
    follow_ups: List[FollowUpItem] = Field(
        ...,
        description="2-3 likely follow-up questions an interviewer might ask after hearing the answer, each with 1-2 sentence talking points for quick preparation."
    )
    key_terms: List[str] = Field(
        ...,
        description="3-5 technical terms or concepts to naturally mention in the answer (e.g., ['AST', 'Tree-sitter', 'structured output', 'pipeline pattern'])."
    )

class QuestionCategory(BaseModel):
    category_name: str = Field(
        ...,
        description="Human-readable category name (e.g., 'Architecture & Design', 'Performance & Scalability', 'Security & Best Practices')."
    )
    questions: List[InterviewQuestion] = Field(
        ...,
        description="6-8 questions in this category. Lean heavily towards Intermediate and Advanced difficulty — at most 1-2 Basic questions. Focus on questions the developer would NOT naturally think to prepare for but that a sharp interviewer would definitely ask. Order from easier to harder."
    )

class Section14InterviewBank(BaseModel):
    question_categories: List[QuestionCategory] = Field(
        ...,
        description="6-8 categories of interview questions, each with 6-8 questions (minimum 6). Categories should cover: architecture, tech choices, performance, security, debugging experiences, system design extensions, edge cases, and trade-offs. Lean towards moderate-to-difficult questions that test real understanding, not just surface knowledge."
    )
    curveball_questions: List[InterviewQuestion] = Field(
        ...,
        description="5-8 unexpected, thought-provoking 'curveball' questions that test deep thinking and adaptability. These should make the developer pause and think — not trivia, but genuine problem-solving questions: 'If you had to rebuild this in Rust, what would change?', 'How would you add real-time collaboration?', 'What if your LLM provider goes down mid-generation?', 'How would you make this work offline?', 'What's the hardest bug you'd expect in production that you haven't seen in dev?'"
    )
    red_flags_to_avoid: List[str] = Field(
        ...,
        description="5-8 things to NOT say in an interview about this project. Written as coaching advice: 'Don't say you just followed a tutorial — emphasize the design decisions YOU made.', 'Don't downplay the project — even if it's a portfolio project, frame it as solving a real problem.'"
    )
    confidence_builders: List[str] = Field(
        ...,
        description="5-8 genuinely impressive aspects of this project that the developer should confidently highlight. Written as coaching: 'You're using Tree-sitter for AST parsing — that's the same tool GitHub uses. Mention that.', 'The 2-pass retrieval strategy shows you think about token optimization — interviewers love that.'"
    )
    weak_spots_and_deflections: List[str] = Field(
        ...,
        description="3-5 potential weak spots in the project and how to gracefully address them. Written as coaching: 'If they ask about testing — be honest that coverage is low, but pivot to explaining what you WOULD test and how: unit tests for extractors, integration tests for the pipeline, E2E tests for the API.'"
    )

SECTION_14_SYSTEM_PROMPT = """You are a senior technical interviewer and career coach helping someone prepare for interviews about their project.

You will be provided with the project's source code, architecture, and metadata. Your goal is to generate a comprehensive question bank that covers every angle an interviewer might take.

# Instructions
1. Generate 6-8 categories of interview questions, each with AT LEAST 6 questions (aim for 6-8). Each category must have minimum 6 questions — this is non-negotiable.
2. Difficulty distribution per category: at most 1-2 Basic, the rest should be Intermediate and Advanced. Focus on questions the developer would NOT naturally prepare for.
3. Include model answers that sound like a confident, experienced engineer responding.
4. For each follow-up question, provide 1-2 sentence talking points — quick hints for how to respond.
5. Add 5-8 curveball questions that test deeper understanding and creative problem-solving.
6. Coach on red flags to avoid and confidence builders to lean into.
7. Identify weak spots and provide graceful deflection strategies.

# CRITICAL — Question Depth
- Do NOT generate obvious questions like "What does this project do?" or "What's your tech stack?" — those are warm-ups that don't need preparation.
- Focus on questions that would make the developer pause and think: edge cases, failure scenarios, scaling challenges, alternative approaches, internal mechanics.
- For System Design Extensions: ask about adding features that stress-test the architecture (caching, rate limiting, multi-tenancy, real-time features, offline support).
- For each category, at least 2-3 questions should be ones the developer would NOT naturally think of on their own.

# Question Difficulty Guidelines
- **Basic**: "What does this project do?", "What's your tech stack?" — Warm-up questions.
- **Intermediate**: "Why did you choose X over Y?", "How does data flow through the system?" — Shows understanding.
- **Advanced**: "How would you scale this to 1000 concurrent users?", "What's the time complexity of your extraction pipeline?" — Tests deep knowledge.

# Categories to Cover
1. **Architecture & Design**: Overall structure, patterns, module organization.
2. **Technology Choices**: Why specific tools/libraries were picked, trade-offs.
3. **Performance & Scalability**: Bottlenecks, optimization opportunities, scaling strategies.
4. **Security & Best Practices**: How secrets are managed, input validation, OWASP concerns.
5. **Debugging & Problem Solving**: Past challenges, how they were resolved.
6. **System Design Extensions**: "How would you add feature X?", "What if requirement Y changed?"
7. **Code Quality & Testing**: Testing strategy, code organization, maintainability.
8. **DevOps & Deployment**: CI/CD, containerization, monitoring.

# CRITICAL — NO FILE PATHS IN MODEL ANSWERS
- NEVER mention file paths, file names, or directory paths inside model answers (e.g., do NOT say "in core/rag_pipeline.py" or "the classifier in core/classifier.py").
- Instead, refer to components by their logical name: "the RAG pipeline", "the urgency classifier", "the caching layer", "the extraction module".
- The answer should sound like natural speech in an interview — nobody says "in slash core slash rag underscore pipeline dot py" out loud.
- WRONG: "The request hits the FastAPI backend in interface/server.py, then goes to the GridMindAPI in interface/api.py."
- RIGHT: "The request hits the FastAPI backend, then flows through the API layer to the RAG pipeline."

# CRITICAL — Writing Style for Model Answers
- Write ALL model answers like the developer is actually speaking in an interview.
- Use first person: "So what I did was...", "The reason I went with this approach is..."
- Be specific and technical — mention class names, patterns, and concepts, but NOT file paths.
- Sound confident but honest: "I know SQLite isn't ideal for production, but for a single-user tool it's perfect because..."
- Include natural speech patterns: "basically", "the idea is", "what's cool about this is"
- Each answer should flow naturally — not bullet points, but conversational paragraphs.

# CRITICAL — Follow-Up Talking Points
- Each follow-up question MUST include 1-2 sentence talking points — quick hints for how to respond.
- These should be concise bullet-style hints, not full model answers.
- Example: Question: "What would you do differently at 10x scale?" → Talking points: "Mention switching to PostgreSQL for concurrent writes, adding Redis for caching, and using Celery for async LLM calls."

# CRITICAL — Question Quality
- Questions should be PROJECT-SPECIFIC, not generic. Instead of "What is Flask?", ask "Why did you choose Flask over FastAPI for this project?"
- Follow-up questions should dig deeper into the initial answer.
- Key terms should be things the developer should naturally weave into their answer.

# Rules
- Ground ALL questions and answers in the actual codebase.
- Model answers must reference real components, patterns, and architecture from the project — but NOT file paths.
- Don't include questions about features that don't exist in the codebase.
- Make curveball questions genuinely challenging but fair.
- Red flags and weak spots should be honest and practical.
"""

# Registry for easy dynamic access
SECTION_SCHEMAS = {
    1: ProjectOverview,
    2: Section2TechStack,
    3: Section3Architecture,
    4: Section4Environment,
    5: Section5CoreFunctions,
    6: FrameworkDeepDive,  # Used per-framework in Phase 1 (not for Phase 0)
    7: Section7DesignDecisions,
    8: Section8FailureLog,
    9: Section9APIs,
    10: Section10DataModels,
    11: Section11Testing,
    12: Section12Scalability,
    13: Section13Deployment,
    14: Section14InterviewBank,
}

SECTION_PROMPTS = {
    1: SECTION_1_SYSTEM_PROMPT,
    2: SECTION_2_SYSTEM_PROMPT,
    3: SECTION_3_SYSTEM_PROMPT,
    4: SECTION_4_SYSTEM_PROMPT,
    5: SECTION_5_SYSTEM_PROMPT,
    6: FRAMEWORK_DEEP_DIVE_PROMPT,
    7: SECTION_7_SYSTEM_PROMPT,
    8: SECTION_8_SYSTEM_PROMPT,
    9: SECTION_9_SYSTEM_PROMPT,
    10: SECTION_10_SYSTEM_PROMPT,
    11: SECTION_11_SYSTEM_PROMPT,
    12: SECTION_12_SYSTEM_PROMPT,
    13: SECTION_13_SYSTEM_PROMPT,
    14: SECTION_14_SYSTEM_PROMPT,
}


