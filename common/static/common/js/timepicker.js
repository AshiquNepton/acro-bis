/**
 * Custom Time Picker  v1.1
 * common/static/common/js/timepicker.js
 *
 * Display format : HH:MM AM/PM  (12-hour)
 * Submit format  : HH:MM        (24-hour, Django-compatible)
 *
 * Fixes in v1.1:
 *   - All panel buttons now carry type="button" — prevents form submission
 *     on OK / Clear / arrow clicks.
 *   - Hour and minute columns use <input type="text"> instead of a plain
 *     <div>, so the user can type values directly with the keyboard.
 *     • Hour  : accepts 1-12, clamps on blur/Enter
 *     • Minute: accepts 0-59, rounds to nearest 5-min step on blur/Enter
 *     Arrow buttons still work exactly as before.
 *
 * Public API (unchanged):
 *   tpToggle(id, event)
 *   tpStep(id, col, dir, event)
 *   tpConfirm(id, event)
 *   tpClear(id, event)
 *   tpRegister(id, hhmm24)
 */

(function () {
    'use strict';

    var pickers = {};

    /* ── Init: scan page for all .tp-panel shells ──────────────── */
    function init() {
        document.querySelectorAll('.tp-panel').forEach(function (panel) {
            var id        = panel.id.replace('_panel', '');
            var fieldName = id.replace('tp_', '');
            var hidden    = document.getElementById(fieldName);
            var raw       = hidden ? hidden.value.trim() : '';

            pickers[id] = _parseState(raw);
            _syncDisplay(id);
        });

        /* Close on outside click */
        document.addEventListener('click', function (e) {
            if (!e.target.closest('.tp-input-wrap') &&
                !e.target.closest('.tp-panel')) {
                closeAll();
            }
        });
        window.addEventListener('scroll', closeAll, true);
        window.addEventListener('resize', closeAll);
    }

    /* ── Parse HH:MM (24-h) string → state object ────────────── */
    function _parseState(raw) {
        if (raw && /^\d{1,2}:\d{2}$/.test(raw)) {
            var parts = raw.split(':').map(Number);
            var h = Math.max(0, Math.min(23, parts[0]));
            var m = Math.round(parts[1] / 5) * 5;
            if (m >= 60) { m = 0; h = (h + 1) % 24; }
            return { h: h, m: m };
        }
        return { h: 0, m: 0 };
    }

    /* ── Public API ──────────────────────────────────────────────*/

    window.tpToggle = function (id, event) {
        if (event) event.stopPropagation();

        var panel = document.getElementById(id + '_panel');
        var wrap  = document.getElementById(id + '_wrap');
        if (!panel || !wrap) return;

        var isOpen = panel.classList.contains('open');
        closeAll();

        if (!isOpen) {
            if (!pickers[id]) {
                var hidden = document.getElementById(id.replace('tp_', ''));
                tpRegister(id, hidden ? hidden.value : '');
            }
            renderPanel(id);
            panel.classList.add('open');
            wrap.classList.add('open');

            /* Position with fixed coords — same flip logic as datepicker */
            var rect = wrap.getBoundingClientRect();
            var panW = 192;
            var panH = 230;

            panel.style.position = 'fixed';
            panel.style.zIndex   = '9999';
            panel.style.width    = panW + 'px';

            if (rect.left + panW > window.innerWidth) {
                panel.style.left  = 'auto';
                panel.style.right = (window.innerWidth - rect.right) + 'px';
            } else {
                panel.style.left  = rect.left + 'px';
                panel.style.right = 'auto';
            }

            var spaceBelow = window.innerHeight - rect.bottom;
            if (spaceBelow < panH && rect.top > panH) {
                panel.style.top    = 'auto';
                panel.style.bottom = (window.innerHeight - rect.top + 2) + 'px';
            } else {
                panel.style.top    = (rect.bottom + 2) + 'px';
                panel.style.bottom = 'auto';
            }
        }
    };

    window.tpStep = function (id, col, dir, event) {
        if (event) event.stopPropagation();
        var s = pickers[id];
        if (!s) return;

        if (col === 'h') {
            s.h = ((s.h + dir) + 24) % 24;
        } else if (col === 'm') {
            var newM = s.m + dir * 5;
            if (newM >= 60) { newM = 0;  s.h = (s.h + 1) % 24; }
            if (newM < 0)   { newM = 55; s.h = ((s.h - 1) + 24) % 24; }
            s.m = newM;
        } else if (col === 'ap') {
            s.h = s.h < 12 ? s.h + 12 : s.h - 12;
        }
        renderPanel(id);
    };

    window.tpConfirm = function (id, event) {
        if (event) event.stopPropagation();
        var s = pickers[id];
        if (!s) return;

        /* Flush any in-progress keyboard edits before committing */
        _flushInputs(id);
        _commit(id, s.h, s.m);
        closeAll();
    };

    window.tpClear = function (id, event) {
        if (event) event.stopPropagation();
        var s = pickers[id];
        if (s) { s.h = 0; s.m = 0; }

        var hidden  = document.getElementById(id.replace('tp_', ''));
        var display = document.getElementById(id + '_display');
        if (hidden)  { hidden.value = ''; hidden.dispatchEvent(new Event('change', { bubbles: true })); }
        if (display) { display.textContent = 'Choose Time'; display.classList.remove('has-value'); }

        closeAll();
    };

    /* ── Read typed values from open inputs into state ───────── */
    function _flushInputs(id) {
        var s = pickers[id];
        if (!s) return;

        var hInput = document.getElementById(id + '_h_input');
        var mInput = document.getElementById(id + '_m_input');

        if (hInput) { _applyHourInput(id, hInput.value); }
        if (mInput) { _applyMinuteInput(id, mInput.value); }
    }

    /* Apply a typed hour string (12-h) into state */
    function _applyHourInput(id, raw) {
        var s   = pickers[id];
        var val = parseInt(raw, 10);
        if (isNaN(val)) return;
        val = Math.max(1, Math.min(12, val));
        var isPM = s.h >= 12;
        s.h = isPM ? (val === 12 ? 12 : val + 12) : (val === 12 ? 0 : val);
    }

    /* Apply a typed minute string into state (rounds to nearest 5) */
    function _applyMinuteInput(id, raw) {
        var s   = pickers[id];
        var val = parseInt(raw, 10);
        if (isNaN(val)) return;
        val = Math.max(0, Math.min(59, val));
        val = Math.round(val / 5) * 5;
        if (val >= 60) val = 55;
        s.m = val;
    }

    /* ── Render the panel HTML ───────────────────────────────────*/
    function renderPanel(id) {
        var s     = pickers[id];
        var panel = document.getElementById(id + '_panel');
        if (!panel || !s) return;

        var h12  = s.h % 12 || 12;
        var ampm = s.h < 12 ? 'AM' : 'PM';
        var mm   = _pad(s.m);
        var hh   = _pad(h12);

        panel.innerHTML =
            '<div class="tp-cols">' +
            /* ── Hour column — editable input ── */
            _colInput('h', id, hh) +
            '<div class="tp-sep">:</div>' +
            /* ── Minute column — editable input ── */
            _colInput('m', id, mm) +
            /* ── AM/PM column — buttons only ── */
            '<div class="tp-col tp-col--ampm">' +
                '<button type="button" class="tp-nav-btn" onclick="tpStep(\'' + id + '\',\'ap\',1,event)">&#9650;</button>' +
                '<div class="tp-val">' + ampm + '</div>' +
                '<button type="button" class="tp-nav-btn" onclick="tpStep(\'' + id + '\',\'ap\',-1,event)">&#9660;</button>' +
            '</div>' +
            '</div>' +
            '<div class="tp-footer">' +
                '<button type="button" class="tp-btn-clear" onclick="tpClear(\'' + id + '\',event)">Clear</button>' +
                '<button type="button" class="tp-btn-ok"    onclick="tpConfirm(\'' + id + '\',event)">OK</button>' +
            '</div>';

        /* Attach keyboard handlers after innerHTML is set */
        _bindInputHandlers(id);
    }

    /* Build a column with ▲ / editable-input / ▼ */
    function _colInput(col, id, displayVal) {
        var inputId = id + '_' + col + '_input';
        return '<div class="tp-col">' +
            '<button type="button" class="tp-nav-btn" onclick="tpStep(\'' + id + '\',\'' + col + '\',1,event)">&#9650;</button>' +
            '<input type="text" class="tp-val tp-val--input" id="' + inputId + '"' +
                   ' value="' + displayVal + '"' +
                   ' maxlength="2"' +
                   ' onclick="event.stopPropagation()"' +
                   ' inputmode="numeric">' +
            '<button type="button" class="tp-nav-btn" onclick="tpStep(\'' + id + '\',\'' + col + '\',-1,event)">&#9660;</button>' +
            '</div>';
    }

    /* Wire up keyboard events on the newly created inputs */
    function _bindInputHandlers(id) {
        var hInput = document.getElementById(id + '_h_input');
        var mInput = document.getElementById(id + '_m_input');

        if (hInput) {
            hInput.addEventListener('focus', function () { this.select(); });

            hInput.addEventListener('keydown', function (e) {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    _applyHourInput(id, this.value);
                    renderPanel(id);
                }
                if (e.key === 'ArrowUp')   { e.preventDefault(); tpStep(id, 'h',  1); }
                if (e.key === 'ArrowDown') { e.preventDefault(); tpStep(id, 'h', -1); }
            });

            hInput.addEventListener('blur', function () {
                _applyHourInput(id, this.value);
                renderPanel(id);
            });
        }

        if (mInput) {
            mInput.addEventListener('focus', function () { this.select(); });

            mInput.addEventListener('keydown', function (e) {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    _applyMinuteInput(id, this.value);
                    renderPanel(id);
                }
                if (e.key === 'ArrowUp')   { e.preventDefault(); tpStep(id, 'm',  1); }
                if (e.key === 'ArrowDown') { e.preventDefault(); tpStep(id, 'm', -1); }
            });

            mInput.addEventListener('blur', function () {
                _applyMinuteInput(id, this.value);
                renderPanel(id);
            });
        }
    }

    /* ── Commit a value (write hidden + display) ─────────────── */
    function _commit(id, h24, m) {
        var iso     = _pad(h24) + ':' + _pad(m);
        var h12     = h24 % 12 || 12;
        var ampm    = h24 < 12 ? 'AM' : 'PM';
        var display = _pad(h12) + ':' + _pad(m) + ' ' + ampm;

        var hidden  = document.getElementById(id.replace('tp_', ''));
        var dispEl  = document.getElementById(id + '_display');

        if (hidden)  { hidden.value = iso; hidden.dispatchEvent(new Event('change', { bubbles: true })); }
        if (dispEl)  { dispEl.textContent = display; dispEl.classList.add('has-value'); }

        if (pickers[id]) { pickers[id].h = h24; pickers[id].m = m; }
    }

    /* ── Sync display text on page load (when field has value) ── */
    function _syncDisplay(id) {
        var s      = pickers[id];
        var dispEl = document.getElementById(id + '_display');
        if (!s || !dispEl) return;

        var hidden = document.getElementById(id.replace('tp_', ''));
        if (!hidden || !hidden.value) return;

        var h12  = s.h % 12 || 12;
        var ampm = s.h < 12 ? 'AM' : 'PM';
        dispEl.textContent = _pad(h12) + ':' + _pad(s.m) + ' ' + ampm;
        dispEl.classList.add('has-value');
    }

    /* ── Close all open panels ───────────────────────────────── */
    function closeAll() {
        document.querySelectorAll('.tp-panel').forEach(function (p) { p.classList.remove('open'); });
        document.querySelectorAll('.tp-input-wrap').forEach(function (w) { w.classList.remove('open'); });
    }

    /* ── Helpers ─────────────────────────────────────────────── */
    function _pad(n) { return ('0' + n).slice(-2); }

    /* ── Public registration (mirrors dpRegister) ────────────── */
    window.tpRegister = function (tpid, hhmm24) {
        pickers[tpid] = _parseState(hhmm24 || '');
    };

    /* Expose internals for dynamic injection */
    window._tpPickers   = pickers;
    window._tpToISO     = function (h, m) { return _pad(h) + ':' + _pad(m); };
    window._tpToDisplay = function (h24, m) {
        var h12 = h24 % 12 || 12;
        return _pad(h12) + ':' + _pad(m) + (h24 < 12 ? ' AM' : ' PM');
    };

    /* ── Boot ─────────────────────────────────────────────────── */
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

}());