// assets/js/profile-handler.js

document.addEventListener('DOMContentLoaded', function() {
    loadProfileData();
    loadTestHistory();

    const profileForm = document.getElementById('profileForm');
    if (profileForm) {
        profileForm.addEventListener('submit', handleProfileUpdate);
    }
});

// 1. Preview the image immediately when selected
function previewImage(input) {
    if (input.files && input.files[0]) {
        const reader = new FileReader();
        reader.onload = function(e) {
            document.getElementById('avatarPreview').src = e.target.result;
        }
        reader.readAsDataURL(input.files[0]);
    }
}

// 2. Fetch current data from server
async function loadProfileData() {
    try {
        // Use the updated makeRequest (sends cookies, no manual token)
        const data = await makeRequest('/api/user/', 'GET');

        // Populate fields
        if (data.first_name || data.last_name) {
            document.getElementById('fullName').value = `${data.first_name} ${data.last_name}`.trim();
        }

        document.getElementById('email').value = data.email || '';
        document.getElementById('nickname').value = data.nickname || '';

        // Handle avatar if it exists
        if (data.avatar) {
            document.getElementById('avatarPreview').src = data.avatar;

            // ADD THESE LINES to update the navbar avatar too:
            const navAvatar = document.getElementById('navbarAvatar');
            if (navAvatar) {
                navAvatar.src = data.avatar;
            }
        }

    } catch (error) {
        console.error('Failed to load profile:', error);
        // If 401, middleware handles redirect
    }
}

// 3. Send updates to server (with FormData for file upload)
async function handleProfileUpdate(e) {
    e.preventDefault();

    const saveButton = document.getElementById('saveButton');
    const messageDiv = document.getElementById('profileMessage');
    const originalText = saveButton.innerHTML;

    saveButton.disabled = true;
    saveButton.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Saving...';
    messageDiv.style.display = 'none';

    try {
        // Create FormData (Required for file uploads)
        const formData = new FormData();

        // Handle Name Splitting (Full Name -> First/Last)
        const fullName = document.getElementById('fullName').value;
        const nameParts = fullName.trim().split(' ');
        formData.append('first_name', nameParts[0] || '');
        if (nameParts.length > 1) {
            formData.append('last_name', nameParts.slice(1).join(' '));
        }

        // Handle other text fields
        formData.append('email', document.getElementById('email').value);
        formData.append('nickname', document.getElementById('nickname').value);

        // Handle File Upload
        const fileInput = document.getElementById('avatarInput');
        if (fileInput.files[0]) {
            formData.append('avatar', fileInput.files[0]);
        }

        // Get CSRF token from cookie (set by Django)
        const csrfToken = getCSRFToken();

        // Use fetch directly with credentials and CSRF header
        const response = await fetch('/api/user/', {
            method: 'PATCH',
            headers: {
                // Do NOT set Content-Type – browser will set it with boundary
                'X-CSRFToken': csrfToken
            },
            credentials: 'same-origin',  // Send cookies (including access_token)
            body: formData
        });

        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || 'Failed to update profile');
        }

        const updatedUser = await response.json();

        // Update local storage if you are caching user data
        if (typeof setUserData === 'function') {
            setUserData(updatedUser);
        }

        showMessage(messageDiv, 'Profile updated successfully!', 'success');

    } catch (error) {
        console.error('Update error:', error);
        showMessage(messageDiv, `Error: ${error.message}`, 'danger');
    } finally {
        saveButton.disabled = false;
        saveButton.innerHTML = originalText;
    }
}

function showMessage(element, text, type) {
    element.textContent = text;
    element.className = `alert alert-${type} mb-3`;
    element.style.display = 'block';
}

async function loadTestHistory() {
    try {
        // Use makeRequest (cookies automatically sent)
        const tests = await makeRequest('/api/user/tests/', 'GET');
        const container = document.getElementById('testHistoryContainer');

        // CRITICAL FIX: Exit the function if the old Bootstrap container no longer exists
        // This prevents the null reference error that crashes the script thread.
        if (!container) return;

        container.innerHTML = ''; // Clear the loading spinner

        if (tests.length === 0) {
            container.innerHTML = `
                <div class="col-12 text-center py-5">
                    <h4 class="text-muted">You haven't taken any tests yet!</h4>
                    <a href="/index" class="btn btn-primary mt-3">Take a Test</a>
                </div>`;
            return;
        }

        // Generate a clickable block for each test
        tests.forEach(test => {
            const dateStr = test.created_at
                ? new Date(test.created_at).toLocaleString('en-US', {
                    year: 'numeric',
                    month: 'short',
                    day: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit'
                  })
                : 'Recently';
            const statusBadge = test.passed
                ? '<span class="badge bg-success">Passed</span>'
                : '<span class="badge bg-danger">Failed</span>';

            const testName = formatTestName(test.test_type);

            const html = `
                <div class="col-md-6 col-lg-4 mb-4">
                    <div class="card h-100 shadow-sm border-0"
                         style="cursor: pointer; transition: transform 0.2s, box-shadow 0.2s;"
                         onclick="window.location.href='/results/${test.id}/${test.test_type}'"
                         onmouseover="this.style.transform='translateY(-5px)'; this.classList.add('shadow');"
                         onmouseout="this.style.transform='translateY(0)'; this.classList.remove('shadow');">
                        <div class="card-body">
                            <div class="d-flex justify-content-between align-items-start mb-3">
                                <h5 class="card-title fw-bold mb-0 text-primary">${testName}</h5>
                                ${statusBadge}
                            </div>
                            <p class="text-muted small mb-3">
                                📅 Date: ${dateStr}
                            </p>
                            <div class="d-flex justify-content-between bg-light p-2 rounded">
                                <div class="text-center">
                                    <small class="text-muted d-block">Base Score</small>
                                    <strong class="fs-5">${test.score}</strong>
                                </div>
                                <div class="text-center border-start ps-3">
                                    <small class="text-muted d-block">Points</small>
                                    <strong class="fs-5 text-success">${test.weighted_score}</strong>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            `;
            container.innerHTML += html;
        });

    } catch (error) {
        console.error("Error loading test history:", error);

        // Added the same check here just in case the error block triggers
        const container = document.getElementById('testHistoryContainer');
        if (container) {
            container.innerHTML = `
                <div class="col-12 text-center text-danger py-5">
                    <p>Failed to load test history. Please try refreshing the page.</p>
                </div>`;
        }
    }
}

// Helper function to make the test types look pretty
function formatTestName(testType) {
    const names = {
        'math_1': 'MATH 1',
        'math_2': 'MATH 2',
        'special_chemistry': 'SPECIAL CHEMISTRY',
        // Add other mappings if needed
    };
    return names[testType] || testType.replace('_', ' ').toUpperCase();
}