/**
 * ═══════════════════════════════════════════════════════════════════════════
 * common/static/common/js/multi_price_modal.js
 *
 * Universal Multiple Price Level Modal & Multi-Unit Manager Component.
 * Exact visual fidelity to D:\PROJECTS\Reference\multi_price.png.
 * Integrated with UtilityModal, theme_constants.py button styles & SVGs.
 * ═══════════════════════════════════════════════════════════════════════════
 */

(function (global) {
    'use strict';

    /* Official SVGs matching common/theme_constants.py */
    var THEME_ICONS = {
        confirm: (
            '<svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">' +
            '<polyline points="9 11 12 14 22 4"/>' +
            '<path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/>' +
            '</svg>'
        ),
        cancel: (
            '<svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">' +
            '<circle cx="12" cy="12" r="10"/>' +
            '<line x1="4.93" y1="4.93" x2="19.07" y2="19.07"/>' +
            '</svg>'
        ),
        add: (
            '<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">' +
            '<circle cx="12" cy="12" r="10"/>' +
            '<line x1="12" y1="8" x2="12" y2="16"/>' +
            '<line x1="8" y1="12" x2="16" y2="12"/>' +
            '</svg>'
        ),
        edit: (
            '<svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">' +
            '<path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>' +
            '<path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>' +
            '</svg>'
        ),
        remove: (
            '<svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">' +
            '<circle cx="12" cy="12" r="10"/>' +
            '<line x1="8" y1="12" x2="16" y2="12"/>' +
            '</svg>'
        ),
        infinity: (
            '<path d="M18.178 8c5.096 0 5.096 8 0 8-5.095 0-7.267-8-12.356-8-5.096 0-5.096 8 0 8 5.096 0 7.261-8 12.356-8z" stroke-width="2"/>'
        )
    };

    /**
     * ── MultiPriceModal ───────────────────────────────────────────────────
     * Reusable dialog matching multi_price.png
     */
    function MultiPriceModal(cfg) {
        this.cfg = cfg || {};
        this.id = cfg.id || 'mp-modal-' + Math.random().toString(36).substr(2, 8);
        this.onConfirm = cfg.onConfirm || function () {};
        this.onCancel = cfg.onCancel || function () {};
        this.modal = null;
        this.activeUnit = null;
        this._build();
    }

    MultiPriceModal.prototype._build = function () {
        var self = this;

        this.modal = new UtilityModal({
            id       : self.id,
            title    : 'Multiple Price Level',
            subtitle : '',
            icon     : THEME_ICONS.infinity,
            width    : '490px',
            height   : '410px',
            tabs     : [
                { id: 'pricing_tab', label: 'Pricing Matrix' }
            ],
            toolbar  : [],
            onBuild  : function (m) {
                if (m._el) {
                    var box = m._el.querySelector('.utm-modal');
                    if (box) box.classList.add('utm-modal--multi-price');
                }

                var nav = document.getElementById(self.id + '-nav');
                if (nav) nav.style.display = 'none';

                var pane = m.pane('pricing_tab');
                if (!pane) return;
                pane.style.padding = '0';
                pane.style.display = 'flex';
                pane.style.flexDirection = 'column';
                pane.style.height = '100%';
                pane.style.minHeight = '0';
                pane.style.overflowY = 'auto';

                pane.innerHTML = self._generateHTML();
                self._bindEvents(pane);
            }
        });
    };

    MultiPriceModal.prototype._generateHTML = function () {
        return (
            '<div class="mp-container">' +
                '<div class="mp-body">' +

                    /* Row 1: Base Rate (Label, Dropdown, Value) */
                    '<div class="mp-base-row">' +
                        '<label class="mp-base-lbl" for="mp-base-val">Base Rate</label>' +
                        '<select class="mp-base-select" id="mp-base-type">' +
                            '<option value="P.Price">P.Price</option>' +
                            '<option value="Cost">Cost</option>' +
                            '<option value="Landing Cost">Landing Cost</option>' +
                            '<option value="Selling Price">Selling Price</option>' +
                            '<option value="Custom">Custom</option>' +
                        '</select>' +
                        '<input type="number" step="0.01" class="mp-base-inp" id="mp-base-val" value="0.00">' +
                    '</div>' +

                    /* Matrix: MRP, DRP, FDP, Branch (Rate(%) and Amount) */
                    '<div class="mp-table-wrap">' +
                        '<table class="mp-table">' +
                            '<thead>' +
                                '<tr>' +
                                    '<th></th>' +
                                    '<th>Rate(%)</th>' +
                                    '<th>Amount</th>' +
                                '</tr>' +
                            '</thead>' +
                            '<tbody>' +
                                '<tr>' +
                                    '<td class="mp-row-lbl">MRP</td>' +
                                    '<td><input type="number" step="0.01" class="mp-cell-inp" id="mp-rate-mrp" placeholder="0.00"></td>' +
                                    '<td><input type="number" step="0.01" class="mp-cell-inp" id="mp-amt-mrp" value="0.00"></td>' +
                                '</tr>' +
                                '<tr>' +
                                    '<td class="mp-row-lbl">DRP</td>' +
                                    '<td><input type="number" step="0.01" class="mp-cell-inp" id="mp-rate-drp" placeholder="0.00"></td>' +
                                    '<td><input type="number" step="0.01" class="mp-cell-inp" id="mp-amt-drp" value="0.00"></td>' +
                                '</tr>' +
                                '<tr>' +
                                    '<td class="mp-row-lbl">FDP</td>' +
                                    '<td><input type="number" step="0.01" class="mp-cell-inp" id="mp-rate-fdp" placeholder="0.00"></td>' +
                                    '<td><input type="number" step="0.01" class="mp-cell-inp" id="mp-amt-fdp" value="0.00"></td>' +
                                '</tr>' +
                                '<tr>' +
                                    '<td class="mp-row-lbl">Branch</td>' +
                                    '<td><input type="number" step="0.01" class="mp-cell-inp" id="mp-rate-branch" placeholder="0.00"></td>' +
                                    '<td><input type="number" step="0.01" class="mp-cell-inp" id="mp-amt-branch" value="0.00"></td>' +
                                '</tr>' +
                            '</tbody>' +
                        '</table>' +
                    '</div>' +

                    /* Secondary Fields (Discount, MRP, LUC, PCS Cost, Location) */
                    '<div class="mp-sec-grid">' +
                        '<div class="mp-sec-row">' +
                            '<div class="mp-sec-cell">' +
                                '<label class="mp-sec-lbl" for="mp-sec-disc">Discount</label>' +
                                '<input type="number" step="0.01" class="mp-sec-inp" id="mp-sec-disc" value="0.00">' +
                            '</div>' +
                            '<div class="mp-sec-cell">' +
                                '<label class="mp-sec-lbl-sub" for="mp-sec-mrp2">MRP</label>' +
                                '<input type="number" step="0.01" class="mp-sec-inp" id="mp-sec-mrp2" value="0.00">' +
                            '</div>' +
                        '</div>' +

                        '<div class="mp-sec-row">' +
                            '<div class="mp-sec-cell">' +
                                '<label class="mp-sec-lbl" for="mp-sec-luc">LUC</label>' +
                                '<input type="number" step="0.01" class="mp-sec-inp" id="mp-sec-luc" value="0.00">' +
                            '</div>' +
                            '<div class="mp-sec-cell">' +
                                '<label class="mp-sec-lbl-sub" for="mp-sec-pcs">PCS Cost</label>' +
                                '<input type="number" step="0.01" class="mp-sec-inp" id="mp-sec-pcs" placeholder="0.00">' +
                            '</div>' +
                        '</div>' +
                    '</div>' +
                '</div>' +

                /* Bottom Action Bar: Confirm and Cancel */
                '<div class="mp-action-bar">' +
                    '<button type="button" class="pf-tb-btn" id="mp-btn-confirm" title="Confirm">' +
                        '<span class="pf-tb-btn-icon">' + THEME_ICONS.confirm + '</span>' +
                        '<span style="text-decoration:underline;">C</span>onfirm' +
                    '</button>' +
                    '<button type="button" class="pf-tb-btn pf-tb-btn-danger" id="mp-btn-cancel" title="Cancel">' +
                        '<span class="pf-tb-btn-icon">' + THEME_ICONS.cancel + '</span>' +
                        '<span style="text-decoration:underline;">C</span>ancel' +
                    '</button>' +
                '</div>' +
            '</div>'
        );
    };

    MultiPriceModal.prototype._bindEvents = function (pane) {
        var self = this;
        var rows = ['mrp', 'drp', 'fdp', 'branch'];

        var baseInp = pane.querySelector('#mp-base-val');
        var baseSelect = pane.querySelector('#mp-base-type');
        var discInp = pane.querySelector('#mp-sec-disc');
        var mrp2Inp = pane.querySelector('#mp-sec-mrp2');
        var lucInp = pane.querySelector('#mp-sec-luc');
        var pcsInp = pane.querySelector('#mp-sec-pcs');
        var locInp = pane.querySelector('#mp-sec-loc');
        var locBtn = pane.querySelector('#mp-btn-loc-list');
        var confirmBtn = pane.querySelector('#mp-btn-confirm');
        var cancelBtn = pane.querySelector('#mp-btn-cancel');

        // Location entry via ListModal
        function openLocationList(e) {
            if (e) { e.preventDefault(); e.stopPropagation(); }
            var currentVal = (locInp ? locInp.value : '') || '';
            var initialList = currentVal ? currentVal.split(',').map(function(s) { return s.trim(); }).filter(Boolean) : [];
            if (!self.locationModal) {
                self.locationModal = new ListModal({
                    id: self.id + '-loc-list-modal',
                    title: 'Position / Location Entry',
                    columnLabel: 'Position / Bin Location',
                    width: '480px',
                    height: '260px',
                    minRows: 8,
                    data: initialList,
                    onSave: function(values, defaultVal, m) {
                        if (locInp) {
                            var formatted = values.map(function(v) {
                                return v === defaultVal ? (v + ' (Default)') : v;
                            }).join(', ');
                            locInp.value = formatted;
                        }
                        m.close();
                        if (locInp) locInp.focus();
                    }
                });
            }
            self.locationModal.open(initialList);
        }

        if (locInp) {
            locInp.addEventListener('click', openLocationList);
            locInp.addEventListener('keydown', function(e) {
                if (e.key === ' ' || e.key === 'Enter') {
                    openLocationList(e);
                }
            });
        }
        if (locBtn) locBtn.addEventListener('click', openLocationList);

        // Two-way calculation handlers
        function getBase() {
            var v = parseFloat(baseInp.value);
            return isNaN(v) ? 0 : v;
        }

        function recalcAllFromBase() {
            var b = getBase();
            rows.forEach(function (r) {
                var rateInp = pane.querySelector('#mp-rate-' + r);
                var amtInp = pane.querySelector('#mp-amt-' + r);
                var rateVal = parseFloat(rateInp.value);
                if (!isNaN(rateVal)) {
                    var amt = b * (1 + (rateVal / 100));
                    amtInp.value = amt.toFixed(2);
                    if (r === 'mrp' && mrp2Inp) mrp2Inp.value = amt.toFixed(2);
                }
            });
        }

        // On Base Rate change
        if (baseInp) {
            baseInp.addEventListener('input', recalcAllFromBase);
        }

        // On Base Rate Select Type change
        if (baseSelect) {
            baseSelect.addEventListener('change', function () {
                var t = baseSelect.value;
                var pPrice = parseFloat((document.getElementById('id_purchase_price') || {}).value) || 0;
                var sPrice = parseFloat((document.getElementById('id_selling_price') || {}).value) || 0;
                var lastPrice = parseFloat((document.getElementById('id_last_purchase_price') || {}).value) || pPrice;

                var factor = self.activeUnit ? (parseFloat(self.activeUnit.factor) || 1) : 1;

                if (t === 'P.Price') {
                    baseInp.value = (pPrice * factor).toFixed(2);
                } else if (t === 'Selling Price') {
                    baseInp.value = (sPrice * factor).toFixed(2);
                } else if (t === 'Cost' || t === 'Landing Cost') {
                    baseInp.value = (lastPrice * factor).toFixed(2);
                }
                recalcAllFromBase();
            });
        }

        // Row calculations (Rate <-> Amount)
        rows.forEach(function (r) {
            var rateInp = pane.querySelector('#mp-rate-' + r);
            var amtInp = pane.querySelector('#mp-amt-' + r);

            if (rateInp && amtInp) {
                // Changing Rate calculates Amount
                rateInp.addEventListener('input', function () {
                    var b = getBase();
                    var rateVal = parseFloat(rateInp.value);
                    if (!isNaN(rateVal)) {
                        var calculatedAmt = b * (1 + (rateVal / 100));
                        amtInp.value = calculatedAmt.toFixed(2);
                        if (r === 'mrp' && mrp2Inp) mrp2Inp.value = calculatedAmt.toFixed(2);
                    }
                });

                // Changing Amount calculates Rate
                amtInp.addEventListener('input', function () {
                    var b = getBase();
                    var amtVal = parseFloat(amtInp.value);
                    if (!isNaN(amtVal) && b > 0) {
                        var calculatedRate = ((amtVal / b) - 1) * 100;
                        rateInp.value = calculatedRate.toFixed(2);
                    }
                    if (r === 'mrp' && mrp2Inp) {
                        mrp2Inp.value = amtInp.value;
                    }
                });
            }
        });

        // Mirror secondary MRP change back to table MRP
        if (mrp2Inp) {
            mrp2Inp.addEventListener('input', function () {
                var amtMrp = pane.querySelector('#mp-amt-mrp');
                if (amtMrp) {
                    amtMrp.value = mrp2Inp.value;
                    amtMrp.dispatchEvent(new Event('input'));
                }
            });
        }

        // Action Buttons
        if (confirmBtn) {
            confirmBtn.addEventListener('click', function () {
                var data = self.getValues();
                if (typeof self.onConfirm === 'function') {
                    self.onConfirm(data, self.activeUnit);
                }
                self.close();
            });
        }

        if (cancelBtn) {
            cancelBtn.addEventListener('click', function () {
                if (typeof self.onCancel === 'function') {
                    self.onCancel();
                }
                self.close();
            });
        }

        // Keyboard flow: Enter key navigation
        var inputSequence = [
            baseInp,
            pane.querySelector('#mp-rate-mrp'), pane.querySelector('#mp-amt-mrp'),
            pane.querySelector('#mp-rate-drp'), pane.querySelector('#mp-amt-drp'),
            pane.querySelector('#mp-rate-fdp'), pane.querySelector('#mp-amt-fdp'),
            pane.querySelector('#mp-rate-branch'), pane.querySelector('#mp-amt-branch'),
            discInp, mrp2Inp, lucInp, pcsInp, locInp
        ].filter(Boolean);

        inputSequence.forEach(function (inp, idx) {
            inp.addEventListener('keydown', function (e) {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    if (idx < inputSequence.length - 1) {
                        inputSequence[idx + 1].focus();
                        if (inputSequence[idx + 1].select) inputSequence[idx + 1].select();
                    } else if (confirmBtn) {
                        confirmBtn.focus();
                    }
                }
            });
        });
    };

    MultiPriceModal.prototype.open = function (initialData, unitContext) {
        this.activeUnit = unitContext || null;
        var modalEl = this.modal._el;

        // Set title with unit context
        var titleText = 'Multiple Price Level';
        if (unitContext && unitContext.unit_name) {
            titleText += ' — ' + unitContext.unit_name;
            if (unitContext.factor) {
                titleText += ' (Factor: ' + unitContext.factor + ')';
            }
        }
        var titleEl = modalEl ? modalEl.querySelector('.utm-title') : null;
        if (titleEl) titleEl.innerText = titleText;

        // Open modal frame
        this.modal.open();

        // Populate fields
        this.setValues(initialData || {});

        // Focus first active input
        var baseInp = modalEl ? modalEl.querySelector('#mp-base-val') : null;
        if (baseInp) {
            setTimeout(function () {
                baseInp.focus();
                if (baseInp.select) baseInp.select();
            }, 60);
        }
    };

    MultiPriceModal.prototype.close = function () {
        if (this.modal) this.modal.close();
    };

    MultiPriceModal.prototype.setValues = function (d) {
        var pane = this.modal.pane('pricing_tab');
        if (!pane) return;

        d = d || {};
        var bType = pane.querySelector('#mp-base-type');
        var bVal  = pane.querySelector('#mp-base-val');
        if (bType) bType.value = d.base_type || 'P.Price';
        if (bVal)  bVal.value  = d.base_rate !== undefined ? d.base_rate : '0.00';

        ['mrp', 'drp', 'fdp', 'branch'].forEach(function (r) {
            var rate = pane.querySelector('#mp-rate-' + r);
            var amt  = pane.querySelector('#mp-amt-' + r);
            if (rate) rate.value = d[r + '_rate'] !== undefined ? d[r + '_rate'] : '';
            if (amt)  amt.value  = d[r + '_amt'] !== undefined ? d[r + '_amt'] : '0.00';
        });

        var disc = pane.querySelector('#mp-sec-disc');
        var mrp2 = pane.querySelector('#mp-sec-mrp2');
        var luc  = pane.querySelector('#mp-sec-luc');
        var pcs  = pane.querySelector('#mp-sec-pcs');
        var loc  = pane.querySelector('#mp-sec-loc');

        if (disc) disc.value = d.discount !== undefined ? d.discount : '0.00';
        if (mrp2) mrp2.value = d.mrp !== undefined ? d.mrp : '0.00';
        if (luc)  luc.value  = d.luc !== undefined ? d.luc : '0.00';
        if (pcs)  pcs.value  = d.pcs_cost !== undefined ? d.pcs_cost : '';
        if (loc)  loc.value  = d.location || '';
    };

    MultiPriceModal.prototype.getValues = function () {
        var pane = this.modal.pane('pricing_tab');
        if (!pane) return {};

        var val = function (sel) {
            var el = pane.querySelector(sel);
            return el ? el.value : '';
        };

        return {
            base_type    : val('#mp-base-type'),
            base_rate    : val('#mp-base-val'),
            mrp_rate     : val('#mp-rate-mrp'),
            mrp_amt      : val('#mp-amt-mrp'),
            drp_rate     : val('#mp-rate-drp'),
            drp_amt      : val('#mp-amt-drp'),
            fdp_rate     : val('#mp-rate-fdp'),
            fdp_amt      : val('#mp-amt-fdp'),
            branch_rate  : val('#mp-rate-branch'),
            branch_amt   : val('#mp-amt-branch'),
            discount     : val('#mp-sec-disc'),
            mrp          : val('#mp-sec-mrp2'),
            luc          : val('#mp-sec-luc'),
            pcs_cost     : val('#mp-sec-pcs'),
            location     : val('#mp-sec-loc')
        };
    };


    /**
     * ── MultiUnitManager v2 ───────────────────────────────────────────────
     * Single inline-editable table: UnitName | Factor | Barcode | Price
     * Fixed 5 rows. No Add/Delete.
     */
    function MultiUnitManager(containerId, initialUnits) {
        this.container = typeof containerId === 'string'
            ? document.getElementById(containerId)
            : containerId;
        this.units  = Array.isArray(initialUnits) ? JSON.parse(JSON.stringify(initialUnits)) : [];
        this.modals = {};   /* keyed by row index — one MultiPriceModal per row */
        this._barcodeModal = null;
        this._barcodeTarget = null; /* { idx, callback } */
        
        /* Ensure exactly 6 rows */
        while (this.units.length < 6) {
            this.units.push({ unit_name: '', factor: '', barcodes: '', prices: {} });
        }
        if (this.units.length > 6) {
            this.units = this.units.slice(0, 6);
        }
        
        this._init();
    }

    MultiUnitManager.prototype._init = function () {
        this.render();
        this.syncToForm();
    };

    /* ── Render the full table ─────────────────────────────────────────── */
    MultiUnitManager.prototype.render = function () {
        if (!this.container) return;
        var self = this;

        var opts = window.MU_UNIT_OPTIONS || null;

        var html =
            '<div class="mu-container" style="overflow-x:auto;">' +
                '<table class="pf-tbl mu-tbl" style="width:100%; border-collapse:collapse; font-size:12px;">' +
                    '<colgroup>' +
                        '<col style="width:36px">' +
                        '<col style="width:170px">' +
                        '<col style="width:110px">' +
                        '<col style="">' +
                        '<col style="width:110px">' +
                    '</colgroup>' +
                    '<thead>' +
                        '<tr style="background:var(--color-bg-tertiary);">' +
                            '<th style="padding:5px 6px; text-align:center; border-bottom:1px solid var(--color-border-light); font-size:11px; color:var(--color-text-muted);">#</th>' +
                            '<th style="padding:5px 6px; border-bottom:1px solid var(--color-border-light); font-size:11px;">Unit Name</th>' +
                            '<th style="padding:5px 6px; border-bottom:1px solid var(--color-border-light); font-size:11px;">Conversion</th>' +
                            '<th style="padding:5px 6px; border-bottom:1px solid var(--color-border-light); font-size:11px;">Barcode(s)</th>' +
                            '<th style="padding:5px 6px; border-bottom:1px solid var(--color-border-light); font-size:11px; text-align:center;">Price Levels</th>' +
                        '</tr>' +
                    '</thead>' +
                    '<tbody id="mu-tbody">';

        this.units.forEach(function (u, i) {
            var p = u.prices || {};
            var hasPrices = p.base_rate && parseFloat(p.base_rate) > 0;
            var priceLbl  = hasPrices
                ? (p.base_rate ? 'Base: ' + parseFloat(p.base_rate).toFixed(2) : 'Edit')
                : 'Set Prices';

            /* Unit Name cell */
            var nameCell;
            if (opts) {
                nameCell = '<select data-mu-field="unit_name" data-allow-add="1" data-mu-row="' + i + '" ' +
                    'style="width:100%; height:24px; font-size:11.5px; border:1px solid var(--color-border-light); ' +
                    'border-radius:3px; padding:0 4px; background:var(--color-bg-secondary); color:var(--color-text-primary);">';
                nameCell += '<option value="">— Select —</option>';
                opts.forEach(function (o) {
                    var sel = (o.value === u.unit_name || o.label === u.unit_name) ? ' selected' : '';
                    nameCell += '<option value="' + _escHtml(o.value) + '"' + sel + '>' + _escHtml(o.label) + '</option>';
                });
                nameCell += '</select>';
            } else {
                nameCell = '<input type="text" data-mu-field="unit_name" data-mu-row="' + i + '" ' +
                    'value="' + _escHtml(u.unit_name || '') + '" placeholder="e.g. Pack" ' +
                    'style="width:100%; height:24px; font-size:11.5px; border:1px solid var(--color-border-light); ' +
                    'border-radius:3px; padding:0 6px; box-sizing:border-box;">';
            }

            html +=
                '<tr data-mu-row="' + i + '" style="border-bottom:1px solid var(--color-border-light);">' +
                    '<td style="text-align:center; color:var(--color-text-muted); font-size:11px; padding:4px 2px;">' + (i + 1) + '</td>' +
                    '<td style="padding:3px 4px;">' + nameCell + '</td>' +
                    '<td style="padding:3px 4px;">' +
                        '<input type="number" step="0.0001" data-mu-field="factor" data-mu-row="' + i + '" ' +
                        'value="' + _escHtml(u.factor || '') + '" placeholder="e.g. 0.1" ' +
                        'style="width:100%; height:24px; font-size:11.5px; border:1px solid var(--color-border-light); ' +
                        'border-radius:3px; padding:0 6px; box-sizing:border-box;">' +
                    '</td>' +
                    '<td style="padding:3px 4px;">' +
                        '<div style="display:flex; align-items:center; gap:3px;">' +
                            '<input type="text" readonly data-mu-field="barcodes" data-mu-row="' + i + '" ' +
                            'value="' + _escHtml(u.barcodes || '') + '" placeholder="Click to add…" ' +
                            'style="flex:1; height:24px; font-size:11px; border:1px solid var(--color-border-light); ' +
                            'border-radius:3px 0 0 3px; padding:0 6px; cursor:pointer; box-sizing:border-box; background:var(--color-bg-secondary);">' +
                            '<button type="button" data-mu-barcode-btn="' + i + '" title="Open Barcodes" ' +
                            'style="height:24px; width:24px; flex-shrink:0; border:1px solid var(--color-border-light); border-left:none; ' +
                            'border-radius:0 3px 3px 0; background:var(--color-bg-tertiary); cursor:pointer; ' +
                            'display:inline-flex; align-items:center; justify-content:center; padding:0;">' +
                                '<svg viewBox="0 0 24 24" width="11" height="11" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>' +
                            '</button>' +
                        '</div>' +
                    '</td>' +
                    '<td style="padding:3px 4px; text-align:center;">' +
                        '<button type="button" data-mu-price-btn="' + i + '" ' +
                        'style="height:24px; padding:0 8px; font-size:11px; border:1px solid var(--color-border-light); ' +
                        'border-radius:3px; background:' + (hasPrices ? 'var(--color-primary)' : 'var(--color-bg-tertiary)') + '; ' +
                        'color:' + (hasPrices ? '#fff' : 'var(--color-text-primary)') + '; cursor:pointer; white-space:nowrap;">' +
                            (hasPrices ? '✓ ' : '') + _escHtml(priceLbl) +
                        '</button>' +
                    '</td>' +
                '</tr>';
        });

        html +=
                    '</tbody>' +
                '</table>' +
            '</div>';

        this.container.innerHTML = html;
        this._bindEvents();

        // Apply custom pf_select design to units dropdown
        if (typeof window.pfSelUpgradeOne === 'function') {
            this.container.querySelectorAll('select').forEach(function(sel) {
                window.pfSelUpgradeOne(sel);
            });
        }
    };

    /* ── Bind all events ──────────────────────────────────────────────── */
    MultiUnitManager.prototype._bindEvents = function () {
        var self = this;
        if (!this.container) return;

        /* Inline field changes (unit_name, factor) → update units array */
        this.container.querySelectorAll('[data-mu-field]').forEach(function (el) {
            var field = el.getAttribute('data-mu-field');
            var rowIdx = parseInt(el.getAttribute('data-mu-row'), 10);
            if (field === 'barcodes') return; /* barcode is readonly, handled by modal */

            el.addEventListener('change', function () {
                if (self.units[rowIdx] !== undefined) {
                    self.units[rowIdx][field] = el.value;
                    self.syncToForm();
                }
            });
            /* For number inputs also on input event */
            if (el.type === 'number') {
                el.addEventListener('input', function () {
                    if (self.units[rowIdx] !== undefined) {
                        self.units[rowIdx][field] = el.value;
                        self.syncToForm();
                    }
                });
            }
        });

        /* Barcode buttons */
        this.container.querySelectorAll('[data-mu-barcode-btn]').forEach(function (btn) {
            btn.addEventListener('click', function (e) {
                e.preventDefault(); e.stopPropagation();
                var rowIdx = parseInt(btn.getAttribute('data-mu-barcode-btn'), 10);
                self._openBarcodeModal(rowIdx);
            });
        });

        /* Barcode input click (readonly — opens modal) */
        this.container.querySelectorAll('[data-mu-field="barcodes"]').forEach(function (inp) {
            inp.addEventListener('click', function (e) {
                e.preventDefault(); e.stopPropagation();
                var rowIdx = parseInt(inp.getAttribute('data-mu-row'), 10);
                self._openBarcodeModal(rowIdx);
            });
        });

        /* Price buttons */
        this.container.querySelectorAll('[data-mu-price-btn]').forEach(function (btn) {
            btn.addEventListener('click', function (e) {
                e.preventDefault(); e.stopPropagation();
                var rowIdx = parseInt(btn.getAttribute('data-mu-price-btn'), 10);
                self._openPriceModal(rowIdx);
            });
        });

        /* Enter-key progression within a row: unit_name → factor → price modal */
        this.container.querySelectorAll('[data-mu-field="unit_name"], [data-mu-field="factor"]').forEach(function (el) {
            el.addEventListener('keydown', function (e) {
                if (e.key !== 'Enter') return;
                e.preventDefault();
                var rowIdx = parseInt(el.getAttribute('data-mu-row'), 10);
                var field  = el.getAttribute('data-mu-field');
                if (field === 'unit_name') {
                    var factorEl = self.container.querySelector('[data-mu-field="factor"][data-mu-row="' + rowIdx + '"]');
                    if (factorEl) { factorEl.focus(); if (factorEl.select) factorEl.select(); }
                } else if (field === 'factor') {
                    /* Open price modal directly from factor Enter */
                    self._openPriceModal(rowIdx);
                }
            });
        });
    };

    /* ── Open Barcode modal for a given row ───────────────────────────── */
    MultiUnitManager.prototype._openBarcodeModal = function (rowIdx) {
        var self = this;
        var u    = this.units[rowIdx];
        if (!u) return;

        var initialList = (u.barcodes || '')
            .split(',')
            .map(function (s) { return s.trim(); })
            .filter(Boolean);

        /* Reuse a single cached barcodeModal, updating its onSave callback */
        if (!this._barcodeModal) {
            this._barcodeModal = new ListModal({
                id: 'mu-barcode-list-modal',
                title: 'Barcodes Entry',
                columnLabel: 'Barcode',
                width: '480px',
                height: '260px',
                minRows: 8,
                data: initialList,
                onSave: function (values, defaultVal, m) {
                    var target = self._barcodeTarget;
                    if (target !== null && self.units[target]) {
                        var formatted = values.join(', ');
                        self.units[target].barcodes = formatted;
                        /* Update the readonly input display without full re-render */
                        var inp = self.container && self.container.querySelector(
                            '[data-mu-field="barcodes"][data-mu-row="' + target + '"]'
                        );
                        if (inp) inp.value = formatted;
                        self.syncToForm();
                    }
                    m.close();
                }
            });
        }
        this._barcodeTarget = rowIdx;
        this._barcodeModal.open(initialList);
    };

    /* ── Open Price modal for a given row ────────────────────────────── */
    MultiUnitManager.prototype._openPriceModal = function (rowIdx) {
        var self = this;
        var u    = this.units[rowIdx];
        if (!u) return;

        /* One MultiPriceModal instance per row, cached by index */
        if (!this.modals[rowIdx]) {
            this.modals[rowIdx] = new MultiPriceModal({
                id: 'mu-price-modal-' + rowIdx,
                onConfirm: function (priceData) {
                    if (self.units[rowIdx]) {
                        self.units[rowIdx].prices = priceData;
                    }
                    /* Re-render to update price button colour/label */
                    self.render();
                    self.syncToForm();
                }
            });
        }

        var pPrice  = parseFloat((document.getElementById('id_purchase_price') || {}).value) || 0;
        var factor  = parseFloat(u.factor) || 1;
        var initBase = (pPrice * factor).toFixed(2);

        var defaultPrices = Object.keys(u.prices || {}).length
            ? u.prices
            : {
                base_type: 'P.Price',
                base_rate: initBase,
                mrp_amt:   initBase,
                drp_amt:   initBase,
                fdp_amt:   initBase,
                branch_amt: initBase,
                mrp: initBase
            };

        this.modals[rowIdx].open(defaultPrices, u);
    };

    /* ── Sync data to hidden form fields ─────────────────────────────── */
    MultiUnitManager.prototype.syncToForm = function () {
        var filtered = this.units.filter(function (u) { return u.unit_name || u.factor; });

        var jsonInp = document.getElementById('id_multiunit_data');
        if (jsonInp) {
            jsonInp.value = JSON.stringify(filtered);
            jsonInp.dispatchEvent(new Event('change', { bubbles: true }));
        }

        /* Backwards compat: Unit1..Unit6 hidden fields */
        for (var i = 1; i <= 6; i++) {
            var u       = filtered[i - 1];
            var nameEl  = document.getElementById('id_Unit' + i);
            var facEl   = document.getElementById('id_Unit' + i + 'Conversion');
            var bcEl    = document.getElementById('id_Unit' + i + 'Barcode');
            if (nameEl)  nameEl.value  = u ? (u.unit_name || '') : '';
            if (facEl)   facEl.value   = u ? (u.factor    || '') : '';
            if (bcEl)    bcEl.value    = u ? (u.barcodes  || '') : '';
        }
    };

    /* ── HTML escape helper ──────────────────────────────────────────── */
    function _escHtml(s) {
        return String(s || '').replace(/&/g,'&amp;').replace(/"/g,'&quot;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
    }

    // Export to global scope
    global.MultiPriceModal = MultiPriceModal;
    global.MultiUnitManager = MultiUnitManager;

})(window);

