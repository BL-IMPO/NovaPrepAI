// assets/js/login-handler.js
document.addEventListener('DOMContentLoaded', async function() {
    const loginForm = document.getElementById('loginForm');
    const loginButton = document.getElementById('loginButton');
    const loginMessage = document.getElementById('loginMessage');

    // Check if already logged in (await the async function)
    if (await isAuthenticated()) {
        // Redirect to profile or dashboard if already authenticated
        window.location.href = '/profile';
        return; // Stop further execution
    }

    if (loginForm) {
        loginForm.addEventListener('submit', async function(e) {
            e.preventDefault();

            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;

            // Validate inputs
            if (!email || !password) {
                showMessage('Пожалуйста, заполните все поля', 'warning');
                return;
            }

            // Show loading state
            loginButton.disabled = true;
            loginButton.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span> Вход...';
            loginMessage.style.display = 'none';
            loginMessage.classList.remove('d-flex'); // убираем flex при скрытии

            try {
                const result = await loginUser(email, password);

                if (result.success) {
                    showMessage('Успешный вход! Перенаправление...', 'success');

                    // Optional: Store user data in session
                    sessionStorage.setItem('welcome_message', 'С возвращением!');

                    // Redirect after delay
                    setTimeout(() => {
                        window.location.href = result.redirectUrl || '/profile';
                    }, 1500);
                } else {
                    showMessage(result.error, 'danger');
                    loginButton.disabled = false;
                    loginButton.innerHTML = 'Войти';
                }
            } catch (error) {
                showMessage('Произошла ошибка сети. Попробуйте снова.', 'danger');
                console.error('Login error:', error);
                loginButton.disabled = false;
                loginButton.innerHTML = 'Войти';
            }
        });
    }

    // Add "Enter" key support
    document.getElementById('password')?.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            e.preventDefault(); // предотвращаем двойную отправку
            loginForm.dispatchEvent(new Event('submit'));
        }
    });

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

        // Формируем красивый HTML
        loginMessage.innerHTML = `${iconSvg} <span class="fw-medium">${text}</span>`;
        loginMessage.className = `mt-4 p-3 rounded-3 shadow-sm d-flex align-items-center ${bgColorClass} ${textColorClass}`;
        loginMessage.style.display = 'flex'; // Используем flex для центрирования иконки и текста

        // Auto-hide messages (для всех, кроме критических ошибок, если хотите, но пока оставим для всех)
        setTimeout(() => {
            if (loginMessage.style.display === 'flex') {
                loginMessage.style.display = 'none';
                loginMessage.classList.remove('d-flex');
            }
        }, 5000);
    }
});