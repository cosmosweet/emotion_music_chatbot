from datetime import datetime
import sqlite3
import hashlib
import json

def init_db(db_name='user_info.db'):
    conn = sqlite3.connect(db_name)
    c = conn.cursor()

    # 사용자 정보 테이블
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            password_hash TEXT NOT NULL,
            nickname TEXT NOT NULL
        )
    ''')

    # 감정 이력 테이블 (날짜, 감정, 카운트)
    c.execute('''
        CREATE TABLE IF NOT EXISTS user_emotions (
            user_id TEXT,
            date TEXT,
            emotion TEXT,
            count INTEGER DEFAULT 0,
            PRIMARY KEY (user_id, date, emotion)
        )
    ''')

    # 메시지 리스트 저장 테이블
    c.execute('''
        CREATE TABLE IF NOT EXISTS user_messages (
            user_id TEXT PRIMARY KEY,
            messages TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    conn.commit()
    conn.close()

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def register_user(user_id: str, password: str, nickname: str, db_name='user_info.db') -> bool:
    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    try:
        c.execute(
            'INSERT INTO users (id, password_hash, nickname) VALUES (?, ?, ?)',
            (user_id, hash_password(password), nickname)
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def login_user(user_id: str, password: str, db_name='user_info.db') -> tuple[bool, str]:
    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    c.execute('SELECT password_hash, nickname FROM users WHERE id = ?', (user_id,))
    row = c.fetchone()
    conn.close()
    if row is None:
        return False, ""
    return (hash_password(password) == row[0], row[1])

def save_user_messages(user_id: str, message_list: list[str], db_name='user_info.db') -> None:
    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    messages_json = json.dumps(message_list)

    c.execute('''
        INSERT INTO user_messages (user_id, messages, updated_at)
        VALUES (?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            messages = excluded.messages,
            updated_at = excluded.updated_at
    ''', (user_id, messages_json, datetime.now()))
    
    conn.commit()
    conn.close()

def get_user_messages(user_id: str, db_name='user_info.db') -> list[str]:
    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    c.execute('SELECT messages FROM user_messages WHERE user_id = ?', (user_id,))
    row = c.fetchone()
    conn.close()
    if row is None:
        return []
    return json.loads(row[0])

def save_emotion_for_user(user_id: str, emotion: str, db_name='user_info.db') -> None:
    today = datetime.now().strftime("%Y-%m-%d")
    conn = sqlite3.connect(db_name)
    c = conn.cursor()

    c.execute('''
        INSERT INTO user_emotions (user_id, date, emotion, count)
        VALUES (?, ?, ?, 1)
        ON CONFLICT(user_id, date, emotion) DO UPDATE SET
            count = count + 1
    ''', (user_id, today, emotion))

    conn.commit()
    conn.close()

def get_user_emotion_history(user_id: str, db_name='user_info.db') -> dict:
    conn = sqlite3.connect(db_name)
    c = conn.cursor()

    c.execute('''
        SELECT date, emotion, count
        FROM user_emotions
        WHERE user_id = ?
    ''', (user_id,))
    
    rows = c.fetchall()
    conn.close()

    history = {}
    for date, emotion, count in rows:
        history.setdefault(date, {})[emotion] = count
    return history