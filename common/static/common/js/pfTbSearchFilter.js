/**
 * common/static/common/js/pfTbSearchFilter.js   v1.0
 *
 * Global utility that wires the profile_form.js toolbar search
 * (pf:search custom event) to any in-page data table.
 *
 * Usage
 * ─────
 *   pfTbSearchAttach(formId, getRows, fieldDefs, onResults);
 *
 *   formId    {string}   — must match form_config.form_id in Django
 *   getRows   {function} — () → Array  returns the CURRENT full row array
 *                          (use a getter so live filter state is respected)
 *   fieldDefs {Array}    — [{key:'emp_name', label:'Name'}, …]
 *                          same objects you pass in form_config.search.fields
 *   onResults {function} — (filteredRows, query, field) → void
 *                          your callback that re-renders the table
 *
 * The function:
 *   • Listens for the 'pf:search' CustomEvent fired by profile_form.js
 *   • When query is empty → calls onResults(allRows, '', '')
 *   • When field is ''   → searches ALL fieldDefs keys (OR logic)
 *   • When field is set  → searches that single key only
 *   • Matching is case-insensitive substring
 *
 * Multiple calls with the same formId replace the previous attachment.
 *
 * Dependencies
 * ─────────────
 * profile_form.js  (provides pf:search event via the toolbar search input)
 */

(function (global) {
    'use strict';

    /* Registry: formId → { detach: fn } so we can replace attachments */
    var _registry = {};

    /**
     * Attach the search filter to a form's toolbar search input.
     *
     * @param {string}   formId    - form_config.form_id value
     * @param {function} getRows   - () → Array  live row source
     * @param {Array}    fieldDefs - [{key, label}, …]
     * @param {function} onResults - (rows, query, field) → void
     */
    global.pfTbSearchAttach = function (formId, getRows, fieldDefs, onResults) {
        if (!formId || typeof getRows !== 'function' || typeof onResults !== 'function') {
            console.warn('[pfTbSearchFilter] pfTbSearchAttach: invalid arguments for formId:', formId);
            return;
        }

        /* Detach any previous attachment for this formId */
        if (_registry[formId] && typeof _registry[formId].detach === 'function') {
            _registry[formId].detach();
        }

        var keys = (fieldDefs || []).map(function (f) { return f.key; }).filter(Boolean);

        /* The pf:search event bubbles up from the search input element.
           We listen on document so we don't need a direct reference.    */
        function _handler(e) {
            if (!e.detail || e.detail.formId !== formId) return;

            var query = (e.detail.query || '').trim().toLowerCase();
            var field = (e.detail.field || '').trim();
            var allRows = getRows();

            if (!query) {
                onResults(allRows.slice(), '', '');
                return;
            }

            /* Decide which keys to search */
            var searchKeys = (field && keys.indexOf(field) !== -1) ? [field] : keys;

            var filtered = allRows.filter(function (row) {
                return searchKeys.some(function (k) {
                    var cell = String(row[k] || '').toLowerCase();
                    return cell.indexOf(query) !== -1;
                });
            });

            onResults(filtered, query, field);
        }

        document.addEventListener('pf:search', _handler);

        _registry[formId] = {
            detach: function () {
                document.removeEventListener('pf:search', _handler);
            }
        };
    };

    /**
     * Detach a previously registered search attachment.
     * Call this if the page/component is torn down.
     *
     * @param {string} formId
     */
    global.pfTbSearchDetach = function (formId) {
        if (_registry[formId] && typeof _registry[formId].detach === 'function') {
            _registry[formId].detach();
            delete _registry[formId];
        }
    };

}(window));