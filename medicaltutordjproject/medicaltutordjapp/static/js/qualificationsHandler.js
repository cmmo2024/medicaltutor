document.addEventListener("DOMContentLoaded", function () {
    var homeButton = document.getElementById("go-home-button");
    homeButton.addEventListener("click", function () {
        window.location.href = "/chat/";
    });

    // Show the question dialog for retrying
    document.getElementById("retry-button").addEventListener("click", checkQuizLimit);
    
    var statisticsButton = document.getElementById("statistics-button");
    statisticsButton.addEventListener("click", function () {
        window.location.href = "/statistics/";
    });
});

function checkQuizLimit() {
    // Check if user has remaining quizzes
    fetch('/check_quiz_limit/', {
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        },
        credentials: 'same-origin'
    })
    .then(response => response.json())
    .then(data => {
        if (data.can_take_quiz) {
            showQuestionDialog();
        } else {
            showPlanUpgradeDialog();
        }
    })
    .catch(error => {
        console.error('Error checking quiz limit:', error);
        alert('Error al verificar el límite de cuestionarios. Por favor intente nuevamente.');
    });
}

function showQuestionDialog() {
    const dialog = document.getElementById('question-dialog');
    if (dialog) {
        dialog.style.display = 'block';
    } else {
        console.error('Modal dialog not found');
    }
}

function closeQuestionDialog() {
    const dialog = document.getElementById('question-dialog');
    if (dialog) {
        dialog.style.display = 'none';
    } else {
        console.error('Modal dialog not found');
    }
}

function showPlanUpgradeDialog() {
    const dialog = document.getElementById('plan-upgrade-dialog');
    if (dialog) {
        dialog.style.display = 'block';
    } else {
        console.error('Plan upgrade dialog not found');
    }
}

function closePlanUpgradeDialog() {
    const dialog = document.getElementById('plan-upgrade-dialog');
    if (dialog) {
        dialog.style.display = 'none';
    } else {
        console.error('Plan upgrade dialog not found');
    }
}

function continueToNextPage() {
    const selectedOption = document.querySelector('input[name="question-count"]:checked');

    if (selectedOption) {
        const numQuestions = parseInt(selectedOption.value, 10);

        // Close the question selection dialog
        closeQuestionDialog();

        // Show the loading dialog
        const loadingDialog = document.getElementById('loading-dialog');
        if (loadingDialog) {
            loadingDialog.style.display = 'block';
        } else {
            console.error('Loading dialog not found');
        }

        generateQuestions(numQuestions);
    } else {
        alert('Por favor selecciona el número de preguntas.');
    }
}

function generateQuestions(numQuestions) {
    // Get values from hidden inputs
    const currentSubject = document.getElementById('current-subject').value;
    const currentTopic = document.getElementById('current-topic').value;
    const chatContent = document.getElementById('chat-content').value;

    if (!currentTopic || !currentSubject) {
        alert('Error: No se pudo determinar el tema o la asignatura.');
        const loadingDialog = document.getElementById('loading-dialog');
        if (loadingDialog) {
            loadingDialog.style.display = 'none';
        }
        return;
    }

    fetch(`/generate_questions/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken(),
            'X-Requested-With': 'XMLHttpRequest'
        },
        credentials: 'same-origin',
        body: JSON.stringify({
            topic: currentTopic,
            subject: currentSubject,
            numQuestions: numQuestions,
            conversation: chatContent
        })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`Server responded with ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.redirect_url) {
            window.location.href = data.redirect_url;
        } else if (data.error) {
            throw new Error(data.error);
        } else {
            throw new Error('Unexpected response from the server.');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Ocurrió un error al generar preguntas. Por favor, inténtelo nuevamente más tarde.');
    })
    .finally(() => {
        const loadingDialog = document.getElementById('loading-dialog');
        if (loadingDialog) {
            loadingDialog.style.display = 'none';
        }
    });
}

// Helper to get CSRF token
function getCSRFToken() {
    const cookie = document.cookie.split('; ').find(row => row.startsWith('csrftoken'));
    return cookie ? cookie.split('=')[1] : null;
}


