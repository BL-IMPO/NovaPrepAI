// assets/js/auth-middleware.js
document.addEventListener('DOMContentLoaded', async function() {
    // Pages that require authentication
    const protectedPages = ['/dashboard/', '/profile/', '/chat/', '/tests/'];
    const currentPath = window.location.pathname;

    // Check if current page requires authentication
    const isProtectedPage = protectedPages.some(page => currentPath.includes(page));

    if (isProtectedPage) {
        if (!isAuthenticated()) {
            // Redirect to login with return URL
            const returnUrl = encodeURIComponent(currentPath);
            window.location.href = `/login?next=${returnUrl}`;
            return;
        }

        // Verify token on server
        try {
            const user = await getCurrentUser();
            if (!user.success) {
                throw new Error('Invalid session');
            }

            // Optional: Update UI with user data
            const userData = getUserData();
            if (userData && document.getElementById('user-greeting')) {
                document.getElementById('user-greeting').textContent =
                    `Welcome, ${userData.first_name || userData.username}!`;
            }

        } catch (error) {
            console.error('Auth verification failed:', error);
            clearTokens();
            window.location.href = `/login.html?session=expired`;
        }
    }
});