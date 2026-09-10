/**
 * user_card_modal.js
 * Universal Player Showcase Card & Prestige Badge Controller
 * Opens an ultra-modern Gamer/LeetCode style card on click of any user across the app.
 */

(function () {
    'use strict';

    const cardCache = new Map();

    function getTierRingClass(levelNum) {
        switch (Number(levelNum)) {
            case 1: return 'tier-ring-debutant';
            case 2: return 'tier-ring-amateur';
            case 3: return 'tier-ring-bosseur';
            case 4: return 'tier-ring-expert';
            case 5: return 'tier-ring-master';
            case 6: return 'tier-ring-legende';
            default: return 'tier-ring-debutant';
        }
    }

    function ensureModalMarkup() {
        if (document.getElementById('player-card-modal-overlay')) return;

        const overlay = document.createElement('div');
        overlay.id = 'player-card-modal-overlay';
        overlay.innerHTML = `
            <div class="player-card-box" role="dialog" aria-modal="true">
                <button class="player-card-close-btn" id="player-card-close" aria-label="Fermer">
                    <i class="fas fa-times"></i>
                </button>
                <div id="player-card-content">
                    <div style="padding: 60px 20px; text-align: center; color: #94a3b8;">
                        <i class="fas fa-spinner fa-spin fa-2x" style="color: #4a6ee0;"></i>
                        <p style="margin-top: 14px; font-weight: 600;">Chargement du profil joueur...</p>
                    </div>
                </div>
            </div>
        `;
        document.body.appendChild(overlay);

        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) closeUserCard();
        });

        const closeBtn = overlay.querySelector('#player-card-close');
        if (closeBtn) closeBtn.addEventListener('click', closeUserCard);

        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && overlay.classList.contains('active')) {
                closeUserCard();
            }
        });
    }

    function closeUserCard() {
        const overlay = document.getElementById('player-card-modal-overlay');
        if (overlay) {
            overlay.classList.remove('active');
        }
    }

    function renderPrestigeBadgeHtml(badge) {
        if (!badge) return '';
        return `
            <span class="prestige-badge ${badge.class || ''}" title="${badge.label || ''}">
                <i class="${badge.icon || 'fas fa-award'}"></i>
                <span>${badge.short_label || badge.label || ''}</span>
            </span>
        `;
    }

    async function openUserCard(userId) {
        if (!userId) return;
        ensureModalMarkup();
        const overlay = document.getElementById('player-card-modal-overlay');
        const content = document.getElementById('player-card-content');
        overlay.classList.add('active');

        // Check in-memory cache
        if (cardCache.has(Number(userId))) {
            renderCardData(cardCache.get(Number(userId)));
            return;
        }

        content.innerHTML = `
            <div style="padding: 60px 20px; text-align: center; color: #94a3b8;">
                <i class="fas fa-spinner fa-spin fa-2x" style="color: #4a6ee0;"></i>
                <p style="margin-top: 14px; font-weight: 600;">Chargement du profil joueur...</p>
            </div>
        `;

        try {
            const resp = await fetch(`/api/users/${userId}/card_profile`);
            if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
            const data = await resp.json();
            if (!data.success || !data.card) throw new Error(data.error || 'Erreur inconnue');

            cardCache.set(Number(userId), data.card);
            renderCardData(data.card);
        } catch (err) {
            content.innerHTML = `
                <div style="padding: 40px 20px; text-align: center; color: #f87171;">
                    <i class="fas fa-exclamation-triangle fa-2x" style="margin-bottom: 12px;"></i>
                    <p style="font-weight: 700;">Impossible de charger ce profil.</p>
                    <p style="font-size: 0.85rem; opacity: 0.8;">${err.message}</p>
                </div>
            `;
        }
    }

    function renderCardData(card) {
        const content = document.getElementById('player-card-content');
        if (!content) return;

        const level = card.level || { num: 1, name: 'Débutant', icon: '🧭', icon_class: 'fa-solid fa-compass', color: '#94a3b8' };
        const ringClass = getTierRingClass(level.num);
        const prestigeHtml = renderPrestigeBadgeHtml(card.prestige_badge);
        const initialLetter = (card.name || '?').trim().charAt(0).toUpperCase();

        const isTop1 = card.prestige_badge && card.prestige_badge.type === 'top1';
        const crownHtml = isTop1 ? `<div class="player-card-avatar-crown">👑</div>` : '';

        const streakDays = (card.streak && card.streak.current_streak) || 0;
        const streakHtml = streakDays > 0 ? `
            <div class="player-card-streak-pill" title="${streakDays} jours d'affilée">
                <i class="fas fa-fire"></i> ${streakDays} ${streakDays > 1 ? 'Jours' : 'Jour'}
            </div>
        ` : '';

        const stats = card.stats || {};
        const badges = card.badges || [];

        // Build Badge Grid
        let badgesHtml = '';
        if (badges.length > 0) {
            badgesHtml = badges.map(b => `
                <div class="player-mini-badge" title="${b.name} : ${b.desc || ''} (+${b.xp || 10} XP)">
                    <i class="${b.icon || 'fas fa-medal'}"></i>
                    <span class="player-mini-badge-xp">+${b.xp || 10}</span>
                </div>
            `).join('');
        } else {
            badgesHtml = `<span style="font-size: 0.82rem; color: #94a3b8; grid-column: 1 / -1; padding: 10px 0; text-align: center;">Aucun trophée débloqué pour l'instant.</span>`;
        }

        // Multi-titles setup
        let equippedList = card.equipped_titles && card.equipped_titles.length
            ? [...card.equipped_titles]
            : (card.equipped_title ? [card.equipped_title] : ['🌱 Novice de l\'Algorithmique']);

        const renderTitlePills = (titles) => {
            if (!titles || !titles.length) return `<span class="player-card-title-pill">« Novice »</span>`;
            return titles.map(t => `<span class="player-card-title-pill">« ${t} »</span>`).join('');
        };

        // Title Chips Selector for owner
        let titlePickerHtml = '';
        if (card.is_owner && card.unlocked_titles && card.unlocked_titles.length > 0) {
            const chipsHtml = card.unlocked_titles.map(t => {
                const isSel = equippedList.includes(t);
                return `
                    <span class="player-title-chip ${isSel ? 'selected' : ''}" data-title="${t}">
                        <i class="fas ${isSel ? 'fa-check-circle' : 'fa-circle'}"></i> ${t}
                    </span>
                `;
            }).join('');

            titlePickerHtml = `
                <div class="player-title-picker-wrap">
                    <div class="player-title-picker-header">
                        <span><i class="fas fa-tags" style="color: #f6c453; margin-right: 6px;"></i> Titres Équipés (max 3)</span>
                        <span id="player-title-count" style="color: #38bdf8; font-size: 0.74rem;">${equippedList.length} / 3</span>
                    </div>
                    <div class="player-title-chips-wrap" id="player-title-chips-container">
                        ${chipsHtml}
                    </div>
                </div>
            `;
        }

        const levelIcon = level.icon_class
            ? `<i class="${level.icon_class}"></i>`
            : `<span>${level.icon || '🧭'}</span>`;

        content.innerHTML = `
            <div class="player-card-banner">
                <div class="player-card-avatar-wrap">
                    ${crownHtml}
                    <div class="player-card-avatar avatar-tier-ring ${ringClass}">
                        ${initialLetter}
                    </div>
                </div>
                <h3 class="player-card-name">
                    <span>${card.name}</span>
                </h3>
                <div class="player-card-equipped-titles-row" id="player-active-titles-row">
                    ${renderTitlePills(equippedList)}
                </div>
                <div class="player-card-badges-row">
                    ${prestigeHtml}
                    <span class="level-badge-modern" style="color:${level.color}; border: 1px solid ${level.color};">
                        <span class="level-icon-badge">${levelIcon}</span>
                        <span>${level.name}</span>
                    </span>
                    <span style="font-size:0.78rem; font-weight:800; color:#38bdf8; background:rgba(56,189,248,0.12); border:1px solid rgba(56,189,248,0.3); padding:2px 8px; border-radius:999px;">
                        ⚡ ${card.xp_total || 0} XP
                    </span>
                    ${streakHtml}
                </div>
            </div>

            <div class="player-card-body">
                <div class="player-card-stats-grid">
                    <div class="player-stat-tile" title="Victoires absolues en N°1">
                        <div class="player-stat-val" style="color: #ffd700;">${stats.top1 || 0}</div>
                        <div class="player-stat-lbl">🥇 Top 1</div>
                    </div>
                    <div class="player-stat-tile" title="Podiums Top 3">
                        <div class="player-stat-val" style="color: #f97316;">${stats.top3 || 0}</div>
                        <div class="player-stat-lbl">🏆 Top 3</div>
                    </div>
                    <div class="player-stat-tile" title="Classements Top 10">
                        <div class="player-stat-val" style="color: #10b981;">${stats.top10 || 0}</div>
                        <div class="player-stat-lbl">🎖️ Top 10</div>
                    </div>
                    <div class="player-stat-tile" title="Défis algorithmiques résolus">
                        <div class="player-stat-val" style="color: #38bdf8;">${stats.challenges_completed || 0}</div>
                        <div class="player-stat-lbl">💻 Défis</div>
                    </div>
                    <div class="player-stat-tile" title="Quiz de cours validés">
                        <div class="player-stat-val" style="color: #a855f7;">${stats.quizzes_passed || 0}</div>
                        <div class="player-stat-lbl">📚 Quiz</div>
                    </div>
                    <div class="player-stat-tile" title="Rang général all-time">
                        <div class="player-stat-val" style="color: #f1f5f9;">#${card.global_rank || '--'}</div>
                        <div class="player-stat-lbl">🌐 Rang</div>
                    </div>
                </div>

                <div class="player-card-trophies-section">
                    <div class="player-card-section-title">
                        <span><i class="fas fa-trophy" style="color: #f6c453; margin-right: 6px;"></i> Trophées & Badges</span>
                        <span style="font-size: 0.72rem; opacity: 0.8;">${badges.length} débloqué${badges.length > 1 ? 's' : ''}</span>
                    </div>
                    <div class="player-card-badges-grid">
                        ${badgesHtml}
                    </div>
                </div>

                ${titlePickerHtml}
            </div>
        `;

        // Handle title chips toggle
        const chipsWrap = content.querySelector('#player-title-chips-container');
        if (chipsWrap) {
            chipsWrap.addEventListener('click', async (e) => {
                const chip = e.target.closest('.player-title-chip');
                if (!chip) return;
                const clickedTitle = chip.getAttribute('data-title');
                if (!clickedTitle) return;

                const isAlreadySelected = equippedList.includes(clickedTitle);

                if (isAlreadySelected) {
                    if (equippedList.length <= 1) {
                        if (typeof Swal !== 'undefined') {
                            Swal.fire({
                                toast: true,
                                position: 'top-end',
                                icon: 'warning',
                                title: 'Vous devez conserver au moins 1 titre actif.',
                                showConfirmButton: false,
                                timer: 2000
                            });
                        } else {
                            alert('Vous devez conserver au moins 1 titre actif.');
                        }
                        return;
                    }
                    equippedList = equippedList.filter(t => t !== clickedTitle);
                } else {
                    if (equippedList.length >= 3) {
                        if (typeof Swal !== 'undefined') {
                            Swal.fire({
                                toast: true,
                                position: 'top-end',
                                icon: 'warning',
                                title: 'Maximum 3 titres peuvent être équipés simultanément.',
                                showConfirmButton: false,
                                timer: 2000
                            });
                        } else {
                            alert('Maximum 3 titres peuvent être équipés simultanément.');
                        }
                        return;
                    }
                    equippedList.push(clickedTitle);
                }

                // Update UI immediately
                const countLabel = content.querySelector('#player-title-count');
                if (countLabel) countLabel.textContent = `${equippedList.length} / 3`;

                chipsWrap.querySelectorAll('.player-title-chip').forEach(c => {
                    const tName = c.getAttribute('data-title');
                    const sel = equippedList.includes(tName);
                    c.classList.toggle('selected', sel);
                    const icon = c.querySelector('i');
                    if (icon) {
                        icon.className = `fas ${sel ? 'fa-check-circle' : 'fa-circle'}`;
                    }
                });

                const titlesRow = content.querySelector('#player-active-titles-row');
                if (titlesRow) titlesRow.innerHTML = renderTitlePills(equippedList);

                // Save to server
                try {
                    const resp = await fetch('/api/user/title', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRFToken': (typeof CSRF_TOKEN !== 'undefined' ? CSRF_TOKEN : (document.querySelector('meta[name="csrf-token"]') ? document.querySelector('meta[name="csrf-token"]').getAttribute('content') : ''))
                        },
                        body: JSON.stringify({ titles: equippedList })
                    });
                    const resData = await resp.json();
                    if (resData.success) {
                        card.equipped_titles = equippedList;
                        card.equipped_title = equippedList[0];
                        cardCache.set(Number(card.user_id), card);
                    } else {
                        alert(resData.error || 'Erreur lors de la sauvegarde des titres.');
                    }
                } catch (err) {
                    console.error('Error saving titles:', err);
                }
            });
        }
    }

    // Global Event Delegation for clicking on any user element with data-user-id or .user-card-trigger
    document.addEventListener('click', (e) => {
        const trigger = e.target.closest('.user-card-trigger, [data-user-id]');
        if (trigger) {
            const userId = trigger.getAttribute('data-user-id');
            if (userId) {
                e.preventDefault();
                e.stopPropagation();
                openUserCard(userId);
            }
        }
    });

    // Expose helper globally
    window.openUserCard = openUserCard;
    window.closeUserCard = closeUserCard;
    window.renderPrestigeBadgeHtml = renderPrestigeBadgeHtml;
})();
