from platformdirs import user_data_dir
from pathlib import Path
import sqlite3

APP_NAME = "SalaryTracker"
APP_AUTHOR = "SalaryAuthor"

data_dir = Path(user_data_dir(APP_NAME, APP_AUTHOR))
data_dir.mkdir(parents=True, exist_ok=True)


DATABASE_PATH = data_dir / "salary.db"

class Database:
    def __init__(self, db_path=DATABASE_PATH):
        self.db = sqlite3.connect(db_path)
        self.cursor = self.db.cursor()
        self._create_table()
        self._create_settings_table()

    def _create_table(self):
        query = """
            CREATE TABLE IF NOT EXISTS salaries(
                id INTEGER PRIMARY KEY,
                data TEXT,
                salary REAL,
                advance REAL,
                sum REAL
            );
        """
        self._run_query(query)

    def _create_settings_table(self):
            query = """
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT
                );
            """
            self._run_query(query)
    
    def _run_query(self, query, *args_query):
        result = self.cursor.execute(query,
        [*args_query])
        self.db.commit()
        return result
    
    def get_organization_name(self):
        row = self.cursor.execute(
            "SELECT value FROM settings WHERE key = 'org_name'"
        ).fetchone()
        return row[0] if row else None

    def set_organization_name(self, name: str):
        self._run_query("""
            INSERT OR REPLACE INTO settings (key, value) VALUES ('org_name', ?)
        """, name.strip())
    
    def get_start_date(self):
        row = self.cursor.execute(
            "SELECT value FROM settings WHERE key = 'start_date'"
        ).fetchone()
        return row[0] if row else None

    def set_start_date(self, date: str):
        self._run_query("""
            INSERT OR REPLACE INTO settings (key, value) VALUES ('start_date', ?)
        """, date.strip() if date else None)

    def get_end_date(self):
        row = self.cursor.execute(
            "SELECT value FROM settings WHERE key = 'end_date'"
        ).fetchone()
        return row[0] if row else None

    def set_end_date(self, date: str):
        self._run_query("""
            INSERT OR REPLACE INTO settings (key, value) VALUES ('end_date', ?)
        """, date.strip() if date else None)

    def get_all_financess(self):
        result = self._run_query("SELECT * FROM salaries;")
        return result.fetchall()
    
    def get_last_financess(self):
        result = self._run_query("SELECT * FROM salaries ORDER BY id DESC LIMIT 1")
        return result.fetchone()
    
    def add_financess(self, salary):
        self._run_query("INSERT INTO salaries VALUES (NULL, ?,?,?,?)", *salary)
    
    def delete_financess(self, id):
        self._run_query("DELETE FROM salaries WHERE id=(?)", id)
    
    def update_financess(self, id, data, salary, advance, sum):
        query = """
            UPDATE salaries 
            SET data = ?, salary = ?, advance = ?, sum = ? 
            WHERE id = ?
        """
        self._run_query(query, data, salary, advance, sum, id)
        
