// ================================================================
//  common/static/common/js/form_design.js   v9.2
//
//  FIXES vs v9.1:
//  7. TABINDEX NOT APPLIED TO DOM ON PAGE LOAD — _applyServerDesign
//     now sets the actual HTML tabindex attribute on each input so
//     the browser Tab key follows the saved FormDesign order.
//     tabStop=false fields get tabIndex=-1 (skipped by Tab key).
//
//  8. DOM ORDER NOT REORDERED ON PAGE LOAD — _applyServerDesign
//     now calls _applyDomOrder() after sorting so the visual layout
//     matches the saved design tab sequence immediately on load.
//
//  FIXES vs v9.0:
//  5. ENABLE/DISABLE NOT PERSISTING ON PAGE LOAD — _applyServerDesign
//     now calls f._input.disabled = !f.enabled so fields saved as
//     disabled actually render disabled after a page refresh.
//     Also sets f._origEnabled = false so _isChanged() correctly
//     treats the already-saved disabled state as the baseline
//     (prevents Save All from redundantly re-saving it every time).
//
//  6. ENABLE/DISABLE TOGGLING UNRELIABLY — fdToggleEnabled now updates
//     f._origEnabled after a successful DB save. Without this, the
//     next Save All would see enabled !== _origEnabled and re-save
//     the field, sometimes with the wrong value if the user toggled
//     twice between saves.
// ================================================================

