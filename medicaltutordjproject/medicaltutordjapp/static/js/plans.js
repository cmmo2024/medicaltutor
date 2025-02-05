document.addEventListener('DOMContentLoaded', function() {
    // Handle subscribe button clicks
    const subscribeButtons = document.querySelectorAll('.subscribe-btn');
    subscribeButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const planId = this.getAttribute('data-plan-id');
            const planPrice = this.getAttribute('data-plan-price');
            const form = document.getElementById('payment-form');
            
            // Set the form action with the plan ID
            form.action = `/subscribe/${planId}/`;
            
            // Set the hidden input value
            document.getElementById('selected-plan-id').value = planId;
            document.getElementById('payment-amount').textContent = planPrice;
            document.getElementById('payment-modal').style.display = 'block';
            document.body.style.overflow = 'hidden'; // Prevent background scrolling
        });
    });

    // Close modal when clicking the close button or outside
    document.querySelector('.close-modal').addEventListener('click', closeModal);

    window.addEventListener('click', function(e) {
        const modal = document.getElementById('payment-modal');
        if (e.target === modal) {
            closeModal();
        }
    });

    // Handle payment method switch
    const switchOptions = document.querySelectorAll('.switch-option');
    switchOptions.forEach(option => {
        option.addEventListener('click', function() {
            // Remove active class from all options and contents
            switchOptions.forEach(opt => opt.classList.remove('active'));
            document.querySelectorAll('.payment-method').forEach(method => {
                method.classList.remove('active');
            });

            // Add active class to clicked option and corresponding content
            this.classList.add('active');
            const methodId = this.getAttribute('data-method');
            document.getElementById(methodId).classList.add('active');
        });
    });

    // Form submission
    document.getElementById('payment-form').addEventListener('submit', function(e) {
        e.preventDefault();
        const planId = document.getElementById('selected-plan-id').value;
        const transactionId = document.getElementById('transaction-id').value;

        if (!planId) {
            showModalError('Error: Plan no seleccionado');
            return;
        }

        if (!transactionId) {
            showModalError('Por favor ingrese el número de transacción');
            return;
        }

        // Submit the form
        this.submit();
    });

    // Check for error messages in URL and restore previous plan selection
    const urlParams = new URLSearchParams(window.location.search);
    const error = urlParams.get('error');
    const previousPlanId = urlParams.get('plan_id');
    
    if (error) {
        if (previousPlanId) {
            // Find the plan button with this ID
            const planButton = document.querySelector(`.subscribe-btn[data-plan-id="${previousPlanId}"]`);
            if (planButton) {
                // Get the plan price
                const planPrice = planButton.getAttribute('data-plan-price');
                // Set the form action
                const form = document.getElementById('payment-form');
                form.action = `/subscribe/${previousPlanId}/`;
                // Update the modal with the previous plan details
                document.getElementById('selected-plan-id').value = previousPlanId;
                document.getElementById('payment-amount').textContent = planPrice;
            }
        }
        showModalError(decodeURIComponent(error));
        document.getElementById('payment-modal').style.display = 'block';
        document.body.style.overflow = 'hidden';
    }

    // Function to show error in modal
    function showModalError(message) {
        const errorDiv = document.getElementById('modal-error');
        errorDiv.textContent = message;
        errorDiv.classList.add('show');
    }

    // Function to close modal - always allow closing
    function closeModal() {
        const modal = document.getElementById('payment-modal');
        const errorDiv = document.getElementById('modal-error');
        
        modal.style.display = 'none';
        document.body.style.overflow = 'auto'; // Restore scrolling
        
        // Clear error message if any
        errorDiv.classList.remove('show');
        errorDiv.textContent = '';
        
        // Only reset the form if there was no error
        if (!urlParams.has('error')) {
            document.getElementById('payment-form').reset();
            // Reset payment method to QR
            document.querySelectorAll('.switch-option').forEach(opt => opt.classList.remove('active'));
            document.querySelector('[data-method="qr-method"]').classList.add('active');
            document.querySelectorAll('.payment-method').forEach(method => method.classList.remove('active'));
            document.getElementById('qr-method').classList.add('active');
        }
    }
});