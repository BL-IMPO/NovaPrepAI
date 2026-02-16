// frontend/assets/js/testing-engine.js
class TestingEngine {
    constructor() {
        const token = localStorage.getItem('access_token');
        if (!token) {
            console.warn("Unauthorized access attempt. Redirecting to login.");
            window.location.href = '/login'; // Update to your login page URL
            return; // Stop the engine from initializing
        }
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
        // Notice: The progress bar update logic was removed from here to fix the resetting bug!
    }

    renderSidebar() {
        const sidebar = document.getElementById('questionSidebar');
        if (!sidebar) return;

        sidebar.innerHTML = '';

        this.questions.forEach((question, index) => {
            const questionNumber = index + 1;
            const isAnswered = this.answers.has(index);
            const isCurrent = index === this.currentQuestionIndex;

            const item = document.createElement('a');
            item.href = '#';
            item.className = 'list-group-item list-group-item-action question-sidebar-item';

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

                // Close mobile sidebar if it's open
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

        const currentQ = this.questions[this.currentQuestionIndex];
        const questionText = currentQ[0];
        const optionsWithExtra = currentQ[1]; // The array from python including answers and extra_data

        // Safely extract the extraData (the last element) and actual answers
        const extraData = optionsWithExtra[optionsWithExtra.length - 1];
        const actualAnswers = optionsWithExtra.slice(0, -1);

        const questionNumber = this.currentQuestionIndex + 1;
        const totalQuestions = this.questions.length;

        // 1. Update Headers
        const titleEl = document.getElementById('currentQuestionTitle');
        if (titleEl) titleEl.textContent = `Question ${questionNumber}`;

        const counterEl = document.getElementById('questionCounter');
        if (counterEl) counterEl.textContent = `${questionNumber} of ${totalQuestions}`;

        const textEl = document.getElementById('questionText');
        if (textEl) textEl.textContent = questionText;

        // 2. Render Dynamic Media (SVG, Image, Text Block, Modal)
        const mediaContainer = document.getElementById('questionMediaContainer');
        if (mediaContainer) {
            mediaContainer.innerHTML = ''; // Clear previous media

            if (extraData && extraData[0] !== null) {
                const tag = extraData[0];
                const content = extraData[1];

                switch(tag) {
                    case 'SVG_GRAPH':
                        mediaContainer.innerHTML = content;
                        break;
                    case 'IMAGE_URL':
                        mediaContainer.innerHTML = `<img src="${content}" class="img-fluid rounded border mb-3" style="max-height: 300px; object-fit: contain;">`;
                        break;
                    case 'HTML_TABLE':
                        mediaContainer.innerHTML = `<div class="table-responsive mb-3 d-flex justify-content-center">${content}</div>`;
                        break;
                    case 'TEXT_BLOCK':
                        mediaContainer.innerHTML = `<div class="p-3 bg-light border rounded mb-3 text-start fw-bold">${content}</div>`;
                        break;
                    case 'FORMULA':
                        mediaContainer.innerHTML = `$$${content}$$`;
                        break;
                    case 'TEXT_BLOCK_LARGE':
                        // Create the trigger button for the reading passage modal
                        mediaContainer.innerHTML = `
                            <button type="button" class="btn btn-outline-primary w-100 mb-4 py-2 fs-5 fw-bold shadow-sm" data-bs-toggle="modal" data-bs-target="#readingPassageModal">
                                📖 Read Passage
                            </button>
                        `;
                        // Inject the text into the hidden modal body
                        const modalContent = document.getElementById('readingPassageContent');
                        if (modalContent) {
                            // Convert standard line breaks to HTML breaks
                            modalContent.innerHTML = content.replace(/\n/g, '<br>');
                        }
                        break;
                }
                mediaContainer.style.display = 'block';
            } else {
                mediaContainer.style.display = 'none'; // Hide if no extra data
            }
        }

        // 3. Render Answers
        const container = document.getElementById('answersContainer');
        if (!container) return;

        container.innerHTML = '';
        const answerLetters = ['A', 'B', 'C', 'D', 'E'];
        const currentAnswer = this.answers.get(this.currentQuestionIndex);
        const previousAnswer = this.previousAnswers.get(this.currentQuestionIndex);

        actualAnswers.forEach((answer, index) => {
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

            // Click entire box
            answerDiv.addEventListener('click', (e) => {
                if (e.target.type !== 'radio') {
                    this.selectAnswer(index);
                }
            });

            // Click radio directly
            const radio = answerDiv.querySelector('input[type="radio"]');
            radio.addEventListener('change', () => {
                if (radio.checked) {
                    this.selectAnswer(index);
                }
            });

            col.appendChild(answerDiv);
            container.appendChild(col);
        });

        // 4. Update Navigation Buttons
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
                const unanswered = this.questions.length - this.answers.size;
                if (unanswered > 0) {
                    const confirmModal = new bootstrap.Modal(document.getElementById('confirmSubmitModal'));
                    document.getElementById('unansweredCount').textContent = unanswered;

                    const confirmBtn = document.getElementById('confirmSubmitBtn');
                    const newConfirmBtn = confirmBtn.cloneNode(true);
                    confirmBtn.parentNode.replaceChild(newConfirmBtn, confirmBtn);

                    newConfirmBtn.addEventListener('click', () => {
                        // 1. Remove focus from the button so the browser doesn't complain
                        newConfirmBtn.blur();

                        // 2. Hide the modal
                        confirmModal.hide();

                        // 3. Submit the test
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
            // 1. Prepare the answers
            const answersObj = {};
            this.answers.forEach((value, key) => {
                answersObj[key] = value;
            });

            // 2. Prepare the submission payload
            const submission = {
                answers: answersObj,
                test_type: this.testType
            };

            // 3. Get the token
            const userToken = localStorage.getItem('access_token');

            // 4. Make ONE single fetch request
            const response = await fetch(`${this.apiBaseUrl}/test/submit`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${userToken}` // Send the token here
                },
                body: JSON.stringify(submission)
            });

            if (!response.ok) {
                throw new Error(`Submission failed: ${response.status}`);
            }

            const result = await response.json();

            // Populate Modals with True Scores vs Base Scores
            const scoreEl = document.getElementById('modalScore');
            if (scoreEl) scoreEl.textContent = result.score;

            const totalEl = document.getElementById('modalTotal');
            if (totalEl) totalEl.textContent = result.total; // From your backend 'total' key

            const weightedScoreEl = document.getElementById('modalWeightedScore');
            if (weightedScoreEl) weightedScoreEl.textContent = result.weighted_score;

            const pctEl = document.getElementById('modalPercentage');
            const percentage = result.percentage || (result.total > 0 ? (result.score / result.total * 100) : 0);
            if (pctEl) pctEl.textContent = percentage.toFixed(1);

            const passedElement = document.getElementById('modalPassed');
            if (passedElement) {
                passedElement.textContent = result.passed ? 'PASSED' : 'FAILED';
                passedElement.className = result.passed ? 'badge bg-success fs-6' : 'badge bg-danger fs-6';
            }

            const barEl = document.getElementById('scoreProgressBar');
            if (barEl) barEl.style.width = `${percentage}%`;

            // Set the View Results button link
            const viewResultsBtn = document.getElementById('viewResultsBtn');
            if (viewResultsBtn) {
                viewResultsBtn.onclick = () => {
                window.location.href = `/results/${result.attempt_id}/${this.testType}`;
                };
            }

            // Show the modal
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

document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('questionSidebar')) {
        window.TestingEngine = new TestingEngine();
    }
});