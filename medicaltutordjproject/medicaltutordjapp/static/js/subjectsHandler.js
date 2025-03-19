// Add this at the beginning of your file
let selectedSubject = "";
let isTopicSelected = false;
let hasGPTResponded = false;
let chatJustCleared = false;

// Get CSRF token from cookies
function getCSRFToken() {
    const name = 'csrftoken';
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

// Accordion functionality
document.addEventListener("DOMContentLoaded", function () {
    var acc = document.getElementsByClassName("accordion");
    for (var i = 0; i < acc.length; i++) {
        acc[i].addEventListener("click", function () {
            this.classList.toggle("active");
            var panel = this.nextElementSibling;
            if (panel.style.display === "block") {
                panel.style.display = "none";
            } else {
                panel.style.display = "block";
            }
        });
    }

    // Get session data from server
    fetch('/get_session_data/', {
        method: 'GET',
        headers: {
            'X-CSRFToken': getCSRFToken()
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.subject && data.topic) {
            selectedSubject = data.subject;
            
            // Find and activate the correct accordion
            const accordions = document.querySelectorAll('.accordion');
            accordions.forEach(accordion => {
                if (accordion.getAttribute('data-subject') === data.subject) {
                    accordion.classList.add('active');
                    const panel = accordion.nextElementSibling;
                    if (panel) {
                        panel.style.display = 'block';
                    }
                }
            });

            // Load the topic if it exists
            loadTopic(data.topic, data.chat_content);
        }
    })
    .catch(error => {
        console.error('Error loading session data:', error);
    });
});

function selectSubject(element) {
    // Remove "active" class from all subjects
    const allSubjects = document.querySelectorAll('.sidebar .accordion');
    allSubjects.forEach(subject => subject.classList.remove('active'));

    // Add "active" class to the clicked subject
    element.classList.add('active');

    // Update the selected subject
    selectedSubject = element.getAttribute('data-subject');
    
    // Update session data
    updateSessionData(selectedSubject, null);
}

// Update the updateSessionData function
function updateSessionData(subject, topic, chatContent) {
    fetch('/update_session/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        },
        body: JSON.stringify({
            subject: subject,
            topic: topic,
            chat_content: chatContent
        })
    })
    .then(response => response.json())
    .then(data => {
        if (!data.status === 'success') {
            console.error('Failed to update session data');
        }
    })
    .catch(error => {
        console.error('Error updating session:', error);
    });
}

function loadTopic(topic, savedContent = null) {
    const chatContent = document.getElementById('chat-content');
    
    document.getElementById('topic-title').innerText = topic;

    if (savedContent) {
        chatContent.innerHTML = savedContent;
        hasGPTResponded = chatContent.querySelector('.bot-message') !== null;
    } else if (chatJustCleared || chatContent.innerHTML.trim() === "") {
        chatContent.innerHTML = `<p>Comenzemos a repasar sobre ${topic}. No dudes en hacer preguntas!</p>`;
        chatJustCleared = false;
    } else {
        const topicSeparator = document.createElement('div');
        topicSeparator.style.borderTop = '2px solid #ccc';
        topicSeparator.style.margin = '20px 0';
        topicSeparator.style.padding = '10px 0';
        topicSeparator.innerHTML = `<strong>Nuevo tema: ${topic}</strong>`;
        chatContent.appendChild(topicSeparator);

        const welcomeMessage = document.createElement('p');
        welcomeMessage.textContent = `Comenzemos a repasar sobre ${topic}. No dudes en hacer preguntas!`;
        chatContent.appendChild(welcomeMessage);
    }
    
    document.getElementById('user-input').disabled = false;
    document.getElementById('send-button').disabled = false;
    document.getElementById('clear-button').disabled = false;
    document.getElementById('ask-questions-btn').disabled = !hasGPTResponded;

    isTopicSelected = true;
    
    // Update session data with current subject, topic and chat content
    updateSessionData(selectedSubject, topic, chatContent.innerHTML);

    // Scroll to the bottom to show the new topic section
    chatContent.scrollTop = chatContent.scrollHeight;
}

