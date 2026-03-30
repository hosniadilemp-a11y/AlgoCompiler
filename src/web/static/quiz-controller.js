class QuizController {
    constructor(courseController) {
        this.course = courseController;
        this.quizData = [];
        this.currentQuestionIndex = 0;
        this.score = 0;
        this.conceptAnalysis = {};
        this.userAnswers = [];
        this.quizLoadTimeoutMs = 12000;
        this.quizSaveTimeoutMs = 12000;
        this.quizSessionToken = 0;

        this.modal = null;
        this.initDOM();
    }

    initDOM() {
        // Create Quiz Modal Container
        this.modal = document.createElement('div');
        this.modal.className = 'quiz-modal';
        this.modal.innerHTML = `
            <div class="quiz-modal-content">
                <div class="quiz-header">
                    <div class="quiz-progress-text">Test - Question <span id="quiz-current-num">1</span> / <span id="quiz-total-num">20</span></div>
                    <div class="quiz-progress-bar" style="display:none;"><div id="quiz-progress-fill"></div></div>
                    <div id="quiz-bubbles" class="quiz-bubbles"></div>
                    <button class="quiz-close-btn"><i class="fas fa-times"></i></button>
                </div>
                <div id="quiz-body" class="quiz-body">
                    <!-- Dynamic Content -->
                </div>
                <div class="quiz-footer">
                    <button id="quiz-prev-btn" class="quiz-btn secondary" disabled><i class="fas fa-arrow-left"></i> Précédent</button>
                    <button id="quiz-next-btn" class="quiz-btn primary">Question suivante <i class="fas fa-arrow-right"></i></button>
                    <button id="quiz-finish-btn" class="quiz-btn success" style="display: none;">Voir les résultats <i class="fas fa-chart-pie"></i></button>
                </div>
            </div>
        `;
        document.body.appendChild(this.modal);

        this.modal.querySelector('.quiz-close-btn').addEventListener('click', () => this.closeQuiz());
        this.modal.querySelector('#quiz-prev-btn').addEventListener('click', () => this.prevQuestion());
        this.modal.querySelector('#quiz-next-btn').addEventListener('click', () => this.nextQuestion());
        this.modal.querySelector('#quiz-finish-btn').addEventListener('click', () => this.showResults());
    }

    async fetchJson(url, options = {}, timeoutMs = this.quizLoadTimeoutMs) {
        const controller = new AbortController();
        const timeoutId = window.setTimeout(() => controller.abort(), timeoutMs);

        try {
            const response = await fetch(url, { ...options, signal: controller.signal });
            if (!response.ok) {
                const error = new Error(`HTTP ${response.status}`);
                error.status = response.status;
                throw error;
            }
            return await response.json();
        } catch (error) {
            if (error.name === 'AbortError') {
                const timeoutError = new Error('Request timed out');
                timeoutError.code = 'timeout';
                throw timeoutError;
            }
            throw error;
        } finally {
            window.clearTimeout(timeoutId);
        }
    }

    isTimeoutError(error) {
        return error && (error.code === 'timeout' || error.name === 'AbortError');
    }

    async startQuiz(chapterIdentifier, chapterTitle) {
        const sessionToken = ++this.quizSessionToken;
        this.chapterIdentifier = chapterIdentifier;
        this.chapterTitle = chapterTitle;
        this.currentQuestionIndex = 0;
        this.score = 0;
        this.conceptAnalysis = {};
        this.userAnswers = [];

        // Reset UI from potential results state
        const footer = this.modal.querySelector('.quiz-footer');
        if (footer) footer.style.display = 'flex';

        const progressText = this.modal.querySelector('.quiz-progress-text');
        if (progressText) {
            progressText.innerHTML = `Test - Question <span id="quiz-current-num">1</span> / <span id="quiz-total-num">--</span>`;
        }

        const progressFill = this.modal.querySelector('#quiz-progress-fill');
        if (progressFill) {
            progressFill.style.width = '0%';
            // Ensure the container is visible if it was hidden
            const barContainer = this.modal.querySelector('.quiz-progress-bar');
            if (barContainer) barContainer.style.display = 'block';
        }

        const body = this.modal.querySelector('#quiz-body');
        body.innerHTML = `<div class="quiz-loading"><i class="fas fa-circle-notch fa-spin"></i> Chargement du test...</div>`;
        this.modal.classList.add('active');

        try {
            const data = await this.fetchJson(`/api/quiz/${chapterIdentifier}`, {}, this.quizLoadTimeoutMs);
            if (sessionToken !== this.quizSessionToken) return;

            if (data.error) throw new Error(data.error);

            this.quizData = data.questions;
            if (this.quizData.length === 0) {
                body.innerHTML = `<div class="quiz-error">Aucune question disponible pour ce chapitre.</div>`;
                return;
            }

            // Initialize Analysis Trackers
            this.quizData.forEach(q => {
                if (!this.conceptAnalysis[q.concept]) {
                    this.conceptAnalysis[q.concept] = { total: 0, correct: 0 };
                }
                this.conceptAnalysis[q.concept].total += 1;
            });

            this.userAnswers = new Array(this.quizData.length).fill(null);

            this.modal.querySelector('#quiz-total-num').textContent = this.quizData.length;
            this.renderBubbles();
            this.renderQuestion();

        } catch (error) {
            if (sessionToken !== this.quizSessionToken) return;
            const message = this.isTimeoutError(error)
                ? 'Le quiz met trop de temps à se charger. Réessayez dans quelques secondes.'
                : `Erreur de chargement: ${error.message}`;
            body.innerHTML = `<div class="quiz-error">${message}</div>`;
        }
    }

    renderQuestion() {
        const q = this.quizData[this.currentQuestionIndex];
        const body = this.modal.querySelector('#quiz-body');
        const progressFill = this.modal.querySelector('#quiz-progress-fill');
        const nextBtn = this.modal.querySelector('#quiz-next-btn');
        const finishBtn = this.modal.querySelector('#quiz-finish-btn');

        // Update Progress
        const currentNum = this.modal.querySelector('#quiz-current-num');
        if (currentNum) currentNum.textContent = this.currentQuestionIndex + 1;

        if (progressFill) progressFill.style.width = `${((this.currentQuestionIndex) / this.quizData.length) * 100}%`;

        // Buttons state
        if (nextBtn) {
            nextBtn.style.display = this.currentQuestionIndex === this.quizData.length - 1 ? 'none' : 'inline-block';
            nextBtn.disabled = true;
        }
        if (finishBtn) {
            finishBtn.style.display = this.currentQuestionIndex === this.quizData.length - 1 ? 'inline-block' : 'none';
            finishBtn.disabled = true;
        }

        // Difficulty Badges
        const diffColors = {
            'Easy': '<span class="quiz-badge badge-easy">Facile</span>',
            'Medium': '<span class="quiz-badge badge-medium">Moyen</span>',
            'Hard': '<span class="quiz-badge badge-hard">Difficile</span>'
        };

        let choicesHtml = q.choices.map(c => `
            <button class="quiz-choice" data-id="${c.id}" data-correct="${c.is_correct}">
                <div class="quiz-choice-text">${this.escapeHtml(c.text)}</div>
                <div class="quiz-choice-icon"><i class="fas fa-circle"></i></div>
            </button>
        `).join('');

        body.innerHTML = `
            <div class="quiz-question-meta">
                ${diffColors[q.difficulty]}
                <span class="quiz-badge badge-concept">${q.concept}</span>
            </div>
            <h3 class="quiz-question-text">${this.escapeHtml(q.text)}</h3>
            <div class="quiz-choices-container">
                ${choicesHtml}
            </div>
            <div id="quiz-feedback" class="quiz-feedback" style="display: none;">
                <div class="quiz-feedback-icon"></div>
                <div class="quiz-feedback-content">
                    <h4 class="quiz-feedback-title"></h4>
                    <p class="quiz-feedback-expl">${this.escapeHtml(q.explanation)}</p>
                </div>
            </div>
        `;

        // Update Bubbles visual state to highlight current
        this.updateBubblesUI();

        const choiceBtns = body.querySelectorAll('.quiz-choice');
        const feedback = this.modal.querySelector('#quiz-feedback');

        // Check if already answered
        const previousAnswer = this.userAnswers[this.currentQuestionIndex];

        if (previousAnswer !== null) {
            // Reconstruct the answered state
            choiceBtns.forEach(btn => {
                btn.disabled = true;
                if (btn.dataset.id === String(previousAnswer.id)) {
                    if (previousAnswer.isCorrect) {
                        btn.classList.add('correct');
                        btn.querySelector('.quiz-choice-icon i').className = 'fas fa-check-circle';
                    } else {
                        btn.classList.add('wrong');
                        btn.querySelector('.quiz-choice-icon i').className = 'fas fa-times-circle';
                    }
                }
                // Highlight the correct one if they missed it
                if (!previousAnswer.isCorrect && btn.dataset.correct === 'true') {
                    btn.classList.add('correct-missed');
                    btn.querySelector('.quiz-choice-icon i').className = 'fas fa-check-circle';
                }
            });

            const fTitle = feedback.querySelector('.quiz-feedback-title');
            const fIcon = feedback.querySelector('.quiz-feedback-icon');
            if (previousAnswer.isCorrect) {
                feedback.className = 'quiz-feedback feedback-success';
                fIcon.innerHTML = '<i class="fas fa-check"></i>';
                fTitle.textContent = 'Excellente réponse !';
            } else {
                feedback.className = 'quiz-feedback feedback-error';
                fIcon.innerHTML = '<i class="fas fa-exclamation-triangle"></i>';
                fTitle.textContent = 'Incorrect';
            }
            feedback.style.display = 'flex';
        } else {
            // Bind Choices if not answered yet
            choiceBtns.forEach(btn => {
                btn.addEventListener('click', (e) => this.handleAnswer(e.currentTarget, choiceBtns, q));
            });
        }

        // Navigation state
        const prevBtn = this.modal.querySelector('#quiz-prev-btn');
        if (prevBtn) prevBtn.disabled = this.currentQuestionIndex === 0;

        if (this.currentQuestionIndex === this.quizData.length - 1) {
            if (nextBtn) nextBtn.style.display = 'none';
            if (finishBtn) finishBtn.style.display = 'inline-block';
            if (finishBtn) finishBtn.disabled = this.userAnswers.includes(null); // Must answer all
        } else {
            if (nextBtn) nextBtn.style.display = 'inline-block';
            if (finishBtn) finishBtn.style.display = 'none';
            if (nextBtn) nextBtn.disabled = false;
        }

        // Render markdown in code chunks if any
        this.formatCodeInQuiz(body);
    }

    handleAnswer(selectedBtn, allBtns, questionData) {
        // Disable all buttons to prevent double answers
        allBtns.forEach(b => b.disabled = true);

        const isCorrect = selectedBtn.dataset.correct === 'true';
        const feedback = this.modal.querySelector('#quiz-feedback');
        const fTitle = feedback.querySelector('.quiz-feedback-title');
        const fIcon = feedback.querySelector('.quiz-feedback-icon');

        if (isCorrect) {
            this.score++;
            this.conceptAnalysis[questionData.concept].correct++;
            selectedBtn.classList.add('correct');
            selectedBtn.querySelector('.quiz-choice-icon i').className = 'fas fa-check-circle';

            feedback.className = 'quiz-feedback feedback-success';
            fIcon.innerHTML = '<i class="fas fa-check"></i>';
            fTitle.textContent = 'Excellente réponse !';
        } else {
            selectedBtn.classList.add('wrong');
            selectedBtn.querySelector('.quiz-choice-icon i').className = 'fas fa-times-circle';

            // Highlight the correct one
            allBtns.forEach(b => {
                if (b.dataset.correct === 'true') {
                    b.classList.add('correct-missed');
                    b.querySelector('.quiz-choice-icon i').className = 'fas fa-check-circle';
                }
            });

            feedback.className = 'quiz-feedback feedback-error';
            fIcon.innerHTML = '<i class="fas fa-exclamation-triangle"></i>';
            fTitle.textContent = 'Incorrect';
        }

        feedback.style.display = 'flex';

        // Save the user answer
        this.userAnswers[this.currentQuestionIndex] = {
            id: selectedBtn.dataset.id,
            isCorrect: isCorrect
        };

        this.updateBubblesUI();

        // Enable Next/Finish btn if disabled
        if (this.currentQuestionIndex === this.quizData.length - 1) {
            this.modal.querySelector('#quiz-finish-btn').disabled = this.userAnswers.includes(null);
        }
    }

    renderBubbles() {
        const container = this.modal.querySelector('#quiz-bubbles');
        container.innerHTML = '';
        for (let i = 0; i < this.quizData.length; i++) {
            const bubble = document.createElement('div');
            bubble.className = 'quiz-bubble';
            bubble.dataset.index = i;
            // Let user click bubble to navigate
            bubble.addEventListener('click', () => {
                this.currentQuestionIndex = i;
                this.renderQuestion();
            });
            container.appendChild(bubble);
        }
    }

    updateBubblesUI() {
        const bubbles = this.modal.querySelectorAll('.quiz-bubble');
        bubbles.forEach((bubble, index) => {
            bubble.className = 'quiz-bubble'; // reset
            if (index === this.currentQuestionIndex) {
                bubble.classList.add('current');
            }
            if (this.userAnswers[index] !== null) {
                if (this.userAnswers[index].isCorrect) {
                    bubble.classList.add('correct-answer');
                } else {
                    bubble.classList.add('wrong-answer');
                }
            }
        });
    }

    prevQuestion() {
        if (this.currentQuestionIndex > 0) {
            this.currentQuestionIndex--;
            this.renderQuestion();
        }
    }

    nextQuestion() {
        if (this.currentQuestionIndex < this.quizData.length - 1) {
            this.currentQuestionIndex++;
            this.renderQuestion();
        }
    }

    async showResults() {
        const sessionToken = this.quizSessionToken;
        const questionResults = {};
        this.quizData.forEach((q, idx) => {
            questionResults[q.id] = this.userAnswers[idx] ? this.userAnswers[idx].isCorrect : false;
        });

        const percentage = Math.round((this.score / this.quizData.length) * 100);
        let message = '';
        let colorClass = '';

        if (percentage >= 80) {
            message = 'Félicitations ! Vous maîtrisez ce chapitre. 🏆';
            colorClass = 'res-excellent';
        } else if (percentage >= 50) {
            message = 'Bon travail ! Quelques petites révisions et ce sera parfait. 📚';
            colorClass = 'res-good';
        } else {
            message = 'Ne vous découragez pas. Relisez le cours attentivement et réessayez ! 💪';
            colorClass = 'res-needs-work';
        }

        const progressText = this.modal.querySelector('.quiz-progress-text');
        if (progressText) progressText.textContent = "Résultats";
        const progressFill = this.modal.querySelector('#quiz-progress-fill');
        if (progressFill) progressFill.style.width = '100%';
        const footer = this.modal.querySelector('.quiz-footer');
        if (footer) footer.style.display = 'none';

        this.renderResultsView({
            message,
            colorClass,
            percentile: null,
            showAuthPrompt: false,
            syncState: 'saving',
            syncMessage: 'Résultats prêts. Synchronisation en cours...'
        });

        this.persistQuizProgress(questionResults, {
            message,
            colorClass
        }, sessionToken);
    }

    renderResultsView({ message, colorClass, percentile = null, showAuthPrompt = false, syncState = 'saved', syncMessage = '' }) {
        const body = this.modal.querySelector('#quiz-body');
        if (!body) return;
        const safeChapterTitle = String(this.chapterTitle || '').replace(/'/g, "\\'");

        const analysisHtml = Object.keys(this.conceptAnalysis).map(concept => {
            const stat = this.conceptAnalysis[concept];
            const perc = Math.round((stat.correct / stat.total) * 100);
            return `
                <div class="analysis-row">
                    <div class="analysis-lbl">${concept}</div>
                    <div class="analysis-bar-bg">
                        <div class="analysis-bar-fill" style="width: ${perc}%; background: ${this.getColorForPerc(perc)}"></div>
                    </div>
                    <div class="analysis-val">${stat.correct}/${stat.total}</div>
                </div>
            `;
        }).join('');

        const percentileHtml = (percentile !== null && percentile !== undefined && percentile > 50)
            ? `<div class="quiz-percentile-msg" style="background:rgba(241,196,15,0.1); border:1px solid #f1c40f; padding:12px; border-radius:8px; margin:15px 0; color:#f1c40f; text-align:center;"><i class="fas fa-trophy"></i> Vous avez fait mieux que <strong>${Math.round(percentile)}%</strong> des autres étudiants !</div>`
            : '';

        let syncBannerHtml = '';
        if (syncState === 'saving') {
            syncBannerHtml = `<div class="quiz-percentile-msg" style="background:rgba(74,110,224,0.12); border:1px solid rgba(74,110,224,0.45); padding:12px; border-radius:8px; margin:15px 0; color:#8fb3ff; text-align:center;"><i class="fas fa-rotate fa-spin"></i> ${this.escapeHtml(syncMessage || 'Synchronisation en cours...')}</div>`;
        } else if (syncState === 'saved') {
            syncBannerHtml = `<div class="quiz-percentile-msg" style="background:rgba(46,164,78,0.12); border:1px solid rgba(46,164,78,0.45); padding:12px; border-radius:8px; margin:15px 0; color:#7ee787; text-align:center;"><i class="fas fa-check-circle"></i> ${this.escapeHtml(syncMessage || 'Progression sauvegardée.')}</div>`;
        } else if (syncState === 'guest') {
            syncBannerHtml = `<div class="quiz-percentile-msg" style="background:rgba(74,110,224,0.12); border:1px solid rgba(74,110,224,0.45); padding:12px; border-radius:8px; margin:15px 0; color:#8fb3ff; text-align:center;"><i class="fas fa-user-circle"></i> ${this.escapeHtml(syncMessage || 'Connectez-vous pour conserver vos résultats.')}</div>`;
        } else if (syncState === 'error') {
            syncBannerHtml = `<div class="quiz-percentile-msg" style="background:rgba(210,153,34,0.12); border:1px solid rgba(210,153,34,0.45); padding:12px; border-radius:8px; margin:15px 0; color:#f2cc60; text-align:center;"><i class="fas fa-triangle-exclamation"></i> ${this.escapeHtml(syncMessage || 'Les résultats sont affichés, mais la synchronisation a échoué.')}</div>`;
        }

        body.innerHTML = `
            <div class="quiz-results-container">
                <div class="quiz-score-circle ${colorClass}">
                    <span class="score-val">${this.score}</span>
                    <span class="score-max">/ ${this.quizData.length}</span>
                </div>
                <h2 class="quiz-res-msg">${message}</h2>
                ${syncBannerHtml}
                ${percentileHtml}
                
                <div class="quiz-analysis-box">
                    <h3>Analyse par concept</h3>
                    ${analysisHtml}
                </div>
                
                <div id="quiz-auth-prompt" style="display: ${showAuthPrompt ? 'block' : 'none'}; background: rgba(74, 110, 224, 0.1); border: 1px solid #4a6ee0; border-radius: 8px; padding: 15px; margin-top: 20px; text-align: center;">
                    <p style="margin-bottom: 10px; color: var(--text-color);">Rejoignez-nous pour sauvegarder vos progrès !</p>
                    <a href="/login" class="quiz-btn primary" style="text-decoration: none; display: inline-block; margin-right: 10px;">Se connecter</a>
                    <a href="/signup" class="quiz-btn outline" style="text-decoration: none; display: inline-block;">Créer un compte</a>
                </div>

                <div class="quiz-res-actions">
                    <button class="quiz-btn outline" onclick="window.quizController.startQuiz('${this.chapterIdentifier}', '${safeChapterTitle}')"><i class="fas fa-redo"></i> Refaire le test</button>
                    <button class="quiz-btn primary" onclick="window.quizController.closeQuiz()"><i class="fas fa-book"></i> Retourner au cours</button>
                </div>
            </div>
        `;
    }

    async persistQuizProgress(questionResults, resultsContext, sessionToken) {
        let isUserAuthenticated = false;
        let percentile = null;

        try {
            const backData = await this.fetchJson('/api/quiz/save_progress', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    chapter_identifier: this.chapterIdentifier,
                    score: this.score,
                    total: this.quizData.length,
                    details: {
                        conceptAnalysis: this.conceptAnalysis,
                        questionResults: questionResults
                    }
                })
            }, this.quizSaveTimeoutMs);

            if (sessionToken !== this.quizSessionToken) return;

            isUserAuthenticated = Boolean(backData.saved);
            percentile = backData.percentile;

            if (this.course && isUserAuthenticated) {
                await this.course.fetchUserProgress();
                this.course.renderOutline();
            }

            if (isUserAuthenticated) {
                localStorage.removeItem('algo_user_level_cache');
            }

            if (typeof window.checkNewBadges === 'function' && isUserAuthenticated) {
                window.checkNewBadges();
            }

            if (backData.level_up && backData.level && typeof Swal !== 'undefined') {
                const lvl = backData.level;
                const xpEarned = backData.xp_earned > 0 ? ` (+${backData.xp_earned} XP)` : '';

                await Swal.fire({
                    title: '🎉 Nouveau Niveau !',
                    html: `<div style="font-size:3rem; margin-bottom:10px;">${lvl.icon}</div>
                           <div style="font-size:1.3rem; font-weight:800; color:${lvl.color};">${lvl.name}</div>
                           <div style="margin-top:10px; color:#c9d1d9; font-size:0.9rem;">Vous avez gagné${xpEarned} et atteint le niveau <strong style="color:${lvl.color}">${lvl.name}</strong> !<br>Félicitations !</div>`,
                    background: '#161b22',
                    color: '#c9d1d9',
                    confirmButtonColor: lvl.color,
                    confirmButtonText: 'Super ! 🚀',
                    allowOutsideClick: false,
                    showClass: { popup: 'animate__animated animate__bounceIn' }
                });
            }

            if (sessionToken !== this.quizSessionToken) return;

            this.renderResultsView({
                ...resultsContext,
                percentile,
                showAuthPrompt: !isUserAuthenticated,
                syncState: isUserAuthenticated ? 'saved' : 'guest',
                syncMessage: isUserAuthenticated
                    ? 'Progression sauvegardée.'
                    : 'Connectez-vous pour conserver vos résultats.'
            });
        } catch (error) {
            if (sessionToken !== this.quizSessionToken) return;
            console.error("Failed to save progress", error);
            this.renderResultsView({
                ...resultsContext,
                percentile,
                showAuthPrompt: false,
                syncState: 'error',
                syncMessage: this.isTimeoutError(error)
                    ? 'Les résultats sont affichés, mais la synchronisation prend trop de temps.'
                    : 'Les résultats sont affichés, mais la sauvegarde n’a pas pu être confirmée.'
            });
        }
    }

    getColorForPerc(perc) {
        if (perc >= 80) return '#2ea44e';
        if (perc >= 50) return '#d29922';
        return '#f85149';
    }

    closeQuiz() {
        this.modal.classList.remove('active');
        setTimeout(() => this.modal.querySelector('.quiz-footer').style.display = 'flex', 300);
        // Refresh course if needed, or simply return visually
        if (this.course) {
            // Maybe reset scroll or do something
        }
    }

    escapeHtml(text) {
        return String(text)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    }

    formatCodeInQuiz(container) {
        // Quick hack to format backticks as code blocks inside quiz text/choices
        const elements = container.querySelectorAll('.quiz-question-text, .quiz-choice-text, .quiz-feedback-expl');
        elements.forEach(el => {
            let html = el.innerHTML;
            html = html.replace(/`(.*?)`/g, '<code class="quiz-inline-code">$1</code>');
            el.innerHTML = html;
        });
    }
}
