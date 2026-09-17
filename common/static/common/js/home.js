// ================================================================
//  home.js  v8.0  —  REPLACE ENTIRE FILE
//  common/static/common/js/home.js
//  Dropdown: inline max-height (CSS handles animation)
//  Toggle button: absolute diamond on sidebar right edge
// ================================================================

/* ── IMMEDIATE: apply saved state before first paint ──────── */
(function () {
    var sidebar   = document.getElementById('sidebar');
    var footer    = document.getElementById('commonFooterBar');
    var collapsed = localStorage.getItem('sidebarCollapsed') === 'true';  /* ← 'true' string */
    if (sidebar && collapsed) sidebar.classList.add('collapsed');
    if (footer)  footer.style.left = collapsed ? '52px' : '220px';
})();


/* ── SIDEBAR COLLAPSE / EXPAND ─────────────────────────────── */
function toggleSidebar() {
    var sidebar = document.getElementById('sidebar');
    var footer  = document.getElementById('commonFooterBar');
    if (!sidebar) return;

    var isNowCollapsed = sidebar.classList.toggle('collapsed');
    localStorage.setItem('sidebarCollapsed', isNowCollapsed ? 'true' : 'false');

    if (footer) footer.style.left = isNowCollapsed ? '52px' : '220px';

    if (isNowCollapsed) {
        document.querySelectorAll('.nav-section.open')
                .forEach(function (s) { s.classList.remove('open'); });
    }
}


/* ── SECTION DROPDOWN (opens downward inline) ──────────────── */
function toggleSection(sectionId, tabEl) {
    var sidebar = document.getElementById('sidebar');
    var footer  = document.getElementById('commonFooterBar');

    /* If collapsed, expand first then open section */
    if (sidebar && sidebar.classList.contains('collapsed')) {
        sidebar.classList.remove('collapsed');
        localStorage.setItem('sidebarCollapsed', 'false');
        if (footer) footer.style.left = '220px';
        setTimeout(function () { _openSection(sectionId, tabEl); }, 280);
        return;
    }
    _openSection(sectionId, tabEl);
}

function _openSection(sectionId, tabEl) {
    var section  = document.getElementById('section-' + sectionId);
    if (!section) return;

    var hasItems = !!section.querySelector('.nav-subitems');
    var wasOpen  = section.classList.contains('open');

    /* Close every other open section */
    document.querySelectorAll('.nav-section.open').forEach(function (s) {
        if (s !== section) s.classList.remove('open');
    });

    /* Toggle this section */
    if (hasItems) section.classList.toggle('open', !wasOpen);

    /* Active tab */
    document.querySelectorAll('.nav-tab').forEach(function (t) { t.classList.remove('active'); });
    if (tabEl) tabEl.classList.add('active');

    /* Persist */
    var openIds = [];
    document.querySelectorAll('.nav-section.open').forEach(function (s) {
        openIds.push(s.id.replace('section-', ''));
    });
    try { localStorage.setItem('expandedSections', JSON.stringify(openIds)); } catch (e) {}
}




/* ── SUBITEM CLICK ─────────────────────────────────────────── */
function handleSubitemClick(event, sectionId) {
    var sidebar = document.getElementById('sidebar');
    var footer  = document.getElementById('commonFooterBar');

    /* If collapsed, expand then navigate */
    if (sidebar && sidebar.classList.contains('collapsed')) {
        event.preventDefault();
        sidebar.classList.remove('collapsed');
        localStorage.setItem('sidebarCollapsed', 'false');
        if (footer) footer.style.left = '220px';

        var href = event.currentTarget.getAttribute('href');
        setTimeout(function () {
            if (href && href !== '#' && href !== window.location.pathname) {
                window.location.href = href;
            }
        }, 300);
        return;
    }

    /* Mark active */
    document.querySelectorAll('.nav-subitem').forEach(function (el) {
        el.classList.remove('active');
    });
    event.currentTarget.classList.add('active');
}


/* ── CLOSE DROPDOWNS ON OUTSIDE CLICK ─────────────────────── */
document.addEventListener('click', function (e) {
    var sidebar = document.getElementById('sidebar');
    if (sidebar && !sidebar.contains(e.target)) {
        document.querySelectorAll('.nav-section.open').forEach(function (s) { s.classList.remove('open'); });
    }
});

/* ── RESTORE STATE ON DOM READY ────────────────────────────── */
document.addEventListener('DOMContentLoaded', function () {
    /* Restore open sections */
    var openIds = [];
    try { openIds = JSON.parse(localStorage.getItem('expandedSections') || '[]'); } catch (e) {}
    openIds.forEach(function (id) {
        var s = document.getElementById('section-' + id);
        if (s) s.classList.add('open');
    });

    /* Auto-mark active subitem from URL */
    var path = window.location.pathname;
    document.querySelectorAll('.nav-subitem').forEach(function (a) {
        if (a.getAttribute('href') === path) {
            a.classList.add('active');
            var ps = a.closest('.nav-section');
            if (ps) ps.classList.add('open');
        }
    });

    /* Mark tab active on any open section */
    document.querySelectorAll('.nav-section.open').forEach(function (s) {
        var tab = s.querySelector('.nav-tab');
        if (tab) tab.classList.add('active');
    });
});

