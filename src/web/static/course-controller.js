class CourseController {
    constructor() {
        this.courseData = null;
        this.userProgress = {};
        this.currentChapterIndex = 0;
        this.contentVersion = '26';
        this.isStandalonePage = !!document.getElementById('course-outline');
        this.requestTimeoutMs = 12000;
        this.progressTimeoutMs = 5000;
        this.chapterCache = new Map();
        this.chapterRenderToken = 0;

        this.sidebar = document.getElementById('course-outline');
        this.contentArea = document.getElementById('course-content');
        this.prevBtn = document.getElementById('course-prev-btn');
        this.nextBtn = document.getElementById('course-next-btn');
        this.paginationLabel = document.getElementById('course-pagination');

        this.setOutlineStatus('Chargement du sommaire...', true);
        this.setContentLoadingState('Chargement du cours...');

        // Initialize Quiz System
        if (typeof QuizController !== 'undefined') {
            this.quiz = new QuizController(this);
            window.quizController = this.quiz; // Export globally for HTML inline onclick
        }

        this.init();
    }

    async fetchJson(url, options = {}, timeoutMs = this.requestTimeoutMs) {
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

    setOutlineStatus(message, isLoading = false) {
        if (!this.sidebar) return;
        const iconClass = isLoading ? 'fas fa-circle-notch fa-spin' : 'fas fa-triangle-exclamation';
        this.sidebar.innerHTML = `
            <div class="course-state course-state-sidebar">
                <i class="${iconClass}"></i>
                <span>${this.escapeHtml(message)}</span>
            </div>
        `;
    }

    setContentLoadingState(message) {
        if (!this.contentArea) return;
        this.contentArea.innerHTML = `
            <div class="course-state course-state-loading">
                <i class="fas fa-circle-notch fa-spin"></i>
                <div>${this.escapeHtml(message)}</div>
            </div>
        `;
    }

    setContentErrorState(message) {
        if (!this.contentArea) return;
        this.contentArea.innerHTML = `
            <div class="course-state course-state-error">
                <i class="fas fa-triangle-exclamation"></i>
                <div>${this.escapeHtml(message)}</div>
            </div>
        `;
    }

    clampCurrentChapterIndex() {
        const totalChapters = (this.courseData && Array.isArray(this.courseData.chapters)) ? this.courseData.chapters.length : 0;
        if (totalChapters === 0) {
            this.currentChapterIndex = 0;
            return;
        }

        const parsedIndex = Number.parseInt(this.currentChapterIndex, 10);
        const safeIndex = Number.isFinite(parsedIndex) ? parsedIndex : 0;
        this.currentChapterIndex = Math.min(Math.max(safeIndex, 0), totalChapters - 1);
    }

    async init() {
        try {
            this.courseData = await this.fetchJson(`/api/course?v=${this.contentVersion}`);
            if (!this.courseData || !Array.isArray(this.courseData.chapters) || this.courseData.chapters.length === 0) {
                this.setOutlineStatus('Aucun chapitre publié pour le moment.');
                this.setContentErrorState('Le cours n’est pas encore disponible.');
                return;
            }

            this.loadState();
            this.clampCurrentChapterIndex();
            this.renderOutline();
            this.bindEvents();

            this.fetchUserProgress()
                .then(() => {
                    this.renderOutline();
                    this.updateChapterTopBar();
                })
                .catch((error) => {
                    console.error('Failed to refresh course progress:', error);
                });

            if (this.isStandalonePage) {
                await this.renderCurrentChapter();
            }
        } catch (error) {
            console.error("Failed to initialize course controller:", error);
            this.setOutlineStatus('Impossible de charger le sommaire.');
            this.setContentErrorState('Le cours est temporairement indisponible. Réessayez dans quelques instants.');
        }
    }

    async fetchUserProgress() {
        this.userProgress = {};
        try {
            const data = await this.fetchJson('/api/user/progress/summary', {}, this.progressTimeoutMs);
            if (data.success) {
                this.userProgress = data.progress.chapter_stats || {};
            }
        } catch (e) {
            if (e.status === 401) return;
            console.error("Failed to fetch user progress", e);
        }
    }

    bindEvents() {
        if (this.prevBtn) this.prevBtn.onclick = () => this.navigate(-1);
        if (this.nextBtn) this.nextBtn.onclick = () => this.navigate(1);

        window.onpopstate = (e) => {
            if (e.state && e.state.chapterIndex !== undefined) {
                this.currentChapterIndex = e.state.chapterIndex;
                this.renderCurrentChapter();
                this.updateOutlineActiveState();
            }
        };
    }

    navigate(direction) {
        const nextIndex = this.currentChapterIndex + direction;
        if (nextIndex >= 0 && nextIndex < this.courseData.chapters.length) {
            this.currentChapterIndex = nextIndex;
            this.saveState();
            this.renderCurrentChapter();
            this.updateOutlineActiveState();
        }
    }

    async renderOutline() {
        if (!this.sidebar) return;
        if (!this.courseData || !Array.isArray(this.courseData.chapters) || this.courseData.chapters.length === 0) {
            this.setOutlineStatus('Aucun chapitre disponible.');
            return;
        }
        this.sidebar.innerHTML = '';

        let earnedWeight = 0;
        const CHAPTER_WEIGHTS = {
            "intro": 1, "tableaux": 3, "chaines": 1, "allocation": 3,
            "actions": 2, "enregistrements": 2, "fichiers": 1,
            "listes_chainees": 2, "piles": 1, "files": 1
        };

        this.courseData.chapters.forEach((chapter, index) => {
            const item = document.createElement('div');
            item.className = 'outline-item' + (index === this.currentChapterIndex ? ' active' : '');

            let statusIcon = '';
            if (chapter.id && this.userProgress && this.userProgress[chapter.id]) {
                const stats = this.userProgress[chapter.id];
                if (stats.taken) {
                    const percent = (stats.score / stats.total) * 100;
                    let r, g, b;
                    if (percent < 50) {
                        const ratio = percent / 50;
                        r = Math.round(220 + (255 - 220) * ratio);
                        g = Math.round(53 + (193 - 53) * ratio);
                        b = Math.round(69 + (7 - 69) * ratio);
                    } else {
                        const ratio = (percent - 50) / 50;
                        r = Math.round(255 + (40 - 255) * ratio);
                        g = Math.round(193 + (167 - 193) * ratio);
                        b = Math.round(7 + (69 - 7) * ratio);
                    }
                    const color = `rgb(${r}, ${g}, ${b})`;

                    if (stats.all_correct) {
                        statusIcon = `<i class="fas fa-check-circle" style="color: ${color}; margin-left: auto;" title="Parfait"></i>`;
                    } else {
                        statusIcon = `<i class="fas fa-dot-circle" style="color: ${color}; margin-left: auto;" title="Partiel: ${stats.score}/${stats.total}"></i>`;
                    }

                    if (stats.total > 0) {
                        const weight = CHAPTER_WEIGHTS[chapter.id] || 0;
                        earnedWeight += (stats.score / stats.total) * weight;
                    }
                }
            }

            item.innerHTML = `<i class="${chapter.icon || 'fas fa-book'}"></i> <span>${chapter.title}</span> ${statusIcon}`;
            item.dataset.index = index;
            item.onclick = () => {
                this.currentChapterIndex = index;
                this.saveState();
                this.renderCurrentChapter();
                this.updateOutlineActiveState();
            };
            this.sidebar.appendChild(item);
        });

        const progressPercent = Math.min(100, Math.round((earnedWeight / 17) * 100));
        const progressContainer = document.createElement('div');
        progressContainer.className = 'user-progress-container';
        progressContainer.innerHTML = `
            <div style="margin-top: 30px; padding: 15px; background: var(--panel-bg); border-radius: 12px; border: 1px solid var(--course-line);">
                <div style="font-size: 0.9em; margin-bottom: 8px; font-weight: 600; color: var(--course-ink); display: flex; justify-content: space-between;">
                    <span><i class="fas fa-trophy" style="color: #f1c40f; margin-right: 5px;"></i> Progression</span>
                    <span style="color: var(--course-accent); font-weight: bold;">${progressPercent}%</span>
                </div>
                <div style="background: var(--course-line); border-radius: 8px; height: 10px; overflow: hidden; width: 100%;">
                    <div style="background: linear-gradient(90deg, #4a6ee0, #6ed68a); width: ${progressPercent}%; height: 100%; transition: width 1s ease-in-out; border-radius: 8px;"></div>
                </div>
            </div>
        `;
        this.sidebar.appendChild(progressContainer);
    }

    updateOutlineActiveState() {
        if (!this.sidebar) return;
        this.sidebar.querySelectorAll('.outline-item').forEach((item, index) => {
            item.classList.toggle('active', index === this.currentChapterIndex);
        });
    }

    async renderCurrentChapter() {
        if (!this.contentArea || !this.courseData) return;
        this.clampCurrentChapterIndex();

        const chapterInfo = this.courseData.chapters[this.currentChapterIndex];
        if (!chapterInfo) {
            this.setContentErrorState('Chapitre introuvable.');
            this.updateNavButtons();
            return;
        }

        const renderToken = ++this.chapterRenderToken;
        this.setContentLoadingState(`Chargement de "${chapterInfo.title}"...`);

        let chapter;
        try {
            chapter = await this.loadChapter(chapterInfo);
        } catch (error) {
            if (renderToken !== this.chapterRenderToken) return;
            console.error('Failed to render chapter:', error);
            const message = this.isTimeoutError(error)
                ? 'Le chapitre met trop de temps à se charger. Réessayez dans quelques secondes.'
                : 'Impossible de charger ce chapitre pour le moment.';
            this.setContentErrorState(message);
            this.updateNavButtons();
            return;
        }

        if (renderToken !== this.chapterRenderToken) return;

        this.contentArea.innerHTML = `
            <h1 class="course-h1">${this.escapeHtml(chapter.title)}</h1>
            ${this.createChapterTopQuizBar(chapterInfo)}
        `;

        if (chapter.sections) {
            let sectionIndex = 0;
            chapter.sections.forEach(section => {
                const sectionEl = document.createElement('section');
                sectionEl.className = 'course-section';

                if (section.title) {
                    sectionIndex += 1;
                    const h3 = document.createElement('h3');
                    h3.className = 'course-h3';
                    h3.innerHTML = `<span class="course-section-num">${sectionIndex}.</span> ${this.escapeHtml(section.title)}`;
                    sectionEl.appendChild(h3);
                }

                if (section.content) {
                    const contentDiv = document.createElement('div');
                    contentDiv.className = 'course-text';
                    contentDiv.innerHTML = this.formatContent(section.content);
                    sectionEl.appendChild(contentDiv);
                }

                if (section.code) {
                    const codeBlock = this.createCodeBlock(section.code);
                    sectionEl.appendChild(codeBlock);
                }

                this.contentArea.appendChild(sectionEl);
            });
        }

        this.bindSectionEvents();
        await this.validateRunnableSnippets();
        this.prefetchAdjacentChapters();

        // Restore scroll position
        const savedScroll = localStorage.getItem('algocompiler.scrollTop');
        if (savedScroll !== null) {
            this.contentArea.scrollTop = parseInt(savedScroll, 10);
            localStorage.removeItem('algocompiler.scrollTop');
        } else {
            this.contentArea.scrollTop = 0;
        }

        this.updateNavButtons();
    }

    createChapterTopQuizBar(chapterInfo) {
        if (!this.quiz || !chapterInfo.id || chapterInfo.id === 'tutorial') {
            return '';
        }

        const safeTitle = (chapterInfo.title || '').replace(/'/g, "\\'");
        const stats = (this.userProgress && this.userProgress[chapterInfo.id]) || null;
        const taken = !!(stats && stats.taken);
        const score = taken ? (stats.score || 0) : 0;
        const total = taken ? (stats.total || 0) : 0;
        const pct = total > 0 ? Math.round((score / total) * 100) : 0;
        const attempts = taken ? (stats.attempts_count || 1) : 0;
        const avgScore = taken && stats.avg_score !== undefined ? stats.avg_score : pct;
        const isPassed = !!(stats && stats.all_correct);

        let statusBadgeHtml = '';
        let scoreHtml = '';
        let buttonHtml = '';

        if (taken) {
            if (isPassed) {
                statusBadgeHtml = `
                    <span class="chapter-quiz-status-tag passed">
                        <i class="fas fa-check-circle"></i> Validé (${pct}%)
                    </span>
                `;
            } else {
                statusBadgeHtml = `
                    <span class="chapter-quiz-status-tag in-progress">
                        <i class="fas fa-exclamation-circle"></i> Non validé (${pct}%)
                    </span>
                `;
            }

            scoreHtml = `
                <div class="chapter-quiz-metric">
                    <span class="chapter-quiz-metric-label">Meilleur Score</span>
                    <span class="chapter-quiz-metric-value" style="color: ${isPassed ? '#10b981' : '#f59e0b'};">
                        <i class="fas fa-trophy"></i> ${score} / ${total}
                    </span>
                </div>
                <div class="chapter-quiz-metric">
                    <span class="chapter-quiz-metric-label">Moyenne & Tentatives</span>
                    <span class="chapter-quiz-metric-value">
                        <i class="fas fa-chart-line"></i> ${avgScore}% (${attempts} tent.)
                    </span>
                </div>
            `;

            buttonHtml = `
                <button class="course-quiz-btn top" onclick="window.quizController.startQuiz('${chapterInfo.id}', '${safeTitle}')" title="Refaire le quiz pour améliorer votre score">
                    <i class="fas fa-redo"></i> Refaire le Quiz
                </button>
            `;
        } else {
            statusBadgeHtml = `
                <span class="chapter-quiz-status-tag not-attempted">
                    <i class="fas fa-circle-notch"></i> Non évalué
                </span>
            `;

            scoreHtml = `
                <div class="chapter-quiz-metric">
                    <span class="chapter-quiz-metric-label">Évaluation</span>
                    <span class="chapter-quiz-metric-value" style="color: var(--course-muted);">
                        -- / --
                    </span>
                </div>
                <div class="chapter-quiz-metric">
                    <span class="chapter-quiz-metric-label">Récompense</span>
                    <span class="chapter-quiz-metric-value" style="color: #f59e0b;">
                        <i class="fas fa-bolt"></i> +15 XP à la validation (≥80%)
                    </span>
                </div>
            `;

            buttonHtml = `
                <button class="course-quiz-btn top" onclick="window.quizController.startQuiz('${chapterInfo.id}', '${safeTitle}')" title="Démarrer le quiz d'évaluation de ce chapitre">
                    <i class="fas fa-play"></i> Passer le Quiz
                </button>
            `;
        }

        return `
            <div class="chapter-quiz-top-bar" id="chapter-quiz-top-bar">
                <div class="chapter-quiz-top-left">
                    <div class="chapter-quiz-top-kicker">
                        <i class="fas fa-tasks"></i> Évaluation de Chapitre
                        ${statusBadgeHtml}
                    </div>
                    <div class="chapter-quiz-top-metrics">
                        ${scoreHtml}
                    </div>
                </div>
                <div class="chapter-quiz-top-action">
                    ${buttonHtml}
                </div>
            </div>
        `;
    }

    updateChapterTopBar() {
        const topBarContainer = document.getElementById('chapter-quiz-top-bar');
        if (!topBarContainer || !this.courseData || !this.courseData.chapters) return;
        const currentChapter = this.courseData.chapters[this.currentChapterIndex];
        if (!currentChapter) return;
        const newHtml = this.createChapterTopQuizBar(currentChapter);
        if (newHtml) {
            topBarContainer.outerHTML = newHtml;
        }
    }

    async loadChapter(chapterInfo) {
        const cacheKey = `${chapterInfo.id}:${this.contentVersion}`;
        if (this.chapterCache.has(cacheKey)) {
            return this.chapterCache.get(cacheKey);
        }

        const sep = chapterInfo.file.includes('?') ? '&' : '?';
        const chapter = await this.fetchJson(`${chapterInfo.file}${sep}v=${this.contentVersion}`);
        this.chapterCache.set(cacheKey, chapter);
        return chapter;
    }

    prefetchAdjacentChapters() {
        if (!this.courseData || !Array.isArray(this.courseData.chapters)) return;

        const indexesToPrefetch = [
            this.currentChapterIndex - 1,
            this.currentChapterIndex + 1
        ];

        indexesToPrefetch.forEach((index) => {
            const chapterInfo = this.courseData.chapters[index];
            if (!chapterInfo) return;
            const cacheKey = `${chapterInfo.id}:${this.contentVersion}`;
            if (this.chapterCache.has(cacheKey)) return;
            this.loadChapter(chapterInfo).catch(() => {
                // Prefetch failures should stay silent; the normal render path handles messaging.
            });
        });
    }

    updateNavButtons() {
        if (this.prevBtn) this.prevBtn.disabled = this.currentChapterIndex === 0;
        if (this.nextBtn) this.nextBtn.disabled = this.currentChapterIndex === this.courseData.chapters.length - 1;

        if (this.paginationLabel && this.courseData) {
            this.paginationLabel.textContent = `${this.currentChapterIndex + 1} / ${this.courseData.chapters.length}`;
        }
    }

    bindSectionEvents() {
        // Add listeners to "Executer" buttons
        this.contentArea.querySelectorAll('.course-exec-btn').forEach(btn => {
            btn.onclick = (e) => {
                const codeBlock = e.currentTarget.closest('.course-code-block').querySelector('.course-code-body');
                const code = codeBlock.dataset.rawCode || codeBlock.innerText;
                this.executeCode(code);
            };
        });

        // Add listeners to "Try in Editor" buttons (Exercises)
        this.contentArea.querySelectorAll('.course-try-btn, .course-solution-run').forEach(btn => {
            btn.onclick = (e) => {
                const rawCode = e.currentTarget.getAttribute('data-code') || '';
                const code = this.normalizeCodeForDisplay(this.decodeCourseCode(rawCode));
                this.executeCode(code, true);
            };
        });

        // Always keep exercise solution buttons actionable and clearly labeled.
        this.contentArea.querySelectorAll('.course-solution-run').forEach((btn) => {
            btn.disabled = false;
            btn.classList.remove('course-solution-run-disabled');
            btn.removeAttribute('title');
            btn.innerHTML = 'Executer code';
        });

        this.contentArea.querySelectorAll('.course-solution-code').forEach((pre) => {
            const normalized = this.normalizeCodeForDisplay(pre.textContent || '');
            pre.innerHTML = this.highlightAlgoCode(normalized);
        });
    }

    async validateRunnableSnippets() {
        const checks = [];

        this.contentArea.querySelectorAll('.course-exec-btn').forEach((btn) => {
            const blockWrap = btn.closest('.course-code-block');
            const codeBlock = blockWrap ? blockWrap.querySelector('.course-code-body') : null;
            const rawCode = codeBlock && codeBlock.dataset ? codeBlock.dataset.rawCode : null;
            const code = (rawCode || (codeBlock ? codeBlock.innerText : '') || '').trim();

            if (!this.isCompleteCourseCode(code)) {
                btn.remove();
                return;
            }

            checks.push(this.validateSnippet(btn, code, false));
        });

        // Do not disable exercise solution buttons.
        // User should always be able to send solution code to the editor.

        if (checks.length > 0) {
            await Promise.all(checks);
        }
    }

    async validateSnippet(button, code, isSolutionButton) {
        let timeoutId = null;
        try {
            const controller = new AbortController();
            timeoutId = window.setTimeout(() => controller.abort(), 8000);
            const response = await fetch('/api/validate_algo', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ code }),
                signal: controller.signal
            });

            if (!response.ok) {
                if (isSolutionButton) return;
                button.remove();
                return;
            }

            const data = await response.json();
            if (!data.ok) {
                if (isSolutionButton) return;
                button.remove();
            }
        } catch (error) {
            if (isSolutionButton) return;
            button.remove();
        } finally {
            if (timeoutId !== null) {
                window.clearTimeout(timeoutId);
            }
        }
    }

    normalizeCodeForDisplay(code) {
        let normalized = String(code || '').replace(/\r\n?/g, '\n');
        normalized = normalized
            .replace(/&#10;|&#x0A;|&#xA;/gi, '\n')
            .replace(/&#13;|&#x0D;|&#xD;/gi, '\n');

        // Some stored blocks may contain literal \n; convert for proper multi-line display.
        if (!normalized.includes('\n') && normalized.includes('\\n')) {
            normalized = normalized.replace(/\\n/g, '\n').replace(/\\t/g, '\t');
        }

        // Split merged statements such as ";Tantque", ";Cour->x :=", ";Fin.".
        normalized = normalized.replace(/;\s*(?=\S)/g, ';\n');

        // Secondary split pass for common pseudo-code tokens.
        normalized = normalized.replace(
            /;\s*(?=(Algorithme|Type|Var|Const|Debut|Procedure|Fonction|Tantque|Pour|Si|Sinon|Fin\s*Si|FinSi|Fin\s*Pour|FinPour|Fin\s*Tantque|Fin\s*TantQue|FinTantque|FinTantQue|Jusqua|Fin\.|[A-Za-z_][A-Za-z0-9_]*\s*:=))/gi,
            ';\n'
        );

        // Ensure block starters are on their own line when flattened after conditions.
        normalized = normalized
            .replace(/\b(Alors)(?!\s*\n)\s+/gi, '$1\n    ')
            .replace(/\b(Faire)(?!\s*\n)\s+/gi, '$1\n    ');

        // If still one line, perform stronger splitting.
        if (!normalized.includes('\n')) {
            normalized = normalized
                .replace(/;\s*/g, ';\n')
                .replace(/\s+(Algorithme|Type|Var|Const|Debut|Procedure|Fonction|Tantque|Pour|Si|Sinon|Fin|Jusqua)\b/g, '\n$1')
                .trim();
        }

        return normalized;
    }

    saveState() {
        if (!this.contentArea) return;
        localStorage.setItem('algocompiler.currentChapter', this.currentChapterIndex);
        localStorage.setItem('algocompiler.scrollTop', this.contentArea.scrollTop);
    }

    loadState() {
        const saved = localStorage.getItem('algocompiler.currentChapter');
        if (saved !== null) {
            const parsedIndex = parseInt(saved, 10);
            this.currentChapterIndex = Number.isFinite(parsedIndex) ? parsedIndex : 0;
        }
    }

    formatContent(text) {
        if (!text) return '';
        const escapeLabel = (value) => this.escapeHtml(value);
        const sanitizeLink = (value) => this.sanitizeLinkUrl(value);

        const calloutBlock = (label, css) => {
            const re = new RegExp(`\\[\\[${label}\\]\\]([\\s\\S]*?)(?:\\n\\s*\\n|$)`, 'g');
            return (input) => input.replace(re, (_, body) => {
                const content = String(body || '').trim();
                return `<div class="course-callout ${css}"><div class="course-callout-title">${label === 'DEF' ? 'Définition' : label === 'ALERT' ? 'Alerte' : label === 'NOTE' ? 'Note' : 'Fun Fact'}</div>${content ? `<div>${content}</div>` : ''}</div>\n\n`;
            });
        };

        let html = text;
        html = calloutBlock('DEF', 'course-callout-def')(html);
        html = calloutBlock('ALERT', 'course-callout-alert')(html);
        html = calloutBlock('NOTE', 'course-callout-note')(html);
        html = calloutBlock('FUN', 'course-callout-fun')(html);

        html = html
            .replace(/\[\[STYLISH_EX\]\]/g, '<div class="stylish-lesson-intro"><i class="fas fa-star"></i> Objectifs pédagogiques</div>\n\n')
            .replace(/```(?:[a-zA-Z0-9_-]+)?\n?([\s\S]*?)```/g, (match, code) => {
                const safeCode = escapeLabel(code.trim());
                return `<pre class="course-solution-code">${safeCode}</pre>\n\n`;
            })
            .replace(/^#### (.*?)$/gm, '<h5 class="course-h5">$1</h5>\n\n')
            .replace(/^### (.*?)$/gm, '<h4 class="course-h4">$1</h4>\n\n')
            .replace(/^## (.*?)$/gm, '<h3 class="course-h3">$1</h3>\n\n')
            .replace(/^# (.*?)$/gm, '<h2 class="course-h2">$1</h2>\n\n')
            .replace(/^[-*]{3,}$/gm, '<hr class="course-divider">\n\n')
            .replace(/\[([^\]]+)\]\(([^)]+)\)/g, (match, label, url) => {
                const safeUrl = sanitizeLink(url);
                const safeLabel = escapeLabel(label);
                if (this.isDemoLink(safeUrl)) {
                    return `<a class="course-demo-btn" href="${safeUrl}" target="_blank" rel="noopener"><span class="demo-glow"></span><i class="fas fa-play"></i> ${safeLabel}</a>`;
                }
                return `<a href="${safeUrl}" target="_blank" rel="noopener">${safeLabel}</a>`;
            })
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/`(.*?)`/g, '<code class="course-inline-code">$1</code>')
            .replace(/^[ \t]*[-*] (.*?)$/gm, '<li>$1</li>');

        if (html.includes('<li>')) {
            html = html.replace(/(?:<li>.*?<\/li>\s*)+/gs, '<ul>$&</ul>\n\n');
        }

        // Protect data-code attribute newlines from being flattened
        html = html.replace(/data-code="([^"]*)"/g, (match, p1) => {
            return 'data-code="' + p1.replace(/\n/g, '&#10;').replace(/\\n/g, '&#10;') + '"';
        });

        // Protect course-diagram and SVG blocks from double newline splitting
        html = html.replace(/<div class="course-diagram">[\s\S]*?<\/div>/g, (match) => {
            return match.replace(/\n\s*\n/g, '\n');
        });
        html = html.replace(/<svg[\s\S]*?<\/svg>/g, (match) => {
            return match.replace(/\n\s*\n/g, '\n');
        });

        return html.split(/\n\n+/).map(block => {
            const normalized = block.trim();
            if (!normalized) return '';
            if (/^<(div|section|article|h[1-6]|ul|ol|pre|table|hr|blockquote|svg|details|p|defs|g|path|rect|text|line|polygon)/i.test(normalized)) {
                return normalized;
            }
            return `<p>${normalized.replace(/\n/g, '<br>')}</p>`;
        }).join('\n\n');
    }

    sanitizeLinkUrl(rawUrl) {
        const url = String(rawUrl || '').trim();
        if (!url) return '#';
        if (/^(https?:\/\/|\/)/i.test(url)) return url;
        if (/^[\w\-./#?=&%]+$/.test(url)) return url;
        return '#';
    }

    isDemoLink(url) {
        return /(^\/?demo-course\/)|(^\/?democourse\/)/i.test(url);
    }

    createCodeBlock(code) {
        const div = document.createElement('div');
        div.className = 'course-code-block';

        const header = document.createElement('div');
        header.className = 'course-code-header';
        const canLoad = this.isCompleteCourseCode(code);
        header.innerHTML = `<span><i class="fas fa-terminal"></i> Exemple d'algorithme</span>` +
            (canLoad ? `<button class="course-exec-btn"><i class="fas fa-play"></i> Charger & Formater</button>` : '');

        const body = document.createElement('div');
        body.className = 'course-code-body';
        const normalizedCode = this.normalizeCodeForDisplay(code);
        body.dataset.rawCode = normalizedCode;
        body.innerHTML = this.highlightAlgoCode(normalizedCode);

        div.appendChild(header);
        div.appendChild(body);
        return div;
    }

    escapeHtml(text) {
        return String(text)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    }

    highlightAlgoCode(code) {
        if (!code) return '';
        let safe = String(code)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;');

        return safe
            .replace(/("(?:[^"\\]|\\.)*"|'(?:[^'\\]|\\.)*')/g, '<span class="algo-str">$1</span>')
            .replace(/\b(\d+(?:\.\d+)?)\b/g, '<span class="algo-num">$1</span>')
            .replace(/\b(Algorithme|Const|Var|Type|Enregistrement|Debut|Fin|Fonction|Procedure|Retourner|Si|Sinon|Alors|Fin Si|Pour|Fin Pour|Tantque|Fin Tantque|Repeter|Jusqua|Lire|Ecrire|Vrai|Faux|NIL|allouer|liberer|taille|Entier|Reel|Chaine|Caractere|Booleen|Tableau|De|Et|Ou|Non)\b/g, '<span class="algo-kw">$1</span>')
            .replace(/(\/\/.*)$/gm, '<span class="algo-cmt">$1</span>');
    }

    decodeCourseCode(rawCode) {
        return String(rawCode)
            .replace(/&#10;|&#x0A;|&#xA;/gi, '\n')
            .replace(/\\n/g, '\n')
            .replace(/\\t/g, '\t')
            .replace(/&lt;/g, '<')
            .replace(/&gt;/g, '>')
            .replace(/&amp;/g, '&')
            .replace(/&#39;/g, "'")
            .replace(/&quot;/g, '"');
    }

    isCompleteCourseCode(code) {
        const normalized = String(code || '').trim();
        if (!normalized) return false;
        if (!/\bDebut\b/i.test(normalized)) return false;
        if (!/\bFin\.\s*$/i.test(normalized)) return false;
        return true;
    }

    executeCode(code, fromExercise = false) {
        // Auto-wrap bare blocks with 'Algorithme' to ensure valid compilation in the IDE
        if (!/^\s*Algorithme\b/i.test(code)) {
            code = "Algorithme ExerciceAuto;\n" + code;
        }

        if (window.editor) {
            window.editor.setValue(code);
            if (typeof formatAlgoCode === 'function') {
                formatAlgoCode(window.editor);
            }
        } else {
            localStorage.setItem('algocompiler.pendingCourseCode', code);
            if (fromExercise) {
                localStorage.setItem('algocompiler.fromExercise', 'true');
            }
            // Save scroll position before leaving
            this.saveState();
            window.location.href = '/';
        }
    }
}

document.addEventListener('DOMContentLoaded', () => {
    window.courseController = new CourseController();
});
