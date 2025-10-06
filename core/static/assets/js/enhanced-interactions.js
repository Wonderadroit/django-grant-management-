// Enhanced Interactions for Grant Application System
// Professional interactions and form enhancements

document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM Content Loaded - Initializing Grant Application Enhancements');
    
    // Add a small delay to ensure all elements are fully rendered
    setTimeout(() => {
        initializeFormEnhancements();
        initializeProgressTracking();
        initializeTooltips();
        initializeNotifications();
        initializeWizard(); // This should initialize the stepper functionality
    }, 100);
});

// Form validation and enhancement functions
function validateField(event) {
    const field = event.target;
    const value = field.value.trim();
    const fieldType = field.type;
    const isRequired = field.hasAttribute('required');
    
    let isValid = true;
    let errorMessage = '';
    
    // Clear previous validation state
    field.classList.remove('is-valid', 'is-invalid');
    
    // Check if required field is empty
    if (isRequired && !value) {
        isValid = false;
        errorMessage = 'This field is required.';
    }
    
    // Email validation
    if (fieldType === 'email' && value) {
        const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailPattern.test(value)) {
            isValid = false;
            errorMessage = 'Please enter a valid email address.';
        }
    }
    
    // Phone validation
    if (field.name === 'phone' && value) {
        const phonePattern = /^[\+]?[1-9][\d]{0,15}$/;
        if (!phonePattern.test(value.replace(/[\s\-\(\)]/g, ''))) {
            isValid = false;
            errorMessage = 'Please enter a valid phone number.';
        }
    }
    
    // Apply validation styling
    field.classList.add(isValid ? 'is-valid' : 'is-invalid');
    
    // Show/hide error message
    let errorDiv = field.parentNode.querySelector('.invalid-feedback');
    if (!errorDiv) {
        errorDiv = document.createElement('div');
        errorDiv.className = 'invalid-feedback';
        field.parentNode.appendChild(errorDiv);
    }
    errorDiv.textContent = errorMessage;
    
    return isValid;
}

function initializeFormEnhancements() {
    // Real-time validation
    const inputs = document.querySelectorAll('input, textarea, select');
    inputs.forEach(input => {
        input.addEventListener('blur', validateField);
        input.addEventListener('input', debounce(validateField, 300));
    });
    
    // Character counter for textareas
    document.querySelectorAll('textarea[maxlength]').forEach(textarea => {
        const maxLength = textarea.getAttribute('maxlength');
        const counter = document.createElement('div');
        counter.className = 'character-counter text-muted small text-end';
        counter.innerHTML = `<span class="current">0</span>/${maxLength} characters`;
        textarea.parentNode.appendChild(counter);
        
        textarea.addEventListener('input', function() {
            const current = this.value.length;
            const currentSpan = counter.querySelector('.current');
            currentSpan.textContent = current;
            
            if (current > maxLength * 0.9) {
                counter.classList.add('text-warning');
            } else {
                counter.classList.remove('text-warning');
            }
            
            if (current === maxLength) {
                counter.classList.add('text-danger');
            } else {
                counter.classList.remove('text-danger');
            }
        });
    });
    
    // Enhanced file upload handling
    document.querySelectorAll('input[type="file"]').forEach(input => {
        input.addEventListener('change', function() {
            const files = this.files;
            let feedback = this.parentNode.querySelector('.file-feedback');
            
            if (!feedback) {
                feedback = document.createElement('div');
                feedback.className = 'file-feedback mt-2';
                this.parentNode.appendChild(feedback);
            }
            
            if (files.length > 0) {
                const fileNames = Array.from(files).map(file => file.name).join(', ');
                feedback.innerHTML = `<i class="ni ni-check-bold text-success"></i> Selected: ${fileNames}`;
                feedback.className = 'file-feedback mt-2 text-success';
            } else {
                feedback.innerHTML = '';
            }
        });
    });
}

function initializeProgressTracking() {
    const form = document.querySelector('#grantApplicationForm');
    if (!form) return;
    
    const steps = form.querySelectorAll('.form-step');
    const progressBar = document.querySelector('.progress-bar');
    
    if (steps.length > 0 && progressBar) {
        updateProgress();
    }
    
    function updateProgress() {
        let completedSteps = 0;
        steps.forEach(step => {
            const requiredFields = step.querySelectorAll('[required]');
            const filledFields = Array.from(requiredFields).filter(field => field.value.trim());
            
            if (filledFields.length === requiredFields.length) {
                completedSteps++;
                step.classList.add('completed');
            } else {
                step.classList.remove('completed');
            }
        });
        
        const progressPercent = (completedSteps / steps.length) * 100;
        progressBar.style.width = progressPercent + '%';
        progressBar.setAttribute('aria-valuenow', progressPercent);
    }
    
    // Update progress on input changes
    form.addEventListener('input', debounce(updateProgress, 500));
}

function initializeTooltips() {
    // Initialize Bootstrap tooltips if available
    if (typeof bootstrap !== 'undefined' && bootstrap.Tooltip) {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }
}

function initializeNotifications() {
    // Auto-dismiss alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    alerts.forEach(alert => {
        setTimeout(() => {
            if (typeof bootstrap !== 'undefined' && bootstrap.Alert) {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            } else {
                alert.style.display = 'none';
            }
        }, 5000);
    });
}

