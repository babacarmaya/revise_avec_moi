import sqlite3
from werkzeug.security import generate_password_hash

def init_db():
    # Connexion à la base de données
    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    # Création de la table users
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            niveau TEXT NOT NULL,
            date_inscription DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Création de la table quiz
    c.execute('''
        CREATE TABLE IF NOT EXISTS quiz (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            matiere_id INTEGER,
            niveau TEXT NOT NULL,
            titre TEXT NOT NULL,
            difficulte INTEGER
        )
    ''')

    # Création de la table questions
    c.execute('''
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            quiz_id INTEGER,
            question TEXT NOT NULL,
            points INTEGER,
            FOREIGN KEY (quiz_id) REFERENCES quiz (id)
        )
    ''')

    # Création de la table reponses
    c.execute('''
        CREATE TABLE IF NOT EXISTS reponses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question_id INTEGER,
            reponse TEXT NOT NULL,
            est_correcte BOOLEAN,
            FOREIGN KEY (question_id) REFERENCES questions (id)
        )
    ''')

    # Création de la table resultats_quiz
    c.execute('''
        CREATE TABLE IF NOT EXISTS resultats_quiz (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            quiz_id INTEGER,
            score INTEGER,
            date_completion DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (quiz_id) REFERENCES quiz (id)
        )
    ''')

    # Sauvegarder les changements et fermer la connexion
    conn.commit()
    conn.close()

def get_db():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

# Fonction pour ajouter un utilisateur
def add_user(username, email, password, niveau):
    conn = get_db()
    c = conn.cursor()
    
    hashed_password = generate_password_hash(password)
    
    try:
        c.execute('''
            INSERT INTO users (username, email, password, niveau)
            VALUES (?, ?, ?, ?)
        ''', (username, email, hashed_password, niveau))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

# Fonction pour obtenir un utilisateur par email
def get_user_by_email(email):
    conn = get_db()
    c = conn.cursor()
    
    user = c.execute('''
        SELECT * FROM users WHERE email = ?
    ''', (email,)).fetchone()
    
    conn.close()
    return user

# Fonction pour obtenir un utilisateur par ID
def get_user_by_id(user_id):
    conn = get_db()
    c = conn.cursor()
    
    user = c.execute('''
        SELECT * FROM users WHERE id = ?
    ''', (user_id,)).fetchone()
    
    conn.close()
    return user
