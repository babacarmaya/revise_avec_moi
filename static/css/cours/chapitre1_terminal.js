document.addEventListener('DOMContentLoaded', function() {
    // Gestion des onglets de comparaison
    const tabButtons = document.querySelectorAll('.tab-button');
    const tabContents = document.querySelectorAll('.tab-content');

    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            // Retirer la classe active de tous les boutons et contenus
            tabButtons.forEach(btn => btn.classList.remove('active'));
            tabContents.forEach(content => content.classList.remove('active'));
            
            // Activer l'onglet cliqué
            button.classList.add('active');
            const tabId = button.getAttribute('data-tab');
            document.getElementById(tabId).classList.add('active');
        });
    });

    // Gestion des périodes historiques
    const eraButtons = document.querySelectorAll('.era-button');
    const eraContents = document.querySelectorAll('.era-content');

    eraButtons.forEach(button => {
        button.addEventListener('click', () => {
            eraButtons.forEach(btn => btn.classList.remove('active'));
            eraContents.forEach(content => content.classList.remove('active'));
            
            button.classList.add('active');
            const eraId = button.getAttribute('data-era');
            document.getElementById(eraId).classList.add('active');
        });
    });

    // Gestion du quiz
    const questions = document.querySelectorAll('.quiz-question');
    const prevButton = document.getElementById('prevQuestion');
    const nextButton = document.getElementById('nextQuestion');
    const submitButton = document.getElementById('submitQuiz');
    const quizContainer = document.querySelector('.quiz-container');
    const quizResult = document.querySelector('.quiz-result');
    let currentQuestion = 0;

    // Réponses correctes
    const correctAnswers = {
        'q1': 'b',
        'q2': 'b',
        'q3': 'b',
        'q4': 'b',
        'q5': 'b'
    };

    function updateQuestion() {
        questions.forEach(q => q.classList.remove('active'));
        questions[currentQuestion].classList.add('active');
        
        // Mise à jour des boutons
        prevButton.disabled = currentQuestion === 0;
        if (currentQuestion === questions.length - 1) {
            nextButton.style.display = 'none';
            submitButton.style.display = 'block';
        } else {
            nextButton.style.display = 'block';
            submitButton.style.display = 'none';
        }

        // Mise à jour de la barre de progression
        const progress = ((currentQuestion + 1) / questions.length) * 100;
        document.querySelector('.progress-fill').style.width = `${progress}%`;
        document.querySelector('.progress-text').textContent = 
            `${currentQuestion + 1}/${questions.length} questions`;
    }

    function calculateScore() {
        let correctCount = 0;
        questions.forEach((question, index) => {
            const selectedAnswer = question.querySelector(`input[name="q${index + 1}"]:checked`);
            if (selectedAnswer && selectedAnswer.value === correctAnswers[`q${index + 1}`]) {
                correctCount++;
            }
        });
        return {
            percentage: (correctCount / questions.length) * 100,
            correctCount: correctCount
        };
    }

    function showFinalScore() {
        const scoreResult = calculateScore();
        
        // Cacher le quiz et afficher le résultat
        quizContainer.style.display = 'none';
        quizResult.classList.remove('hidden');
        
        // Mettre à jour le score
        const scoreNumber = quizResult.querySelector('.score-number');
        const correctAnswersElement = quizResult.querySelector('.count');
        const scoreMessage = quizResult.querySelector('.score-message');
        
        scoreNumber.textContent = Math.round(scoreResult.percentage);
        correctAnswersElement.textContent = scoreResult.correctCount;
        
        // Message personnalisé selon le score
        if (scoreResult.percentage >= 80) {
            scoreMessage.textContent = "Excellent ! Vous maîtrisez bien ce chapitre.";
        } else if (scoreResult.percentage >= 60) {
            scoreMessage.textContent = "Bien ! Continuez vos efforts.";
        } else {
            scoreMessage.textContent = "Vous devriez revoir ce chapitre.";
        }
    }

    // Événements des boutons du quiz
    if (prevButton && nextButton && submitButton) {
        prevButton.addEventListener('click', () => {
            if (currentQuestion > 0) {
                currentQuestion--;
                updateQuestion();
            }
        });

        nextButton.addEventListener('click', () => {
            if (currentQuestion < questions.length - 1) {
                currentQuestion++;
                updateQuestion();
            }
        });

        submitButton.addEventListener('click', showFinalScore);
    }

    // Gestion des boutons post-quiz
    const retryButton = document.querySelector('.retry-button');
    const nextChapterButton = document.querySelector('.next-chapter-button');

    if (retryButton) {
        retryButton.addEventListener('click', () => {
            location.reload();
        });
    }

    if (nextChapterButton) {
        nextChapterButton.addEventListener('click', () => {
            // Redirection vers le chapitre suivant
            // window.location.href = '/chapitre2';
        });
    }

    // Initialisation du quiz
    if (questions.length > 0) {
        updateQuestion();
    }

    // Gestion des indices
    const hintButtons = document.querySelectorAll('.toggle-hint');
    hintButtons.forEach(button => {
        button.addEventListener('click', () => {
            const hintContent = button.nextElementSibling;
            hintContent.classList.toggle('hidden');
            button.textContent = hintContent.classList.contains('hidden') ? 
                'Voir les pistes de réflexion' : 'Masquer les pistes';
        });
    });
});
