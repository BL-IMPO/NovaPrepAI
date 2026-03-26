// frontend/assets/js/profile-dashboard.js

document.addEventListener('DOMContentLoaded', () => {

    const API_STATS_URL = '/fastapi/api/user/statistics';

    // UI Elements
    const statTotalTests = document.getElementById('statTotalTests');
    const statAvgScore = document.getElementById('statAvgScore');
    const historyTableBody = document.getElementById('historyTableBody');
    const progressChartCanvas = document.getElementById('progressChart');
    const radarChartCanvas = document.getElementById('radarChart');
    const spinner = document.getElementById('chartLoadingSpinner');

    let isDashboardLoaded = false;

    // Helper: Красивые названия тестов
    const formatTestName = (rawText) => {
        const map = {
            'math_1': 'Математика (Осн.)',
            'math_2': 'Математика 2',
            'reading': 'Чтение',
            'grammar': 'Грамматика',
            'analogy': 'Аналогии',
            'full_test': 'Полный Тест'
        };
        return map[rawText] || rawText.replace(/_/g, ' ').toUpperCase();
    };

    // Helper: Форматирование даты
    const formatDate = (isoString) => {
        const date = new Date(isoString);
        return date.toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' });
    };

    // Главная функция инициализации
    const initDashboard = async () => {
        if(isDashboardLoaded) return; // Чтобы не грузить дважды при переключении табов

        try {
            let data;
            if (typeof makeRequest === 'function') {
                data = await makeRequest(API_STATS_URL, 'GET', null, false);
            } else {
                const response = await fetch(API_STATS_URL);
                data = await response.json();
            }

            if (data && data.status === "success" && data.data) {
                const attempts = data.data;
                renderHistoryTable(attempts);
                calculateOverallStats(attempts);
                renderCharts(attempts);

                if(spinner) spinner.style.display = 'none';
                if(progressChartCanvas) progressChartCanvas.style.display = 'block';
                if(radarChartCanvas) radarChartCanvas.style.display = 'block';

                isDashboardLoaded = true;
            }
        } catch (error) {
            console.error("Failed to load statistics:", error);
            if (historyTableBody) {
                historyTableBody.innerHTML = '<tr><td colspan="5" class="text-center text-danger py-4">Ошибка загрузки данных.</td></tr>';
            }
            if(spinner) {
                spinner.innerHTML = '<p class="text-danger">Не удалось загрузить графики.</p>';
            }
        }
    };

    // Отрисовка таблицы истории
    const renderHistoryTable = (attempts) => {
        if (!historyTableBody) return;
        historyTableBody.innerHTML = '';

        if (attempts.length === 0) {
            historyTableBody.innerHTML = '<tr><td colspan="5" class="text-center text-muted py-5">Вы еще не прошли ни одного теста.</td></tr>';
            return;
        }

        const reversed = [...attempts].reverse();

        reversed.forEach(a => {
            const percentage = a.total_questions > 0 ? Math.round((a.score / a.total_questions) * 100) : 0;
            const statusBadge = a.passed
                ? `<span class="badge bg-success bg-opacity-10 text-success border border-success border-opacity-25 px-3 py-2 rounded-pill">Успешно</span>`
                : `<span class="badge bg-danger bg-opacity-10 text-danger border border-danger border-opacity-25 px-3 py-2 rounded-pill">Не сдан</span>`;

            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td class="ps-4 fw-medium text-muted">${formatDate(a.created_at)}</td>
                <td class="fw-bold">${formatTestName(a.test_type)}</td>
                <td class="text-center fw-bold">${percentage}%</td>
                <td class="text-center">${statusBadge}</td>
                <td class="text-end pe-4">
                    <a href="/results/${a.id}/${a.test_type}" class="btn btn-sm btn-outline-primary rounded-pill px-3 fw-bold">Смотреть</a>
                </td>
            `;
            historyTableBody.appendChild(tr);
        });
    };

    // Подсчет общих цифр
    const calculateOverallStats = (attempts) => {
        if(attempts.length === 0 || !statTotalTests) return;

        statTotalTests.textContent = attempts.length;

        let totalPercentageSum = 0;
        let validTests = 0;

        attempts.forEach(a => {
            if(a.total_questions > 0) {
                const pct = (a.score / a.total_questions) * 100;
                totalPercentageSum += pct;
                validTests++;
            }
        });

        if(validTests > 0 && statAvgScore) {
            statAvgScore.textContent = Math.round(totalPercentageSum / validTests) + '%';
        }
    };

    // Отрисовка Chart.js графиков
    const renderCharts = (attempts) => {
        if(attempts.length === 0 || !progressChartCanvas || !radarChartCanvas) return;

        // --- Данные для Линейного графика ---
        const labelsLine = [];
        const dataLine = [];

        attempts.forEach(a => {
            if(a.total_questions > 0) {
                const dateObj = new Date(a.created_at);
                labelsLine.push(`${dateObj.getDate()}.${dateObj.getMonth()+1}`);
                dataLine.push(Math.round((a.score / a.total_questions) * 100));
            }
        });

        // --- Данные для Радара (или Бара) ---
        const subjectScores = {};
        attempts.forEach(a => {
            if(a.total_questions > 0 && a.test_type !== 'full_test') {
                const pct = (a.score / a.total_questions) * 100;
                if(!subjectScores[a.test_type]) subjectScores[a.test_type] = { sum: 0, count: 0 };
                subjectScores[a.test_type].sum += pct;
                subjectScores[a.test_type].count += 1;
            }
        });

        const radarLabels = Object.keys(subjectScores).map(k => formatTestName(k));
        const radarData = Object.values(subjectScores).map(v => Math.round(v.sum / v.count));

        Chart.defaults.font.family = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif";
        Chart.defaults.color = '#6c757d';

        // Инициализация Line Chart
        new Chart(progressChartCanvas.getContext('2d'), {
            type: 'line',
            data: {
                labels: labelsLine,
                datasets: [{
                    label: 'Точность (%)',
                    data: dataLine,
                    borderColor: '#0d6efd', // Primary color
                    backgroundColor: 'rgba(13, 110, 253, 0.1)',
                    borderWidth: 3,
                    pointBackgroundColor: '#ffffff',
                    pointBorderColor: '#0d6efd',
                    pointBorderWidth: 2,
                    pointRadius: 4,
                    pointHoverRadius: 6,
                    fill: true,
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                plugins: { legend: { display: false } },
                scales: {
                    y: { beginAtZero: true, max: 100, grid: { borderDash: [4, 4] } },
                    x: { grid: { display: false } }
                }
            }
        });

        // Инициализация Radar/Bar Chart
        if (radarLabels.length > 2) {
            new Chart(radarChartCanvas.getContext('2d'), {
                type: 'radar',
                data: {
                    labels: radarLabels,
                    datasets: [{
                        label: 'Средняя точность',
                        data: radarData,
                        backgroundColor: 'rgba(25, 135, 84, 0.2)', // Success color
                        borderColor: '#198754',
                        pointBackgroundColor: '#198754',
                        pointBorderColor: '#fff',
                        pointHoverBackgroundColor: '#fff',
                        pointHoverBorderColor: '#198754',
                        borderWidth: 2,
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        r: {
                            angleLines: { color: 'rgba(0, 0, 0, 0.1)' },
                            suggestedMin: 0, suggestedMax: 100,
                            ticks: { stepSize: 20, backdropColor: 'transparent' }
                        }
                    },
                    plugins: { legend: { display: false } }
                }
            });
        } else if (radarLabels.length > 0) {
             // Если предметов мало (1 или 2), радар выглядит как линия. Рисуем обычные столбики.
             new Chart(radarChartCanvas.getContext('2d'), {
                 type: 'bar',
                 data: {
                     labels: radarLabels,
                     datasets: [{
                         label: 'Точность',
                         data: radarData,
                         backgroundColor: 'rgba(25, 135, 84, 0.7)',
                         borderRadius: 6
                     }]
                 },
                 options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { display: false } },
                    scales: { y: { beginAtZero: true, max: 100 } }
                 }
             });
        }
    };

    // Слушатель: загружаем графики только тогда, когда пользователь нажимает на вкладку "Мои результаты"
    const historyMainTab = document.getElementById('history-tab');
    if (historyMainTab) {
        historyMainTab.addEventListener('shown.bs.tab', function () {
            initDashboard();
        });
    }
});