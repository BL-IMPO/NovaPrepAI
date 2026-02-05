// assets/js/register-handler.js
document.addEventListener('DOMContentLoaded', function() {
    const registerForm = document.getElementById('registerForm');
    const registerButton = document.getElementById('registerButton');
    const registerMessage = document.getElementById('registerMessage');
    const passwordInput = document.getElementById('password');
    const passwordConfirmInput = document.getElementById('password_confirm');
    const termsCheckbox = document.getElementById('terms');

    if (registerForm) {
        registerForm.addEventListener('submit', async function(e) {
            e.preventDefault();

            // Validate passwords match
            if (passwordInput.value !== passwordConfirmInput.value) {
                showMessage('Passwords do not match!', 'danger');
                return;
            }

            // Validate terms acceptance
            if (!termsCheckbox.checked) {
                showMessage('You must agree to the terms and conditions!', 'danger');
                return;
            }

            const userData = {
                full_name: document.getElementById('full_name').value,
                nickname: document.getElementById('nickname').value,
                email: document.getElementById('email').value,
                password: passwordInput.value,
                password2: passwordConfirmInput.value,
                subscribe_newsletter: document.getElementById('newsletter').checked
            };

            // Show loading state
            registerButton.disabled = true;
            registerButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Registering...';
            registerMessage.style.display = 'none';

            try {
                const result = await registerUser(userData);

                if (result.success) {
                    showMessage('Registration successful! Redirecting...', 'success');

                    setTimeout(() => {
                        window.location.href = result.redirectUrl;
                    }, 1500);
                } else {
                    showMessage(result.error || 'Registration failed. Please try again.', 'danger');
                    registerButton.disabled = false;
                    registerButton.innerHTML = 'Register';
                }
            } catch (error) {
                showMessage('An error occurred. Please try again.', 'danger');
                console.error('Registration error:', error);
                registerButton.disabled = false;
                registerButton.innerHTML = 'Register';
            }
        });
    }

    function showMessage(text, type) {
        registerMessage.textContent = text;
        registerMessage.className = `alert alert-${type} mt-3`;
        registerMessage.style.display = 'block';
    }
});