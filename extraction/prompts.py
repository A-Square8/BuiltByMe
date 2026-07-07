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
        description="A concise, 20-25 second explanation written in extremely simple, natural spoken English. Use basic vocabulary that is easy to memorize naturally, while keeping correct technical terms."
    )
    code_snippet: str = Field(
        default="",
        description="Relevant code snippet for revision, if applicable. Empty string if not applicable."
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
    basics: List[Concept] = Field(
        ...,
        description="Basic foundational concepts (e.g., what is it, core architecture). Each explanation should be like a 20-second spoken English pitch."
    )
    directly_used_concepts: List[Concept] = Field(
        ...,
        description="Concepts, features, or patterns from this framework that are DIRECTLY USED in the project code. Each explanation should be a 25-second spoken English pitch, accompanied by a code snippet for revision."
    )
    indirect_concepts: List[Concept] = Field(
        ...,
        description="Important concepts that are NOT directly used in the project, but are essential to know if you mention this tech stack in an interview (e.g., tools/agents in LangChain even if you only use agents). Each explanation should be a 25-second spoken English pitch."
    )

FRAMEWORK_DEEP_DIVE_PROMPT = """You are a senior engineer helping someone prepare to confidently discuss a specific framework in a technical interview.

You are analyzing how a framework is used in a real project. You have the actual source code.

# Instructions

## Part 1: Basics
- Cover foundational concepts (what it is, how it works at a high level).
- Write each explanation like you're telling a friend over coffee: "So basically, LangChain is like a toolkit that lets you chain together different AI operations..."
- 20 seconds max per explanation. Keep it punchy.

## Part 2: Directly Used Concepts
- Find features/patterns from this framework that are ACTUALLY USED in the project code.
- Explain each like: "In my project, I use ChatGroq to connect to the Groq API — basically I pass in the model name and API key, and it gives me back a chat interface..."
- Include a code snippet from the actual project for quick revision.
- This MUST be grounded in real code — don't make up usage.

## Part 3: Indirect Concepts
- Cover important concepts you DIDN'T use but should know for interviews (e.g., if you use LangChain chains, you should still know about agents/tools).
- Explain like: "I didn't use this in my project, but if an interviewer asks — agents are basically LLMs that can decide which tools to call on their own..."
- Include example code snippets where helpful.

# CRITICAL — Writing Style
- Sound like a real person explaining things, NOT a documentation page.
- WRONG: "LangChain is a framework for developing applications powered by language models."
- RIGHT: "LangChain is basically a toolkit that makes it way easier to build apps with LLMs — you can chain together prompts, connect to APIs, parse outputs, all that stuff."
- Use "basically", "so", "the idea is", "what this does is" — natural speech patterns.
- Be technically accurate but explain simply. Use correct terms but wrap them in plain English.
- Short sentences. No walls of text. Each explanation should feel like something you'd actually say out loud.

# Rules
- Do NOT hallucinate features not in the provided code for "Directly Used Concepts."
- Code snippets should be realistic, correct, and self-contained.
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
}

