from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime, timedelta, timezone
from flask_migrate import Migrate
import os
import pytz
from flask_mail import Mail, Message
from flask_apscheduler import APScheduler
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Création de l'application Flask
app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = 'votre_clé_secrète'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///education.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Configuration de Flask-Mail
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'babsjr28@gmail.com'
app.config['MAIL_PASSWORD'] = 'kipl ioor pyko sith'
app.config['MAIL_DEFAULT_SENDER'] = ('revise avec moi', 'babsjr28@gmail.com')

# Initialisation des extensions
db = SQLAlchemy(app)
mail = Mail(app)
scheduler = APScheduler()
scheduler.api_enabled = True
scheduler.init_app(app)

# Protection des routes
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

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

class CalendarEvent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    color = db.Column(db.String(20), default='#3498db')
    type = db.Column(db.String(20), default='other')
    completed = db.Column(db.Boolean, default=False)
    reminder = db.Column(db.Boolean, default=False)
    reminder_time = db.Column(db.DateTime)
    reminder_sent = db.Column(db.Boolean, default=False)
    
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

class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relation avec l'utilisateur
    user = db.relationship('User', backref=db.backref('notes', lazy=True, cascade="all, delete-orphan"))

# Fonctions utilitaires
def send_reminder_email(event, user):
    """Envoie un email de rappel pour un événement"""
    subject = f"Rappel : {event.title}"
    
    # Convertir l'heure UTC stockée en heure locale (Paris)
    paris_tz = pytz.timezone('Europe/Paris')
    if event.start_date.tzinfo is None:  # Si la date n'a pas de timezone (naive)
        start_date_utc = pytz.utc.localize(event.start_date)
    else:
        start_date_utc = event.start_date
    
    start_date_local = start_date_utc.astimezone(paris_tz)
    
    # Formatage de la date et heure en heure locale
    start_time = start_date_local.strftime("%d/%m/%Y à %H:%M")
    
    # Corps du message
    body = f"""
    Salem mon frére {user.prenom} {user.nom},
    
    Ceci est un rappel pour votre événement "{event.title}" qui commence le {start_time} in sha allah .
    
    Description : {event.description or 'Aucune description'}
    
    Bonne journée !
    """
    
    msg = Message(
        subject=subject,
        recipients=[user.email],
        body=body
    )
    
    try:
        mail.send(msg)
        print(f"Email de rappel envoyé à {user.email} pour l'événement '{event.title}'")
        return True
    except Exception as e:
        print(f"Erreur lors de l'envoi de l'email: {str(e)}")
        return False

def check_reminders():
    """Vérifie les rappels à envoyer et envoie les emails"""
    print("Vérification des rappels en cours...")
    
    # Vérifier si nous sommes dans un contexte d'application
    ctx = None
    if not app.app_context():
        ctx = app.app_context()
        ctx.push()
    
    try:
        # Utiliser pytz pour une gestion précise des fuseaux horaires
        paris_tz = pytz.timezone('Europe/Paris')
        now = datetime.now(paris_tz)
        
        print(f"Heure actuelle (Paris): {now}")
        
        # Convertir en UTC pour la comparaison avec la base de données
        now_utc = now.astimezone(pytz.UTC)
        print(f"Heure actuelle (UTC): {now_utc}")
        
        # Trouver tous les événements avec rappel activé, non envoyé, et dont le temps de rappel est passé
        upcoming_reminders = CalendarEvent.query.filter(
            CalendarEvent.reminder == True,
            CalendarEvent.reminder_sent == False,
            CalendarEvent.reminder_time <= now_utc,
            CalendarEvent.start_date > now_utc  # L'événement n'a pas encore commencé
        ).all()
        
        print(f"Nombre de rappels à envoyer : {len(upcoming_reminders)}")
        
        for event in upcoming_reminders:
            print(f"Événement trouvé: {event.id}, titre: {event.title}")
            print(f"  Heure de rappel: {event.reminder_time}")
            print(f"  Heure de début: {event.start_date}")
            
            user = User.query.get(event.user_id)
            if user:
                success = send_reminder_email(event, user)
                if success:
                    # Marquer le rappel comme envoyé
                    event.reminder_sent = True
                    db.session.commit()
                    print(f"Rappel envoyé pour l'événement {event.id} à {user.email}")
    finally:
        # Libérer le contexte si nous l'avons créé
        if ctx:
            ctx.pop()

