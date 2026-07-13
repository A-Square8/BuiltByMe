import requests
import base64
from .file_filter import should_skip_dir, should_skip_file


import fnmatch

class GitHubFetcher:

    def __init__(self, repo_url, token=None, ignore_patterns=None):
        self.repo_url = repo_url.rstrip('/')
        self.token = token
        self.ignore_patterns = ignore_patterns or []
        self.owner, self.repo = self._parse_url()
        self.api_base = f"https://api.github.com/repos/{self.owner}/{self.repo}"
        self.headers = {'Accept': 'application/vnd.github.v3+json'}
        if self.token:
            self.headers['Authorization'] = f'token {self.token}'

    def _parse_url(self):
        parts = self.repo_url.replace('https://github.com/', '').replace('.git', '').split('/')
        return parts[0], parts[1]

    def get_repo_info(self):
        resp = requests.get(self.api_base, headers=self.headers)
        resp.raise_for_status()
        data = resp.json()
        return {
            'name': data['name'],
            'full_name': data['full_name'],
            'description': data.get('description', ''),
            'language': data.get('language', ''),
            'topics': data.get('topics', []),
            'stars': data.get('stargazers_count', 0),
            'forks': data.get('forks_count', 0),
            'default_branch': data.get('default_branch', 'main'),
        }

    def get_tree(self, branch='main'):
        url = f"{self.api_base}/git/trees/{branch}?recursive=1"
        resp = requests.get(url, headers=self.headers)
        resp.raise_for_status()
        return resp.json().get('tree', [])

    def get_file_content(self, path):
        url = f"{self.api_base}/contents/{path}"
        resp = requests.get(url, headers=self.headers)
        resp.raise_for_status()
        data = resp.json()
        if data.get('encoding') == 'base64':
            return base64.b64decode(data['content']).decode('utf-8', errors='replace')
        return data.get('content', '')

    def get_commits(self, limit=50):
        url = f"{self.api_base}/commits?per_page={limit}"
        resp = requests.get(url, headers=self.headers)
        resp.raise_for_status()
        commits = []
        for c in resp.json():
            commits.append({
                'sha': c['sha'][:7],
                'message': c['commit']['message'],
                'author': c['commit']['author']['name'],
                'date': c['commit']['author']['date'],
            })
        return commits

    def get_filtered_files(self, branch='main'):
        tree = self.get_tree(branch)
        files = []
        for item in tree:
            if item['type'] != 'blob':
                continue
            path = item['path']
            parts = path.split('/')
            skip = False
            
            # Check custom ignore patterns (using fnmatch for wildcard support)
            for pattern in self.ignore_patterns:
                if fnmatch.fnmatch(path, pattern) or any(fnmatch.fnmatch(p, pattern) for p in parts):
                    skip = True
                    break
            
            if skip:
                continue

            # Standard filtering
            for part in parts[:-1]:
                if should_skip_dir(part):
                    skip = True
                    break
            if skip:
                continue
            size = item.get('size', 0)
            if should_skip_file(path, size):
                continue
            files.append({'path': path, 'size': size})
        return files
