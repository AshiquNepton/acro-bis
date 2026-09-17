/**
 * Custom Date Picker  v1.2
 * common/static/common/js/datepicker.js
 *
 * Display format : DD-MM-YYYY
 * Submit format  : YYYY-MM-DD  (hidden input, Django-compatible)
 */

(function () {
    'use strict';

    const MONTHS = ['January', 'February', 'March', 'April', 'May', 'June',
        'July', 'August', 'September', 'October', 'November', 'December'];
    const WEEKDAYS = ['S', 'M', 'T', 'W', 'T', 'F', 'S'];

    const pickers = {};

    // ── Init: scan page for all .dp-calendar shells ──────────────
    function init() {
        document.querySelectorAll('.dp-calendar').forEach(function (cal) {
            var id = cal.id.replace('_cal', '');
            var fieldName = id.replace('dp_', '');
            var hiddenInput = document.getElementById(fieldName);
            var display = document.getElementById(id + '_display');

            var selected = null;
            var raw = hiddenInput ? hiddenInput.value.trim() : '';
            if (raw && /^\d{4}-\d{2}-\d{2}$/.test(raw)) {
                var parts = raw.split('-').map(Number);
                selected = new Date(parts[0], parts[1] - 1, parts[2]);
            }

            var now = selected || new Date();
            pickers[id] = { month: now.getMonth(), year: now.getFullYear(), selected: selected };

            if (selected && display) {
                display.textContent = toDisplay(selected);
                display.classList.add('has-value');
            }
        });

        // Close on outside click — only when click is truly outside any picker
        document.addEventListener('click', function (e) {
            if (!e.target.closest('.dp-input-wrap') &&
                !e.target.closest('.dp-calendar')) {
                closeAll();
            }
        });
        // Close on scroll or resize to prevent drifting fixed calendar
        window.addEventListener('scroll', closeAll, true);
        window.addEventListener('resize', closeAll);
    }

    // ── Public API ────────────────────────────────────────────────

    window.dpToggle = function (id, event) {
    if (event) event.stopPropagation();

    var cal = document.getElementById(id + '_cal');
    var wrap = document.getElementById(id + '_wrap');
    if (!cal || !wrap) return;

    var isOpen = cal.classList.contains('open');
    closeAll();

    if (!isOpen) {
        if (!pickers[id]) {
            var _h = document.getElementById(id.replace('dp_', ''));
            var _v = _h ? _h.value : '';
            window.dpRegister(id, _v);
        }
        renderCalendar(id);

        // ── Move to <body> so no ancestor (overflow/transform/sticky) can clip or reorder it ──
        if (cal.parentNode !== document.body) {
            cal._originalParent = cal.parentNode;
            cal._originalNextSibling = cal.nextSibling;
            document.body.appendChild(cal);
        }

        cal.classList.add('open');
        wrap.classList.add('open');

        var rect = wrap.getBoundingClientRect();
        var calW = Math.min(Math.max(rect.width, 260), 300);

        cal.style.position = 'fixed';
        cal.style.zIndex = '10600';  // above .pf-toast (10500) and everything else
        cal.style.width = calW + 'px';

        if (rect.left + calW > window.innerWidth) {
            cal.style.left = 'auto';
            cal.style.right = (window.innerWidth - rect.right) + 'px';
        } else {
            cal.style.left = rect.left + 'px';
            cal.style.right = 'auto';
        }

        var calH = 300;
        var spaceBelow = window.innerHeight - rect.bottom;
        if (spaceBelow < calH && rect.top > calH) {
            cal.style.top = 'auto';
            cal.style.bottom = (window.innerHeight - rect.top + 2) + 'px';
        } else {
            cal.style.top = (rect.bottom + 2) + 'px';
            cal.style.bottom = 'auto';
        }
    }
};

    window.dpNavigate = function (id, dir, event) {
        if (event) event.stopPropagation();
        var s = pickers[id];
        if (!s) return;
        s.month += dir;
        if (s.month > 11) { s.month = 0; s.year++; }
        if (s.month < 0) { s.month = 11; s.year--; }
        renderCalendar(id);
    };

    window.dpSelect = function (id, year, month, day, event) {
        if (event) event.stopPropagation();
        var s = pickers[id];
        if (!s) return;

        s.selected = new Date(year, month, day);
        s.month = month;
        s.year = year;

        // Hidden input → YYYY-MM-DD for Django
        var hiddenInput = document.getElementById(id.replace('dp_', ''));
        if (hiddenInput) {
            hiddenInput.value = toISO(s.selected);
            hiddenInput.dispatchEvent(new Event('change', { bubbles: false }));
        }

        // Visible display → DD-MM-YYYY
        var display = document.getElementById(id + '_display');
        if (display) {
            display.textContent = toDisplay(s.selected);
            display.classList.add('has-value');
        }

        closeAll();
    };

    // ── Render ────────────────────────────────────────────────────
    function renderCalendar(id) {
        var s = pickers[id];
        var cal = document.getElementById(id + '_cal');
        if (!cal || !s) return;

        var firstDow = new Date(s.year, s.month, 1).getDay();
        var daysInMonth = new Date(s.year, s.month + 1, 0).getDate();
        var daysInPrev = new Date(s.year, s.month, 0).getDate();
        var today = new Date();

        var html = '<div class="dp-cal-header">'
            + '<span class="dp-month-label">'
            + MONTHS[s.month] + ' ' + s.year
            + '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M6 9l6 6 6-6"/></svg>'
            + '</span>'
            + '<div class="dp-nav-btns">'
            + '<button type="button" class="dp-nav-btn" onclick="dpNavigate(\'' + id + '\',-1,event)">&#8249;</button>'
            + '<button type="button" class="dp-nav-btn" onclick="dpNavigate(\'' + id + '\',1,event)">&#8250;</button>'
            + '</div></div>'
            + '<div class="dp-weekdays">'
            + WEEKDAYS.map(function (d) { return '<div class="dp-weekday">' + d + '</div>'; }).join('')
            + '</div>'
            + '<div class="dp-days-grid">';

        // Prev month fill
        for (var i = firstDow - 1; i >= 0; i--) {
            html += '<button type="button" class="dp-day dp-day--other" tabindex="-1">' + (daysInPrev - i) + '</button>';
        }

        // Current month
        for (var d = 1; d <= daysInMonth; d++) {
            var isToday = (d === today.getDate() &&
                s.month === today.getMonth() &&
                s.year === today.getFullYear());
            var isSel = s.selected &&
                d === s.selected.getDate() &&
                s.month === s.selected.getMonth() &&
                s.year === s.selected.getFullYear();

            var cls = 'dp-day';
            if (isToday) cls += ' dp-day--today';
            if (isSel) cls += ' dp-day--selected';

            html += '<button type="button" class="' + cls + '"'
                + ' onclick="dpSelect(\'' + id + '\',' + s.year + ',' + s.month + ',' + d + ',event)">'
                + d + '</button>';
        }

        // Next month fill
        var rem = (firstDow + daysInMonth) % 7;
        for (var j = 1; j <= (rem ? 7 - rem : 0); j++) {
            html += '<button type="button" class="dp-day dp-day--other" tabindex="-1">' + j + '</button>';
        }

        html += '</div>';
        cal.innerHTML = html;
    }

    // ── Helpers ───────────────────────────────────────────────────
    function closeAll() {
    document.querySelectorAll('.dp-calendar').forEach(function (c) {
        c.classList.remove('open');
        if (c._originalParent && c.parentNode === document.body) {
            if (c._originalNextSibling) {
                c._originalParent.insertBefore(c, c._originalNextSibling);
            } else {
                c._originalParent.appendChild(c);
            }
        }
    });
    document.querySelectorAll('.dp-input-wrap').forEach(function (w) { w.classList.remove('open'); });
}
    function toISO(d) {
        return d.getFullYear()
            + '-' + String(d.getMonth() + 1).padStart(2, '0')
            + '-' + String(d.getDate()).padStart(2, '0');
    }

    function toDisplay(d) {
        return String(d.getDate()).padStart(2, '0')
            + '-' + String(d.getMonth() + 1).padStart(2, '0')
            + '-' + d.getFullYear();
    }

    window._dpToDisplay = toDisplay;
    window._dpToISO = toISO;
    window._dpPickers = pickers;   /* expose registry for dynamic injection */
    window.dpCloseAll = closeAll;   // ← add here

    window.dpRegister = function (dpid, isoValue) {
        var selected = null;
        if (isoValue && /^\d{4}-\d{2}-\d{2}$/.test(isoValue)) {
            var parts = isoValue.split('-').map(Number);
            selected = new Date(parts[0], parts[1] - 1, parts[2]);
        }
        var now = selected || new Date();
        pickers[dpid] = { month: now.getMonth(), year: now.getFullYear(), selected: selected };
    };

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

}());