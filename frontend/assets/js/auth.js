// assets/js/auth.js
const API_BASE_URL = '/api';
const TOKEN_KEY = 'access_token';
const REFRESH_TOKEN_KEY = 'refresh_token';
const USER_KEY = 'user_data';

// ========== TOKEN MANAGEMENT ==========
function setTokens(accessToken, refreshToken = null) {
    localStorage.setItem(TOKEN_KEY, accessToken);
    if (refreshToken) {
        localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
    }
}

function getAccessToken() {
    return localStorage.getItem(TOKEN_KEY);
}

function getRefreshToken() {
    return localStorage.getItem(REFRESH_TOKEN_KEY);
}

function clearTokens() {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
}

function setUserData(user) {
    localStorage.setItem(USER_KEY, JSON.stringify(user));
}

function getUserData() {
    const user = localStorage.getItem(USER_KEY);
    return user ? JSON.parse(user) : null;
}

// ========== API FUNCTIONS ==========
async function makeRequest(url, method, data = null, requiresAuth = true) {
    const headers = { 'Content-Type': 'application/json' };

    if (requiresAuth) {
        const token = getAccessToken();
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }
    }

    const options = { method, headers, credentials: 'same-origin' };
    if (data) options.body = JSON.stringify(data);

    try {
        const response = await fetch(url, options);

        if (response.status === 401 && requiresAuth) {
            clearTokens();
            if (!window.location.pathname.includes('login')) {
                window.location.href = '/login.html?session=expired';
            }
            throw new Error('Session expired. Please login again.');
        }

        const result = await response.json();

        if (!response.ok) {
            // Extract error message from Django response
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
                // Try to get first error
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

// ========== AUTH FUNCTIONS ==========
async function registerUser(userData) {
    console.log('Sending registration data:', userData);

    try {
        const response = await fetch('/api/register/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            body: JSON.stringify(userData),
            credentials: 'same-origin'
        });

        console.log('Response status:', response.status);
        console.log('Response headers:', response.headers);

        const text = await response.text();
        console.log('Response body:', text);

        let result;
        try {
            result = text ? JSON.parse(text) : {};
        } catch (e) {
            console.error('Failed to parse JSON:', text);
            result = { detail: text };
        }

        if (!response.ok) {
            throw new Error(result.detail || result.error || `HTTP ${response.status}: ${response.statusText}`);
        }

        // Auto-login after registration if tokens are returned
        if (result.access && result.refresh) {
            setTokens(result.access, result.refresh);
            if (result.user) {
                setUserData(result.user);
            }
        }

        return {
            success: true,
            data: result,
            redirectUrl: result.redirect_url || '/login.html'
        };
    } catch (error) {
        console.error('Registration API error:', error);
        return {
            success: false,
            error: error.message || 'Registration failed. Please try again.'
        };
    }
}

// ========== AUTHENTICATION ===========

function isAuthenticated() {
    const token = getAccessToken();
    // Returns true if token exists, false otherwise
    return !!token;
}

async function loginUser(email, password) {
    try {
        // Django's JWT endpoint expects username, not email
        // But your LoginView handles email -> username conversion
        const response = await makeRequest(`${API_BASE_URL}/token/`, 'POST', {
            email: email,
            password: password
        }, false);

        if (!response.access) {
            throw new Error('Invalid response from server');
        }

        setTokens(response.access, response.refresh);

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
    try {
        await makeRequest(`${API_BASE_URL}/logout/`, 'POST');
    } catch (error) {
        console.log('Logout API call failed');
    } finally {
        clearTokens();
        return {
            success: true,
            redirectUrl: '/login.html'
        };
    }
}

// Replace your existing getCurrentUser() with this:
async function getCurrentUser() {
    const token = getAccessToken(); // Now correctly uses 'access_token'
    if (!token) return { success: false };

    try {
        // Decode the JWT directly in the browser to check expiration
        // This avoids making a network request to a missing endpoint!
        const base64Url = token.split('.')[1];
        const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
        const payload = JSON.parse(window.atob(base64));

        // Check if the current time is past the token's expiration time
        const isExpired = (Math.floor(Date.now() / 1000)) >= payload.exp;

        if (isExpired) {
            console.warn("Token has expired.");
            return { success: false };
        }

        return { success: true, user: getUserData() };
    } catch (e) {
        console.error("Token validation error:", e);
        return { success: false };
    }
}

function showMessage(element, text, type) {
    if (!element) return;

    element.textContent = text;
    element.className = `alert alert-${type} mt-3`;
    element.style.display = 'block';
}

function resetButton(button, originalText) {
    button.disabled = false;
    button.innerHTML = originalText;
}

// ========== UI STATE MANAGEMENT ==========
function updateUI() {
    const isLoggedIn = isAuthenticated();

    // 1. Show/Hide "Auth Only" elements (Profile, Logout)
    document.querySelectorAll('[data-auth="true"]').forEach(el => {
        if (isLoggedIn) {
            el.style.display = '';
        } else {
            el.style.display = 'none';
        }
    });

    // 2. Show/Hide "Guest Only" elements
    document.querySelectorAll('[data-guest="true"]').forEach(el => {
        if (!isLoggedIn) {
            el.style.display = '';
        } else {
            el.style.display = 'none';
        }
    });
}

// ========== INITIALIZATION ==========
document.addEventListener('DOMContentLoaded', function() {

    updateUI();

    // Handle logout buttons
    document.querySelectorAll('[data-logout], .logout-btn').forEach(button => {
        button.addEventListener('click', async function(e) {
            e.preventDefault();
            await logoutUser();
            window.location.href = '/dashboard';
        });
    });
});