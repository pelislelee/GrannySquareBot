import hashlib
import hmac
import secrets
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

DB_PATH = Path(__file__).with_name('granny_square_bot.db')
PASSWORD_HASH_ITERATIONS = 600_000

@contextmanager
def _connection(db_path: Path | None = None) -> Generator[sqlite3.Connection, None, None]:
    if db_path is None:
        db_path = DB_PATH
    connection = sqlite3.connect(db_path)
    connection.execute('PRAGMA foreign_keys = ON')
    try:
        with connection:
            yield connection
    finally:
        connection.close()

def _hash_password(password: str, salt: bytes | None = None) -> str:
    salt = salt if salt is not None else secrets.token_bytes(16)
    password_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, PASSWORD_HASH_ITERATIONS)
    return f'{salt.hex()}:{password_hash.hex()}'

def _verify_password(password: str, stored_hash: str) -> bool:
    try:
        salt_hex, expected_hash = stored_hash.split(':', maxsplit=1)
        actual_hash = _hash_password(password, bytes.fromhex(salt_hex)).split(':', maxsplit=1)[1]
        return hmac.compare_digest(actual_hash, expected_hash)
    except (ValueError, TypeError):
        return False

def initialize_database(db_path: Path | None = None) -> None:
    with _connection(db_path) as connection:
        connection.executescript('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_name TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                is_hidden INTEGER NOT NULL DEFAULT 0,
                user_id INTEGER NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            );
            CREATE TABLE IF NOT EXISTS patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                image BLOB NOT NULL,
                pattern TEXT NOT NULL,
                project_id INTEGER NOT NULL,
                FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE CASCADE
            );
        ''')
        project_columns = {row[1] for row in connection.execute('PRAGMA table_info(projects)')}
        if 'is_hidden' not in project_columns:
            connection.execute('ALTER TABLE projects ADD COLUMN is_hidden INTEGER NOT NULL DEFAULT 0')

def username_exists(username: str, db_path: Path | None = None) -> bool:
    with _connection(db_path) as connection:
        return connection.execute('SELECT 1 FROM users WHERE username = ?', (username,)).fetchone() is not None

def register_user(username: str, password: str, db_path: Path | None = None) -> int | None:
    if not username or any(c.isspace() for c in username):
        raise ValueError('Username cannot be empty or contain spaces.')
    import re
    if (len(password) < 8 or not re.search(r'[A-Z]', password)
            or not re.search(r'[0-9]', password) or not re.search(r'[^\w\s]|_', password)):
        raise ValueError('Password must be at least 8 characters with an uppercase letter, number, and special character.')
    with _connection(db_path) as connection:
        try:
            cursor = connection.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)',
                                        (username, _hash_password(password)))
        except sqlite3.IntegrityError as exc:
            if 'users.username' in str(exc) or 'UNIQUE constraint failed' in str(exc):
                return None
            raise
        return int(cursor.lastrowid)

def authenticate_user(username: str, password: str, db_path: Path | None = None) -> int | None:
    with _connection(db_path) as connection:
        user = connection.execute('SELECT id, password_hash FROM users WHERE username = ?', (username,)).fetchone()
    if user is None or not _verify_password(password, user[1]):
        return None
    return int(user[0])


def create_project(
    user_id: int, project_name: str, db_path: Path | None = None
) -> tuple[int, str]:
    with _connection(db_path) as connection:
        cursor = connection.execute(
            "INSERT INTO projects (project_name, user_id) VALUES (?, ?)",
            (project_name, user_id),
        )
        project = connection.execute(
            "SELECT id, created_at FROM projects WHERE id = ?",
            (cursor.lastrowid,),
        ).fetchone()
        return int(project[0]), str(project[1])


def list_projects(
    user_id: int, db_path: Path | None = None
) -> list[tuple[int, str, str]]:
    with _connection(db_path) as connection:
        projects = connection.execute(
            """
            SELECT id, project_name, created_at
            FROM projects
            WHERE user_id = ? AND is_hidden = 0
            ORDER BY updated_at DESC, id DESC
            """,
            (user_id,),
        ).fetchall()
    return [(int(row[0]), str(row[1]), str(row[2])) for row in projects]


def hide_project(
    user_id: int, project_id: int, db_path: Path | None = None
) -> None:
    with _connection(db_path) as connection:
        cursor = connection.execute(
            """
            UPDATE projects
            SET is_hidden = 1
            WHERE id = ? AND user_id = ?
            """,
            (project_id, user_id),
        )
        if cursor.rowcount != 1:
            raise ValueError("Project does not exist or does not belong to this user.")


def list_patterns(
    project_id: int, db_path: Path | None = None
) -> list[tuple[bytes, str]]:
    with _connection(db_path) as connection:
        patterns = connection.execute(
            """
            SELECT image, pattern
            FROM patterns
            WHERE project_id = ?
            ORDER BY created_at, id
            """,
            (project_id,),
        ).fetchall()
    return [(bytes(row[0]), str(row[1])) for row in patterns]


def rename_project(
    user_id: int,
    project_id: int,
    project_name: str,
    db_path: Path | None = None,
) -> None:
    with _connection(db_path) as connection:
        cursor = connection.execute(
            """
            UPDATE projects
            SET project_name = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ? AND user_id = ?
            """,
            (project_name, project_id, user_id),
        )
        if cursor.rowcount != 1:
            raise ValueError("Project does not exist or does not belong to this user.")


def save_pattern(
    user_id: int,
    project_id: int,
    image: bytes,
    pattern: str,
    db_path: Path | None = None,
) -> None:
    with _connection(db_path) as connection:
        project = connection.execute(
            "SELECT 1 FROM projects WHERE id = ? AND user_id = ?",
            (project_id, user_id),
        ).fetchone()
        if project is None:
            raise ValueError("Project does not exist or does not belong to this user.")

        connection.execute(
            """
            INSERT INTO patterns (image, pattern, project_id)
            VALUES (?, ?, ?)
            """,
            (image, pattern, project_id),
        )
        connection.execute(
            "UPDATE projects SET updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (project_id,),
        )
