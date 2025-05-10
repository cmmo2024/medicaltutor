document.addEventListener("DOMContentLoaded", function () {
    var form = document.getElementById("questions-form");
    var dialog = document.getElementById("confirmation-dialog");
    var chatDialog = document.getElementById("chat-confirmation-dialog");
    var overlay = document.getElementById("overlay");

    // Track whether inputs are disabled
    let inputsDisabled = false;

    // Close the confirmation dialog
    function closeDialog() {
        dialog.style.display = "none";
        chatDialog.style.display = "none";
        overlay.style.display = "none";

        if (!inputsDisabled) {
            enableInputs();
        }
    }

    // Disable all input elements
    function disableInputs() {
        const inputs = form.querySelectorAll("input, select, textarea");
        inputs.forEach(input => {
            input.disabled = true;
        });
        inputsDisabled = true;
    }

    // Enable all input elements
    function enableInputs() {
        const inputs = form.querySelectorAll("input, select, textarea");
        inputs.forEach(input => {
            input.disabled = false;
        });
        inputsDisabled = false;
    }

    // Show the "Calificar" confirmation dialog
    function showDialog() {
        dialog.style.display = "block";
        overlay.style.display = "block";
    }

    // Show "Regresar al chat" confirmation dialog
    function showChatDialog() {
        chatDialog.style.display = "block";
        overlay.style.display = "block";
    }

    // Expose functions to global scope
    window.closeDialog = closeDialog;
    window.showDialog = showDialog;
    window.showChatDialog = showChatDialog;

    // Get CSRF token from cookie
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

    // Handle "Calificar" button inside the modal
    var submitButton = dialog.querySelector("input[type='submit']");
    if (submitButton) {
        submitButton.addEventListener("click", function () {
            disableInputs();
        
            // Collect form data
            var formData = {};
            const csrfToken = getCookie('csrftoken');

            form.querySelectorAll("input[name^='q'], select[name^='q']").forEach(input => {
                let mainQuestionKey = input.name.split('_')[0];

                if (input.type === "checkbox" && input.checked) {
                    if (!formData[mainQuestionKey]) {
                        formData[mainQuestionKey] = [];
                    }
                    formData[mainQuestionKey].push(input.value);
                } else if (input.type === "radio" && input.checked) {
                    formData[mainQuestionKey] = input.value;
                } else if (input.tagName === "SELECT" && input.value) {
                    if (!formData[mainQuestionKey]) {
                        formData[mainQuestionKey] = [];
                    }
                    formData[mainQuestionKey].push(input.value);
                } else if (input.type === "text" && input.value) {
                    formData[mainQuestionKey] = input.value;
                }
            });

            // Submit form data using fetch
            fetch("/qualify_answers/", {
                method: "POST",
                headers: {
                    'X-CSRFToken': csrfToken,
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: JSON.stringify(formData)
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                if (data.error) {
                    alert(`Error: ${data.error}`);
                    enableInputs();
                    return;
                }

                const encodedResults = encodeURIComponent(JSON.stringify(data.result));
                const encodedQuestions = encodeURIComponent(JSON.stringify(data.questions));
                window.location.href = `/qualified_answers/?score=${data.total_score}&results=${encodedResults}&questions=${encodedQuestions}`;
            })
            .catch(error => {
                console.error('Fetch request failed:', error);
                alert('An error occurred while submitting the form.');
                enableInputs();
            });

            dialog.style.display = "none";
            overlay.style.display = "none";
        });
    }

    // Handle "Regresar al chat" button inside the modal
    var goHomeButton = document.getElementById("confirm-go-home-button");
    if (goHomeButton) {
        goHomeButton.addEventListener("click", function () {
            const csrfToken = getCookie('csrftoken');
            
            fetch('/restore_quiz_count/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrfToken,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({})
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                console.log('Quiz count restored:', data);
                disableInputs();
                window.location.href = "/chat/";
            })
            .catch(error => {
                console.error('Error restoring quiz count:', error);
                disableInputs();
                window.location.href = "/chat/";
            });
        });
    }
});