# Planifier la tâche pour qu'elle s'exécute toutes les 5 minutes
@scheduler.task('interval', id='check_reminders', seconds=30)
def scheduled_check_reminders():
    print(f"[{datetime.now()}] Exécution planifiée de la vérification des rappels")
    with app.app_context():
        check_reminders()
    print(f"[{datetime.now()}] Fin de la vérification planifiée des rappels")

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

@app.route('/debug_event/<int:event_id>')
@login_required
def debug_event(event_id):
    event = CalendarEvent.query.get_or_404(event_id)
    
    # Vérifier que l'utilisateur connecté est bien le propriétaire de l'événement
    if event.user_id != session['user_id']:
        return "Vous n'êtes pas autorisé à voir cet événement"
    
    # Heure actuelle
    now_utc = datetime.now(timezone.utc)
    paris_tz = pytz.timezone('Europe/Paris')
    now_paris = datetime.now(paris_tz)
    
    # Convertir les dates de l'événement en heure de Paris
    if event.start_date.tzinfo is None:  # Si la date n'a pas de timezone (naive)
        start_date_utc = pytz.utc.localize(event.start_date)
        end_date_utc = pytz.utc.localize(event.end_date)
        reminder_time_utc = pytz.utc.localize(event.reminder_time) if event.reminder_time else None
    else:
        start_date_utc = event.start_date
        end_date_utc = event.end_date
        reminder_time_utc = event.reminder_time
    
    start_date_paris = start_date_utc.astimezone(paris_tz) if start_date_utc else None
    end_date_paris = end_date_utc.astimezone(paris_tz) if end_date_utc else None
    reminder_time_paris = reminder_time_utc.astimezone(paris_tz) if reminder_time_utc else None
    
    return {
        "event_id": event.id,
        "title": event.title,
        "current_time": {
            "utc": str(now_utc),
            "paris": str(now_paris)
        },
        "start_date": {
            "raw": str(event.start_date),
            "utc": str(start_date_utc),
            "paris": str(start_date_paris)
        },
        "end_date": {
            "raw": str(event.end_date),
            "utc": str(end_date_utc),
            "paris": str(end_date_paris)
        },
        "reminder": {
            "enabled": event.reminder,
            "sent": event.reminder_sent,
            "time": {
                "raw": str(event.reminder_time),
                "utc": str(reminder_time_utc),
                "paris": str(reminder_time_paris)
            } if event.reminder_time else None
        }
    }

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

# boite a outils 
@app.route('/toolbox')
def toolbox():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('toolbox.html')

# Routes API pour le calendrier
@app.route('/api/events', methods=['GET'])
@login_required
def get_events():
    user_id = session['user_id']
    start = request.args.get('start', '')
    end = request.args.get('end', '')
    
    try:
        # Convertir les dates de chaîne ISO à objets datetime
        if start and end:
            start_date = datetime.fromisoformat(start.replace('Z', '+00:00'))
            end_date = datetime.fromisoformat(end.replace('Z', '+00:00'))
            
            # Convertir en UTC pour la comparaison avec la base de données
            if start_date.tzinfo is not None:
                start_date = start_date.astimezone(pytz.UTC)
            if end_date.tzinfo is not None:
                end_date = end_date.astimezone(pytz.UTC)
            
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
            # Convertir les dates UTC en ISO pour le client
            start_iso = event.start_date.isoformat() if event.start_date.tzinfo else pytz.UTC.localize(event.start_date).isoformat()
            end_iso = event.end_date.isoformat() if event.end_date.tzinfo else pytz.UTC.localize(event.end_date).isoformat()
            
            reminder_time_iso = None
            if event.reminder_time:
                reminder_time_iso = event.reminder_time.isoformat() if event.reminder_time.tzinfo else pytz.UTC.localize(event.reminder_time).isoformat()
            
            events_data.append({
                'id': event.id,
                'title': event.title,
                'description': event.description,
                'start': start_iso,
                'end': end_iso,
                'color': event.color,
                'extendedProps': {
                    'type': event.type,
                    'completed': event.completed,
                    'reminder': event.reminder,
                    'reminder_time': reminder_time_iso
                }
            })
        
        return jsonify(events_data)
    except Exception as e:
        print(f"Erreur lors de la récupération des événements: {str(e)}")
        return jsonify([])

