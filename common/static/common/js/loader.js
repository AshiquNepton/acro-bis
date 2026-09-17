/**
 * common/static/common/js/loader.js
 *
 * Provides  window.erpLoader  — a universal loading overlay used by every
 * module in the ERP.  Replaces the old  window.utils.showLoading / hideLoading.
 *
 * ── Public API ───────────────────────────────────────────────────────────────
 *
 *   erpLoader.show(message)     Show overlay with optional message string.
 *   erpLoader.hide()            Fade out and hide the overlay.
 *   erpLoader.progress(n)       Set progress bar to 0-100. Shows bar automatically.
 *   erpLoader.message(text)     Update the message while already visible.
 *
 * ── Module logos ─────────────────────────────────────────────────────────────
 *
 *   Add  data-module="hrms"  to <body> in each module's base.html.
 *   Add the static logo path and label to MODULE_CONFIG below.
 *
 * ── Automatic page-load hide ─────────────────────────────────────────────────
 *
 *   The HTML overlay starts visible so slow connections see something
 *   instantly.  This script hides it as soon as DOMContentLoaded fires.
 *
 * ── Backwards compat ─────────────────────────────────────────────────────────
 *
 *   window.utils.showLoading / hideLoading are re-mapped to erpLoader so
 *   any existing code keeps working without changes.
 * ─────────────────────────────────────────────────────────────────────────────
 */

