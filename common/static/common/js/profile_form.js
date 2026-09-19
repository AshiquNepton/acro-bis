/**
 * â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
 *  common/static/common/js/profile_form.js   v4.5
 *
 *  v4.5 fixes:
 *  â‘£ LOADER FLICKER â€” replaced the ref-counted _loaderStart/_loaderDone
 *    pair (which caused showâ†’hideâ†’showâ†’hide when lookup + depLoad ran
 *    back-to-back) with a single persistent overlay during the full
 *    page-init sequence. The overlay now shows ONCE when the auto-load
 *    starts and hides ONCE when every queued async operation is settled.
 *    A _batchComplete() gate ensures the overlay only drops after both
 *    the lookup fetch and any onPopulate-triggered sub-loads (e.g.
 *    depLoad) have finished. Interactive saves/deletes still use the
 *    simpler erpLoader.show/hide directly â€” no flicker there because
 *    they are single sequential operations.
 *
 *  v4.4 fixes:
 *  â‘  DOUBLE LOAD  â€” blur listener now guards with _lookupInFlight flag.
 *  â‘¡ DROPDOWN REVERSE-POPULATION â€” pfPopulate calls pfSelSetValue().
 *  â‘¢ URL CLEANUP ON NEW â€” pfClear calls history.replaceState.
 *
 *  v4.3 adds:
 *  - pfActSave: full client-side required-field validation before
 *    the fetch. Marks bad fields red, injects inline error message,
 *    shakes + scrolls the first bad field, switches to the correct
 *    tab, shows a showToast() warning listing missing field labels.
 *    Errors clear automatically on next input/change.
 *
 *  v4.2 fixes:
 *  - pfPopulate: per-field try/catch so one bad selector doesn't abort
 *  - pfPopulate: supports data.photo directly (FTP path)
 *  - pfLookupNow: checks r.ok before r.json()
 * â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
 */

