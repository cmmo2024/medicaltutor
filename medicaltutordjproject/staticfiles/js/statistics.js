document.addEventListener('DOMContentLoaded', function() {
    // Format date to local timezone
    function formatLocalDate(timestamp) {
        if (!timestamp) return "Sin actividad";
        const date = new Date(timestamp);
        return date.toLocaleString('es', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
            hour12: true
        });
    }

    // Update last activity timestamp
    const lastActivity = document.getElementById('last-activity');
    if (lastActivity) {
        const timestamp = lastActivity.getAttribute('data-timestamp');
        lastActivity.textContent = formatLocalDate(timestamp);
    }

    // Update all quiz timestamps
    document.querySelectorAll('.quiz-date').forEach(element => {
        const timestamp = element.getAttribute('data-timestamp');
        element.textContent = formatLocalDate(timestamp);
    });
});
