document.addEventListener("DOMContentLoaded", function () {
    var homeButton = document.getElementById("go-home-button");
    homeButton.addEventListener("click", function () {
        // Clean up temp files before navigating
        cleanupTempFiles().then(() => {
            window.location.href = "/chat/";
        });
    });

    document.getElementById("retry-button").addEventListener("click", checkQuizLimit);
    
    var statisticsButton = document.getElementById("statistics-button");
    statisticsButton.addEventListener("click", function () {
        // Clean up temp files before navigating
        cleanupTempFiles().then(() => {
            window.location.href = "/statistics/";
        });
    });
});

function cleanupTempFiles() {
    return fetch('/cleanup_temp_files/', {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken')
        }
    })
    .then(response => response.json())
    .catch(error => console.error('Error cleaning up temp files:', error));
}

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function checkQuizLimit() {
    // Clean up any existing temp files before generating new ones
    cleanupTempFiles().then(() => {
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
                alert('Error al verificar el límite de cuestionarios. Por favor intente nuevamente.');
            });
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
    const selectedQuestionType = document.querySelector('input[name="question-type"]:checked');

    if (selectedOption && selectedQuestionType) {
        const numQuestions = parseInt(selectedOption.value, 10);
        const questionType = selectedQuestionType.value;

        // Close the question selection dialog
        closeQuestionDialog();

        // Show the loading dialog
        const loadingDialog = document.getElementById('loading-dialog');
        if (loadingDialog) {
            loadingDialog.style.display = 'block';
        } else {
            console.error('Loading dialog not found');
        }

        generateQuestions(numQuestions, questionType);
    } else {
        alert('Por favor selecciona el número de preguntas y el tipo de test.');
    }
}

function generateQuestions(numQuestions, questionType = 'topic') {
    // Get the current topic and subject from the URL parameters or localStorage
    const urlParams = new URLSearchParams(window.location.search);
    const topic = urlParams.get('topic') || localStorage.getItem('currentTopic');
    const subject = urlParams.get('subject') || localStorage.getItem('currentSubject');
    
    // Get the chat content from local storage or session
    const chatContent = localStorage.getItem('lastChatContent') || sessionStorage.getItem('lastChatContent') || '';

    if (!subject) {
        alert('Error: No se pudo determinar la asignatura.');
        const loadingDialog = document.getElementById('loading-dialog');
        if (loadingDialog) {
            loadingDialog.style.display = 'none';
        }
        return;
    }

    // For topic-specific tests, we need a topic
    if (questionType === 'topic' && !topic) {
        alert('Error: No se pudo determinar el tema para el test específico.');
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
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({
            topic: questionType === 'topic' ? topic : '',
            subject: subject,
            numQuestions: numQuestions,
            conversation: chatContent,
            question_type: questionType
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