(function () {
    'use strict';

    /* â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
       SVG ICON REGISTRY
    â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€*/
    var PF_ICONS = (function () {
        function svg(paths) {
            return '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" ' +
                'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">' +
                paths + '</svg>';
        }
        return {
            'Close': svg('<line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>'),
            'Save': svg('<path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/><polyline points="17 21 17 13 7 13 7 21"/><polyline points="7 3 7 8 15 8"/>'),
            'New': svg('<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="12" y1="18" x2="12" y2="12"/><line x1="9" y1="15" x2="15" y2="15"/>'),
            'Delete': svg('<polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/><path d="M10 11v6"/><path d="M14 11v6"/><path d="M9 6V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2"/>'),
            'Print': svg('<polyline points="6 9 6 2 18 2 18 9"/><path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"/><rect x="6" y="14" width="12" height="8"/>'),
            'Search': svg('<circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>'),
            'Refresh': svg('<polyline points="23 4 23 10 17 10"/><polyline points="1 20 1 14 7 14"/><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/>'),
            'Export': svg('<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/>'),
            'Import': svg('<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/>'),
            'Add': svg('<circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="16"/><line x1="8" y1="12" x2="16" y2="12"/>'),
            'Remove': svg('<circle cx="12" cy="12" r="10"/><line x1="8" y1="12" x2="16" y2="12"/>'),
            'Change': svg('<path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>'),
            'Edit': svg('<path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>'),
            'View': svg('<path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/>'),
            'Approve': svg('<polyline points="20 6 9 17 4 12"/>'),
            'Reject': svg('<circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/>'),
            'Cancel': svg('<circle cx="12" cy="12" r="10"/><line x1="4.93" y1="4.93" x2="19.07" y2="19.07"/>'),
            'Submit': svg('<line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/>'),
            'Confirm': svg('<polyline points="9 11 12 14 22 4"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/>'),
            'Back': svg('<line x1="19" y1="12" x2="5" y2="12"/><polyline points="12 19 5 12 12 5"/>'),
            'Forward': svg('<line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/>'),
            'Settings': svg('<circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/>'),
            'Default': svg('<circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/>'),
            'Design': svg('<circle cx="13.5" cy="6.5" r="0.5" fill="currentColor"/><circle cx="17.5" cy="10.5" r="0.5" fill="currentColor"/><circle cx="8.5" cy="7.5" r="0.5" fill="currentColor"/><circle cx="6.5" cy="12.5" r="0.5" fill="currentColor"/><path d="M12 2C6.5 2 2 6.5 2 12s4.5 10 10 10c.926 0 1.648-.746 1.648-1.688 0-.437-.18-.835-.437-1.125-.29-.289-.438-.652-.438-1.125a1.64 1.64 0 0 1 1.668-1.668h1.996c3.051 0 5.555-2.503 5.555-5.554C21.965 6.012 17.461 2 12 2z"/>'),
            'Theme': svg('<circle cx="13.5" cy="6.5" r="0.5" fill="currentColor"/><circle cx="17.5" cy="10.5" r="0.5" fill="currentColor"/><circle cx="8.5" cy="7.5" r="0.5" fill="currentColor"/><circle cx="6.5" cy="12.5" r="0.5" fill="currentColor"/><path d="M12 2C6.5 2 2 6.5 2 12s4.5 10 10 10c.926 0 1.648-.746 1.648-1.688 0-.437-.18-.835-.437-1.125-.29-.289-.438-.652-.438-1.125a1.64 1.64 0 0 1 1.668-1.668h1.996c3.051 0 5.555-2.503 5.555-5.554C21.965 6.012 17.461 2 12 2z"/>'),
            'Utilities': svg('<path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/>'),
            'Tools': svg('<path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/>'),
            'Visa': svg('<rect x="2" y="5" width="20" height="14" rx="2"/><line x1="2" y1="10" x2="22" y2="10"/><line x1="6" y1="15" x2="6.01" y2="15"/><line x1="10" y1="15" x2="14" y2="15"/>'),
            'Passport': svg('<path d="M4 4a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v16a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V4z"/><circle cx="12" cy="10" r="3"/><path d="M7 20s.5-3 5-3 5 3 5 3"/>'),
            'Report': svg('<line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/>'),
            'History': svg('<polyline points="12 8 12 12 14 14"/><path d="M3.05 11a9 9 0 1 1 .5 4"/><polyline points="3 16 3 11 8 11"/>'),
            'Lock': svg('<rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/>'),
            'Unlock': svg('<rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 9.9-1"/>'),
            'Email': svg('<path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/>'),
            'Logout': svg('<path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/>'),
            'Menu': svg('<line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="18" x2="21" y2="18"/>'),
            'Filter': svg('<polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"/>'),
            'Upload': svg('<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/>'),
            'Download': svg('<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/>'),
            'Note': svg('<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/>'),
            'Attach': svg('<path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48"/>'),
            'Copy': svg('<rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>'),
            'Documents': svg('<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/>'),
        };
    }());

    var _pendingFiles = {};

    /* â”€â”€ Batch-gate loader  (v4.5) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
       Eliminates the showâ†’hideâ†’showâ†’hide flicker that occurred when the
       page-init sequence ran lookup + onPopulate sub-loads back-to-back.

       HOW IT WORKS
       â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
       â€¢ _batchOpen(n, msg)  â€” show overlay once; register n "slots" to fill
       â€¢ _batchTick()        â€” call once per completed async operation;
                               hides overlay only when ALL slots are done
       â€¢ _loaderStart(msg)   â€” convenience: open a 1-slot batch
       â€¢ _loaderDone()       â€” convenience: tick the current batch

       The lookup flow uses _batchOpen(2) for "lookup + depLoad" so the
       overlay stays up across both fetches and drops only when both finish:

           pfLookupNow()           â†’ _batchOpen(2, 'Loadingâ€¦')
           lookup fetch done       â†’ pfPopulate â†’ onPopulate â†’ depLoad start
           lookup slot             â†’ _batchTick()   (count 2â†’1, stays up)
           depLoad fetch done      â†’ _batchTick()   (count 1â†’0, hides)

       For simple single operations (save, delete) callers use
       erpLoader.show/hide directly â€” no batch needed.
    â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */
    var _batchTotal = 0;   /* total slots registered in current batch */
    var _batchPending = 0;   /* how many slots are still outstanding     */

    function _batchOpen(slots, msg) {
        _batchTotal = slots || 1;
        _batchPending = _batchTotal;
        if (window.erpLoader) erpLoader.show(msg || 'Loadingâ€¦');
    }

    function _batchTick() {
        _batchPending = Math.max(0, _batchPending - 1);
        if (_batchPending === 0 && window.erpLoader) erpLoader.hide();
    }

    /* Legacy-compatible single-slot wrappers used by onPopulate callers
       (e.g. depLoad) that call _loaderStart / _loaderDone directly.
       These are intentionally NON-additive â€” they reuse the existing batch
       slot rather than opening a new one, preventing double-hide.         */
    function _loaderStart(msg) {
        /* If a batch is already open (from pfLookupNow), just update the
           message â€” don't open a new overlay or add to the slot count.   */
        if (_batchPending > 0) {
            if (window.erpLoader && msg) erpLoader.show(msg);
            return;
        }
        /* No active batch â€” open a fresh 1-slot batch */
        _batchOpen(1, msg);
    }

    function _loaderDone() {
        _batchTick();
    }

    window._loaderStart = _loaderStart;
    window._loaderDone = _loaderDone;

    /* â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
       FIX â‘   â€” in-flight guard prevents the blur listener from
       triggering a second lookup while an auto-load (or manual
       input-debounce) fetch is already running.
    â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€*/
    var _lookupInFlight = {};   /* { formId: true } while a fetch is pending */

    /* â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
       INIT
    â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€*/
    var _initialised = {};

    function _pfInit() {
        var configs = window._pfConfig || {};
        Object.keys(configs).forEach(function (formId) {
            if (_initialised[formId]) return;
            _initialised[formId] = true;
            _initForm(formId, configs[formId]);
        });
    }

    document.addEventListener('DOMContentLoaded', _pfInit);

    window.pfRegister = function (formId, cfg) {
        window._pfConfig = window._pfConfig || {};
        window._pfConfig[formId] = cfg;

        if (document.readyState !== 'loading') {
            if (!_initialised[formId]) {
                _initialised[formId] = true;
                _initForm(formId, cfg);
            }
        }
    };
    document.addEventListener('DOMContentLoaded', function () {
        var regEl = document.getElementById('id_reg_no');
        if (!regEl) return;
        // Replace the element to strip all event listeners added by _initLookup
        var clone = regEl.cloneNode(true);
        regEl.parentNode.replaceChild(clone, regEl);
    });
    

    window.pfInit = _pfInit;

    function _wrapColumns(paneEl) {
        if (!paneEl) return;
        var grids = paneEl.querySelectorAll('.pf-field-grid[data-col-sizes]');
        grids.forEach(function (grid) {
            if (grid.querySelector('.pf-col')) return;
            var sizes = (grid.dataset.colSizes || '').split(',').map(Number).filter(Boolean);
            if (!sizes.length) return;
            var children = Array.prototype.slice.call(grid.children);
            if (!children.length) return;
            var colDivs = sizes.map(function () {
                var d = document.createElement('div');
                d.className = 'pf-col';
                return d;
            });
            var childIdx = 0;
            sizes.forEach(function (size, colIdx) {
                for (var i = 0; i < size && childIdx < children.length; i++, childIdx++) {
                    colDivs[colIdx].appendChild(children[childIdx]);
                }
            });
            colDivs.forEach(function (col) { grid.appendChild(col); });
        });
    }

    function _initForm(formId, cfg) {
        var formEl = document.getElementById(formId);
        if (!formEl) return;
        var realBox = document.getElementById('pf-avatar-box-' + formId);
        var fallbacks = document.querySelectorAll('#pf-hero-' + formId + ' .pf-hero-photo--hero-fallback');
        fallbacks.forEach(function (fb) {
            if (realBox && realBox !== fb) {
                fb.style.display = 'none';
                var nxt = fb.nextElementSibling;
                if (nxt && nxt.tagName === 'INPUT' && nxt.type === 'file') nxt.style.display = 'none';
            } else if (!realBox) {
                fb.id = 'pf-avatar-box-' + formId;
                fb.style.display = '';
            }
        });
        _initLookup(formId, cfg, formEl);
        _initHeroLive(formId, cfg, formEl);
        _initEnterKey(formId, formEl);
        _updateHero(formId, cfg, formEl);
        _initToolbarSearch(formId, cfg);
        var firstPane = document.querySelector('#pf-content-' + formId + ' .pf-pane.active');
        _wrapColumns(firstPane);
        var avatarImg = document.getElementById('pf-avatar-img-' + formId);
        if (avatarImg && avatarImg.getAttribute('src')) {
            avatarImg.style.display = 'block';
            var ph = document.getElementById('pf-avatar-ph-' + formId);
            if (ph) ph.style.display = 'none';
        }
    }

    /* â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
       TAB SWITCH
    â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€*/
    window.pfTab = function (formId, tabId, navEl) {
        document.querySelectorAll('#pf-content-' + formId + ' .pf-pane').forEach(function (p) {
            p.classList.remove('active');
        });
        var pane = document.getElementById('pf-pane-' + formId + '-' + tabId);
        if (pane) { pane.classList.add('active'); _wrapColumns(pane); }
        document.querySelectorAll('#pf-tabs-' + formId + ' .pf-tab').forEach(function (t) {
            t.classList.remove('active');
        });
        var tab = document.getElementById('pf-tab-' + formId + '-' + tabId);
        if (tab) tab.classList.add('active');
        var nav = document.getElementById('pf-sidenav-' + formId);
        if (nav) {
            nav.querySelectorAll('.pf-sidenav-item').forEach(function (n) { n.classList.remove('active'); });
            var activeNav = navEl || document.getElementById('pf-nav-' + formId + '-' + tabId);
            if (activeNav) activeNav.classList.add('active');
        }
    };

    /* â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
       LOOKUP  v4.4
       FIX â‘ : _lookupInFlight[formId] is set true before the fetch
       and cleared (false) in both .then() and .catch(). The blur
       listener checks this flag before firing so the ?id= auto-load
       path (input event â†’ debounce â†’ pfLookupNow) doesn't get a
       second duplicate call from the subsequent blur.
    â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€*/
    window.pfLookupNow = function (formId) {
        var cfg = _cfg(formId);
        var formEl = _form(formId);
        if (!cfg || !formEl) {
            console.warn('[pfLookupNow] cfg or formEl missing for formId:', formId);
            return;
        }
        var lookupUrl = (cfg.lookupUrl || '').trim();
        if (!lookupUrl) {
            console.warn('[pfLookupNow] lookupUrl is empty for formId:', formId);
            return;
        }
        var keyEl = formEl.querySelector('[name="' + cfg.lookupField + '"]');
        if (!keyEl || !keyEl.value.trim()) return;

        /* â”€â”€ FIX â‘ : guard against concurrent duplicate fetches â”€â”€ */
        if (_lookupInFlight[formId]) return;
        _lookupInFlight[formId] = true;

        /* â”€â”€ FIX â‘£: open a batch with the right slot count â”€â”€â”€â”€â”€â”€
           If cfg.onPopulate is defined it will likely trigger a
           sub-load (e.g. depLoad) which calls _loaderStart itself.
           Opening 2 slots means the overlay stays up across both
           the lookup fetch AND the sub-load fetch.
           If there is no onPopulate, 1 slot is enough.            */
        var hasOnPopulate = cfg && typeof cfg.onPopulate === 'function';
        _batchOpen(hasOnPopulate ? 2 : 1, 'Loadingâ€¦');

        fetch(lookupUrl
            + '?field=' + encodeURIComponent(cfg.lookupDbField || cfg.lookupField)
            + '&value=' + encodeURIComponent(keyEl.value))
            .then(function (r) {
                if (!r.ok) {
                    return r.text().then(function (t) {
                        console.error('[pfLookup] HTTP ' + r.status + ':', t.substring(0, 500));
                        throw new Error('HTTP ' + r.status);
                    });
                }
                return r.json();
            })
            .then(function (d) {
                _lookupInFlight[formId] = false;   /* â† clear flag */
                if (d.success && d.data) {
                    pfPopulate(formId, d.data);
                    keyEl.classList.add('pf-found');
                    keyEl.classList.remove('pf-notfound');
                    _toast('Record loaded', 's');
                } else {
                    keyEl.classList.add('pf-notfound');
                    keyEl.classList.remove('pf-found');
                    _toast(d.error || 'Record not found', 'w');
                    /* No sub-load will run â€” consume the extra slot if opened */
                    if (hasOnPopulate) _batchTick();
                }
                /* Tick the lookup slot â€” overlay hides only when all slots done */
                _batchTick();
            })
            .catch(function (err) {
                _lookupInFlight[formId] = false;   /* â† clear flag on error too */
                /* Drain all pending slots so overlay never gets stuck */
                _batchPending = 0;
                if (window.erpLoader) erpLoader.hide();
                console.error('[pfLookup] error:', err);
                _toast('Lookup failed â€” check browser console (F12)', 'e');
            });
    };

    function _initLookup(formId, cfg, formEl) {
        var lookupField = (cfg && cfg.lookupField) || '';
        if (!lookupField) {
            setTimeout(function () {
                var lateCfg = _cfg(formId);
                if (lateCfg && lateCfg.lookupField) _initLookup(formId, lateCfg, formEl);
            }, 0);
            return;
        }
        var keyEl = formEl.querySelector('[name="' + lookupField + '"]');
        if (!keyEl) return;
        var timer;
        keyEl.addEventListener('input', function () {
            clearTimeout(timer);
            if (!keyEl.value.trim()) return;
            var delay = (_cfg(formId) || {}).debounce;
            delay = (delay !== undefined) ? delay : 500;
            timer = setTimeout(function () { pfLookupNow(formId); }, delay);
        });
        keyEl.addEventListener('blur', function () {
            /* FIX â‘ : skip blur-triggered lookup if one is already in flight */
            if (_lookupInFlight[formId]) return;
            var liveCfg = _cfg(formId);
            if (!liveCfg || !(liveCfg.lookupUrl || '').trim()) return;
            if (keyEl.value.trim()) pfLookupNow(formId);
        });
    }

    /* â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
       POPULATE  v4.4
       FIX â‘¡: After setting native <select>.value, call pfSelSetValue()
       so the pf_select.js custom dropdown UI also reflects the new
       value. Without this the trigger label stays at "Selectâ€¦" even
       though the underlying <select> has the correct value.
    â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€*/
    window.pfPopulate = function (formId, data) {
        var formEl = _form(formId);
        if (!formEl) return;

        /* Fields listed here are skipped in the generic loop and handled
           exclusively by the cfg.onPopulate callback (e.g. photo â†’ FTP proxy). */
        var cfg_early = _cfg(formId);
        var excluded = (cfg_early && cfg_early.excludeFromPopulate) || [];

        Object.keys(data).forEach(function (k) {
            try {
                var v = data[k];
                /* â”€â”€ FIX â‘¡: skip fields owned by onPopulate (e.g. 'photo') â”€â”€ */
                if (excluded.indexOf(k) !== -1) return;
                var el = formEl.querySelector('[name="' + k + '"]');
                if (!el || el.name === 'csrfmiddlewaretoken') return;

                if (el.type === 'checkbox') {
                    el.checked = !!v;
                } else {
                    el.value = (v !== null && v !== undefined) ? v : '';

                    /* â”€â”€ FIX â‘¡: sync the pf_select.js custom UI â”€â”€ */
                    if (el.tagName === 'SELECT' && el.getAttribute('data-upgraded') === '1') {
                        if (typeof window.pfSelSetValue === 'function') {
                            window.pfSelSetValue(el.name || el.id, String(v !== null && v !== undefined ? v : ''));
                        }
                    }
                }

                /* Clear any lingering invalid mark when data is loaded */
                var wrapper = el.closest('.pf-field') || el.closest('.pf-hf-cell');
                if (wrapper) _pfClearInvalid(wrapper);
            } catch (e) {
                console.warn('[pfPopulate] skipped field "' + k + '":', e.message);
            }
        });

        var isNewEl = formEl.querySelector('[name="_is_new"]');
        if (isNewEl) isNewEl.value = '0';

        _updateHero(formId, _cfg(formId), formEl);

        var cfg = _cfg(formId);

        var hasOnPopulate = cfg && typeof cfg.onPopulate === 'function';

        if (cfg && cfg.heroPhotoField && !hasOnPopulate) {
            var photoSrc = data[cfg.heroPhotoField + '_url'] || data[cfg.heroPhotoField] || '';
            var isFetchable = photoSrc && (
                photoSrc.indexOf('http') === 0 ||
                photoSrc.indexOf('blob:') === 0 ||
                photoSrc.indexOf('data:') === 0 ||
                photoSrc.indexOf('/static/') === 0
            );
            if (isFetchable) {
                var img = document.getElementById('pf-avatar-img-' + formId);
                if (img) { img.src = photoSrc; img.style.display = 'block'; }
                var ph2 = document.getElementById('pf-avatar-ph-' + formId);
                if (ph2) ph2.style.display = 'none';
            }
        }

        if (hasOnPopulate) {
            try { cfg.onPopulate(data); } catch (e) { console.error('[pfPopulate] onPopulate threw:', e); }
        }
    };

    /* â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
       HERO LIVE UPDATE
    â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€*/
    function _updateHero(formId, cfg, formEl) {
        if (!cfg) return;
        function _val(fieldName) {
            if (!fieldName) return '';
            try {
                var el = formEl ? formEl.querySelector('[name="' + fieldName + '"]') : null;
                if (!el) return '';
                if (el.tagName === 'SELECT') return el.options[el.selectedIndex] ? el.options[el.selectedIndex].text : '';
                return el.value || '';
            } catch (e) { return ''; }
        }
        _setText('pf-display-name-' + formId, _val(cfg.heroNameField) || (cfg.heroDefaultName || 'New Record'));
        _setText('pf-display-row1-' + formId, _val(cfg.heroRow1Field) || 'â€”');
        _setText('pf-display-row2-' + formId, _val(cfg.heroRow2Field) || 'â€”');
        _setText('pf-display-sub-' + formId, _val(cfg.heroSubField) || 'â€”');
    }

    window.pfUpdateHero = function (formId) {
        var cfg = _cfg(formId); var formEl = _form(formId);
        if (cfg && formEl) _updateHero(formId, cfg, formEl);
    };

    function _initHeroLive(formId, cfg, formEl) {
        var watch = [cfg.heroNameField, cfg.heroRow1Field, cfg.heroRow2Field, cfg.heroSubField].filter(Boolean);
        watch.forEach(function (name) {
            try {
                var el = formEl.querySelector('[name="' + name + '"]');
                if (!el) return;
                el.addEventListener('input', function () { _updateHero(formId, cfg, formEl); });
                el.addEventListener('change', function () { _updateHero(formId, cfg, formEl); });
            } catch (e) { /* skip */ }
        });
    }




    /* â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
   TOOLBAR SEARCH
   Activated when fc.search is set in the Django form_config dict.
   Wired automatically by pfInitToolbarSearch(formId) which is
   called from _initForm() if the input element is present.

   Public API:
     pfTbToggleSearchDrop(formId)              â€” open/close field dropdown
     pfTbSetSearchField(formId, key, lbl, el)  â€” pick a search field
     pfTbSearchClear(formId)                   â€” clear input + re-run
â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â• */

    /* Per-form search state */
    var _tbSearch = {};   /* formId â†’ { field:'', timer:null, onSearch:fn } */

    /**
     * Called from _initForm() when the toolbar search input exists.
     * cfg.search.onSearch(query, field, formId) â€” caller-supplied handler.
     */
    function _initToolbarSearch(formId, cfg) {
        var input = document.getElementById('pf-tb-search-' + formId);
        if (!input) return;

        _tbSearch[formId] = {
            field: '',
            timer: null,
            onSearch: (cfg.search && typeof cfg.search.onSearch === 'function')
                ? cfg.search.onSearch
                : null,
        };

        /* Show/hide clear button and fire search on every keystroke */
        input.addEventListener('input', function () {
            var clearBtn = document.getElementById('pf-tb-sclear-' + formId);
            if (clearBtn) clearBtn.style.display = input.value ? 'inline-flex' : 'none';

            clearTimeout(_tbSearch[formId].timer);
            var delay = (cfg.search && cfg.search.debounce != null)
                ? cfg.search.debounce : 300;
            _tbSearch[formId].timer = setTimeout(function () {
                _runTbSearch(formId, input.value.trim());
            }, delay);
        });

        /* Close field dropdown when clicking outside */
        document.addEventListener('click', function (e) {
            var wrap = document.getElementById('pf-tb-search-wrap-' + formId);
            var drop = document.getElementById('pf-tb-sfdrop-' + formId);
            if (wrap && drop && !wrap.contains(e.target)) drop.style.display = 'none';
        });
    }

    function _runTbSearch(formId, query) {
        var st = _tbSearch[formId];
        if (!st) return;
        if (typeof st.onSearch === 'function') {
            st.onSearch(query, st.field, formId);
        }
        /* Also dispatch a custom event so external code can listen */
        var input = document.getElementById('pf-tb-search-' + formId);
        if (input) {
            input.dispatchEvent(new CustomEvent('pf:search', {
                bubbles: true,
                detail: { query: query, field: st.field, formId: formId }
            }));
        }
    }

    window.pfTbToggleSearchDrop = function (formId) {
        var drop = document.getElementById('pf-tb-sfdrop-' + formId);
        if (!drop) return;
        var open = drop.style.display !== 'none';
        /* Close every other open search-drop first */
        document.querySelectorAll('.pf-tb-search-drop').forEach(function (d) {
            d.style.display = 'none';
        });
        drop.style.display = open ? 'none' : 'block';
    };

    window.pfTbSetSearchField = function (formId, fieldKey, fieldLabel, el) {
        var st = _tbSearch[formId];
        if (!st) return;
        st.field = fieldKey;

        var lbl = document.getElementById('pf-tb-sflabel-' + formId);
        if (lbl) lbl.textContent = fieldLabel || 'All';

        var drop = document.getElementById('pf-tb-sfdrop-' + formId);
        if (drop) {
            drop.querySelectorAll('.pf-tb-search-drop-item').forEach(function (it) {
                it.classList.toggle('active', it === el);
            });
            drop.style.display = 'none';
        }

        /* Re-run current query against the new field immediately */
        var input = document.getElementById('pf-tb-search-' + formId);
        if (input) _runTbSearch(formId, input.value.trim());
    };

    window.pfTbSearchClear = function (formId) {
        var input = document.getElementById('pf-tb-search-' + formId);
        var clearBtn = document.getElementById('pf-tb-sclear-' + formId);
        if (input) { input.value = ''; input.focus(); }
        if (clearBtn) clearBtn.style.display = 'none';
        _runTbSearch(formId, '');
    };

    /** Read the current search query from anywhere */
    window.pfTbSearchQuery = function (formId) {
        var input = document.getElementById('pf-tb-search-' + formId);
        return input ? input.value.trim() : '';
    };
    window.pfTbSearchField = function (formId) {
        return (_tbSearch[formId] || {}).field || '';
    };

    /* â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
       CLEAR  v4.4
       FIX â‘¢: Strip ?id= (and any other query params) from the URL
       via history.replaceState so "New" resets the address bar to
       the clean /new/ path without a page reload.
       FIX â‘¡: Reset every upgraded pf_select dropdown to its first
       option so the trigger label doesn't keep the previous value.
    â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€*/
    window.pfClear = function (formId, keepFields) {
        var formEl = _form(formId);
        if (!formEl) return;
        var keep = Array.isArray(keepFields) ? keepFields : (keepFields ? [keepFields] : []);
        formEl.querySelectorAll('input, select, textarea').forEach(function (el) {
            if (keep.indexOf(el.name) !== -1 || el.name === 'csrfmiddlewaretoken') return;
            if (el.name === '_is_new') {
                el.value = '1';
                return;
            }
            if (el.type === 'checkbox' || el.type === 'radio') {
                el.checked = false;
            } else if (el.tagName === 'SELECT') {
                el.selectedIndex = 0;
            } else {
                el.value = '';
            }
        });
        formEl.querySelectorAll('.pf-found, .pf-notfound').forEach(function (el) {
            el.classList.remove('pf-found', 'pf-notfound');
        });
        _pfClearAllInvalid(formEl);
        var img = document.getElementById('pf-avatar-img-' + formId);
        if (img) { img.src = ''; img.style.display = 'none'; }
        var ph = document.querySelector('#pf-avatar-box-' + formId + ' .pf-hero-photo-ph');
        if (ph) ph.style.display = '';
        _pendingFiles = {};
        _updateHero(formId, _cfg(formId), formEl);

        /* â”€â”€ FIX â‘¢: strip ?id= from the URL without a page reload â”€â”€ */
        try {
            if (window.location.search) {
                history.replaceState(null, '', window.location.pathname);
            }
        } catch (e) { /* ignore in environments where history API is unavailable */ }

        
        if (formEl) {
            formEl.dispatchEvent(new CustomEvent('pf:reset', { bubbles: true }));
        }
    };

    /* â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
       BROWSE BUTTON
    â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€*/
    window.pfBrowsePicked = function (fieldName, input) {
        if (!input.files || !input.files[0]) return;
        var file = input.files[0];
        var textEl = document.getElementById('id_' + fieldName);
        if (textEl) {
            textEl.value = file.name;
            textEl.dispatchEvent(new Event('change', { bubbles: true }));
        }
        _pendingFiles[fieldName] = file;
    };

    /* â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
       STANDARD ACTION HANDLERS
    â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€*/
    window.pfActClose = function (formId) { history.back(); };

    window.pfActNew = function (formId) {
        _confirm('Clear the form for a new record? Unsaved changes will be lost.',
            function (ok) { if (ok) pfClear(formId || _firstFormId()); },
            'warning', 'New Record', 'Yes, clear', 'Cancel');
    };

    /* â”€â”€ v4.3: pfActSave â€” full required-field validation â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */
    window.pfActSave = function (formId) {
        var fid = formId || _firstFormId();
        var formEl = _form(fid);
        var cfg = _cfg(fid);
        if (!formEl) return;
        if (!cfg || !cfg.saveUrl) {
            _alert('Save URL is not configured.', 'error', 'Configuration Error');
            return;
        }

        var badFields = _pfValidate(formEl);

        if (badFields.length) {
            badFields.forEach(function (info, idx) {
                _pfMarkInvalid(info.el, info.label, fid, idx === 0);
            });
            var labels = badFields.map(function (i) { return i.label; });
            var msg = labels.length === 1
                ? '"' + labels[0] + '" is required.'
                : labels.map(function (l) { return 'â€¢ ' + l; }).join('\n');
            if (typeof window.showToast === 'function') {
                window.showToast(msg, 'warning', 6000, 'Required fields missing');
            }
            return;
        }

        _pfClearAllInvalid(formEl);

        var fd = new FormData(formEl);
        Object.keys(_pendingFiles).forEach(function (fieldName) {
            var file = _pendingFiles[fieldName];
            if (file) fd.set(fieldName + '_file', file, file.name);
        });

        _loaderStart('Savingâ€¦');

        fetch(cfg.saveUrl, {
            method: 'POST',
            body: fd,
            headers: { 'X-CSRFToken': _csrf() }
        })
            .then(function (r) { return r.json(); })
            .then(function (d) {
                _loaderDone();
                if (d.success) {
                    _toast(d.message || 'Saved successfully.', 's');
                    _pendingFiles = {};
                    if (typeof cfg.onSaveSuccess === 'function') cfg.onSaveSuccess(d);
                } else if (d.field_errors && d.field_errors.length) {
                    /* â”€â”€ Field-length violations from DataError â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
                       Mark each offending field with an inline limit hint.
                       The first field also gets tab-switch + scroll + shake.   */
                    d.field_errors.forEach(function (fe, idx) {
                        _pfMarkFieldError(fid, fe.field, fe.limit, fe.actual, idx === 0);
                    });
                    /* Toast lists all offending field names */
                    var names = d.field_errors.map(function (fe) {
                        return 'â€¢ ' + fe.db_col + ' (max ' + fe.limit + ')';
                    }).join('\n');
                    if (typeof window.showToast === 'function') {
                        window.showToast(names, 'warning', 8000, 'Value too long');
                    }
                } else if (d.duplicate) {
                    _toast(d.error || 'A duplicate record already exists.', 'w');
                } else {
                    _alert(d.error || d.message || 'An error occurred.', 'error', 'Save Failed');
                }
            })
            .catch(function () {
                _loaderDone();
                _alert('A network error occurred.', 'error', 'Network Error');
            });
    };

    window.pfActDelete = function (formId) {
        var fid = formId || _firstFormId();
        var cfg = _cfg(fid);
        var formEl = _form(fid);
        if (!cfg || !cfg.deleteUrl) { _alert('Delete is not configured.', 'warning', 'Not Configured'); return; }
        var idEl = formEl && formEl.querySelector('[name="' + cfg.deleteIdField + '"]');
        var labelEl = formEl && formEl.querySelector('[name="' + cfg.deleteLabelField + '"]');
        var id = idEl ? idEl.value.trim() : '';
        var label = labelEl ? labelEl.value.trim() : id;
        if (!id) { _alert('No record selected.', 'warning', 'No Record Selected'); return; }
        _confirm('Delete "' + (label || id) + '"? This cannot be undone.',
            function (confirmed) {
                if (!confirmed) return;
                var url = cfg.deleteUrl.replace('{id}', encodeURIComponent(id));
                _loaderStart('Deletingâ€¦');
                fetch(url, { method: 'POST', headers: { 'X-CSRFToken': _csrf() } })
                    .then(function (r) { return r.json(); })
                    .then(function (d) {
                        _loaderDone();
                        if (d.success) {
                            pfClear(fid);
                            _toast(d.message || 'Deleted.', 's');
                            if (typeof cfg.onDeleteSuccess === 'function') cfg.onDeleteSuccess();
                        } else {
                            _alert(d.message || 'Could not delete.', 'error', 'Delete Failed');
                        }
                    })
                    .catch(function () {
                        _loaderDone();
                        _alert('Network error during delete.', 'error', 'Network Error');
                    });
            }, 'danger', 'Delete Record', 'Yes, Delete', 'Cancel');
    };

    window.pfSave = function () { window.pfActSave(_firstFormId()); };
    window.pfDelete = function () { window.pfActDelete(_firstFormId()); };
    window.pfNew = function () { window.pfActNew(_firstFormId()); };

    /* â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
       AVATAR / PHOTO PREVIEWS
    â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€*/
    window.pfAvatarPreview = function (input, formId) {
        if (!input.files[0]) return;
        var r = new FileReader();
        r.onload = function (e) {
            var img = document.getElementById('pf-avatar-img-' + formId);
            if (img) { img.src = e.target.result; img.style.display = 'block'; }
            var ph = document.querySelector('#pf-avatar-box-' + formId + ' .pf-hero-photo-ph');
            if (ph) ph.style.display = 'none';
            var cfg = _cfg(formId);
            if (cfg && cfg.heroPhotoField) {
                var tabImg = document.getElementById('pf-photo-img-' + cfg.heroPhotoField);
                if (tabImg) { tabImg.src = e.target.result; tabImg.style.display = 'block'; }
            }
        };
        r.readAsDataURL(input.files[0]);
    };
    window.pfPhotoPreview = function (fieldName, input) {
        if (!input.files[0]) return;
        var r = new FileReader();
        r.onload = function (e) {
            var img = document.getElementById('pf-photo-img-' + fieldName);
            if (img) { img.src = e.target.result; img.style.display = 'block'; }
        };
        r.readAsDataURL(input.files[0]);
    };
    window.pfPhotoClear = function (fieldName) {
        var inp = document.getElementById('pf-photo-' + fieldName);
        var img = document.getElementById('pf-photo-img-' + fieldName);
        if (inp) inp.value = '';
        if (img) { img.src = ''; img.style.display = 'none'; }
        delete _pendingFiles[fieldName];
    };

    /* â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
       MENU DROPDOWN
    â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€*/
    window.pfToolbarMenu = function (btnEl, formId) {
        var ul = document.getElementById('pf-menu-items-' + formId);
        if (!ul) return;
        var existing = document.querySelector('.pf-menu-dd');
        if (existing) { existing.remove(); return; }
        var menu = document.createElement('div');
        menu.className = 'pf-menu-dd';
        ul.querySelectorAll('li').forEach(function (li) {
            var isSep = li.dataset.sep === '1';
            var isDanger = li.dataset.danger === '1';
            var label = li.dataset.label || '';
            var onclick = li.dataset.onclick || '';
            var iconKey = li.dataset.key || label;
            if (isSep) {
                var hr = document.createElement('hr'); hr.className = 'pf-menu-sep'; menu.appendChild(hr); return;
            }
            var item = document.createElement('div');
            item.className = 'pf-menu-item' + (isDanger ? ' pf-menu-item-danger' : '');
            item.innerHTML = '<span class="pf-menu-item-icon">' + (PF_ICONS[iconKey] || '') + '</span>' +
                '<span class="pf-menu-item-label">' + _esc(label) + '</span>';
            if (onclick) {
                item.addEventListener('click', (function (oc) {
                    return function () { menu.remove(); eval(oc); }; // eslint-disable-line no-eval
                }(onclick)));
            }
            menu.appendChild(item);
        });
        document.body.appendChild(menu);
        var rect = btnEl.getBoundingClientRect();
        menu.style.minWidth = '200px';
        menu.style.top = (rect.bottom + window.scrollY + 4) + 'px';
        menu.style.left = Math.min(rect.left + window.scrollX, window.innerWidth - 208) + 'px';
        setTimeout(function () {
            document.addEventListener('click', function _cl(e) {
                if (!e.target.closest('.pf-menu-dd')) { if (menu.parentNode) menu.remove(); document.removeEventListener('click', _cl); }
            });
        }, 50);
    };

    window.pfOpenMenu = function (btnEl, items) {
        var existing = document.querySelector('.pf-menu-dd');
        if (existing) { existing.remove(); return; }
        var menu = document.createElement('div');
        menu.className = 'pf-menu-dd';
        (items || []).forEach(function (item) {
            if (item.sep) {
                var hr = document.createElement('hr'); hr.className = 'pf-menu-sep'; menu.appendChild(hr);
            } else {
                var li = document.createElement('div');
                li.className = 'pf-menu-item' + (item.danger ? ' pf-menu-item-danger' : '');
                var iconSvg = (item.icon && PF_ICONS[item.icon]) ? PF_ICONS[item.icon] : '';
                li.innerHTML = '<span class="pf-menu-item-icon">' + iconSvg + '</span>' +
                    '<span class="pf-menu-item-label">' + _esc(item.label || '') + '</span>';
                li.onclick = function () { menu.remove(); if (typeof item.fn === 'function') item.fn(); };
                menu.appendChild(li);
            }
        });
        document.body.appendChild(menu);
        var rect = btnEl.getBoundingClientRect();
        menu.style.minWidth = '200px';
        menu.style.top = (rect.bottom + window.scrollY + 4) + 'px';
        menu.style.left = Math.min(rect.left + window.scrollX, window.innerWidth - 208) + 'px';
        setTimeout(function () {
            document.addEventListener('click', function _cl(e) {
                if (!e.target.closest('.pf-menu-dd')) { menu.remove(); document.removeEventListener('click', _cl); }
            });
        }, 50);
    };

    /* â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
       ENTER KEY
    â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€*/
    function _initEnterKey(formId, formEl) {
    /* â”€â”€ Selector for all visible focusable elements â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
       Adds .dp-input-wrap divs (custom datepicker triggers) alongside the
       standard inputs. Date fields use <input type="hidden"> + a <div>
       as the clickable trigger â€” the hidden input is excluded from tab
       order, so we include the trigger div instead.
    â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */
    var FOCUSABLE =
        'input:not([type=hidden]):not([readonly]):not(:disabled),' +
        'select:not(:disabled),' +
        'textarea:not(:disabled),' +
        '.dp-input-wrap';   /* â† date-picker trigger divs */

    formEl.addEventListener('keydown', function (e) {
        if (e.key !== 'Enter') return;

        /* Let textarea keep its natural newline behaviour */
        if (e.target.tagName === 'TEXTAREA') return;

        /* If Enter is pressed INSIDE an open calendar, close it and move on */
        if (e.target.closest && e.target.closest('.dp-calendar')) {
            e.preventDefault();
            /* closeAll() is defined inside datepicker.js IIFE â€” call via global */
            if (typeof window.dpCloseAll === 'function') window.dpCloseAll();
            /* After the calendar closes, focus the NEXT field after the
               .dp-input-wrap that owns this calendar */
            var cal = e.target.closest('.dp-calendar');
            var wrap = cal && cal.previousElementSibling;  /* .dp-input-wrap is
                        rendered just before .dp-calendar in datepicker.html */
            if (wrap && wrap.classList.contains('dp-input-wrap')) {
                _focusNextFrom(formEl, FOCUSABLE, wrap);
            }
            return;
        }

        /* Normal Enter on a .dp-input-wrap: toggle the calendar open/closed */
        if (e.target.classList && e.target.classList.contains('dp-input-wrap')) {
            e.preventDefault();
            /* Extract the dp id from the wrap id: "<dpid>_wrap" */
            var wrapId = e.target.id || '';
            var dpId = wrapId.replace(/_wrap$/, '');
            if (dpId && typeof window.dpToggle === 'function') {
                window.dpToggle(dpId, e);
            }
            return;
        }

        /* Select: Enter moves to next field (default would do nothing useful) */
        if (e.target.tagName === 'SELECT') {
            e.preventDefault();
            _focusNextFrom(formEl, FOCUSABLE, e.target);
            return;
        }

        /* Standard text/number/etc. input */
        e.preventDefault();
        _focusNextFrom(formEl, FOCUSABLE, e.target);
    });
}

function _focusNextFrom(formEl, selector, currentEl) {
    /* Collect all focusable elements, excluding tabIndex=-1 (tabStop=false). */
    var all = Array.prototype.slice.call(formEl.querySelectorAll(selector))
        .filter(function (el) { return el.tabIndex !== -1; });

    /* Sort by tabIndex — positive tabIndex values come first (in numeric order),
       then tabIndex=0 elements follow in DOM order (their relative order in `all`
       is already DOM order from querySelectorAll).
       This mirrors exactly how browsers resolve Tab-key focus order. */
    var positives = all.filter(function (el) { return el.tabIndex > 0; })
                       .sort(function (a, b) { return a.tabIndex - b.tabIndex; });
    var zeros     = all.filter(function (el) { return el.tabIndex === 0; });
    var sorted    = positives.concat(zeros);

    var idx  = sorted.indexOf(currentEl);
    var next = sorted[idx + 1];
    if (!next && sorted.length) next = sorted[0]; /* wrap to first on last field */
    if (next) {
        /* .dp-input-wrap is a div — ensure it can receive focus */
        if (next.classList && next.classList.contains('dp-input-wrap')) {
            if (!next.hasAttribute('tabindex')) next.setAttribute('tabindex', '0');
            next.focus();
        } else {
            next.focus();
            if (next.select) next.select();
        }
    }
}


    /* â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
       TOAST
    â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€*/
    window.pfToast = function (msg, type) {
        var map = { s: 'success', e: 'error', w: 'warning', i: 'info' };
        var t = map[type] || type || 'info';
        if (typeof window.showToast === 'function') window.showToast(msg, t);
        else console.info('[pfToast]', t, msg);
    };
    window.tfToast = window.pfToast;
    window.epToast = window.pfToast;

    /* â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
       REQUIRED-FIELD VALIDATION HELPERS  (v4.3)
    â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€*/
    window._pfValidate = _pfValidate;
    function _pfValidate(formEl) {
        var bad = [];
        formEl.querySelectorAll('input[required], select[required], textarea[required]')
            .forEach(function (el) {
                if (el.name === 'csrfmiddlewaretoken') return;
                if (el.type === 'hidden') return;
                if (el.disabled) return;

                var empty = (el.type === 'checkbox')
                    ? !el.checked
                    : (el.type === 'file')
                        ? (!el.files || el.files.length === 0)
                        : el.value.trim() === '';

                if (!empty) return;

                var wrapper = el.closest('.pf-field') || el.closest('.pf-hf-cell');
                var labelEl = wrapper
                    ? (wrapper.querySelector('.pf-field-lbl') || wrapper.querySelector('.pf-hf-lbl'))
                    : null;
                var labelTxt = labelEl
                    ? (labelEl.textContent || '').replace(/\s*\*\s*$/, '').trim()
                    : (el.placeholder || el.name || 'Field');

                bad.push({ el: el, wrapper: wrapper, label: labelTxt });
            });
        return bad;
    }

    window._pfMarkInvalid = _pfMarkInvalid;
    function _pfMarkInvalid(el, label, formId, isFirst) {
        var wrapper = el.closest('.pf-field') || el.closest('.pf-hf-cell');
        if (!wrapper) return;

        wrapper.classList.add('pf-invalid');

        var ctl = wrapper.querySelector('.pf-field-ctl') || wrapper.querySelector('.pf-hf-ctl');
        if (ctl && !ctl.querySelector('.pf-field-error')) {
            var err = document.createElement('span');
            err.className = 'pf-field-error';
            err.textContent = label + ' is required';
            ctl.appendChild(err);
        }

        if (isFirst) {
            wrapper.classList.add('pf-shake');
            wrapper.addEventListener('animationend', function () {
                wrapper.classList.remove('pf-shake');
            }, { once: true });

            var pane = wrapper.closest('.pf-pane');
            if (pane && pane.id) {
                var suffix = pane.id.replace('pf-pane-' + formId + '-', '');
                if (suffix && typeof pfTab === 'function') pfTab(formId, suffix, null);
            }

            setTimeout(function () {
                wrapper.scrollIntoView({ behavior: 'smooth', block: 'center' });
                try { el.focus(); } catch (e) { /* ignore */ }
            }, 80);
        }

        var _clear = function () { _pfClearInvalid(wrapper); };
        el.addEventListener('input', _clear, { once: true });
        el.addEventListener('change', _clear, { once: true });
    }

    /**
     * _pfMarkFieldError â€” shows an inline length-limit hint below a field.
     *
     * Called when the server returns field_errors from a DataError.
     * Displays: "Max 15 characters (you entered 23)"
     * Adds a live character counter that updates as the user types and
     * auto-clears the error once the value is within the limit.
     *
     * @param {string} formId
     * @param {string} fieldName  â€” form field name attr (e.g. 'mobile')
     * @param {number} limit      â€” column character_maximum_length
     * @param {number} actual     â€” characters entered at time of save
     * @param {boolean} isFirst   â€” scroll/shake/tab-switch for the first one
     */
    window._pfMarkFieldError = _pfMarkFieldError;
    function _pfMarkFieldError(formId, fieldName, limit, actual, isFirst) {
        var formEl = _form(formId);
        if (!formEl) return;
        var el = formEl.querySelector('[name="' + fieldName + '"]');
        if (!el) return;

        var wrapper = el.closest('.pf-field') || el.closest('.pf-hf-cell');
        if (!wrapper) return;

        wrapper.classList.add('pf-invalid');

        var ctl = wrapper.querySelector('.pf-field-ctl') || wrapper.querySelector('.pf-hf-ctl');
        /* Remove any stale error from a previous save attempt */
        var stale = ctl && ctl.querySelector('.pf-field-error');
        if (stale) stale.parentNode.removeChild(stale);

        if (ctl) {
            var err = document.createElement('span');
            err.className = 'pf-field-error pf-field-error--limit';

            var _render = function (cur) {
                var over = cur - limit;
                err.textContent = over > 0
                    ? 'Max ' + limit + ' characters â€” ' + over + ' too many (you entered ' + cur + ')'
                    : 'Max ' + limit + ' characters';
                err.style.color = over > 0
                    ? 'var(--color-danger, #dc2626)'
                    : 'var(--color-success, #16a34a)';
            };
            _render(actual);
            ctl.appendChild(err);

            /* Live counter â€” updates on every keystroke */
            var _onInput = function () {
                var cur = el.value.length;
                _render(cur);
                if (cur <= limit) {
                    /* Value is now within limit â€” clear the error state */
                    wrapper.classList.remove('pf-invalid', 'pf-shake');
                    if (err.parentNode) err.parentNode.removeChild(err);
                    el.removeEventListener('input', _onInput);
                }
            };
            el.addEventListener('input', _onInput);
        }

        if (isFirst) {
            wrapper.classList.add('pf-shake');
            wrapper.addEventListener('animationend', function () {
                wrapper.classList.remove('pf-shake');
            }, { once: true });

            /* Switch to the tab that contains this field */
            var pane = wrapper.closest('.pf-pane');
            if (pane && pane.id) {
                var suffix = pane.id.replace('pf-pane-' + formId + '-', '');
                if (suffix && typeof pfTab === 'function') pfTab(formId, suffix, null);
            }

            setTimeout(function () {
                wrapper.scrollIntoView({ behavior: 'smooth', block: 'center' });
                try { el.focus(); el.select && el.select(); } catch (ex) { /* ignore */ }
            }, 80);
        }
    }

    function _pfClearInvalid(wrapper) {
        if (!wrapper) return;
        wrapper.classList.remove('pf-invalid', 'pf-shake');
        var err = wrapper.querySelector('.pf-field-error');
        if (err && err.parentNode) err.parentNode.removeChild(err);
    }

    function _pfClearAllInvalid(formEl) {
        formEl.querySelectorAll('.pf-field.pf-invalid, .pf-hf-cell.pf-invalid').forEach(function (w) {
            _pfClearInvalid(w);
        });
    }

    /* â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
       PRIVATE UTILS
    â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€*/
    function _cfg(formId) { return (window._pfConfig || {})[formId]; }
    function _form(formId) { return document.getElementById(formId); }
    function _firstFormId() { var k = Object.keys(window._pfConfig || {}); return k.length ? k[0] : ''; }
    function _setText(id, text) { var el = document.getElementById(id); if (el) el.textContent = text; }
    function _csrf() { var m = document.cookie.match(/csrftoken=([^;]+)/); return m ? decodeURIComponent(m[1]) : ''; }
    function _toast(msg, type) { window.pfToast(msg, type); }
    function _esc(s) { return String(s || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;'); }
    function _alert(message, type, title) {
        if (typeof window.showAlert === 'function') window.showAlert(message, type || 'error', title);
        else window.pfToast(message, type === 'success' ? 's' : type === 'warning' ? 'w' : 'e');
    }
    function _confirm(message, callback, type, title, confirmText, cancelText) {
        if (typeof window.showConfirm === 'function') window.showConfirm(message, callback, type || 'danger', title, confirmText, cancelText);
        else callback(window.confirm(message));
    }




    (function _pfToolbarStuck() {
 
    function _init() {
        document.querySelectorAll('.pf-toolbar').forEach(function (toolbar) {
            var page = toolbar.closest('.pf-page');
 
            /* â”€â”€ Sentinel: 1px invisible div placed just before toolbar â”€â”€ */
            var sentinel = document.createElement('div');
            sentinel.style.cssText = 'height:1px;width:100%;pointer-events:none;visibility:hidden;flex-shrink:0;';
            toolbar.parentNode.insertBefore(sentinel, toolbar);
 
            /* â”€â”€ Scroll container: .content-inner â”€â”€ */
            var scrollRoot = toolbar.closest('.content-inner') || null;
 
            /* â”€â”€ IntersectionObserver: sentinel out of view = toolbar stuck â”€â”€ */
            var io = new IntersectionObserver(function (entries) {
                entries.forEach(function (e) {
                    toolbar.classList.toggle('pf-toolbar--stuck', !e.isIntersecting);
                });
            }, { root: scrollRoot, threshold: 0 });
            io.observe(sentinel);
 
            /* â”€â”€ Keep .pf-tabs top in sync with actual toolbar height â”€â”€ */
            function _syncTabsTop() {
                var h = toolbar.getBoundingClientRect().height;
                /* find .pf-tabs within the same pf-page scope */
                var tabs = page
                    ? page.querySelector('.pf-tabs')
                    : document.querySelector('.pf-tabs');
                if (tabs) {
                    /* +2px breathing gap between toolbar bottom and tab strip */
                    tabs.style.top = (h + 2) + 'px';
                }
            }
 
            /* Run once on load, then on every resize */
            _syncTabsTop();
            var ro = new ResizeObserver(_syncTabsTop);
            ro.observe(toolbar);
        });
    }
 
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', _init);
    } else {
        _init();
    }
 
    }());


    /* â”€â”€ Ctrl+E on a focused control â€” toggle disable/enable â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
+       Focus the field first (click it), then press Ctrl+E.
+       Note: e.shiftKey check prevents conflict with Ctrl+Shift+E below.   */
    document.addEventListener('keydown', function (e) {
        if (!e.ctrlKey || e.shiftKey || e.key !== 'e') return;
        var el = document.activeElement;
        if (!el) return;
        var tag = el.tagName;
        if (tag !== 'INPUT' && tag !== 'SELECT' && tag !== 'TEXTAREA') return;
        if (!el.closest('.pf-page')) return;
        e.preventDefault();
        if (typeof window.fdToggleEnabled === 'function') {
            window.fdToggleEnabled(el.name);
        } else {
            el.disabled = !el.disabled;
        }
    });

   /* â”€â”€ Ctrl+Shift+E â€” toggle the hovered field (works on disabled inputs) â”€â”€
      Hover the mouse over any field label or control, then press Ctrl+Shift+E.
      This is the re-enable path when Ctrl+E is unreachable (input is disabled). */
   document.addEventListener('keydown', function (e) {
       if (!e.ctrlKey || !e.shiftKey || e.key.toLowerCase() !== 'e') return;
       var hovered = document.querySelector(
           '.pf-page .pf-field:hover, .pf-page .pf-hf-cell:hover'
       );
       if (!hovered) return;
       var inp = hovered.querySelector('input[name], select[name], textarea[name]');
       if (!inp || !inp.name) return;
       e.preventDefault();
       if (typeof window.fdToggleEnabled === 'function') {
           window.fdToggleEnabled(inp.name);
       } else {
           inp.disabled = !inp.disabled;
       }
   });

    /* â”€â”€ Double-click a field label â†’ toggle the disabled control â”€â”€â”€â”€â”€â”€â”€â”€â”€
       Works even when the control is disabled (and therefore unfocusable).
       Targets .pf-field-lbl (body fields) and .pf-hf-lbl (header fields). */
    document.addEventListener('dblclick', function (e) {
        var lbl = e.target.closest('.pf-field-lbl, .pf-hf-lbl');
        if (!lbl || !lbl.closest('.pf-page')) return;
        var wrap = lbl.closest('.pf-field, .pf-hf-cell');
        if (!wrap) return;
        var inp = wrap.querySelector('input[name], select[name], textarea[name]');
        if (!inp || !inp.name) return;
        e.preventDefault();
        if (typeof window.fdToggleEnabled === 'function') {
            window.fdToggleEnabled(inp.name);
        } else {
            inp.disabled = !inp.disabled;
        }
    });



}());










