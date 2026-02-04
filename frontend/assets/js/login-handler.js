// assets/js/login-handler.js
// assets/js/login-handler.js
document.addEventListener('DOMContentLoaded', function() {
    const loginForm = document.getElementById('loginForm');
    const loginButton = document.getElementById('loginButton');
    const loginMessage = document.getElementById('loginMessage');

    // Check if already logged in
    if (isAuthenticated()) {
        // Redirect to dashboard if already authenticated
        window.location.href = '/dashboard/';
    }

    if (loginForm) {
        loginForm.addEventListener('submit', async function(e) {
            e.preventDefault();

            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;

            // Validate inputs
            if (!email || !password) {
                showMessage('Please fill in all fields', 'warning');
                return;
            }

            // Show loading state
            loginButton.disabled = true;
            loginButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Logging in...';
            loginMessage.style.display = 'none';

            try {
                const result = await loginUser(email, password);

                if (result.success) {
                    showMessage('✓ Login successful! Redirecting...', 'success');

                    // Optional: Store user data in session
                    sessionStorage.setItem('welcome_message', `Welcome back, ${result.user.first_name || result.user.username}!`);

                    // Redirect after delay
                    setTimeout(() => {
                        window.location.href = result.redirectUrl;
                    }, 1500);
                } else {
                    showMessage(`✗ ${result.error}`, 'danger');
                    loginButton.disabled = false;
                    loginButton.innerHTML = 'Login';
                }
            } catch (error) {
                showMessage('✗ An error occurred. Please try again.', 'danger');
                console.error('Login error:', error);
                loginButton.disabled = false;
                loginButton.innerHTML = 'Login';
            }
        });
    }

    // Add "Enter" key support
    document.getElementById('password')?.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            loginForm.dispatchEvent(new Event('submit'));
        }
    });

    function showMessage(text, type) {
        loginMessage.innerHTML = text;
        loginMessage.className = `alert alert-${type} mt-3`;
        loginMessage.style.display = 'block';

        // Auto-hide success messages
        if (type === 'success') {
            setTimeout(() => {
                loginMessage.style.display = 'none';
            }, 5000);
        }
    }
});