// Utility functions
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Form submission enhancement
function enhanceFormSubmission() {
    const forms = document.querySelectorAll('form[data-enhance="true"]');
    
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const submitButton = form.querySelector('button[type="submit"]');
            
            if (submitButton) {
                submitButton.disabled = true;
                const originalText = submitButton.innerHTML;
                submitButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
                
                // Re-enable after 10 seconds as fallback
                setTimeout(() => {
                    submitButton.disabled = false;
                    submitButton.innerHTML = originalText;
                }, 10000);
            }
        });
    });
}

// Initialize form submission enhancement
document.addEventListener('DOMContentLoaded', enhanceFormSubmission);

// Professional animations and transitions
function addProfessionalAnimations() {
    // Smooth scroll for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
    
    // Fade-in animation for cards
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver(function(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate-fade-in');
            }
        });
    }, observerOptions);
    
    document.querySelectorAll('.card, .form-group').forEach(el => {
        observer.observe(el);
    });
}

// Initialize animations
document.addEventListener('DOMContentLoaded', addProfessionalAnimations);

// Export functions for external use
window.GrantApplicationEnhancer = {
    validateField,
    initializeFormEnhancements,
    initializeProgressTracking,
    debounce,
    initializeWizard
};

console.log('Grant Application Enhanced Interactions loaded successfully');

// Wizard/Stepper logic with enhanced debugging and error handling
function initializeWizard() {
    console.log('Initializing wizard...');
    
    const form = document.getElementById('grantApplicationForm');
    if (!form) {
        console.error('grantApplicationForm not found');
        return;
    }
    console.log('Form found:', form);

    const steps = Array.from(form.querySelectorAll('.form-step'));
    if (steps.length === 0) {
        console.error('No form steps found');
        return;
    }
    console.log('Found', steps.length, 'form steps:', steps);

    const nextButtons = form.querySelectorAll('[data-next]');
    const backButtons = form.querySelectorAll('[data-back]');
    const submitButton = form.querySelector('[data-submit]');
    const progressBar = document.querySelector('.progress-bar');
    const stepper = document.getElementById('wizardStepper');
    const stepperItems = stepper ? Array.from(stepper.children) : [];

    console.log('Next buttons found:', nextButtons.length);
    console.log('Back buttons found:', backButtons.length);
    console.log('Progress bar:', progressBar);

    let current = 0;
    update();

    nextButtons.forEach((btn, index) => {
        console.log('Adding click listener to next button', index);
        btn.addEventListener('click', (e) => {
            console.log('Next button clicked, current step:', current);
            e.preventDefault();
            
            if (!validateCurrentStep()) {
                console.log('Validation failed for current step');
                return;
            }
            
            current = Math.min(current + 1, steps.length - 1);
            console.log('Moving to step:', current);
            update();
        });
    });

    backButtons.forEach((btn, index) => {
        console.log('Adding click listener to back button', index);
        btn.addEventListener('click', (e) => {
            console.log('Back button clicked, current step:', current);
            e.preventDefault();
            current = Math.max(current - 1, 0);
            console.log('Moving to step:', current);
            update();
        });
    });

    function validateCurrentStep() {
        const currentStep = steps[current];
        const required = Array.from(currentStep.querySelectorAll('[required]'));
        console.log('Validating step', current, 'with', required.length, 'required fields');
        
        let ok = true;
        required.forEach(field => {
            if (!field.value || field.value.trim() === '') {
                console.log('Required field is empty:', field.name || field.id);
                field.classList.add('is-invalid');
                ok = false;
            } else {
                field.classList.remove('is-invalid');
                field.classList.add('is-valid');
            }
        });
        
        // focus first invalid
        const firstInvalid = currentStep.querySelector('.is-invalid');
        if (firstInvalid) {
            firstInvalid.focus();
            console.log('Focused on invalid field:', firstInvalid.name || firstInvalid.id);
        }
        
        console.log('Step validation result:', ok);
        return ok;
    }

    function update() {
        console.log('Updating wizard display for step:', current);
        
        steps.forEach((panel, idx) => {
            const isActive = idx === current;
            panel.classList.toggle('active', isActive);
            panel.style.display = isActive ? 'block' : 'none';
            console.log('Step', idx, 'active:', isActive);
        });

        // update stepper
        if (stepperItems.length) {
            stepperItems.forEach((li, idx) => {
                const isActive = idx === current;
                const isCompleted = idx < current;
                
                li.classList.toggle('active', isActive);
                li.classList.toggle('completed', isCompleted);
                li.setAttribute('aria-selected', isActive ? 'true' : 'false');
                li.setAttribute('tabindex', isActive ? '0' : '-1');
            });
        }

        // update progress bar
        if (progressBar) {
            const percent = ((current) / (steps.length - 1)) * 100;
            progressBar.style.width = `${percent}%`;
            progressBar.setAttribute('aria-valuenow', `${percent}`);
            progressBar.setAttribute('aria-label', `Grant application progress: ${Math.round(percent)}% complete`);
            progressBar.setAttribute('title', `Step ${current + 1} of ${steps.length} - ${Math.round(percent)}% complete`);
            console.log('Progress updated to:', percent + '%');
        }

        // enable/disable submit
        if (submitButton) {
            const atLast = current === steps.length - 1;
            submitButton.disabled = !atLast;
            submitButton.style.display = atLast ? 'inline-block' : 'none';
        }
    }
}