function sendMessage() {
    const input = document.getElementById('user-input');
    const chatContent = document.getElementById('chat-content');
    const loadingIndicator = document.getElementById('loading-indicator');
    const userMessage = input.value;
    const topic = document.getElementById('topic-title').innerText.trim();

    if (!selectedSubject) {
        alert("Please select a subject first.");
        return;
    }

    if (userMessage.trim()) {
        // Display user message in the chat
        const userMessageElement = document.createElement('p');
        userMessageElement.className = 'user-message';
        userMessageElement.textContent = userMessage;
        chatContent.appendChild(userMessageElement);

        // Show loading animation
        loadingIndicator.style.display = 'block';

        // Send request to Django view
        fetch(`/ask_gpt?subject=${encodeURIComponent(selectedSubject)}&topic=${encodeURIComponent(topic)}&message=${encodeURIComponent(userMessage)}`)
            .then(response => response.json())
            .then(data => {
                loadingIndicator.style.display = 'none';

                if (data.error) {
                    const errorMessageElement = document.createElement('div');
                    errorMessageElement.className = 'error-message';
                    errorMessageElement.textContent = data.error;
                    chatContent.appendChild(errorMessageElement);
                    
                    setTimeout(() => {
                        errorMessageElement.style.opacity = '0';
                        errorMessageElement.style.transform = 'translateY(-10px)';
                        setTimeout(() => {
                            errorMessageElement.remove();
                        }, 300);
                    }, 5000);
                } else {
                    const botMessageContainer = document.createElement('div');
                    botMessageContainer.className = 'bot-message-container';

                    const botMessageElement = document.createElement('div');
                    botMessageElement.className = 'bot-message';
                    botMessageElement.innerHTML = marked.parse(data.response);

                    const copyButton = document.createElement('button');
                    copyButton.className = 'copy-button';
                    copyButton.innerHTML = '📋';
                    copyButton.title = 'Copiar respuesta';
                    copyButton.onclick = function() {
                        navigator.clipboard.writeText(data.response)
                            .then(() => {
                                // Visual feedback
                                copyButton.innerHTML = '✓';
                                setTimeout(() => {
                                    copyButton.innerHTML = '📋';
                                }, 2000);
                            })
                            .catch(err => {
                                console.error('Error copying text:', err);
                                copyButton.innerHTML = '❌';
                                setTimeout(() => {
                                    copyButton.innerHTML = '📋';
                                }, 2000);
                            });
                    };

                    botMessageContainer.appendChild(botMessageElement);
                    botMessageContainer.appendChild(copyButton);
                    chatContent.appendChild(botMessageContainer);
                    hasGPTResponded = true;
                }

                // Update session with new chat content
                updateSessionData(selectedSubject, topic, chatContent.innerHTML);
                
                document.getElementById('ask-questions-btn').disabled = false;
            })
            .catch(error => {
                console.error('Error:', error);
                loadingIndicator.style.display = 'none';
                const errorMessageElement = document.createElement('div');
                errorMessageElement.className = 'error-message';
                errorMessageElement.textContent = "⚠️ Conexión interrumpida. Por favor intente de nuevo.";
                chatContent.appendChild(errorMessageElement);
                
                // Update session even on error to preserve the error message
                updateSessionData(selectedSubject, topic, chatContent.innerHTML);
            });

        input.value = '';
    }
}

function clearChat() {
    const currentTopic = document.getElementById('topic-title').innerText;
    document.getElementById('topic-title').innerText = "Seleccione un tema para repasar";
    document.getElementById('chat-content').innerHTML = "";
    
    // Update session to clear the chat
    updateSessionData(null, null, null);

    // Disable buttons after clearing
    document.getElementById('user-input').disabled = true;
    document.getElementById('send-button').disabled = true;
    document.getElementById('clear-button').disabled = true;
    document.getElementById('ask-questions-btn').disabled = true;

    isTopicSelected = false;
    hasGPTResponded = false;
    chatJustCleared = true;
}

// Function to show plan upgrade message
function showPlanUpgradeMessage() {
    document.getElementById('plan-upgrade-dialog').style.display = 'block';
}

// Function to close plan upgrade dialog
function closePlanUpgradeDialog() {
    document.getElementById('plan-upgrade-dialog').style.display = 'none';
}

// Toggle sidebar navigation
function toggleNav() {
    const sidebar = document.getElementById("mySidebar");
    const mainContent = document.getElementById("chat");
    const toggleButton = document.querySelector(".toggle-btn");

    if (sidebar.classList.contains("open")) {
        // Close the sidebar
        sidebar.classList.remove("open");
        sidebar.style.width = "0"; // Fully collapse the sidebar
        mainContent.style.marginLeft = "0"; // Chat panel covers the sidebar
        toggleButton.innerHTML = "&#9776;"; // Hamburger icon
    } else {
        // Open the sidebar
        sidebar.classList.add("open");
        sidebar.style.width = "250px"; // Adjust to sidebar width
        mainContent.style.marginLeft = "250px"; // Align chat panel
        toggleButton.innerHTML = "&times;"; // Close (X) icon
    }
}

