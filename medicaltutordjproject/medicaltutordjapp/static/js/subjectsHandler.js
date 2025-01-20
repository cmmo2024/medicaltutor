// Add this at the beginning of your file
let selectedSubject = "";

// Track whether a topic is selected and whether GPT has responded at least once
let isTopicSelected = false;
let hasGPTResponded = false;

// Accordion functionality
document.addEventListener("DOMContentLoaded", function () {
    var acc = document.getElementsByClassName("accordion");
    for (var i = 0; i < acc.length; i++) {
        acc[i].addEventListener("click", function () {
            // Toggle active class for the accordion button
            this.classList.toggle("active");

            // Toggle display of the associated panel
            var panel = this.nextElementSibling;
            if (panel.style.display === "block") {
                panel.style.display = "none";
            } else {
                panel.style.display = "block";
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
}

function loadTopic(topic) {
    const chatContent = document.getElementById('chat-content');
    
    localStorage.setItem('selectedTopic', topic);
    document.getElementById('topic-title').innerText = topic;

    chatContent.innerHTML = `<p>Comenzemos a repasar sobre ${topic}. No dudes en hacer preguntas!</p>`;

    document.getElementById('user-input').disabled = false;
    document.getElementById('send-button').disabled = false;
    document.getElementById('clear-button').disabled = false;
    document.getElementById('ask-questions-btn').disabled = true;
    document.getElementById('share-button').disabled = true;

    isTopicSelected = true;
    hasGPTResponded = false;
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

function sendMessage() {
    const input = document.getElementById('user-input');
    const chatContent = document.getElementById('chat-content');
    const loadingIndicator = document.getElementById('loading-indicator');
    const userMessage = input.value;
    const topic = document.getElementById('topic-title').innerText.trim(); // Current topic

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

                // Display GPT's response as Markdown
                const botMessageElement = document.createElement('div');
                botMessageElement.className = 'bot-message';
                botMessageElement.innerHTML = marked.parse(data.response); // Render Markdown
                chatContent.appendChild(botMessageElement);

                // Enable "Ask Me Questions" button after GPT responds
                hasGPTResponded = true;
                saveConversation(chatContent);
                document.getElementById('ask-questions-btn').disabled = false;
                document.getElementById('share-button').disabled = false;
            })
            .catch(error => {
                console.error('Error fetching GPT response:', error);

                // Hide loading animation
                loadingIndicator.style.display = 'none';

                // Display an error message in the chat
                const errorMessageElement = document.createElement('div');
                errorMessageElement.className = 'error-message';
                errorMessageElement.textContent = "⚠️ Connection interrupted. Please try again.";
                chatContent.appendChild(errorMessageElement);
            });

        input.value = ''; // Clear input after sending
    }
}

// Load conversation from localStorage when the page is loaded
function loadConversation() {
    const chatContent = document.getElementById("chat-content");
    const savedConversation = localStorage.getItem("chatConversation");
    if (savedConversation) {
        chatContent.innerHTML = savedConversation;
    }
}

// Save conversation to localStorage
function saveConversation(chatContent) {
    localStorage.setItem("chatConversation", chatContent.innerHTML);
}

function clearChat() {
    document.getElementById('topic-title').innerText = "Seleccione un tema para repasar";
    document.getElementById('chat-content').innerHTML = "";
    localStorage.removeItem("chatConversation");

    // Optionally disable buttons after clearing
    document.getElementById('user-input').disabled = true;
    document.getElementById('send-button').disabled = true;
    document.getElementById('clear-button').disabled = true;
    document.getElementById('ask-questions-btn').disabled = true;
    document.getElementById('share-button').disabled = true;

    isTopicSelected = false;
}

// Handle 'Enter' key to send message
function handleKeyPress(event) {
    if (event.key === 'Enter') {
        sendMessage();
    }
}

// Show the question selection dialog
function showQuestionDialog() {
    document.getElementById('question-dialog').style.display = 'block';
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
        // Hide the loading dialog regardless of success or failure .finally(() => {
        // Hide the loading dialog regardless of success or failure
        document.getElementById('loading-dialog').style.display = 'none';
    });
}

// Helper to get CSRF token
function getCSRFToken() {
    return document.cookie.split('; ').find(row => row.startsWith('csrftoken')).split('=')[1];
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
    loadConversation();
    
    document.getElementById('user-input').disabled = false;
    document.getElementById('send-button').disabled = false;
    document.getElementById('clear-button').disabled = false;
    document.getElementById('ask-questions-btn').disabled = false;
    document.getElementById('share-button').disabled = false;
};