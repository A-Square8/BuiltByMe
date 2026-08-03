import os
import re
import json
import stat
import threading
import io
import textwrap
import base64
import zlib
import html as html_module
from cryptography.fernet import Fernet
from flask import Flask, request, jsonify, send_from_directory, send_file
import traceback as traceback_module
from flask_cors import CORS
from extraction.pipeline import ExtractionPipeline
from extraction.database import ProjectDB
from extraction.llm_gateway import generate_content
from extraction.prompts import (
    SECTION_SCHEMAS, SECTION_PROMPTS,
    FileRetrievalRequest, FILE_RETRIEVAL_PROMPT,
    FrameworkDiscovery, FRAMEWORK_DISCOVERY_PROMPT,
    FrameworkDeepDive, FRAMEWORK_DEEP_DIVE_PROMPT,
    Section3Architecture, Section4Environment,
    Section5CoreFunctions, Section7DesignDecisions, Section8FailureLog,
    Section9APIs, Section10DataModels, Section11Testing, Section12Scalability,
    Section13Deployment, Section14InterviewBank
)

app = Flask(__name__, static_folder='ui', static_url_path='')
CORS(app, origins=['http://localhost:5000', 'http://127.0.0.1:5000'])


@app.after_request
def set_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    return response


def secure_project_name(name):
    """Validate and sanitize project name to prevent path traversal."""
    if not name or not isinstance(name, str):
        return None
    # Strip any path separators and parent directory references
    name = name.strip()
    if '..' in name or '/' in name or '\\' in name or '\x00' in name:
        return None
    # Only allow alphanumeric, hyphens, underscores, and dots
    if not re.match(r'^[a-zA-Z0-9._-]+$', name):
        return None
    return name


def _escape_html(text):
    """Escape HTML special characters to prevent XSS."""
    if text is None:
        return ''
    return html_module.escape(str(text))

PROJECTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'my_projects')
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.json')
MASTER_KEY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.master.key')
extraction_status = {}

