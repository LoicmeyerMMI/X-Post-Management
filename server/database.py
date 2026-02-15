import sqlite3
import os
from datetime import datetime

from paths import DB_PATH


def get_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    conn = get_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT DEFAULT '',
            image_path TEXT DEFAULT '',
            scheduled_at TEXT,
            status TEXT DEFAULT 'draft' CHECK(status IN ('draft','scheduled','scheduling','scheduled_on_x','posting','posted','error')),
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            posted_at TEXT,
            error_message TEXT DEFAULT '',
            retries_count INTEGER DEFAULT 0,
            tweet_url TEXT DEFAULT ''
        )
    ''')
    conn.commit()

    # Migrate: add tweet_url column if missing
    try:
        cur = conn.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='posts'")
        row = cur.fetchone()
        if row and 'tweet_url' not in (row[0] or ''):
            conn.execute("ALTER TABLE posts ADD COLUMN tweet_url TEXT DEFAULT ''")
            conn.commit()
    except Exception:
        pass

    # Migrate: if the CHECK constraint is missing 'scheduling'/'scheduled_on_x', recreate the table
    try:
        cur = conn.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='posts'")
        row = cur.fetchone()
        if row and 'scheduling' not in (row[0] or ''):
            conn.executescript('''
                ALTER TABLE posts RENAME TO posts_old;
                CREATE TABLE posts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    text TEXT DEFAULT '',
                    image_path TEXT DEFAULT '',
                    scheduled_at TEXT,
                    status TEXT DEFAULT 'draft' CHECK(status IN ('draft','scheduled','scheduling','scheduled_on_x','posting','posted','error')),
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    posted_at TEXT,
                    error_message TEXT DEFAULT '',
                    retries_count INTEGER DEFAULT 0,
                    tweet_url TEXT DEFAULT ''
                );
                INSERT INTO posts (id, text, image_path, scheduled_at, status, created_at, updated_at, posted_at, error_message, retries_count)
                    SELECT id, text, image_path, scheduled_at, status, created_at, updated_at, posted_at, error_message, retries_count FROM posts_old;
                DROP TABLE posts_old;
            ''')
    except Exception:
        pass

    conn.execute('''
        CREATE TABLE IF NOT EXISTS followers_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            followers_count INTEGER DEFAULT 0,
            following_count INTEGER DEFAULT 0,
            recorded_at TEXT NOT NULL,
            username TEXT DEFAULT ''
        )
    ''')
    conn.commit()

    # Migrate: add username column to followers_history if missing
    try:
        cur = conn.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='followers_history'")
        row = cur.fetchone()
        if row and 'username' not in (row[0] or ''):
            conn.execute("ALTER TABLE followers_history ADD COLUMN username TEXT DEFAULT ''")
            conn.commit()
    except Exception:
        pass

    conn.close()


def _row_to_dict(row):
    if row is None:
        return None
    return dict(row)


def create_post(text='', image_path='', scheduled_at=None, status='draft'):
    now = datetime.now().isoformat()
    conn = get_connection()
    cur = conn.execute(
        '''INSERT INTO posts (text, image_path, scheduled_at, status, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?)''',
        (text, image_path, scheduled_at, status, now, now)
    )
    post_id = cur.lastrowid
    conn.commit()
    conn.close()
    return post_id


def get_post(post_id):
    conn = get_connection()
    row = conn.execute('SELECT * FROM posts WHERE id = ?', (post_id,)).fetchone()
    conn.close()
    return _row_to_dict(row)


def get_posts_by_status(status):
    conn = get_connection()
    rows = conn.execute(
        'SELECT * FROM posts WHERE status = ? ORDER BY created_at DESC', (status,)
    ).fetchall()
    conn.close()
    return [_row_to_dict(r) for r in rows]


def get_pending_scheduled():
    """Get posts with status 'scheduled' that need to be sent to X for native scheduling."""
    conn = get_connection()
    rows = conn.execute(
        '''SELECT * FROM posts
           WHERE status = 'scheduled'
           ORDER BY scheduled_at ASC'''
    ).fetchall()
    conn.close()
    return [_row_to_dict(r) for r in rows]


def get_all_posts():
    conn = get_connection()
    rows = conn.execute('SELECT * FROM posts ORDER BY created_at DESC').fetchall()
    conn.close()
    return [_row_to_dict(r) for r in rows]


def update_post(post_id, **kwargs):
    allowed = {'text', 'image_path', 'scheduled_at', 'status', 'error_message', 'retries_count', 'posted_at', 'tweet_url'}
    fields = {k: v for k, v in kwargs.items() if k in allowed}
    if not fields:
        return False
    fields['updated_at'] = datetime.now().isoformat()
    set_clause = ', '.join(f'{k} = ?' for k in fields)
    values = list(fields.values()) + [post_id]
    conn = get_connection()
    conn.execute(f'UPDATE posts SET {set_clause} WHERE id = ?', values)
    conn.commit()
    conn.close()
    return True


def update_post_status(post_id, status, error_message=None):
    kwargs = {'status': status}
    if error_message is not None:
        kwargs['error_message'] = error_message
    if status == 'posted':
        kwargs['posted_at'] = datetime.now().isoformat()
    return update_post(post_id, **kwargs)


def delete_post(post_id):
    conn = get_connection()
    conn.execute('DELETE FROM posts WHERE id = ?', (post_id,))
    conn.commit()
    conn.close()
    return True


def add_follower_snapshot(followers_count, following_count, username=''):
    now = datetime.now().isoformat()
    conn = get_connection()
    conn.execute(
        'INSERT INTO followers_history (followers_count, following_count, recorded_at, username) VALUES (?, ?, ?, ?)',
        (followers_count, following_count, now, username)
    )
    conn.commit()
    conn.close()


def get_follower_history(username=None):
    conn = get_connection()
    if username:
        rows = conn.execute(
            'SELECT * FROM followers_history WHERE username = ? ORDER BY recorded_at ASC',
            (username,)
        ).fetchall()
    else:
        rows = conn.execute(
            'SELECT * FROM followers_history ORDER BY recorded_at ASC'
        ).fetchall()
    conn.close()
    return [_row_to_dict(r) for r in rows]
