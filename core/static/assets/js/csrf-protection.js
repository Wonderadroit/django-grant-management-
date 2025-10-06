// CSRF Protection and Logout Handling
// Prevents double-clicking logout buttons which can cause CSRF errors

document.addEventListener('DOMContentLoaded', function() {
    // Get CSRF token from cookies
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

    // Prevent double-clicking on logout forms
    const logoutForms = document.querySelectorAll('form[action*="logout"]');
    logoutForms.forEach(function(form) {
        form.addEventListener('submit', function(e) {
            const submitButton = form.querySelector('button[type="submit"]');
            if (submitButton) {
                // Disable button to prevent double-click
                submitButton.disabled = true;
                submitButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Logging out...';
                
                // Re-enable after a short delay in case of error
                setTimeout(function() {
                    submitButton.disabled = false;
                    submitButton.innerHTML = submitButton.getAttribute('data-original-text') || 'Logout';
                }, 3000);
            }
        });
        
        // Store original button text
        const submitButton = form.querySelector('button[type="submit"]');
        if (submitButton && !submitButton.getAttribute('data-original-text')) {
            submitButton.setAttribute('data-original-text', submitButton.innerHTML);
        }
    });

    // Ensure CSRF token is present in all forms
    const csrfToken = getCookie('csrftoken');
    if (csrfToken) {
        const forms = document.querySelectorAll('form[method="post"]');
        forms.forEach(function(form) {
            const csrfInput = form.querySelector('input[name="csrfmiddlewaretoken"]');
            if (!csrfInput) {
                const hiddenInput = document.createElement('input');
                hiddenInput.type = 'hidden';
                hiddenInput.name = 'csrfmiddlewaretoken';
                hiddenInput.value = csrfToken;
                form.appendChild(hiddenInput);
            }
        });
    }
});

// Handle logout with proper CSRF protection
function safeLogout() {
    const csrfToken = getCookie('csrftoken');
    const form = document.createElement('form');
    form.method = 'POST';
    form.action = '/accounts/logout/';
    
    const csrfInput = document.createElement('input');
    csrfInput.type = 'hidden';
    csrfInput.name = 'csrfmiddlewaretoken';
    csrfInput.value = csrfToken;
    form.appendChild(csrfInput);
    
    document.body.appendChild(form);
    form.submit();
}