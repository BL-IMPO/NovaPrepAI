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

    if (!['GET', 'HEAD', 'OPTIONS', 'TRACE'].includes(method.toUpperCase())) {
        const csrfToken = getCSRFToken();
        if (csrfToken) {
            headers['X-CSRFToken'] = csrfToken;
        }
    }

    const options = {
        method,
        headers,
        credentials: 'same-origin',
        body: data ? JSON.stringify(data) : undefined
    };

    try {
        const response = await fetch(url, options);

        // Handle 401 Unauthorized – session expired (ONLY if requiresAuth is true)
        if (response.status === 401 && requiresAuth) {
            clearUserData();
            if (!window.location.pathname.includes('login')) {
                window.location.href = '/login.html?session=expired';
            }
            throw new Error('Session expired. Please login again.');
        }

        const result = await response.json();

        if (!response.ok) {
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

async function ensureCSRF() {
    if (!getCSRFToken()) {
        await fetch('/api/csrf/', { credentials: 'same-origin' });
    }
}

async function registerUser(userData) {
    await ensureCSRF();
    try {
        const response = await makeRequest('/api/register/', 'POST', userData, false);
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

async function loginUser(email, password) {
    await ensureCSRF();
    try {
        const response = await makeRequest('/api/token/', 'POST', { email, password }, false);
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

async function logoutUser() {
    await ensureCSRF();
    try {
        await makeRequest('/api/logout/', 'POST', {});
    } catch (error) {
        console.log('Logout API call failed:', error);
    } finally {
        clearUserData();
        return {
            success: true,
            redirectUrl: '/login.html'
        };
    }
}

/**
 * Check if the user is authenticated by verifying the token via the server.
 */
async function isAuthenticated() {
    try {
        // CHANGED: requiresAuth is now FALSE. It will just return a 401 and fail safely without redirecting.
        await makeRequest('/api/token/verify/', 'GET', null, false);
        return true;
    } catch (error) {
        return false;
    }
}

/**
 * Get the current user's data.
 */
async function getCurrentUser() {
    try {
        // CHANGED: requiresAuth is now FALSE.
        const response = await makeRequest('/api/token/verify/', 'GET', null, false);
        if (response.user) {
            setUserData(response.user);
            return { success: true, user: response.user };
        }
        return { success: true, user: getUserData() };
    } catch (error) {
        return { success: false, user: null };
    }
}

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
    const user = getUserData();
    const isLoggedIn = !!user;

    document.querySelectorAll('[data-auth="true"]').forEach(el => {
        el.style.display = isLoggedIn ? '' : 'none';
    });

    document.querySelectorAll('[data-guest="true"]').forEach(el => {
        el.style.display = !isLoggedIn ? '' : 'none';
    });

    const greetingEl = document.getElementById('user-greeting');
    if (greetingEl && user) {
        greetingEl.textContent = `Welcome, ${user.first_name || user.username || user.email}!`;
    }
}

// ========== INITIALIZATION ==========
document.addEventListener('DOMContentLoaded', async function() {
    await ensureCSRF();
    updateUI();

    document.querySelectorAll('[data-logout], .logout-btn').forEach(button => {
        button.addEventListener('click', async function(e) {
            e.preventDefault();
            const result = await logoutUser();
            window.location.href = result.redirectUrl;
        });
    });
});