@app.route('/api/events', methods=['POST'])
@login_required
def create_event():
    try:
        user_id = session['user_id']
        data = request.json
        
        print(f"Données reçues complètes: {data}")
        
        # Vérifier que les champs requis sont présents
        required_fields = ['title', 'start', 'end']
        for field in required_fields:
            if field not in data:
                print(f"Champ requis manquant: {field}")
                return jsonify({
                    'status': 'error',
                    'message': f'Le champ {field} est requis'
                }), 400
        
        # Convertir les dates de chaîne ISO à objets datetime avec timezone
        from datetime import datetime, timezone
        
        # Afficher les dates brutes pour le débogage
        print(f"Date de début brute: {data['start']}")
        print(f"Date de fin brute: {data['end']}")
        
        try:
            # Convertir en objets datetime avec timezone
            start_date = datetime.fromisoformat(data['start'].replace('Z', '+00:00'))
            end_date = datetime.fromisoformat(data['end'].replace('Z', '+00:00'))
            
            # S'assurer que les dates sont en UTC pour le stockage
            if start_date.tzinfo is not None:
                start_date = start_date.astimezone(timezone.utc)
            if end_date.tzinfo is not None:
                end_date = end_date.astimezone(timezone.utc)
            
            print(f"Date de début convertie (UTC): {start_date}")
            print(f"Date de fin convertie (UTC): {end_date}")
        except Exception as e:
            print(f"Erreur lors de la conversion des dates: {str(e)}")
            return jsonify({
                'status': 'error',
                'message': f'Erreur de format de date: {str(e)}'
            }), 400
        
        # Créer un nouvel événement
        new_event = CalendarEvent(
            user_id=user_id,
            title=data['title'],
            description=data.get('description', ''),
            start_date=start_date,
            end_date=end_date,
            color=data.get('color', '#3498db'),
            type=data.get('type', 'other'),
            reminder=data.get('reminder', False),
            reminder_sent=False
        )
        
        # Ajouter un rappel si demandé
        if data.get('reminder'):
            reminder_minutes = int(data.get('reminder_minutes', 30))
            reminder_time = start_date - timedelta(minutes=reminder_minutes)
            new_event.reminder_time = reminder_time
            print(f"Rappel configuré pour: {reminder_time} ({reminder_minutes} minutes avant le début)")
        
        db.session.add(new_event)
        
        try:
            db.session.commit()
            print(f"Événement créé avec succès, ID: {new_event.id}")
            return jsonify({
                'status': 'success',
                'id': new_event.id,
                'message': 'Événement créé avec succès'
            }), 201
        except Exception as e:
            db.session.rollback()
            print(f"Erreur lors de la création de l'événement dans la base de données: {str(e)}")
            return jsonify({
                'status': 'error',
                'message': f'Erreur de base de données: {str(e)}'
            }), 500
    except Exception as e:
        print(f"Erreur générale dans create_event: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Erreur serveur: {str(e)}'
        }), 500

@app.route('/test_create_event')
@login_required
def test_create_event():
    try:
        user_id = session['user_id']
        
        # Créer un événement de test avec des valeurs fixes
        from datetime import datetime, timedelta, timezone
        
        now = datetime.now(timezone.utc)
        start_date = now + timedelta(hours=1)
        end_date = start_date + timedelta(hours=1)
        
        test_event = CalendarEvent(
            user_id=user_id,
            title="Événement de test automatique",
            description="Ceci est un test de création d'événement",
            start_date=start_date,
            end_date=end_date,
            color="#3498db",
            type="other",
            reminder=False,
            reminder_sent=False
        )
        
        db.session.add(test_event)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': f'Événement de test créé avec succès, ID: {test_event.id}',
            'event': {
                'id': test_event.id,
                'title': test_event.title,
                'start': test_event.start_date.isoformat(),
                'end': test_event.end_date.isoformat()
            }
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Erreur lors du test: {str(e)}'
        })

