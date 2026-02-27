// assets/js/auth.js
const API_BASE_URL = '/api';

// ========== CSRF TOKEN HELPER ==========
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

function getCSRFToken() {
    return getCookie('csrftoken');
}

// ========== USER DATA STORAGE ==========
// User data is still stored in localStorage for UI convenience,
// but tokens are NEVER stored on the client side.
function setUserData(user) {
    localStorage.setItem('user_data', JSON.stringify(user));
}

function getUserData() {
    const user = localStorage.getItem('user_data');
    return user ? JSON.parse(user) : null;
}

function clearUserData() {
    localStorage.removeItem('user_data');
}

// ========== API REQUEST FUNCTION ==========
async function makeRequest(url, method, data = null, requiresAuth = true) {
    const headers = { 'Content-Type': 'application/json' };

    // Add CSRF token for unsafe methods (POST, PUT, DELETE, PATCH)
    if (!['GET', 'HEAD', 'OPTIONS', 'TRACE'].includes(method.toUpperCase())) {
        const csrfToken = getCSRFToken();
        if (csrfToken) {
            headers['X-CSRFToken'] = csrfToken;
        }
    }

    // No Authorization header – cookies are sent automatically with credentials: 'same-origin'

    const options = {
        method,
        headers,
        credentials: 'same-origin',  // Important: sends cookies (including HttpOnly JWT cookies)
        body: data ? JSON.stringify(data) : undefined
    };

    try {
        const response = await fetch(url, options);

        // Handle 401 Unauthorized – session expired
        if (response.status === 401 && requiresAuth) {
            clearUserData();  // Remove any stale user data
            // Redirect to login if not already there
            if (!window.location.pathname.includes('login')) {
                window.location.href = '/login.html?session=expired';
            }
            throw new Error('Session expired. Please login again.');
        }

        const result = await response.json();

        if (!response.ok) {
            // Extract error message from Django response (same as before)
            let errorMessage = 'Request failed';
            if (result.detail) {
                errorMessage = result.detail;
            } else if (result.email && Array.isArray(result.email)) {
                errorMessage = result.email[0];
            } else if (result.password && Array.isArray(result.password)) {
                errorMessage = result.password[0];
            } else if (result.password2 && Array.isArray(result.password2)) {
                errorMessage = result.password2[0];
            } else if (typeof result === 'object') {
                for (const key in result) {
                    if (Array.isArray(result[key]) && result[key].length > 0) {
                        errorMessage = `${key}: ${result[key][0]}`;
                        break;
                    }
                }
            }
            throw new Error(errorMessage);
        }

        return result;
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
}

// ========== AUTHENTICATION FUNCTIONS ==========

/**
 * Ensures the CSRF cookie is set by calling the CSRF endpoint.
 * Should be called once before the first POST request if the cookie is missing.
 */
async function ensureCSRF() {
    if (!getCSRFToken()) {
        await fetch('/api/csrf/', { credentials: 'same-origin' });
    }
}

/**
 * Register a new user.
 * @param {Object} userData - Contains email, password, password2, full_name, nickname, subscribe_newsletter
 * @returns {Promise<Object>} - { success, data/error, redirectUrl }
 */
async function registerUser(userData) {
    await ensureCSRF();

    try {
        const response = await makeRequest('/api/register/', 'POST', userData, false);

        // If registration returns user data, store it (tokens are in cookies)
        if (response.user) {
            setUserData(response.user);
        }

        return {
            success: true,
            data: response,
            redirectUrl: response.redirect_url || '/login.html'
        };
    } catch (error) {
        return {
            success: false,
            error: error.message || 'Registration failed. Please try again.'
        };
    }
}

/**
 * Log in a user using email and password.
 * @param {string} email
 * @param {string} password
 * @returns {Promise<Object>} - { success, data/error, redirectUrl }
 */
async function loginUser(email, password) {
    await ensureCSRF();

    try {
        const response = await makeRequest('/api/token/', 'POST', {
            email: email,
            password: password
        }, false);

        // Tokens are now in HttpOnly cookies; only store user data if provided
        if (response.user) {
            setUserData(response.user);
        }

        return {
            success: true,
            data: response,
            redirectUrl: response.redirect_url || '/dashboard'
        };
    } catch (error) {
        return {
            success: false,
            error: error.message || 'Invalid email or password'
        };
    }
}

/**
 * Log out the current user.
 * @returns {Promise<Object>} - { success, redirectUrl }
 */
async function logoutUser() {
    await ensureCSRF();

    try {
        await makeRequest('/api/logout/', 'POST', {});
    } catch (error) {
        console.log('Logout API call failed:', error);
    } finally {
        clearUserData();  // Remove user data from localStorage
        return {
            success: true,
            redirectUrl: '/login.html'
        };
    }
}

/**
 * Check if the user is authenticated by verifying the token via the server.
 * @returns {Promise<boolean>} - true if authenticated, false otherwise.
 */
async function isAuthenticated() {
    try {
        await makeRequest('/api/token/verify/', 'GET', null, true);
        return true;
    } catch (error) {
        return false;
    }
}

/**
 * Get the current user's data.
 * @returns {Promise<Object>} - { success: boolean, user: object|null }
 */
async function getCurrentUser() {
    try {
        const response = await makeRequest('/api/token/verify/', 'GET', null, true);
        // The verify endpoint returns user data if successful
        if (response.user) {
            // Optionally update stored user data
            setUserData(response.user);
            return { success: true, user: response.user };
        }
        return { success: true, user: getUserData() }; // fallback to stored data
    } catch (error) {
        return { success: false, user: null };
    }
}

/**
 * Refresh the access token using the refresh token cookie.
 * @returns {Promise<boolean>} - true if successful
 */
async function refreshAccessToken() {
    try {
        await makeRequest('/api/token/refresh/', 'POST', {});
        console.log('Token refreshed successfully');
        return true;
    } catch (error) {
        console.error('Token refresh failed:', error);
        return false;
    }
}

// ========== UI STATE MANAGEMENT ==========
function updateUI() {
    // This function is now async because isAuthenticated is async.
    // It's better to call it from a separate initialization block.
    // For simplicity, we'll keep it synchronous using stored user data,
    // but you may want to call getCurrentUser() instead.
    const user = getUserData();
    const isLoggedIn = !!user;

    // 1. Show/Hide "Auth Only" elements (Profile, Logout)
    document.querySelectorAll('[data-auth="true"]').forEach(el => {
        el.style.display = isLoggedIn ? '' : 'none';
    });

    // 2. Show/Hide "Guest Only" elements
    document.querySelectorAll('[data-guest="true"]').forEach(el => {
        el.style.display = !isLoggedIn ? '' : 'none';
    });

    // 3. Update user greeting if element exists
    const greetingEl = document.getElementById('user-greeting');
    if (greetingEl && user) {
        greetingEl.textContent = `Welcome, ${user.first_name || user.username || user.email}!`;
    }
}

// ========== INITIALIZATION ==========
document.addEventListener('DOMContentLoaded', async function() {
    // Ensure CSRF cookie is present (optional, it may already be set)
    await ensureCSRF();

    // Update UI based on authentication status
    updateUI();

    // Handle logout buttons
    document.querySelectorAll('[data-logout], .logout-btn').forEach(button => {
        button.addEventListener('click', async function(e) {
            e.preventDefault();
            const result = await logoutUser();
            window.location.href = result.redirectUrl;
        });
    });
});