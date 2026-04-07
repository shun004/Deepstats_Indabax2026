"""
AirEka — Gestion des utilisateurs
Base de données SQLite pour l'authentification
"""

import sqlite3
import hashlib
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), 'users.db')

def init_db():
    """Initialise la base de données des utilisateurs (si elle n'existe pas)."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL,
            city TEXT,
            region TEXT,
            created_at TEXT NOT NULL,
            last_login TEXT
        )
    ''')
    
    conn.commit()
    conn.close()
    print(f"[Auth] Base de données initialisée: {DB_PATH}")

def hash_password(password):
    """Hache un mot de passe avec SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()

def create_user(name, email, password, role, city=None, region=None):
    """Crée un nouvel utilisateur."""
    # S'assurer que la base existe
    init_db()
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        password_hash = hash_password(password)
        created_at = datetime.now().isoformat()
        
        cursor.execute('''
            INSERT INTO users (name, email, password_hash, role, city, region, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (name, email, password_hash, role, city, region, created_at))
        
        conn.commit()
        user_id = cursor.lastrowid
        conn.close()
        return {'success': True, 'user_id': user_id}
    except sqlite3.IntegrityError as e:
        conn.close()
        if "UNIQUE constraint failed: users.email" in str(e):
            return {'success': False, 'error': 'Cet email est déjà utilisé'}
        return {'success': False, 'error': 'Erreur lors de la création du compte'}
    except Exception as e:
        conn.close()
        return {'success': False, 'error': f'Erreur: {str(e)}'}

def authenticate_user(email, password):
    """Authentifie un utilisateur."""
    # S'assurer que la base existe
    init_db()
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    password_hash = hash_password(password)
    
    cursor.execute('''
        SELECT id, name, email, role, city, region FROM users
        WHERE email = ? AND password_hash = ?
    ''', (email, password_hash))
    
    user = cursor.fetchone()
    conn.close()
    
    if user:
        # Mettre à jour la date de dernière connexion
        update_last_login(user[0])
        return {
            'success': True,
            'user_id': user[0],
            'name': user[1],
            'email': user[2],
            'role': user[3],
            'city': user[4],
            'region': user[5]
        }
    return {'success': False, 'error': 'Email ou mot de passe incorrect'}

def update_last_login(user_id):
    """Met à jour la date de dernière connexion."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET last_login = ? WHERE id = ?', 
                   (datetime.now().isoformat(), user_id))
    conn.commit()
    conn.close()

def get_user_by_email(email):
    """Récupère un utilisateur par son email."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT id, name, email, role, city, region FROM users WHERE email = ?', (email,))
    user = cursor.fetchone()
    conn.close()
    return user

def user_exists(email):
    """Vérifie si un utilisateur existe."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT 1 FROM users WHERE email = ?', (email,))
    exists = cursor.fetchone() is not None
    conn.close()
    return exists

def delete_all_users():
    """Supprime tous les utilisateurs (pour debug)."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM users')
    conn.commit()
    conn.close()
    print("[Auth] Tous les utilisateurs ont été supprimés")