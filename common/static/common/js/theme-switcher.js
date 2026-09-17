/* common/static/common/js/theme-switcher.js
   ─────────────────────────────────────────────────────────────────
   Responsibilities
   1. tsApply(swatchEl)  — called by each swatch card onclick
       • updates <html data-theme="..."> immediately (zero flicker)
       • persists to localStorage  (survives page reload before session)
       • POSTs to /common/save-theme/ to store in Django session
         (so server-rendered data-theme is correct on next load)
   2. On every page load the inline script in base.html already reads
      localStorage, so themes apply before CSS — this file only handles
      the picker page interaction and the session sync.
   ─────────────────────────────────────────────────────────────────*/

(function () {
    'use strict';

    var VALID_THEMES = ['red-white', 'blue-white', 'purple-white', 'green-white', 'teal-white', 'dark'];
    var SAVE_URL     = '/common/save-theme/';   // wired in urls.py

    /* ── Apply a theme from a swatch click ─────────────────── */
    window.tsApply = function (swatchEl) {
        var theme = swatchEl.dataset.theme;
        if (!theme || VALID_THEMES.indexOf(theme) === -1) return;

        // 1) Instant visual switch
        document.documentElement.setAttribute('data-theme', theme);

        // 2) Persist to localStorage (base.html reads this on every page)
        try { localStorage.setItem('erp_theme', theme); } catch (e) { /* private mode */ }

        // 3) Mark active swatch
        document.querySelectorAll('.ts-swatch').forEach(function (el) {
            el.classList.toggle('active', el === swatchEl);
        });

        // 4) Save to Django session via AJAX
        _saveToSession(theme);
    };

    /* ── AJAX: save theme to Django session ────────────────── */
    function _saveToSession(theme) {
        var csrf = _csrf();
        fetch(SAVE_URL, {
            method:  'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken':  csrf,
            },
            body: JSON.stringify({ theme: theme }),
        })
        .then(function (r) { return r.json(); })
        .then(function (d) {
            if (d.success) { _showBanner(); }
        })
        .catch(function () {
            // Silent fail — localStorage already persists the choice
        });
    }

    /* ── Show success banner on the settings page ───────────── */
    function _showBanner() {
        var banner = document.getElementById('ts-save-banner');
        if (!banner) return;
        banner.classList.add('visible');
        setTimeout(function () { banner.classList.remove('visible'); }, 3000);
    }

    /* ── CSRF helper ────────────────────────────────────────── */
    function _csrf() {
        var m = document.cookie.match(/csrftoken=([^;]+)/);
        return m ? decodeURIComponent(m[1]) : '';
    }

}());