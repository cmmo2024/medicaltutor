// Add this at the beginning of your file
let selectedSubject = "";
let isTopicSelected = false;
let hasGPTResponded = false;
let chatJustCleared = false; // New flag to track if chat was just cleared

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

    // Load saved subject and topic if they exist
    const savedSubject = localStorage.getItem('selectedSubject');
    const savedTopic = localStorage.getItem('selectedTopic');
    
    if (savedSubject && savedTopic) {
        selectedSubject = savedSubject;
        updateSessionData(savedSubject, savedTopic);
        
        // Find and activate the correct accordion
        const accordions = document.querySelectorAll('.accordion');
        accordions.forEach(accordion => {
            if (accordion.getAttribute('data-subject') === savedSubject) {
                accordion.classList.add('active');
                const panel = accordion.nextElementSibling;
                if (panel) {
                    panel.style.display = 'block';
                }
            }
        });
    }
});

function selectSubject(element) {
    // Remove "active" class from all subjects
    const allSubjects = document.querySelectorAll('.sidebar .accordion');
    allSubjects.forEach(subject => subject.classList.remove('active'));

    // Add "active" class to the clicked subject
    element.classList.add('active');

    // Update the selected subject
    selectedSubject = element.getAttribute('data-subject');
    
    // Store the selected subject in localStorage
    localStorage.setItem('selectedSubject', selectedSubject);
}