// Handle 'Enter' key to send message
function handleKeyPress(event) {
    if (event.key === 'Enter') {
        sendMessage();
    }
}

function showQuestionDialog() {
    // Check if user has a paid plan with remaining quizzes
    fetch('/check_quiz_limit/')
        .then(response => response.json())
        .then(data => {
            if (data.can_take_quiz) {
                document.getElementById('question-dialog').style.display = 'block';
            } else {
                // Display message in chat that quiz limit is reached with fade-out effect
                const chatContent = document.getElementById('chat-content');
                const limitMessageElement = document.createElement('div');
                limitMessageElement.className = 'error-message';
                limitMessageElement.textContent = data.message || 'Has alcanzado el límite de cuestionarios en tu plan actual. ' +
                    'Puedes seguir haciendo preguntas o adquirir un nuevo plan.';
                chatContent.appendChild(limitMessageElement);
                
                // Remove the error message after 5 seconds
                setTimeout(() => {
                    limitMessageElement.style.opacity = '0';
                    limitMessageElement.style.transform = 'translateY(-10px)';
                    setTimeout(() => {
                        limitMessageElement.remove();
                    }, 300);
                }, 5000);
                
                saveChatContent();
            }
        })
        .catch(error => {
            console.error('Error checking quiz limit:', error);
            const chatContent = document.getElementById('chat-content');
            const errorMessageElement = document.createElement('div');
            errorMessageElement.className = 'error-message';
            errorMessageElement.textContent = 'Error al verificar el límite de cuestionarios. Por favor intente nuevamente.';
            chatContent.appendChild(errorMessageElement);
            saveChatContent();
        });
}

// Close the question selection dialog
function closeQuestionDialog() {
    document.getElementById('question-dialog').style.display = 'none';
}

function continueToNextPage() {
    const selectedOption = document.querySelector('input[name="question-count"]:checked');

    if (selectedOption) {
        const numQuestions = parseInt(selectedOption.value, 10);

        // Close the question selection dialog
        closeQuestionDialog();

        // Show the loading dialog
        document.getElementById('loading-dialog').style.display = 'block';

        generateQuestions(numQuestions); // Call your generateQuestions method
    } else {
        alert('Please select the number of questions.');
    }
}

function generateQuestions(numQuestions) {
    const topic = document.getElementById('topic-title').innerText.trim(); // Ensure no leading/trailing whitespace
    const chatContent = document.getElementById('chat-content').innerText.trim(); // Get conversation text from chat content

    if (!chatContent) {
        alert('The conversation is empty. Start a conversation before generating questions.');
        document.getElementById('loading-dialog').style.display = 'none'; // Hide loading dialog
        return;
    }

    fetch(`/generate_questions/`, { // Use the generate endpoint for POST
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        },
        body: JSON.stringify({
            topic,
            numQuestions,
            conversation: chatContent // Include conversation in the request payload
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
        alert('An error occurred while generating questions. Please try again later.');
    })
    .finally(() => {
        // Hide the loading dialog regardless of success or failure
        document.getElementById('loading-dialog').style.display = 'none';
    });
}

// Update the window.onload function
window.onload = function() {
    // Initialize UI state
    const chatContent = document.getElementById('chat-content');
    const topicTitle = document.getElementById('topic-title');
    
    // Restore chat state if available
    if (window.initialChatState) {
        if (window.initialChatState.content) {
            chatContent.innerHTML = window.initialChatState.content;
            hasGPTResponded = true;
        }
        
        if (window.initialChatState.topic) {
            topicTitle.innerText = window.initialChatState.topic;
            selectedSubject = window.initialChatState.subject;
            isTopicSelected = true;
            
            // Enable buttons if we have a topic
            document.getElementById('user-input').disabled = false;
            document.getElementById('send-button').disabled = false;
            document.getElementById('clear-button').disabled = false;
            document.getElementById('ask-questions-btn').disabled = !hasGPTResponded;
        } else {
            // Default state - everything disabled
            document.getElementById('user-input').disabled = true;
            document.getElementById('send-button').disabled = true;
            document.getElementById('clear-button').disabled = true;
            document.getElementById('ask-questions-btn').disabled = true;
        }
    }
};