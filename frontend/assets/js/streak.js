// frontend/assets/js/streak.js

document.addEventListener('DOMContentLoaded', async () => {
    try {
        // We use your existing makeRequest from auth.js
        // The 'false' at the end ensures it doesn't kick guests to the login screen
        const streakData = await makeRequest('/api/streak/', 'GET', null, false);

        if (streakData && streakData.streak !== undefined) {
            const streakBadge = document.getElementById('navStreakBar');
            const streakCount = document.getElementById('streakCount');

            // Update the number
            streakCount.textContent = streakData.streak;

            // Show the badge
            if (streakBadge) {
                streakBadge.classList.remove('d-none');

                // Optional: Make it grey if they haven't practiced today
                if (!streakData.daily_streak) {
                    streakBadge.classList.replace('bg-warning', 'bg-secondary');
                    streakBadge.classList.replace('text-dark', 'text-white');
                }
            }
        }
    } catch (error) {
        // Silently fail if the user is a guest or the API endpoint isn't ready
        console.log('Streak not loaded (guest user or API error).');
    }
});