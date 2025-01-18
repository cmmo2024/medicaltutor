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

        // If inputs were disabled, re-enable them (only if the user hasn't navigated or submitted)
        if (!inputsDisabled) {
            enableInputs();
        }
    }

    // Disable all input elements
    function disableInputs() {
        const inputs = form.querySelectorAll("input, select, textarea");
        inputs.forEach(input => {
            input.disabled = true; // Disable all input elements
        });
        inputsDisabled = true; // Mark inputs as disabled
    }

    // Enable all input elements
    function enableInputs() {
        const inputs = form.querySelectorAll("input, select, textarea");
        inputs.forEach(input => {
            input.disabled = false; // Enable all input elements
        });
        inputsDisabled = false; // Mark inputs as enabled
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

    // Handle "Calificar" button inside the modal
    var submitButton = dialog.querySelector("input[type='submit']");
    if (submitButton) {
        submitButton.addEventListener("click", function () {
        
            disableInputs();
        
            // Collect form data
            var formData = {
                csrfmiddlewaretoken: document.querySelector('[name=csrfmiddlewaretoken]').value
            };

            form.querySelectorAll("input[name^='q'], select[name^='q']").forEach(input => {
                let mainQuestionKey = input.name.split('_')[0]; // Extract main question key (e.g., 'q8' from 'q8_2')

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
                    'X-Requested-With': 'XMLHttpRequest',
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    alert(`Error: ${data.details || 'Unknown error'}`);
                    enableInputs(); // Re-enable inputs if an error occurs
                    return;
                }

                const encodedResults = encodeURIComponent(JSON.stringify(data.result));
                const encodedQuestions = encodeURIComponent(JSON.stringify(data.questions));
                window.location.href = `/qualified_answers/?score=${data.total_score}&results=${encodedResults}&questions=${encodedQuestions}`;
            })
            .catch(error => {
                console.error('Fetch request failed:', error);
                alert('An error occurred while submitting the form.');
                enableInputs(); // Re-enable inputs on fetch failure
            });

            // Hide dialog and overlay
            dialog.style.display = "none";
            overlay.style.display = "none";
        });
    } else {
        console.error("The submit button in the 'Calificar' dialog was not found.");
    }

    // Handle "Regresar al chat" button inside the modal
    var goHomeButton = document.getElementById("confirm-go-home-button");
    if (goHomeButton) {
        goHomeButton.addEventListener("click", function () {
            // Disable inputs only if the user navigates away
            disableInputs();
            window.location.href = "/chat/";
        });
    } else {
        console.error("The 'confirm-go-home-button' was not found in the DOM.");
    }
});
