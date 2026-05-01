// frontend/assets/js/testing-engine.js

const FULL_TEST_SECTIONS = [
    { id: 'math_1', name: 'МАТЕМАТИКА (ОСНОВНОЙ ТЕСТ)', count: 30 },
    { id: 'analogy', name: 'АНАЛОГИИ И ДОПОЛНЕНИЕ ПРЕДЛОЖЕНИЙ', count: 30 },
    { id: 'reading', name: 'ЧТЕНИЕ И ПОНИМАНИЕ', count: 30 },
    { id: 'grammar', name: 'ПРАКТИЧЕСКАЯ ГРАММАТИКА', count: 30 },
    { id: 'math_2', name: 'МАТЕМАТИКА 2', count: 30 }
];

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

    // --- МЕТОДЫ ДЛЯ СОХРАНЕНИЯ ПРОГРЕССА ---
    saveLocalProgress() {
        const progress = {
            answers: Array.from(this.answers.entries()),
            markedQuestions: Array.from(this.markedQuestions),
            endTime: Date.now() + (this.timeLeft * 1000)
        };
        sessionStorage.setItem(`nova_prep_${this.testType}_progress`, JSON.stringify(progress));
    }

    loadLocalProgress() {
        const saved = sessionStorage.getItem(`nova_prep_${this.testType}_progress`);
        if (saved) {
            const progress = JSON.parse(saved);
            this.answers = new Map(progress.answers);
            this.markedQuestions = new Set(progress.markedQuestions);

            const timeRemaining = Math.floor((progress.endTime - Date.now()) / 1000);
            if (timeRemaining > 0) {
                this.timeLeft = timeRemaining;
            } else {
                this.timeLeft = 0;
            }
            return true;
        }
        return false;
    }

    clearLocalProgress() {
        sessionStorage.removeItem(`nova_prep_${this.testType}_progress`);
    }
    // ----------------------------------------

    getQuestionMeta(globalIndex) {
        if (this.testType !== 'full_test') {
            return {
                subType: this.testType,
                localIndex: globalIndex,
                sectionName: this.formatTestName(this.testType),
                totalInSection: this.questions.length
            };
        }

        let currentCount = 0;
        for (let section of FULL_TEST_SECTIONS) {
            if (globalIndex < currentCount + section.count) {
                return {
                    subType: section.id,
                    localIndex: globalIndex - currentCount,
                    sectionName: section.name,
                    totalInSection: section.count
                };
            }
            currentCount += section.count;
        }
        return { subType: 'unknown', localIndex: globalIndex, sectionName: 'Неизвестно', totalInSection: 0 };
    }

    async loadTestData() {
        try {
            console.log(`Загрузка теста: ${this.testType}`);
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
                            this.questions = new Array(chunk.total_questions).fill(null);

                            const hasSavedProgress = this.loadLocalProgress();

                            if (!hasSavedProgress) {
                                this.timeLeft = this.totalTime;
                            }

                            this.updateTimerDisplay();
                            this.renderSidebar();
                            this.updateProgress();

                        } else if (chunk.type === 'question') {
                            this.questions[chunk.index] = [chunk.question, chunk.answers];
                            const loadedQuestions = this.questions.filter(q => q !== null).length;

                            if (!this.timerInterval && loadedQuestions > 0) {
                                this.startTimer();
                            }

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
            console.error('Ошибка загрузки теста:', error);
            if (typeof window.showLoginRequiredModal === 'function') {
                window.showLoginRequiredModal();
            } else {
                alert('Ошибка загрузки теста. Пожалуйста, войдите в систему.');
            }
        }
    }

    formatTestName(testType) {
        const names = {
            'math_1': 'МАТЕМАТИКА (ОСНОВНОЙ)', 'math_2': 'МАТЕМАТИКА 2',
            'analogy': 'АНАЛОГИИ И ДОПОЛНЕНИЕ ПРЕДЛОЖЕНИЙ', 'reading': 'ЧТЕНИЕ И ПОНИМАНИЕ',
            'grammar': 'ПРАКТИЧЕСКАЯ ГРАММАТИКА', 'full_test': 'ПОЛНЫЙ ТЕСТ ОРТ'
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

            if (this.timeLeft > 0 && this.timeLeft < 300) {
                timerElement.classList.add('text-error', 'border-error');
                timerElement.classList.remove('text-warning', 'border-warning');
            } else if (this.timeLeft > 0 && this.timeLeft < 600) {
                timerElement.classList.add('text-warning', 'border-warning');
                timerElement.classList.remove('text-error', 'border-error');
            } else {
                timerElement.classList.remove('text-error', 'border-error', 'text-warning', 'border-warning');
            }
        }
    }

    renderSidebar() {
        const sidebar = document.getElementById('questionSidebar');
        if (!sidebar) return;

        sidebar.innerHTML = '';
        let currentSectionId = null;

        this.questions.forEach((question, index) => {
            const meta = this.getQuestionMeta(index);

            if (this.testType === 'full_test' && meta.subType !== currentSectionId) {
                const header = document.createElement('div');
                header.className = 'text-xs font-bold text-base-content/50 uppercase tracking-widest px-2 py-3 mt-4 mb-2 border-b border-base-200/50 sticky top-0 bg-base-100 z-10';
                header.textContent = meta.sectionName;
                sidebar.appendChild(header);
                currentSectionId = meta.subType;
            }

            const questionNumber = meta.localIndex + 1;
            const isLoaded = question !== null;
            const isAnswered = this.answers.has(index);
            const isCurrent = index === this.currentQuestionIndex;
            const isMarked = this.markedQuestions.has(index);

            const item = document.createElement('a');
            item.href = '#';

            item.className = 'question-sidebar-item';

            if (isCurrent) item.classList.add('active');
            if (isAnswered) {
                item.classList.add('answered');
                if (this.previousAnswers.has(index) && this.previousAnswers.get(index) !== this.answers.get(index)) {
                    item.classList.add('current-answer');
                }
            }
            if (isMarked) item.classList.add('marked');
            if (!isLoaded) item.classList.add('opacity-50', 'pointer-events-none', 'border-dashed');

            item.innerHTML = `
                <div class="flex justify-between items-center w-full">
                    <span class="flex items-center gap-2">Вопрос ${questionNumber} ${!isLoaded ? '<span class="loading loading-spinner loading-xs text-primary/50"></span>' : ''} ${isMarked ? '<span>🚩</span>' : ''}</span>
                    ${isAnswered ? '<span class="font-bold">✓</span>' : ''}
                </div>
            `;

            item.addEventListener('click', (e) => {
                e.preventDefault();
                this.goToQuestion(index);

                const sidebarEl = document.getElementById('sidebar');
                const overlayEl = document.getElementById('sidebarOverlay');
                if (window.innerWidth <= 1024 && sidebarEl && sidebarEl.classList.contains('open')) {
                    sidebarEl.classList.remove('open');
                    if (overlayEl) overlayEl.classList.remove('open');
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

        this.saveLocalProgress();
    }

    renderQuestion() {
        if (this.questions.length === 0) return;

        const currentQ = this.questions[this.currentQuestionIndex];
        const meta = this.getQuestionMeta(this.currentQuestionIndex);

        const questionNumber = meta.localIndex + 1;
        const totalInThisSection = meta.totalInSection;

        if (!currentQ) {
            const titleEl = document.getElementById('currentQuestionTitle');
            if (titleEl) titleEl.textContent = `Вопрос ${questionNumber}`;

            const counterEl = document.getElementById('questionCounter');
            if (counterEl) counterEl.textContent = `${questionNumber} из ${totalInThisSection}`;

            const textEl = document.getElementById('questionText');
            if (textEl) {
                textEl.innerHTML = `
                    <div class="text-center my-16 py-10">
                        <span class="loading loading-spinner text-primary w-16 h-16"></span>
                        <p class="mt-6 text-base-content/60 font-bold text-xl">ИИ генерирует этот вариант...</p>
                        <p class="text-base-content/40 font-medium mt-2">Пожалуйста, решите другие вопросы, пока мы его подготавливаем.</p>
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

        const questionText = currentQ[0];
        const optionsWithExtra = currentQ[1];

        let actualAnswers = [];
        let extraData = null;

        if (optionsWithExtra.length > 3) {
            const splitIndex = optionsWithExtra.length - 3;
            actualAnswers = optionsWithExtra.slice(0, splitIndex);
            const metadata = optionsWithExtra.slice(splitIndex);
            extraData = metadata.find(item => Array.isArray(item)) || ["None"];
        } else {
            actualAnswers = optionsWithExtra;
        }

        const titleEl = document.getElementById('currentQuestionTitle');
        if (titleEl) titleEl.textContent = `Вопрос ${questionNumber}`;

        const counterEl = document.getElementById('questionCounter');
        if (counterEl) counterEl.textContent = `${questionNumber} из ${totalInThisSection}`;

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
                        mediaContainer.innerHTML = `<img src="${content}" class="rounded-xl border border-base-300 shadow-sm" style="max-height: 400px; object-fit: contain;">`;
                        break;
                    case 'HTML_TABLE':
                        mediaContainer.innerHTML = `<div class="overflow-x-auto w-full flex justify-center"><div class="table-wrapper">${content}</div></div>`;
                        break;
                    case 'TEXT_BLOCK':
                        mediaContainer.innerHTML = `<div class="p-6 bg-base-200/50 border border-base-300 rounded-[1.5rem] w-full text-left font-medium text-lg leading-relaxed text-base-content/80 shadow-sm">${content}</div>`;
                        break;
                    case 'FORMULA':
                        mediaContainer.innerHTML = `<div class="text-3xl text-base-content font-bold p-4">$$${content}$$</div>`;
                        break;
                    case 'TEXT_BLOCK_LARGE':
                        mediaContainer.innerHTML = `
                            <button type="button" class="btn btn-primary rounded-full px-8 py-4 h-auto text-lg font-bold shadow-lg shadow-primary/20" onclick="document.getElementById('readingPassageModal').showModal();">
                                📖 Открыть текст для чтения
                            </button>
                        `;
                        const modalContent = document.getElementById('readingPassageContent');
                        if (modalContent) {
                            let formattedHtml = '';
                            let lineNumber = 1;
                            let isNumbering = false;

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

                            const rawParagraphs = content.split('\n');
                            const finalLines = [];

                            rawParagraphs.forEach(p => {
                                if (p.trim() === '') {
                                    finalLines.push('');
                                } else {
                                    const indentMatch = p.match(/^(\s+)/);
                                    const indent = indentMatch ? indentMatch[1] : '';
                                    const cleanText = p.substring(indent.length);

                                    const wrappedLines = wrapText(cleanText, 55);
                                    if (wrappedLines.length > 0) {
                                        wrappedLines[0] = indent + wrappedLines[0];
                                    }
                                    finalLines.push(...wrappedLines);
                                }
                            });

                            finalLines.forEach(line => {
                                if (line.includes('_start_')) { isNumbering = true; line = line.replace('_start_', ''); }
                                if (line.includes('_continue_')) { isNumbering = true; line = line.replace('_continue_', ''); }
                                if (line.includes('_pause_')) { isNumbering = false; line = line.replace('_pause_', ''); }

                                let numDisplay = '';
                                if (isNumbering && line.trim() !== '') {
                                    if (lineNumber === 1) {
                                        numDisplay = '<span class="text-xs">строка</span>';
                                    } else if (lineNumber % 5 === 0) {
                                        numDisplay = lineNumber;
                                    }
                                    lineNumber++;
                                }

                                let textHtml = line.replace(/\t/g, '&nbsp;&nbsp;&nbsp;&nbsp;');

                                formattedHtml += `
                                <div class="ort-line">
                                    <div class="ort-line-number font-mono">${numDisplay}</div>
                                    <div class="ort-line-text">${textHtml}</div>
                                </div>`;
                            });

                            modalContent.innerHTML = formattedHtml;
                        }
                        break;
                }
                mediaContainer.style.display = 'flex';
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

        if (meta.subType === 'math_1') {
            if (comparisonContainer) {
                comparisonContainer.style.display = 'grid';
                document.getElementById('columnA').innerHTML = actualAnswers[0] || '';
                document.getElementById('columnB').innerHTML = actualAnswers[1] || '';
            }

            const ortOptions = ["Значение в колонке А больше", "Значение в колонке Б больше", "Оба значения равны", "Значения невозможно сравнить"];
            const answerLetters = ['А', 'Б', 'В', 'Г'];

            ortOptions.forEach((answerText, index) => {

                const answerDiv = document.createElement('div');
                answerDiv.className = `answer-option ${currentAnswer === index ? 'selected' : ''} ${previousAnswer === index && currentAnswer !== index ? 'previous' : ''} ${isLocked && currentAnswer !== index && previousAnswer !== index ? 'opacity-50' : ''}`;

                if (isLocked) answerDiv.style.cursor = 'not-allowed';

                answerDiv.innerHTML = `
                    <div class="flex items-center w-full pointer-events-none">
                        <input class="hidden" type="radio" name="answer" id="answer${index}" value="${index}" ${currentAnswer === index ? 'checked' : ''} ${isLocked ? 'disabled' : ''}>
                        <label class="flex items-center w-full m-0 pointer-events-none" for="answer${index}">
                            <span class="option-letter">${answerLetters[index]}</span>
                            <span class="flex-grow">${answerText}</span>
                        </label>
                    </div>
                `;

                answerDiv.addEventListener('click', (e) => {
                    if (isLocked) return;
                    this.selectAnswer(index);
                });

                container.appendChild(answerDiv);
            });

            if (window.MathJax) {
                MathJax.typesetPromise([document.getElementById('questionText'), comparisonContainer, container, document.getElementById('questionMediaContainer')]).catch(err => console.log('MathJax error:', err));
            }

        } else {
            if (comparisonContainer) comparisonContainer.style.display = 'none';

            const answerLetters = ['А', 'Б', 'В', 'Г', 'Д'];
            actualAnswers.forEach((answer, index) => {

                const answerDiv = document.createElement('div');
                answerDiv.className = `answer-option ${currentAnswer === index ? 'selected' : ''} ${previousAnswer === index && currentAnswer !== index ? 'previous' : ''} ${isLocked && currentAnswer !== index && previousAnswer !== index ? 'opacity-50' : ''}`;

                if (isLocked) answerDiv.style.cursor = 'not-allowed';

                answerDiv.innerHTML = `
                    <div class="flex items-center w-full pointer-events-none">
                        <input class="hidden" type="radio" name="answer" id="answer${index}" value="${index}" ${currentAnswer === index ? 'checked' : ''} ${isLocked ? 'disabled' : ''}>
                        <label class="flex items-center w-full m-0 pointer-events-none" for="answer${index}">
                            <span class="option-letter">${answerLetters[index] || index + 1})</span>
                            <span class="flex-grow">${answer}</span>
                        </label>
                    </div>
                `;

                answerDiv.addEventListener('click', (e) => {
                    if (isLocked) return;
                    this.selectAnswer(index);
                });

                container.appendChild(answerDiv);
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

        const warningIcon = `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="mr-2" viewBox="0 0 16 16"><path d="M14.778.085A.5.5 0 0 1 15 .5V8a.5.5 0 0 1-.314.464L14.5 8l.186.464-.003.001-.006.003-.023.009a12 12 0 0 1-.397.15c-.264.095-.631.223-1.047.35-.816.252-1.879.523-2.71.523-.847 0-1.548-.28-2.158-.525l-.028-.01C7.68 8.71 7.14 8.5 6.5 8.5c-.7 0-1.638.23-2.437.477A20 20 0 0 0 3 9.342V15.5a.5.5 0 0 1-1 0V.5a.5.5 0 0 1 1 0v.282c.226-.079.496-.17.79-.26C4.606.272 5.67 0 6.5 0c.84 0 1.524.277 2.121.519l.043.018C9.286.788 9.828 1 10.5 1c.7 0 1.638-.23 2.437-.477a20 20 0 0 0 1.349-.476l.019-.007.004-.002h.001"/></svg>`;

        if (markBtn) {
            if (isMarked) {
                markBtn.classList.remove('btn-outline');
                markBtn.innerHTML = `${warningIcon} Снять сомнение`;
            } else {
                markBtn.classList.add('btn-outline');
                markBtn.innerHTML = `${warningIcon} Сомневаюсь`;
            }
        }

        if (markCurrentBtn) {
            if (isMarked) {
                markCurrentBtn.classList.remove('btn-outline');
                markCurrentBtn.innerHTML = `${warningIcon} Снять отметку`;
            } else {
                markCurrentBtn.classList.add('btn-outline');
                markCurrentBtn.innerHTML = `${warningIcon} Сомневаюсь`;
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

        this.saveLocalProgress();
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
        if (progressBar) progressBar.value = percentage;
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

                    const confirmModalEl = document.getElementById('confirmSubmitModal');
                    if (confirmModalEl) {
                        document.getElementById('unansweredCount').textContent = unanswered;

                        const confirmBtn = document.getElementById('confirmSubmitBtn');
                        const newConfirmBtn = confirmBtn.cloneNode(true);
                        confirmBtn.parentNode.replaceChild(newConfirmBtn, confirmBtn);

                        newConfirmBtn.addEventListener('click', () => {
                            newConfirmBtn.innerHTML = '<span class="loading loading-spinner loading-sm mr-2"></span>Отправка...';
                            newConfirmBtn.disabled = true;
                            confirmModalEl.close();
                            this.submitTest();
                        });

                        confirmModalEl.showModal();
                    }
                } else {
                    const allAnsweredModalEl = document.getElementById('allAnsweredModal');
                    if (allAnsweredModalEl) {
                        const confirmBtn = document.getElementById('confirmAllAnsweredBtn');

                        const newConfirmBtn = confirmBtn.cloneNode(true);
                        confirmBtn.parentNode.replaceChild(newConfirmBtn, confirmBtn);

                        newConfirmBtn.addEventListener('click', () => {
                            newConfirmBtn.innerHTML = '<span class="loading loading-spinner loading-sm mr-2"></span>Отправка...';
                            newConfirmBtn.disabled = true;
                            allAnsweredModalEl.close();

                            submitBtn.innerHTML = '<span class="loading loading-spinner loading-sm"></span>';
                            submitBtn.disabled = true;
                            this.submitTest();
                        });

                        allAnsweredModalEl.showModal();
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
                if (!refreshed) console.warn('Ошибка обновления токена');
            } catch (error) { console.error('Ошибка обновления токена:', error); }
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

        this.clearLocalProgress();

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

            if (!response.ok) throw new Error(`Ошибка отправки: ${response.status}`);
            const result = await response.json();
            const streakCount = document.getElementById('streakCount');
            const streakBadge = document.getElementById('navStreakBar');

            if (streakCount && streakBadge) {
                if (!streakBadge.classList.contains('bg-warning')) {
                    let currentStreak = parseInt(streakCount.textContent) || 0;
                    streakCount.textContent = currentStreak + 1;
                    streakBadge.classList.remove('d-none');
                }
            }

            const scoreEl = document.getElementById('modalScore');
            if (scoreEl) scoreEl.textContent = result.score;
            const totalEl = document.getElementById('modalTotal');
            if (totalEl) totalEl.textContent = result.total;
            const weightedScoreEl = document.getElementById('modalWeightedScore');
            if (weightedScoreEl) weightedScoreEl.textContent = result.weighted_score;
            const pctEl = document.getElementById('modalPercentage');
            const percentage = result.percentage || (result.total > 0 ? (result.score / result.total * 100) : 0);
            if (pctEl) pctEl.textContent = percentage.toFixed(0);

            const passedElement = document.getElementById('modalPassed');
            if (passedElement) {
                passedElement.textContent = result.passed ? 'ПРОЙДЕН' : 'НЕ ПРОЙДЕН';
                passedElement.className = result.passed ? 'badge badge-success font-black text-xs py-3 px-4 shadow-sm' : 'badge badge-error font-black text-xs py-3 px-4 shadow-sm';
            }

            const barEl = document.getElementById('scoreProgressBar');
            if (barEl) barEl.value = percentage;

            const viewResultsBtn = document.getElementById('viewResultsBtn');
            if (viewResultsBtn) {
                viewResultsBtn.onclick = () => window.location.href = `/results/${result.attempt_id}/${this.testType}`;
            }

            const modalEl = document.getElementById('successModal');
            if (modalEl) modalEl.showModal();

        } catch (error) {
            console.error('Ошибка при отправке теста:', error);
            alert('Произошла ошибка при сохранении результатов. Пожалуйста, попробуйте еще раз.');
            const submitBtn = document.getElementById('submitBtn');
            if (submitBtn) {
                submitBtn.innerHTML = 'Завершить';
                submitBtn.disabled = false;
            }
        }
    }
}

document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('questionSidebar')) {
        window.TestingEngine = new TestingEngine();
    }
});