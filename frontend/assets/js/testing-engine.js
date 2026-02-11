// frontend/assets/js/testing-engine.js
class TestingEngine {
    constructor() {
        // Extract test type from URL path
        const pathParts = window.location.pathname.split('/');
        this.testType = pathParts[pathParts.length - 1];

        this.questions = [];
        this.answers = new Map();
        this.previousAnswers = new Map();
        this.currentQuestionIndex = 0;
        this.timeLeft = 0;
        this.totalTime = 0;
        this.timerInterval = null;
        this.isPaused = false;

        // Base URL for API calls
        this.apiBaseUrl = '/fastapi/api';

        this.loadTestData();
        this.initEventListeners();
    }

    async loadTestData() {
        try {
            console.log(`Loading test data for: ${this.testType}`);
            const response = await fetch(`${this.apiBaseUrl}/test/${this.testType}`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();

            // Handle object vs array response structure
            if (Array.isArray(data.questions)) {
                this.questions = data.questions;
            } else {
                this.questions = Object.entries(data.questions);
            }

            this.totalTime = data.time_limit;
            this.timeLeft = this.totalTime;

            console.log(`Loaded ${this.questions.length} questions, time limit: ${this.totalTime}s`);

            this.renderSidebar();
            this.renderQuestion();
            this.updateProgress();
            this.startTimer();

            // Update title
            const testName = this.formatTestName(this.testType);
            const titleEl = document.getElementById('testTypeTitle');
            if (titleEl) titleEl.textContent = testName;

        } catch (error) {
            console.error('Error loading test data:', error);
            alert('Error loading test. Please refresh the page.');
        }
    }

    formatTestName(testType) {
        const names = {
            'math_1': 'MATH 1',
            'math_2': 'MATH 2',
            'analogy': 'ANALOGY',
            'reading': 'READING',
            'grammar': 'GRAMMAR',
            'full_test': 'FULL ORT TEST',
            'special_math': 'SPECIAL MATH',
            'special_biology': 'SPECIAL BIOLOGY',
            'special_chemistry': 'SPECIAL CHEMISTRY',
            'special_english': 'SPECIAL ENGLISH',
            'special_history': 'SPECIAL HISTORY',
            'special_physics': 'SPECIAL PHYSICS',
            'special_russian_grammar': 'SPECIAL RUSSIAN GRAMMAR',
            'special_kyrgyz_grammar': 'SPECIAL KYRGYZ GRAMMAR'
        };

        return names[testType] || testType.replace('_', ' ').toUpperCase();
    }

    startTimer() {
        this.updateTimerDisplay();
        this.timerInterval = setInterval(() => {
            if (!this.isPaused && this.timeLeft > 0) {
                this.timeLeft--;
                this.updateTimerDisplay();

                if (this.timeLeft <= 0) {
                    clearInterval(this.timerInterval);
                    this.submitTest();
                }
            }
        }, 1000);
    }

    updateTimerDisplay() {
        const hours = Math.floor(this.timeLeft / 3600);
        const minutes = Math.floor((this.timeLeft % 3600) / 60);
        const seconds = this.timeLeft % 60;

        const timerElement = document.getElementById('timer');
        if (timerElement) {
            timerElement.textContent =
                `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;

            if (this.timeLeft < 300) {
                timerElement.style.color = '#dc3545';
            } else if (this.timeLeft < 600) {
                timerElement.style.color = '#ffc107';
            } else {
                timerElement.style.color = '';
            }
        }

        const timePercentage = ((this.totalTime - this.timeLeft) / this.totalTime) * 100;
        const progressBar = document.getElementById('progressBar');
        if (progressBar) {
            progressBar.style.width = `${timePercentage}%`;
            progressBar.setAttribute('aria-valuenow', timePercentage);
        }
    }

    renderSidebar() {
        const sidebar = document.getElementById('questionSidebar');
        if (!sidebar) return; // Guard clause to prevent crash

        sidebar.innerHTML = '';

        // We do NOT look for mobileQuestionSidebar because it doesn't exist in your HTML

        this.questions.forEach((question, index) => {
            const questionNumber = index + 1;
            const isAnswered = this.answers.has(index);
            const isCurrent = index === this.currentQuestionIndex;

            const item = document.createElement('a');
            item.href = '#';
            item.className = 'list-group-item list-group-item-action question-sidebar-item';

            // Add styling classes
            if (isCurrent) item.classList.add('active');
            if (isAnswered) {
                item.classList.add('answered');
                if (this.previousAnswers.has(index) && this.previousAnswers.get(index) !== this.answers.get(index)) {
                    item.classList.add('current-answer');
                }
            }

            item.innerHTML = `
                <div class="d-flex justify-content-between align-items-center">
                    <span>Question ${questionNumber}</span>
                    ${isAnswered ? '<span class="badge bg-success">✓</span>' : ''}
                </div>
            `;

            item.addEventListener('click', (e) => {
                e.preventDefault();
                this.goToQuestion(index);

                // Close mobile sidebar if it's open (using the CSS class from your HTML)
                const sidebarEl = document.getElementById('sidebar');
                const overlayEl = document.getElementById('sidebarOverlay');
                if (window.innerWidth <= 768 && sidebarEl && sidebarEl.classList.contains('show')) {
                    sidebarEl.classList.remove('show');
                    if (overlayEl) overlayEl.classList.remove('show');
                }
            });

            sidebar.appendChild(item);
        });
    }

    renderQuestion() {
        if (this.questions.length === 0) return;

        const [questionText, answers] = this.questions[this.currentQuestionIndex];
        const questionNumber = this.currentQuestionIndex + 1;
        const totalQuestions = this.questions.length;

        const titleEl = document.getElementById('currentQuestionTitle');
        if (titleEl) titleEl.textContent = `Question ${questionNumber}`;

        const counterEl = document.getElementById('questionCounter');
        if (counterEl) counterEl.textContent = `${questionNumber} of ${totalQuestions}`;

        const textEl = document.getElementById('questionText');
        if (textEl) textEl.textContent = questionText;

        const container = document.getElementById('answersContainer');
        if (!container) return;

        container.innerHTML = '';

        const answerLetters = ['A', 'B', 'C', 'D', 'E'];
        const currentAnswer = this.answers.get(this.currentQuestionIndex);
        const previousAnswer = this.previousAnswers.get(this.currentQuestionIndex);

        answers.forEach((answer, index) => {
            const col = document.createElement('div');
            col.className = 'col-md-6 mb-3';

            const answerDiv = document.createElement('div');
            answerDiv.className = 'answer-option';
            answerDiv.innerHTML = `
                <div class="form-check">
                    <input class="form-check-input" type="radio"
                           name="answer"
                           id="answer${index}"
                           value="${index}"
                           ${currentAnswer === index ? 'checked' : ''}>
                    <label class="form-check-label w-100" for="answer${index}">
                        <strong>${answerLetters[index] || index + 1})</strong> ${answer}
                    </label>
                </div>
            `;

            if (currentAnswer === index) {
                answerDiv.classList.add('selected');
            } else if (previousAnswer === index) {
                answerDiv.classList.add('previous');
            }

            // Click on the whole box
            answerDiv.addEventListener('click', (e) => {
                // Prevent double triggering if clicking the radio itself
                if (e.target.type !== 'radio') {
                    this.selectAnswer(index);
                }
            });

            // Click on radio specifically
            const radio = answerDiv.querySelector('input[type="radio"]');
            radio.addEventListener('change', () => {
                if (radio.checked) {
                    this.selectAnswer(index);
                }
            });

            col.appendChild(answerDiv);
            container.appendChild(col);
        });

        // Update buttons
        const prevBtn = document.getElementById('prevBtn');
        if (prevBtn) prevBtn.disabled = this.currentQuestionIndex === 0;

        const nextBtn = document.getElementById('nextBtn');
        if (nextBtn) nextBtn.disabled = this.currentQuestionIndex === totalQuestions - 1;
    }

    selectAnswer(answerIndex) {
        const currentAnswer = this.answers.get(this.currentQuestionIndex);

        if (currentAnswer !== undefined && currentAnswer !== answerIndex) {
            this.previousAnswers.set(this.currentQuestionIndex, currentAnswer);
        }

        this.answers.set(this.currentQuestionIndex, answerIndex);

        this.renderSidebar();
        this.renderQuestion();
        this.updateProgress();
    }

    goToQuestion(index) {
        this.currentQuestionIndex = index;
        this.renderQuestion();
        this.renderSidebar();
    }

    updateProgress() {
        const answeredCount = this.answers.size;
        const totalQuestions = this.questions.length;
        const percentage = totalQuestions > 0 ? (answeredCount / totalQuestions) * 100 : 0;

        const progressText = document.getElementById('progressText');
        if (progressText) progressText.textContent = `${answeredCount}/${totalQuestions} answered`;

        const progressBar = document.getElementById('progressBar');
        if (progressBar) progressBar.style.width = `${percentage}%`;
    }

    markCurrentQuestion() {
        // Logic to visually mark the current question in sidebar
        // This requires CSS support for .marked class
        const sidebarItems = document.querySelectorAll('.question-sidebar-item');
        if (sidebarItems[this.currentQuestionIndex]) {
            sidebarItems[this.currentQuestionIndex].classList.toggle('marked');
        }
    }

    clearCurrentAnswer() {
        this.answers.delete(this.currentQuestionIndex);
        this.renderQuestion();
        this.renderSidebar();
        this.updateProgress();
    }

    initEventListeners() {
        const prevBtn = document.getElementById('prevBtn');
        if (prevBtn) {
            prevBtn.addEventListener('click', () => {
                if (this.currentQuestionIndex > 0) {
                    this.goToQuestion(this.currentQuestionIndex - 1);
                }
            });
        }

        const nextBtn = document.getElementById('nextBtn');
        if (nextBtn) {
            nextBtn.addEventListener('click', () => {
                if (this.currentQuestionIndex < this.questions.length - 1) {
                    this.goToQuestion(this.currentQuestionIndex + 1);
                }
            });
        }

        const pauseBtn = document.getElementById('pauseBtn');
        if (pauseBtn) {
            pauseBtn.addEventListener('click', () => {
                this.isPaused = !this.isPaused;
                pauseBtn.textContent = this.isPaused ? 'Resume' : 'Pause';
                pauseBtn.className = this.isPaused ? 'btn btn-success me-2' : 'btn btn-warning me-2';
            });
        }

        const submitBtn = document.getElementById('submitBtn');
        if (submitBtn) {
            submitBtn.addEventListener('click', () => {
                // Check if all questions are answered
                const unanswered = this.questions.length - this.answers.size;
                if (unanswered > 0) {
                    // Show confirmation modal instead of simple alert
                    const confirmModal = new bootstrap.Modal(document.getElementById('confirmSubmitModal'));
                    document.getElementById('unansweredCount').textContent = unanswered;

                    // Setup the confirm button inside the modal
                    const confirmBtn = document.getElementById('confirmSubmitBtn');
                    // Remove old listeners to prevent multiple submissions
                    const newConfirmBtn = confirmBtn.cloneNode(true);
                    confirmBtn.parentNode.replaceChild(newConfirmBtn, confirmBtn);

                    newConfirmBtn.addEventListener('click', () => {
                        confirmModal.hide();
                        this.submitTest();
                    });

                    confirmModal.show();
                } else {
                    if (confirm('Are you sure you want to submit the test?')) {
                        this.submitTest();
                    }
                }
            });
        }

        // NOTE: We removed the 'toggleSidebarBtn' listener from here
        // because it is already handled in your HTML file's inline script.

        // Keyboard navigation
        document.addEventListener('keydown', (e) => {
            if (e.key === 'ArrowLeft' && this.currentQuestionIndex > 0) {
                this.goToQuestion(this.currentQuestionIndex - 1);
            } else if (e.key === 'ArrowRight' && this.currentQuestionIndex < this.questions.length - 1) {
                this.goToQuestion(this.currentQuestionIndex + 1);
            } else if (e.key === 'Enter') {
                if (this.currentQuestionIndex < this.questions.length - 1) {
                    this.goToQuestion(this.currentQuestionIndex + 1);
                }
            }
        });
    }

    async submitTest() {
        if (this.timerInterval) clearInterval(this.timerInterval);

        try {
            // Convert Map to plain object for JSON
            const answersObj = {};
            this.answers.forEach((value, key) => {
                answersObj[key] = value;
            });

            const submission = {
                answers: answersObj,
                test_type: this.testType
            };

            const response = await fetch(`${this.apiBaseUrl}/test/submit`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(submission)
            });

            if (!response.ok) {
                throw new Error(`Submission failed: ${response.status}`);
            }

            const result = await response.json();

            // Show results
            const scoreEl = document.getElementById('modalScore');
            if (scoreEl) scoreEl.textContent = result.score;

            const totalEl = document.getElementById('modalTotal');
            if (totalEl) totalEl.textContent = result.total;

            const pctEl = document.getElementById('modalPercentage');
            if (pctEl) pctEl.textContent = result.percentage.toFixed(1);

            const passedElement = document.getElementById('modalPassed');
            if (passedElement) {
                passedElement.textContent = result.passed ? 'PASSED' : 'FAILED';
                passedElement.className = result.passed ? 'badge bg-success fs-6' : 'badge bg-danger fs-6';
            }

            const barEl = document.getElementById('scoreProgressBar');
            if (barEl) barEl.style.width = `${result.percentage}%`;

            const modalEl = document.getElementById('successModal');
            if (modalEl) {
                const modal = new bootstrap.Modal(modalEl);
                modal.show();
            }

        } catch (error) {
            console.error('Error submitting test:', error);
            alert('Error submitting test. Please try again.');
        }
    }
}

// Initialize when page loads
document.addEventListener('DOMContentLoaded', () => {
    // Only initialize if the sidebar exists (meaning we are on the testing page)
    if (document.getElementById('questionSidebar')) {
        // Expose to window for button onclick handlers in HTML
        window.TestingEngine = new TestingEngine();
    }
});