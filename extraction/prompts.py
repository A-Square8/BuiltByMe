from pydantic import BaseModel, Field

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

# Registry for easy dynamic access
SECTION_SCHEMAS = {
    1: ProjectOverview,
}

SECTION_PROMPTS = {
    1: SECTION_1_SYSTEM_PROMPT,
}
