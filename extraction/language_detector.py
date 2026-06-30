from pathlib import Path

LANGUAGE_MAP = {
    '.py': 'python',
    '.js': 'javascript',
    '.ts': 'typescript',
    '.jsx': 'javascript',
    '.tsx': 'typescript',
    '.java': 'java',
    '.cpp': 'cpp',
    '.c': 'c',
    '.cs': 'csharp',
    '.go': 'go',
    '.rs': 'rust',
    '.php': 'php',
    '.rb': 'ruby',
    '.swift': 'swift',
    '.kt': 'kotlin',
    '.html': 'html',
    '.css': 'css',
    '.json': 'json',
    '.yaml': 'yaml',
    '.yml': 'yaml',
    '.toml': 'toml',
    '.dart': 'dart',
}

FULL_EXTRACT_FILES = {
    'readme.md', 'readme.rst', 'readme.txt', 'readme',
    'requirements.txt', 'setup.py', 'setup.cfg', 'pyproject.toml',
    'package.json', 'package-lock.json',
    'cargo.toml', 'go.mod', 'go.sum',
    'gemfile', 'composer.json', 'pom.xml', 'build.gradle',
    'dockerfile', 'docker-compose.yml', 'docker-compose.yaml',
    '.env.example', 'makefile', 'cmakelists.txt',
    'license', 'license.md', 'license.txt',
    '.gitignore', '.dockerignore',
}


def detect_language(filename):
    ext = Path(filename).suffix.lower()
    return LANGUAGE_MAP.get(ext, None)


def should_full_extract(filename):
    return Path(filename).name.lower() in FULL_EXTRACT_FILES
