import os
import json
from .github_fetcher import GitHubFetcher
from .language_detector import detect_language, should_full_extract
from .extractors import extract_file
from .database import ProjectDB


class ExtractionPipeline:

    def __init__(self, repo_url, token, base_dir='my_projects', ignore_patterns=None):
        self.fetcher = GitHubFetcher(repo_url, token, ignore_patterns=ignore_patterns)
        self.repo_name = self.fetcher.repo
        self.project_dir = os.path.join(base_dir, self.repo_name)
        self.db_path = os.path.join(self.project_dir, 'project.db')
        self.db = None
        self.progress = {'status': 'idle', 'total': 0, 'processed': 0, 'current_file': '', 'errors': []}

    def run(self, progress_callback=None):
        os.makedirs(self.project_dir, exist_ok=True)
        self.db = ProjectDB(self.db_path)

        try:
            self.progress['status'] = 'fetching_info'
            if progress_callback:
                progress_callback(self.progress)

            repo_info = self.fetcher.get_repo_info()
            self.db.save_repo_info(repo_info)
            branch = repo_info.get('default_branch', 'main')

            self.progress['status'] = 'fetching_commits'
            if progress_callback:
                progress_callback(self.progress)

            commits = self.fetcher.get_commits(limit=100)
            self.db.save_commits(commits)

            self.progress['status'] = 'fetching_tree'
            if progress_callback:
                progress_callback(self.progress)

            files = self.fetcher.get_filtered_files(branch)
            self.progress['total'] = len(files)

            log_id = self.db.start_extraction(len(files))

            self.progress['status'] = 'extracting'
            if progress_callback:
                progress_callback(self.progress)

            errors = []
            for i, file_info in enumerate(files):
                path = file_info['path']
                size = file_info['size']
                self.progress['processed'] = i + 1
                self.progress['current_file'] = path

                try:
                    content = self.fetcher.get_file_content(path)
                    is_full = should_full_extract(path)
                    language = detect_language(path)

                    metadata = None
                    blocks = []
                    
                    if language:
                        try:
                            source_bytes = content.encode('utf-8')
                            res = extract_file(source_bytes, language)
                            if isinstance(res, tuple) and len(res) == 2:
                                metadata, blocks = res
                            else:
                                metadata = res
                                blocks = [{'block_type': 'module_level', 'content': content}]
                        except Exception as e:
                            errors.append(f"Parse error {path}: {str(e)}")
                            blocks = [{'block_type': 'module_level', 'content': content}]
                    else:
                        blocks = [{'block_type': 'module_level', 'content': content}]

                    file_id = self.db.save_file(
                        path=path,
                        language=language or 'unknown',
                        size=size,
                        is_full_extract=is_full,
                        metadata=metadata
                    )
                    
                    # Ensure all blocks have their file_id set just in case, though save_code_blocks sets it
                    self.db.save_code_blocks(file_id, blocks)
                except Exception as e:
                    errors.append(f"Fetch error {path}: {str(e)}")

                if progress_callback:
                    progress_callback(self.progress)

                if (i + 1) % 10 == 0:
                    self.db.update_extraction(log_id, i + 1, errors)

            self.db.update_extraction(log_id, len(files), errors)
            self.db.complete_extraction(log_id)

            self.progress['status'] = 'completed'
            self.progress['errors'] = errors
            if progress_callback:
                progress_callback(self.progress)

            return {'success': True, 'project_name': self.repo_name, 'files_processed': len(files), 'errors': errors}

        except Exception as e:
            self.progress['status'] = 'failed'
            self.progress['errors'] = [str(e)]
            if progress_callback:
                progress_callback(self.progress)
            if self.db:
                try:
                    self.db.fail_extraction(log_id, str(e))
                except:
                    pass
            return {'success': False, 'error': str(e)}
        finally:
            if self.db:
                self.db.close()
