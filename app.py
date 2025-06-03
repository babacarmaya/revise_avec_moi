from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime, timedelta
from flask_migrate import Migrate


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
    # Relation avec CalendarEvent définie dans le modèle CalendarEvent

class CalendarEvent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    color = db.Column(db.String(20), default='#3498db')  # Couleur de l'événement
    type = db.Column(db.String(20), default='other')  # cours, exercice, examen, rappel, etc.
    completed = db.Column(db.Boolean, default=False)
    reminder = db.Column(db.Boolean, default=False)
    reminder_time = db.Column(db.DateTime)
    
    # Relation avec l'utilisateur
    user = db.relationship('User', backref=db.backref('calendar_events', lazy=True, cascade="all, delete-orphan"))

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

class CourseContent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    subject = db.Column(db.String(50))  # philo, maths, etc.
    chapter_number = db.Column(db.String(10))  # "1.1", "1.2", etc.
    title = db.Column(db.String(200))
    content = db.Column(db.Text)
    is_locked = db.Column(db.Boolean, default=True)

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
            flash('thia kaw ; thia kanam !', 'success')
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
        
        flash('aythia niou dem !', 'success')
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

@app.route('/update_profile', methods=['POST'])
@login_required
def update_profile():
    if request.method == 'POST':
        user = User.query.get(session['user_id'])
        
        # Récupérer les données du formulaire
        prenom = request.form.get('prenom')
        nom = request.form.get('nom')
        email = request.form.get('email')
        niveau = request.form.get('niveau')
        telephone = request.form.get('telephone', user.telephone)
        age = request.form.get('age')
        if age:
            try:
                age = int(age)
            except ValueError:
                age = user.age
        else:
            age = user.age
        
        # Vérifier si l'email est déjà utilisé par un autre utilisateur
        existing_user = User.query.filter_by(email=email).first()
        if existing_user and existing_user.id != user.id:
            flash('Cet email est déjà utilisé par un autre compte', 'error')
            return redirect(url_for('profile'))
        
        # Mettre à jour les informations personnelles
        user.prenom = prenom
        user.nom = nom
        user.email = email
        user.niveau = niveau
        user.telephone = telephone
        user.age = age
        
        # Mettre à jour la session si le niveau a changé
        if session['niveau'] != niveau:
            session['niveau'] = niveau
        
        # Vérifier si le mot de passe doit être mis à jour
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        
        if current_password and new_password:
            # Vérifier que le mot de passe actuel est correct
            if check_password_hash(user.password, current_password):
                # Mettre à jour le mot de passe
                user.password = generate_password_hash(new_password)
                flash('Votre mot de passe a été mis à jour', 'success')
            else:
                flash('Le mot de passe actuel est incorrect', 'error')
                return redirect(url_for('profile'))
        
        # Sauvegarder les modifications
        try:
            db.session.commit()
            flash('Votre profil a été mis à jour avec succès', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Une erreur est survenue: {str(e)}', 'error')
        
    return redirect(url_for('profile'))

@app.route('/calendar')
@login_required
def calendar():
    user = User.query.get(session['user_id'])
    return render_template('calendar.html', user=user)

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

# Routes API pour le calendrier
@app.route('/api/events', methods=['GET'])
@login_required
def get_events():
    user_id = session['user_id']
    start = request.args.get('start', '')
    end = request.args.get('end', '')
    
    # Convertir les dates de chaîne ISO à objets datetime
    if start and end:
        start_date = datetime.fromisoformat(start.replace('Z', '+00:00'))
        end_date = datetime.fromisoformat(end.replace('Z', '+00:00'))
        
        events = CalendarEvent.query.filter(
            CalendarEvent.user_id == user_id,
            CalendarEvent.start_date >= start_date,
            CalendarEvent.end_date <= end_date
        ).all()
    else:
        events = CalendarEvent.query.filter_by(user_id=user_id).all()
    
    # Formater les événements pour FullCalendar
    events_data = []
    for event in events:
        events_data.append({
            'id': event.id,
            'title': event.title,
            'description': event.description,
            'start': event.start_date.isoformat(),
            'end': event.end_date.isoformat(),
            'color': event.color,
            'extendedProps': {
                'type': event.type,
                'completed': event.completed,
                'reminder': event.reminder,
                'reminder_time': event.reminder_time.isoformat() if event.reminder_time else None
            }
        })
    
    return jsonify(events_data)

@app.route('/api/events', methods=['POST'])
@login_required
def create_event():
    user_id = session['user_id']
    data = request.json
    
    # Convertir les dates de chaîne ISO à objets datetime
    start_date = datetime.fromisoformat(data['start'].replace('Z', '+00:00'))
    end_date = datetime.fromisoformat(data['end'].replace('Z', '+00:00'))
    
    # Créer un nouvel événement
    new_event = CalendarEvent(
        user_id=user_id,
        title=data['title'],
                description=data.get('description', ''),
        start_date=start_date,
        end_date=end_date,
        color=data.get('color', '#3498db'),
        type=data.get('type', 'other'),
        reminder=data.get('reminder', False)
    )
    
    # Ajouter un rappel si demandé
    if data.get('reminder'):
        reminder_minutes = int(data.get('reminder_minutes', 30))
        reminder_time = start_date - timedelta(minutes=reminder_minutes)
        new_event.reminder_time = reminder_time
    
    db.session.add(new_event)
    
    try:
        db.session.commit()
        return jsonify({
            'status': 'success',
            'id': new_event.id,
            'message': 'Événement créé avec succès'
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/events/<int:event_id>', methods=['PUT'])
@login_required
def update_event(event_id):
    user_id = session['user_id']
    data = request.json
    
    # Trouver l'événement
    event = CalendarEvent.query.filter_by(id=event_id, user_id=user_id).first()
    
    if not event:
        return jsonify({
            'status': 'error',
            'message': 'Événement non trouvé'
        }), 404
    
    # Mettre à jour les champs
    if 'title' in data:
        event.title = data['title']
    if 'description' in data:
        event.description = data['description']
    if 'start' in data:
        event.start_date = datetime.fromisoformat(data['start'].replace('Z', '+00:00'))
    if 'end' in data:
        event.end_date = datetime.fromisoformat(data['end'].replace('Z', '+00:00'))
    if 'color' in data:
        event.color = data['color']
    if 'type' in data:
        event.type = data['type']
    if 'completed' in data:
        event.completed = data['completed']
    if 'reminder' in data:
        event.reminder = data['reminder']
        
        if data['reminder']:
            reminder_minutes = int(data.get('reminder_minutes', 30))
            reminder_time = event.start_date - timedelta(minutes=reminder_minutes)
            event.reminder_time = reminder_time
        else:
            event.reminder_time = None
    
    try:
        db.session.commit()
        return jsonify({
            'status': 'success',
            'message': 'Événement mis à jour avec succès'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/events/<int:event_id>', methods=['DELETE'])
@login_required
def delete_event(event_id):
    user_id = session['user_id']
    
    # Trouver l'événement
    event = CalendarEvent.query.filter_by(id=event_id, user_id=user_id).first()
    
    if not event:
        return jsonify({
            'status': 'error',
            'message': 'Événement non trouvé'
        }), 404
    
    db.session.delete(event)
    
    try:
        db.session.commit()
        return jsonify({
            'status': 'success',
            'message': 'Événement supprimé avec succès'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/events/complete/<int:event_id>', methods=['PUT'])
@login_required
def complete_event(event_id):
    user_id = session['user_id']
    
    # Trouver l'événement
    event = CalendarEvent.query.filter_by(id=event_id, user_id=user_id).first()
    
    if not event:
        return jsonify({
            'status': 'error',
            'message': 'Événement non trouvé'
        }), 404
    
    # Inverser l'état de complétion
    event.completed = not event.completed
    
    try:
        db.session.commit()
        return jsonify({
            'status': 'success',
            'completed': event.completed,
            'message': f'Événement marqué comme {"complété" if event.completed else "non complété"}'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

# Routes pour les matières de terminale
# PHILO
@app.route('/cours/philo/terminale')
@login_required
def philo_terminale():
    return render_template('cours/philo/philo_terminal.html')  # Assurez-vous que ce chemin est correct

@app.route('/cours/philo/chapitre1')
@login_required
def philo_chapitre1():
    return render_template('cours/philo/chapitre1._terminal.html')

@app.route('/cours/philo/chapitre2')
@login_required
def philo_chapitre2():
    return render_template('cours/philo/chapitre2._terminal.html')

@app.route('/cours/philo/chapitre3')
@login_required
def philo_chapitre3():
    return render_template('cours/philo/chapitre3._terminal.html')

@app.route('/cours/philo/chapitre4')
@login_required
def philo_chapitre4():
    return render_template('cours/philo/chapitre4._terminal.html')

@app.route('/cours/philo/chapitre5')
@login_required
def philo_chapitre5():
    return render_template('cours/philo/chapitre5._terminal.html')

@app.route('/cours/philo/chapitre6')
@login_required
def philo_chapitre6():
    return render_template('cours/philo/chapitre6._terminal.html')

@app.route('/cours/philo/chapitre7')
@login_required
def philo_chapitre7():
    return render_template('cours/philo/chapitre7._terminal.html')

@app.route('/cours/philo/chapitre8')
@login_required
def philo_chapitre8():
    return render_template('cours/philo/chapitre8._terminal.html')

@app.route('/cours/philo/premiere')
@login_required
def philo_premiere():
    return render_template('cours/philo/philo_premiere.html')

@app.route('/cours/philo/seconde')
@login_required
def philo_seconde():
    return render_template('cours/philo/philo_seconde.html')

# Mathématiques
@app.route('/cours/mathematiques/terminale')
@login_required
def mathematiques_terminale():
    return render_template('cours/maths/maths_terminal.html')

@app.route('/cours/maths/chapitre1')
@login_required
def mathematiques_chapitre1():
    return render_template('cours/maths/chapitre1._terminal.html')

@app.route('/cours/maths/chapitre2')
@login_required
def mathematiques_chapitre2():
    return render_template('cours/maths/chapitre2._terminal.html')

@app.route('/cours/maths/chapitre3')
@login_required
def mathematiques_chapitre3():
    return render_template('cours/maths/chapitre3._terminal.html')

@app.route('/cours/maths/chapitre4')
@login_required
def mathematiques_chapitre4():
    return render_template('cours/maths/chapitre4._terminal.html')

@app.route('/cours/maths/chapitre5')
@login_required
def mathematiques_chapitre5():
    return render_template('cours/maths/chapitre5._terminal.html')

@app.route('/cours/maths/chapitre6')
@login_required
def mathematiques_chapitre6():
    return render_template('cours/maths/chapitre6._terminal.html')

@app.route('/cours/maths/chapitre7')
@login_required
def mathematiques_chapitre7():
    return render_template('cours/maths/chapitre7._terminal.html')

@app.route('/cours/maths/chapitre8')
@login_required
def mathematiques_chapitre8():
    return render_template('cours/maths/chapitre8._terminal.html')

@app.route('/cours/mathematiques/premiere')
@login_required
def mathematiques_premiere():
    return render_template('cours/maths/maths_premiere.html')

@app.route('/cours/mathematiques/seconde')
@login_required
def mathematiques_seconde():
    return render_template('cours/maths/maths_seconde.html')

# Histoire
@app.route('/cours/histoire/terminale')
@login_required
def histoire_terminale():
    return render_template('cours/histoire/histoire_terminal.html')

@app.route('/cours/histoire/chapitre1')
@login_required
def histoire_chapitre1():
    return render_template('cours/histoire/chapitre1._terminal.html')

@app.route('/cours/histoire/chapitre2')
@login_required
def histoire_chapitre2():
    return render_template('cours/histoire/chapitre2._terminal.html')

@app.route('/cours/histoire/chapitre3')
@login_required
def histoire_chapitre3():
    return render_template('cours/histoire/chapitre3._terminal.html')

@app.route('/cours/histoire/chapitre4')
@login_required
def histoire_chapitre4():
    return render_template('cours/histoire/chapitre4._terminal.html')

@app.route('/cours/histoire/chapitre5')
@login_required
def histoire_chapitre5():
    return render_template('cours/histoire/chapitre5._terminal.html')

@app.route('/cours/histoire/chapitre6')
@login_required
def histoire_chapitre6():
    return render_template('cours/histoire/chapitre6._terminal.html')

@app.route('/cours/histoire/chapitre7')
@login_required
def histoire_chapitre7():
    return render_template('cours/histoire/chapitre7._terminal.html')

@app.route('/cours/histoire/chapitre8')
@login_required
def histoire_chapitre8():
    return render_template('cours/histoire/chapitre8._terminal.html')

@app.route('/cours/histoire/premiere')
@login_required
def histoire_premiere():
    return render_template('cours/histoire/histoire_premiere.html')

@app.route('/cours/histoire/seconde')
@login_required
def histoire_seconde():
    return render_template('cours/histoire/histoire_seconde.html')

# Anglais 
@app.route('/cours/anglais/terminale')
@login_required
def anglais_terminale():
    return render_template('cours/anglais/anglais_terminal.html')

@app.route('/cours/Anglais/chapitre1')
@login_required
def anglais_chapitre1():
    return render_template('cours/anglais/chapitre1._terminal.html')

@app.route('/cours/Anglais/chapitre2')
@login_required
def anglais_chapitre2():
    return render_template('cours/anglais/chapitre2._terminal.html')

@app.route('/cours/Anglais/chapitre3')
@login_required
def anglais_chapitre3():
    return render_template('cours/anglais/chapitre3._terminal.html')

@app.route('/cours/Anglais/chapitre4')
@login_required
def anglais_chapitre4():
    return render_template('cours/anglais/chapitre4._terminal.html')

@app.route('/cours/Anglais/chapitre5')
@login_required
def anglais_chapitre5():
    return render_template('cours/anglais/chapitre5._terminal.html')

@app.route('/cours/Anglais/chapitre6')
@login_required
def anglais_chapitre6():
    return render_template('cours/anglais/chapitre6._terminal.html')

@app.route('/cours/Anglais/chapitre7')
@login_required
def anglais_chapitre7():
    return render_template('cours/anglais/chapitre7._terminal.html')

@app.route('/cours/Anglais/chapitre8')
@login_required
def anglais_chapitre8():
    return render_template('cours/anglais/chapitre8._terminal.html')

@app.route('/cours/anglais/premiere')
@login_required
def anglais_premiere():
    return render_template('cours/anglais/anglais_premiere.html')

@app.route('/cours/anglais/seconde')
@login_required
def anglais_seconde():
    return render_template('cours/anglais/anglais_seconde.html')



# SVT
@app.route('/cours/svt/terminale')
@login_required
def svt_terminale():
    return render_template('cours/svt/svt_terminal.html')

@app.route('/cours/svt/chapitre1')
@login_required
def svt_chapitre1():
    return render_template('cours/svt/chapitre1._terminal.html')

@app.route('/cours/svt/chapitre2')
@login_required
def svt_chapitre2():
    return render_template('cours/svt/chapitre2._terminal.html')

@app.route('/cours/svt/chapitre3')
@login_required
def svt_chapitre3():
    return render_template('cours/svt/chapitre3._terminal.html')

@app.route('/cours/svt/premiere')
@login_required
def svt_premiere():
    return render_template('cours/svt/svt_premiere.html')

@app.route('/cours/svt/seconde')
@login_required
def svt_seconde():
    return render_template('cours/svt/svt_seconde.html')

# Physique-Chimie
@app.route('/cours/physique-chimie/terminale')
@login_required
def physique_chimie_terminale():
    return render_template('cours/physique-chimie/physique_chimie_terminal.html')

@app.route('/cours/physique-chimie/chapitre1')
@login_required
def PC_chapitre1():
    return render_template('cours/physique-chimie/chapitre1._terminal.html')

@app.route('/cours/physique-chimie/chapitre2')
@login_required
def PC_chapitre2():
    return render_template('cours/physique-chimie/chapitre2._terminal.html')

@app.route('/cours/physique-chimie/chapitre3')
@login_required
def PC_chapitre3():
    return render_template('cours/physique-chimie/chapitre3._terminal.html')

@app.route('/cours/physique-chimie/chapitre4')
@login_required
def PC_chapitre4():
    return render_template('cours/physique-chimie/chapitre4._terminal.html')

@app.route('/cours/physique-chimie/chapitre5')
@login_required
def PC_chapitre5():
    return render_template('cours/physique-chimie/chapitre5._terminal.html')

@app.route('/cours/physique-chimie/chapitre6')
@login_required
def PC_chapitre6():
    return render_template('cours/physique-chimie/chapitre6._terminal.html')

@app.route('/cours/physique-chimie/chapitre7')
@login_required
def PC_chapitre7():
    return render_template('cours/physique-chimie/chapitre7._terminal.html')

@app.route('/cours/physique-chimie/chapitre8')
@login_required
def PC_chapitre8():
    return render_template('cours/physique-chimie/chapitre8._terminal.html')

@app.route('/cours/physique-chimie/premiere')
@login_required
def physique_chimie_premiere():
    return render_template('cours/physique-chimie/physique_chimie_premiere.html')

@app.route('/cours/physique-chimie/seconde')
@login_required
def physique_chimie_seconde():
    return render_template('cours/physique-chimie/physique_chimie_seconde.html')

# Routes de test
@app.route('/test/users')
@login_required
def test_users():
    try:
        # Récupère tous les utilisateurs de la base de données
        users = User.query.all()
        return render_template('test_users.html', users=users)
    except Exception as e:
        flash(f"Erreur: {str(e)}", "error")
        return redirect(url_for('home'))

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
    migrate = Migrate(app, db)

# Lancement de l'applications
if __name__ == '__main__':
    app.run(debug=True)

