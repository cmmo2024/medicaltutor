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

// Enhanced cleanup function for temp files
function cleanup_temp_files() {
    return fetch('/cleanup_temp_files/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken(),
            'X-Requested-With': 'XMLHttpRequest'
        },
        credentials: 'same-origin'
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        console.log('Cleanup successful:', data);
        return data;
    })
    .catch(error => {
        console.error('Error cleaning up temp files:', error);
        // Don't throw error to allow navigation to continue
        return { status: 'error', error: error.message };
    });
}

// Function to close modal dialogs
function closeModalDialog() {
    // Close question dialog
    const questionDialog = document.getElementById('question-dialog');
    if (questionDialog) {
        questionDialog.style.display = 'none';
    }
    
    // Close chat confirmation dialog
    const chatDialog = document.getElementById('chat-confirmation-dialog');
    if (chatDialog) {
        chatDialog.style.display = 'none';
    }
    
    // Hide overlay
    const overlay = document.getElementById('overlay');
    if (overlay) {
        overlay.style.display = 'none';
    }
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

            // Update subject name in modal when accordion is clicked
            selectedSubject = this.getAttribute('data-subject');
            const subjectNameSpan = document.getElementById('subject-name');
            if (subjectNameSpan) {
                subjectNameSpan.textContent = selectedSubject;
            }

            // Enable Ejercitar button if user has paid plan
            const exerciseButton = document.getElementById('ask-questions-btn');
            const generalTestRadio = document.querySelector('input[name="question-type"][value="general"]:not([disabled])');
            if (exerciseButton && generalTestRadio) {
                exerciseButton.disabled = false;
            }
        });
    }

    // Handle "Regresar al chat" button click
    const confirmGoHomeButton = document.getElementById('confirm-go-home-button');
    if (confirmGoHomeButton) {
        confirmGoHomeButton.addEventListener('click', async function(event) {
            event.preventDefault();
            
            // Disable button to prevent multiple clicks
            confirmGoHomeButton.disabled = true;
            confirmGoHomeButton.textContent = 'Procesando...';
            
            try {
                // Step 1: Clean up temporary files
                console.log('Cleaning up temporary files...');
                await cleanup_temp_files();
                
                // Step 2: Close modal dialog
                console.log('Closing modal dialog...');
                closeModalDialog();
                
                // Step 3: Navigate back to chat interface
                console.log('Navigating to chat...');
                window.location.href = '/chat/';
                
            } catch (error) {
                console.error('Error during cleanup process:', error);
                
                // Re-enable button and restore text
                confirmGoHomeButton.disabled = false;
                confirmGoHomeButton.textContent = 'Regresar al chat';
                
                // Still navigate to chat even if cleanup fails
                alert('Hubo un problema al limpiar archivos temporales, pero continuaremos al chat.');
                window.location.href = '/chat/';
            }
        });
    }

    // Get session data from server
    fetch('/get_session_data/', {
        method: 'GET',
        headers: {
            'X-CSRFToken': getCSRFToken(),
            'X-Requested-With': 'XMLHttpRequest'
        },
        credentials: 'same-origin'
    })
    .then(response => response.json())
    .then(data => {
        if (data.subject && data.topic) {
            selectedSubject = data.subject;
            
            // Store in localStorage for navigation
            localStorage.setItem('currentSubject', data.subject);
            localStorage.setItem('currentTopic', data.topic);
            if (data.chat_content) {
                localStorage.setItem('lastChatContent', data.chat_content);
            }
            
            // Update modal dialog immediately
            const subjectNameSpan = document.getElementById('subject-name');
            const topicNameSpan = document.getElementById('topic-name');
            if (subjectNameSpan) subjectNameSpan.textContent = data.subject;
            if (topicNameSpan) topicNameSpan.textContent = data.topic;
            
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

            // Enable Ejercitar button if user has paid plan
            const exerciseButton = document.getElementById('ask-questions-btn');
            const generalTestRadio = document.querySelector('input[name="question-type"][value="general"]:not([disabled])');
            if (exerciseButton && generalTestRadio) {
                exerciseButton.disabled = false;
            }
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
    localStorage.setItem('currentSubject', selectedSubject);
    
    // Update subject name in modal immediately
    const subjectNameSpan = document.getElementById('subject-name');
    if (subjectNameSpan) {
        subjectNameSpan.textContent = selectedSubject;
    }

    // Enable Ejercitar button if user has paid plan
    const exerciseButton = document.getElementById('ask-questions-btn');
    const generalTestRadio = document.querySelector('input[name="question-type"][value="general"]:not([disabled])');
    if (exerciseButton && generalTestRadio) {
        exerciseButton.disabled = false;
    }
    
    // Update session data
    updateSessionData(selectedSubject, null);
}

function loadTopic(topic, savedContent = null) {
    const chatContent = document.getElementById('chat-content');
    
    // Get the parent accordion (subject) if not already selected
    if (!selectedSubject) {
        const topicElement = document.querySelector(`li:contains('${topic}')`);
        if (topicElement) {
            const accordion = topicElement.closest('.panel').previousElementSibling;
            if (accordion) {
                selectedSubject = accordion.getAttribute('data-subject');
                localStorage.setItem('currentSubject', selectedSubject);
                // Update subject name in modal immediately
                const subjectNameSpan = document.getElementById('subject-name');
                if (subjectNameSpan) {
                    subjectNameSpan.textContent = selectedSubject;
                }
            }
        }
    }
    
    document.getElementById('topic-title').innerText = topic;
    // Update topic name in modal immediately
    const topicNameSpan = document.getElementById('topic-name');
    if (topicNameSpan) {
        topicNameSpan.textContent = topic;
    }
    localStorage.setItem('currentTopic', topic);

    if (savedContent) {
        chatContent.innerHTML = savedContent;
        localStorage.setItem('lastChatContent', savedContent);
        hasGPTResponded = chatContent.querySelector('.bot-message') !== null;
    } else if (chatJustCleared || chatContent.innerHTML.trim() === "") {
        const welcomeMessage = `<p>Comenzemos a repasar sobre ${topic}. No dudes en hacer preguntas!</p>`;
        chatContent.innerHTML = welcomeMessage;
        localStorage.setItem('lastChatContent', welcomeMessage);
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
        localStorage.setItem('lastChatContent', chatContent.innerHTML);
    }
    
    document.getElementById('user-input').disabled = false;
    document.getElementById('send-button').disabled = false;
    document.getElementById('clear-button').disabled = false;

    // Enable Ejercitar button based on user's plan
    const exerciseButton = document.getElementById('ask-questions-btn');
    const generalTestRadio = document.querySelector('input[name="question-type"][value="general"]:not([disabled])');
    if (generalTestRadio) {
        // User has paid plan - enable button immediately
        exerciseButton.disabled = false;
    } else {
        // Free user - enable button when topic is selected
        exerciseButton.disabled = false;
    }

    isTopicSelected = true;
    
    // Update session data with current subject, topic and chat content
    updateSessionData(selectedSubject, topic, chatContent.innerHTML);

    // Scroll to the bottom to show the new topic section
    chatContent.scrollTop = chatContent.scrollHeight;
}

function updateSessionData(subject, topic, chatContent) {
    fetch('/update_session/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken(),
            'X-Requested-With': 'XMLHttpRequest'
        },
        credentials: 'same-origin',
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
                localStorage.setItem('lastChatContent', chatContent.innerHTML);
                
                // For free users, enable the button after GPT responds
                const exerciseButton = document.getElementById('ask-questions-btn');
                const generalTestRadio = document.querySelector('input[name="question-type"][value="general"]:not([disabled])');
                if (!generalTestRadio) {
                    exerciseButton.disabled = false;
                }
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
                localStorage.setItem('lastChatContent', chatContent.innerHTML);
            });

        input.value = '';
    }
}

