document.addEventListener("DOMContentLoaded", function () {
    var form = document.getElementById("questions-form");
    var dialog = document.getElementById("confirmation-dialog");
    var overlay = document.getElementById("overlay");

    // Close the confirmation dialog
    function closeDialog() {
        dialog.style.display = "none";
        overlay.style.display = "none";
    }

    // Show the confirmation dialog
    function showDialog() {
        dialog.style.display = "block";
        overlay.style.display = "block";
    }

    // Expose functions to global scope
    window.closeDialog = closeDialog;
    window.showDialog = showDialog;

    // Intercept the form submission to show the confirmation dialog
    form.addEventListener("submit", function (event) {
        event.preventDefault(); // Prevent the default form submission
        showDialog(); // Show the confirmation dialog
    });

    form.addEventListener("submit", function (event) {
        event.preventDefault();

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
                return;
            }

            const encodedResults = encodeURIComponent(JSON.stringify(data.result));
            const encodedQuestions = encodeURIComponent(JSON.stringify(data.questions));
            window.location.href = `/qualified_answers/?score=${data.total_score}&results=${encodedResults}&questions=${encodedQuestions}`;
        })
        .catch(error => {
            console.error('Fetch request failed:', error);
            alert('An error occurred while submitting the form.');
        });
    });

    // Add event listener for "go-home-button" after DOMContentLoaded
    var homeButton = document.getElementById("go-home-button");

    if (homeButton) {
        homeButton.addEventListener("click", function (event) {
            event.preventDefault(); // Prevent default action if the button is inside a form or anchor
            event.stopPropagation(); // Stop propagation to parent elements
            window.location.href = "/";
        });
    } else {
        console.error("The 'go-home-button' was not found in the DOM.");
    }
});
