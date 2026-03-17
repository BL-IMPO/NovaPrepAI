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
                showMessage('Пароли не совпадают!', 'danger');
                return;
            }

            // Validate terms acceptance
            if (!termsCheckbox.checked) {
                showMessage('Необходимо согласиться с условиями использования!', 'danger');
                return;
            }

            const userData = {
                full_name: document.getElementById('full_name').value,
                nickname: document.getElementById('nickname').value,
                email: document.getElementById('email').value,
                password: passwordInput.value,
                password2: document.getElementById('password_confirm').value,
                subscribe_newsletter: document.getElementById('newsletter').checked
            };

            // Show loading state
            registerButton.disabled = true;
            registerButton.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span> Регистрация...';
            registerMessage.style.display = 'none';
            registerMessage.classList.remove('d-flex');

            try {
                const result = await registerUser(userData);

                if (result.success) {
                    showMessage('Регистрация успешна! Перенаправление...', 'success');

                    setTimeout(() => {
                        window.location.href = result.redirectUrl || '/login';
                    }, 1500);
                } else {
                    showMessage(result.error || 'Ошибка регистрации. Попробуйте снова.', 'danger');
                    registerButton.disabled = false;
                    registerButton.innerHTML = 'Зарегистрироваться';
                }
            } catch (error) {
                showMessage('Произошла ошибка сети. Попробуйте снова.', 'danger');
                console.error('Registration error:', error);
                registerButton.disabled = false;
                registerButton.innerHTML = 'Зарегистрироваться';
            }
        });
    }

    // Красивое отображение сообщений от сервера с иконками
    function showMessage(text, type) {
        let iconSvg = '';
        let bgColorClass = '';
        let textColorClass = '';

        if (type === 'success') {
            bgColorClass = 'bg-success bg-opacity-10';
            textColorClass = 'text-success';
            iconSvg = `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="currentColor" class="bi bi-check-circle-fill me-3 flex-shrink-0" viewBox="0 0 16 16">
                           <path d="M16 8A8 8 0 1 1 0 8a8 8 0 0 1 16 0zm-3.97-3.03a.75.75 0 0 0-1.08.022L7.477 9.417 5.384 7.323a.75.75 0 0 0-1.06 1.06L6.97 11.03a.75.75 0 0 0 1.079-.02l3.992-4.99a.75.75 0 0 0-.01-1.05z"/>
                       </svg>`;
        } else if (type === 'danger') {
            bgColorClass = 'bg-danger bg-opacity-10';
            textColorClass = 'text-danger';
            iconSvg = `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="currentColor" class="bi bi-exclamation-triangle-fill me-3 flex-shrink-0" viewBox="0 0 16 16">
                           <path d="M8.982 1.566a1.13 1.13 0 0 0-1.96 0L.165 13.233c-.457.778.091 1.767.98 1.767h13.713c.889 0 1.438-.99.98-1.767L8.982 1.566zM8 5c.535 0 .954.462.9.995l-.35 3.507a.552.552 0 0 1-1.1 0L7.1 5.995A.905.905 0 0 1 8 5zm.002 6a1 1 0 1 1 0 2 1 1 0 0 1 0-2z"/>
                       </svg>`;
        } else {
            // warning
            bgColorClass = 'bg-warning bg-opacity-10';
            textColorClass = 'text-warning-emphasis';
            iconSvg = `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="currentColor" class="bi bi-info-circle-fill me-3 flex-shrink-0" viewBox="0 0 16 16">
                           <path d="M8 16A8 8 0 1 0 8 0a8 8 0 0 0 0 16zm.93-9.412-1 4.705c-.07.34.029.533.304.533.194 0 .487-.07.686-.246l-.088.416c-.287.346-.92.598-1.465.598-.703 0-1.002-.422-.808-1.319l.738-3.468c.064-.293.006-.399-.287-.47l-.451-.081.082-.381 2.29-.287zM8 5.5a1 1 0 1 1 0-2 1 1 0 0 1 0 2z"/>
                       </svg>`;
        }

        registerMessage.innerHTML = `${iconSvg} <span class="fw-medium">${text}</span>`;
        registerMessage.className = `mt-4 p-3 rounded-3 shadow-sm d-flex align-items-center ${bgColorClass} ${textColorClass}`;
        registerMessage.style.display = 'flex';

        // Авто-скрытие сообщений (опционально, для красоты)
        setTimeout(() => {
            if (registerMessage.style.display === 'flex') {
                registerMessage.style.display = 'none';
                registerMessage.classList.remove('d-flex');
            }
        }, 5000);
    }
});