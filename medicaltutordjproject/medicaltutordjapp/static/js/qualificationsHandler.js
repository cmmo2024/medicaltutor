document.addEventListener("DOMContentLoaded", function () {
    var homeButton = document.getElementById("go-home-button");
    homeButton.addEventListener("click", function () {
        window.location.href = "/chat/";
    });

    // Show the question dialog for retrying
    document.getElementById("retry-button").addEventListener("click", showQuestionDialog);
});

// Redirect to home if the user tries to navigate back
//window.addEventListener("popstate", function () {
//    window.location.href = "/";
//});

function showQuestionDialog() {
    const dialog = document.getElementById('question-dialog');
    if (dialog) {
        dialog.style.display = 'block'; // Show the modal
    } else {
        console.error('Modal dialog not found');
    }
}

function closeQuestionDialog() {
    const dialog = document.getElementById('question-dialog');
    if (dialog) {
        dialog.style.display = 'none'; // Hide the modal
    } else {
        console.error('Modal dialog not found');
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

        generateQuestions(numQuestions); // Call your generateQuestions method
    } else {
        alert('Por favor selecciona el número de preguntas.');
    }
}

function generateQuestions(numQuestions) {
    const topic = localStorage.getItem('selectedTopic') || 'General'; // Default to 'General' if not found

    fetch(`/generate_questions/`, { // Use the generate endpoint for POST
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        },
        body: JSON.stringify({
            topic,
            numQuestions,
            conversation: '' // Pass the conversation if needed
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
            // Redirect to the questions page
            window.location.href = data.redirect_url;
        } else if (data.error) {
            alert(`Error: ${data.error}`);
        } else {
            alert('Unexpected response from the server.');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Ocurrió un error al generar preguntas. Por favor, inténtelo nuevamente más tarde.');
    })
    .finally(() => {
        // Hide the loading dialog regardless of success or failure
        const loadingDialog = document.getElementById('loading-dialog');
        if (loadingDialog) {
            loadingDialog.style.display = 'none';
        }
    });
}

// Helper to get CSRF token
function getCSRFToken() {
    const cookie = document.cookie.split('; ').find(row => row.startsWith('csrftoken'));
    return cookie ? cookie.split('=')[1] : null; // Ensure no errors if csrftoken is missing
}
