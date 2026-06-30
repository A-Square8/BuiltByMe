from pathlib import Path

SKIP_DIRS = {
    'node_modules', '.git', '__pycache__', '.venv', 'venv', 'env',
    '.env', 'dist', 'build', '.next', '.nuxt', 'target', 'bin', 'obj',
    '.idea', '.vscode', '.vs', 'vendor', 'Pods', '.gradle',
    'coverage', '.nyc_output', '.pytest_cache', '.mypy_cache',
    'egg-info', '.eggs', '.tox', 'migrations', '.terraform',
    'bower_components', 'jspm_packages', '.cache', '.parcel-cache',
}

SKIP_EXTENSIONS = {
    '.pyc', '.pyo', '.class', '.o', '.obj', '.exe', '.dll', '.so',
    '.dylib', '.a', '.lib', '.jar', '.war', '.ear', '.zip', '.tar',
    '.gz', '.bz2', '.rar', '.7z', '.png', '.jpg', '.jpeg', '.gif',
    '.bmp', '.ico', '.svg', '.webp', '.mp3', '.mp4', '.avi', '.mov',
    '.wmv', '.flv', '.pdf', '.doc', '.docx', '.xls', '.xlsx',
    '.ppt', '.pptx', '.db', '.sqlite', '.sqlite3', '.pkl', '.pickle',
    '.h5', '.hdf5', '.npy', '.npz', '.jbl', '.joblib', '.model',
    '.bin', '.dat', '.csv', '.tsv', '.log', '.lock', '.woff',
    '.woff2', '.ttf', '.eot', '.min.js', '.min.css', '.map',
    '.DS_Store', '.env',
}

MAX_FILE_SIZE = 500_000


def should_skip_dir(dirname):
    return dirname in SKIP_DIRS or dirname.startswith('.')


def should_skip_file(filepath, size=0):
    path = Path(filepath)
    if path.suffix.lower() in SKIP_EXTENSIONS:
        return True
    if path.name.startswith('.') and path.name not in {'.gitignore', '.dockerignore', '.env.example'}:
        return True
    if size > MAX_FILE_SIZE:
        return True
    return False