function clearChat() {
    const currentTopic = document.getElementById('topic-title').innerText;
    document.getElementById('topic-title').innerText = "Seleccione un tema para repasar";
    document.getElementById('chat-content').innerHTML = "";
    
    // Reset modal dialog text immediately
    const subjectNameSpan = document.getElementById('subject-name');
    const topicNameSpan = document.getElementById('topic-name');
    if (subjectNameSpan) subjectNameSpan.textContent = "la asignatura";
    if (topicNameSpan) topicNameSpan.textContent = "tema no seleccionado";
    
    // Update session to clear the chat
    updateSessionData(null, null, null);
    
    // Clear localStorage
    localStorage.removeItem('currentSubject');
    localStorage.removeItem('currentTopic');
    localStorage.removeItem('lastChatContent');

    // Disable buttons after clearing
    document.getElementById('user-input').disabled = true;
    document.getElementById('send-button').disabled = true;
    document.getElementById('clear-button').disabled = true;
    document.getElementById('ask-questions-btn').disabled = true;

    isTopicSelected = false;
    hasGPTResponded = false;
    chatJustCleared = true;
}

function showPlanUpgradeMessage() {
    document.getElementById('plan-upgrade-dialog').style.display = 'block';
}

function closePlanUpgradeDialog() {
    document.getElementById('plan-upgrade-dialog').style.display = 'none';
}

function toggleNav() {
    const sidebar = document.getElementById("mySidebar");
    const mainContent = document.getElementById("chat");
    const toggleButton = document.querySelector(".toggle-btn");

    if (sidebar.classList.contains("open")) {
        sidebar.classList.remove("open");
        sidebar.style.width = "0";
        mainContent.style.marginLeft = "0";
        toggleButton.innerHTML = "&#9776;";
    } else {
        sidebar.classList.add("open");
        sidebar.style.width = "250px";
        mainContent.style.marginLeft = "250px";
        toggleButton.innerHTML = "&times;";
    }
}

