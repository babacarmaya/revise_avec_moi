from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime

# Création de l'application Flask
app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = 'votre_clé_secrète'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///education.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Modèles de base de données
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    prenom = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    telephone = db.Column(db.String(20))
    niveau = db.Column(db.String(20), nullable=False)
    password = db.Column(db.String(200), nullable=False)
    age = db.Column(db.Integer)
    date_inscription = db.Column(db.DateTime, default=datetime.utcnow)
    # Relations
    quiz_results = db.relationship('QuizResult', backref='user', lazy=True)
    badges = db.relationship('Badge', secondary='user_badges', backref='users', lazy=True)
    events = db.relationship('Event', backref='user', lazy=True)

class Quiz(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    titre = db.Column(db.String(100), nullable=False)
    matiere = db.Column(db.String(50), nullable=False)
    niveau = db.Column(db.String(20), nullable=False)
    difficulte = db.Column(db.Integer, nullable=False)
    # Relations
    questions = db.relationship('Question', backref='quiz', lazy=True)
    results = db.relationship('QuizResult', backref='quiz', lazy=True)

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False)
    question = db.Column(db.Text, nullable=False)
    points = db.Column(db.Integer, default=1)
    # Relations
    reponses = db.relationship('Reponse', backref='question', lazy=True)

class Reponse(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)
    reponse = db.Column(db.Text, nullable=False)
    est_correcte = db.Column(db.Boolean, default=False)

class QuizResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    date_completion = db.Column(db.DateTime, default=datetime.utcnow)

class Badge(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text)
    image_url = db.Column(db.String(200))

# Table d'association pour les badges des utilisateurs
user_badges = db.Table('user_badges',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('badge_id', db.Integer, db.ForeignKey('badge.id'), primary_key=True),
    db.Column('date_obtention', db.DateTime, default=datetime.utcnow)
)

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    titre = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    date_debut = db.Column(db.DateTime, nullable=False)
    date_fin = db.Column(db.DateTime, nullable=False)
    type = db.Column(db.String(50))

# Protection des routes
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Routes pour l'authentification
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['niveau'] = user.niveau
            flash('Connexion réussie !', 'success')
            return redirect(url_for('home'))
        flash('Email ou mot de passe incorrect', 'error')
    return render_template('auth/login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        nom = request.form.get('nom')
        prenom = request.form.get('prenom')
        email = request.form.get('email')
        telephone = request.form.get('telephone')
        niveau = request.form.get('niveau')
        password = request.form.get('password')
        age = request.form.get('age')

        if User.query.filter_by(email=email).first():
            flash('Email déjà utilisé', 'error')
            return redirect(url_for('register'))

        hashed_password = generate_password_hash(password)
        new_user = User(
            nom=nom, 
            prenom=prenom, 
            email=email, 
            telephone=telephone, 
            niveau=niveau, 
            password=hashed_password, 
            age=age
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        flash('Inscription réussie !', 'success')
        return redirect(url_for('login'))
    return render_template('auth/register.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Vous avez été déconnecté', 'info')
    return redirect(url_for('login'))

# Routes principales
@app.route('/')
@login_required
def home():
    user = User.query.get(session['user_id'])
    return render_template('home.html', user=user)

# Routes pour les niveaux
@app.route('/seconde')
@login_required
def seconde():
    return render_template('niveaux/seconde.html')

@app.route('/premiere')
@login_required
def premiere():
    return render_template('niveaux/premiere.html')

@app.route('/terminale')
@login_required
def terminale():
    return render_template('niveaux/terminale.html')

# Route pour les cours
@app.route('/cours/<niveau>/<matiere>')
@login_required
def cours(niveau, matiere):
    return render_template(f'cours/{matiere}/{niveau}.html')

@app.route('/profile')
@login_required
def profile():
    user = User.query.get(session['user_id'])
    quiz_results = QuizResult.query.filter_by(user_id=user.id).order_by(QuizResult.date_completion.desc()).all()
    
    # Calculer les statistiques
    total_quizzes = len(quiz_results)
    average_score = sum(result.score for result in quiz_results) / total_quizzes if total_quizzes > 0 else 0
    
    # Obtenir les derniers résultats
    recent_results = quiz_results[:5]  # 5 derniers résultats
    
    return render_template('profile.html', 
                         user=user,
                         total_quizzes=total_quizzes,
                         average_score=average_score,
                         recent_results=recent_results)


 ########################################## Matiere terminale
@app.route('/cours/philo/terminale')
@login_required
def philo_terminale():
    return render_template('cours/philo/philo_terminal.html')  # Assurez-vous que ce chemin est correct

@app.route('/cours/philo/chapitre1')
@login_required
def philo_chapitre1():
    return render_template('cours/philo/chapitre1._terminal.html')


@app.route('/cours/mathematiques/terminale')
@login_required
def mathematiques_terminale():
    return render_template('cours/maths/maths_terminal.html')

@app.route('/cours/histoire/terminale')
@login_required
def histoire_terminale():
    return render_template('cours/histoire/histoire_terminal.html')

@app.route('/cours/histoire/chapitre1')
@login_required
def histoire_chapitre1():
    return render_template('cours/histoire/chapitre1._terminal.html')

#type de commentaires
@app.route('/cours/histoire/chapitre2')
@login_required
def histoire_chapitre2():
    return render_template('cours/histoire/chapitre2._terminal.html')

@app.route('/cours/anglais/terminale')
@login_required
def anglais_terminale():
    return render_template('cours/anglais/anglais_terminal.html')

@app.route('/cours/Anglais/chapitre1')
@login_required
def anglais_chapitre1():
    return render_template('cours/anglais/chapitre1._terminal.html')


@app.route('/cours/physique-chimie/terminale')
@login_required
def physique_chimie_terminale():
    return render_template('cours/physique-chimie/physique_chimie_terminal.html')

@app.route('/cours/svt/terminale')
@login_required
def svt_terminale():
    if session.get('niveau') != 'terminale':
        flash("Vous n'avez pas accès à ce contenu.", 'error')
        return redirect(url_for('home'))
    return render_template('cours/svt/svt_terminal.html')



class CourseContent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    subject = db.Column(db.String(50))  # philo, maths, etc.
    chapter_number = db.Column(db.String(10))  # "1.1", "1.2", etc.
    title = db.Column(db.String(200))
    content = db.Column(db.Text)
    is_locked = db.Column(db.Boolean, default=True)

@app.route('/cours/<subject>/chapitre/<chapter_number>')
@login_required
def view_chapter(subject, chapter_number):
    chapter = CourseContent.query.filter_by(
        subject=subject,
        chapter_number=chapter_number
    ).first_or_404()
    
    return render_template('cours/chapter_content.html', 
                         chapter=chapter,
                         subject=subject)








   ######### # Route pour voir tous les utilisateurs inscrits
@app.route('/test/users')
@login_required  # Ajoute la protection de la route
def test_users():
    try:
        # Récupère tous les utilisateurs de la base de données
        users = User.query.all()
        return render_template('test_users.html', users=users)
    except Exception as e:
        flash(f"Erreur: {str(e)}", "error")
        return redirect(url_for('home'))

# Route pour tester la connexion à la base de données
@app.route('/test/db')
def test_db():
    try:
        # Compte le nombre d'utilisateurs
        users_count = User.query.count()
        return f"La base de données fonctionne ! Il y a {users_count} utilisateurs inscrits."
    
    except Exception as e:
        return f"Erreur de connexion à la base de données : {str(e)}"
    

# Initialisation de la base de données
with app.app_context():
    db.create_all()

# Lancement de l'application
if __name__ == '__main__':
    app.run(debug=True)
