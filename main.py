import os
import json
import threading
from cryptography.fernet import Fernet
# pyrefly: ignore [missing-import]
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from extraction.pipeline import ExtractionPipeline
from extraction.database import ProjectDB
from extraction.llm_gateway import generate_content
from extraction.prompts import SECTION_SCHEMAS, SECTION_PROMPTS

app = Flask(__name__, static_folder='ui', static_url_path='')
CORS(app)

PROJECTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'my_projects')
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.json')
MASTER_KEY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.master.key')
extraction_status = {}

def get_fernet():
    if not os.path.exists(MASTER_KEY_FILE):
        key = Fernet.generate_key()
        with open(MASTER_KEY_FILE, 'wb') as f:
            f.write(key)
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
    except:
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
            except:
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

    if not repo_url:
        return jsonify({'error': 'Repository URL is required'}), 400

    try:
        parts = repo_url.replace('https://github.com/', '').replace('.git', '').split('/')
        repo_name = parts[1]
    except:
        return jsonify({'error': 'Invalid GitHub URL'}), 400

    if repo_name in extraction_status and extraction_status[repo_name].get('status') == 'extracting':
        return jsonify({'error': 'Extraction already in progress'}), 409

    extraction_status[repo_name] = {'status': 'starting', 'total': 0, 'processed': 0, 'current_file': '', 'errors': []}

    def run_pipeline():
        pipeline = ExtractionPipeline(repo_url, token, PROJECTS_DIR)

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
            except:
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
    db_path = os.path.join(PROJECTS_DIR, project_name, 'project.db')
    if not os.path.exists(db_path):
        return jsonify({'error': 'Project not found'}), 404

    data = request.json
    section_id = int(data.get('section_id'))
    provider = data.get('provider')
    api_key = data.get('api_key')
    strategy = data.get('strategy', '1_pass')
    custom_instructions = data.get('custom_instructions', '')

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
        
        context_str += "Files in repository:\n"
        for f in files:
            context_str += f"- {f['path']} ({f['size']} bytes)\n"
            
        # Add README content if it exists
        readme_file = next((f for f in files if 'readme' in f['path'].lower()), None)
        if readme_file:
            blocks = db.get_code_blocks(readme_file['id'])
            readme_content = "".join([b['content'] for b in blocks if b['content']])
            if readme_content:
                context_str += f"\n\n--- README.md ---\n{readme_content}\n--- END README ---\n"
                
        # If strategy is 1_pass, we should also include all code content
        if strategy == '1_pass':
            context_str += "\n\n--- ENTIRE CODEBASE ---\n"
            for f in files:
                if 'readme' in f['path'].lower(): continue
                blocks = db.get_code_blocks(f['id'])
                file_content = "".join([b['content'] for b in blocks if b['content']])
                if file_content:
                    context_str += f"\nFile: {f['path']}\n{file_content}\n"
            context_str += "--- END ENTIRE CODEBASE ---\n"

        system_prompt = SECTION_PROMPTS[section_id]
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
        
        section_names = {1: 'Project Overview'}
        
        db.save_generated_section(section_id, section_names.get(section_id, f'Section {section_id}'), content)
        
        return jsonify({'message': 'Success', 'content': content})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()


@app.route('/api/project/<project_name>/generated', methods=['GET'])
def get_generated_sections(project_name):
    db_path = os.path.join(PROJECTS_DIR, project_name, 'project.db')
    if not os.path.exists(db_path):
        return jsonify({'error': 'Project not found'}), 404

    db = ProjectDB(db_path)
    try:
        sections = db.get_generated_sections()
        for s in sections:
            try:
                s['content'] = json.loads(s['content'])
            except:
                pass
        return jsonify(sections)
    finally:
        db.close()


@app.route('/api/project/<project_name>/generated/<int:section_id>', methods=['DELETE'])
def delete_generated_section(project_name, section_id):
    db_path = os.path.join(PROJECTS_DIR, project_name, 'project.db')
    if not os.path.exists(db_path):
        return jsonify({'error': 'Project not found'}), 404

    db = ProjectDB(db_path)
    try:
        db.delete_generated_section(section_id)
        return jsonify({'message': 'Deleted successfully'})
    finally:
        db.close()

@app.route('/api/project/<project_name>/delete', methods=['DELETE'])
def delete_project(project_name):
    import shutil
    project_path = os.path.join(PROJECTS_DIR, project_name)
    if os.path.exists(project_path):
        shutil.rmtree(project_path)
        if project_name in extraction_status:
            del extraction_status[project_name]
        return jsonify({'message': 'Deleted'})
    return jsonify({'error': 'Not found'}), 404


if __name__ == '__main__':
    os.makedirs(PROJECTS_DIR, exist_ok=True)
    app.run(debug=True, port=5000)