function updateSessionData(subject, topic) {
    fetch('/update_session/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        },
        body: JSON.stringify({
            subject: subject,
            topic: topic
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

function loadTopic(topic) {
    const chatContent = document.getElementById('chat-content');
    
    localStorage.setItem('selectedTopic', topic);
    document.getElementById('topic-title').innerText = topic;

    if (chatJustCleared || chatContent.innerHTML.trim() === "") {
        // If chat was just cleared or is empty, just add the welcome message
        chatContent.innerHTML = `<p>Comenzemos a repasar sobre ${topic}. No dudes en hacer preguntas!</p>`;
        chatJustCleared = false; // Reset the flag
    } else {
        // If chat has content, add separator and new topic section
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
    
    saveChatContent();
    
    document.getElementById('user-input').disabled = false;
    document.getElementById('send-button').disabled = false;
    document.getElementById('clear-button').disabled = false;
    document.getElementById('ask-questions-btn').disabled = !hasGPTResponded;
    document.getElementById('share-button').disabled = !hasGPTResponded;

    isTopicSelected = true;
    
    // Update session data with current subject and topic
    updateSessionData(selectedSubject, topic);

    // Scroll to the bottom to show the new topic section
    chatContent.scrollTop = chatContent.scrollHeight;
}

// Save chat content whenever it changes
function saveChatContent() {
    const chatContent = document.getElementById('chat-content');
    const currentTopic = document.getElementById('topic-title').innerText;
    if (currentTopic && currentTopic !== 'Seleccione un tema para repasar') {
        localStorage.setItem(`chat_${currentTopic}`, chatContent.innerHTML);
    }
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

        // Send request to Django view to get GPT response
        fetch(`/ask_gpt?subject=${encodeURIComponent(selectedSubject)}&topic=${encodeURIComponent(topic)}&message=${encodeURIComponent(userMessage)}`)
            .then(response => response.json())
            .then(data => {
                // Hide loading animation
                loadingIndicator.style.display = 'none';

                if (data.error) {
                    // Display error message in chat with fade-out effect
                    const errorMessageElement = document.createElement('div');
                    errorMessageElement.className = 'error-message';
                    errorMessageElement.textContent = data.error;
                    chatContent.appendChild(errorMessageElement);
                    
                    // Remove the error message after 5 seconds
                    setTimeout(() => {
                        errorMessageElement.style.opacity = '0';
                        errorMessageElement.style.transform = 'translateY(-10px)';
                        setTimeout(() => {
                            errorMessageElement.remove();
                        }, 300);
                    }, 5000);
                } else {
                    // Display GPT's response as Markdown
                    const botMessageElement = document.createElement('div');
                    botMessageElement.className = 'bot-message';
                    botMessageElement.innerHTML = marked.parse(data.response);
                    chatContent.appendChild(botMessageElement);

                    // Enable "Ask Me Questions" button after GPT responds
                    hasGPTResponded = true;
                }
                saveChatContent();
                document.getElementById('ask-questions-btn').disabled = false;
                document.getElementById('share-button').disabled = false;
            })
            .catch(error => {
                console.error('Error fetching GPT response:', error);
                loadingIndicator.style.display = 'none';
                const errorMessageElement = document.createElement('div');
                errorMessageElement.className = 'error-message';
                errorMessageElement.textContent = "⚠️ Conexión interrumpida. Por favor intente de nuevo.";
                chatContent.appendChild(errorMessageElement);
                saveChatContent();
            });

        input.value = '';
    }
}

function clearChat() {
    const currentTopic = document.getElementById('topic-title').innerText;
    document.getElementById('topic-title').innerText = "Seleccione un tema para repasar";
    document.getElementById('chat-content').innerHTML = "";
    
    // Clear stored chat for current topic
    if (currentTopic && currentTopic !== 'Seleccione un tema para repasar') {
        localStorage.removeItem(`chat_${currentTopic}`);
    }

    // Disable buttons after clearing
    document.getElementById('user-input').disabled = true;
    document.getElementById('send-button').disabled = true;
    document.getElementById('clear-button').disabled = true;
    document.getElementById('ask-questions-btn').disabled = true;
    document.getElementById('share-button').disabled = true;

    isTopicSelected = false;
    hasGPTResponded = false;
    chatJustCleared = true; // Set the flag when chat is cleared
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

function shareChatContent() {
    const chatContent = document.getElementById('chat-content').innerText.trim(); // Get the text content of the chat

    if (!chatContent) {
        alert('There is no chat content to share.');
        return;
    }

    if (navigator.share) {
        // Use the Web Share API
        navigator.share({
            title: 'Revisa esta conversación del Tutor Médico',
            text: chatContent,
            url: generateShareableLink(chatContent)
        })
        .then(() => console.log('Content shared successfully!'))
        .catch((error) => console.error('Error sharing content:', error));
    } else {
        // Fallback for unsupported browsers: Generate a shareable link
        const shareableLink = generateShareableLink(chatContent);
        alert(`Sharing is not supported on this browser. Here is your shareable link:\n\n${shareableLink}`);
    }
}

// Helper function to generate a shareable link
function generateShareableLink(chatContent) {
    const baseUrl = window.location.origin + window.location.pathname; // Base URL of the current page
    const encodedContent = encodeURIComponent(chatContent); // Encode the chat content for safe use in a URL
    return `${baseUrl}?sharedChat=${encodedContent}`;
}

// Optionally, function to load chat content from URL on page load
function loadSharedChat() {
    const urlParams = new URLSearchParams(window.location.search);
    const sharedChat = urlParams.get('sharedChat');
    if (sharedChat) {
        const chatContent = decodeURIComponent(sharedChat); // Decode the chat content
        document.getElementById('chat-content').innerText = chatContent; // Populate the chat area with the shared content
    }
}

// Call loadSharedChat when the page loads
document.addEventListener('DOMContentLoaded', loadSharedChat);

// Disable input and buttons by default until a topic is selected
window.onload = function () {
    document.getElementById('topic-title').innerText = localStorage.getItem('selectedTopic');
    const savedTopic = localStorage.getItem('selectedTopic');
    if (savedTopic) {
        const savedChat = localStorage.getItem(`chat_${savedTopic}`);
        
        isTopicSelected = true;
                
        if (savedChat) {
            document.getElementById('chat-content').innerHTML = savedChat;
            hasGPTResponded = true;
        }
    }
    
    document.getElementById('user-input').disabled = !isTopicSelected;
    document.getElementById('send-button').disabled = !isTopicSelected;
    document.getElementById('clear-button').disabled = !isTopicSelected;
    document.getElementById('ask-questions-btn').disabled = !hasGPTResponded;
    document.getElementById('share-button').disabled = !hasGPTResponded;
};