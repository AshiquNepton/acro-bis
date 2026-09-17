/**
 * common/static/common/js/prefetch.js
 *
 * Global prefetch system.
 *
 * HOW IT WORKS
 * ────────────
 * 1. The Django view sets window.PAGE_PREFETCH (injected via template).
 * 2. On DOMContentLoaded this script fires ALL URLs in parallel.
 * 3. Loader stays up the whole time, hides once every promise settles.
 * 4. Results land in window.prefetchCache[url] = parsed JSON.
 * 5. Any module fetch function calls pfCacheGet(url) first — if it hits,
 *    no network request is made.
 *
 * PAGE_PREFETCH format (set by Django view in template):
 *   window.PAGE_PREFETCH = [
 *     '/hrms/employee/lookup/?field=RegNo&value=123',
 *     '/hrms/employee/report-to-options/?exclude=123',
 *     '/hrms/employee/dependents/EMP001/',
 *   ];
 *
 * Module usage:
 *   var cached = pfCacheGet(url);
 *   if (cached) { useData(cached); return; }
 *   fetch(url).then(...);
 *
 * Include in base.html AFTER loader.js, BEFORE any module JS:
 *   <script src="{% static 'common/js/prefetch.js' %}"></script>
 */

(function () {
    'use strict';

    /* ── Public cache store ──────────────────────────────────────────────── */
    window.prefetchCache = window.prefetchCache || {};

    /**
     * pfCacheGet — read a cached response.
     * Returns parsed JSON object if cached, null otherwise.
     */
    window.pfCacheGet = function (url) {
        if (!url) return null;
        var hit = window.prefetchCache[url];
        return hit !== undefined ? hit : null;
    };

    /**
     * pfCacheSet — store a response manually (used by modules that want
     * to warm the cache for follow-up calls, e.g. after a save).
     */
    window.pfCacheSet = function (url, data) {
        if (url) window.prefetchCache[url] = data;
    };

    /**
     * pfCacheClear — invalidate one URL or the whole cache.
     * Call after saves/deletes so stale data is not served.
     */
    window.pfCacheClear = function (url) {
        if (url) {
            delete window.prefetchCache[url];
        } else {
            window.prefetchCache = {};
        }
    };

    /* ── Core prefetch runner ────────────────────────────────────────────── */
    function _runPrefetch() {
        var urls = window.PAGE_PREFETCH;

        /* Nothing declared — just hide the loader and exit */
        if (!Array.isArray(urls) || !urls.length) {
            if (window.erpLoader) window.erpLoader.hide();
            return;
        }

        /* Loader is already visible (shown by the HTML overlay on page load).
           Keep it up — hide only after every fetch settles.                 */
        if (window.erpLoader) window.erpLoader.show('Loading…');

        var total   = urls.length;
        var settled = 0;

        function _tick() {
            settled++;
            if (settled >= total) {
                if (window.erpLoader) window.erpLoader.hide();
                /* Dispatch event so modules can react after prefetch done */
                document.dispatchEvent(new CustomEvent('prefetch:done'));
            }
        }

        urls.forEach(function (url) {
            /* Skip if already cached (e.g. hot-module reload) */
            if (window.prefetchCache[url] !== undefined) {
                _tick();
                return;
            }

            fetch(url, { credentials: 'same-origin' })
                .then(function (r) {
                    if (!r.ok) throw new Error('HTTP ' + r.status);
                    return r.json();
                })
                .then(function (data) {
                    window.prefetchCache[url] = data;
                })
                .catch(function (err) {
                    console.warn('[prefetch] failed:', url, err);
                    /* Store null so pfCacheGet returns null → fallback fetch */
                    window.prefetchCache[url] = null;
                })
                .finally(function () {
                    _tick();
                });
        });
    }

    /* ── Run on DOMContentLoaded ─────────────────────────────────────────── */
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', _runPrefetch);
    } else {
        _runPrefetch();
    }

}());