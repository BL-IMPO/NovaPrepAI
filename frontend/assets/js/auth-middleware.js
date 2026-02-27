// assets/js/auth-middleware.js
// This script should be included on every page to protect routes and update UI.

document.addEventListener('DOMContentLoaded', async function() {
    // Define protected page prefixes
    const protectedPages = ['/dashboard/', '/profile/', '/chat/', '/tests/', '/testing/'];
    const currentPath = window.location.pathname;

    // Check if current page requires authentication
    const isProtectedPage = protectedPages.some(page => currentPath.includes(page));

    if (isProtectedPage) {
        // Use the async isAuthenticated function
        const authenticated = await isAuthenticated();

        if (!authenticated) {
            // Redirect to login with return URL
            const returnUrl = encodeURIComponent(currentPath);
            window.location.href = `/login.html?next=${returnUrl}`;
            return;
        }

        // Optionally update UI with user data (e.g., a greeting)
        const userData = await getCurrentUser();
        if (userData.success && document.getElementById('user-greeting')) {
            document.getElementById('user-greeting').textContent =
                `Welcome, ${userData.user.first_name || userData.user.username || userData.user.email}!`;
        }
    }
});