@app.route('/api/events/<int:event_id>', methods=['PUT'])
@login_required
def update_event(event_id):
    try:
        user_id = session['user_id']
        data = request.json
        
        print(f"Données reçues pour mise à jour de l'événement {event_id}: {data}")
        
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
            try:
                start_date = datetime.fromisoformat(data['start'].replace('Z', '+00:00'))
                if start_date.tzinfo is not None:
                    start_date = start_date.astimezone(timezone.utc)
                event.start_date = start_date
            except Exception as e:
                print(f"Erreur lors de la conversion de la date de début: {str(e)}")
                return jsonify({
                    'status': 'error',
                    'message': f'Format de date de début invalide: {str(e)}'
                }), 400
        if 'end' in data:
            try:
                end_date = datetime.fromisoformat(data['end'].replace('Z', '+00:00'))
                if end_date.tzinfo is not None:
                    end_date = end_date.astimezone(timezone.utc)
                event.end_date = end_date
            except Exception as e:
                print(f"Erreur lors de la conversion de la date de fin: {str(e)}")
                return jsonify({
                    'status': 'error',
                    'message': f'Format de date de fin invalide: {str(e)}'
                }), 400
        if 'color' in data:
            event.color = data['color']
        if 'type' in data:
            event.type = data['type']
        if 'completed' in data:
            event.completed = data['completed']
        if 'reminder' in data:
            event.reminder = data['reminder']
            # Réinitialiser le statut d'envoi si le rappel est modifié
            event.reminder_sent = False
            
            if data['reminder']:
                reminder_minutes = int(data.get('reminder_minutes', 30))
                reminder_time = event.start_date - timedelta(minutes=reminder_minutes)
                event.reminder_time = reminder_time
            else:
                event.reminder_time = None
        
        try:
            db.session.commit()
            print(f"Événement {event_id} mis à jour avec succès")
            return jsonify({
                'status': 'success',
                'message': 'Événement mis à jour avec succès'
            })
        except Exception as e:
            db.session.rollback()
            print(f"Erreur lors de la mise à jour de l'événement dans la base de données: {str(e)}")
            return jsonify({
                'status': 'error',
                'message': f'Erreur de base de données: {str(e)}'
            }), 500
    except Exception as e:
        print(f"Erreur générale dans update_event: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Erreur serveur: {str(e)}'
        }), 500

@app.route('/api/events/<int:event_id>', methods=['DELETE'])
@login_required
def delete_event(event_id):
    try:
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
    except Exception as e:
        print(f"Erreur générale dans delete_event: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Erreur serveur: {str(e)}'
        }), 500

@app.route('/api/events/complete/<int:event_id>', methods=['PUT'])
@login_required
def complete_event(event_id):
    try:
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
    except Exception as e:
        print(f"Erreur générale dans complete_event: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Erreur serveur: {str(e)}'
        }), 500

# Routes API pour les notes
@app.route('/api/notes', methods=['GET'])
@login_required
def get_notes():
    user_id = session['user_id']
    notes = Note.query.filter_by(user_id=user_id).order_by(Note.updated_at.desc()).all()
    
    notes_data = []
    for note in notes:
        notes_data.append({
            'id': note.id,
            'title': note.title,
            'content': note.content,
            'created_at': note.created_at.isoformat(),
            'updated_at': note.updated_at.isoformat()
        })
    
    return jsonify(notes_data)