function handleKeyPress(event) {
    if (event.key === 'Enter') {
        sendMessage();
    }
}

function showQuestionDialog() {
    fetch('/check_quiz_limit/')
        .then(response => response.json())
        .then(data => {
            if (data.can_take_quiz) {
                document.getElementById('question-dialog').style.display = 'block';
            } else {
                const chatContent = document.getElementById('chat-content');
                const limitMessageElement = document.createElement('div');
                limitMessageElement.className = 'error-message';
                limitMessageElement.textContent = data.message || 'Has alcanzado el límite de cuestionarios en tu plan actual. ' +
                    'Puedes seguir haciendo preguntas o adquirir un nuevo plan.';
                chatContent.appendChild(limitMessageElement);
                
                setTimeout(() => {
                    limitMessageElement.style.opacity = '0';
                    limitMessageElement.style.transform = 'translateY(-10px)';
                    setTimeout(() => {
                        limitMessageElement.remove();
                    }, 300);
                }, 5000);
                
                localStorage.setItem('lastChatContent', chatContent.innerHTML);
            }
        })
        .catch(error => {
            console.error('Error checking quiz limit:', error);
            const chatContent = document.getElementById('chat-content');
            const errorMessageElement = document.createElement('div');
            errorMessageElement.className = 'error-message';
            errorMessageElement.textContent = 'Error al verificar el límite de cuestionarios. Por favor intente nuevamente.';
            chatContent.appendChild(errorMessageElement);
            localStorage.setItem('lastChatContent', chatContent.innerHTML);
        });
}

function closeQuestionDialog() {
    document.getElementById('question-dialog').style.display = 'none';
}

function continueToNextPage() {
    const selectedOption = document.querySelector('input[name="question-count"]:checked');
    const selectedQuestionType = document.querySelector('input[name="question-type"]:checked');

    if (selectedOption && selectedQuestionType) {
        const numQuestions = parseInt(selectedOption.value, 10);
        const questionType = selectedQuestionType.value;
        
        closeQuestionDialog();
        document.getElementById('loading-dialog').style.display = 'block';
        generateQuestions(numQuestions, questionType);
    } else {
        alert('Por favor selecciona el número de preguntas y el tipo de test.');
    }
}

function generateQuestions(numQuestions, questionType = 'topic') {
    const currentSubject = localStorage.getItem('currentSubject');
    const currentTopic = localStorage.getItem('currentTopic');
    const chatContent = localStorage.getItem('lastChatContent');

    if (!currentSubject) {
        alert('Error: No se pudo determinar la asignatura.');
        const loadingDialog = document.getElementById('loading-dialog');
        if (loadingDialog) {
            loadingDialog.style.display = 'none';
        }
        return;
    }

    // For topic-specific tests, we need a topic
    if (questionType === 'topic' && !currentTopic) {
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
            'X-CSRFToken': getCSRFToken(),
            'X-Requested-With': 'XMLHttpRequest'
        },
        credentials: 'same-origin',
        body: JSON.stringify({
            topic: questionType === 'topic' ? currentTopic : '',
            subject: currentSubject,
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

window.onload = function() {
    const chatContent = document.getElementById('chat-content');
    const topicTitle = document.getElementById('topic-title');
    
    const savedSubject = localStorage.getItem('currentSubject');
    const savedTopic = localStorage.getItem('currentTopic');
    const savedContent = localStorage.getItem('lastChatContent');
    
    if (savedSubject && savedTopic) {
        selectedSubject = savedSubject;
        topicTitle.innerText = savedTopic;
        
        // Update modal dialog immediately
        const subjectNameSpan = document.getElementById('subject-name');
        const topicNameSpan = document.getElementById('topic-name');
        if (subjectNameSpan) subjectNameSpan.textContent = savedSubject;
        if (topicNameSpan) topicNameSpan.textContent = savedTopic;
        
        if (savedContent) {
            chatContent.innerHTML = savedContent;
            hasGPTResponded = chatContent.querySelector('.bot-message') !== null;
        }
        isTopicSelected = true;
        
        document.getElementById('user-input').disabled = false;
        document.getElementById('send-button').disabled = false;
        document.getElementById('clear-button').disabled = false;

        // Enable Ejercitar button based on user's plan
        const exerciseButton = document.getElementById('ask-questions-btn');
        const generalTestRadio = document.querySelector('input[name="question-type"][value="general"]:not([disabled])');
        if (generalTestRadio) {
            // User has paid plan - enable button immediately
            exerciseButton.disabled = false;
        } else {
            // Free user - enable button only when topic is selected
            exerciseButton.disabled = false;
        }
    } else {
        document.getElementById('user-input').disabled = true;
        document.getElementById('send-button').disabled = true;
        document.getElementById('clear-button').disabled = true;
        document.getElementById('ask-questions-btn').disabled = true;
    }
};
