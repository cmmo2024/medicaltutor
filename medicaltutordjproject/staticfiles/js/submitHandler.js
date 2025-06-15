document.addEventListener("DOMContentLoaded", function () {
    const form = document.getElementById("questions-form");
    const dialog = document.getElementById("confirmation-dialog");
    const chatDialog = document.getElementById("chat-confirmation-dialog");
    const overlay = document.getElementById("overlay");

    let inputsDisabled = false;

    function closeDialog() {
        dialog.style.display = "none";
        chatDialog.style.display = "none";
        overlay.style.display = "none";

        if (!inputsDisabled) {
            enableInputs();
        }
    }

    function disableInputs() {
        const inputs = form.querySelectorAll("input, select, textarea");
        inputs.forEach(input => {
            input.disabled = true;
        });
        inputsDisabled = true;
    }

    function enableInputs() {
        const inputs = form.querySelectorAll("input, select, textarea");
        inputs.forEach(input => {
            input.disabled = false;
        });
        inputsDisabled = false;
    }

    function showDialog() {
        dialog.style.display = "block";
        overlay.style.display = "block";
    }

    function showChatDialog() {
        chatDialog.style.display = "block";
        overlay.style.display = "block";
    }

    window.closeDialog = closeDialog;
    window.showDialog = showDialog;
    window.showChatDialog = showChatDialog;

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

    const submitButton = dialog.querySelector("input[type='submit']");
    if (submitButton) {
        let submissionInProgress = false;
        let submissionCompleted = false;

        // Generate UUID once per session
        const submissionId = crypto.randomUUID();

        const handleClick = async function (e) {
            e.preventDefault();

            if (submissionInProgress || submissionCompleted) {
                console.log('Submission already in progress or completed');
                return;
            }

            submissionInProgress = true;
            submitButton.disabled = true;
            disableInputs();
            submitButton.removeEventListener("click", handleClick); // prevent further clicks

            const csrfToken = getCookie('csrftoken');
            const formData = {};

            const inputs = form.querySelectorAll("input[name^='q'], select[name^='q']");
            inputs.forEach(input => {
                const mainKey = input.name.split('_')[0];

                if (input.type === "checkbox" && input.checked) {
                    formData[mainKey] = formData[mainKey] || [];
                    formData[mainKey].push(input.value);
                } else if (input.type === "radio" && input.checked) {
                    formData[mainKey] = input.value;
                } else if (input.tagName === "SELECT" && input.value) {
                    formData[mainKey] = formData[mainKey] || [];
                    formData[mainKey].push(input.value);
                } else if (input.type === "text" && input.value) {
                    formData[mainKey] = input.value;
                }
            });

            formData.submission_id = submissionId;

            const controller = new AbortController();
            const timeout = setTimeout(() => controller.abort(), 10000); // 10s

            try {
                const response = await fetch("/qualify_answers/", {
                    method: "POST",
                    headers: {
                        'X-CSRFToken': csrfToken,
                        'Content-Type': 'application/json',
                        'X-Requested-With': 'XMLHttpRequest',
                        'Idempotency-Key': submissionId
                    },
                    body: JSON.stringify(formData),
                    signal: controller.signal
                });

                clearTimeout(timeout);

                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }

                let qualifyData;
                try {
                    qualifyData = await response.json();
                } catch (jsonErr) {
                    console.error("Invalid JSON from server:", jsonErr);
                    throw new Error("Server returned invalid response.");
                }

                // Hide modal
                dialog.style.display = "none";
                overlay.style.display = "none";

                // Create and submit form
                const postForm = document.createElement('form');
                postForm.method = 'POST';
                postForm.action = '/qualified_answers/';

                const addHidden = (name, value) => {
                    const input = document.createElement('input');
                    input.type = 'hidden';
                    input.name = name;
                    input.value = typeof value === 'object' ? JSON.stringify(value) : value;
                    postForm.appendChild(input);
                };

                addHidden('csrfmiddlewaretoken', csrfToken);
                addHidden('score', qualifyData.total_score);
                addHidden('results', qualifyData.result);
                addHidden('questions', qualifyData.questions);
                addHidden('submission_id', submissionId);

                document.body.appendChild(postForm);
                submissionCompleted = true;
                postForm.submit();

            } catch (error) {
                console.error('Submission error:', error.message || error);

                submitButton.disabled = false;
                enableInputs();
                submissionInProgress = false;

                dialog.style.display = "block";
                overlay.style.display = "block";

                if (error.name === 'AbortError') {
                    alert('The request timed out. Please try again.');
                } else {
                    alert('An error occurred while submitting. Please try again.\n' + error.message);
                }
            }
        };

        submitButton.addEventListener("click", handleClick);
    }
  
    // Chat "Go Home" Button
    const goHomeButton = document.getElementById("confirm-go-home-button");
    if (goHomeButton) {
        goHomeButton.addEventListener("click", function () {
            goHomeButton.disabled = true;
            const csrfToken = getCookie('csrftoken');
          
			fetch('/cleanup_temp_files/', {
          		method: 'POST',
          		headers: {
              		'X-CSRFToken': getCookie('csrftoken')
          		}
      		})
      		.then(response => response.json())
      		.catch(error => console.error('Error cleaning up temp files:', error));
          
            fetch('/restore_quiz_count/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrfToken,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({})
            })
            .then(response => response.json())
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