def get_fernet():
    if not os.path.exists(MASTER_KEY_FILE):
        key = Fernet.generate_key()
        # Create file with restrictive permissions (owner read/write only)
        fd = os.open(MASTER_KEY_FILE, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        try:
            os.write(fd, key)
        finally:
            os.close(fd)
    else:
        # Ensure existing key file has correct permissions
        try:
            os.chmod(MASTER_KEY_FILE, stat.S_IRUSR | stat.S_IWUSR)
        except OSError:
            pass
    with open(MASTER_KEY_FILE, 'rb') as f:
        key = f.read()
    return Fernet(key)

def encrypt_val(val: str) -> str:
    if not val:
        return val
    f = get_fernet()
    return f.encrypt(val.encode()).decode()

def decrypt_val(val: str) -> str:
    if not val:
        return val
    f = get_fernet()
    try:
        return f.decrypt(val.encode()).decode()
    except Exception:
        return val

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_config(cfg):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(cfg, f, indent=2)

@app.route('/')
def index():
    return send_from_directory('ui', 'index.html')

@app.route('/api/config/pat', methods=['GET'])
def get_pat():
    cfg = load_config()
    pat = decrypt_val(cfg.get('github_pat', ''))
    # Mask the PAT for security - only show last 4 chars
    if pat and len(pat) > 8:
        masked = '*' * (len(pat) - 4) + pat[-4:]
    else:
        masked = pat
    return jsonify({'pat': masked, 'has_pat': bool(pat)})

@app.route('/api/config/pat', methods=['POST'])
def set_pat():
    data = request.json
    pat = (data.get('pat') or '').strip()
    cfg = load_config()
    # Don't save masked values back
    if pat and not pat.startswith('*'):
        cfg['github_pat'] = encrypt_val(pat)
    elif not pat:
        cfg.pop('github_pat', None)
    save_config(cfg)
    return jsonify({'message': 'Token saved successfully' if pat else 'Token cleared'})

@app.route('/api/config/llm_keys', methods=['GET'])
def get_llm_keys():
    cfg = load_config()
    keys = cfg.get('llm_keys', [])
    # Return masked keys to frontend
    masked_keys = []
    for k in keys:
        raw_key = decrypt_val(k.get('key', ''))
        masked_val = '*' * 8 + raw_key[-4:] if len(raw_key) > 4 else '***'
        masked_keys.append({
            'name': k.get('name'),
            'provider': k.get('provider'),
            'key': masked_val
        })
    return jsonify(masked_keys)

@app.route('/api/config/llm_keys', methods=['POST'])
def add_llm_key():
    data = request.json
    name = (data.get('name') or '').strip()
    provider = (data.get('provider') or '').strip()
    key = (data.get('key') or '').strip()
    
    if not name or not key or not provider:
        return jsonify({'error': 'Name, provider, and key are required'}), 400
        
    cfg = load_config()
    keys = cfg.get('llm_keys', [])
    
    keys.append({
        'name': name,
        'provider': provider,
        'key': encrypt_val(key)
    })
    
    cfg['llm_keys'] = keys
    save_config(cfg)
    return jsonify({'message': 'Key saved successfully'})

@app.route('/api/config/llm_keys/<int:index>', methods=['DELETE'])
def delete_llm_key(index):
    cfg = load_config()
    keys = cfg.get('llm_keys', [])
    if 0 <= index < len(keys):
        keys.pop(index)
        cfg['llm_keys'] = keys
        save_config(cfg)
        return jsonify({'message': 'Key deleted successfully'})
    return jsonify({'error': 'Key not found'}), 404


@app.route('/api/projects', methods=['GET'])
def list_projects():
    if not os.path.exists(PROJECTS_DIR):
        return jsonify([])
    projects = []
    for name in sorted(os.listdir(PROJECTS_DIR)):
        if not secure_project_name(name):
            continue
        project_path = os.path.join(PROJECTS_DIR, name)
        db_path = os.path.join(project_path, 'project.db')
        if os.path.isdir(project_path) and os.path.exists(db_path):
            try:
                db = ProjectDB(db_path)
                info = db.get_repo_info()
                status = db.get_extraction_status()
                db.close()
                projects.append({
                    'name': name,
                    'info': info,
                    'extraction_status': status.get('status') if status else None,
                })
            except Exception:
                projects.append({'name': name, 'info': None, 'extraction_status': 'unknown'})
    return jsonify(projects)


@app.route('/api/extract', methods=['POST'])
def start_extraction():
    data = request.json
    repo_url = data.get('repo_url', '').strip()
    token = (data.get('token') or '').strip() or None

    # Fall back to saved PAT if no token provided
    if not token:
        cfg = load_config()
        token = decrypt_val(cfg.get('github_pat', '')) or None

    ignore_patterns_str = data.get('ignore_patterns', '').strip()
    ignore_patterns = [p.strip() for p in ignore_patterns_str.split(',')] if ignore_patterns_str else []

    if not repo_url:
        return jsonify({'error': 'Repository URL is required'}), 400

    try:
        parts = repo_url.replace('https://github.com/', '').replace('.git', '').split('/')
        repo_name = parts[1]
    except (IndexError, ValueError):
        return jsonify({'error': 'Invalid GitHub URL'}), 400

    if not secure_project_name(repo_name):
        return jsonify({'error': 'Invalid repository name'}), 400

    if repo_name in extraction_status and extraction_status[repo_name].get('status') == 'extracting':
        return jsonify({'error': 'Extraction already in progress'}), 409

    extraction_status[repo_name] = {'status': 'starting', 'total': 0, 'processed': 0, 'current_file': '', 'errors': []}

    def run_pipeline():
        pipeline = ExtractionPipeline(repo_url, token, PROJECTS_DIR, ignore_patterns=ignore_patterns)

        def on_progress(prog):
            extraction_status[repo_name] = dict(prog)

        pipeline.run(progress_callback=on_progress)

    thread = threading.Thread(target=run_pipeline, daemon=True)
    thread.start()

    return jsonify({'message': 'Extraction started', 'project_name': repo_name})


@app.route('/api/extract/status/<project_name>', methods=['GET'])
def get_extraction_status(project_name):
    if project_name in extraction_status:
        return jsonify(extraction_status[project_name])
    return jsonify({'status': 'unknown'})


@app.route('/api/project/<project_name>', methods=['GET'])
def get_project(project_name):
    project_name = secure_project_name(project_name)
    if not project_name:
        return jsonify({'error': 'Invalid project name'}), 400
    db_path = os.path.join(PROJECTS_DIR, project_name, 'project.db')
    if not os.path.exists(db_path):
        return jsonify({'error': 'Project not found'}), 404

    db = ProjectDB(db_path)
    info = db.get_repo_info()
    files = db.get_files()
    commits = db.get_commits()
    status = db.get_extraction_status()
    for f in files:
        if f.get('metadata'):
            try:
                f['metadata'] = json.loads(f['metadata'])
            except (json.JSONDecodeError, TypeError):
                pass
        
        # Fetch blocks and attach
        blocks = db.get_code_blocks(f['id'])
        for b in blocks:
            if b.get('content') and len(b['content']) > 5000:
                b['content'] = b['content'][:5000] + '\n... (truncated)'
        f['blocks'] = blocks

    db.close()

    return jsonify({
        'info': info,
        'files': files,
        'commits': commits,
        'extraction_status': status,
    })


@app.route('/api/project/<project_name>/generate', methods=['POST'])
def generate_section(project_name):
    project_name = secure_project_name(project_name)
    if not project_name:
        return jsonify({'error': 'Invalid project name'}), 400
    db_path = os.path.join(PROJECTS_DIR, project_name, 'project.db')
    if not os.path.exists(db_path):
        return jsonify({'error': 'Project not found'}), 404

    data = request.json
    try:
        section_id = int(data.get('section_id'))
    except (TypeError, ValueError):
        return jsonify({'error': 'Invalid section_id'}), 400
    provider = data.get('provider')
    api_key = data.get('api_key')
    strategy = data.get('strategy', '1_pass')
    custom_instructions = data.get('custom_instructions', '')
    detail_level = data.get('detail_level', 1)  # 0=Short, 1=Medium, 2=Detailed

    if not provider or not api_key:
        return jsonify({'error': 'Provider and API key are required'}), 400
        
    # If api_key is an index of a saved key
    if str(api_key).startswith('saved_'):
        try:
            key_index = int(api_key.replace('saved_', ''))
            cfg = load_config()
            keys = cfg.get('llm_keys', [])
            if 0 <= key_index < len(keys):
                api_key = decrypt_val(keys[key_index].get('key'))
                provider = keys[key_index].get('provider')
            else:
                return jsonify({'error': 'Invalid saved key reference'}), 400
        except ValueError:
            return jsonify({'error': 'Invalid saved key format'}), 400

    if section_id not in SECTION_SCHEMAS:
        return jsonify({'error': 'Unsupported section ID'}), 400

    db = ProjectDB(db_path)
    try:
        # Build context
        info = db.get_repo_info()
        files = db.get_files()
        
        context_str = f"Project Name: {info.get('full_name')}\n"
        context_str += f"Description: {info.get('description')}\n"
        context_str += f"Language: {info.get('language')}\n\n"
        
        passes_log = []  # Track pass info for frontend terminal
        
        if section_id == 2:
            # For section 2, we ONLY want unique imports across all files.
            all_imports = set()
            for f in files:
                if f.get('metadata'):
                    try:
                        meta = json.loads(f['metadata']) if isinstance(f['metadata'], str) else f['metadata']
                        
                        imports = meta.get('imports', [])
                        if isinstance(imports, list):
                            all_imports.update(imports)
                        includes = meta.get('includes', [])
                        if isinstance(includes, list):
                            all_imports.update(includes)
                        uses = meta.get('uses', [])
                        if isinstance(uses, list):
                            all_imports.update(uses)
                    except json.JSONDecodeError:
                        pass
            
            context_str += "Unique Imports Found in Project:\n"
            for imp in sorted(all_imports):
                context_str += f"- {imp}\n"
            passes_log.append({'pass': 1, 'info': 'Import-only mode for Tech Stack section'})
        else:
            context_str += "Files in repository:\n"
            for f in files:
                context_str += f"- {f['path']} ({f['size']} bytes)\n"
            
            # Add commit history for Section 8 (Failure Log) - LLM can analyze commit messages for evidence of fixes/bugs
            if section_id == 8:
                commits = db.get_commits()
                if commits:
                    context_str += "\n\n--- COMMIT HISTORY (recent 100) ---\n"
                    for c in commits[:100]:
                        context_str += f"[{c.get('sha', '')}] {c.get('date', '')} - {c.get('message', '').split(chr(10))[0]}\n"
                    context_str += "--- END COMMIT HISTORY ---\n"
                
            # Add README content if it exists
            readme_file = next((f for f in files if 'readme' in f['path'].lower()), None)
            if readme_file:
                blocks = db.get_code_blocks(readme_file['id'])
                readme_content = "".join([b['content'] for b in blocks if b['content']])
                if readme_content:
                    context_str += f"\n\n--- README.md ---\n{readme_content}\n--- END README ---\n"
                    
            if strategy == '1_pass':
                # 1-pass: dump entire codebase into context
                context_str += "\n\n--- ENTIRE CODEBASE ---\n"
                for f in files:
                    if 'readme' in f['path'].lower(): continue
                    blocks = db.get_code_blocks(f['id'])
                    file_content = "".join([b['content'] for b in blocks if b['content']])
                    if file_content:
                        context_str += f"\nFile: {f['path']}\n{file_content}\n"
                context_str += "--- END ENTIRE CODEBASE ---\n"
                passes_log.append({'pass': 1, 'info': 'Full codebase dump (1-pass)'})
                
            elif strategy == '2_pass':
                # ===== PASS 1: Build skeleton and ask LLM which files it needs =====
                skeleton_str = context_str  # Already has project info + file list + README
                skeleton_str += "\n\n--- FILE SKELETON WITH METADATA ---\n"
                for f in files:
                    if 'readme' in f['path'].lower():
                        continue
                    skeleton_str += f"\nFile: {f['path']} | Language: {f.get('language', 'unknown')} | Size: {f['size']} bytes\n"
                    # Add metadata summary (imports, class/function names)
                    if f.get('metadata'):
                        try:
                            meta = json.loads(f['metadata']) if isinstance(f['metadata'], str) else f['metadata']
                            imports = meta.get('imports', []) or meta.get('includes', []) or meta.get('uses', [])
                            if imports:
                                skeleton_str += f"  Imports: {', '.join(imports[:20])}\n"
                        except (json.JSONDecodeError, TypeError):
                            pass
                    # Add code block names (class/function signatures without content)
                    blocks = db.get_code_blocks(f['id'])
                    block_names = []
                    for b in blocks:
                        if b.get('block_type') in ('class', 'function', 'method') and b.get('name'):
                            prefix = b['block_type']
                            parent = f" (in {b['parent_name']})" if b.get('parent_name') else ''
                            block_names.append(f"{prefix} {b['name']}{parent}")
                    if block_names:
                        skeleton_str += f"  Definitions: {', '.join(block_names[:15])}\n"
                skeleton_str += "--- END FILE SKELETON ---\n"
                
                # Get the section description for context
                section_names_map = {
                    1: 'Project Overview', 2: 'Tech Stack', 3: 'Architecture & Module Map',
                    4: 'Environment & Secrets', 5: 'Core Functions & Classes',
                    6: 'Technology Deep Dives', 7: 'Design Decisions',
                    8: 'Failure Log & Learnings', 9: 'APIs & Interfaces',
                    10: 'Data Models & Storage', 11: 'Testing Strategy',
                    12: 'Scalability & Production', 13: 'Deployment & Infra',
                    14: 'Interview Question Bank'
                }
                section_topic = section_names_map.get(section_id, f'Section {section_id}')
                
                retrieval_user_prompt = (
                    f"I need to generate the following documentation section: **{section_topic}**\n\n"
                    f"Please analyze the file skeleton below and tell me which files I should retrieve "
                    f"the full source code for.\n\n{skeleton_str}"
                )
                
                retrieval_result = generate_content(
                    provider=provider,
                    api_key=api_key,
                    system_prompt=FILE_RETRIEVAL_PROMPT,
                    user_prompt=retrieval_user_prompt,
                    response_schema=FileRetrievalRequest
                )
                
                # Parse the requested files
                if hasattr(retrieval_result, 'model_dump'):
                    retrieval_data = retrieval_result.model_dump()
                else:
                    retrieval_data = retrieval_result
                    
                requested_paths = retrieval_data.get('requested_files', [])
                reasoning = retrieval_data.get('reasoning', '')
                
                # Cap at 15 files
                requested_paths = requested_paths[:15]
                
                passes_log.append({
                    'pass': 1,
                    'info': f'LLM analyzed skeleton and requested {len(requested_paths)} files',
                    'reasoning': reasoning,
                    'requested_files': requested_paths
                })
                
                # ===== PASS 2: Fetch requested files and build focused context =====
                # Build a path->file lookup
                file_lookup = {f['path']: f for f in files}
                
                context_str += "\n\n--- SELECTED SOURCE CODE (retrieved via 2-pass) ---\n"
                retrieved_count = 0
                for path in requested_paths:
                    file_record = file_lookup.get(path)
                    if not file_record:
                        continue
                    if 'readme' in path.lower():
                        continue  # Already included above
                    blocks = db.get_code_blocks(file_record['id'])
                    file_content = "".join([b['content'] for b in blocks if b['content']])
                    if file_content:
                        context_str += f"\nFile: {path}\n{file_content}\n"
                        retrieved_count += 1
                context_str += "--- END SELECTED SOURCE CODE ---\n"
                
                passes_log.append({
                    'pass': 2,
                    'info': f'Retrieved {retrieved_count} files for focused generation'
                })

        system_prompt = SECTION_PROMPTS[section_id]
        
        # Inject detail level instructions
        detail_instructions = {
            0: "\n\nDETAIL LEVEL: SHORT. Keep all responses brief and concise. Use bullet points over paragraphs. Limit explanations to 1-2 sentences each. Prioritize breadth over depth.",
            1: "\n\nDETAIL LEVEL: MEDIUM. Provide balanced detail — 2-3 sentences for paragraph fields. Include enough technical depth to be interview-ready without being exhaustive.",
            2: "\n\nDETAIL LEVEL: DETAILED. Provide comprehensive, in-depth analysis. Use 5-8 sentences for paragraph fields. Include technical nuances, edge cases, trade-offs, and implementation specifics. This should be thorough enough for a senior-level deep-dive discussion."
        }
        system_prompt += detail_instructions.get(detail_level, detail_instructions[1])
        
        if custom_instructions:
            system_prompt += f"\n\nUser Custom Instructions:\n{custom_instructions}"
            
        user_prompt = f"Please generate the section based on the following context:\n\n{context_str}"
        
        result = generate_content(
            provider=provider,
            api_key=api_key,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            response_schema=SECTION_SCHEMAS[section_id]
        )
        
        content = result.model_dump() if hasattr(result, 'model_dump') else result
        
        section_names = {
            1: 'Project Overview', 2: 'Tech Stack', 3: 'Architecture & Module Map',
            4: 'Environment & Secrets', 5: 'Core Functions & Classes',
            7: 'Design Decisions', 8: 'Failure Log & Learnings',
            9: 'APIs & Interfaces', 10: 'Data Models & Storage',
            11: 'Testing Strategy', 12: 'Scalability & Production',
            13: 'Deployment & Infra', 14: 'Interview Question Bank'
        }
        
        db.save_generated_section(section_id, section_names.get(section_id, f'Section {section_id}'), content)
        
        return jsonify({'message': 'Success', 'content': content, 'passes': passes_log})
    except Exception as e:
        app.logger.error(f'Section generation error: {traceback_module.format_exc()}')
        with open('server_errors.log', 'a') as ef:
            ef.write(f"--- [Section {section_id}] ---\n{traceback_module.format_exc()}\n")
        return jsonify({'error': f'Section {section_id} generation failed: {str(e)}'}), 500
    finally:
        db.close()


@app.route('/api/project/<project_name>/generate_s6', methods=['POST'])
def generate_section6(project_name):
    """
    Section 6: Technology Deep Dives — Chunked per-framework generation.
    
    Called in two modes:
    1. phase=discovery (or no phase): Run Phase 0 to discover frameworks. Returns framework list.
    2. phase=deep_dive, framework_index=N: Generate deep dive for framework N. Merges into section 6.
    """
    project_name = secure_project_name(project_name)
    if not project_name:
        return jsonify({'error': 'Invalid project name'}), 400
    db_path = os.path.join(PROJECTS_DIR, project_name, 'project.db')
    if not os.path.exists(db_path):
        return jsonify({'error': 'Project not found'}), 404

    data = request.json
    provider = data.get('provider')
    api_key = data.get('api_key')
    phase = data.get('phase', 'discovery')
    framework_index = data.get('framework_index')
    detail_level = data.get('detail_level', 2)  # Default to Detailed for section 6
    custom_instructions = data.get('custom_instructions', '')

    if not provider or not api_key:
        return jsonify({'error': 'Provider and API key are required'}), 400

    # Resolve saved key references
    if str(api_key).startswith('saved_'):
        try:
            key_index = int(api_key.replace('saved_', ''))
            cfg = load_config()
            keys = cfg.get('llm_keys', [])
            if 0 <= key_index < len(keys):
                api_key = decrypt_val(keys[key_index].get('key'))
                provider = keys[key_index].get('provider')
            else:
                return jsonify({'error': 'Invalid saved key reference'}), 400
        except ValueError:
            return jsonify({'error': 'Invalid saved key format'}), 400

    db = ProjectDB(db_path)
    try:
        info = db.get_repo_info()
        files = db.get_files()

        # Load existing section 6 content for resume support
        existing_section = db.get_generated_section(6)
        existing_content = {}
        if existing_section and existing_section.get('content'):
            try:
                existing_content = json.loads(existing_section['content']) if isinstance(existing_section['content'], str) else existing_section['content']
            except (json.JSONDecodeError, TypeError):
                existing_content = {}

        # ===== PHASE 0: Framework Discovery =====
        if phase == 'discovery':
            # Build context: project info + all imports + file skeleton
            context_str = f"Project Name: {info.get('full_name')}\n"
            context_str += f"Description: {info.get('description')}\n"
            context_str += f"Language: {info.get('language')}\n\n"

            # Collect all imports
            all_imports = set()
            file_imports_map = {}
            for f in files:
                if f.get('metadata'):
                    try:
                        meta = json.loads(f['metadata']) if isinstance(f['metadata'], str) else f['metadata']
                        file_imps = []
                        for key in ('imports', 'includes', 'uses'):
                            vals = meta.get(key, [])
                            if isinstance(vals, list):
                                all_imports.update(vals)
                                file_imps.extend(vals)
                        if file_imps:
                            file_imports_map[f['path']] = file_imps
                    except (json.JSONDecodeError, TypeError):
                        pass

            context_str += "All imports found in the project:\n"
            for imp in sorted(all_imports):
                context_str += f"- {imp}\n"

            context_str += "\nFile structure with their imports:\n"
            for f in files:
                imps = file_imports_map.get(f['path'], [])
                imp_str = f" [imports: {', '.join(imps[:10])}]" if imps else ""
                context_str += f"- {f['path']} ({f.get('language', 'unknown')}, {f['size']}B){imp_str}\n"

            # Check if Section 2 (Tech Stack) exists for richer context
            section2 = db.get_generated_section(2)
            if section2 and section2.get('content'):
                try:
                    s2_content = json.loads(section2['content']) if isinstance(section2['content'], str) else section2['content']
                    context_str += "\n\nExisting Tech Stack Analysis:\n"
                    context_str += json.dumps(s2_content, indent=2)
                except (json.JSONDecodeError, TypeError):
                    pass

            discovery_result = generate_content(
                provider=provider,
                api_key=api_key,
                system_prompt=FRAMEWORK_DISCOVERY_PROMPT,
                user_prompt=f"Analyze this project and identify the frameworks for deep dives:\n\n{context_str}",
                response_schema=FrameworkDiscovery
            )

            discovery_data = discovery_result.model_dump() if hasattr(discovery_result, 'model_dump') else discovery_result

            # Save discovery to section 6 content
            existing_content['discovery'] = discovery_data
            if 'deep_dives' not in existing_content:
                existing_content['deep_dives'] = []

            db.save_generated_section(6, 'Technology Deep Dives', existing_content)

            # Determine which frameworks are already completed
            completed_names = [d.get('framework_name', '') for d in existing_content.get('deep_dives', [])]
            frameworks = discovery_data.get('frameworks', [])

            return jsonify({
                'message': 'Discovery complete',
                'phase': 'discovery',
                'frameworks': frameworks,
                'total': len(frameworks),
                'completed': completed_names,
                'remaining': [fw for fw in frameworks if fw['name'] not in completed_names]
            })

        # ===== PHASE 1: Per-Framework Deep Dive =====
        elif phase == 'deep_dive':
            if framework_index is None:
                return jsonify({'error': 'framework_index is required for deep_dive phase'}), 400

            framework_index = int(framework_index)

            # Load discovery data
            discovery = existing_content.get('discovery', {})
            frameworks = discovery.get('frameworks', [])
            if framework_index < 0 or framework_index >= len(frameworks):
                return jsonify({'error': f'Invalid framework_index: {framework_index}'}), 400

            fw = frameworks[framework_index]
            fw_name = fw['name']

            # Check if already completed (resume support)
            existing_dives = existing_content.get('deep_dives', [])
            if any(d.get('framework_name') == fw_name for d in existing_dives):
                return jsonify({
                    'message': f'{fw_name} already completed',
                    'phase': 'deep_dive',
                    'framework_name': fw_name,
                    'framework_index': framework_index,
                    'skipped': True
                })

            # Build focused context: only files relevant to this framework
            context_str = f"Project Name: {info.get('full_name')}\n"
            context_str += f"Description: {info.get('description')}\n"
            context_str += f"Language: {info.get('language')}\n\n"
            context_str += f"Framework to analyze: {fw_name} ({fw.get('category', '')})\n"
            context_str += f"Relevant files: {', '.join(fw.get('relevant_files', []))}\n\n"

            # Fetch actual code for relevant files
            file_lookup = {f['path']: f for f in files}
            context_str += "--- SOURCE CODE OF RELEVANT FILES ---\n"
            for path in fw.get('relevant_files', []):
                file_record = file_lookup.get(path)
                if not file_record:
                    continue
                blocks = db.get_code_blocks(file_record['id'])
                file_content = "".join([b['content'] for b in blocks if b['content']])
                if file_content:
                    context_str += f"\nFile: {path}\n{file_content}\n"
            context_str += "--- END SOURCE CODE ---\n"

            # Build the system prompt with detail level guidance
            system_prompt = FRAMEWORK_DEEP_DIVE_PROMPT

            # Guide the LLM on directly-used completeness and indirect scaling
            system_prompt += "\n\nIMPORTANT COVERAGE GUIDANCE:"
            system_prompt += "\n- For 'directly_used_concepts': Be EXHAUSTIVE. Cover every single feature, API, decorator, method, class, or pattern from this framework that appears in the provided code. Do not skip anything."
            system_prompt += "\n- For 'indirect_concepts': Include MANY topics. For major interview-heavy technologies, provide a large number of concepts covering the full breadth — core concepts, advanced features, ecosystem tools, design patterns, performance considerations, common interview topics. For simpler libraries, still provide a solid number covering all essentials. Err on the side of MORE topics, not fewer."
            system_prompt += "\n- For 'interview_quickfire': Include the most commonly asked interview questions about this specific framework — aim for 8-12 Q&A pairs."

            detail_instructions = {
                0: "\n\nDETAIL LEVEL: SHORT. Keep explanations concise but still comprehensive — 2-3 sentences per concept. Cover the essentials without going into edge cases.",
                1: "\n\nDETAIL LEVEL: MEDIUM. Balanced depth — 4-6 sentences per concept. Include enough detail for confident interview answers. Mention key nuances.",
                2: "\n\nDETAIL LEVEL: DETAILED. Comprehensive, in-depth coverage — 6-8 sentences per concept. Include edge cases, internal mechanics, trade-offs, and production considerations. This should be thorough enough for a senior-level deep-dive discussion."
            }
            system_prompt += detail_instructions.get(detail_level, detail_instructions[2])

            if custom_instructions:
                system_prompt += f"\n\nUser Custom Instructions:\n{custom_instructions}"

            user_prompt = f"Generate a comprehensive deep dive for {fw_name}:\n\n{context_str}"

            result = generate_content(
                provider=provider,
                api_key=api_key,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                response_schema=FrameworkDeepDive
            )

            dive_data = result.model_dump() if hasattr(result, 'model_dump') else result

            # Merge into section 6 content
            existing_dives.append(dive_data)
            existing_content['deep_dives'] = existing_dives
            db.save_generated_section(6, 'Technology Deep Dives', existing_content)

            # Calculate overall progress
            total_frameworks = len(frameworks)
            completed_count = len(existing_dives)

            return jsonify({
                'message': f'{fw_name} deep dive complete',
                'phase': 'deep_dive',
                'framework_name': fw_name,
                'framework_index': framework_index,
                'content': dive_data,
                'progress': {
                    'completed': completed_count,
                    'total': total_frameworks
                }
            })

        else:
            return jsonify({'error': f'Unknown phase: {phase}'}), 400

    except Exception as e:
        app.logger.error(f'Section 6 generation error: {traceback_module.format_exc()}')
        with open('server_errors.log', 'a') as ef:
            ef.write(f"--- [Section 6 ({phase})] ---\n{traceback_module.format_exc()}\n")
        return jsonify({'error': f'Section 6 generation failed: {str(e)}'}), 500
    finally:
        db.close()

@app.route('/api/project/<project_name>/generated', methods=['GET'])
def get_generated_sections(project_name):
    project_name = secure_project_name(project_name)
    if not project_name:
        return jsonify({'error': 'Invalid project name'}), 400
    db_path = os.path.join(PROJECTS_DIR, project_name, 'project.db')
    if not os.path.exists(db_path):
        return jsonify({'error': 'Project not found'}), 404

    db = ProjectDB(db_path)
    try:
        sections = db.get_generated_sections()
        for s in sections:
            try:
                s['content'] = json.loads(s['content'])
            except (json.JSONDecodeError, TypeError):
                pass
        return jsonify(sections)
    finally:
        db.close()


def get_mermaid_ink_url(mermaid_text):
    # mermaid.ink accepts base64 url-safe encoded string (no zlib compression needed for simple base64 route)
    # It renders to a raster image (JPEG/PNG) which WeasyPrint can display perfectly (unlike Mermaid's SVGs with <foreignObject>)
    
    # Base64 encode the string
    mermaid_text = mermaid_text.strip()
    encoded = base64.urlsafe_b64encode(mermaid_text.encode('utf-8')).decode('ascii')
    
    return f"https://mermaid.ink/img/{encoded}"

@app.route('/api/project/<project_name>/pdf', methods=['GET', 'POST'])
def generate_pdf(project_name):
    try:
        from weasyprint import HTML
        import markdown2
    except ImportError as e:
        return jsonify({'error': f'PDF dependencies not installed: {str(e)}'}), 500
        
    project_name = secure_project_name(project_name)
    if not project_name:
        return jsonify({'error': 'Invalid project name'}), 400
    db_path = os.path.join(PROJECTS_DIR, project_name, 'project.db')
    if not os.path.exists(db_path):
        return jsonify({'error': 'Project not found'}), 404

    # PDF Color Themes
    PDF_THEMES = {
        'sunrise': {
            'bg': '#ffffff', 'text': '#334155', 'h1': '#0f172a', 'h2_bg': '#0f172a', 'h2_text': '#ffffff',
            'accent': '#f97316', 'border': '#e2e8f0', 'card_bg': '#ffffff', 'card_border': '#cbd5e1',
            'key_color': '#64748b', 'val_color': '#1e293b', 'pre_bg': '#0f172a', 'pre_text': '#e2e8f0',
            'code_bg': '#f1f5f9', 'code_text': '#ea580c', 'title_box_bg': '#f8fafc',
            'badge_bg': '#fff7ed', 'badge_text': '#ea580c', 'badge_border': '#fed7aa',
            'toc_dots': '#cbd5e1', 'footer': '#9ca3af', 'note_bg': '#f8fafc', 'note_text': '#94a3b8'
        },
        'ocean': {
            'bg': '#ffffff', 'text': '#334155', 'h1': '#1e3a5f', 'h2_bg': '#1e3a5f', 'h2_text': '#ffffff',
            'accent': '#0ea5e9', 'border': '#e0f2fe', 'card_bg': '#ffffff', 'card_border': '#7dd3fc',
            'key_color': '#0369a1', 'val_color': '#0c4a6e', 'pre_bg': '#0f172a', 'pre_text': '#e0f2fe',
            'code_bg': '#f0f9ff', 'code_text': '#0284c7', 'title_box_bg': '#f0f9ff',
            'badge_bg': '#e0f2fe', 'badge_text': '#0369a1', 'badge_border': '#7dd3fc',
            'toc_dots': '#7dd3fc', 'footer': '#64748b', 'note_bg': '#f0f9ff', 'note_text': '#0284c7'
        },
        'forest': {
            'bg': '#ffffff', 'text': '#334155', 'h1': '#1a3c34', 'h2_bg': '#1a3c34', 'h2_text': '#ffffff',
            'accent': '#22c55e', 'border': '#dcfce7', 'card_bg': '#ffffff', 'card_border': '#86efac',
            'key_color': '#15803d', 'val_color': '#14532d', 'pre_bg': '#052e16', 'pre_text': '#dcfce7',
            'code_bg': '#f0fdf4', 'code_text': '#16a34a', 'title_box_bg': '#f0fdf4',
            'badge_bg': '#dcfce7', 'badge_text': '#15803d', 'badge_border': '#86efac',
            'toc_dots': '#86efac', 'footer': '#64748b', 'note_bg': '#f0fdf4', 'note_text': '#16a34a'
        },
        'royal': {
            'bg': '#ffffff', 'text': '#334155', 'h1': '#2e1065', 'h2_bg': '#2e1065', 'h2_text': '#ffffff',
            'accent': '#a855f7', 'border': '#f3e8ff', 'card_bg': '#ffffff', 'card_border': '#d8b4fe',
            'key_color': '#7e22ce', 'val_color': '#3b0764', 'pre_bg': '#1e1b4b', 'pre_text': '#f3e8ff',
            'code_bg': '#faf5ff', 'code_text': '#9333ea', 'title_box_bg': '#faf5ff',
            'badge_bg': '#f3e8ff', 'badge_text': '#6b21a8', 'badge_border': '#d8b4fe',
            'toc_dots': '#d8b4fe', 'footer': '#64748b', 'note_bg': '#faf5ff', 'note_text': '#9333ea'
        },
        'midnight': {
            'bg': '#0f172a', 'text': '#cbd5e1', 'h1': '#f8fafc', 'h2_bg': '#1e293b', 'h2_text': '#f8fafc',
            'accent': '#f59e0b', 'border': '#334155', 'card_bg': '#1e293b', 'card_border': '#475569',
            'key_color': '#94a3b8', 'val_color': '#f8fafc', 'pre_bg': '#020617', 'pre_text': '#f8fafc',
            'code_bg': '#334155', 'code_text': '#fbbf24', 'title_box_bg': '#1e293b',
            'badge_bg': '#334155', 'badge_text': '#fbbf24', 'badge_border': '#475569',
            'toc_dots': '#475569', 'footer': '#64748b', 'note_bg': '#1e293b', 'note_text': '#94a3b8'
        },
        'obsidian': {
            'bg': '#18181b', 'text': '#d4d4d8', 'h1': '#fafafa', 'h2_bg': '#27272a', 'h2_text': '#fafafa',
            'accent': '#f43f5e', 'border': '#3f3f46', 'card_bg': '#27272a', 'card_border': '#52525b',
            'key_color': '#a1a1aa', 'val_color': '#fafafa', 'pre_bg': '#09090b', 'pre_text': '#fafafa',
            'code_bg': '#3f3f46', 'code_text': '#fb7185', 'title_box_bg': '#27272a',
            'badge_bg': '#3f3f46', 'badge_text': '#fb7185', 'badge_border': '#52525b',
            'toc_dots': '#52525b', 'footer': '#71717a', 'note_bg': '#27272a', 'note_text': '#a1a1aa'
        }
    }

    # Parse skip/placeholder/theme config from request body (POST) or default to empty
    skip_sections = []
    placeholder_sections = []
    theme_name = 'sunrise'
    if request.method == 'POST' and request.json:
        skip_sections = request.json.get('skip_sections', [])
        placeholder_sections = request.json.get('placeholder_sections', [])
        theme_name = request.json.get('theme', 'sunrise')

    t = PDF_THEMES.get(theme_name, PDF_THEMES['sunrise'])

    db = ProjectDB(db_path)
    try:
        sections = db.get_generated_sections()
        info = db.get_repo_info()
        
        project_title = str(info.get('name', project_name))
        
        html_content = f"""
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                @page {{ size: A4; margin: 18mm; background: {t['bg']}; @bottom-center {{ content: counter(page); font-family: -apple-system, sans-serif; font-size: 9pt; color: {t['footer']}; }} }}
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: {t['text']}; line-height: 1.7; font-size: 10.5pt; background-color: {t['bg']}; }}
                h1 {{ color: {t['h1']}; font-size: 28pt; border-bottom: 3px solid {t['accent']}; padding-bottom: 12px; margin-top: 0; font-weight: 800; }}
                h2 {{ color: {t['h2_text']}; background-color: {t['h2_bg']}; font-size: 20pt; margin-top: 40px; page-break-before: always; padding: 16px 24px; border-radius: 8px; border-left: 6px solid {t['accent']}; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); }}
                h3 {{ color: {t['accent']}; font-size: 15pt; margin-top: 24px; margin-bottom: 12px; border-bottom: 1px solid {t['border']}; padding-bottom: 6px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; }}
                h4 {{ color: {t['text']}; font-size: 13pt; margin-top: 16px; margin-bottom: 10px; font-weight: 600; }}
                h5 {{ color: {t['h1']}; font-size: 11.5pt; margin-top: 12px; margin-bottom: 8px; font-weight: 600; }}
                
                .title-page {{ height: 85vh; display: flex; flex-direction: column; justify-content: center; align-items: center; text-align: center; page-break-after: always; }}
                .title-page-inner {{ background: {t['title_box_bg']}; padding: 40px; border-radius: 16px; border: 1px solid {t['border']}; box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1); width: 80%; margin: 0 auto; }}
                .title-page h1 {{ border: none; font-size: 42pt; margin-bottom: 16px; color: {t['h1']}; text-align: center; }}
                .title-page p {{ font-size: 16pt; color: {t['key_color']}; margin-top: 0; }}
                .title-page .badge {{ display: inline-block; background: {t['badge_bg']}; color: {t['badge_text']}; padding: 8px 16px; border-radius: 999px; font-size: 12pt; font-weight: 600; border: 1px solid {t['badge_border']}; margin-top: 24px; }}
                
                pre {{ background: {t['pre_bg']}; color: {t['pre_text']}; padding: 16px; border-radius: 8px; overflow-x: auto; font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; font-size: 9pt; border: 1px solid {t['border']}; white-space: pre-wrap; word-break: break-word; box-shadow: inset 0 2px 4px 0 rgba(0, 0, 0, 0.06); line-height: 1.5; }}
                code {{ background: {t['code_bg']}; color: {t['code_text']}; padding: 3px 6px; border-radius: 4px; font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; font-size: 9pt; font-weight: 500; border: 1px solid {t['border']}; }}
                pre code {{ background: transparent; color: inherit; padding: 0; border: none; }}
                
                ul {{ margin-top: 8px; margin-bottom: 16px; padding-left: 24px; color: {t['text']}; }}
                li {{ margin-bottom: 8px; }}
                li::marker {{ color: {t['accent']}; }}
                
                .item-card {{ background: {t['card_bg']}; border: 1px solid {t['card_border']}; border-radius: 8px; padding: 16px; margin-bottom: 16px; box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06); display: table; width: 100%; box-sizing: border-box; page-break-inside: avoid; border-left: 4px solid {t['accent']}; }}
                .item-row {{ display: table-row; }}
                .item-key {{ font-weight: 600; color: {t['key_color']}; display: table-cell; width: 22%; padding-right: 16px; padding-bottom: 12px; vertical-align: top; word-break: break-word; font-size: 10pt; text-transform: uppercase; letter-spacing: 0.5px; }}
                .item-val {{ display: table-cell; width: 78%; padding-bottom: 12px; vertical-align: top; font-size: 10.5pt; color: {t['val_color']}; }}
                .item-row:last-child .item-key, .item-row:last-child .item-val {{ padding-bottom: 0; }}
                
                p {{ margin-top: 0; margin-bottom: 16px; }}
                .placeholder-note {{ color: {t['note_text']}; font-style: italic; padding: 24px; background: {t['note_bg']}; border-radius: 8px; border: 1px dashed {t['card_border']}; text-align: center; margin-top: 20px; }}
                
                /* Badges */
                .badge-green {{ background: #dcfce7; color: #166534; padding: 2px 8px; border-radius: 4px; font-size: 8.5pt; font-weight: 700; border: 1px solid #bbf7d0; display: inline-block; }}
                .badge-orange {{ background: #ffedd5; color: #c2410c; padding: 2px 8px; border-radius: 4px; font-size: 8.5pt; font-weight: 700; border: 1px solid #fed7aa; display: inline-block; }}
                .badge-red {{ background: #fee2e2; color: #991b1b; padding: 2px 8px; border-radius: 4px; font-size: 8.5pt; font-weight: 700; border: 1px solid #fecaca; display: inline-block; }}
                .badge-gray {{ background: #f1f5f9; color: #475569; padding: 2px 8px; border-radius: 4px; font-size: 8.5pt; font-weight: 700; border: 1px solid #e2e8f0; display: inline-block; }}
                .badge-purple {{ background: #f3e8ff; color: #6b21a8; padding: 2px 8px; border-radius: 4px; font-size: 8.5pt; font-weight: 700; border: 1px solid #e9d5ff; display: inline-block; }}
                .badge-blue {{ background: #dbeafe; color: #1e40af; padding: 2px 8px; border-radius: 4px; font-size: 8.5pt; font-weight: 700; border: 1px solid #bfdbfe; display: inline-block; }}
                
                /* Callout Boxes */
                .callout-success {{ background: #f0fdf4; border-left: 4px solid #22c55e; padding: 16px; border-radius: 0 8px 8px 0; margin-bottom: 16px; color: #166534; }}
                .callout-warning {{ background: #fffbeb; border-left: 4px solid #f59e0b; padding: 16px; border-radius: 0 8px 8px 0; margin-bottom: 16px; color: #b45309; }}
                .callout-danger {{ background: #fef2f2; border-left: 4px solid #ef4444; padding: 16px; border-radius: 0 8px 8px 0; margin-bottom: 16px; color: #b91c1c; }}
            </style>
        </head>
        <body>
            <div class="title-page">
                <div class="title-page-inner">
                    <h1>{_escape_html(project_title)}</h1>
                    <p>Technical Documentation & Interview Guide</p>
                    <div class="badge">Generated by BuiltByMe</div>
                </div>
            </div>
            
            <!-- Table of Contents -->
            <h2>Table of Contents</h2>
            <ul style="list-style-type: none; padding-left: 0;">
        """
        
        # Build TOC
        for s in sections:
            if s['section_id'] not in skip_sections:
                html_content += f"<li style='margin-bottom: 12px; font-size: 12pt; border-bottom: 1px dotted {t['toc_dots']}; padding-bottom: 4px;'><strong style='color: {t['accent']};'>Section {s['section_id']}:</strong> {_escape_html(s['name'])}</li>\n"
        html_content += "</ul>\n"
        
        for s in sections:
            sid = s['section_id']
            
            # Skip sections marked as skip — exclude entirely
            if sid in skip_sections:
                continue
            
            html_content += f"<h2>Section {sid}: {_escape_html(s['name'])}</h2>\n"
            
            # Placeholder sections — heading only, blank content
            if sid in placeholder_sections:
                html_content += "<div class='placeholder-note'><p style='margin:0; font-size: 14pt;'>✍️</p><p style='margin-top:8px; margin-bottom:0;'>This section is intentionally left blank for manual completion.</p></div>\n"
                continue
            
            content_dict = None
            try:
                content_dict = json.loads(s['content'])
            except (json.JSONDecodeError, TypeError):
                pass
                
            if isinstance(content_dict, dict):
                if sid == 3:
                    # === Section 3: Architecture & Module Map ===
                    # Folder Tree
                    folder_tree = content_dict.get('folder_tree', '')
                    if folder_tree:
                        html_content += "<h3>Folder Structure</h3>\n"
                        html_content += f"<pre style='background:#f8f9fa; padding:16px; border-radius:8px; font-size:10pt; line-height:1.6; border:1px solid #e5e7eb;'>{str(folder_tree)}</pre>\n"
                    
                    # Architecture Diagram (Mermaid)
                    diagram = content_dict.get('architecture_diagram', '')
                    if diagram:
                        html_content += "<h3>Architecture Diagram</h3>\n"
                        try:
                            kroki_url = get_mermaid_ink_url(diagram)
                            html_content += f"<div style='text-align: center; margin: 20px 0;'><img src='{kroki_url}' style='max-width: 100%; max-height: 500px;' /></div>\n"
                        except Exception as e:
                            html_content += f"<p style='color: red;'>Failed to render diagram: {str(e)}</p>"
                            html_content += f"<pre style='background:#1e1e2e; color:#cdd6f4; padding:20px; border-radius:8px; font-size:10pt; line-height:1.6; border:2px solid #f97316;'>{str(diagram)}</pre>\n"
                    
                    # Architecture Style
                    style = content_dict.get('architecture_style', '')
                    if style:
                        html_content += "<h3>Architecture Style</h3>\n"
                        html_content += f"<p>{markdown2.markdown(str(style)).replace('<p>','').replace('</p>','')}</p>\n"
                    
                    # Layer Breakdown
                    layers = content_dict.get('layer_breakdown', '')
                    if layers:
                        html_content += "<h3>Layer Breakdown</h3>\n"
                        html_content += f"<p>{markdown2.markdown(str(layers)).replace('<p>','').replace('</p>','')}</p>\n"
                    
                    # Modules
                    modules = content_dict.get('modules', [])
                    if modules:
                        html_content += "<h3>Modules</h3>\n"
                        for mod in modules:
                            html_content += "<div class='item-card'>"
                            html_content += f"<div class='item-row'><div class='item-key'>Module</div><div class='item-val'><strong>{str(mod.get('folder_or_file', ''))}</strong></div></div>"
                            html_content += f"<div class='item-row'><div class='item-key'>Purpose</div><div class='item-val'>{str(mod.get('purpose', ''))}</div></div>"
                            key_files = mod.get('key_files', [])
                            if key_files:
                                html_content += f"<div class='item-row'><div class='item-key'>Key Files</div><div class='item-val'>{'<br>'.join(str(f) for f in key_files)}</div></div>"
                            html_content += "</div>\n"
                    
                    # Entry Points
                    entries = content_dict.get('entry_points', [])
                    if entries:
                        html_content += "<h3>Entry Points</h3>\n<ul>\n"
                        for ep in entries:
                            html_content += f"<li>{str(ep)}</li>\n"
                        html_content += "</ul>\n"
                    
                    # Data Flow (text steps)
                    flow = content_dict.get('data_flow', [])
                    if flow:
                        html_content += "<h3>Data Flow</h3>\n"
                        for step in flow:
                            html_content += "<div class='item-card'>"
                            html_content += f"<div class='item-row'><div class='item-key'>Step {step.get('step_number', '')}</div><div class='item-val'>{str(step.get('description', ''))}</div></div>"
                            mods = step.get('modules_involved', [])
                            if mods:
                                html_content += f"<div class='item-row'><div class='item-key'>Modules</div><div class='item-val'>{', '.join(str(m) for m in mods)}</div></div>"
                            html_content += "</div>\n"
                    
                    # Data Flow Diagram (Mermaid)
                    flow_diagram = content_dict.get('data_flow_diagram', '')
                    if flow_diagram:
                        html_content += "<h3>Data Flow Diagram</h3>\n"
                        try:
                            kroki_url = get_mermaid_ink_url(flow_diagram)
                            html_content += f"<div style='text-align: center; margin: 20px 0;'><img src='{kroki_url}' style='max-width: 100%; max-height: 500px;' /></div>\n"
                        except Exception as e:
                            html_content += f"<p style='color: red;'>Failed to render diagram: {str(e)}</p>"
                            html_content += f"<pre style='background:#1e1e2e; color:#cdd6f4; padding:20px; border-radius:8px; font-size:10pt; line-height:1.6; border:2px solid #f97316;'>{str(flow_diagram)}</pre>\n"

                
                elif sid == 4:
                    # === Section 4: Environment & Secrets ===
                    # Environment Variables
                    env_vars = content_dict.get('env_variables', [])
                    if env_vars:
                        html_content += "<h3>Environment Variables</h3>\n"
                        for ev in env_vars:
                            html_content += "<div class='item-card'>"
                            html_content += f"<div class='item-row'><div class='item-key'>Variable</div><div class='item-val'><code>{str(ev.get('name', ''))}</code></div></div>"
                            html_content += f"<div class='item-row'><div class='item-key'>Purpose</div><div class='item-val'>{str(ev.get('purpose', ''))}</div></div>"
                            html_content += f"<div class='item-row'><div class='item-key'>Required</div><div class='item-val'>{'Yes' if ev.get('required') else 'No'}</div></div>"
                            html_content += f"<div class='item-row'><div class='item-key'>Example</div><div class='item-val'><code>{str(ev.get('example_value', ''))}</code></div></div>"
                            html_content += f"<div class='item-row'><div class='item-key'>Used In</div><div class='item-val'>{str(ev.get('where_used', ''))}</div></div>"
                            html_content += "</div>\n"
                    else:
                        html_content += "<h3>Environment Variables</h3>\n<p>No environment variables detected in this project.</p>\n"
                    
                    # Config Files
                    configs = content_dict.get('config_files', [])
                    if configs:
                        html_content += "<h3>Configuration Files</h3>\n"
                        for cf in configs:
                            html_content += "<div class='item-card'>"
                            html_content += f"<div class='item-row'><div class='item-key'>File</div><div class='item-val'><code>{str(cf.get('file_path', ''))}</code></div></div>"
                            html_content += f"<div class='item-row'><div class='item-key'>Purpose</div><div class='item-val'>{str(cf.get('purpose', ''))}</div></div>"
                            html_content += f"<div class='item-row'><div class='item-key'>Format</div><div class='item-val'>{str(cf.get('format', ''))}</div></div>"
                            settings = cf.get('key_settings', [])
                            if settings:
                                html_content += f"<div class='item-row'><div class='item-key'>Key Settings</div><div class='item-val'>{'<br>'.join(str(s) for s in settings)}</div></div>"
                            html_content += "</div>\n"
                    
                    # Secrets
                    secrets = content_dict.get('secrets', [])
                    if secrets:
                        html_content += "<h3>Secrets Management</h3>\n"
                        for sec_item in secrets:
                            html_content += "<div class='item-card'>"
                            html_content += f"<div class='item-row'><div class='item-key'>Secret</div><div class='item-val'><strong>{str(sec_item.get('name', ''))}</strong></div></div>"
                            html_content += f"<div class='item-row'><div class='item-key'>Storage</div><div class='item-val'>{str(sec_item.get('how_stored', ''))}</div></div>"
                            html_content += f"<div class='item-row'><div class='item-key'>Access</div><div class='item-val'>{str(sec_item.get('how_accessed', ''))}</div></div>"
                            html_content += f"<div class='item-row'><div class='item-key'>Rotation</div><div class='item-val'>{str(sec_item.get('rotation_strategy', ''))}</div></div>"
                            html_content += "</div>\n"
                    
                    # Dev vs Prod
                    dvp = content_dict.get('dev_vs_prod', '')
                    if dvp:
                        html_content += "<h3>Development vs Production</h3>\n"
                        html_content += f"<p>{markdown2.markdown(str(dvp)).replace('<p>','').replace('</p>','')}</p>\n"
                    
                    # Setup Steps
                    steps = content_dict.get('setup_steps', [])
                    if steps:
                        html_content += "<h3>Setup Instructions</h3>\n<ol>\n"
                        for step in steps:
                            html_content += f"<li>{str(step)}</li>\n"
                        html_content += "</ol>\n"
                    
                    # Security
                    security = content_dict.get('security_considerations', '')
                    if security:
                        html_content += "<h3>Security Considerations</h3>\n"
                        html_content += f"<p>{markdown2.markdown(str(security)).replace('<p>','').replace('</p>','')}</p>\n"
                
                elif sid == 5:
                    # === Section 5: Core Functions & Classes ===
                    summary = content_dict.get('summary', '')
                    if summary:
                        html_content += "<h3>Summary</h3>\n"
                        html_content += f"<p>{markdown2.markdown(str(summary)).replace('<p>','').replace('</p>','')}</p>\n"
                    
                    interaction_map = content_dict.get('interaction_map', '')
                    if interaction_map:
                        html_content += "<h3>Interaction Map</h3>\n"
                        html_content += f"<p>{markdown2.markdown(str(interaction_map)).replace('<p>','').replace('</p>','')}</p>\n"
                    
                    core_items = content_dict.get('core_items', [])
                    if core_items:
                        html_content += "<h3>Core Functions & Classes</h3>\n"
                        for item in core_items:
                            html_content += "<div class='item-card'>"
                            kind_val = str(item.get('kind', 'function')).lower()
                            if kind_val in ['class', 'struct']:
                                badge_class = 'badge-blue'
                            elif kind_val in ['method', 'interface']:
                                badge_class = 'badge-purple'
                            else:
                                badge_class = 'badge-orange'
                            kind_badge = kind_val.upper()
                            html_content += f"<div class='item-row'><div class='item-key'>Name</div><div class='item-val'><strong style='font-size:12pt; color:#0f172a;'>{str(item.get('name', ''))}</strong> &nbsp;<span class='{badge_class}'>{kind_badge}</span></div></div>"
                            html_content += f"<div class='item-row'><div class='item-key'>File</div><div class='item-val'><code>{str(item.get('file_location', ''))}</code> ({str(item.get('line_range', ''))})</div></div>"
                            html_content += f"<div class='item-row'><div class='item-key'>Purpose</div><div class='item-val'>{str(item.get('purpose', ''))}</div></div>"
                            html_content += f"<div class='item-row'><div class='item-key'>Inputs</div><div class='item-val'>{str(item.get('inputs', ''))}</div></div>"
                            html_content += f"<div class='item-row'><div class='item-key'>Outputs</div><div class='item-val'>{str(item.get('outputs', ''))}</div></div>"
                            html_content += f"<div class='item-row'><div class='item-key'>Why Important</div><div class='item-val'>{str(item.get('why_important', ''))}</div></div>"
                            html_content += f"<div class='item-row'><div class='item-key'>Called By</div><div class='item-val'>{str(item.get('called_by', ''))}</div></div>"
                            complexity = item.get('complexity_note', '')
                            if complexity:
                                html_content += f"<div class='item-row'><div class='item-key'>Complexity</div><div class='item-val'><em>{str(complexity)}</em></div></div>"
                            html_content += "</div>\n"

                elif sid == 6 and 'deep_dives' in content_dict:
                    dives = content_dict.get('deep_dives', [])
                    if not dives:
                        html_content += "<p>No deep dives generated yet.</p>\n"
                    for dive in dives:
                        fw_name = dive.get('framework_name', 'Unknown Framework')
                        html_content += f"<h3>Framework: {fw_name}</h3>\n"
                        category = dive.get('category', '')
                        if category:
                            html_content += f"<p><strong>Category:</strong> {category}</p>\n"
                        
                        # One-liner
                        one_liner = dive.get('one_liner', '')
                        if one_liner:
                            html_content += f"<div class='item-card'><div class='item-row'><div class='item-key'>What Is It</div><div class='item-val'><em>{_escape_html(str(one_liner))}</em></div></div></div>\n"
                        
                        # How It Works Internally
                        internals = dive.get('how_it_works_internally', '')
                        if internals:
                            html_content += "<h4>How It Works Internally</h4>\n"
                            html_content += f"<p>{markdown2.markdown(str(internals)).replace('<p>','').replace('</p>','')}</p>\n"
                        
                        for section_key in ['basics', 'directly_used_concepts', 'indirect_concepts']:
                            concepts = dive.get(section_key, [])
                            if concepts:
                                section_title = section_key.replace('_', ' ').title()
                                html_content += f"<h4>{section_title} ({len(concepts)})</h4>\n"
                                for concept in concepts:
                                    html_content += "<div class='item-card'>"
                                    c_title = concept.get('title', '')
                                    c_exp = concept.get('explanation', '')
                                    c_analogy = concept.get('real_world_analogy', '')
                                    c_why = concept.get('why_it_matters', '')
                                    c_code = concept.get('code_snippet', '')
                                    html_content += f"<h5>{c_title}</h5>\n"
                                    if c_exp:
                                        html_content += f"<p>{markdown2.markdown(str(c_exp)).replace('<p>','').replace('</p>','')}</p>\n"
                                    if c_analogy:
                                        html_content += f"<p style='font-style:italic;color:#8b5cf6;margin-top:4px;'>💡 {_escape_html(str(c_analogy))}</p>\n"
                                    if c_why:
                                        html_content += f"<p style='font-style:italic;color:#6b7280;margin-top:4px;'><strong>Interview Angle:</strong> {_escape_html(str(c_why))}</p>\n"
                                    if c_code:
                                        html_content += f"<pre><code>{_escape_html(str(c_code))}</code></pre>\n"
                                    html_content += "</div>\n"
                        
                        # Common Pitfalls
                        pitfalls = dive.get('common_pitfalls', [])
                        if pitfalls:
                            html_content += "<h4>Common Pitfalls</h4>\n<ul>\n"
                            for p in pitfalls:
                                html_content += f"<li>{_escape_html(str(p))}</li>\n"
                            html_content += "</ul>\n"
                        
                        # Interview Quickfire
                        quickfire = dive.get('interview_quickfire', [])
                        if quickfire:
                            html_content += "<h4>Interview Quickfire</h4>\n"
                            for qa in quickfire:
                                html_content += f"<div class='item-card'><p>{_escape_html(str(qa))}</p></div>\n"
                        
                        # Vs Alternatives
                        vs_alts = dive.get('vs_alternatives', '')
                        if vs_alts:
                            html_content += "<h4>Vs Alternatives</h4>\n"
                            html_content += f"<p>{markdown2.markdown(str(vs_alts)).replace('<p>','').replace('</p>','')}</p>\n"


                elif sid == 7:
                    # === Section 7: Design Decisions ===
                    arch_pattern = content_dict.get('architectural_pattern', '')
                    if arch_pattern:
                        html_content += "<h3>Architectural Pattern</h3>\n"
                        html_content += f"<p>{markdown2.markdown(str(arch_pattern)).replace('<p>','').replace('</p>','')}</p>\n"
                    
                    principles = content_dict.get('design_principles', [])
                    if principles:
                        html_content += "<h3>Guiding Principles</h3>\n<ul>\n"
                        for p in principles:
                            html_content += f"<li>{str(p)}</li>\n"
                        html_content += "</ul>\n"
                    
                    decisions = content_dict.get('decisions', [])
                    if decisions:
                        html_content += "<h3>Key Decisions</h3>\n"
                        for dec in decisions:
                            html_content += "<div class='item-card'>"
                            html_content += f"<div class='item-row'><div class='item-key'>Decision</div><div class='item-val'><strong>{str(dec.get('title', ''))}</strong></div></div>"
                            html_content += f"<div class='item-row'><div class='item-key'>Context</div><div class='item-val'>{str(dec.get('context', ''))}</div></div>"
                            html_content += f"<div class='item-row'><div class='item-key'>Decision</div><div class='item-val'>{str(dec.get('decision', ''))}</div></div>"
                            alts = dec.get('alternatives_considered', [])
                            if alts:
                                html_content += f"<div class='item-row'><div class='item-key'>Alternatives</div><div class='item-val'>{', '.join(str(a) for a in alts)}</div></div>"
                            html_content += f"<div class='item-row'><div class='item-key'>Trade-offs</div><div class='item-val'>{str(dec.get('trade_offs', ''))}</div></div>"
                            html_content += f"<div class='item-row'><div class='item-key'>Outcome</div><div class='item-val'>{str(dec.get('outcome', ''))}</div></div>"
                            html_content += f"<div class='item-row'><div class='item-key'>Interview Angle</div><div class='item-val'><em>{str(dec.get('interview_angle', ''))}</em></div></div>"
                            html_content += "</div>\n"

                elif sid == 8:
                    # === Section 8: Failure Log & Learnings ===
                    biggest = content_dict.get('biggest_lesson', '')
                    if biggest:
                        html_content += "<h3>Biggest Lesson</h3>\n"
                        html_content += f"<p>{markdown2.markdown(str(biggest)).replace('<p>','').replace('</p>','')}</p>\n"
                    
                    diff = content_dict.get('what_id_do_differently', '')
                    if diff:
                        html_content += "<h3>What I'd Do Differently</h3>\n"
                        html_content += f"<p>{markdown2.markdown(str(diff)).replace('<p>','').replace('</p>','')}</p>\n"
                    
                    growth = content_dict.get('growth_areas', [])
                    if growth:
                        html_content += "<h3>Growth Areas</h3>\n<ul>\n"
                        for g in growth:
                            html_content += f"<li>{str(g)}</li>\n"
                        html_content += "</ul>\n"
                    
                    failures = content_dict.get('failures', [])
                    if failures:
                        html_content += "<h3>Failure Log</h3>\n"
                        for fail in failures:
                            category_badge = str(fail.get('category', '')).upper()
                            html_content += "<div class='item-card'>"
                            html_content += f"<div class='item-row'><div class='item-key'>Problem</div><div class='item-val'><strong>{str(fail.get('title', ''))}</strong> &nbsp;<span class='badge-red'>{category_badge}</span></div></div>"
                            html_content += f"<div class='item-row'><div class='item-key'>What Happened</div><div class='item-val'>{str(fail.get('what_happened', ''))}</div></div>"
                            html_content += f"<div class='item-row'><div class='item-key'>Initial Approach</div><div class='item-val'>{str(fail.get('initial_approach', ''))}</div></div>"
                            html_content += f"<div class='item-row'><div class='item-key'>Root Cause</div><div class='item-val'>{str(fail.get('root_cause', ''))}</div></div>"
                            html_content += f"<div class='item-row'><div class='item-key'>Solution</div><div class='item-val'>{str(fail.get('solution', ''))}</div></div>"
                            html_content += f"<div class='item-row'><div class='item-key'>Lesson Learned</div><div class='item-val'><em>{str(fail.get('lesson_learned', ''))}</em></div></div>"
                            html_content += "</div>\n"

                elif sid == 9:
                    # === Section 9: APIs & Interfaces ===
                    overview = content_dict.get('api_overview', '')
                    if overview:
                        html_content += "<h3>API Overview</h3>\n"
                        html_content += f"<p>{markdown2.markdown(str(overview)).replace('<p>','').replace('</p>','')}</p>\n"
                    
                    # Endpoints
                    endpoints = content_dict.get('endpoints', [])
                    if endpoints:
                        html_content += "<h3>API Endpoints</h3>\n"
                        for ep in endpoints:
                            method = str(ep.get('method', 'GET')).upper()
                            if method == 'GET':
                                m_class = 'badge-blue'
                            elif method == 'POST':
                                m_class = 'badge-green'
                            elif method in ('PUT', 'PATCH'):
                                m_class = 'badge-orange'
                            elif method == 'DELETE':
                                m_class = 'badge-red'
                            else:
                                m_class = 'badge-gray'
                            
                            html_content += "<div class='item-card'>"
                            html_content += f"<div class='item-row'><div class='item-key'>Endpoint</div><div class='item-val'><span class='{m_class}'>{method}</span> &nbsp;<code>{str(ep.get('path', ''))}</code></div></div>"
                            html_content += f"<div class='item-row'><div class='item-key'>Purpose</div><div class='item-val'>{str(ep.get('purpose', ''))}</div></div>"
                            html_content += f"<div class='item-row'><div class='item-key'>Request Body</div><div class='item-val'><code>{str(ep.get('request_body', ''))}</code></div></div>"
                            html_content += f"<div class='item-row'><div class='item-key'>Response</div><div class='item-val'><code>{str(ep.get('response_format', ''))}</code></div></div>"
                            html_content += f"<div class='item-row'><div class='item-key'>Auth / Errors</div><div class='item-val'><strong>Auth:</strong> {str(ep.get('auth_required', ''))}<br><strong>Errors:</strong> {str(ep.get('error_handling', ''))}</div></div>"
                            html_content += "</div>\n"
                    
                    # Design Patterns
                    patterns = content_dict.get('design_patterns', [])
                    if patterns:
                        html_content += "<h3>API Design Patterns</h3>\n"
                        for p in patterns:
                            html_content += "<div class='item-card'>"
                            html_content += f"<div class='item-row'><div class='item-key'>Pattern</div><div class='item-val'><strong>{str(p.get('pattern', ''))}</strong></div></div>"
                            html_content += f"<div class='item-row'><div class='item-key'>Description</div><div class='item-val'>{str(p.get('description', ''))}</div></div>"
                            examples = p.get('examples', [])
                            if examples:
                                html_content += f"<div class='item-row'><div class='item-key'>Examples</div><div class='item-val'>{'<br>'.join('• ' + str(ex) for ex in examples)}</div></div>"
                            html_content += "</div>\n"
                    
                    # Strategies
                    strategies = [
                        ('Error Strategy', content_dict.get('error_strategy', '')),
                        ('Rate Limiting', content_dict.get('rate_limiting', '')),
                        ('Versioning', content_dict.get('versioning', ''))
                    ]
                    for title, content in strategies:
                        if content:
                            html_content += f"<h3>{title}</h3>\n"
                            html_content += f"<p>{markdown2.markdown(str(content)).replace('<p>','').replace('</p>','')}</p>\n"
                    
                    tips = content_dict.get('interview_tips', '')
                    if tips:
                        html_content += "<h3>Interview Tips</h3>\n"
                        html_content += f"<div class='item-card' style='background:#f0fdf4;border-left:4px solid #22c55e;'><p><em>{markdown2.markdown(str(tips)).replace('<p>','').replace('</p>','')}</em></p></div>\n"

                elif sid == 10:
                    # === Section 10: Data Models & Storage ===
                    overview = content_dict.get('data_overview', '')
                    if overview:
                        html_content += "<h3>Data & Storage Overview</h3>\n"
                        html_content += f"<p>{markdown2.markdown(str(overview)).replace('<p>','').replace('</p>','')}</p>\n"
                    
                    # ER Diagram
                    diagram = content_dict.get('schema_diagram', '')
                    if diagram:
                        html_content += "<h3>Schema Diagram</h3>\n"
                        try:
                            kroki_url = get_mermaid_ink_url(diagram)
                            html_content += f"<div style='text-align: center; margin: 20px 0;'><img src='{kroki_url}' style='max-width: 100%; max-height: 500px;' /></div>\n"
                        except Exception as e:
                            html_content += f"<p style='color: red;'>Failed to render diagram: {str(e)}</p>"
                            html_content += f"<pre style='background:#1e1e2e; color:#cdd6f4; padding:20px; border-radius:8px; font-size:10pt; line-height:1.6; border:2px solid #f97316;'>{str(diagram)}</pre>\n"
                    
                    # Models
                    models = content_dict.get('models', [])
                    if models:
                        html_content += "<h3>Data Models</h3>\n"
                        for m in models:
                            html_content += "<div class='item-card'>"
                            html_content += f"<div class='item-row'><div class='item-key'>Model</div><div class='item-val'><strong>{str(m.get('name', ''))}</strong> <span style='background:#475569;color:#fff;padding:1px 6px;border-radius:3px;font-size:9pt;'>{str(m.get('storage_type', ''))}</span></div></div>"
                            html_content += f"<div class='item-row'><div class='item-key'>Purpose</div><div class='item-val'>{str(m.get('purpose', ''))}</div></div>"
                            fields = m.get('fields', [])
                            if fields:
                                html_content += f"<div class='item-row'><div class='item-key'>Fields</div><div class='item-val'>{'<br>'.join('• <code>' + str(f).split(' — ')[0] + '</code>' + (' — ' + str(f).split(' — ')[1] if ' — ' in str(f) else '') for f in fields)}</div></div>"
                            html_content += f"<div class='item-row'><div class='item-key'>Relationships</div><div class='item-val'>{str(m.get('relationships', ''))}</div></div>"
                            html_content += f"<div class='item-row'><div class='item-key'>Access Patterns</div><div class='item-val'>{str(m.get('access_patterns', ''))}</div></div>"
                            html_content += "</div>\n"
                    
                    # Storage Decisions
                    decisions = content_dict.get('storage_decisions', [])
                    if decisions:
                        html_content += "<h3>Key Storage Decisions</h3>\n"
                        for d in decisions:
                            html_content += "<div class='item-card'>"
                            html_content += f"<div class='item-row'><div class='item-key'>Decision</div><div class='item-val'><strong>{str(d.get('decision', ''))}</strong></div></div>"
                            html_content += f"<div class='item-row'><div class='item-key'>Reasoning</div><div class='item-val'>{str(d.get('reasoning', ''))}</div></div>"
                            html_content += f"<div class='item-row'><div class='item-key'>Trade-offs</div><div class='item-val'>{str(d.get('trade_offs', ''))}</div></div>"
                            html_content += f"<div class='item-row'><div class='item-key'>Production Alt.</div><div class='item-val' style='color:#0284c7;'>{str(d.get('production_alternative', ''))}</div></div>"
                            html_content += "</div>\n"
                    
                    strategies = [
                        ('Indexing Strategy', content_dict.get('indexing_strategy', '')),
                        ('Data Lifecycle', content_dict.get('data_lifecycle', '')),
                        ('Migration Strategy', content_dict.get('migration_strategy', ''))
                    ]
                    for title, content in strategies:
                        if content:
                            html_content += f"<h3>{title}</h3>\n"
                            html_content += f"<p>{markdown2.markdown(str(content)).replace('<p>','').replace('</p>','')}</p>\n"

                elif sid == 11:
                    # === Section 11: Testing Strategy ===
                    overview = content_dict.get('testing_overview', '')
                    if overview:
                        html_content += "<h3>Testing Overview</h3>\n"
                        html_content += f"<p>{markdown2.markdown(str(overview)).replace('<p>','').replace('</p>','')}</p>\n"
                    
                    current = content_dict.get('current_tests', [])
                    if current:
                        html_content += "<h3>Current Test Coverage</h3>\n<ul>\n"
                        for c in current:
                            html_content += f"<li>{str(c)}</li>\n"
                        html_content += "</ul>\n"
                    
                    # Proposed Test Plan
                    plan = content_dict.get('proposed_test_plan', [])
                    if plan:
                        html_content += "<h3>Proposed Test Plan</h3>\n"
                        for t in plan:
                            prio = str(t.get('priority', 'Medium')).upper()
                            if prio == 'HIGH':
                                p_class = 'badge-red'
                            elif prio == 'LOW':
                                p_class = 'badge-blue'
                            else:
                                p_class = 'badge-orange'
                            
                            t_type = str(t.get('test_type', 'unit')).upper()
                            
                            html_content += "<div class='item-card'>"
                            html_content += f"<div class='item-row'><div class='item-key'>Test Case</div><div class='item-val'><strong>{str(t.get('name', ''))}</strong> &nbsp;<span class='badge-gray'>{t_type}</span> &nbsp;<span class='{p_class}'>{prio} PRIORITY</span></div></div>"
                            html_content += f"<div class='item-row'><div class='item-key'>What it tests</div><div class='item-val'>{str(t.get('what_it_tests', ''))}</div></div>"
                            html_content += f"<div class='item-row'><div class='item-key'>Implementation</div><div class='item-val'><code>{str(t.get('how_to_implement', ''))}</code></div></div>"
                            html_content += "</div>\n"
                    
                    # Frameworks
                    frameworks = content_dict.get('framework_choices', [])
                    if frameworks:
                        html_content += "<h3>Framework Choices</h3>\n"
                        for f in frameworks:
                            html_content += "<div class='item-card'>"
                            html_content += f"<div class='item-row'><div class='item-key'>Framework</div><div class='item-val'><strong>{str(f.get('framework', ''))}</strong></div></div>"
                            html_content += f"<div class='item-row'><div class='item-key'>Why Chosen</div><div class='item-val'>{str(f.get('why_chosen', ''))}</div></div>"
                            features = f.get('key_features_used', [])
                            if features:
                                html_content += f"<div class='item-row'><div class='item-key'>Key Features</div><div class='item-val'>{'<br>'.join('• ' + str(feat) for feat in features)}</div></div>"
                            html_content += "</div>\n"
                    
                    strategies = [
                        ('Mocking Strategy', content_dict.get('mocking_strategy', '')),
                        ('CI Integration', content_dict.get('ci_integration', '')),
                        ('Testing Philosophy', content_dict.get('testing_philosophy', ''))
                    ]
                    for title, content in strategies:
                        if content:
                            html_content += f"<h3>{title}</h3>\n"
                            html_content += f"<p>{markdown2.markdown(str(content)).replace('<p>','').replace('</p>','')}</p>\n"
                    
                    gaps = content_dict.get('coverage_gaps', [])
                    if gaps:
                        html_content += "<h3>Known Coverage Gaps (Honest Assessment)</h3>\n<ul>\n"
                        for g in gaps:
                            html_content += f"<li>{str(g)}</li>\n"
                        html_content += "</ul>\n"

                elif sid == 12:
                    # === Section 12: Scalability & Production ===
                    overview = content_dict.get('scalability_overview', '')
                    if overview:
                        html_content += "<h3>Scalability Overview</h3>\n"
                        html_content += f"<p>{markdown2.markdown(str(overview)).replace('<p>','').replace('</p>','')}</p>\n"
                    
                    # Bottlenecks
                    bottlenecks = content_dict.get('bottlenecks', [])
                    if bottlenecks:
                        html_content += "<h3>Identified Bottlenecks</h3>\n"
                        for b in bottlenecks:
                            html_content += "<div class='item-card'>"
                            html_content += f"<div class='item-row'><div class='item-key'>Bottleneck</div><div class='item-val'><strong>{str(b.get('area', ''))}</strong></div></div>"
                            html_content += f"<div class='item-row'><div class='item-key'>Description</div><div class='item-val'>{str(b.get('description', ''))}</div></div>"
                            html_content += f"<div class='item-row'><div class='item-key'>Impact</div><div class='item-val' style='color:#ef4444;'>{str(b.get('impact', ''))}</div></div>"
                            html_content += f"<div class='item-row'><div class='item-key'>Solution</div><div class='item-val' style='color:#22c55e;'>{str(b.get('solution', ''))}</div></div>"
                            html_content += "</div>\n"
                    
                    # Code Smells
                    smells = content_dict.get('code_smells', [])
                    if smells:
                        html_content += "<h3>Technical Debt & Code Smells</h3>\n"
                        for s in smells:
                            sev = str(s.get('severity', 'Medium')).upper()
                            if sev == 'HIGH':
                                s_class = 'badge-red'
                            elif sev == 'LOW':
                                s_class = 'badge-blue'
                            else:
                                s_class = 'badge-orange'
                                
                            html_content += "<div class='item-card'>"
                            html_content += f"<div class='item-row'><div class='item-key'>Code Smell</div><div class='item-val'><strong>{str(s.get('smell', ''))}</strong> &nbsp;<span class='{s_class}'>{sev} SEVERITY</span></div></div>"
                            html_content += f"<div class='item-row'><div class='item-key'>Location</div><div class='item-val'><code>{str(s.get('location', ''))}</code></div></div>"
                            html_content += f"<div class='item-row'><div class='item-key'>Proposed Fix</div><div class='item-val'>{str(s.get('fix', ''))}</div></div>"
                            html_content += "</div>\n"
                    
                    # Security Audit
                    sec = content_dict.get('security_audit', [])
                    if sec:
                        html_content += "<h3>Security Audit</h3>\n"
                        for s in sec:
                            html_content += "<div class='item-card'>"
                            html_content += f"<div class='item-row'><div class='item-key'>Security Area</div><div class='item-val'><strong>{str(s.get('area', ''))}</strong></div></div>"
                            html_content += f"<div class='item-row'><div class='item-key'>Current State</div><div class='item-val'>{str(s.get('current_state', ''))}</div></div>"
                            html_content += f"<div class='item-row'><div class='item-key'>Recommendation</div><div class='item-val' style='color:#0284c7;'>{str(s.get('recommendation', ''))}</div></div>"
                            html_content += "</div>\n"
                    
                    strategies = [
                        ('Scaling Strategy (100+ Concurrent Users)', content_dict.get('scaling_strategy', '')),
                        ('Ideal Production Architecture', content_dict.get('production_architecture', ''))
                    ]
                    for title, content in strategies:
                        if content:
                            html_content += f"<h3>{title}</h3>\n"
                            html_content += f"<p>{markdown2.markdown(str(content)).replace('<p>','').replace('</p>','')}</p>\n"
                    
                    for title, key in [('Performance Optimizations', 'performance_optimizations'), ('Monitoring Gaps', 'monitoring_gaps')]:
                        items = content_dict.get(key, [])
                        if items:
                            html_content += f"<h3>{title}</h3>\n<ul>\n"
                            for i in items:
                                html_content += f"<li>{str(i)}</li>\n"
                            html_content += "</ul>\n"

                elif sid == 13:
                    # === Section 13: Deployment & Infra ===
                    overview = content_dict.get('deployment_overview', '')
                    if overview:
                        html_content += "<h3>Deployment Overview</h3>\n"
                        html_content += f"<p>{markdown2.markdown(str(overview)).replace('<p>','').replace('</p>','')}</p>\n"
                    
                    # Environments
                    envs = content_dict.get('environments', [])
                    if envs:
                        html_content += "<h3>Deployment Environments</h3>\n"
                        for env in envs:
                            html_content += "<div class='item-card'>"
                            html_content += f"<div class='item-row'><div class='item-key'>Environment</div><div class='item-val'><strong>{str(env.get('name', ''))}</strong></div></div>"
                            html_content += f"<div class='item-row'><div class='item-key'>Description</div><div class='item-val'>{str(env.get('description', ''))}</div></div>"
                            html_content += f"<div class='item-row'><div class='item-key'>How to Run</div><div class='item-val'>{str(env.get('how_to_run', ''))}</div></div>"
                            html_content += f"<div class='item-row'><div class='item-key'>Differences</div><div class='item-val'>{str(env.get('differences', ''))}</div></div>"
                            html_content += "</div>\n"
                    
                    # Infra Components
                    infra = content_dict.get('infra_components', [])
                    if infra:
                        html_content += "<h3>Infrastructure Components</h3>\n"
                        for comp in infra:
                            html_content += "<div class='item-card'>"
                            html_content += f"<div class='item-row'><div class='item-key'>Component</div><div class='item-val'><strong>{str(comp.get('component', ''))}</strong></div></div>"
                            html_content += f"<div class='item-row'><div class='item-key'>Technology</div><div class='item-val'><code>{str(comp.get('technology', ''))}</code></div></div>"
                            html_content += f"<div class='item-row'><div class='item-key'>Purpose</div><div class='item-val'>{str(comp.get('purpose', ''))}</div></div>"
                            config_notes = comp.get('configuration_notes', '')
                            if config_notes:
                                html_content += f"<div class='item-row'><div class='item-key'>Config Notes</div><div class='item-val'><em>{str(config_notes)}</em></div></div>"
                            html_content += "</div>\n"
                    
                    # CI/CD Pipeline
                    cicd = content_dict.get('cicd_pipeline', [])
                    if cicd:
                        html_content += "<h3>CI/CD Pipeline</h3>\n"
                        for step in cicd:
                            html_content += "<div class='item-card'>"
                            html_content += f"<div class='item-row'><div class='item-key'>Stage</div><div class='item-val'><strong>{str(step.get('name', ''))}</strong></div></div>"
                            html_content += f"<div class='item-row'><div class='item-key'>Description</div><div class='item-val'>{str(step.get('description', ''))}</div></div>"
                            tools = step.get('tools_used', [])
                            if tools:
                                html_content += f"<div class='item-row'><div class='item-key'>Tools</div><div class='item-val'>{', '.join(str(t) for t in tools)}</div></div>"
                            html_content += "</div>\n"
                    
                    # Containerization
                    container = content_dict.get('containerization', '')
                    if container:
                        html_content += "<h3>Containerization</h3>\n"
                        html_content += f"<p>{markdown2.markdown(str(container)).replace('<p>','').replace('</p>','')}</p>\n"
                    
                    # Monitoring & Logging
                    monitoring = content_dict.get('monitoring_and_logging', '')
                    if monitoring:
                        html_content += "<h3>Monitoring & Logging</h3>\n"
                        html_content += f"<p>{markdown2.markdown(str(monitoring)).replace('<p>','').replace('</p>','')}</p>\n"
                    
                    # Disaster Recovery
                    dr = content_dict.get('disaster_recovery', '')
                    if dr:
                        html_content += "<h3>Disaster Recovery</h3>\n"
                        html_content += f"<p>{markdown2.markdown(str(dr)).replace('<p>','').replace('</p>','')}</p>\n"
                    
                    # Cost Analysis
                    cost = content_dict.get('cost_analysis', '')
                    if cost:
                        html_content += "<h3>Cost Analysis</h3>\n"
                        html_content += f"<p>{markdown2.markdown(str(cost)).replace('<p>','').replace('</p>','')}</p>\n"
                    
                    # Production Readiness Checklist
                    checklist = content_dict.get('production_readiness_checklist', [])
                    if checklist:
                        html_content += "<h3>Production Readiness Checklist</h3>\n<ul>\n"
                        for item in checklist:
                            html_content += f"<li>{str(item)}</li>\n"
                        html_content += "</ul>\n"
                    
                    # Interview Talking Points
                    talking = content_dict.get('interview_talking_points', '')
                    if talking:
                        html_content += "<h3>Interview Talking Points</h3>\n"
                        html_content += f"<p>{markdown2.markdown(str(talking)).replace('<p>','').replace('</p>','')}</p>\n"

                elif sid == 14:
                    # === Section 14: Interview Question Bank ===
                    # Question Categories
                    categories = content_dict.get('question_categories', [])
                    if categories:
                        for cat in categories:
                            cat_name = cat.get('category_name', 'Questions')
                            html_content += f"<h3>{str(cat_name)}</h3>\n"
                            questions = cat.get('questions', [])
                            for q in questions:
                                diff = q.get('difficulty', 'Intermediate')
                                if diff.lower() == 'advanced':
                                    diff_class = 'badge-red'
                                elif diff.lower() == 'basic':
                                    diff_class = 'badge-green'
                                else:
                                    diff_class = 'badge-orange'
                                html_content += "<div class='item-card'>"
                                html_content += f"<div class='item-row'><div class='item-key'>Question</div><div class='item-val'><strong style='font-size:11.5pt;'>{str(q.get('question', ''))}</strong> &nbsp;<span class='{diff_class}'>{diff}</span></div></div>"
                                html_content += f"<div class='item-row'><div class='item-key'>Key Concept</div><div class='item-val'>{str(q.get('key_concept_tested', ''))}</div></div>"
                                html_content += f"<div class='item-row'><div class='item-key'>Model Answer</div><div class='item-val'>{str(q.get('model_answer', ''))}</div></div>"
                                followups = q.get('follow_ups', [])
                                if followups:
                                    fu_html = ''
                                    for fu in followups:
                                        if isinstance(fu, dict):
                                            fu_html += f"→ <strong>{str(fu.get('question', ''))}</strong><br><em style='color:#9ca3af;margin-left:16px;'>{str(fu.get('talking_points', ''))}</em><br>"
                                        else:
                                            fu_html += f"→ {str(fu)}<br>"
                                    html_content += f"<div class='item-row'><div class='item-key'>Follow-ups</div><div class='item-val'>{fu_html}</div></div>"
                                terms = q.get('key_terms', [])
                                if terms:
                                    terms_html = ' '.join(f"<span style='background:#1e293b;color:#94a3b8;padding:2px 8px;border-radius:3px;font-size:9pt;margin-right:4px;'>{str(t)}</span>" for t in terms)
                                    html_content += f"<div class='item-row'><div class='item-key'>Key Terms</div><div class='item-val'>{terms_html}</div></div>"
                                html_content += "</div>\n"
                    
                    # Curveball Questions
                    curveballs = content_dict.get('curveball_questions', [])
                    if curveballs:
                        html_content += "<h3>Curveball Questions</h3>\n"
                        for q in curveballs:
                            html_content += "<div class='item-card'>"
                            html_content += f"<div class='item-row'><div class='item-key'>Question</div><div class='item-val'><strong>{str(q.get('question', ''))}</strong> <span style='background:#a855f7;color:#fff;padding:1px 6px;border-radius:3px;font-size:9pt;'>CURVEBALL</span></div></div>"
                            html_content += f"<div class='item-row'><div class='item-key'>Model Answer</div><div class='item-val'>{str(q.get('model_answer', ''))}</div></div>"
                            followups = q.get('follow_ups', [])
                            if followups:
                                fu_html = ''
                                for fu in followups:
                                    if isinstance(fu, dict):
                                        fu_html += f"→ <strong>{str(fu.get('question', ''))}</strong><br><em style='color:#9ca3af;margin-left:16px;'>{str(fu.get('talking_points', ''))}</em><br>"
                                    else:
                                        fu_html += f"→ {str(fu)}<br>"
                                html_content += f"<div class='item-row'><div class='item-key'>Follow-ups</div><div class='item-val'>{fu_html}</div></div>"
                            html_content += "</div>\n"
                    
                    # Red Flags to Avoid
                    red_flags = content_dict.get('red_flags_to_avoid', [])
                    if red_flags:
                        html_content += "<h3>Red Flags to Avoid</h3>\n<ul>\n"
                        for rf in red_flags:
                            html_content += f"<li style='color:#ef4444;'>{str(rf)}</li>\n"
                        html_content += "</ul>\n"
                    
                    # Confidence Builders
                    builders = content_dict.get('confidence_builders', [])
                    if builders:
                        html_content += "<h3>Confidence Builders</h3>\n<ul>\n"
                        for cb in builders:
                            html_content += f"<li style='color:#22c55e;'>{str(cb)}</li>\n"
                        html_content += "</ul>\n"
                    
                    # Weak Spots & Deflections
                    weak = content_dict.get('weak_spots_and_deflections', [])
                    if weak:
                        html_content += "<h3>Weak Spots & Graceful Deflections</h3>\n<ul>\n"
                        for ws in weak:
                            html_content += f"<li>{str(ws)}</li>\n"
                        html_content += "</ul>\n"

                else:
                    primitives = {k: v for k, v in content_dict.items() if not isinstance(v, (list, dict))}
                    complex_items = {k: v for k, v in content_dict.items() if isinstance(v, (list, dict))}

                    if primitives:
                        html_content += "<div class='item-card'>"
                        for key, val in primitives.items():
                            formatted_key = key.replace('_', ' ').title()
                            val_html = markdown2.markdown(str(val)).replace('<p>', '').replace('</p>', '').strip()
                            html_content += f"<div class='item-row'><div class='item-key'>{formatted_key}</div><div class='item-val'>{val_html}</div></div>"
                        html_content += "</div>\n"

                    for key, val in complex_items.items():
                        title = ' '.join(word.capitalize() for word in key.split('_'))
                        html_content += f"<h3>{title}</h3>\n"
                        
                        if isinstance(val, list):
                            for item in val:
                                if isinstance(item, dict):
                                    html_content += "<div class='item-card'>"
                                    for k, v in item.items():
                                        formatted_key = k.replace('_', ' ').title()
                                        if isinstance(v, list):
                                            html_content += f"<div class='item-row'><div class='item-key'>{formatted_key}</div><div class='item-val'>{', '.join(str(x) for x in v)}</div></div>"
                                        else:
                                            html_content += f"<div class='item-row'><div class='item-key'>{formatted_key}</div><div class='item-val'>{markdown2.markdown(str(v)).replace('<p>','').replace('</p>','')}</div></div>"
                                    html_content += "</div>"
                                else:
                                    html_content += f"<ul><li>{markdown2.markdown(str(item)).replace('<p>','').replace('</p>','')}</li></ul>"
                        elif isinstance(val, dict):
                            html_content += "<div class='item-card'>"
                            for k, v in val.items():
                                formatted_key = k.replace('_', ' ').title()
                                html_content += f"<div class='item-row'><div class='item-key'>{formatted_key}</div><div class='item-val'>{markdown2.markdown(str(v)).replace('<p>','').replace('</p>','')}</div></div>"
                            html_content += "</div>"
            else:
                html_content += markdown2.markdown(str(s['content']))
            
        html_content += "</body></html>"
        
        # Generate PDF
        pdf_bytes = HTML(string=html_content).write_pdf()
        
        # Save a copy to the project folder
        pdf_path = os.path.join(PROJECTS_DIR, project_name, f"{project_name}_revision.pdf")
        with open(pdf_path, 'wb') as f:
            f.write(pdf_bytes)
            
        buffer = io.BytesIO(pdf_bytes)
        buffer.seek(0)
        
        return send_file(
            buffer,
            as_attachment=True,
            download_name=f"{project_name}_revision.pdf",
            mimetype='application/pdf'
        )
    except Exception as e:
        app.logger.error(f'PDF generation error: {traceback_module.format_exc()}')
        with open('server_errors.log', 'a') as ef:
            ef.write(f"--- [PDF] ---\n{traceback_module.format_exc()}\n")
        return jsonify({'error': f'PDF generation failed: {str(e)}'}), 500
    finally:
        db.close()



@app.route('/api/project/<project_name>/markdown', methods=['POST'])
def generate_markdown(project_name):
    project_name = secure_project_name(project_name)
    if not project_name:
        return jsonify({'error': 'Invalid project name'}), 400
    db_path = os.path.join(PROJECTS_DIR, project_name, 'project.db')
    if not os.path.exists(db_path):
        return jsonify({'error': 'Project not found'}), 404

    skip_sections = []
    placeholder_sections = []
    if request.json:
        skip_sections = request.json.get('skip_sections', [])
        placeholder_sections = request.json.get('placeholder_sections', [])

    db = ProjectDB(db_path)
    try:
        sections = db.get_generated_sections()
        info = db.get_repo_info()
        project_title = str(info.get('name', project_name))

        md = f"# {project_title}\n\n"
        md += "**Technical Documentation & Interview Guide**\n\n"
        md += "_Generated by BuiltByMe_\n\n---\n\n"

        # Table of Contents
        md += "## Table of Contents\n\n"
        for s in sections:
            if s['section_id'] not in skip_sections:
                md += f"- **Section {s['section_id']}:** {str(s['name'])}\n"
        md += "\n---\n\n"

        for s in sections:
            sid = s['section_id']

            if sid in skip_sections:
                continue

            md += f"## Section {sid}: {str(s['name'])}\n\n"

            if sid in placeholder_sections:
                md += "_This section is intentionally left blank for manual completion._\n\n---\n\n"
                continue

            content_dict = None
            try:
                content_dict = json.loads(s['content'])
            except (json.JSONDecodeError, TypeError):
                pass

            if isinstance(content_dict, dict):
                md += _render_dict_to_markdown(content_dict, sid)
            elif s.get('content'):
                md += str(s['content']) + "\n"

            md += "\n---\n\n"

        md_bytes = md.encode('utf-8')
        md_path = os.path.join(PROJECTS_DIR, project_name, f"{project_name}_docs.md")
        with open(md_path, 'wb') as f:
            f.write(md_bytes)

        buffer = io.BytesIO(md_bytes)
        buffer.seek(0)

        return send_file(
            buffer,
            as_attachment=True,
            download_name=f"{project_name}_docs.md",
            mimetype='text/markdown'
        )
    except Exception as e:
        app.logger.error(f'Markdown export error: {traceback_module.format_exc()}')
        with open('server_errors.log', 'a') as ef:
            ef.write(f"--- [Markdown] ---\n{traceback_module.format_exc()}\n")
        return jsonify({'error': f'Markdown export failed: {str(e)}'}), 500
    finally:
        db.close()


def _render_dict_to_markdown(d, sid=None):
    """Converts a section content dict to formatted Markdown."""
    md = ""
    for key, value in d.items():
        title = key.replace('_', ' ').title()

        if isinstance(value, str):
            if not value:
                continue
            md += f"### {title}\n\n{value}\n\n"
        elif isinstance(value, bool):
            md += f"**{title}:** {'Yes' if value else 'No'}\n\n"
        elif isinstance(value, (int, float)):
            md += f"**{title}:** {value}\n\n"
        elif isinstance(value, list):
            if not value:
                continue
            md += f"### {title}\n\n"
            if len(value) > 0 and isinstance(value[0], dict):
                for i, item in enumerate(value):
                    # Use name/title as heading if available
                    item_name = item.get('name') or item.get('title') or item.get('question') or item.get('framework_name') or item.get('framework') or f"Item {i+1}"
                    md += f"#### {item_name}\n\n"
                    for k, v in item.items():
                        if k in ('name', 'title'):
                            continue
                        field_title = k.replace('_', ' ').title()
                        if isinstance(v, list):
                            md += f"- **{field_title}:** {', '.join(str(x) for x in v)}\n"
                        elif isinstance(v, bool):
                            md += f"- **{field_title}:** {'Yes' if v else 'No'}\n"
                        else:
                            md += f"- **{field_title}:** {v}\n"
                    md += "\n"
            else:
                for item in value:
                    md += f"- {item}\n"
                md += "\n"
        elif isinstance(value, dict):
            md += f"### {title}\n\n"
            for k, v in value.items():
                field_title = k.replace('_', ' ').title()
                if isinstance(v, list):
                    md += f"**{field_title}:** {', '.join(str(x) for x in v)}\n\n"
                else:
                    md += f"**{field_title}:** {v}\n\n"

    return md


@app.route('/api/project/<project_name>/generated/<int:section_id>', methods=['DELETE'])
def delete_generated_section(project_name, section_id):
    project_name = secure_project_name(project_name)
    if not project_name:
        return jsonify({'error': 'Invalid project name'}), 400
    db_path = os.path.join(PROJECTS_DIR, project_name, 'project.db')
    if not os.path.exists(db_path):
        return jsonify({'error': 'Project not found'}), 404

    db = ProjectDB(db_path)
    try:
        db.delete_generated_section(section_id)
        return jsonify({'message': 'Deleted successfully'})
    finally:
        db.close()

@app.route('/api/project/<project_name>/custom_section_def', methods=['POST'])
def create_custom_section_def(project_name):
    project_name = secure_project_name(project_name)
    if not project_name:
        return jsonify({'error': 'Invalid project name'}), 400
    db_path = os.path.join(PROJECTS_DIR, project_name, 'project.db')
    if not os.path.exists(db_path):
        return jsonify({'error': 'Project not found'}), 404

    data = request.json
    name = (data.get('name') or data.get('title') or data.get('section_title') or '').strip()
    description = (data.get('description') or data.get('section_description') or '').strip()
    if not name:
        return jsonify({'error': 'Section title is required'}), 400

    db = ProjectDB(db_path)
    try:
        existing_defs = db.get_custom_section_defs()
        existing_gen = db.get_generated_sections()
        custom_ids = [s['section_id'] for s in existing_defs + existing_gen if s['section_id'] >= 100]
        next_id = max(custom_ids) + 1 if custom_ids else 100

        db.save_custom_section_def(next_id, name, description)
        return jsonify({
            'message': 'Custom section created successfully',
            'section_id': next_id,
            'name': name,
            'description': description
        })
    finally:
        db.close()

@app.route('/api/project/<project_name>/custom_section_defs', methods=['GET'])
def get_custom_section_defs(project_name):
    project_name = secure_project_name(project_name)
    if not project_name:
        return jsonify({'error': 'Invalid project name'}), 400
    db_path = os.path.join(PROJECTS_DIR, project_name, 'project.db')
    if not os.path.exists(db_path):
        return jsonify({'error': 'Project not found'}), 404

    db = ProjectDB(db_path)
    try:
        defs = db.get_custom_section_defs()
        return jsonify(defs)
    finally:
        db.close()

@app.route('/api/project/<project_name>/custom_section_def/<int:section_id>', methods=['DELETE'])
def delete_custom_section_def(project_name, section_id):
    project_name = secure_project_name(project_name)
    if not project_name:
        return jsonify({'error': 'Invalid project name'}), 400
    db_path = os.path.join(PROJECTS_DIR, project_name, 'project.db')
    if not os.path.exists(db_path):
        return jsonify({'error': 'Project not found'}), 404

    db = ProjectDB(db_path)
    try:
        db.delete_custom_section_def(section_id)
        return jsonify({'message': 'Custom section definition deleted successfully'})
    finally:
        db.close()

@app.route('/api/project/<project_name>/generate_custom', methods=['POST'])
def generate_custom_section(project_name):
    """
    Generate a custom section using the built-in LLM gateway.
    Takes a section title and description, builds a prompt, calls the LLM,
    validates the response, and saves it as a custom section (ID >= 100).
    """
    project_name = secure_project_name(project_name)
    if not project_name:
        return jsonify({'error': 'Invalid project name'}), 400
    db_path = os.path.join(PROJECTS_DIR, project_name, 'project.db')
    if not os.path.exists(db_path):
        return jsonify({'error': 'Project not found'}), 404

    data = request.json
    section_title = (data.get('section_title') or '').strip()
    section_description = (data.get('section_description') or '').strip()
    provider = data.get('provider')
    api_key = data.get('api_key')
    detail_level = data.get('detail_level', 1)
    custom_instructions = data.get('custom_instructions', '')
    strategy = data.get('strategy', '1_pass')

    if not section_title:
        return jsonify({'error': 'Section title is required'}), 400
    if not section_description:
        return jsonify({'error': 'Section description is required'}), 400
    if not provider or not api_key:
        return jsonify({'error': 'Provider and API key are required'}), 400

    # Resolve saved key references
    if str(api_key).startswith('saved_'):
        try:
            key_index = int(api_key.replace('saved_', ''))
            cfg = load_config()
            keys = cfg.get('llm_keys', [])
            if 0 <= key_index < len(keys):
                api_key = decrypt_val(keys[key_index].get('key'))
                provider = keys[key_index].get('provider')
            else:
                return jsonify({'error': 'Invalid saved key reference'}), 400
        except ValueError:
            return jsonify({'error': 'Invalid saved key format'}), 400

    db = ProjectDB(db_path)
    try:
        # Build project context
        info = db.get_repo_info()
        files = db.get_files()

        context_str = f"Project Name: {info.get('full_name')}\n"
        context_str += f"Description: {info.get('description')}\n"
        context_str += f"Language: {info.get('language')}\n\n"

        # Add file list
        context_str += "Files in repository:\n"
        for f in files:
            context_str += f"- {f['path']} ({f['size']} bytes)\n"

        # Add README if exists
        readme_file = next((f for f in files if 'readme' in f['path'].lower()), None)
        if readme_file:
            blocks = db.get_code_blocks(readme_file['id'])
            readme_content = "".join([b['content'] for b in blocks if b['content']])
            if readme_content:
                context_str += f"\n\n--- README.md ---\n{readme_content}\n--- END README ---\n"

        passes_log = []

        if strategy == '1_pass':
            context_str += "\n\n--- ENTIRE CODEBASE ---\n"
            for f in files:
                if 'readme' in f['path'].lower():
                    continue
                blocks = db.get_code_blocks(f['id'])
                file_content = "".join([b['content'] for b in blocks if b['content']])
                if file_content:
                    context_str += f"\nFile: {f['path']}\n{file_content}\n"
            context_str += "--- END ENTIRE CODEBASE ---\n"
            passes_log.append({'pass': 1, 'info': 'Full codebase dump (1-pass)'})
        elif strategy == '2_pass':
            # Build skeleton for pass 1
            skeleton_str = context_str
            skeleton_str += "\n\n--- FILE SKELETON WITH METADATA ---\n"
            for f in files:
                if 'readme' in f['path'].lower():
                    continue
                skeleton_str += f"\nFile: {f['path']} | Language: {f.get('language', 'unknown')} | Size: {f['size']} bytes\n"
                if f.get('metadata'):
                    try:
                        meta = json.loads(f['metadata']) if isinstance(f['metadata'], str) else f['metadata']
                        imports = meta.get('imports', []) or meta.get('includes', []) or meta.get('uses', [])
                        if imports:
                            skeleton_str += f"  Imports: {', '.join(imports[:20])}\n"
                    except (json.JSONDecodeError, TypeError):
                        pass
                blocks = db.get_code_blocks(f['id'])
                block_names = []
                for b in blocks:
                    if b.get('block_type') in ('class', 'function', 'method') and b.get('name'):
                        prefix = b['block_type']
                        parent = f" (in {b['parent_name']})" if b.get('parent_name') else ''
                        block_names.append(f"{prefix} {b['name']}{parent}")
                if block_names:
                    skeleton_str += f"  Definitions: {', '.join(block_names[:15])}\n"
            skeleton_str += "--- END FILE SKELETON ---\n"

            retrieval_user_prompt = (
                f"I need to generate a custom documentation section titled: **{section_title}**\n"
                f"Section focus: {section_description}\n\n"
                f"Please analyze the file skeleton below and tell me which files I should retrieve "
                f"the full source code for.\n\n{skeleton_str}"
            )

            retrieval_result = generate_content(
                provider=provider,
                api_key=api_key,
                system_prompt=FILE_RETRIEVAL_PROMPT,
                user_prompt=retrieval_user_prompt,
                response_schema=FileRetrievalRequest
            )

            if hasattr(retrieval_result, 'model_dump'):
                retrieval_data = retrieval_result.model_dump()
            else:
                retrieval_data = retrieval_result

            requested_paths = retrieval_data.get('requested_files', [])[:15]
            reasoning = retrieval_data.get('reasoning', '')

            passes_log.append({
                'pass': 1,
                'info': f'LLM analyzed skeleton and requested {len(requested_paths)} files',
                'reasoning': reasoning,
                'requested_files': requested_paths
            })

            file_lookup = {f['path']: f for f in files}
            context_str += "\n\n--- SELECTED SOURCE CODE (retrieved via 2-pass) ---\n"
            retrieved_count = 0
            for path in requested_paths:
                file_record = file_lookup.get(path)
                if not file_record:
                    continue
                if 'readme' in path.lower():
                    continue
                blocks = db.get_code_blocks(file_record['id'])
                file_content = "".join([b['content'] for b in blocks if b['content']])
                if file_content:
                    context_str += f"\nFile: {path}\n{file_content}\n"
                    retrieved_count += 1
            context_str += "--- END SELECTED SOURCE CODE ---\n"
            passes_log.append({'pass': 2, 'info': f'Retrieved {retrieved_count} files for focused generation'})

        # Build system prompt for the custom section
        system_prompt = f"""You are an expert Principal Software Engineer analyzing a codebase.
Your goal is to generate a custom documentation section titled: "{section_title}"

Section Description / Focus:
{section_description}

# Instructions
1. Analyze the provided codebase context carefully.
2. Generate a comprehensive, structured analysis based on the section title and description above.
3. Your response MUST be a valid JSON object with clear, descriptive string keys.
4. Structure your response logically — group related information together.
5. Use a mix of strings (for explanations), arrays (for lists), and nested objects (for grouped data).
6. Write in a conversational, first-person interview style: "So what I did was...", "The reason I chose..."

# CRITICAL — Response Format
You MUST return a valid JSON object. Structure it like this:
{{
    "overview": "A 3-5 sentence summary of the section topic as it relates to this project...",
    "key_points": [
        {{
            "title": "Point title",
            "explanation": "Detailed explanation in conversational style..."
        }}
    ],
    "detailed_analysis": "In-depth analysis paragraph...",
    "recommendations": ["Recommendation 1", "Recommendation 2"],
    "interview_angle": "How to discuss this in an interview..."
}}

The exact keys depend on what makes sense for the topic "{section_title}". Use descriptive key names.
Include 4-8 top-level keys for a comprehensive analysis.

# CRITICAL — Writing Style
- Write like you're explaining to an interviewer face-to-face.
- Use first person: "I designed...", "The reason I went with..."
- Be specific and opinionated. Real trade-offs, real reasoning.
- Short, punchy sentences. Sound like a real engineer, not a textbook.
"""

        detail_instructions = {
            0: "\n\nDETAIL LEVEL: SHORT. Keep all responses brief. 1-2 sentences per field. Use bullet points over paragraphs.",
            1: "\n\nDETAIL LEVEL: MEDIUM. Provide balanced detail — 2-3 sentences for paragraph fields.",
            2: "\n\nDETAIL LEVEL: DETAILED. Provide comprehensive, in-depth analysis. 5-8 sentences for paragraph fields. Include technical nuances, edge cases, and implementation specifics."
        }
        system_prompt += detail_instructions.get(detail_level, detail_instructions[1])

        if custom_instructions:
            system_prompt += f"\n\nUser Custom Instructions:\n{custom_instructions}"

        user_prompt = f"Please generate the custom section based on the following codebase context:\n\n{context_str}"

        # Generate without structured output (raw JSON mode) since we don't have a Pydantic schema
        result = generate_content(
            provider=provider,
            api_key=api_key,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            response_schema=None,
            temperature=0.3
        )

        # Parse the LLM response as JSON
        raw_content = result if isinstance(result, str) else (result.content if hasattr(result, 'content') else str(result))

        # Try to extract JSON from the response
        content = None
        # Try direct parse
        try:
            content = json.loads(raw_content)
        except (json.JSONDecodeError, TypeError):
            pass

        # Try extracting from markdown code block
        if content is None:
            import re as _re
            json_match = _re.search(r'```(?:json)?\s*\n?(.*?)\n?```', raw_content, _re.DOTALL)
            if json_match:
                try:
                    content = json.loads(json_match.group(1))
                except (json.JSONDecodeError, TypeError):
                    pass

        # Fallback: wrap raw text as content
        if content is None:
            content = {"raw_content": raw_content}

        # Determine section ID: use provided section_id or compute 100+ range for custom sections
        if data.get('section_id'):
            next_id = int(data.get('section_id'))
        else:
            existing_sections = db.get_generated_sections()
            existing_defs = db.get_custom_section_defs()
            custom_ids = [s['section_id'] for s in existing_sections + existing_defs if s['section_id'] >= 100]
            next_id = max(custom_ids) + 1 if custom_ids else 100

        db.save_generated_section(next_id, section_title, content)

        return jsonify({
            'message': 'Custom section generated successfully',
            'section_id': next_id,
            'section_title': section_title,
            'content': content,
            'passes': passes_log
        })
    except Exception as e:
        app.logger.error(f'Custom section generation error: {traceback_module.format_exc()}')
        return jsonify({'error': f'Custom section generation failed: {str(e)}'}), 500
    finally:
        db.close()


@app.route('/api/project/<project_name>/add_custom_manual', methods=['POST'])
def add_custom_section_manual(project_name):
    """
    Add a custom section by pasting raw JSON content (manual mode).
    Validates the JSON and saves it with a custom section ID >= 100.
    """
    project_name = secure_project_name(project_name)
    if not project_name:
        return jsonify({'error': 'Invalid project name'}), 400
    db_path = os.path.join(PROJECTS_DIR, project_name, 'project.db')
    if not os.path.exists(db_path):
        return jsonify({'error': 'Project not found'}), 404

    data = request.json
    section_title = (data.get('section_title') or '').strip()
    raw_content = (data.get('content') or '').strip()

    if not section_title:
        return jsonify({'error': 'Section title is required'}), 400
    if not raw_content:
        return jsonify({'error': 'Content is required'}), 400

    # Try to parse as JSON
    content = None
    try:
        content = json.loads(raw_content)
    except (json.JSONDecodeError, TypeError):
        pass

    # Try extracting from markdown code block
    if content is None:
        json_match = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', raw_content, re.DOTALL)
        if json_match:
            try:
                content = json.loads(json_match.group(1))
            except (json.JSONDecodeError, TypeError):
                pass

    if content is None:
        return jsonify({'error': 'Invalid JSON content. Please paste valid JSON or a JSON code block.'}), 400

    if not isinstance(content, dict):
        return jsonify({'error': 'Content must be a JSON object (not an array or primitive).'}), 400

    db = ProjectDB(db_path)
    try:
        if data.get('section_id'):
            next_id = int(data.get('section_id'))
        else:
            existing_sections = db.get_generated_sections()
            existing_defs = db.get_custom_section_defs()
            custom_ids = [s['section_id'] for s in existing_sections + existing_defs if s['section_id'] >= 100]
            next_id = max(custom_ids) + 1 if custom_ids else 100

        db.save_generated_section(next_id, section_title, content)

        return jsonify({
            'message': 'Custom section added successfully',
            'section_id': next_id,
            'section_title': section_title,
            'content': content
        })
    except Exception as e:
        app.logger.error(f'Manual custom section error: {traceback_module.format_exc()}')
        return jsonify({'error': f'Failed to add custom section: {str(e)}'}), 500
    finally:
        db.close()


@app.route('/api/project/<project_name>/custom_prompt', methods=['POST'])
def get_custom_section_prompt(project_name):
    """
    Generate a ready-to-copy prompt for external LLM usage.
    Returns the full prompt with project context that the user can paste into ChatGPT/Claude.
    """
    project_name = secure_project_name(project_name)
    if not project_name:
        return jsonify({'error': 'Invalid project name'}), 400
    db_path = os.path.join(PROJECTS_DIR, project_name, 'project.db')
    if not os.path.exists(db_path):
        return jsonify({'error': 'Project not found'}), 404

    data = request.json
    section_title = (data.get('section_title') or '').strip()
    section_description = (data.get('section_description') or '').strip()

    if not section_title or not section_description:
        return jsonify({'error': 'Section title and description are required'}), 400

    db = ProjectDB(db_path)
    try:
        info = db.get_repo_info()
        files = db.get_files()

        # Build a condensed context for copy-paste
        context_str = f"Project Name: {info.get('full_name')}\n"
        context_str += f"Description: {info.get('description')}\n"
        context_str += f"Language: {info.get('language')}\n\n"
        context_str += "Files in repository:\n"
        for f in files:
            context_str += f"- {f['path']} ({f['size']} bytes, {f.get('language', 'unknown')})\n"

        # Include file skeleton with metadata
        context_str += "\n--- FILE SKELETON WITH METADATA ---\n"
        for f in files[:50]:  # Limit for copy-paste friendliness
            if f.get('metadata'):
                try:
                    meta = json.loads(f['metadata']) if isinstance(f['metadata'], str) else f['metadata']
                    imports = meta.get('imports', []) or meta.get('includes', [])
                    if imports:
                        context_str += f"  {f['path']}: imports [{', '.join(imports[:10])}]\n"
                except (json.JSONDecodeError, TypeError):
                    pass

        prompt = f"""You are an expert Principal Software Engineer analyzing a codebase.

I need you to generate a custom documentation section for my project.

# Section: {section_title}
# Focus: {section_description}

# Instructions
1. Analyze the project context below carefully.
2. Generate a comprehensive, structured analysis as a valid JSON object.
3. Use descriptive string keys, mix of strings, arrays, and nested objects.
4. Write in a conversational, first-person interview style.
5. Include 4-8 top-level keys for comprehensive coverage.

# Response Format
Return ONLY a valid JSON object wrapped in ```json ... ``` code fences. Example structure:
```json
{{
    "overview": "Summary of this topic for the project...",
    "key_points": [
        {{"title": "Point 1", "explanation": "Detailed explanation..."}},
        {{"title": "Point 2", "explanation": "Detailed explanation..."}}
    ],
    "detailed_analysis": "In-depth analysis...",
    "recommendations": ["Item 1", "Item 2"],
    "interview_angle": "How to discuss this in an interview..."
}}
```

Adapt the keys to match the topic "{section_title}". Be comprehensive and technical.

# Project Context
{context_str}
"""
        return jsonify({'prompt': prompt})
    finally:
        db.close()


@app.route('/api/project/<project_name>/delete', methods=['DELETE'])
def delete_project(project_name):
    import shutil
    project_name = secure_project_name(project_name)
    if not project_name:
        return jsonify({'error': 'Invalid project name'}), 400
    project_path = os.path.join(PROJECTS_DIR, project_name)
    if os.path.exists(project_path):
        shutil.rmtree(project_path)
        if project_name in extraction_status:
            del extraction_status[project_name]
        return jsonify({'message': 'Deleted'})
    return jsonify({'error': 'Not found'}), 404


if __name__ == '__main__':
    os.makedirs(PROJECTS_DIR, exist_ok=True)
    app.run(debug=False, port=5000)
