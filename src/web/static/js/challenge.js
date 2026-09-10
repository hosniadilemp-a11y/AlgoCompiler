function escapeHtml(text) {
    return String(text !== null && text !== undefined ? text : '')
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

document.addEventListener('DOMContentLoaded', () => {
    // 1. Split Pane Logic
    const vSplitter = document.getElementById('vertical-splitter');
    const problemPane = document.querySelector('.problem-pane');
    const editorPane = document.querySelector('.editor-pane');

    let isVSplitResizing = false;

    if (vSplitter) {
        vSplitter.addEventListener('mousedown', (e) => {
            isVSplitResizing = true;
            vSplitter.classList.add('dragging');
            document.body.style.cursor = 'col-resize';
            e.preventDefault();
        });

        document.addEventListener('mousemove', (e) => {
            if (!isVSplitResizing) return;
            const containerWidth = document.querySelector('.challenge-layout').offsetWidth;
            let newWidth = (e.clientX / containerWidth) * 100;
            // constraints
            if (newWidth < 20) newWidth = 20;
            if (newWidth > 60) newWidth = 60;

            problemPane.style.width = `${newWidth}%`;
            editorPane.style.width = `calc(${100 - newWidth}% - 5px)`;
            if (window.editor) window.editor.refresh();
        });

        document.addEventListener('mouseup', () => {
            if (isVSplitResizing) {
                isVSplitResizing = false;
                vSplitter.classList.remove('dragging');
                document.body.style.cursor = '';
            }
        });
    }

    // Horizontal Split Pane (Editor / Bottom)
    const hSplitter = document.getElementById('horizontal-splitter');
    const editorWrapper = document.querySelector('.editor-wrapper');
    const bottomPane = document.querySelector('.bottom-pane');
    let isHSplitResizing = false;

    if (hSplitter) {
        hSplitter.addEventListener('mousedown', (e) => {
            isHSplitResizing = true;
            hSplitter.classList.add('dragging');
            document.body.style.cursor = 'row-resize';
            e.preventDefault();
        });

        document.addEventListener('mousemove', (e) => {
            if (!isHSplitResizing) return;
            const editorPaneHeight = editorPane.offsetHeight;
            const editorPaneTop = editorPane.getBoundingClientRect().top;

            let newTopHeight = e.clientY - editorPaneTop;
            let percentage = (newTopHeight / editorPaneHeight) * 100;

            // Constraints
            if (percentage < 30) percentage = 30;
            if (percentage > 85) percentage = 85;

            editorWrapper.style.height = `calc(${percentage}% - 5px)`;
            bottomPane.style.height = `${100 - percentage}%`;

            if (window.editor) window.editor.refresh();
        });

        document.addEventListener('mouseup', () => {
            if (isHSplitResizing) {
                isHSplitResizing = false;
                hSplitter.classList.remove('dragging');
                document.body.style.cursor = '';
            }
        });
    }

    // 2. Tabs Logic
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');

    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            // Remove active from all
            tabBtns.forEach(b => b.classList.remove('active'));
            tabContents.forEach(c => c.style.display = 'none');

            // Add active to clicked
            btn.classList.add('active');
            const target = document.getElementById(btn.getAttribute('data-target'));
            if (target) {
                if (target.id === 'tab-console') {
                    target.style.display = 'flex'; // Flex for split view
                } else {
                    target.style.display = 'block';
                }
            }
        });
    });

    // 3. Load Problem Data
    const problemId = Number(window.CURRENT_PROBLEM_ID);
    const titleEl = document.getElementById('problem-title');
    const topicEl = document.getElementById('problem-topic');
    const diffEl = document.getElementById('problem-difficulty');
    const descEl = document.getElementById('problem-description');
    const testsList = document.getElementById('test-cases-list');
    const testsTab = document.getElementById('tab-tests');
    const prevChallengeBtn = document.getElementById('prev-challenge-btn');
    const nextChallengeBtn = document.getElementById('next-challenge-btn');

    let currentProblem = null;
    const REQUEST_TIMEOUT_MS = {
        navigation: 8000,
        problemLoad: 20000,
        submissions: 60000,
        stdin: 30000
    };

    async function fetchWithTimeout(url, options = {}, timeoutMs = 15000) {
        const controller = new AbortController();
        const timeoutId = window.setTimeout(() => controller.abort(), timeoutMs);
        try {
            return await fetch(url, { ...options, signal: controller.signal });
        } finally {
            window.clearTimeout(timeoutId);
        }
    }

    function describeRequestError(error, timeoutMessage) {
        if (error && error.name === 'AbortError') {
            return timeoutMessage;
        }
        return (error && error.message) || 'Erreur de connexion';
    }


    function formatSingleError(err) {
        if (typeof err === 'string') return err;
        if (err == null) return '';
        if (typeof err === 'object') {
            const line = err.line != null ? `Ligne ${err.line}` : null;
            const col = err.column != null ? `Col ${err.column}` : null;
            const type = err.type ? String(err.type) : null;
            const prefix = [type, line, col].filter(Boolean).join(' | ');
            const message = err.message || err.error || JSON.stringify(err);
            return prefix ? `${prefix}: ${message}` : String(message);
        }
        return String(err);
    }

    function formatErrorDetails(details) {
        if (!details) return [];
        if (Array.isArray(details)) return details.map(formatSingleError).filter(Boolean);
        return [formatSingleError(details)];
    }

    function renderRunError(message, details = []) {
        if (!testsTab) return;
        let box = document.getElementById('run-error-box');
        if (!box) {
            box = document.createElement('div');
            box.id = 'run-error-box';
            box.style.margin = '10px 0';
            box.style.padding = '10px';
            box.style.border = '1px solid #dc3545';
            box.style.borderRadius = '6px';
            box.style.background = 'rgba(220,53,69,0.1)';
            box.style.color = '#ff6b6b';
            box.style.fontFamily = 'monospace';
            box.style.whiteSpace = 'pre-wrap';
            testsTab.insertBefore(box, testsList);
        }
        const detailsHtml = details.length
            ? `<br>${details.map(d => escapeHtml(d)).join('<br>')}`
            : '';
        box.innerHTML = `<strong>Erreur:</strong> ${escapeHtml(message || 'Erreur inconnue')}${detailsHtml}`;
    }

    function clearRunError() {
        const box = document.getElementById('run-error-box');
        if (box) box.remove();
    }

    function setChallengeNavState(btn, targetProblemId) {
        if (!btn) return;
        if (targetProblemId == null) {
            btn.href = '#';
            btn.setAttribute('aria-disabled', 'true');
            return;
        }
        btn.href = `/challenge/${targetProblemId}`;
        btn.setAttribute('aria-disabled', 'false');
    }

    let currentNextProblemId = null;
    let currentPrevProblemId = null;

    function getCookie(name) {
        const raw = document.cookie
            .split('; ')
            .find(row => row.startsWith(name + '='));
        return raw ? decodeURIComponent(raw.split('=')[1]) : '';
    }

    function setCookie(name, value, maxAgeSeconds) {
        document.cookie = `${name}=${encodeURIComponent(value)};path=/;max-age=${maxAgeSeconds};SameSite=Lax`;
    }

    function markProblemSolved(pId) {
        if (!pId) return;
        const current = getCookie('algo_solved_problems');
        const solved = new Set(
            current
                ? current.split(',').map(v => Number(v.trim())).filter(Number.isFinite)
                : []
        );
        solved.add(Number(pId));
        setCookie('algo_solved_problems', Array.from(solved).join(','), 60 * 60 * 24 * 365);
    }

    async function setupProblemNavigation() {
        try {
            const res = await fetchWithTimeout(
                '/api/problems/navigation',
                {},
                REQUEST_TIMEOUT_MS.navigation
            );
            const data = await res.json();
            if (!data.success || !Array.isArray(data.problem_ids)) {
                setChallengeNavState(prevChallengeBtn, null);
                setChallengeNavState(nextChallengeBtn, null);
                return;
            }

            const ids = data.problem_ids
                .map(id => Number(id))
                .filter(Number.isFinite)
                .sort((a, b) => a - b);

            const idx = ids.indexOf(problemId);
            currentPrevProblemId = idx > 0 ? ids[idx - 1] : null;
            currentNextProblemId = idx >= 0 && idx < ids.length - 1 ? ids[idx + 1] : null;

            setChallengeNavState(prevChallengeBtn, currentPrevProblemId);
            setChallengeNavState(nextChallengeBtn, currentNextProblemId);
        } catch (e) {
            setChallengeNavState(prevChallengeBtn, null);
            setChallengeNavState(nextChallengeBtn, null);
        }
    }

    async function loadProblem() {
        try {
            const res = await fetchWithTimeout(
                `/api/problems/${problemId}`,
                {},
                REQUEST_TIMEOUT_MS.problemLoad
            );
            const data = await res.json();

            if (data.success) {
                currentProblem = data.problem;
                titleEl.textContent = currentProblem.title;
                topicEl.textContent = currentProblem.topic;
                diffEl.textContent = translateDifficulty(currentProblem.difficulty);
                diffEl.className = `difficulty-badge difficulty-${currentProblem.difficulty}`;

                // Render markdown
                descEl.innerHTML = marked.parse(currentProblem.description);

                // Render LaTeX math formulas
                const renderLatex = (attempts = 0) => {
                    if (window.renderMathInElement) {
                        try {
                            window.renderMathInElement(descEl, {
                                delimiters: [
                                    { left: '$$', right: '$$', display: true },
                                    { left: '$', right: '$', display: false },
                                    { left: '\\(', right: '\\)', display: false },
                                    { left: '\\[', right: '\\]', display: true }
                                ],
                                throwOnError: false
                            });
                        } catch (e) {
                            console.warn('KaTeX render warning:', e);
                        }
                    } else if (attempts < 10) {
                        setTimeout(() => renderLatex(attempts + 1), 100);
                    }
                };
                renderLatex();

                // Render public test cases 
                renderTestCases(currentProblem.test_cases);

                // Initialize CodeMirror 
                setTimeout(() => {
                    const codeEditor = document.getElementById('code-editor');
                    if (!window.editor && codeEditor) {
                        window.editor = CodeMirror.fromTextArea(codeEditor, {
                            mode: "algo",
                            theme: document.body.classList.contains('light-theme') ? 'default' : 'dracula',
                            lineNumbers: true,
                            indentUnit: 4,
                            smartIndent: true,
                            styleActiveLine: true,
                            matchBrackets: true,
                            autoCloseBrackets: true,
                            extraKeys: {
                                "Ctrl-Space": "autocomplete"
                            },
                            hintOptions: {
                                hint: (CodeMirror.hint && CodeMirror.hint.algo) || (CodeMirror.helpers && CodeMirror.helpers.hint && CodeMirror.helpers.hint.algo) || CodeMirror.hint.anyword,
                                completeSingle: false,
                                alignWithWord: true,
                                closeOnUnfocus: true
                            }
                        });
                        window.editor.setSize("100%", "100%");

                        // Keep editor theme in sync when user toggles light/dark mode.
                        function applyEditorThemeFromBody() {
                            const isLight = document.body.classList.contains('light-theme');
                            window.editor.setOption('theme', isLight ? 'default' : 'dracula');
                        }
                        applyEditorThemeFromBody();
                        window.addEventListener('themechange', applyEditorThemeFromBody);

                        if (typeof window.initEditorUI === 'function') {
                            window.initEditorUI();
                        }

                        // Auto-trigger autocomplete after typing
                        let typingTimer;
                        window.editor.on("inputRead", function (cm, change) {
                            if (change.text[0].match(/[\w]/)) {
                                clearTimeout(typingTimer);
                                typingTimer = setTimeout(function () {
                                    var cursor = cm.getCursor();
                                    var token = cm.getTokenAt(cursor);
                                    if (token.string.length >= 2) {
                                        const hfn = (CodeMirror.hint && CodeMirror.hint.algo) || (CodeMirror.helpers && CodeMirror.helpers.hint && CodeMirror.helpers.hint.algo);
                                        if (hfn) {
                                            cm.showHint({ hint: hfn });
                                        }
                                    }
                                }, 300);
                            }
                        });

                        // Smart Block Auto-Closing and Semicolon insertion on Enter
                        window.editor.addKeyMap({
                            "Enter": function (cm) {
                                if (cm.getOption("disableInput")) return CodeMirror.Pass;
                                const cursor = cm.getCursor();
                                const line = cm.getLine(cursor.line);
                                const lineTextUntilCursor = line.slice(0, cursor.ch);
                                const textBefore = lineTextUntilCursor.trim();

                                // 1. Smart Block Auto-Closing (Parity with AlgoExamination)
                                if (!lineTextUntilCursor.includes('//') && ((lineTextUntilCursor.match(/"/g) || []).length % 2 === 0)) {
                                    let closer = '';
                                    let openerRegex = null;
                                    let closerRegex = null;

                                    if (/(^|\s)alors$/i.test(textBefore)) {
                                        closer = 'FinSi;';
                                        openerRegex = /\bSi\b/gi;
                                        closerRegex = /\bFinSi\b/gi;
                                    } else if (/(^|\s)faire$/i.test(textBefore)) {
                                        if (/pour/i.test(textBefore) || /pour\b/i.test(lineTextUntilCursor)) {
                                            closer = 'FinPour;';
                                            openerRegex = /\bPour\b/gi;
                                            closerRegex = /\bFinPour\b/gi;
                                        } else {
                                            closer = 'FinTantQue;';
                                            openerRegex = /\bTantQue\b/gi;
                                            closerRegex = /\bFinTantQue\b/gi;
                                        }
                                    } else if (/^repeter$/i.test(textBefore)) {
                                        closer = "Jusqu'a (condition);";
                                        openerRegex = /\bRepeter\b/gi;
                                        closerRegex = /\bJusqu'a\b/gi;
                                    }

                                    if (closer) {
                                        const totalLines = cm.lineCount();
                                        let textAfterCursor = line.slice(cursor.ch) + "\n";
                                        for (let i = cursor.line + 1; i < totalLines; i++) {
                                            textAfterCursor += cm.getLine(i) + "\n";
                                        }
                                        const openersAfter = (textAfterCursor.match(openerRegex) || []).length;
                                        const closersAfter = (textAfterCursor.match(closerRegex) || []).length;

                                        if (closersAfter <= openersAfter) {
                                            const indentMatch = line.match(/^\s*/);
                                            const baseIndent = indentMatch ? indentMatch[0] : '';
                                            const innerIndent = baseIndent + '    ';
                                            const insertText = '\n' + innerIndent + '\n' + baseIndent + closer;
                                            cm.replaceRange(insertText, cursor);
                                            cm.setCursor({ line: cursor.line + 1, ch: innerIndent.length });
                                            return;
                                        }
                                    }
                                }

                                // 2. Semicolon auto-insertion logic for normal statements
                                const trimmedLine = line.trim();
                                if (trimmedLine.length > 0 &&
                                    !trimmedLine.startsWith("//") &&
                                    !/[;:\.\,\{\[\(\^]$/.test(trimmedLine) &&
                                    !/^(Algorithme|Var|Const|Debut|Alors|Faire|Sinon|Repeter|Type|Enregistrement|Fin|FinSi|FinPour|FinTantQue)/i.test(trimmedLine) &&
                                    !/\s+(Alors|Faire)$/i.test(trimmedLine)
                                ) {
                                    const lastCharIdx = line.search(/\S\s*$/);
                                    if (cursor.ch > lastCharIdx) {
                                        cm.replaceRange(";", { line: cursor.line, ch: line.length });
                                    }
                                }
                                return CodeMirror.Pass;
                            }
                        });
                    }
                    if (window.editor && !window.editor.getValue().trim()) {
                        window.editor.setValue(currentProblem.template_code);
                        applyTemplateProtection(window.editor);
                    } else if (window.editor) {
                        applyTemplateProtection(window.editor);
                    }
                }, 100);

            } else {
                descEl.innerHTML = `<p class="error-msg">Erreur: ${data.error}</p>`;
            }
        } catch (e) {
            descEl.innerHTML = `<p class="error-msg">${escapeHtml(describeRequestError(e, 'Le chargement du problème a pris trop de temps. Réessayez.'))}</p>`;
        }
    }

    let protectedMarks = [];

    function applyTemplateProtection(cm) {
        if (!cm) return;

        protectedMarks.forEach(m => {
            try { m.clear(); } catch (e) { }
        });
        protectedMarks = [];

        // Clear previous protected line background classes
        const totalLinesCount = cm.lineCount();
        for (let i = 0; i < totalLinesCount; i++) {
            cm.removeLineClass(i, 'background', 'cm-protected-line-bg');
        }

        const text = cm.getValue();
        const lines = text.split('\n');

        // 1. Find solution marker line
        let solutionMarkerIdx = -1;
        for (let i = 0; i < lines.length; i++) {
            const l = lines[i].toLowerCase();
            if (l.includes('// solution ici') || l.includes('// todo') || l.includes('// ecrire votre') || l.includes('// s <-')) {
                solutionMarkerIdx = i;
                break;
            }
        }

        // Fallback: If no comment marker, find the last Lire(...) before output/Fin
        if (solutionMarkerIdx === -1) {
            for (let i = 0; i < lines.length; i++) {
                if (/^\s*Lire\s*\(/i.test(lines[i])) {
                    solutionMarkerIdx = i;
                }
            }
        }

        if (solutionMarkerIdx === -1) return;

        // 2. Find footer start line (Ecrire, output loop, or Fin.)
        let footerStartIdx = -1;
        for (let i = lines.length - 1; i > solutionMarkerIdx; i--) {
            const trimmed = lines[i].trim();
            if (/^(Ecrire|Pour\b.*Ecrire|Fin\.)/i.test(trimmed) || trimmed === 'Fin.' || trimmed.startsWith('Pour ') || trimmed.startsWith('FinPour')) {
                footerStartIdx = i;
            } else if (trimmed !== '') {
                break;
            }
        }

        if (footerStartIdx === -1) {
            for (let i = lines.length - 1; i > solutionMarkerIdx; i--) {
                if (lines[i].trim().toLowerCase() === 'fin.') {
                    footerStartIdx = i;
                    break;
                }
            }
        }

        if (footerStartIdx === -1) {
            footerStartIdx = lines.length - 1;
        }

        // Ensure at least 1 editable line exists
        if (footerStartIdx <= solutionMarkerIdx + 1) {
            cm.replaceRange("\n    \n", { line: solutionMarkerIdx, ch: lines[solutionMarkerIdx].length });
            applyTemplateProtection(cm);
            return;
        }

        // 3. Mark Top Section as readOnly (inclusive of the marker line)
        try {
            const topMark = cm.markText(
                { line: 0, ch: 0 },
                { line: solutionMarkerIdx + 1, ch: 0 },
                {
                    readOnly: true,
                    atomic: true,
                    className: 'cm-protected-line',
                    inclusiveLeft: true,
                    inclusiveRight: false
                }
            );
            protectedMarks.push(topMark);
            for (let i = 0; i <= solutionMarkerIdx; i++) {
                cm.addLineClass(i, 'background', 'cm-protected-line-bg');
            }
        } catch (e) {
            console.warn("Could not mark top section:", e);
        }

        // 4. Mark Bottom Section as readOnly (from footer start to end)
        try {
            const lastLine = lines.length - 1;
            const lastCh = lines[lastLine].length;
            const bottomMark = cm.markText(
                { line: footerStartIdx, ch: 0 },
                { line: lastLine, ch: lastCh },
                {
                    readOnly: true,
                    atomic: true,
                    className: 'cm-protected-line',
                    inclusiveLeft: false,
                    inclusiveRight: true
                }
            );
            protectedMarks.push(bottomMark);
            for (let i = footerStartIdx; i <= lastLine; i++) {
                cm.addLineClass(i, 'background', 'cm-protected-line-bg');
            }
        } catch (e) {
            console.warn("Could not mark bottom section:", e);
        }

        // Position cursor inside the editable solution zone if currently outside
        const cur = cm.getCursor();
        if (cur.line <= solutionMarkerIdx || cur.line >= footerStartIdx) {
            cm.setCursor({ line: solutionMarkerIdx + 1, ch: 4 });
        }
    }


    const resetTemplateBtn = document.getElementById('reset-template-btn');
    if (resetTemplateBtn) {
        resetTemplateBtn.addEventListener('click', () => {
            if (!window.editor || !currentProblem || !currentProblem.template_code) return;
            if (typeof Swal !== 'undefined') {
                Swal.fire({
                    title: 'Réinitialiser le code ?',
                    text: 'Votre code actuel sera remplacé par le modèle initial.',
                    icon: 'warning',
                    showCancelButton: true,
                    confirmButtonText: 'Oui, réinitialiser',
                    cancelButtonText: 'Annuler',
                    confirmButtonColor: '#2563eb',
                    background: document.body.classList.contains('light-theme') ? '#ffffff' : '#161b22',
                    color: document.body.classList.contains('light-theme') ? '#24292f' : '#c9d1d9'
                }).then((result) => {
                    if (result.isConfirmed) {
                        window.editor.setValue(currentProblem.template_code);
                        applyTemplateProtection(window.editor);
                    }
                });
            } else {
                if (confirm('Réinitialiser le code au modèle initial ?')) {
                    window.editor.setValue(currentProblem.template_code);
                    applyTemplateProtection(window.editor);
                }
            }
        });
    }

    const formatBtn = document.getElementById('format-btn');
    if (formatBtn) {
        formatBtn.addEventListener('click', () => {
            setTimeout(() => {
                if (window.editor) {
                    applyTemplateProtection(window.editor);
                }
            }, 80);
        });
    }

    function renderTestCases(tests) {
        if (!tests || tests.length === 0) {
            testsList.innerHTML = '<p>Aucun cas de test public disponible.</p>';
            return;
        }

        testsList.innerHTML = tests.map((tc, idx) => `
            <div class="test-case-card">
                <h4>Cas de test #${idx + 1}</h4>
                <strong>Entrée :</strong>
                <div class="io-block">${tc.input || '(Vide)'}</div>
                <strong>Sortie Attendue :</strong>
                <div class="io-block">${tc.expected_output || '(Vide)'}</div>
            </div>
        `).join('');
    }

    function translateDifficulty(diff) {
        switch (diff) {
            case 'Easy': return 'Facile';
            case 'Medium': return 'Moyen';
            case 'Hard': return 'Difficile';
            default: return diff;
        }
    }

    loadProblem();
    setupProblemNavigation();

    // 4. Execution Logic (Run Tests vs Submit vs Stdin)
    const runTestsBtn = document.getElementById('run-tests-btn');
    const submitBtn = document.getElementById('submit-btn');
    const runStdinBtn = document.getElementById('run-stdin-btn');

    async function executeCode(executeAll) {
        if (!window.editor) return;

        const code = window.editor.getValue();

        let originalRunBtnText = '';
        if (executeAll) {
            originalRunBtnText = submitBtn.innerHTML;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Soumission...';
            submitBtn.disabled = true;
        } else {
            originalRunBtnText = runTestsBtn.innerHTML;
            runTestsBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Exécution...';
            runTestsBtn.disabled = true;
            document.querySelector('[data-target="tab-tests"]').click();
        }

        try {
            const res = await fetchWithTimeout('/api/submissions', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    problem_id: problemId,
                    code: code,
                    execute_all: executeAll,
                    time_taken_seconds: window.challengeTimerSeconds || 0
                })
            }, REQUEST_TIMEOUT_MS.submissions);

            const data = await res.json();

            data.problem_id = problemId;

            if (executeAll) {
                localStorage.removeItem('algo_user_level_cache');

                if (data.success) {
                    clearRunError();
                    renderTestResultsInContext(data);

                    if (data.all_passed) {
                        markProblemSolved(problemId);
                        if (typeof window.launchConfetti === 'function') {
                            window.launchConfetti();
                        }
                    }

                    showSubmissionResultsModal(data);
                } else {
                    renderRunError(data.error || 'Erreur de soumission', formatErrorDetails(data.details));
                }
            } else {
                if (data.success) {
                    clearRunError();
                    renderTestResultsInContext(data);
                    if (data.all_passed && typeof window.launchConfetti === 'function') {
                        window.launchConfetti();
                    }
                } else {
                    renderRunError(data.error || 'Erreur d’exécution', formatErrorDetails(data.details));
                }
            }
        } catch (e) {
            renderRunError(
                'Erreur de connexion',
                [describeRequestError(e, 'La soumission a pris trop de temps. Le serveur est probablement occupé, réessayez dans quelques secondes.')]
            );
        } finally {
            if (executeAll) {
                submitBtn.innerHTML = originalRunBtnText;
                submitBtn.disabled = false;
            } else {
                runTestsBtn.innerHTML = originalRunBtnText;
                runTestsBtn.disabled = false;
            }
        }
    }

    function showSubmissionResultsModal(data) {
        const isLight = document.body.classList.contains('light-theme');
        const passedCount = data.results ? data.results.filter(r => r.passed).length : 0;
        const totalCount = data.results ? data.results.length : 0;
        const allPassed = !!data.all_passed;

        const solveTime = (data.time_taken_seconds !== null && data.time_taken_seconds !== undefined)
            ? `${data.time_taken_seconds}s`
            : '-';
        const avgExec = (data.avg_execution_time_ms !== null && data.avg_execution_time_ms !== undefined)
            ? `${Number(data.avg_execution_time_ms).toFixed(2)} ms`
            : '-';
        const avgMem = (data.avg_memory_kb !== null && data.avg_memory_kb !== undefined)
            ? `${Number(data.avg_memory_kb).toFixed(0)} KB`
            : '-';

        const statusTitle = allPassed ? 'Solution Acceptée !' : 'Certains tests ont échoué';
        const statusIcon = allPassed
            ? '<div style="font-size: 3.2rem; color: #10b981; margin-bottom: 8px;"><i class="fas fa-check-circle"></i></div>'
            : '<div style="font-size: 3.2rem; color: #ef4444; margin-bottom: 8px;"><i class="fas fa-times-circle"></i></div>';
        const statusSub = allPassed
            ? 'Félicitations ! Votre algorithme a validé avec succès l’ensemble des cas de test.'
            : `Votre code a passé ${passedCount} sur ${totalCount} cas de test. Examinez les cas non validés et réessayez.`;

        let levelUpHtml = '';
        if (data.level_up && data.new_level) {
            const lvl = data.new_level;
            const xpEarned = data.xp_earned > 0 ? `+${data.xp_earned} XP` : '';
            levelUpHtml = `
                <div style="background: rgba(255, 193, 7, 0.15); border: 1px solid #ffc107; border-radius: 8px; padding: 10px; margin-bottom: 14px; text-align: center;">
                    <span style="font-size: 1.3rem;">${lvl.icon}</span>
                    <strong style="color: #ffc107; margin-left: 6px;">Nouveau Niveau : ${escapeHtml(lvl.name)} !</strong>
                    ${xpEarned ? `<span style="display:inline-block; background:#ffc107; color:#000; font-weight:bold; padding:2px 8px; border-radius:12px; font-size:0.75rem; margin-left:8px;">${xpEarned}</span>` : ''}
                </div>
            `;
        }

        const nextBtnLabel = currentNextProblemId
            ? 'Problème suivant <i class="fas fa-arrow-right" style="margin-left:6px;"></i>'
            : 'Tous les problèmes <i class="fas fa-list" style="margin-left:6px;"></i>';
        const nextBtnHref = currentNextProblemId ? `/challenge/${currentNextProblemId}` : '/problems';

        const modalHtml = `
            <div style="text-align: center; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
                ${statusIcon}
                <h2 style="margin: 0 0 6px 0; font-size: 1.45rem; font-weight: 700; color: ${allPassed ? (isLight ? '#065f46' : '#34d399') : (isLight ? '#991b1b' : '#f87171')};">
                    ${statusTitle}
                </h2>
                <p style="margin: 0 0 16px 0; font-size: 0.92rem; color: ${isLight ? '#4b5563' : '#9ca3af'}; line-height: 1.4;">
                    ${statusSub}
                </p>

                ${levelUpHtml}

                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 20px; text-align: left;">
                    <div style="background: ${isLight ? '#f3f4f6' : '#21262d'}; border: 1px solid ${isLight ? '#e5e7eb' : '#30363d'}; border-radius: 8px; padding: 10px 12px;">
                        <div style="font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.05em; color: ${isLight ? '#6b7280' : '#8b949e'}; margin-bottom: 3px;">Tests validés</div>
                        <div style="font-size: 1.15rem; font-weight: 700; color: ${allPassed ? '#10b981' : (passedCount > 0 ? '#f59e0b' : '#ef4444')};">
                            ${passedCount} / ${totalCount}
                        </div>
                    </div>

                    <div style="background: ${isLight ? '#f3f4f6' : '#21262d'}; border: 1px solid ${isLight ? '#e5e7eb' : '#30363d'}; border-radius: 8px; padding: 10px 12px;">
                        <div style="font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.05em; color: ${isLight ? '#6b7280' : '#8b949e'}; margin-bottom: 3px;">Temps de résolution</div>
                        <div style="font-size: 1.15rem; font-weight: 700; color: ${isLight ? '#111827' : '#f0f6fc'};">
                            ${solveTime}
                        </div>
                    </div>

                    <div style="background: ${isLight ? '#f3f4f6' : '#21262d'}; border: 1px solid ${isLight ? '#e5e7eb' : '#30363d'}; border-radius: 8px; padding: 10px 12px;">
                        <div style="font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.05em; color: ${isLight ? '#6b7280' : '#8b949e'}; margin-bottom: 3px;">Exécution moyenne</div>
                        <div style="font-size: 1.15rem; font-weight: 700; color: ${isLight ? '#111827' : '#f0f6fc'};">
                            ${avgExec}
                        </div>
                    </div>

                    <div style="background: ${isLight ? '#f3f4f6' : '#21262d'}; border: 1px solid ${isLight ? '#e5e7eb' : '#30363d'}; border-radius: 8px; padding: 10px 12px;">
                        <div style="font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.05em; color: ${isLight ? '#6b7280' : '#8b949e'}; margin-bottom: 3px;">Mémoire moyenne</div>
                        <div style="font-size: 1.15rem; font-weight: 700; color: ${isLight ? '#111827' : '#f0f6fc'};">
                            ${avgMem}
                        </div>
                    </div>
                </div>

                <div style="display: flex; gap: 10px; justify-content: center; align-items: center;">
                    <button id="modal-redo-btn" style="flex: 1; padding: 10px 16px; border-radius: 6px; border: 1px solid ${isLight ? '#d1d5db' : '#30363d'}; background: ${isLight ? '#ffffff' : '#21262d'}; color: ${isLight ? '#374151' : '#c9d1d9'}; font-weight: 600; font-size: 0.9rem; cursor: pointer; display: inline-flex; align-items: center; justify-content: center; gap: 6px; transition: all 0.2s;">
                        <i class="fas fa-redo"></i> Refaire le problème
                    </button>
                    <a id="modal-next-btn" href="${nextBtnHref}" style="flex: 1; text-decoration: none; padding: 10px 16px; border-radius: 6px; border: none; background: #2563eb; color: #ffffff; font-weight: 600; font-size: 0.9rem; cursor: pointer; display: inline-flex; align-items: center; justify-content: center; gap: 6px; transition: all 0.2s;">
                        ${nextBtnLabel}
                    </a>
                </div>
                ${data.leaderboard_url ? `
                    <div style="margin-top: 14px;">
                        <a href="${data.leaderboard_url}" target="_blank" style="font-size: 0.82rem; color: #3b82f6; text-decoration: underline; display: inline-flex; align-items: center; gap: 4px;">
                            <i class="fas fa-trophy"></i> Voir le classement du problème
                        </a>
                    </div>
                ` : ''}
            </div>
        `;

        if (typeof Swal !== 'undefined') {
            Swal.fire({
                html: modalHtml,
                showConfirmButton: false,
                showCloseButton: true,
                background: isLight ? '#ffffff' : '#161b22',
                color: isLight ? '#1f2937' : '#c9d1d9',
                width: '460px',
                padding: '24px 20px',
                customClass: {
                    popup: 'algo-submission-modal'
                },
                didOpen: () => {
                    const redoBtn = document.getElementById('modal-redo-btn');
                    if (redoBtn) {
                        redoBtn.addEventListener('click', () => {
                            Swal.close();
                            if (window.editor) {
                                window.editor.focus();
                            }
                        });
                    }
                }
            });
        }
    }

    function renderTestResultsInContext(data) {
        if (!data.results || !testsList) return;

        const tcCards = document.querySelectorAll('.test-case-card');

        // If results include hidden tests (more than public cards), render all test cases
        if (data.results.length > tcCards.length) {
            testsList.innerHTML = data.results.map((r, i) => {
                const isHidden = (r.input === undefined || r.input === null || r.input === '') &&
                                 (r.expected_output === undefined || r.expected_output === null || r.expected_output === '');
                const cardTitle = isHidden ? `Cas de test #${i + 1} <span style="font-size:0.75em; opacity:0.7; font-weight:normal;">(Caché)</span>` : `Cas de test #${i + 1}`;
                const statusIcon = r.passed ? '<i class="fas fa-check"></i> Réussi' : '<i class="fas fa-times"></i> Échoué';
                const statusColor = r.passed ? '#28a745' : '#dc3545';
                const statusBg = r.passed ? 'rgba(40,167,69,0.1)' : 'rgba(220,53,69,0.1)';

                let detailsHtml = '';
                if (r.error && r.error !== 'Execution Failed') {
                    detailsHtml = `<div style="color:#ff6b6b; white-space: pre-wrap; font-family: monospace; font-size: 0.9em; padding: 8px;">${escapeHtml(formatSingleError(r.error))}</div>`;
                } else if (!isHidden) {
                    detailsHtml = `
                        <div style="padding: 8px; font-size: 0.9em; font-family: monospace;">
                            <div style="margin-bottom: 4px;"><strong>Entrée :</strong> ${escapeHtml(r.input || '(Vide)')}</div>
                            <div style="margin-bottom: 4px;"><strong>Attendu :</strong> ${escapeHtml(r.expected_output || '(Vide)')}</div>
                            <div><strong>Votre Sortie :</strong> <span style="color:${statusColor}">${escapeHtml(r.actual_output || '(Rien)')}</span></div>
                        </div>
                    `;
                }

                return `
                    <div class="test-case-card" style="margin-bottom: 12px;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                            <h4 style="margin:0;">${cardTitle}</h4>
                            <span style="font-size: 0.8rem; font-weight: 600; color: ${statusColor}; background: ${statusBg}; padding: 2px 8px; border-radius: 4px;">
                                ${statusIcon} (${Number(r.execution_time_ms || 0).toFixed(2)} ms)
                            </span>
                        </div>
                        ${detailsHtml}
                    </div>
                `;
            }).join('');
            return;
        }

        // Standard pairing with existing public test case cards
        data.results.forEach((r, i) => {
            if (i < tcCards.length) {
                const card = tcCards[i];
                const oldRes = card.querySelector('.tc-quick-result');
                if (oldRes) oldRes.remove();

                const resDiv = document.createElement('div');
                resDiv.className = `tc-quick-result ${r.passed ? 'passed' : 'failed'}`;
                resDiv.style.marginTop = '10px';
                resDiv.style.borderRadius = '4px';
                resDiv.style.overflow = 'hidden';
                resDiv.style.border = r.passed ? '1px solid #28a745' : '1px solid #dc3545';

                const header = document.createElement('div');
                header.style.padding = '8px';
                header.style.cursor = 'pointer';
                header.style.display = 'flex';
                header.style.justifyContent = 'space-between';
                header.style.alignItems = 'center';
                header.style.backgroundColor = r.passed ? 'rgba(40,167,69,0.1)' : 'rgba(220,53,69,0.1)';
                header.style.color = r.passed ? '#28a745' : '#dc3545';
                header.style.fontWeight = 'bold';
                header.innerHTML = `<span>${r.passed ? '<i class="fas fa-check"></i> Réussi' : '<i class="fas fa-times"></i> Échoué'}</span> <i class="fas fa-chevron-down"></i>`;

                const body = document.createElement('div');
                body.style.padding = '8px';
                body.style.display = r.passed ? 'none' : 'block';
                body.style.backgroundColor = 'var(--bg-color, #1e1e1e)';
                body.style.color = 'var(--text-color, #e0e0e0)';
                body.style.fontSize = '0.9em';
                body.style.fontFamily = 'monospace';

                let detailsHtml = '';
                if (r.error && r.error !== 'Execution Failed') {
                    detailsHtml = `<div style="color:#ff6b6b; white-space: pre-wrap;">${escapeHtml(formatSingleError(r.error))}</div>`;
                } else {
                    detailsHtml = `
                        <div style="margin-bottom: 5px; white-space: pre-wrap;"><strong>Entrée :</strong> ${escapeHtml(r.input || '(Vide)')}</div>
                        <div style="margin-bottom: 5px; white-space: pre-wrap;"><strong>Attendu :</strong> ${escapeHtml(r.expected_output || '(Vide)')}</div>
                        <div style="white-space: pre-wrap;"><strong>Votre Sortie :</strong> <span style="color:${r.passed ? '#28a745' : '#ff6b6b'}">${escapeHtml(r.actual_output || '(Rien)')}</span></div>
                    `;
                }
                body.innerHTML = detailsHtml;

                header.onclick = () => {
                    const isHidden = body.style.display === 'none';
                    body.style.display = isHidden ? 'block' : 'none';
                    header.querySelector('i:last-child').className = isHidden ? 'fas fa-chevron-up' : 'fas fa-chevron-down';
                };

                resDiv.appendChild(header);
                resDiv.appendChild(body);
                card.appendChild(resDiv);
            }
        });
    }

    async function executeStdin() {
        if (!window.editor) return;

        // Switch to console tab automatically
        document.querySelector('[data-target="tab-console"]').click();

        const code = window.editor.getValue();
        const customInput = document.getElementById('custom-input').value;
        const consoleLogs = document.getElementById('console-logs');

        consoleLogs.innerHTML = '<span style="color:#888;">Exécution en cours...</span>';

        try {
            const res = await fetchWithTimeout('/api/submissions/custom', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    code: code,
                    input: customInput
                })
            }, REQUEST_TIMEOUT_MS.stdin);

            const data = await res.json();

            if (data.success && data.results && data.results.length > 0) {
                const r = data.results[0];
                if (r.error && r.error !== 'Execution Failed') {
                    consoleLogs.innerHTML = `<span style="color:#ff6b6b; white-space: pre-wrap;">${escapeHtml(formatSingleError(r.error))}</span>`;
                } else {
                    consoleLogs.innerHTML = `<span style="white-space: pre-wrap;">${escapeHtml(r.actual_output || '(Aucune Sortie)')}</span>`;
                }
            } else {
                const details = formatErrorDetails(data.details);
                consoleLogs.innerHTML = `<span style="color:#ff6b6b; white-space: pre-wrap;">Erreur: ${escapeHtml(data.error || 'Erreur inconnue')}</span>`;
                if (details.length) {
                    consoleLogs.innerHTML += `<br><span style="color:#ff6b6b; white-space: pre-wrap;">${details.map(d => escapeHtml(d)).join('<br>')}</span>`;
                }
            }
        } catch (e) {
            consoleLogs.innerHTML = `<span style="color:#ff6b6b; white-space: pre-wrap;">Erreur de connexion: ${escapeHtml(describeRequestError(e, 'L’exécution stdin a pris trop de temps. Réessayez.'))}</span>`;
        }
    }

    if (runTestsBtn) runTestsBtn.addEventListener('click', () => executeCode(false));
    if (submitBtn) submitBtn.addEventListener('click', () => executeCode(true));
    if (runStdinBtn) runStdinBtn.addEventListener('click', () => executeStdin());

    // Clear Console
    const clearBtn = document.getElementById('clear-console-btn');
    if (clearBtn) {
        clearBtn.addEventListener('click', () => {
            document.getElementById('console-logs').innerHTML = '';
        });
    }

    // Timer Logic
    window.challengeTimerSeconds = 0;
    const timerDisplay = document.getElementById('timer-display');
    let timerInterval = null;

    function formatTime(totalSeconds) {
        const m = Math.floor(totalSeconds / 60).toString().padStart(2, '0');
        const s = (totalSeconds % 60).toString().padStart(2, '0');
        return `${m}:${s}`;
    }

    function startTimer() {
        if (timerInterval) clearInterval(timerInterval);
        timerInterval = setInterval(() => {
            window.challengeTimerSeconds++;
            if (timerDisplay) {
                timerDisplay.textContent = formatTime(window.challengeTimerSeconds);
                // change color if taking too long (e.g. 15 minutes = 900s)
                if (window.challengeTimerSeconds > 900) {
                    timerDisplay.parentElement.style.color = '#ffc107'; // yellow
                    timerDisplay.parentElement.style.background = 'rgba(255, 193, 7, 0.1)';
                }
            }
        }, 1000);
    }

    // Start timer automatically when the problem is fully loaded
    startTimer();

});
