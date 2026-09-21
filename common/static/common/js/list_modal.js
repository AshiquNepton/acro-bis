/**
 * ═══════════════════════════════════════════════════════════════════════════
 * common/static/common/js/list_modal.js
 *
 * Universal ListModal / Position Entry Screen Component.
 * Unified with UtilityModal shell and theme_constants.py button styles/SVGs:
 *   • Identical modal frame and header to Item Split modal (UtilityModal)
 *   • Standardized modal dimensions (480px × 260px)
 *   • Exact SVG icons from common/theme_constants.py
 *   • Reusable button styling matching profile_form (.pf-tb-btn)
 *   • Editable DataGridView from list.png (auto SlNo, continuous gridlines)
 * ═══════════════════════════════════════════════════════════════════════════
 */

(function (global) {
    'use strict';

    /* Exact SVGs from common/theme_constants.py */
    var THEME_ICONS = {
        save: (
            '<svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">' +
            '<path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/>' +
            '<polyline points="17 21 17 13 7 13 7 21"/>' +
            '<polyline points="7 3 7 8 15 8"/>' +
            '</svg>'
        ),
        cancel: (
            '<svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">' +
            '<circle cx="12" cy="12" r="10"/>' +
            '<line x1="4.93" y1="4.93" x2="19.07" y2="19.07"/>' +
            '</svg>'
        ),
        close: (
            '<svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">' +
            '<line x1="18" y1="6" x2="6" y2="18"/>' +
            '<line x1="6" y1="6" x2="18" y2="18"/>' +
            '</svg>'
        ),
        remove: (
            '<svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">' +
            '<circle cx="12" cy="12" r="10"/>' +
            '<line x1="8" y1="12" x2="16" y2="12"/>' +
            '</svg>'
        ),
        defaultCog: (
            '<svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">' +
            '<circle cx="12" cy="12" r="3"/>' +
            '<path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06' +
            'a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09' +
            'A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83' +
            'l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09' +
            'A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83' +
            'l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09' +
            'a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83' +
            'l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09' +
            'a1.65 1.65 0 0 0-1.51 1z"/>' +
            '</svg>'
        ),
        confirm: (
            '<svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">' +
            '<polyline points="9 11 12 14 22 4"/>' +
            '<path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/>' +
            '</svg>'
        ),
        infinity: (
            '<path d="M18.178 8c5.096 0 5.096 8 0 8-5.095 0-7.267-8-12.356-8-5.096 0-5.096 8 0 8 5.096 0 7.261-8 12.356-8z" stroke-width="2"/>'
        )
    };

    function ListModal(cfg) {
        this.cfg = cfg || {};
        this.id = cfg.id || ('lm-' + Math.random().toString(36).substr(2, 9));
        this.title = cfg.title || 'Bin Locations';
        this.columnLabel = cfg.columnLabel || 'Position / Bin Location';
        this.width = cfg.width || '480px';
        this.height = cfg.height || '260px';
        this.minRows = cfg.minRows || 8;
        this.rows = [];
        this.selectedIndex = 0;
        this.utilModal = null;

        this._initRows(cfg.data);
        this._build();
    }

    ListModal.prototype._initRows = function (initialData) {
        var self = this;
        this.rows = [];

        if (Array.isArray(initialData)) {
            initialData.forEach(function (item) {
                if (typeof item === 'string') {
                    var isDef = item.indexOf('(Default)') !== -1;
                    var clean = item.replace('(Default)', '').trim();
                    if (clean) self.rows.push({ value: clean, isDefault: isDef });
                } else if (item && typeof item === 'object') {
                    self.rows.push({
                        value: item.value || item.code || '',
                        isDefault: !!item.isDefault
                    });
                }
            });
        }

        if (this.rows.length === 0) {
            this.rows.push({ value: '', isDefault: false });
        }
    };

    ListModal.prototype._build = function () {
        if (this.utilModal) return;

        var self = this;

        // Clean up any stale backdrop element with the same id if already present in DOM
        var existingBd = document.getElementById(this.id + '-bd');
        if (existingBd && existingBd.parentNode) {
            existingBd.parentNode.removeChild(existingBd);
        }

        // Build atop UtilityModal engine so modal shell is 100% identical to Select Item
        this.utilModal = new UtilityModal({
            id: this.id,
            title: this.title,
            subtitle: '',
            icon: THEME_ICONS.infinity,
            width: this.width,
            height: this.height,
            tabs: [
                { id: 'grid_tab', label: this.title }
            ],
            toolbar: [],
            onBuild: function (m) {
                // Ensure standard sizing class is applied
                if (m._el) {
                    var modalBox = m._el.querySelector('.utm-modal');
                    if (modalBox) {
                        modalBox.classList.add('utm-modal--standard');
                        modalBox.style.width = self.width;
                        modalBox.style.height = self.height;
                    }
                }

                // Hide left sidenav tab strip
                var nav = (m._el ? m._el.querySelector('.utm-nav') : null) || document.getElementById(self.id + '-nav');
                if (nav) nav.style.display = 'none';

                var pane = m.pane('grid_tab');
                if (!pane) return;

                pane.style.padding = '0';
                pane.style.margin = '0';
                pane.style.display = 'flex';
                pane.style.flexDirection = 'column';
                pane.style.height = '100%';
                pane.style.overflow = 'hidden';

                var html =
                    '<div class="lm-container">' +
                        /* Data Grid Area */
                        '<div class="lm-body">' +
                            '<div class="lm-grid-wrap" id="' + self.id + '-gwrap">' +
                                '<table class="lm-table">' +
                                    '<thead>' +
                                        '<tr>' +
                                            '<th class="lm-col-sn">SlNo</th>' +
                                            '<th class="lm-col-data">' + self.columnLabel + '</th>' +
                                            '<th class="lm-col-scroll-spacer"></th>' +
                                        '</tr>' +
                                    '</thead>' +
                                    '<tbody id="' + self.id + '-tbody"></tbody>' +
                                '</table>' +
                            '</div>' +
                        '</div>' +

                        /* Standard Action Bar using .pf-tb-btn and theme_constants.py icons */
                        '<div class="lm-action-bar">' +
                            '<button type="button" class="pf-tb-btn" id="' + self.id + '-btn-default" title="Set Active as Default">' +
                                '<span class="pf-tb-btn-icon">' + THEME_ICONS.defaultCog + '</span>' +
                                'Default' +
                            '</button>' +
                            '<button type="button" class="pf-tb-btn" id="' + self.id + '-btn-remove" title="Remove Active Row">' +
                                '<span class="pf-tb-btn-icon">' + THEME_ICONS.remove + '</span>' +
                                'Remove' +
                            '</button>' +
                            '<button type="button" class="pf-tb-btn" id="' + self.id + '-btn-save" title="Save (Alt+S)">' +
                                '<span class="pf-tb-btn-icon">' + THEME_ICONS.save + '</span>' +
                                '<span style="text-decoration:underline;">S</span>ave' +
                            '</button>' +
                            '<button type="button" class="pf-tb-btn pf-tb-btn-danger" id="' + self.id + '-btn-cancel" title="Cancel (Esc)">' +
                                '<span class="pf-tb-btn-icon">' + THEME_ICONS.cancel + '</span>' +
                                '<span style="text-decoration:underline;">C</span>ancel' +
                            '</button>' +
                        '</div>' +
                    '</div>';

                pane.innerHTML = html;

                // Wire Button Handlers
                pane.querySelector('#' + self.id + '-btn-save').addEventListener('click', function () { self._doSave(); });
                pane.querySelector('#' + self.id + '-btn-remove').addEventListener('click', function () { self._doRemove(); });
                pane.querySelector('#' + self.id + '-btn-default').addEventListener('click', function () { self._doDefault(); });
                pane.querySelector('#' + self.id + '-btn-cancel').addEventListener('click', function () { self.close(); });

                // Keyboard Shortcuts inside Modal
                pane.addEventListener('keydown', function (e) {
                    if (e.key === 'Escape') {
                        e.preventDefault();
                        self.close();
                    } else if (e.altKey && (e.key === 's' || e.key === 'S')) {
                        e.preventDefault();
                        self._doSave();
                    } else if (e.altKey && (e.key === 'c' || e.key === 'C')) {
                        e.preventDefault();
                        self.close();
                    } else if (e.ctrlKey && e.key === 'Enter') {
                        e.preventDefault();
                        self._doSave();
                    }
                });

                self.renderRows();
            },
            onClose: function () {
                if (typeof self.cfg.onClose === 'function') {
                    self.cfg.onClose(self);
                }
            }
        });
    };

    ListModal.prototype.renderRows = function () {
        var root = (this.utilModal && this.utilModal._el) ? this.utilModal._el : document;
        var tbody = root.querySelector('#' + this.id + '-tbody') || document.getElementById(this.id + '-tbody');
        if (!tbody) return;

        var self = this;
        tbody.innerHTML = '';

        var totalRows = Math.max(this.rows.length, this.minRows);

        for (var i = 0; i < totalRows; i++) {
            var rowData = this.rows[i] || null;
            var isDataRow = rowData !== null;
            var isSelected = (i === this.selectedIndex);

            var tr = document.createElement('tr');
            tr.dataset.index = i;
            if (isSelected) tr.classList.add('selected');
            if (rowData && rowData.isDefault) tr.classList.add('is-default');

            // 1. SlNo Cell
            var slNoText = isDataRow ? (i + 1) : '';
            var tdSlNo = document.createElement('td');
            tdSlNo.className = 'lm-col-sn';
            tdSlNo.textContent = slNoText;
            tr.appendChild(tdSlNo);

            // 2. Data Entry Cell
            var tdData = document.createElement('td');
            tdData.className = 'lm-col-data';

            var input = document.createElement('input');
            input.type = 'text';
            input.className = 'lm-cell-input';
            input.autocomplete = 'off';
            input.value = isDataRow ? rowData.value : '';
            input.dataset.index = i;

            // Wire input events
            (function (idx, inp) {
                inp.addEventListener('focus', function () {
                    self._selectIndex(idx);
                });

                inp.addEventListener('input', function () {
                    self._onCellInput(idx, inp.value);
                });

                inp.addEventListener('keydown', function (e) {
                    if (e.key === 'Enter') {
                        e.preventDefault();
                        self._onEnterKey(idx);
                    } else if (e.key === 'ArrowDown') {
                        e.preventDefault();
                        self._focusRow(idx + 1);
                    } else if (e.key === 'ArrowUp') {
                        e.preventDefault();
                        self._focusRow(idx - 1);
                    }
                });
            })(i, input);

            tdData.appendChild(input);
            tr.appendChild(tdData);

            // 3. Scrollbar Spacer Cell
            var tdSpacer = document.createElement('td');
            tdSpacer.className = 'lm-col-scroll-spacer';
            tr.appendChild(tdSpacer);

            // Row click selection
            (function (idx) {
                tr.addEventListener('click', function (e) {
                    if (e.target.tagName !== 'INPUT') {
                        self._focusRow(idx);
                    }
                });
            })(i);

            tbody.appendChild(tr);
        }
    };

    ListModal.prototype._selectIndex = function (idx) {
        this.selectedIndex = idx;
        var root = (this.utilModal && this.utilModal._el) ? this.utilModal._el : document;
        var tbody = root.querySelector('#' + this.id + '-tbody') || document.getElementById(this.id + '-tbody');
        if (!tbody) return;

        var rows = tbody.querySelectorAll('tr[data-index]');
        rows.forEach(function (tr) {
            var rIdx = parseInt(tr.dataset.index, 10);
            tr.classList.toggle('selected', rIdx === idx);
        });
    };

    ListModal.prototype._focusRow = function (idx) {
        var root = (this.utilModal && this.utilModal._el) ? this.utilModal._el : document;
        var tbody = root.querySelector('#' + this.id + '-tbody') || document.getElementById(this.id + '-tbody');
        if (!tbody) return;

        var row = tbody.querySelector('tr[data-index="' + idx + '"]');
        if (row) {
            var inp = row.querySelector('.lm-cell-input');
            if (inp) {
                inp.focus();
                if (inp.select) inp.select();
            }
        }
    };

    ListModal.prototype._onCellInput = function (idx, val) {
        while (this.rows.length <= idx) {
            this.rows.push({ value: '', isDefault: false });
        }
        this.rows[idx].value = val;

        var root = (this.utilModal && this.utilModal._el) ? this.utilModal._el : document;
        var tbody = root.querySelector('#' + this.id + '-tbody') || document.getElementById(this.id + '-tbody');
        if (tbody) {
            var row = tbody.querySelector('tr[data-index="' + idx + '"]');
            if (row) {
                var slCell = row.querySelector('.lm-col-sn');
                if (slCell && !slCell.textContent) {
                    slCell.textContent = (idx + 1);
                }
            }
        }
    };

    ListModal.prototype._onEnterKey = function (idx) {
        var currentVal = this.rows[idx] ? (this.rows[idx].value || '').trim() : '';
        if (!currentVal) {
            this._doSave();
            return;
        }
        
        var lowerVal = currentVal.toLowerCase();
        var dupIdx = this.rows.findIndex(function(r, i) {
            return i !== idx && (r.value || '').trim().toLowerCase() === lowerVal;
        });
        
        if (dupIdx !== -1) {
            this.rows[idx].value = '';
            this.renderRows();
            this._focusRow(dupIdx);
            if (window.showToast) window.showToast('Duplicate entry. Jumped to existing row.', 'warning');
            return;
        }

        var nextIdx = idx + 1;
        if (nextIdx >= this.rows.length) {
            this.rows.push({ value: '', isDefault: false });
        }
        this.renderRows();
        this._focusRow(nextIdx);
    };

    ListModal.prototype._doRemove = function () {
        if (this.selectedIndex >= 0 && this.selectedIndex < this.rows.length) {
            this.rows.splice(this.selectedIndex, 1);
            if (this.rows.length === 0) {
                this.rows.push({ value: '', isDefault: false });
            }
            if (this.selectedIndex >= this.rows.length) {
                this.selectedIndex = this.rows.length - 1;
            }
            this.renderRows();
            this._focusRow(this.selectedIndex);
        }
    };

    ListModal.prototype._doDefault = function () {
        var self = this;
        this.rows.forEach(function (r, i) {
            r.isDefault = (i === self.selectedIndex);
        });
        this.renderRows();
        this._focusRow(this.selectedIndex);
    };

    ListModal.prototype._doSave = function () {
        var self = this;
        var root = (this.utilModal && this.utilModal._el) ? this.utilModal._el : document;
        var tbody = root.querySelector('#' + this.id + '-tbody') || document.getElementById(this.id + '-tbody');
        if (tbody) {
            var inputs = tbody.querySelectorAll('.lm-cell-input');
            inputs.forEach(function (inp) {
                var idx = parseInt(inp.dataset.index, 10);
                if (!isNaN(idx) && inp.value !== undefined) {
                    while (self.rows.length <= idx) {
                        self.rows.push({ value: '', isDefault: false });
                    }
                    self.rows[idx].value = inp.value;
                }
            });
        }

        var nonBlank = [];
        var defaultVal = '';
        var seen = {};

        this.rows.forEach(function (r) {
            var val = (r.value || '').trim();
            if (val) {
                var key = val.toLowerCase();
                if (!seen[key]) {
                    seen[key] = true;
                    nonBlank.push(val);
                }
                if (r.isDefault && !defaultVal) {
                    defaultVal = val;
                }
            }
        });

        if (typeof this.cfg.onSave === 'function') {
            this.cfg.onSave(nonBlank, defaultVal, this);
        } else {
            this.close();
        }
    };

    ListModal.prototype.open = function (data) {
        if (data !== undefined) {
            this._initRows(data);
        }
        if (!this.utilModal) {
            this._build();
        }
        this.utilModal.open();
        this.renderRows();

        var self = this;
        setTimeout(function () {
            self._focusRow(0);
        }, 60);

        if (typeof this.cfg.onOpen === 'function') {
            this.cfg.onOpen(this);
        }
    };

    ListModal.prototype.close = function () {
        if (this.utilModal) this.utilModal.close();
    };

    // ── Global Helper for any ERP Screen ──────────────────────────────────
    var _commonListModals = {};

    global.openCommonListModal = function (targetFieldOrId, modalTitle, columnLabel) {
        var targetEl = typeof targetFieldOrId === 'string'
            ? document.getElementById(targetFieldOrId) || document.getElementById('id_' + targetFieldOrId)
            : targetFieldOrId;

        var elId = targetEl ? (targetEl.id || targetEl.name || 'field') : 'common';
        var modalId = 'lm-dialog-' + elId;
        var rawVal = targetEl ? targetEl.value : '';
        var initialList = rawVal.split(',').map(function (s) { return s.trim(); }).filter(Boolean);

        if (!_commonListModals[modalId]) {
            _commonListModals[modalId] = new ListModal({
                id: modalId,
                title: modalTitle || 'List Entries',
                columnLabel: columnLabel || 'Value',
                width: '480px',
                height: '260px',
                data: initialList,
                onSave: function (values, defVal, m) {
                    var curEl = m._currentTargetEl;
                    if (curEl) {
                        var seen = {};
                        var uniqueVals = [];
                        values.forEach(function (v) {
                            var t = (v || '').trim();
                            var k = t.toLowerCase();
                            if (t && !seen[k]) {
                                seen[k] = true;
                                uniqueVals.push(t);
                            }
                        });
                        var isBarcode = (columnLabel && columnLabel.toLowerCase().indexOf('barcode') !== -1) ||
                                        (modalTitle && modalTitle.toLowerCase().indexOf('barcode') !== -1) ||
                                        (curEl.id && curEl.id.toLowerCase().indexOf('barcode') !== -1);
                        var formatted = isBarcode
                            ? uniqueVals.join(', ')
                            : uniqueVals.map(function (v) {
                                return v.toLowerCase() === (defVal || '').trim().toLowerCase() ? (v + ' (Default)') : v;
                            }).join(', ');
                        curEl.value = formatted;
                        curEl.dispatchEvent(new Event('input', { bubbles: true }));
                        curEl.dispatchEvent(new Event('change', { bubbles: true }));
                    }
                    m.close();
                    if (curEl) curEl.focus();
                }
            });
        }

        var modal = _commonListModals[modalId];
        modal._currentTargetEl = targetEl;
        modal.open(initialList);
        return modal;
    };

    global.ListModal = ListModal;
    global.THEME_ICONS = THEME_ICONS;

})(window);
