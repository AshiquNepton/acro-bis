/* ══════════════════════════════════════════════════════════════
   AUTO-CAPITALIZE  — applies to all text inputs site-wide
   Capitalizes the first letter of every word as the user types.
   Skips: email, password, search, url, hidden, readonly, disabled.
══════════════════════════════════════════════════════════════ */
(function () {
    'use strict';

    var SKIP_TYPES = {
        email: 1, password: 1, search: 1, url: 1, hidden: 1,
        tel: 1, number: 1, date: 1, time: 1, 'datetime-local': 1,
        month: 1, file: 1, checkbox: 1, radio: 1
    };

    function _applyCapitalize(el) {
        if (!el || el.dataset.capBound) return;
        if (el.readOnly || el.disabled) return;
        var t = (el.type || 'text').toLowerCase();
        if (SKIP_TYPES[t]) return;
        el.dataset.capBound = '1';
        el.addEventListener('input', function () {
            var start = el.selectionStart;
            var end   = el.selectionEnd;
            var val   = el.value;
            var newVal = val.replace(/(^|\s)(\S)/g, function (_, space, char) {
    return space + char.toUpperCase();
});
            if (newVal !== val) {
                el.value = newVal;
                try { el.setSelectionRange(start, end); } catch (e) {}
            }
        });
    }

    function _applyAll(root) {
        (root || document).querySelectorAll('input[type="text"], input:not([type]), textarea').forEach(_applyCapitalize);
    }

    document.addEventListener('DOMContentLoaded', function () {
        _applyAll(document);
        new MutationObserver(function (mutations) {
            mutations.forEach(function (m) {
                m.addedNodes.forEach(function (node) {
                    if (node.nodeType !== 1) return;
                    if (node.matches && node.matches('input[type="text"], input:not([type]), textarea')) {
                        _applyCapitalize(node);
                    } else if (node.querySelectorAll) {
                        _applyAll(node);
                    }
                });
            });
        }).observe(document.body, { childList: true, subtree: true });
    });

    window.applyCapitalize = _applyAll;
}());