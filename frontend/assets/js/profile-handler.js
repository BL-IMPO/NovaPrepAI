// assets/js/profile-handler.js

document.addEventListener('DOMContentLoaded', function() {
    loadProfileData();

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
        // We can use your existing helper for GET requests
        const data = await makeRequest('/api/user/', 'GET');

        // Populate fields
        if (data.first_name || data.last_name) {
            document.getElementById('fullName').value = `${data.first_name} ${data.last_name}`.trim();
        }

        document.getElementById('email').value = data.email || '';
        document.getElementById('nickname').value = data.nickname || ''; // Requires 'nickname' in serializer

        // Handle avatar if it exists
        if (data.avatar) {
            document.getElementById('avatarPreview').src = data.avatar;
        }

    } catch (error) {
        console.error('Failed to load profile:', error);
        // If 401, middleware handles redirect
    }
}

// 3. Send updates to server
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

        // We CANNOT use makeRequest() here because it sets Content-Type: application/json
        // We must use fetch directly for FormData
        const token = getAccessToken();
        const response = await fetch('/api/user/', {
            method: 'PATCH', // or PUT
            headers: {
                'Authorization': `Bearer ${token}`
                // CRITICAL: Do NOT set Content-Type here.
                // The browser sets it automatically with the boundary for FormData.
            },
            body: formData
        });

        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || 'Failed to update profile');
        }

        const updatedUser = await response.json();

        // Update local storage if you are caching user data
        setUserData(updatedUser);

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