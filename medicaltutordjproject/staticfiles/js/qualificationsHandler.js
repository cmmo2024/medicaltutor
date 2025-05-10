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
    fetch('/check_quiz_limit/')
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
            alert('Error al verificar el lÃ­mite de cuestionarios. Por favor intente nuevamente.');
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
        alert('Por favor selecciona el nÃºmero de preguntas.');
    }
}

function generateQuestions(numQuestions) {
    // Get the current topic and subject from the URL parameters
    const urlParams = new URLSearchParams(window.location.search);
    const topic = urlParams.get('topic') || localStorage.getItem('currentTopic');
    const subject = urlParams.get('subject') || localStorage.getItem('currentSubject');
    
    // Get the chat content from local storage or session
    const chatContent = localStorage.getItem('lastChatContent') || sessionStorage.getItem('lastChatContent') || '';

    if (!topic || !subject) {
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
            'X-CSRFToken': getCSRFToken()
        },
        body: JSON.stringify({
            topic: topic,
            subject: subject,
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
            alert(`Error: ${data.error}`);
        } else {
            alert('Unexpected response from the server.');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('OcurriÃ³ un error al generar preguntas. Por favor, intÃ©ntelo nuevamente mÃ¡s tarde.');
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
