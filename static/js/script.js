// theme.js
document.addEventListener('DOMContentLoaded', () => {
    const themeToggle = document.getElementById('checkbox');
    
    // Vérifier la préférence sauvegardée
    const currentTheme = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-theme', currentTheme);
    themeToggle.checked = currentTheme === 'dark';

    document.addEventListener('DOMContentLoaded', () => {
        const toggle = document.getElementById('darkmode-toggle');
        const body = document.body;
    
        // Fonction pour activer le mode sombre
        function enableDarkMode() {
            body.classList.add('dark-mode');
            localStorage.setItem('darkMode', 'enabled');
            toggle.checked = true;
            console.log('Mode sombre activé'); // Pour déboguer
        }
    
        // Fonction pour désactiver le mode sombre
        function disableDarkMode() {
            body.classList.remove('dark-mode');
            localStorage.setItem('darkMode', null);
            toggle.checked = false;
            console.log('Mode sombre désactivé'); // Pour déboguer
        }
    
        // Vérifier la préférence enregistrée
        if (localStorage.getItem('darkMode') === 'enabled') {
            enableDarkMode();
        }
    
        // Écouter les changements du toggle
        toggle.addEventListener('click', () => {
            if (toggle.checked) {
                enableDarkMode();
            } else {
                disableDarkMode();
            }
        });
    });
    

    // Gérer le changement de thème
    themeToggle.addEventListener('change', function() {
        if(this.checked) {
            document.documentElement.setAttribute('data-theme', 'dark');
            localStorage.setItem('theme', 'dark');
        } else {
            document.documentElement.setAttribute('data-theme', 'light');
            localStorage.setItem('theme', 'light');
        }
    });

    // Vérifier les préférences système
    const prefersDarkScheme = window.matchMedia('(prefers-color-scheme: dark)');
    prefersDarkScheme.addEventListener('change', (e) => {
        const newTheme = e.matches ? 'dark' : 'light';
        document.documentElement.setAttribute('data-theme', newTheme);
        themeToggle.checked = e.matches;
        localStorage.setItem('theme', newTheme);
    });
});