/* ── DATETIME ──────────────────────────────────────────────── */
function updateDateTime() {
    var el = document.getElementById('currentDateTime');
    if (!el) return;
    el.textContent = new Date().toLocaleString('en-US', {
        weekday: 'short', year: 'numeric', month: 'short', day: 'numeric',
        hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: true
    });
}
updateDateTime();
setInterval(updateDateTime, 1000);

/* ── PROGRESS BAR ──────────────────────────────────────────── */
function showProgressBar(label) {
    var line = document.getElementById('footerProgressLine');
    var lbl  = document.getElementById('progressLabel');
    if (line) line.classList.add('active');
    if (lbl && label) lbl.textContent = label;
    updateProgress(0);
}
function hideProgressBar() {
    var line = document.getElementById('footerProgressLine');
    if (line) line.classList.remove('active');
}
function updateProgress(pct) {
    var fill = document.getElementById('progressBarFill');
    var pEl  = document.getElementById('progressPercentage');
    if (fill) fill.style.width = pct + '%';
    if (pEl)  pEl.textContent  = Math.round(pct) + '%';
}

/* ── MINIMIZED FORMS ───────────────────────────────────────── */
var _minimizedForms = new Map();

window.minimizeFormToFooter = function (formId, formTitle, formIcon) {
    var ov = document.getElementById(formId);
    if (ov) ov.style.display = 'none';
    _minimizedForms.set(formId, { title: formTitle || 'Form', icon: formIcon || '📝' });
    _renderMinimized();
};
window.restoreFormFromFooter = function (formId) {
    var stored = [];
    try { stored = JSON.parse(sessionStorage.getItem('minimizedForms') || '[]'); } catch (e) {}
    var info = null;
    for (var i = 0; i < stored.length; i++) { if (stored[i].id === formId) { info = stored[i]; break; } }
    if (info && info.url) {
        _minimizedForms.delete(formId);
        sessionStorage.setItem('minimizedForms', JSON.stringify(stored.filter(function (f) { return f.id !== formId; })));
        window.location.href = info.url;
    } else {
        var ov = document.getElementById(formId);
        if (ov) { ov.style.display = 'flex'; _minimizedForms.delete(formId); _renderMinimized(); }
    }
};
window.closeFormFromFooter = function (formId) {
    _minimizedForms.delete(formId);
    var stored = [];
    try { stored = JSON.parse(sessionStorage.getItem('minimizedForms') || '[]'); } catch (e) {}
    sessionStorage.setItem('minimizedForms', JSON.stringify(stored.filter(function (f) { return f.id !== formId; })));
    _renderMinimized();
};
function _renderMinimized() {
    var c = document.getElementById('minimizedFormsContainer');
    if (!c) return;
    c.innerHTML = '';
    _minimizedForms.forEach(function (d, id) {
        var el = document.createElement('div');
        el.className = 'minimized-form-item';
        el.innerHTML =
            '<span class="minimized-form-icon">'  + d.icon  + '</span>' +
            '<span class="minimized-form-title">' + d.title + '</span>' +
            '<div class="minimized-form-actions">' +
                '<button class="minimized-form-btn expand" onclick="restoreFormFromFooter(\'' + id + '\')">⬆</button>' +
                '<button class="minimized-form-btn close"  onclick="closeFormFromFooter(\''  + id + '\')">✕</button>' +
            '</div>';
        c.appendChild(el);
    });
}
document.addEventListener('DOMContentLoaded', function () {
    var stored = [];
    try { stored = JSON.parse(sessionStorage.getItem('minimizedForms') || '[]'); } catch (e) {}
    stored.forEach(function (f) { _minimizedForms.set(f.id, { title: f.title, icon: f.icon, url: f.url }); });
    _renderMinimized();
});

/* ── KEYBOARD ──────────────────────────────────────────────── */
document.addEventListener('keydown', function (e) {
    if ((e.ctrlKey || e.metaKey) && e.key === 'b') { e.preventDefault(); toggleSidebar(); }
});

/* ── UTILS ─────────────────────────────────────────────────── */
function getCsrfToken() {
    var m = document.cookie.match(/csrftoken=([^;]+)/);
    return m ? decodeURIComponent(m[1]) : '';
}
function debounce(fn, wait) {
    var timer;
    return function () {
        var a = arguments, ctx = this;
        clearTimeout(timer);
        timer = setTimeout(function () { fn.apply(ctx, a); }, wait);
    };
}