(function () {
    'use strict';

    /* ── Module configuration ───────────────────────────────────────────────
       logo   : path relative to STATIC_URL, or '' to skip the image
       label  : short capitalize text shown below the logo box
       icon   : SVG inner path(s) — shown when logo image is absent/fails
    ────────────────────────────────────────────────────────────────────────── */
    var MODULE_CONFIG = {
        hrms: {
            logo  : '/static/hrms/images/icons/logo.png',
            label : 'HRMS',
            icon  : '<path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>' +
                    '<circle cx="12" cy="7" r="4"/>',
        },
        laundry: {
            logo  : '/static/laundry/images/icons/logo.png',
            label : 'LAUNDRY',
            icon  : '<path d="M3 6h18"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6"/>' +
                    '<path d="M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>',
        },
        restaurant: {
            logo  : '/static/restaurant/images/icons/logo.png',
            label : 'RESTAURANT',
            icon  : '<path d="M3 2v7c0 1.1.9 2 2 2h4a2 2 0 0 0 2-2V2"/>' +
                    '<path d="M7 2v20"/><path d="M21 15V2a5 5 0 0 0-5 5v6c0 1.1.9 2 2 2h3z"/>',
        },
        inventory: {
            logo  : '/static/inventory/images/icons/logo.png',
            label : 'INVENTORY',
            icon  : '<path d="m7.5 4.27 9 5.15"/>' +
                    '<path d="M21 8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16Z"/>' +
                    '<path d="m3.3 7 8.7 5 8.7-5"/><path d="M12 22V12"/>',
        },
        financial: {
            logo  : '/static/financial/images/icons/logo.png',
            label : 'FINANCIAL',
            icon  : '<line x1="12" y1="1" x2="12" y2="23"/>' +
                    '<path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>',
        },
        reports: {
            logo  : '/static/reports/images/icons/logo.png',
            label : 'REPORTS',
            icon  : '<line x1="18" y1="20" x2="18" y2="10"/>' +
                    '<line x1="12" y1="20" x2="12" y2="4"/>' +
                    '<line x1="6"  y1="20" x2="6"  y2="14"/>',
        },
        /* ── default / common ── */
        default: {
            logo  : '',
            label : 'ERP',
            icon  : '<rect x="2" y="3" width="20" height="14" rx="2"/>' +
                    '<line x1="8" y1="21" x2="16" y2="21"/>' +
                    '<line x1="12" y1="17" x2="12" y2="21"/>',
        },
    };

    /* ── DOM refs ───────────────────────────────────────────────────────────── */
    var _overlay  = null;
    var _img      = null;
    var _icon     = null;
    var _svg      = null;
    var _moduleEl = null;
    var _msgEl    = null;
    var _barWrap  = null;
    var _bar      = null;

    function _grab() {
        _overlay  = document.getElementById('erp-loader');
        _img      = document.getElementById('erp-loader-img');
        _icon     = document.getElementById('erp-loader-icon');
        _svg      = document.getElementById('erp-loader-svg');
        _moduleEl = document.getElementById('erp-loader-module');
        _msgEl    = document.getElementById('erp-loader-msg');
        _barWrap  = document.getElementById('erp-loader-bar-wrap');
        _bar      = document.getElementById('erp-loader-bar');
    }

    /* ── Read --color-primary from the live CSS theme ───────────────────────
       Falls back to #c0123c so the ring always has a colour even if the
       CSS variable isn't set yet.
    ────────────────────────────────────────────────────────────────────────── */
    function _getPrimaryColor() {
        var color = getComputedStyle(document.documentElement)
                        .getPropertyValue('--color-primary')
                        .trim();
        return color || '#c0123c';
    }

    /* ── Build the gradient SVG ring using the live theme colour ────────────── */
    function _getPrimaryColor() {
    var color = getComputedStyle(document.documentElement)
                    .getPropertyValue('--color-primary')
                    .trim();
    /* fallback — must NOT be blue, use your actual brand color */
    return color || '#c0123c';
}

function _buildRing(ringEl) {
    if (!ringEl) return;

    /* Read color AFTER a short delay so CSS variables are fully resolved */
    setTimeout(function () {
        var color = _getPrimaryColor();
        var uid   = 'erp-ring-' + Math.random().toString(36).slice(2, 7);

        // Card = 140×140, center = 70,70
        // Image circle r = 50, circumference ≈ 314px
        // ¾ arc = 235px shown, ¼ gap = 79px
        // rotate(-90) → arc starts at top, gap at bottom-left
        // gradient: transparent at tail → solid at head

        ringEl.innerHTML =
            '<svg viewBox="0 0 140 140" fill="none" xmlns="http://www.w3.org/2000/svg">' +
              '<defs>' +
                '<linearGradient id="' + uid + '" gradientUnits="userSpaceOnUse"' +
                ' x1="70" y1="20" x2="120" y2="120">' +
                  '<stop offset="0%"   stop-color="' + color + '" stop-opacity="0"/>' +
                  '<stop offset="60%"  stop-color="' + color + '" stop-opacity="0.4"/>' +
                  '<stop offset="100%" stop-color="' + color + '" stop-opacity="1"/>' +
                '</linearGradient>' +
              '</defs>' +

              /* ── Single clean arc, no split, no scoop ── */
              '<circle cx="70" cy="70" r="50"' +
                ' stroke="url(#' + uid + ')"' +
                ' stroke-width="4.8"' +
                ' stroke-linecap="round"' +
                ' stroke-dasharray="235 79"' +
                ' transform="rotate(-90 70 70)"/>' +

            '</svg>';

    }, 50); /* wait 50ms for CSS vars to resolve */
}


    /* ── Init — run once on DOMContentLoaded ────────────────────────────────── */
    function _init() {
        _grab();
        if (!_overlay) return;

        var module = (document.body.getAttribute('data-module') || 'default').toLowerCase();
        var cfg    = MODULE_CONFIG[module] || MODULE_CONFIG['default'];

        /* ── Set module label ── */
        var customLabel = document.body.getAttribute('data-module-label');
        if (_moduleEl) _moduleEl.textContent = customLabel || cfg.label;

        /* ── Set SVG fallback icon ── */
        if (_svg && cfg.icon) _svg.innerHTML = cfg.icon;

        /* ── Inject gradient SVG ring using live --color-primary ── */
        var ringEl = document.getElementById('erp-loader-ring');
        _buildRing(ringEl);

        /* ── Try loading the logo image ── */
        if (_img && cfg.logo) {
            _img.onload = function () {
                _img.classList.add('erp-logo--loaded');
            };
            _img.onerror = function () {
                _img.src = '';
            };
            _img.src = cfg.logo;
        }

        /* ── Hide overlay now that the page is ready ── */
        _hideOverlay();
    }

    /* ── Core show / hide ───────────────────────────────────────────────────── */
    function _showOverlay(msg) {
        if (!_overlay) _grab();
        if (!_overlay) return;
        if (_msgEl) _msgEl.textContent = msg || '';
        _overlay.classList.remove('erp-loader--hidden');
    }

    function _hideOverlay() {
        if (!_overlay) _grab();
        if (!_overlay) return;
        _overlay.classList.add('erp-loader--hidden');
        if (_barWrap) _barWrap.style.display = 'none';
        if (_bar)     _bar.style.width = '0%';
    }

    /* ── Public API ─────────────────────────────────────────────────────────── */
    window.erpLoader = {

        show: function (message) {
            _showOverlay(message);
        },

        hide: function () {
            _hideOverlay();
        },

        message: function (text) {
            if (!_msgEl) _grab();
            if (_msgEl) _msgEl.textContent = text || '';
        },

        progress: function (value) {
            if (!_barWrap) _grab();
            if (!_barWrap || !_bar) return;
            var pct = Math.min(100, Math.max(0, value));
            _barWrap.style.display = 'block';
            _bar.style.width = pct + '%';
            if (pct >= 100) {
                var self = this;
                setTimeout(function () { self.hide(); }, 400);
            }
        },
    };

    /* ── Backwards compatibility ─────────────────────────────────────────────── */
    window.utils = window.utils || {};
    window.utils.showLoading = function (msg) { window.erpLoader.show(msg); };
    window.utils.hideLoading = function ()    { window.erpLoader.hide();    };

    /* ── Auto-hide on DOMContentLoaded ─────────────────────────────────────── */
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', _init);
    } else {
        _init();
    }

}());