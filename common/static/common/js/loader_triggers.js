/**
 * common/static/common/js/loader_triggers.js  v2.0
 *
 * Shows the loader ONLY for user-triggered navigation events:
 *   • clicking <a> links that navigate away
 *   • submitting <form> elements (traditional full-page submits)
 *   • browser back / forward (popstate)
 *   • tab/window close (beforeunload)
 *   • bfcache restore (pageshow)
 *
 * REMOVED in v2.0:
 *   • fetch() patch   — data fetches are handled by prefetch.js
 *   • XMLHttpRequest patch — same reason
 *
 * This means the loader no longer flickers on every API call.
 * Modules that want a loader during a specific user action (save, delete)
 * call erpLoader.show/hide directly — as they already do.
 *
 * Include AFTER loader.js in base.html:
 *   <script src="{% static 'common/js/loader.js' %}"></script>
 *   <script src="{% static 'common/js/loader_triggers.js' %}"></script>
 */

(function () {
    'use strict';

    function show(msg) {
        if (window.erpLoader) window.erpLoader.show(msg || '');
    }

    function hide() {
        if (window.erpLoader) window.erpLoader.hide();
    }

    /* ── Should we show the loader for this <a> href? ────────────────────
       Skip:
         • empty / hash-only anchors  (#section)
         • javascript: links
         • external URLs (different origin)
         • links with download attribute
         • links that open in a new tab / window
    ──────────────────────────────────────────────────────────────────── */
    function shouldShowForLink(anchor) {
        var href = anchor.getAttribute('href') || '';
        if (!href || href.startsWith('#') || href.startsWith('javascript:')) return false;
        if (anchor.hasAttribute('download')) return false;
        if (anchor.target === '_blank' || anchor.target === '_new') return false;
        try {
            var url = new URL(href, window.location.href);
            if (url.origin !== window.location.origin) return false;
            if (url.pathname === window.location.pathname &&
                url.search  === window.location.search  &&
                url.hash    !== '') return false;
        } catch (e) {
            return false;
        }
        return true;
    }

    /* ── 1. Link clicks ──────────────────────────────────────────────── */
    document.addEventListener('click', function (e) {
        var anchor = e.target.closest('a[href]');
        if (!anchor) return;
        if (e.defaultPrevented || e.ctrlKey || e.metaKey || e.shiftKey) return;
        if (shouldShowForLink(anchor)) show('');
    }, true);

    /* ── 2. Form submits (traditional full-page only) ────────────────── */
    document.addEventListener('submit', function (e) {
        if (e.defaultPrevented) return;
        show('Saving…');
    }, true);

    /* ── 3. Browser back / forward ───────────────────────────────────── */
    window.addEventListener('popstate', function () {
        show('');
    });

    /* ── 4. Page unload / hard navigation ────────────────────────────── */
    window.addEventListener('beforeunload', function () {
        show('');
    });

    /* ── 5. bfcache restore — hide if loader was left visible ────────── */
    window.addEventListener('pageshow', function (e) {
        if (e.persisted) hide();
    });

}());