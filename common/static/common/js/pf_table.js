/**
 * ════════════════════════════════════════════════════════════════════
 *  common/static/common/js/pf_table.js
 *
 *  Helpers for the reusable _table.html include.
 *
 *  Load after profile_form.js:
 *      <script src="{% static 'common/js/pf_table.js' %}"></script>
 *
 *  ── API ──────────────────────────────────────────────────────────
 *
 *  pf_table_row(cells, actions?)
 *    Returns an HTML <tr> string ready to inject into a tbody.
 *
 *  pf_table_empty(colspan, text?)
 *    Returns an empty-state <tr> string.
 *
 *  pf_table_set(tbodyId, rows, renderFn)
 *    Replaces tbody content. renderFn(row, index) → HTML string.
 *
 *  ── Optional search (activated by search_fields in table config) ──
 *
 *  pfTblCacheRows(tableId, rows, renderFn)
 *    Cache flat row data + render function for search filtering.
 *    Call this after populating the tbody.
 *
 *  pfTblToggleDrop(tableId)   — called by search field button
 *  pfTblSetField(tableId, field, label, el) — called by dropdown items
 *  pfTblSearch(tableId)       — called on input event
 * ════════════════════════════════════════════════════════════════════
 */

(function () {
    'use strict';

    // ── Core helpers ──────────────────────────────────────────────────

    window.pf_table_row = function (cells, actions) {
        var tds = (cells || []).map(function (v) {
            return '<td>' + _e(v) + '</td>';
        }).join('');

        var actTd = '';
        if (actions && actions.length) {
            var btns = actions.map(function (a) {
                var cls = 'pf-tb-btn' + (a.danger ? ' pf-tb-btn-danger' : '');
                return '<button type="button" class="' + cls + '" onclick="' + a.onclick + '">'
                     + _e(a.label) + '</button>';
            }).join(' ');
            actTd = '<td style="text-align:right;white-space:nowrap;padding-right:8px">' + btns + '</td>';
        }

        return '<tr>' + tds + actTd + '</tr>';
    };

    window.pf_table_empty = function (colspan, text) {
        return '<tr><td colspan="' + (colspan || 1) + '" class="pf-tbl-empty">'
             + _e(text || 'No records yet.') + '</td></tr>';
    };

    window.pf_table_set = function (tbodyId, rows, renderFn, colspan, emptyText) {
        var tb = document.getElementById(tbodyId);
        if (!tb) return;

        if (!rows || !rows.length) {
            var cols = colspan;
            if (!cols) {
                var tbl = tb.closest('table');
                var ths = tbl ? tbl.querySelectorAll('thead th') : [];
                cols = ths.length || 1;
            }
            tb.innerHTML = window.pf_table_empty(cols, emptyText);
            return;
        }

        tb.innerHTML = rows.map(renderFn).join('');
    };

    // ── Optional search ───────────────────────────────────────────────
    // Keyed by tableId so multiple tables on the same page never conflict.

    var _cache = {};

    /**
     * Cache flat rows + render function for a table.
     * Must be called after the tbody is first populated.
     *
     * @param {string}   tableId   Matches t.id in _table.html
     * @param {Array}    rows      Flat array of data objects
     * @param {Function} renderFn  function(row) → HTML <tr> string
     */
    window.pfTblCacheRows = function (tableId, rows, renderFn) {
        _cache[tableId] = { rows: rows || [], renderFn: renderFn, field: '' };

        // Close this table's dropdown when clicking outside — registered once
        document.addEventListener('click', function (e) {
            var wrap = document.getElementById(tableId + '-search-wrap');
            var drop = document.getElementById(tableId + '-search-drop');
            if (wrap && drop && !wrap.contains(e.target)) {
                drop.style.display = 'none';
            }
        });
    };

    window.pfTblToggleDrop = function (tableId) {
        var drop = document.getElementById(tableId + '-search-drop');
        if (!drop) return;
        drop.style.display = drop.style.display === 'none' ? 'block' : 'none';
    };

    window.pfTblSetField = function (tableId, field, label, el) {
        if (_cache[tableId]) _cache[tableId].field = field;

        var lbl = document.getElementById(tableId + '-search-field-label');
        if (lbl) lbl.textContent = label;

        var drop = document.getElementById(tableId + '-search-drop');
        if (drop) {
            drop.querySelectorAll('.rpt-search-drop-item').forEach(function (it) {
                it.classList.toggle('active', it === el);
            });
            drop.style.display = 'none';
        }

        window.pfTblSearch(tableId);
    };

    window.pfTblSearch = function (tableId) {
        var c = _cache[tableId];
        if (!c) return;

        var input = document.getElementById(tableId + '-search-input');
        var q     = input ? input.value.toLowerCase().trim() : '';
        var field = c.field;

        var filtered = q ? c.rows.filter(function (row) {
            if (field) {
                return String(row[field] || '').toLowerCase().indexOf(q) !== -1;
            }
            return Object.values(row).some(function (v) {
                return String(v || '').toLowerCase().indexOf(q) !== -1;
            });
        }) : c.rows;

        var tbody = document.getElementById(tableId + '-tbody');
        if (!tbody) return;

        if (!filtered.length) {
            var tbl  = tbody.closest('table');
            var cols = tbl ? tbl.querySelectorAll('thead th').length : 1;
            tbody.innerHTML = window.pf_table_empty(cols, 'No records found.');
        } else {
            tbody.innerHTML = filtered.map(c.renderFn).join('');
        }
    };

    // ── Private ───────────────────────────────────────────────────────

    function _e(s) {
        return String(s == null ? '' : s)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;');
    }

}());