(function () {
    'use strict';

    /* ── State ─────────────────────────────────────────────── */
    var _formId         = '';
    var _formName       = '';
    var _fields         = [];
    var _filtered       = [];
    var _selectedIdx    = 0;
    var _dragOnMode     = false;
    var _fieldListeners = [];
    var _dragSrc        = null;
    var _initialized    = false;
    var _savedControls  = [];   // cache of last loaded DB controls

    /* ─────────────────────────────────────────────────────────
       ENCODE / DECODE  width/height ↔ integer
    ───────────────────────────────────────────────────────── */
    function _encodeWidth(v) {
        var s = String(v || '').trim().replace('px', '');
        if (!s) return null;
        if (s.slice(-1) === '%') {
            var n = parseFloat(s);
            return isNaN(n) ? null : Math.round(n * 100);
        }
        var n2 = parseInt(s, 10);
        return isNaN(n2) ? null : n2;
    }

    function _decodeWidth(n) {
        if (n === null || n === undefined || n === 0) return '';
        var num = parseInt(n, 10);
        if (isNaN(num) || num === 0) return '';
        if (num >= 100 && num % 100 === 0) return (num / 100) + '%';
        return num + 'px';
    }

    function _toCss(v) {
        var s = String(v || '').trim();
        if (!s) return '';
        if (s.slice(-1) === '%') return s;
        s = s.replace('px', '');
        var n = parseInt(s, 10);
        return isNaN(n) ? '' : n + 'px';
    }

    /* ─────────────────────────────────────────────────────────
       PUBLIC: initFormDesign  — page load (silent)
    ───────────────────────────────────────────────────────── */
    window.initFormDesign = function (formId, formName) {
        _formId   = formId   || '';
        _formName = formName || '';
        _injectStyleTag([]);   // empty style tag immediately — no flicker

        _loadDesign(function (saved) {
            _savedControls = saved || [];
            _fields        = _collectFields(_formId);
            _filtered      = _fields.slice();
            _applyServerDesign(_savedControls);
            _injectStyleTag(_fields);
            _injectResponsiveCSS();
            _initialized = true;
        });
    };

    /* ─────────────────────────────────────────────────────────
       PUBLIC: openFormDesign  — menu click (shows panel)
    ───────────────────────────────────────────────────────── */
    window.openFormDesign = function (formId, formName) {
        _formId   = formId   || '';
        _formName = formName || '';

        var existing = document.getElementById('fd-panel');
        if (existing && existing.classList.contains('fd-open')) {
            existing.style.zIndex = 9600;
            return;
        }

        // FAST OPEN — reuse cached fields if already initialized
        if (_initialized && _fields.length > 0 && _formId === formId) {
            _selectedIdx = 0;
            _dragOnMode  = false;
            _buildPanel();
            _openPanel();
            _attachClickListeners();
            return;
        }

        _fields   = _collectFields(_formId);
        _filtered = _fields.slice();
        _selectedIdx = 0;
        _dragOnMode  = false;

        _loadDesign(function (saved) {
            _savedControls = saved || [];
            _applyServerDesign(_savedControls);
            _injectStyleTag(_fields);
            _injectResponsiveCSS();
            _buildPanel();
            _openPanel();
            _attachClickListeners();
        });
    };

    window.closeFormDesign = function () {
        _detachClickListeners();
        _setDragMode(false);
        _closePanel();
    };

    /* ─────────────────────────────────────────────────────────
       INJECT STYLE TAG  — zero-jump CSS, no inline styles
    ───────────────────────────────────────────────────────── */
    function _injectStyleTag(fields) {
        var styleId  = 'fd-design-style-' + _formId;
        var existing = document.getElementById(styleId);
        if (!existing) {
            existing    = document.createElement('style');
            existing.id = styleId;
            document.head.appendChild(existing);
        }

        var css = '';
        (fields || []).forEach(function (f) {
            if (!f.name) return;

            if (!f.visible) {
                css += '#' + _formId + ' [name="' + f.name + '"],' +
                       '#' + _formId + ' .pf-hf-cell:has([name="' + f.name + '"]),' +
                       '#' + _formId + ' .pf-field:has([name="' + f.name + '"]) { display:none !important; }\n';
            }

            if (f.width && f.isHeader) {
                var wcss = _toCss(f.width);
                if (wcss) {
                    css += '#' + _formId + ' .pf-hf-cell:has([name="' + f.name + '"]) { ' +
                           'width:' + wcss + ' !important; flex: 0 0 ' + wcss + ' !important; }\n';
                }
            }

            if (f.width && !f.isHeader) {
                var wmcss = _toCss(f.width);
                if (wmcss) {
                    css += '#' + _formId + ' .pf-field:has([name="' + f.name + '"]) { max-width:' + wmcss + ' !important; }\n';
                    css += '#' + _formId + ' .pf-field:has([name="' + f.name + '"]) .pf-field-ctl { width:' + wmcss + ' !important; max-width:' + wmcss + ' !important; }\n';
                }
            }

            if (f.height) {
                var hcss = _toCss(f.height);
                if (hcss) {
                    css += '#' + _formId + ' [name="' + f.name + '"] { height:' + hcss + ' !important; min-height:' + hcss + ' !important; }\n';
                }
            }
        });

        existing.textContent = css;
    }

    function _injectResponsiveCSS() {
        var id = 'fd-responsive-css';
        if (document.getElementById(id)) return;
        var st  = document.createElement('style');
        st.id   = id;
        st.textContent =
            '.pf-pane { container-type: inline-size; }\n' +
            '@container (max-width: 700px) {\n' +
            '  .pf-cols-3 { grid-template-columns: 1fr 1fr !important; }\n' +
            '  .pf-cols-4 { grid-template-columns: 1fr 1fr !important; }\n' +
            '}\n' +
            '@container (max-width: 460px) {\n' +
            '  .pf-cols-2, .pf-cols-3, .pf-cols-4 { grid-template-columns: 1fr !important; }\n' +
            '}\n' +
            '@media (max-width: 860px) {\n' +
            '  .pf-cols-3 { grid-template-columns: 1fr 1fr; }\n' +
            '  .pf-cols-4 { grid-template-columns: 1fr 1fr; }\n' +
            '}\n' +
            '@media (max-width: 560px) {\n' +
            '  .pf-cols-2, .pf-cols-3, .pf-cols-4 { grid-template-columns: 1fr; }\n' +
            '}\n';
        document.head.appendChild(st);
    }

    /* ─────────────────────────────────────────────────────────
       COLLECT FIELDS
    ───────────────────────────────────────────────────────── */
    function _collectFields(formId) {
        var formEl = document.getElementById(formId);
        if (!formEl) return [];
        var seen = {}, result = [];

        formEl.querySelectorAll('.pf-hf-cell, .pf-field').forEach(function (wrap) {
            var inp = wrap.querySelector('input[name], select[name], textarea[name]');
            if (!inp || !inp.name || inp.type === 'hidden') return;
            if (seen[inp.name]) return;
            seen[inp.name] = true;

            var lbl      = wrap.querySelector('label, .pf-field-lbl, .pf-hf-lbl');
            var rawLabel = lbl ? lbl.textContent.replace(/\*/g, '').trim() : inp.name;
            var isHeader = wrap.classList.contains('pf-hf-cell');

            var defaultWidth  = '';
            var defaultHeight = '';
            if (isHeader && wrap.style.width) {
                defaultWidth = wrap.style.width;
            }
            if (inp.tagName === 'TEXTAREA') {
                var computed = window.getComputedStyle(inp);
                if (computed.height && computed.height !== 'auto' && computed.height !== '0px') {
                    defaultHeight = computed.height;
                }
            }

            result.push({
                name          : inp.name,
                label         : rawLabel,
                caption       : rawLabel,
                width         : '',
                height        : '',
                _defaultWidth : defaultWidth,
                _defaultHeight: defaultHeight,
                row           : 1,
                tabIndex      : result.length + 1,
                tabStop       : true,
                visible       : true,
                enabled       : true,
                isHeader      : isHeader,
                _wrap         : wrap,
                _input        : inp,
                _origCaption  : rawLabel,
                _origWidth    : defaultWidth,
                _origHeight   : '',
                _origRow      : 1,
                _origTabStop  : true,
                _origVisible  : true,
                _origEnabled  : true,
            });
        });
        return result;
    }

    /* ─────────────────────────────────────────────────────────
       APPLY SAVED DESIGN
       FIX 5: Actually apply disabled state to DOM on page load.
              Also sets _origEnabled so _isChanged() baseline is
              correct (won't re-save an already-saved disabled
              field on every subsequent Save All).
    ───────────────────────────────────────────────────────── */
    function _applyServerDesign(controls) {
        if (!controls || !controls.length) return;
        var map = {};
        controls.forEach(function (c) { map[c.controlName] = c; });

        _fields.forEach(function (f) {
            var c = map[f.name];
            if (!c) return;
            if (c.caption  != null) f.caption  = c.caption;
            if (c.width  != null && c.width)  f.width  = _decodeWidth(c.width);
            if (c.height != null && c.height) f.height = _decodeWidth(c.height);
            if (c.row    != null) f.row      = c.row || 1;
            if (c.tabIndex != null) f.tabIndex = c.tabIndex;
            f.tabStop = c.tabStop !== 0;
            f.visible = c.visible !== 0;
            f.enabled = c.enabled !== 0;

            /* FIX 5a: apply disabled state to DOM immediately (visual, no reload) */
            var disabled5 = !f.enabled;
            if (f._input) {
                f._input.disabled = disabled5;
                /* Keep profile_form.js Enter-key skip in sync with saved enabled state */
                f._input.setAttribute('data-enterskip', disabled5 ? '1' : '0');
            }
            if (f._wrap) {
                f._wrap.classList.toggle('fd-field-disabled', disabled5);
                /* Apply the skip colour hint class too if disabled */
                f._wrap.classList.toggle('pf-field-skipped', disabled5);
            }

            /* FIX 5b: update _orig baseline so _isChanged() doesn't
               treat an already-saved disabled field as "newly changed" */
            f._origEnabled = f.enabled;
            f._origVisible = f.visible;
            f._origCaption = f.caption;
            if (f.width)  f._origWidth  = f.width;
            if (f.height) f._origHeight = f.height;
            f._origRow     = f.row;
            f._origTabStop = f.tabStop;
        });

        _fields.sort(function (a, b) { return (a.tabIndex || 0) - (b.tabIndex || 0); });
        _filtered = _fields.slice();

        /* v9.2 — Apply tabIndex and tabStop to actual DOM inputs so the
           browser Tab key follows the saved FormDesign order.
           tabStop=false → tabIndex=-1 (field is skipped by Tab key).
           NOTE: We do NOT call _applyDomOrder() here because reordering
           DOM elements across multi-column tab layouts (pf-cols-2 etc.)
           breaks the visual grid structure. The tabIndex attribute is
           sufficient for both Tab-key and Enter-key navigation order. */
        _fields.forEach(function (f, i) {
            if (!f._input) return;
            if (f.tabStop === false) {
                f._input.tabIndex = -1;
            } else {
                f._input.tabIndex = f.tabIndex || (i + 1);
            }
        });
    }

    /* ─────────────────────────────────────────────────────────
       CLICK-TO-SELECT
    ───────────────────────────────────────────────────────── */
    function _attachClickListeners() {
        _detachClickListeners();
        _fields.forEach(function (f) {
            var handler = function (e) {
                if (!document.getElementById('fd-panel')) return;
                if (_dragOnMode) return;
                e.stopPropagation();
                _selectByField(f);
            };
            f._wrap.addEventListener('click', handler, true);
            _fieldListeners.push({ el: f._wrap, fn: handler });
        });
    }
    function _detachClickListeners() {
        _fieldListeners.forEach(function (l) { l.el.removeEventListener('click', l.fn, true); });
        _fieldListeners = [];
    }
    function _selectByField(f) {
        fd_filter('');
        for (var i = 0; i < _filtered.length; i++) {
            if (_filtered[i] === f) { _selectField(i); return; }
        }
    }

    /* ─────────────────────────────────────────────────────────
       DRAG-ON MODE
    ───────────────────────────────────────────────────────── */
    function _setDragMode(on) {
        _dragOnMode = on;
        _fields.forEach(function (f) {
            if (f._wrap) f._wrap.classList.toggle('fd-drag-hint', on);
        });
        var btn = document.getElementById('fd-dragon-btn');
        if (btn) { btn.classList.toggle('fd-btn-active', on); btn.textContent = on ? '🔴 Drag On' : '↔ Drag On'; }
        _rebuildDropList();
    }
    window.fd_toggleDragOn = function () { _setDragMode(!_dragOnMode); };

    function _wireDragRows() {
        var list = document.getElementById('fd-dd-list');
        if (!list) return;
        list.querySelectorAll('.fd-dd-item').forEach(function (row) {
            row.addEventListener('dragstart', function (e) {
                _dragSrc = row; e.dataTransfer.effectAllowed = 'move';
                e.dataTransfer.setData('text/plain', row.getAttribute('data-idx'));
                setTimeout(function () { row.classList.add('fd-dragging'); }, 0);
            });
            row.addEventListener('dragend', function () {
                row.classList.remove('fd-dragging');
                list.querySelectorAll('.fd-dd-item').forEach(function (r) { r.classList.remove('fd-drag-over'); });
                _dragSrc = null;
            });
            row.addEventListener('dragover', function (e) {
                e.preventDefault();
                if (row !== _dragSrc) row.classList.add('fd-drag-over');
            });
            row.addEventListener('dragleave', function () { row.classList.remove('fd-drag-over'); });
            row.addEventListener('drop', function (e) {
                e.preventDefault(); row.classList.remove('fd-drag-over');
                if (!_dragSrc || _dragSrc === row) return;
                var si = parseInt(_dragSrc.getAttribute('data-idx'), 10);
                var di = parseInt(row.getAttribute('data-idx'), 10);
                if (isNaN(si) || isNaN(di)) return;
                var moved = _filtered.splice(si, 1)[0];
                _filtered.splice(di, 0, moved);
                var inF = {};
                _filtered.forEach(function (f) { inF[f.name] = true; });
                _fields = _filtered.slice().concat(_fields.filter(function (f) { return !inF[f.name]; }));
                _fields.forEach(function (f, i) { f.tabIndex = i + 1; });
                _applyDomOrder();
                _rebuildDropList();
                var ni = _filtered.indexOf(moved);
                if (ni !== -1) _selectField(ni);
                _toast('Reordered — Save All to persist', 'info');
            });
        });
    }

    function _rebuildDropList() {
        var list = document.getElementById('fd-dd-list');
        if (!list) return;
        list.innerHTML = _dropItemsHTML(_filtered);
        if (_dragOnMode) _wireDragRows();
    }

    /* ─────────────────────────────────────────────────────────
       SERVER  LOAD / SAVE / RESET
    ───────────────────────────────────────────────────────── */
    function _loadDesign(cb) {
        if (!_formName) { cb([]); return; }
        var url = (window.FD_URLS && window.FD_URLS.load) || '/common/form-design/load/';
        fetch(url + '?form=' + encodeURIComponent(_formName))
            .then(function (r) { return r.json(); })
            .then(function (d) { cb(d.success ? (d.controls || []) : []); })
            .catch(function () { cb([]); });
    }

    function _buildPayload(fields) {
        var changed = fields.filter(_isChanged);
        return changed.map(function (f) {
            return {
                controlName : f.name,
                typeCode    : 0,
                caption     : f.caption || '',
                width       : _encodeWidth(f.width),
                height      : _encodeWidth(f.height),
                row         : parseInt(f.row) || 1,
                tabIndex    : parseInt(f.tabIndex) || (fields.indexOf(f) + 1),
                tabStop     : f.tabStop ? 1 : 0,
                visible     : f.visible ? 1 : 0,
                enabled     : f.enabled ? 1 : 0,
                design      : 1,
            };
        });
    }

    function _isChanged(f) {
        if (f.caption  !== f._origCaption)               return true;
        if ((f.width   || '') !== (f._origWidth  || ''))  return true;
        if ((f.height  || '') !== (f._origHeight || ''))  return true;
        if (f.row      !== (f._origRow      || 1))        return true;
        if (f.tabStop  !== (f._origTabStop  !== false))   return true;
        if (f.visible  !== (f._origVisible  !== false))   return true;
        if (f.enabled  !== (f._origEnabled  !== false))   return true;
        return false;
    }

    function _postSave(payload, cb) {
        var url = (window.FD_URLS && window.FD_URLS.save) || '/common/form-design/save/';
        fetch(url, {
            method  : 'POST',
            headers : { 'Content-Type': 'application/json', 'X-CSRFToken': _csrf() },
            body    : JSON.stringify({ form: _formName, controls: payload }),
        })
        .then(function (r) { return r.json(); })
        .then(function (d) { if (d.success) { if (cb) cb(); } else _alert(d.error || 'Save failed', 'error'); })
        .catch(function () { _alert('Network error', 'error'); });
    }

    function _saveAll() {
        _readGridInto(_filtered[_selectedIdx]);
        var payload = _buildPayload(_fields);
        if (payload.length === 0) {
            _toast('No changes to save', 'info');
            return;
        }
        _postSave(payload, function () {
            /* Update _orig baseline so these fields aren't re-saved next time */
            _fields.forEach(function (f) {
                f._origCaption  = f.caption;
                f._origWidth    = f.width;
                f._origHeight   = f.height;
                f._origRow      = f.row;
                f._origTabStop  = f.tabStop;
                f._origVisible  = f.visible;
                f._origEnabled  = f.enabled;
            });
            _injectStyleTag(_fields);
            _savedControls = payload;
            _toast('Saved ' + payload.length + ' changed field' + (payload.length !== 1 ? 's' : ''), 'success');
        });
    }

    function _resetDesign() {
        _confirm(
            'Reset "' + _formName + '" to defaults?\nAll saved widths, captions and visibility will be cleared.',
            function (ok) {
                if (!ok) return;
                var url = (window.FD_URLS && window.FD_URLS.reset) || '/common/form-design/reset/';
                fetch(url, {
                    method  : 'POST',
                    headers : { 'Content-Type': 'application/json', 'X-CSRFToken': _csrf() },
                    body    : JSON.stringify({ form: _formName }),
                })
                .then(function (r) { return r.json(); })
                .then(function (d) {
                    if (!d.success) { _alert('Reset failed', 'error'); return; }

                    var st = document.getElementById('fd-design-style-' + _formId);
                    if (st) st.textContent = '';

                    _fields.forEach(function (f) {
                        f.width    = '';
                        f.height   = '';
                        f.caption  = f.label;
                        f.visible  = true;
                        f.enabled  = true;
                        f.row      = 1;
                        f.tabIndex = _fields.indexOf(f) + 1;
                        f.tabStop  = true;
                        /* Re-enable DOM input */
                        if (f._input) f._input.disabled = false;
                        /* Restore label text */
                        var lbl = f._wrap && f._wrap.querySelector('label, .pf-field-lbl, .pf-hf-lbl');
                        if (lbl) {
                            var req = lbl.querySelector('.req, .pf-hf-req');
                            lbl.textContent = f.label;
                            if (req) lbl.appendChild(req);
                        }
                        /* Reset _orig to true defaults */
                        f._origCaption = f.label;
                        f._origWidth   = f._defaultWidth || '';
                        f._origHeight  = '';
                        f._origRow     = 1;
                        f._origTabStop = true;
                        f._origVisible = true;
                        f._origEnabled = true;
                    });

                    _savedControls = [];
                    _initialized   = false;
                    _selectField(_selectedIdx);
                    closeFormDesign();
                    _toast('Form design reset to defaults', 'success');
                })
                .catch(function () { _alert('Network error during reset', 'error'); });
            },
            'danger', 'Reset Design', 'Yes, Reset', 'Cancel'
        );
    }

    /* ─────────────────────────────────────────────────────────
       APPLY DOM ORDER (drag reorder)
    ───────────────────────────────────────────────────────── */
    function _applyDomOrder() {
        var pList = [], pMap = [];
        _fields.forEach(function (f) {
            if (!f._wrap || !f._wrap.parentNode) return;
            var p = f._wrap.parentNode, entry = null;
            for (var i = 0; i < pList.length; i++) { if (pList[i] === p) { entry = pMap[i]; break; } }
            if (!entry) { entry = { parent: p, nodes: [] }; pList.push(p); pMap.push(entry); }
            entry.nodes.push(f._wrap);
        });
        pMap.forEach(function (e) { e.nodes.forEach(function (n) { e.parent.appendChild(n); }); });
    }

    function _readGridInto(f) {
        if (!f) return;
        var g = function (id) { var el = document.getElementById(id); return el ? el.value : ''; };
        f.caption  = g('fd-prop-caption');
        f.width    = g('fd-prop-width').trim();
        f.height   = g('fd-prop-height').trim();
        f.row      = parseInt(g('fd-prop-row')) || 1;
        f.tabIndex = parseInt(g('fd-prop-tabindex')) || (_selectedIdx + 1);
        f.tabStop  = g('fd-prop-tabstop') === 'Yes';
        f.visible  = g('fd-prop-visible') === 'Yes';
        f.enabled  = g('fd-prop-enabled') === 'Yes';
    }

    /* ─────────────────────────────────────────────────────────
       LIVE APPLY
    ───────────────────────────────────────────────────────── */
    function _liveApply() {
        var f = _filtered[_selectedIdx];
        if (!f) return;
        var g = function (id) { var el = document.getElementById(id); return el ? el.value : ''; };
        f.visible = g('fd-prop-visible') === 'Yes';
        f.enabled = g('fd-prop-enabled') === 'Yes';
        f.caption = g('fd-prop-caption');
        f.width   = g('fd-prop-width').trim();
        f.height  = g('fd-prop-height').trim();
        f.row     = parseInt(g('fd-prop-row')) || 1;

        var lbl = f._wrap && f._wrap.querySelector('label, .pf-field-lbl, .pf-hf-lbl');
        if (lbl) {
            var req = lbl.querySelector('.req, .pf-hf-req');
            lbl.textContent = f.caption;
            if (req) lbl.appendChild(req);
        }
        if (f._input) f._input.disabled = !f.enabled;
        if (f._wrap)  f._wrap.classList.toggle('fd-field-disabled', !f.enabled);

        _injectStyleTag(_fields);
        var vr = document.getElementById('row-fd-prop-visible');
        if (vr) vr.classList.toggle('fd-prop-hidden-row', !f.visible);
    }

    /* ─────────────────────────────────────────────────────────
       BUILD PANEL
    ───────────────────────────────────────────────────────── */
    function _buildPanel() {
        var old = document.getElementById('fd-panel');
        if (old) old.remove();
        var panel = document.createElement('div');
        panel.id  = 'fd-panel';
        panel.innerHTML = _panelHTML();
        document.body.appendChild(panel);
        _makeDraggable(panel, panel.querySelector('.fd-title-bar'));
        document.addEventListener('click', _outsideClick);
    }

    function _outsideClick(e) {
        var pop = document.getElementById('fd-dd-popup');
        var tri = document.getElementById('fd-dd-trigger');
        if (pop && tri && !pop.contains(e.target) && !tri.contains(e.target)) pop.style.display = 'none';
    }

    function _panelHTML() {
        return (
            '<div class="fd-title-bar">' +
                '<span class="fd-title-icon">⚙️</span>' +
                '<span class="fd-title-text">Form Design — ' + _esc(_formName) + '</span>' +
                '<button class="fd-title-close" onclick="closeFormDesign()" title="Close">✕</button>' +
            '</div>' +
            '<div class="fd-body">' +
                '<div class="fd-dd-wrap">' +
                    '<div class="fd-dd-trigger" id="fd-dd-trigger" onclick="fd_toggleDrop()">' +
                        '<span class="fd-dd-label" id="fd-dd-label">' + (_fields[0] ? _esc(_fields[0].name) : 'Select…') + '</span>' +
                        '<span class="fd-dd-arrow">▾</span>' +
                    '</div>' +
                    '<div class="fd-dd-popup" id="fd-dd-popup" style="display:none">' +
                        '<input id="fd-dd-search" type="text" placeholder="Search…" oninput="fd_filter(this.value)" onclick="event.stopPropagation()">' +
                        '<div class="fd-dd-list" id="fd-dd-list">' + _dropItemsHTML(_fields) + '</div>' +
                    '</div>' +
                '</div>' +
                '<div class="fd-grid-wrap">' +
                    '<table class="fd-prop-table"><tbody>' +
                        _pRow('Width',    'fd-prop-width',    'text',   '') +
                        _pRow('Height',   'fd-prop-height',   'text',   '') +
                        _pRow('Row',      'fd-prop-row',      'number', '1') +
                        _pRow('TabIndex', 'fd-prop-tabindex', 'number', '') +
                        _pSel('TabStop',  'fd-prop-tabstop') +
                        _pSel('Visible',  'fd-prop-visible')  +
                        _pRow('Caption',  'fd-prop-caption',  'text',   '') +
                        _pSel('Enabled',  'fd-prop-enabled')  +
                    '</tbody></table>' +
                '</div>' +
                '<div class="fd-btns">' +
                    '<button id="fd-dragon-btn" class="fd-btn fd-btn-full" onclick="fd_toggleDragOn()">↔ Drag On</button>' +
                    '<button class="fd-btn" onclick="fd_apply()">✓ Apply</button>' +
                    '<button class="fd-btn fd-btn-primary" onclick="fd_saveAll()">💾 Save All</button>' +
                    '<button class="fd-btn fd-btn-danger" onclick="fd_reset()">↩ Reset</button>' +
                '</div>' +
            '</div>'
        );
    }

    function _dropItemsHTML(arr) {
        return arr.map(function (f, i) {
            var drag   = _dragOnMode ? ' draggable="true"' : '';
            var handle = _dragOnMode
                ? '<span class="fd-drag-handle">⠿</span>'
                : '<span class="fd-row-badge">R' + (f.row || 1) + '</span>';
            return '<div class="fd-dd-item' + (_dragOnMode ? ' fd-dd-draggable' : '') + '"' +
                   drag + ' data-idx="' + i + '" onclick="fd_pick(' + i + ')">' +
                   handle +
                   '<span class="fd-dd-name">' + _esc(f.name) + '</span>' +
                   '<span class="fd-dd-sub">' + _esc(f.label) + '</span>' +
                   '</div>';
        }).join('');
    }

    function _pRow(label, id, type, ph) {
        return '<tr class="fd-prop-row" id="row-' + id + '">' +
                   '<td class="fd-prop-name">' + label + '</td>' +
                   '<td class="fd-prop-val"><input id="' + id + '" type="' + type + '" value="" ' +
                   'placeholder="' + _esc(ph || '') + '" oninput="fd_liveApply()"></td>' +
               '</tr>';
    }
    function _pSel(label, id) {
        return '<tr class="fd-prop-row" id="row-' + id + '">' +
                   '<td class="fd-prop-name">' + label + '</td>' +
                   '<td class="fd-prop-val"><select id="' + id + '" onchange="fd_liveApply()">' +
                   '<option>Yes</option><option>No</option></select></td>' +
               '</tr>';
    }

    /* ─────────────────────────────────────────────────────────
       SELECT FIELD
    ───────────────────────────────────────────────────────── */
    function _selectField(idx) {
        if (idx < 0) idx = 0;
        if (idx >= _filtered.length) idx = _filtered.length - 1;
        _selectedIdx = idx;
        var f = _filtered[idx];
        if (!f) return;

        var ddl = document.getElementById('fd-dd-label');
        if (ddl) ddl.textContent = f.name;

        document.querySelectorAll('.fd-dd-item').forEach(function (el) {
            el.classList.toggle('fd-dd-item-active', parseInt(el.getAttribute('data-idx'), 10) === idx);
        });
        var item = document.querySelector('.fd-dd-item[data-idx="' + idx + '"]');
        if (item) item.scrollIntoView({ block: 'nearest' });

        _fields.forEach(function (ff) { if (ff._wrap) ff._wrap.classList.remove('fd-wrap-selected'); });
        if (f._wrap) {
            f._wrap.classList.add('fd-wrap-selected');
            f._wrap.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
        }

        var s  = function (id, v) { var el = document.getElementById(id); if (el) el.value = v; };
        var sp = function (id, v) { var el = document.getElementById(id); if (el) el.placeholder = v; };
        var bs = function (id, v) { s(id, v ? 'Yes' : 'No'); };

        s('fd-prop-width',    f.width    || '');
        s('fd-prop-height',   f.height   || '');
        s('fd-prop-row',      f.row      || 1);
        s('fd-prop-tabindex', f.tabIndex || (idx + 1));
        bs('fd-prop-tabstop', f.tabStop  !== false);
        bs('fd-prop-visible', f.visible  !== false);
        s('fd-prop-caption',  f.caption  || f.label || '');
        bs('fd-prop-enabled', f.enabled  !== false);

        sp('fd-prop-width',  f._defaultWidth  ? 'default: ' + f._defaultWidth  : 'e.g. 80% or 200');
        sp('fd-prop-height', f._defaultHeight ? 'default: ' + f._defaultHeight : 'e.g. 120');

        var vr = document.getElementById('row-fd-prop-visible');
        if (vr) vr.classList.toggle('fd-prop-hidden-row', !f.visible);
    }

    /* ─────────────────────────────────────────────────────────
       DROPDOWN
    ───────────────────────────────────────────────────────── */
    window.fd_toggleDrop = function () {
        var pop = document.getElementById('fd-dd-popup');
        if (!pop) return;
        if (pop.style.display !== 'none') { pop.style.display = 'none'; }
        else {
            pop.style.display = 'block'; fd_filter('');
            var s = document.getElementById('fd-dd-search');
            if (s) { s.value = ''; s.focus(); }
        }
    };
    window.fd_filter = function (q) {
        var query = (q || '').toLowerCase().trim();
        _filtered = query
            ? _fields.filter(function (f) { return f.name.toLowerCase().indexOf(query) !== -1 || f.label.toLowerCase().indexOf(query) !== -1; })
            : _fields.slice();
        _rebuildDropList();
    };
    window.fd_pick = function (idx) {
        _selectField(idx);
        var pop = document.getElementById('fd-dd-popup');
        if (pop) pop.style.display = 'none';
    };

    /* ─────────────────────────────────────────────────────────
       BUTTON CALLBACKS
    ───────────────────────────────────────────────────────── */
    window.fd_liveApply = _liveApply;
    window.fd_apply     = function () { _readGridInto(_filtered[_selectedIdx]); _injectStyleTag(_fields); _toast('Applied', 'info'); };
    window.fd_saveAll   = _saveAll;
    window.fd_reset     = _resetDesign;

    /* ─────────────────────────────────────────────────────────
       Ctrl+E / label-dblclick bridge

       FIXES:
       • Toast message was inverted — captured BEFORE the toggle
         so the string always reflects the NEW state correctly.
       • Live visual — _applyEnabledVisual() immediately updates
         the input, wrapper class and any pf_select overlay so
         the user sees the change without a page reload.
       • _origEnabled synced after DB save so Save All doesn't
         re-save this field unnecessarily.
    ───────────────────────────────────────────────────────── */

    /* Applies the enabled/disabled state visually to a field RIGHT NOW,
       no page reload required. Handles plain inputs, selects, textareas
       and pf_select custom-dropdown overlays.                           */
    function _applyEnabledVisual(f) {
        var disabled = !f.enabled;

        /* 1. Native input element */
        if (f._input) f._input.disabled = disabled;

        /* 2. Wrapper CSS class — lets you style disabled fields via CSS */
        if (f._wrap) f._wrap.classList.toggle('fd-field-disabled', disabled);

        /* 3. pf_select custom overlay — the clickable trigger div that
              sits on top of the real <select>. Without this the overlay
              still accepts clicks even when the underlying select is
              disabled, making the change invisible until reload.        */
        if (f._input && f._input.tagName === 'SELECT') {
            /* pf_select renders a sibling or child .pf-sel-trigger */
            var wrap    = f._wrap || (f._input && f._input.closest('.pf-field, .pf-hf-cell'));
            var trigger = wrap && wrap.querySelector('.pf-sel-trigger, .pf-select-trigger, [data-pf-trigger]');
            if (trigger) {
                trigger.style.pointerEvents = disabled ? 'none' : '';
                trigger.style.opacity       = disabled ? '0.45' : '';
            }
        }

        /* 4. Sync design-panel dropdown if this field is currently selected */
        var sel = document.getElementById('fd-prop-enabled');
        if (sel && _filtered[_selectedIdx] === f) sel.value = f.enabled ? 'Yes' : 'No';
    }

    window.fdToggleEnabled = function (fieldName) {
        var f = null;
        for (var i = 0; i < _fields.length; i++) {
            if (_fields[i].name === fieldName) { f = _fields[i]; break; }
        }
        if (!f) return;

        /* Toggle state FIRST, capture the label AFTER so message is correct */
        f.enabled = !f.enabled;
        var actionLabel = f.enabled ? 'Enabled' : 'Disabled';   /* new state */

        /* Apply visual change immediately — no reload needed */
        _applyEnabledVisual(f);

        if (!_formName) {
            _toast(actionLabel + ': ' + f.name, 'info');
            return;
        }

        var payload = [{
            controlName : f.name,
            typeCode    : 0,
            caption     : f.caption || '',
            width       : _encodeWidth(f.width),
            height      : _encodeWidth(f.height),
            row         : parseInt(f.row) || 1,
            tabIndex    : f.tabIndex || 1,
            tabStop     : f.tabStop ? 1 : 0,
            visible     : f.visible ? 1 : 0,
            enabled     : f.enabled ? 1 : 0,
            design      : 1,
        }];

        _postSave(payload, function () {
            /* Sync _orig baseline so _isChanged() is correct on next Save All */
            f._origEnabled = f.enabled;
            _toast(actionLabel + ': ' + f.name, 'info');
        });
    };

    /* ─────────────────────────────────────────────────────────
       OPEN / CLOSE
    ───────────────────────────────────────────────────────── */
    function _openPanel() {
        var panel = document.getElementById('fd-panel');
        if (!panel) return;
        panel.style.display = 'flex';
        requestAnimationFrame(function () { panel.classList.add('fd-open'); });
        document.addEventListener('keydown', _escClose);
        if (_fields.length) _selectField(0);
    }

    function _closePanel() {
        document.removeEventListener('keydown', _escClose);
        document.removeEventListener('click',   _outsideClick);
        var panel = document.getElementById('fd-panel');
        if (!panel) return;
        panel.classList.remove('fd-open');
        _fields.forEach(function (f) {
            if (f._wrap) { f._wrap.classList.remove('fd-wrap-selected'); f._wrap.classList.remove('fd-drag-hint'); }
        });
        panel.addEventListener('transitionend', function h() { panel.removeEventListener('transitionend', h); panel.remove(); });
    }

    function _escClose(e) { if (e.key === 'Escape') closeFormDesign(); }

    /* ─────────────────────────────────────────────────────────
       DRAGGABLE TITLE BAR
    ───────────────────────────────────────────────────────── */
    function _makeDraggable(panel, handle) {
        if (!handle) return;
        var sx, sy, sl, st;
        handle.addEventListener('mousedown', function (e) {
            if (e.target.tagName === 'BUTTON') return;
            e.preventDefault();
            var rect = panel.getBoundingClientRect();
            sx = e.clientX; sy = e.clientY; sl = rect.left; st = rect.top;
            panel.style.right = 'auto'; panel.style.left = sl + 'px'; panel.style.top = st + 'px'; panel.style.zIndex = 9600;
            function move(ev) {
                panel.style.left = Math.max(0, Math.min(window.innerWidth  - 80, sl + ev.clientX - sx)) + 'px';
                panel.style.top  = Math.max(0, Math.min(window.innerHeight - 40, st + ev.clientY - sy)) + 'px';
            }
            function up() { document.removeEventListener('mousemove', move); document.removeEventListener('mouseup', up); }
            document.addEventListener('mousemove', move);
            document.addEventListener('mouseup',   up);
        });
    }

    /* ─────────────────────────────────────────────────────────
       UTILS
    ───────────────────────────────────────────────────────── */
    function _csrf() { var m = document.cookie.match(/csrftoken=([^;]+)/); return m ? decodeURIComponent(m[1]) : ''; }
    function _esc(s) { return String(s || '').replace(/&/g,'&amp;').replace(/"/g,'&quot;').replace(/</g,'&lt;'); }
    function _toast(m, t)       { if (typeof window.showToast   === 'function') window.showToast(m, t); }
    function _alert(m, t)       { if (typeof window.showAlert   === 'function') window.showAlert(m, t); else alert(m); }
    function _confirm(m,cb,t,ti,ok,ca) {
        if (typeof window.showConfirm === 'function') window.showConfirm(m,cb,t,ti,ok,ca);
        else cb(window.confirm(m));
    }

}());