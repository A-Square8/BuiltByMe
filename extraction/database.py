import sqlite3
import json
import os


class ProjectDB:

    def __init__(self, db_path):
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()

    def _create_tables(self):
        self.conn.executescript('''
            CREATE TABLE IF NOT EXISTS repo_info (
                id INTEGER PRIMARY KEY,
                name TEXT,
                full_name TEXT,
                description TEXT,
                language TEXT,
                topics TEXT,
                stars INTEGER,
                forks INTEGER,
                default_branch TEXT,
                extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                path TEXT UNIQUE,
                language TEXT,
                size INTEGER,
                is_full_extract INTEGER DEFAULT 0,
                metadata TEXT,
                extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS code_blocks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_id INTEGER,
                block_type TEXT,
                name TEXT,
                parent_name TEXT,
                start_line INTEGER,
                end_line INTEGER,
                content TEXT,
                FOREIGN KEY (file_id) REFERENCES files(id)
            );

            CREATE TABLE IF NOT EXISTS commits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sha TEXT,
                message TEXT,
                author TEXT,
                date TEXT
            );

            CREATE TABLE IF NOT EXISTS extraction_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                status TEXT,
                total_files INTEGER,
                processed_files INTEGER,
                errors TEXT,
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS generated_sections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                section_id INTEGER,
                name TEXT,
                content TEXT,
                generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS custom_section_defs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                section_id INTEGER UNIQUE,
                name TEXT,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        ''')
        self.conn.commit()

    def save_repo_info(self, info):
        self.conn.execute('DELETE FROM repo_info')
        self.conn.execute(
            'INSERT INTO repo_info (name, full_name, description, language, topics, stars, forks, default_branch) VALUES (?,?,?,?,?,?,?,?)',
            (info['name'], info['full_name'], info.get('description', ''),
             info.get('language', ''), json.dumps(info.get('topics', [])),
             info.get('stars', 0), info.get('forks', 0), info.get('default_branch', 'main'))
        )
        self.conn.commit()

    def save_file(self, path, language, size, is_full_extract, metadata):
        cur = self.conn.execute(
            'INSERT OR REPLACE INTO files (path, language, size, is_full_extract, metadata) VALUES (?,?,?,?,?)',
            (path, language, size, 1 if is_full_extract else 0, json.dumps(metadata) if metadata else None)
        )
        self.conn.commit()
        return cur.lastrowid

    def save_code_blocks(self, file_id, blocks):
        for b in blocks:
            self.conn.execute(
                'INSERT INTO code_blocks (file_id, block_type, name, parent_name, start_line, end_line, content) VALUES (?,?,?,?,?,?,?)',
                (file_id, b.get('block_type'), b.get('name'), b.get('parent_name'), b.get('start_line'), b.get('end_line'), b.get('content'))
            )
        self.conn.commit()

    def save_commits(self, commits):
        self.conn.execute('DELETE FROM commits')
        for c in commits:
            self.conn.execute(
                'INSERT INTO commits (sha, message, author, date) VALUES (?,?,?,?)',
                (c['sha'], c['message'], c['author'], c['date'])
            )
        self.conn.commit()

    def start_extraction(self, total_files):
        cur = self.conn.execute(
            'INSERT INTO extraction_log (status, total_files, processed_files, errors) VALUES (?,?,?,?)',
            ('running', total_files, 0, '[]')
        )
        self.conn.commit()
        return cur.lastrowid

    def update_extraction(self, log_id, processed, errors=None):
        self.conn.execute(
            'UPDATE extraction_log SET processed_files=?, errors=? WHERE id=?',
            (processed, json.dumps(errors or []), log_id)
        )
        self.conn.commit()

    def complete_extraction(self, log_id):
        self.conn.execute(
            "UPDATE extraction_log SET status='completed', completed_at=CURRENT_TIMESTAMP WHERE id=?",
            (log_id,)
        )
        self.conn.commit()

    def fail_extraction(self, log_id, error):
        self.conn.execute(
            "UPDATE extraction_log SET status='failed', errors=?, completed_at=CURRENT_TIMESTAMP WHERE id=?",
            (json.dumps([error]), log_id)
        )
        self.conn.commit()

    def get_repo_info(self):
        row = self.conn.execute('SELECT * FROM repo_info LIMIT 1').fetchone()
        if row:
            return dict(row)
        return None

    def get_files(self):
        rows = self.conn.execute('SELECT * FROM files ORDER BY path').fetchall()
        return [dict(r) for r in rows]

    def get_commits(self):
        rows = self.conn.execute('SELECT * FROM commits ORDER BY date DESC').fetchall()
        return [dict(r) for r in rows]

    def get_extraction_status(self):
        row = self.conn.execute('SELECT * FROM extraction_log ORDER BY id DESC LIMIT 1').fetchone()
        if row:
            return dict(row)
        return None

    def get_code_blocks(self, file_id):
        rows = self.conn.execute('SELECT * FROM code_blocks WHERE file_id = ? ORDER BY start_line', (file_id,)).fetchall()
        return [dict(r) for r in rows]

    def save_generated_section(self, section_id, name, content):
        self.conn.execute(
            'DELETE FROM generated_sections WHERE section_id = ?', (section_id,)
        )
        self.conn.execute(
            'INSERT INTO generated_sections (section_id, name, content) VALUES (?,?,?)',
            (section_id, name, json.dumps(content) if isinstance(content, dict) else content)
        )
        self.conn.commit()

    def get_generated_section(self, section_id):
        row = self.conn.execute(
            'SELECT * FROM generated_sections WHERE section_id = ?', (section_id,)
        ).fetchone()
        if row:
            return dict(row)
        return None

    def get_generated_sections(self):
        rows = self.conn.execute('SELECT * FROM generated_sections ORDER BY section_id').fetchall()
        return [dict(r) for r in rows]

    def delete_generated_section(self, section_id):
        self.conn.execute('DELETE FROM generated_sections WHERE section_id = ?', (section_id,))
        self.conn.commit()

    def save_custom_section_def(self, section_id, name, description):
        self.conn.execute(
            'DELETE FROM custom_section_defs WHERE section_id = ?', (section_id,)
        )
        self.conn.execute(
            'INSERT INTO custom_section_defs (section_id, name, description) VALUES (?,?,?)',
            (section_id, name, description)
        )
        self.conn.commit()

    def get_custom_section_defs(self):
        rows = self.conn.execute('SELECT * FROM custom_section_defs ORDER BY section_id').fetchall()
        return [dict(r) for r in rows]

    def delete_custom_section_def(self, section_id):
        self.conn.execute('DELETE FROM custom_section_defs WHERE section_id = ?', (section_id,))
        self.conn.execute('DELETE FROM generated_sections WHERE section_id = ?', (section_id,))
        self.conn.commit()

    def close(self):
        self.conn.close()
