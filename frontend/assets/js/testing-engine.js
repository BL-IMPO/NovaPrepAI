// frontend/assets/js/testing-engine.js
class TestingEngine {
    constructor() {
        const pathParts = window.location.pathname.split('/');
        this.testType = pathParts[pathParts.length - 1];

        this.questions = [];
        this.answers = new Map();
        this.previousAnswers = new Map();
        this.markedQuestions = new Set();

        this.currentQuestionIndex = 0;
        this.timeLeft = 0;
        this.totalTime = 0;
        this.timerInterval = null;
        this.refreshInterval = null;

        this.apiBaseUrl = '/fastapi/api';

        window.addEventListener('beforeunload', () => this.unloadHandler());

        this.loadTestData();
        this.initEventListeners();
    }

    async loadTestData() {
        try {
            console.log(`Loading test data for: ${this.testType}`);
            const response = await fetch(`${this.apiBaseUrl}/test/${this.testType}`, {
                credentials: 'same-origin'
            });
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split('\n');
                buffer = lines.pop();

                for (const line of lines) {
                    if (line.trim()) {
                        const chunk = JSON.parse(line);

                        if (chunk.type === 'meta') {
                            this.totalTime = chunk.time_limit;
                            this.timeLeft = this.totalTime;

                            this.questions = new Array(chunk.total_questions).fill(null);

                            this.startTimer();
                            this.updateTimerDisplay();
                            this.renderSidebar();
                            this.updateProgress();

                        } else if (chunk.type === 'question') {
                            this.questions[chunk.index] = [chunk.question, chunk.answers];
                            const loadedQuestions = this.questions.filter(q => q !== null).length;

                            if (loadedQuestions === 1) {
                                this.currentQuestionIndex = chunk.index;
                                this.renderQuestion();
                            } else if (this.currentQuestionIndex === chunk.index) {
                                this.renderQuestion();
                            }

                            this.renderSidebar();
                            this.updateProgress();
                        }
                    }
                }
            }

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
            'math_1': 'МАТЕМАТИКА (ОСНОВНОЙ)', 'math_2': 'МАТЕМАТИКА 2',
            'analogy': 'АНАЛОГИИ И ДОПОЛНЕНИЕ ПРЕДЛОЖЕНИЙ', 'reading': 'ЧТЕНИЕ И ПОНИМАНИЕ',
            'grammar': 'ПРАКТИЧЕСКАЯ ГРАММАТИКА РУССКОГО ЯЗЫКА', 'full_test': 'ПОЛНЫЙ ТЕСТ ОРТ',
            'special_math': 'МАТЕМАТИКА (ПРЕДМЕТНЫЙ)', 'special_biology': 'БИОЛОГИЯ',
            'special_chemistry': 'ХИМИЯ', 'special_english': 'АНГЛИЙСКИЙ ЯЗЫК',
            'special_history': 'ИСТОРИЯ', 'special_physics': 'ФИЗИКА',
            'special_russian_grammar': 'РУССКИЙ ЯЗЫК И ЛИТЕРАТУРА', 'special_kyrgyz_grammar': 'КЫРГЫЗСКИЙ ЯЗЫК И ЛИТЕРАТУРА'
        };
        return names[testType] || testType.replace('_', ' ').toUpperCase();
    }

    startTimer() {
        this.updateTimerDisplay();
        this.timerInterval = setInterval(() => {
            if (this.timeLeft > 0) {
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
    }

    renderSidebar() {
        const sidebar = document.getElementById('questionSidebar');
        if (!sidebar) return;

        sidebar.innerHTML = '';

        this.questions.forEach((question, index) => {
            const questionNumber = index + 1;
            const isLoaded = question !== null;
            const isAnswered = this.answers.has(index);
            const isCurrent = index === this.currentQuestionIndex;
            const isMarked = this.markedQuestions.has(index);

            const item = document.createElement('a');
            item.href = '#';
            item.className = `list-group-item list-group-item-action question-sidebar-item`;

            if (isCurrent) item.classList.add('active');
            if (isAnswered) {
                item.classList.add('answered');
                if (this.previousAnswers.has(index) && this.previousAnswers.get(index) !== this.answers.get(index)) {
                    item.classList.add('current-answer');
                }
            }

            if (!isLoaded) item.style.opacity = '0.6';

            item.innerHTML = `
                <div class="d-flex justify-content-between align-items-center">
                    <span>Вопрос ${questionNumber} ${!isLoaded ? '⏳' : ''} ${isMarked ? '<span class="ms-1 fs-6">🚩</span>' : ''}</span>
                    ${isAnswered ? '<span class="badge bg-success">✓</span>' : ''}
                </div>
            `;

            item.addEventListener('click', (e) => {
                e.preventDefault();
                this.goToQuestion(index);

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

    markCurrentQuestion() {
        if (this.markedQuestions.has(this.currentQuestionIndex)) {
            this.markedQuestions.delete(this.currentQuestionIndex);
        } else {
            this.markedQuestions.add(this.currentQuestionIndex);
        }
        this.renderSidebar();
        this.renderQuestion();
    }

    renderQuestion() {
        if (this.questions.length === 0) return;

        const currentQ = this.questions[this.currentQuestionIndex];
        const questionNumber = this.currentQuestionIndex + 1;
        const totalQuestions = this.questions.length;

        // --- HANDLE LOADING STATE FOR AI QUESTIONS ---
        if (!currentQ) {
            const titleEl = document.getElementById('currentQuestionTitle');
            if (titleEl) titleEl.textContent = `Вопрос ${questionNumber}`;

            const counterEl = document.getElementById('questionCounter');
            if (counterEl) counterEl.textContent = `${questionNumber} из ${totalQuestions}`;

            const textEl = document.getElementById('questionText');
            if (textEl) {
                textEl.innerHTML = `
                    <div class="text-center my-5 py-5">
                        <div class="spinner-border text-primary" role="status"></div>
                        <p class="mt-3 text-muted">ИИ генерирует этот вопрос. Пожалуйста, решите другие вопросы, пока мы его подготавливаем...</p>
                    </div>
                `;
            }

            const mediaContainer = document.getElementById('questionMediaContainer');
            if (mediaContainer) mediaContainer.style.display = 'none';

            const container = document.getElementById('answersContainer');
            if (container) container.innerHTML = '';

            const comparisonContainer = document.getElementById('comparisonContainer');
            if (comparisonContainer) comparisonContainer.style.display = 'none';

            this.updateNavigationButtons();
            return;
        }

        // --- HANDLE RENDER FOR LOADED QUESTIONS ---
        const questionText = currentQ[0];
        const optionsWithExtra = currentQ[1];

        // --- THE FIX: Smartly locate the extraData array ---
        let extraData = null;
        for (let i = Math.max(0, optionsWithExtra.length - 3); i < optionsWithExtra.length; i++) {
            if (Array.isArray(optionsWithExtra[i])) {
                extraData = optionsWithExtra[i];
                break;
            }
        }

        const actualAnswers = optionsWithExtra.slice(0, -3);

        const titleEl = document.getElementById('currentQuestionTitle');
        if (titleEl) titleEl.textContent = `Вопрос ${questionNumber}`;

        const counterEl = document.getElementById('questionCounter');
        if (counterEl) counterEl.textContent = `${questionNumber} из ${totalQuestions}`;

        const textEl = document.getElementById('questionText');
        if (textEl) textEl.textContent = questionText;

        const mediaContainer = document.getElementById('questionMediaContainer');
        if (mediaContainer) {
            mediaContainer.innerHTML = '';

            if (extraData && extraData[0] !== null && extraData[0] !== "None") {
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
                        mediaContainer.innerHTML = `
                            <button type="button" class="btn btn-outline-primary w-100 mb-4 py-2 fs-5 fw-bold shadow-sm" data-bs-toggle="modal" data-bs-target="#readingPassageModal">
                                📖 Прочитать текст
                            </button>
                        `;
                        const modalContent = document.getElementById('readingPassageContent');
                        if (modalContent) {
                            let formattedHtml = '';
                            let lineNumber = 1;
                            let isNumbering = false;

                            // 1. Smart function to slice long AI paragraphs into short ORT-style lines
                            const wrapText = (text, maxLength) => {
                                const words = text.split(' ');
                                let lines = [];
                                let currentLine = '';
                                words.forEach(word => {
                                    if (currentLine.length + word.length > maxLength && currentLine.trim() !== '') {
                                        lines.push(currentLine);
                                        currentLine = word + ' ';
                                    } else {
                                        currentLine += word + ' ';
                                    }
                                });
                                if (currentLine.trim()) lines.push(currentLine);
                                return lines;
                            };

                            // 2. Break down the raw text into a list of short strings
                            const rawParagraphs = content.split('\n');
                            const finalLines = [];

                            rawParagraphs.forEach(p => {
                                if (p.trim() === '') {
                                    finalLines.push('');
                                } else {
                                    // Preserve tabs/spaces at the start of paragraphs
                                    const indentMatch = p.match(/^(\s+)/);
                                    const indent = indentMatch ? indentMatch[1] : '';
                                    const cleanText = p.substring(indent.length);

                                    // Force wrap at 55 characters to create the narrow column look
                                    const wrappedLines = wrapText(cleanText, 55);
                                    if (wrappedLines.length > 0) {
                                        wrappedLines[0] = indent + wrappedLines[0]; // Put indent back on line 1
                                    }
                                    finalLines.push(...wrappedLines);
                                }
                            });

                            // 3. Render the processed short lines with line numbers
                            finalLines.forEach(line => {
                                if (line.includes('_start_')) { isNumbering = true; line = line.replace('_start_', ''); }
                                if (line.includes('_continue_')) { isNumbering = true; line = line.replace('_continue_', ''); }
                                if (line.includes('_pause_')) { isNumbering = false; line = line.replace('_pause_', ''); }

                                let numDisplay = '';
                                // Only add a number if the line actually has text
                                if (isNumbering && line.trim() !== '') {
                                    if (lineNumber === 1) {
                                        numDisplay = '<span style="font-size: 0.7em;">строка</span>';
                                    } else if (lineNumber % 5 === 0) {
                                        numDisplay = lineNumber;
                                    }
                                    lineNumber++;
                                }

                                let textHtml = line.replace(/\t/g, '&nbsp;&nbsp;&nbsp;&nbsp;');

                                formattedHtml += `
                                <div class="ort-line">
                                    <div class="ort-line-number">${numDisplay}</div>
                                    <div class="ort-line-text">${textHtml}</div>
                                </div>`;
                            });

                            modalContent.innerHTML = formattedHtml;
                        }
                        break;
                }
                mediaContainer.style.display = 'block';
            } else {
                mediaContainer.style.display = 'none';
            }
        }

        const container = document.getElementById('answersContainer');
        const comparisonContainer = document.getElementById('comparisonContainer');
        if (!container) return;
        container.innerHTML = '';

        const currentAnswer = this.answers.get(this.currentQuestionIndex);
        const previousAnswer = this.previousAnswers.get(this.currentQuestionIndex);

        const isLocked = this.previousAnswers.has(this.currentQuestionIndex) && previousAnswer !== currentAnswer;

        if (this.testType === 'math_1') {
            if (comparisonContainer) {
                comparisonContainer.style.display = 'flex';
                document.getElementById('columnA').innerHTML = actualAnswers[0] || '';
                document.getElementById('columnB').innerHTML = actualAnswers[1] || '';
            }

            const ortOptions = ["Значение в колонке А больше", "Значение в колонке Б больше", "Оба значения равны", "Значения невозможно сравнить"];
            const answerLetters = ['А', 'Б', 'В', 'Г'];

            ortOptions.forEach((answerText, index) => {
                const col = document.createElement('div');
                col.className = 'col-md-6 mb-3';

                const answerDiv = document.createElement('div');
                answerDiv.className = `answer-option ${currentAnswer === index ? 'selected' : ''} ${previousAnswer === index && currentAnswer !== index ? 'previous' : ''} ${isLocked && currentAnswer !== index && previousAnswer !== index ? 'opacity-50' : ''}`;
                if (isLocked) answerDiv.style.cursor = 'not-allowed';

                answerDiv.innerHTML = `
                    <div class="form-check">
                        <input class="form-check-input" type="radio" name="answer" id="answer${index}" value="${index}" ${currentAnswer === index ? 'checked' : ''} ${isLocked ? 'disabled' : ''}>
                        <label class="form-check-label w-100" for="answer${index}" ${isLocked ? 'style="cursor: not-allowed;"' : ''}>
                            <span class="option-letter">${answerLetters[index]}</span> ${answerText}
                        </label>
                    </div>
                `;

                answerDiv.addEventListener('click', (e) => {
                    if (isLocked) return;
                    if (e.target.type !== 'radio') this.selectAnswer(index);
                });
                answerDiv.querySelector('input[type="radio"]').addEventListener('change', (e) => {
                    if (isLocked) return;
                    if (e.target.checked) this.selectAnswer(index);
                });

                col.appendChild(answerDiv);
                container.appendChild(col);
            });

            if (window.MathJax) {
                MathJax.typesetPromise([document.getElementById('questionText'), comparisonContainer, container, document.getElementById('questionMediaContainer')]).catch(err => console.log('MathJax error:', err));
            }

        } else {
            if (comparisonContainer) comparisonContainer.style.display = 'none';

            const answerLetters = ['А', 'Б', 'В', 'Г', 'Д'];
            actualAnswers.forEach((answer, index) => {
                const col = document.createElement('div');
                col.className = 'col-md-6 mb-3';

                const answerDiv = document.createElement('div');
                answerDiv.className = `answer-option ${currentAnswer === index ? 'selected' : ''} ${previousAnswer === index && currentAnswer !== index ? 'previous' : ''} ${isLocked && currentAnswer !== index && previousAnswer !== index ? 'opacity-50' : ''}`;
                if (isLocked) answerDiv.style.cursor = 'not-allowed';

                answerDiv.innerHTML = `
                    <div class="form-check">
                        <input class="form-check-input" type="radio" name="answer" id="answer${index}" value="${index}" ${currentAnswer === index ? 'checked' : ''} ${isLocked ? 'disabled' : ''}>
                        <label class="form-check-label w-100" for="answer${index}" ${isLocked ? 'style="cursor: not-allowed;"' : ''}>
                            <span class="option-letter">${answerLetters[index] || index + 1})</span> ${answer}
                        </label>
                    </div>
                `;

                answerDiv.addEventListener('click', (e) => {
                    if (isLocked) return;
                    if (e.target.type !== 'radio') this.selectAnswer(index);
                });
                answerDiv.querySelector('input[type="radio"]').addEventListener('change', (e) => {
                    if (isLocked) return;
                    if (e.target.checked) this.selectAnswer(index);
                });

                col.appendChild(answerDiv);
                container.appendChild(col);
            });

            if (window.MathJax) {
                MathJax.typesetPromise([document.getElementById('questionText'), container, document.getElementById('questionMediaContainer')]).catch(err => console.log('MathJax error:', err));
            }
        }

        this.updateNavigationButtons();
    }

    updateNavigationButtons() {
        const totalQuestions = this.questions.length;
        const prevBtn = document.getElementById('prevBtn');
        if (prevBtn) prevBtn.disabled = this.currentQuestionIndex === 0;
        const nextBtn = document.getElementById('nextBtn');
        if (nextBtn) nextBtn.disabled = this.currentQuestionIndex === totalQuestions - 1;

        const isMarked = this.markedQuestions.has(this.currentQuestionIndex);
        const markBtn = document.getElementById('markBtn');
        const markCurrentBtn = document.getElementById('markCurrentBtn');

        if (markBtn) {
            if (isMarked) {
                markBtn.classList.remove('btn-outline-warning');
                markBtn.classList.add('btn-warning');
                markBtn.innerHTML = `Unflag Question`;
            } else {
                markBtn.classList.remove('btn-warning');
                markBtn.classList.add('btn-outline-warning');
                markBtn.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-flag me-1" viewBox="0 0 16 16"><path d="M14.778.085A.5.5 0 0 1 15 .5V8a.5.5 0 0 1-.314.464L14.5 8l.186.464-.003.001-.006.003-.023.009a12 12 0 0 1-.397.15c-.264.095-.631.223-1.047.35-.816.252-1.879.523-2.71.523-.847 0-1.548-.28-2.158-.525l-.028-.01C7.68 8.71 7.14 8.5 6.5 8.5c-.7 0-1.638.23-2.437.477A20 20 0 0 0 3 9.342V15.5a.5.5 0 0 1-1 0V.5a.5.5 0 0 1 1 0v.282c.226-.079.496-.17.79-.26C4.606.272 5.67 0 6.5 0c.84 0 1.524.277 2.121.519l.043.018C9.286.788 9.828 1 10.5 1c.7 0 1.638-.23 2.437-.477a20 20 0 0 0 1.349-.476l.019-.007.004-.002h.001"/></svg> Flag as Strange`;
            }
        }

        if (markCurrentBtn) {
            if (isMarked) {
                markCurrentBtn.classList.remove('btn-outline-warning');
                markCurrentBtn.classList.add('btn-warning');
                markCurrentBtn.innerHTML = `Unflag Question`;
            } else {
                markCurrentBtn.classList.remove('btn-warning');
                markCurrentBtn.classList.add('btn-outline-warning');
                markCurrentBtn.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-flag-fill me-1" viewBox="0 0 16 16"><path d="M14.778.085A.5.5 0 0 1 15 .5V8a.5.5 0 0 1-.314.464L14.5 8l.186.464-.003.001-.006.003-.023.009a12 12 0 0 1-.397.15c-.264.095-.631.223-1.047.35-.816.252-1.879.523-2.71.523-.847 0-1.548-.28-2.158-.525l-.028-.01C7.68 8.71 7.14 8.5 6.5 8.5c-.7 0-1.638.23-2.437.477A20 20 0 0 0 3 9.342V15.5a.5.5 0 0 1-1 0V.5a.5.5 0 0 1 1 0v.282c.226-.079.496-.17.79-.26C4.606.272 5.67 0 6.5 0c.84 0 1.524.277 2.121.519l.043.018C9.286.788 9.828 1 10.5 1c.7 0 1.638-.23 2.437-.477a20 20 0 0 0 1.349-.476l.019-.007.004-.002h.001"/></svg> Flag as Strange`;
            }
        }
    }

    selectAnswer(answerIndex) {
        if (!this.questions[this.currentQuestionIndex]) return;

        const currentAnswer = this.answers.get(this.currentQuestionIndex);
        const hasPrevious = this.previousAnswers.has(this.currentQuestionIndex);

        if (hasPrevious && currentAnswer !== undefined && currentAnswer !== answerIndex) {
            return;
        }

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
        if (progressText) progressText.textContent = `${answeredCount}/${totalQuestions}`;
        const progressBar = document.getElementById('progressBar');
        if (progressBar) progressBar.style.width = `${percentage}%`;
    }

    initEventListeners() {
        const prevBtn = document.getElementById('prevBtn');
        if (prevBtn) {
            prevBtn.addEventListener('click', () => {
                if (this.currentQuestionIndex > 0) this.goToQuestion(this.currentQuestionIndex - 1);
            });
        }

        const nextBtn = document.getElementById('nextBtn');
        if (nextBtn) {
            nextBtn.addEventListener('click', () => {
                if (this.currentQuestionIndex < this.questions.length - 1) this.goToQuestion(this.currentQuestionIndex + 1);
            });
        }

        const markBtn = document.getElementById('markBtn');
        if (markBtn) markBtn.addEventListener('click', () => this.markCurrentQuestion());
        const markCurrentBtn = document.getElementById('markCurrentBtn');
        if (markCurrentBtn) markCurrentBtn.addEventListener('click', () => this.markCurrentQuestion());

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
                        newConfirmBtn.blur();
                        confirmModal.hide();
                        this.submitTest();
                    });

                    confirmModal.show();
                } else {
                    if (confirm('Вы уверены, что хотите завершить тест?')) {
                        this.submitTest();
                    }
                }
            });
        }

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

    startTokenRefresh() {
        if (this.refreshInterval) clearInterval(this.refreshInterval);
        this.refreshInterval = setInterval(async () => {
            try {
                const refreshed = await refreshAccessToken();
                if (!refreshed) console.warn('Token refresh failed');
            } catch (error) { console.error('Token refresh error:', error); }
        }, 50 * 60 * 1000);
    }

    clearRefreshInterval() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
            this.refreshInterval = null;
        }
    }

    unloadHandler() {
        this.clearRefreshInterval();
    }

    async submitTest() {
        if (this.timerInterval) clearInterval(this.timerInterval);
        this.clearRefreshInterval();

        try {
            const answersObj = {};
            this.answers.forEach((value, key) => { answersObj[key] = value; });

            const submission = {
                answers: answersObj,
                test_type: this.testType,
                marked_questions: Array.from(this.markedQuestions)
            };

            const response = await fetch(`${this.apiBaseUrl}/test/submit`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'same-origin',
                body: JSON.stringify(submission)
            });

            if (!response.ok) throw new Error(`Submission failed: ${response.status}`);
            const result = await response.json();

            const scoreEl = document.getElementById('modalScore');
            if (scoreEl) scoreEl.textContent = result.score;
            const totalEl = document.getElementById('modalTotal');
            if (totalEl) totalEl.textContent = result.total;
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

            const viewResultsBtn = document.getElementById('viewResultsBtn');
            if (viewResultsBtn) {
                viewResultsBtn.onclick = () => window.location.href = `/results/${result.attempt_id}/${this.testType}`;
            }

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