@app.route('/api/notes', methods=['POST'])
@login_required
def create_note():
    user_id = session['user_id']
    data = request.json
    
    new_note = Note(
        user_id=user_id,
        title=data.get('title', 'Sans titre'),
        content=data.get('content', '')
    )
    
    db.session.add(new_note)
    
    try:
        db.session.commit()
        return jsonify({
            'status': 'success',
            'id': new_note.id,
            'message': 'Note créée avec succès'
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/notes/<int:note_id>', methods=['PUT'])
@login_required
def update_note(note_id):
    user_id = session['user_id']
    data = request.json
    
    note = Note.query.filter_by(id=note_id, user_id=user_id).first()
    
    if not note:
        return jsonify({
            'status': 'error',
            'message': 'Note non trouvée'
        }), 404
    
    note.title = data.get('title', note.title)
    note.content = data.get('content', note.content)
    
    try:
        db.session.commit()
        return jsonify({
            'status': 'success',
            'message': 'Note mise à jour avec succès'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/notes/<int:note_id>', methods=['DELETE'])
@login_required
def delete_note(note_id):
    user_id = session['user_id']
    
    note = Note.query.filter_by(id=note_id, user_id=user_id).first()
    
    if not note:
        return jsonify({
            'status': 'error',
            'message': 'Note non trouvée'
        }), 404
    
    db.session.delete(note)
    
    try:
        db.session.commit()
        return jsonify({
            'status': 'success',
            'message': 'Note supprimée avec succès'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

# Routes de test pour le système de rappel
@app.route('/test_email')
def test_email():
    try:
        msg = Message(
            subject="Test d'email",
            recipients=[os.environ.get('MAIL_USERNAME', 'babsjr28@gmail.com')],
            body="Ceci est un test d'envoi d'email depuis votre application Flask."
        )
        mail.send(msg)
        return "Email envoyé avec succès!"
    except Exception as e:
        return f"Erreur lors de l'envoi de l'email: {str(e)}"

@app.route('/check_reminders_now')
def check_reminders_now():
    try:
        check_reminders()
        return "Vérification des rappels effectuée. Consultez les logs du serveur pour plus de détails."
    except Exception as e:
        return f"Erreur lors de la vérification des rappels: {str(e)}"

@app.route('/create_test_reminder')
@login_required
def create_test_reminder():
    user_id = session['user_id']
    
    # Créer un événement qui commence dans 10 minutes
    start_date = datetime.utcnow() + timedelta(minutes=10)
    end_date = start_date + timedelta(hours=1)
    
    # Le rappel est défini pour 2 minutes à partir de maintenant
    reminder_time = datetime.utcnow() + timedelta(minutes=2)
    
    test_event = CalendarEvent(
        user_id=user_id,
        title="Événement de test pour rappel",
        description="Ceci est un test du système de rappel par email",
        start_date=start_date,
        end_date=end_date,
        color="#3498db",
        type="other",
        reminder=True,
        reminder_time=reminder_time,
        reminder_sent=False
    )
    
    db.session.add(test_event)
    
    try:
        db.session.commit()
        return f"Événement de test créé. Un rappel sera envoyé dans environ 2 minutes. ID de l'événement: {test_event.id}"
    except Exception as e:
        db.session.rollback()
        return f"Erreur lors de la création de l'événement de test: {str(e)}"

@app.route('/create_precise_test_reminder')
@login_required
def create_precise_test_reminder():
    user_id = session['user_id']
    
    # Obtenir l'heure actuelle
    now = datetime.now(timezone.utc)
    
    # Créer un événement qui commence dans exactement 10 minutes
    start_date = now + timedelta(minutes=10)
    end_date = start_date + timedelta(hours=1)
    
    # Le rappel est défini pour exactement 1 minute à partir de maintenant
    reminder_time = now + timedelta(minutes=1)
    
    print(f"Heure actuelle: {now}")
    print(f"Heure de début: {start_date}")
    print(f"Heure de rappel: {reminder_time}")
    
    test_event = CalendarEvent(
        user_id=user_id,
        title="Test précis de rappel",
        description="Ceci est un test précis du système de rappel par email",
        start_date=start_date,
        end_date=end_date,
        color="#3498db",
        type="other",
        reminder=True,
        reminder_time=reminder_time,
        reminder_sent=False
    )
    
    db.session.add(test_event)
    
    try:
        db.session.commit()
        return f"""
        Événement de test créé avec des heures précises:
        - ID: {test_event.id}
        - Heure actuelle: {now}
        - Heure de début: {start_date} (dans 10 minutes)
        - Heure de rappel: {reminder_time} (dans 1 minute)
        
        Un rappel devrait être envoyé dans environ 1 minute.
        """
    except Exception as e:
        db.session.rollback()
        return f"Erreur lors de la création de l'événement de test: {str(e)}"

@app.route('/scheduler_status')
def scheduler_status():
    jobs = []
    for job in scheduler.get_jobs():
        jobs.append({
            'id': job.id,
            'next_run_time': str(job.next_run_time),
            'trigger': str(job.trigger)
        })
    
    return {
        'running': scheduler.running,
        'jobs': jobs
    }

# Routes pour les matières de terminale
# PHILO
@app.route('/cours/philo/terminale')
@login_required
def philo_terminale():
    return render_template('cours/philo/philo_terminal.html')

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

# Démarrer le planificateur
scheduler.start()

# Lancement de l'application
if __name__ == '__main__':
    app.run(debug=True)  # Activer le mode debug pour le développement
