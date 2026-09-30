/**
 * common/static/common/js/default_settings_modal.js
 * ═══════════════════════════════════════════════════════════════════
 *  Default Settings Modal  — built on top of UtilityModal engine
 *
 *  Main modal (id: 'defsett-modal'):
 *    Left sidebar: Inventory | Global
 *    Inventory pane : toggle switches for multiunit & group visibility
 *    Global pane    : placeholder / future use
 *    Both panes have a "Set Captions" action button
 *
 *  Captions modal (id: 'defsett-cap-modal'):
 *    Opened from "Set Captions" button
 *    Grid layout matching caption.png reference:
 *      Col 1 : Rate0–Rate5 (6 price levels)
 *      Col 2 : Group1–Group5 (5 item groups) + Warehouse
 *      Col 3 : Company / Category / Brand
 *      Col 4 : City / Area / District / State
 *    Caption keys are UPPERCASE to match ChartOfCode Code column,
 *    aligned with existing get_rate_captions() in item_master.py.
 *
 *  DEPENDS ON (must load first):
 *    1. utilities_modal.js  ← UtilityModal engine
 *    2. profile_form.js     ← pfToast, showConfirm
 * ═══════════════════════════════════════════════════════════════════
 */

(function (global) {
    'use strict';

    /* ── Guard ───────────────────────────────────────────────────────────── */
    if (typeof global.UtilityModal === 'undefined') {
        console.error('[DefaultSettings] UtilityModal not found — load utilities_modal.js first.');
        global.openDefaultSettings         = function () {};
        global.openDefaultSettingsCaptions = function () {};
        return;
    }

    /* ── Helpers ─────────────────────────────────────────────────────────── */
    function _toast(msg, type) {
        if (typeof global.pfToast === 'function') global.pfToast(msg, type);
        else console.info('[DS toast]', type, msg);
    }

    function _csrf() {
        var m = document.cookie.match(/csrftoken=([^;]+)/);
        return m ? decodeURIComponent(m[1]) : '';
    }

    /* ── Toggle-switch HTML builder ──────────────────────────────────────── */
    function _buildToggleRow(id, label, desc, defaultVal) {
        var checked = (defaultVal === 'true' || defaultVal === true) ? 'checked' : '';
        return (
            '<div class="ds-toggle-row">' +
              '<div class="ds-toggle-info">' +
                '<span class="ds-toggle-label">' + label + '</span>' +
                (desc ? '<span class="ds-toggle-desc">' + desc + '</span>' : '') +
              '</div>' +
              '<label class="ds-toggle-ctl" style="cursor:pointer;">' +
                '<input type="checkbox" id="' + id + '" name="' + id + '" ' + checked + '>' +
                '<span class="ds-switch"></span>' +
              '</label>' +
            '</div>'
        );
    }

    /* ── Set Captions action button HTML ─────────────────────────────────── */
    function _buildSetCaptionsBtn() {
        return (
            '<div class="ds-action-list" style="margin-top:20px;">' +
              '<button type="button" class="ds-action-btn" onclick="openDefaultSettingsCaptions()">' +
                '<div class="ds-action-btn-ico">' +
                  '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor"' +
                  ' stroke-width="2" stroke-linecap="round" stroke-linejoin="round">' +
                    '<path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>' +
                    '<path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>' +
                  '</svg>' +
                '</div>' +
                '<div class="ds-action-btn-info">' +
                  '<span class="ds-action-btn-label">Set Captions</span>' +
                  '<span class="ds-action-btn-desc">Customise field labels shown across forms and reports</span>' +
                '</div>' +
                '<div class="ds-action-btn-arrow">' +
                  '<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor"' +
                  ' stroke-width="2" stroke-linecap="round" stroke-linejoin="round">' +
                    '<polyline points="9 18 15 12 9 6"/>' +
                  '</svg>' +
                '</div>' +
              '</button>' +
            '</div>'
        );
    }

    /* ═══════════════════════════════════════════════════════════════════════
       MAIN DEFAULT SETTINGS MODAL
    ═══════════════════════════════════════════════════════════════════════ */
    var _mainModal = null;

    function _buildMainModal() {
        if (_mainModal) return _mainModal;

        _mainModal = new UtilityModal({
            id      : 'defsett-modal',
            title   : 'Default Settings',
        size: 'md',
            subtitle: 'Configure application defaults',
            icon    : '<path d="M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6z"/>' +
                      '<path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06' +
                      'a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09' +
                      'A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06' +
                      'A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09' +
                      'A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06' +
                      'A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09' +
                      'a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06' +
                      'A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09' +
                      'a1.65 1.65 0 0 0-1.51 1z"/>',
            width   : '820px',
            height  : '72vh',

            tabs: [
                {
                    id   : 'inventory',
                    label: '» Inventory',
                    icon : '<path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/>'
                },
                {
                    id   : 'global',
                    label: '» Global',
                    icon : '<circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>'
                },
            ],

            toolbar: [
                {
                    label  : 'Save',
                    icon   : 'save',
                    danger : false,
                    onclick: function () { _saveMainSettings(); },
                },
            ],

            onBuild: function (modal) {
                _buildInventoryPane(modal);
                _buildGlobalPane(modal);
            },

            onOpen: function () {
                _loadMainSettings();
            },
        });

        return _mainModal;
    }

    /* ── Inventory pane ────────────────────────────────────────────────────── */
    function _buildInventoryPane(modal) {
        var pane = modal.pane('inventory');
        if (!pane) return;

        pane.innerHTML =
            '<div class="utm-sec">Inventory Visibility Options</div>' +
            '<div id="ds-inv-toggles">' +
                _buildToggleRow(
                    'ds-inv-multiunit',
                    'Item Multiunit Visibility',
                    'Show or hide multi-unit conversion rows in the item form',
                    'true'
                ) +
                _buildToggleRow(
                    'ds-inv-group',
                    'Item Group Visibility',
                    'Show or hide the item group classification column in lists',
                    'true'
                ) +
            '</div>' +
            _buildSetCaptionsBtn();
    }

    /* ── Global pane ───────────────────────────────────────────────────────── */
    function _buildGlobalPane(modal) {
        var pane = modal.pane('global');
        if (!pane) return;

        pane.innerHTML =
            '<div class="utm-sec">Global Settings</div>' +
            '<div style="color:var(--color-text-tertiary,#aaa);font-size:12px;padding:12px 0;">' +
                'Additional global default options will appear here.' +
            '</div>' +
            _buildSetCaptionsBtn();
    }

    /* ── Load settings from server ─────────────────────────────────────────── */
    function _loadMainSettings() {
        fetch('/common/ds/load/', { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
        .then(function (r) { if (!r.ok) throw new Error('HTTP ' + r.status); return r.json(); })
        .then(function (d) {
            if (!d.success) { console.warn('[DS] load:', d.error); return; }
            var s = d.settings || {};
            var mu = document.getElementById('ds-inv-multiunit');
            if (mu) mu.checked = (s.inv_item_multiunit_visibility !== 'false');
            var gv = document.getElementById('ds-inv-group');
            if (gv) gv.checked = (s.inv_item_group_visibility !== 'false');
        })
        .catch(function (err) { console.error('[DS] load error:', err); });
    }

    /* ── Save settings to server ───────────────────────────────────────────── */
    function _saveMainSettings() {
        var mu = document.getElementById('ds-inv-multiunit');
        var gv = document.getElementById('ds-inv-group');

        var payload = {
            inv_item_multiunit_visibility: (mu && mu.checked) ? 'true' : 'false',
            inv_item_group_visibility    : (gv && gv.checked) ? 'true' : 'false',
        };

        fetch('/common/ds/save/', {
            method : 'POST',
            headers: {
                'Content-Type'    : 'application/json',
                'X-CSRFToken'     : _csrf(),
                'X-Requested-With': 'XMLHttpRequest',
            },
            body: JSON.stringify(payload),
        })
        .then(function (r) { if (!r.ok) throw new Error('HTTP ' + r.status); return r.json(); })
        .then(function (d) {
            if (d.success) _toast('Settings saved', 's');
            else _toast(d.error || 'Could not save settings', 'e');
        })
        .catch(function (err) {
            console.error('[DS] save error:', err);
            _toast('Network error saving settings', 'e');
        });
    }


    /* ═══════════════════════════════════════════════════════════════════════
       CAPTIONS MODAL
       Sidebar layout (Prices, Groups, Entity, Location).
       Keys are UPPERCASE, matching ChartOfCode Code column so that
       get_rate_captions() in item_master.py picks them up automatically.
    ═══════════════════════════════════════════════════════════════════════ */
    var _capModal = null;
    var _captionOriginalValues = {};

    var CAP_CATEGORIES = [
        {
            id: 'cap_prices',
            tabLabel: '» Prices',
            title: 'Price Level Captions',
            fields: [
                { key: 'RATE0', label: 'Rate 0 (Purchase Price)' },
                { key: 'RATE1', label: 'Rate 1 (MRP)'           },
                { key: 'RATE2', label: 'Rate 2 (DRP)'           },
                { key: 'RATE3', label: 'Rate 3 (FDP)'           },
                { key: 'RATE4', label: 'Rate 4'                  },
                { key: 'RATE5', label: 'Rate 5'                  },
            ]
        },
        {
            id: 'cap_groups',
            tabLabel: '» Groups',
            title: 'Item Group Captions',
            fields: [
                { key: 'GROUP1',     label: 'Group 1'   },
                { key: 'GROUP2',     label: 'Group 2'   },
                { key: 'GROUP3',     label: 'Group 3'   },
                { key: 'GROUP4',     label: 'Group 4'   },
                { key: 'GROUP5',     label: 'Group 5'   },
                { key: 'WAREHOUSES', label: 'Warehouses' },
            ]
        },
        {
            id: 'cap_entity',
            tabLabel: '» Entity',
            title: 'Entity Captions',
            fields: [
                { key: 'COMPANY',  label: 'Company'  },
                { key: 'CATEGORY', label: 'Category' },
                { key: 'BRAND',    label: 'Brand'    },
            ]
        },
        {
            id: 'cap_location',
            tabLabel: '» Location',
            title: 'Location Captions',
            fields: [
                { key: 'CITY',     label: 'City'     },
                { key: 'AREA',     label: 'Area'     },
                { key: 'DISTRICT', label: 'District' },
                { key: 'STATE',    label: 'State'    },
            ]
        }
    ];

    function _buildCapModal() {
        if (_capModal) return _capModal;

        var tabs = CAP_CATEGORIES.map(function(cat) {
            return { id: cat.id, label: cat.tabLabel, icon: 'doc' };
        });

        _capModal = new UtilityModal({
            id      : 'defsett-cap-modal',
            title   : 'Set Captions',
        size: 'md',
            subtitle: 'Customise field labels shown across forms and reports',
            icon    : '<path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>' +
                      '<path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>',
            width   : '700px',
            height  : '60vh',

            tabs: tabs,

            toolbar: [
                {
                    label  : 'Save All',
                    icon   : 'save',
                    danger : false,
                    onclick: function () { _saveCaptions(); },
                },
            ],

            onBuild: function (modal) {
                CAP_CATEGORIES.forEach(function(cat) {
                    _buildCaptionsPane(modal, cat);
                });
            },
            onOpen : function () { _loadCaptions(); },
        });

        return _capModal;
    }

    /* ── Build captions pane content ──────────────────────────────────────── */
    function _buildCaptionsPane(modal, cat) {
        var pane = modal.pane(cat.id);
        if (!pane) return;

        var html = '<div class="utm-sec">' + cat.title + '</div>';
        html += '<div style="max-width: 480px; padding: 12px 0;">';

        cat.fields.forEach(function (fld) {
            html +=
                '<div class="pf-field" style="margin-bottom:14px;">' +
                    '<div class="pf-field-lbl" style="min-width:160px;font-size:12.5px;">' + fld.label + '</div>' +
                    '<div class="pf-field-ctl">' +
                      '<input type="text" id="ds-cap-' + fld.key + '" class="utm-inp"' +
                      ' placeholder="' + fld.label + '" style="height:32px;font-size:12.5px;">' +
                    '</div>' +
                '</div>';
        });

        html += '</div>';
        pane.innerHTML = html;

        // Bind blur event for auto-saving individual fields
        cat.fields.forEach(function (fld) {
            var inp = document.getElementById('ds-cap-' + fld.key);
            if (inp) {
                inp.addEventListener('blur', function() {
                    _saveSingleCaption(fld.key, inp);
                });
            }
        });
    }

    /* ── Auto-save single caption on blur ─────────────────────────────────── */
    function _saveSingleCaption(key, inp) {
        var newVal = inp.value.trim();
        if (newVal === _captionOriginalValues[key]) return; // no change
        
        var captions = {};
        captions[key] = newVal;
        
        fetch('/common/ds/captions/save/', {
            method : 'POST',
            headers: {
                'Content-Type'    : 'application/json',
                'X-CSRFToken'     : _csrf(),
                'X-Requested-With': 'XMLHttpRequest',
            },
            body: JSON.stringify({ captions: captions }),
        })
        .then(function (r) { if (!r.ok) throw new Error('HTTP ' + r.status); return r.json(); })
        .then(function (d) {
            if (d.success) {
                _captionOriginalValues[key] = newVal;
            } else {
                _toast(d.error || 'Could not save caption', 'e');
            }
        })
        .catch(function (err) {
            console.error('[DS/cap] single save error:', err);
            _toast('Network error saving caption', 'e');
        });
    }

    /* ── Load captions from server ────────────────────────────────────────── */
    function _loadCaptions() {
        fetch('/common/ds/captions/load/', { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
        .then(function (r) { if (!r.ok) throw new Error('HTTP ' + r.status); return r.json(); })
        .then(function (d) {
            if (!d.success) { console.warn('[DS/cap] load:', d.error); return; }
            var caps = d.captions || {};
            CAP_CATEGORIES.forEach(function (cat) {
                cat.fields.forEach(function (fld) {
                    var inp = document.getElementById('ds-cap-' + fld.key);
                    if (inp && caps[fld.key] !== undefined) {
                        inp.value = caps[fld.key];
                        _captionOriginalValues[fld.key] = caps[fld.key];
                    }
                });
            });
        })
        .catch(function (err) { console.error('[DS/cap] load error:', err); });
    }

    /* ── Save captions to server ─────────────────────────────────────────── */
    function _saveCaptions() {
        var captions = {};
        var hasChanges = false;
        CAP_CATEGORIES.forEach(function (cat) {
            cat.fields.forEach(function (fld) {
                var inp = document.getElementById('ds-cap-' + fld.key);
                if (inp) {
                    var val = inp.value.trim();
                    if (val !== _captionOriginalValues[fld.key]) {
                        captions[fld.key] = val;
                        hasChanges = true;
                    }
                }
            });
        });

        if (!hasChanges) {
            _toast('No changes to save', 'i');
            return;
        }

        fetch('/common/ds/captions/save/', {
            method : 'POST',
            headers: {
                'Content-Type'    : 'application/json',
                'X-CSRFToken'     : _csrf(),
                'X-Requested-With': 'XMLHttpRequest',
            },
            body: JSON.stringify({ captions: captions }),
        })
        .then(function (r) { if (!r.ok) throw new Error('HTTP ' + r.status); return r.json(); })
        .then(function (d) {
            if (d.success) {
                Object.keys(captions).forEach(function(k) {
                    _captionOriginalValues[k] = captions[k];
                });
                _toast('All Captions saved', 's');
            }
            else _toast(d.error || 'Could not save captions', 'e');
        })
        .catch(function (err) {
            console.error('[DS/cap] save error:', err);
            _toast('Network error saving captions', 'e');
        });
    }


    /* ═══════════════════════════════════════════════════════════════════════
       PUBLIC EXPORTS
    ═══════════════════════════════════════════════════════════════════════ */
    global.openDefaultSettings = function () {
        _buildMainModal().open();
    };

    global.openDefaultSettingsCaptions = function () {
        _buildCapModal().open();
    };

}(window));
