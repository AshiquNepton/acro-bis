// common/static/common/js/rpt_filter.js

(function (global) {
    'use strict';

    /* ── CSRF ── */
    function _csrf() {
        var m = document.cookie.match(/csrftoken=([^;]+)/);
        return m ? decodeURIComponent(m[1]) : '';
    }

    function _toast(msg, type) {
        if (typeof window.pfToast === 'function') window.pfToast(msg, type);
        else console.log('[rpt_filter]', type, msg);
    }

    function _esc(s) {
        return String(s || '')
            .replace(/&/g, '&amp;').replace(/</g, '&lt;')
            .replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#39;');
    }

    /* ══════════════════════════════════════════════════════════════
   pfSel HELPER
══════════════════════════════════════════════════════════════ */
    function _pfSelUpgrade(el) {
        if (!el || el.tagName !== 'SELECT') return;
        if (typeof window.pfSelUpgradeOne === 'function') {
            window.pfSelUpgradeOne(el);
        }
    }

    function _pfSelUpgradeAll(container) {
        if (!container) return;
        container.querySelectorAll('select').forEach(function (sel) { _pfSelUpgrade(sel); });
    }

    /* ── Terminal logger ── */
    function _logToTerminal(reportId, header, filterRows) {
        var lines = ['', '┌─ Filter Applied ─────────────────────────────────'];
        lines.push('│  Report  : ' + reportId);
        if (header.deptProject) lines.push('│  Dept    : ' + (header.deptProjectLabel || header.deptProject));
        if (header.status) lines.push('│  Status  : ' + header.status);
        if (header.type) lines.push('│  Type    : ' + header.type);
        if (header.dateFrom) lines.push('│  From    : ' + header.dateFrom);
        if (header.dateTo) lines.push('│  To      : ' + header.dateTo);
        if (filterRows && filterRows.length) {
            lines.push('│  Rows    :');
            filterRows.forEach(function (f, i) {
                if (f.field && f.value !== '') {
                    var op = i === 0 ? '   ' : (f.operator === 1 ? 'OR ' : 'AND');
                    var showVal = f.displayValue || f.value;
                    lines.push('│    ' + op + ' ' + f.field + ' = \'' + showVal + '\' (id=' + f.value + ')');
                }
            });
        }
        lines.push('└──────────────────────────────────────────────────', '');
        var msg = lines.join('\n');
        console.log(msg);
        try {
            fetch('/common/filter/log/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': _csrf() },
                body: JSON.stringify({ message: msg }),
            }).catch(function () { });
        } catch (e) { }
    }

    /* ═════════════════════════════════════════════════════════════════
       SHARED STATE
    ═════════════════════════════════════════════════════════════════ */
    var _filterState = {
        reportId: '',
        filterRows: [],
        fieldDefs: [],
        loaded: false,
        headerVals: {},
    };

    var _editState = {
        reportId: '',
        rows: [],
        selected: null,
        isNew: false,
        reports: [],
    };

    var _optState = {
        reportId: '',
        cols: [],
        selected: null,
    };

    var _srState = {
        reportId: '',
        mrName: '',
        selected: null,
        styles: [],
    };

    global._rptFieldsUrl = global._rptFieldsUrl || {};

    /* ═════════════════════════════════════════════════════════════════
       COLOR PICKER FACTORY
       ─────────────────────────────────────────────────────────────────
       Wraps PfColorPicker (pf_color_picker.js) when available.
       Falls back to a minimal inline implementation so the rest of the
       code always works even if pf_color_picker.js hasn't loaded yet.
       The public API is identical in both cases:
         { el, getValue(), setValue(hex), clear() }
    ═════════════════════════════════════════════════════════════════ */
    function _createColorPicker(initialColor) {
        if (typeof global.PfColorPicker !== 'undefined' &&
            typeof global.PfColorPicker.create === 'function') {
            return global.PfColorPicker.create({ value: initialColor || '' });
        }

        var _hex = (initialColor || '').trim();
        var _active = !!_hex;

        var wrap = document.createElement('div');
        wrap.className = 'rpt-cp-wrap';
        wrap.style.width = '100%';

        var input = document.createElement('input');
        input.type = 'color';
        input.className = 'rpt-cp-input';
        input.value = _hex || '#ffffff';

        var swatch = document.createElement('span');
        swatch.className = 'rpt-cp-swatch';

        var lbl = document.createElement('span');
        lbl.className = 'rpt-cp-label';

        var clearBtn = document.createElement('button');
        clearBtn.type = 'button';
        clearBtn.className = 'rpt-cp-clear';
        clearBtn.textContent = '×';
        clearBtn.title = 'Remove color';

        wrap.appendChild(input);
        wrap.appendChild(swatch);
        wrap.appendChild(lbl);
        wrap.appendChild(clearBtn);

        function _render() {
            swatch.style.background = (_active && _hex) ? _hex : 'transparent';
            lbl.textContent = (_active && _hex) ? _hex : 'None';
            lbl.className = 'rpt-cp-label' + ((_active && _hex) ? ' rpt-cp-label--active' : '');
        }

        input.addEventListener('input', function () { _hex = input.value; _active = true; _render(); });
        input.addEventListener('change', function () { _hex = input.value; _active = true; _render(); });
        clearBtn.addEventListener('click', function () { _active = false; _hex = ''; _render(); });

        _render();

        return {
            el: wrap,
            getValue: function () { return _active ? _hex : ''; },
            setValue: function (hex) {
                _hex = (hex || '').trim(); _active = !!_hex;
                if (_hex) input.value = _hex; _render();
            },
            clear: function () { _active = false; _hex = ''; _render(); },
        };
    }



    // ADD this new function:
    window.rptOptOpenColorPicker = function (swatchEl, idx, colorType) {
        colorType = colorType || 'bg';
        // close any existing popover
        var existing = document.getElementById('ropt-cp-popover');
        if (existing) {
            existing.remove();
            if (existing.dataset.idx === String(idx) && existing.dataset.colorType === colorType) return;
        }

        var col = _optState.cols[idx];
        if (!col) return;

        var popover = document.createElement('div');
        popover.id = 'ropt-cp-popover';
        popover.dataset.idx = String(idx);
        popover.style.cssText =
            'position:fixed;z-index:9999;background:var(--color-bg-card,#fff);' +
            'border:1px solid var(--color-border-medium,#ccc);border-radius:6px;' +
            'box-shadow:0 6px 20px rgba(0,0,0,.15);padding:10px;display:flex;' +
            'flex-direction:column;gap:8px;min-width:200px';

        // build picker with current color (or '' if none was set)
        popover.dataset.colorType = colorType;
        // build picker with current color (or '' if none was set)
        var currentColor = colorType === 'fg' ? (col.textColor || '') : (col.color || '');
        var picker = (typeof PfColorPicker !== 'undefined' && PfColorPicker.create)
            ? PfColorPicker.create({ value: currentColor })
            : _createColorPicker(currentColor);

        popover.appendChild(picker.el);

        // OK button to confirm
        var okBtn = document.createElement('button');
        okBtn.textContent = 'OK';
        okBtn.style.cssText =
            'align-self:flex-end;padding:3px 14px;font-size:12px;cursor:pointer;' +
            'border:1px solid var(--color-border-medium,#ccc);border-radius:3px;' +
            'background:var(--color-primary,#8b0000);color:#fff';
        okBtn.onclick = function () {
            var hex = picker.getValue();
            if (colorType === 'fg') {
                _optState.cols[idx].textColor = hex;
            } else {
                _optState.cols[idx].color = hex;
            }
            swatchEl.style.background = hex || '#e0e0e0';
            popover.remove();
            _optSaveColorToServer();
        };
        popover.appendChild(okBtn);
        document.body.appendChild(popover);

        // position below the swatch
        var rect = swatchEl.getBoundingClientRect();
        popover.style.top  = (rect.bottom + 4) + 'px';
        popover.style.left = rect.left + 'px';

        // close on outside click
        setTimeout(function () {
            document.addEventListener('click', function _close(e) {
                if (!popover.contains(e.target)) {
                    popover.remove();
                    document.removeEventListener('click', _close);
                }
            });
        }, 10);
    };

    function _optSaveColorToServer() {
    var reportId   = _optState.reportId;
    var cfg        = window.rptGetConfig ? window.rptGetConfig(reportId) : null;
    var extra      = _reportExtraFields[reportId] || {};
    var mrName     = extra.mrName || (cfg && cfg.mrName) || '';
    var styleName  = _filterState.headerVals && _filterState.headerVals.reportStyle
        ? _filterState.headerVals.reportStyle : '';

    if (!styleName) {
        /* No style loaded — open Save Report modal so user can name it */
        _srModal.open({ reportId: reportId, mrName: mrName });
        return;
    }

    /* Reuse _srSave logic inline with known style name */
    var cols = _optState.cols.filter(function (c) { return c.show !== false; });
    if (!cols.length) { _toast('No columns to save', 'w'); return; }

    var details = cols.map(function (c, i) {
        var widthNum = parseFloat(String(c.width || '').replace(/[^0-9.]/g, '')) || 0;
        var alignNum = parseInt(String(c.align || '0'), 10) || 0;
        return {
            ReportName  : styleName,
            MRName      : mrName,
            Section     : c.key,
            FName       : c.label,
            UFName      : c.label,
            Width       : widthNum,
            Index       : i + 1,
            Alignment   : alignNum,
            Show        : c.show !== false ? 1 : 0,
            Heder       : 0,
            Break       : 0,
            UIndex      : i + 1,
            UWidth      : widthNum,
            MReport     : 0,
            DField      : 0,
            Font        : 0,
            FieldType   : c.fieldType || 1,
            FormatText  : c.format || '',
            FontName    : '',
            SYS_ITEM    : 0,
            Color       : c.color || '',
            TextColor   : c.textColor || '',
            FKTable     : c.fkTable || '',
            FKIDField   : c.fkIdField || '',
            FKField     : c.fkField || '',
        };
    });

    fetch('/common/report/save-style/', {
        method  : 'POST',
        headers : { 'Content-Type': 'application/json', 'X-CSRFToken': _csrf() },
        body    : JSON.stringify({
            report_name : styleName,
            mr_name     : mrName,
            details     : details,
            overwrite   : true,   // always overwrite existing style
        }),
    })
    .then(function (r) { return r.json(); })
    .then(function (d) {
        if (d.success) {
            _toast('Color saved to "' + styleName + '"', 's');
            delete _headerCache.styles[mrName];
        } else {
            _toast(d.error || 'Save failed', 'e');
        }
    })
    .catch(function (e) { _toast('Network error: ' + e, 'e'); });
}


    /* ═════════════════════════════════════════════════════════════════
       GET FIELDS MODAL
    ═════════════════════════════════════════════════════════════════ */
    var _gfState = { tables: [], fields: {}, activeTable: '', callback: null, reportId: '' };
    var _gfCache = {};

    function _fetchFieldsSchema(reportId, cb) {
        if (_gfCache[reportId]) { cb(_gfCache[reportId]); return; }
        var url = (global._rptFieldsUrl && global._rptFieldsUrl[reportId])
            ? global._rptFieldsUrl[reportId]
            : '/common/report/fields/?report=' + encodeURIComponent(reportId);
        fetch(url)
            .then(function (r) { return r.json(); })
            .then(function (d) {
                if (d.success) {
                    _gfCache[reportId] = { tables: d.tables || [], fields: d.fields || {} };
                    cb(_gfCache[reportId]);
                } else { cb({ tables: [], fields: {} }); }
            })
            .catch(function () { cb({ tables: [], fields: {} }); });
    }

    var _gfModal = new UtilityModal({
        id: 'rptf-gf', title: 'Get Fields',
        icon: '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/>',
        tabs: [{ id: 'gf', label: '» Tables / Fields', icon: 'doc' }],
        onBuild: function (modal) {
            var nav = document.getElementById('rptf-gf-nav');
            if (nav) nav.style.cssText = 'display:none!important';
            var pane = modal.pane('gf');
            if (!pane) return;
            pane.style.padding = '0'; pane.style.overflow = 'hidden';
            pane.style.flexDirection = 'row'; pane.style.gap = '0';
            var left = document.createElement('div');
            left.style.cssText = 'width:45%;display:flex;flex-direction:column;min-width:0;border-right:1px solid var(--color-border,#ddd)';
            left.innerHTML = '<div class="gf-panel-hdr">Table Name</div><div class="gf-search"><input type="text" id="gf-tbl-search" placeholder="Search tables…"></div><div class="gf-list" id="gf-table-list"><div class="gf-empty">Loading…</div></div>';
            var right = document.createElement('div');
            right.style.cssText = 'flex:1;display:flex;flex-direction:column;min-width:0';
            right.innerHTML = '<div class="gf-panel-hdr">Field Name</div><div class="gf-search"><input type="text" id="gf-fld-search" placeholder="Search fields…"></div><div class="gf-list" id="gf-field-list"><div class="gf-empty">Select a table</div></div>';
            pane.appendChild(left); pane.appendChild(right);
            left.querySelector('#gf-tbl-search').addEventListener('input', function () { _renderGfTables(this.value); });
            right.querySelector('#gf-fld-search').addEventListener('input', function () { _renderGfFields(_gfState.activeTable, this.value); });
        },
        onOpen: function (modal, ctx) {
            _gfState.reportId = ctx.reportId || ''; _gfState.callback = ctx.callback || null;
            _gfState.activeTable = ''; _gfState.tables = []; _gfState.fields = {};
            var tblList = document.getElementById('gf-table-list');
            var fldList = document.getElementById('gf-field-list');
            var ts = document.getElementById('gf-tbl-search');
            var fs = document.getElementById('gf-fld-search');
            if (tblList) tblList.innerHTML = '<div class="gf-empty">Loading…</div>';
            if (fldList) fldList.innerHTML = '<div class="gf-empty">Select a table</div>';
            if (ts) ts.value = ''; if (fs) fs.value = '';
            _fetchFieldsSchema(ctx.reportId, function (schema) {
                _gfState.tables = schema.tables || []; _gfState.fields = schema.fields || {};
                _renderGfTables('');
            });
        },
    });

    function _openGetFields(reportId, cb) {
        _gfModal.open({ reportId: reportId, callback: cb });
        setTimeout(function () { var bd = document.getElementById('rptf-gf-bd'); if (bd) bd.style.zIndex = '2300'; }, 0);
    }

    global._rptGfSelectTable = function (t) { _gfSelectTable(t); };

    function _renderGfTables(q) {
        var list = document.getElementById('gf-table-list'); if (!list) return;
        var tables = q ? _gfState.tables.filter(function (t) { return t.toLowerCase().indexOf(q.toLowerCase()) !== -1; }) : _gfState.tables;
        if (!tables.length) { list.innerHTML = '<div class="gf-empty">' + (_gfState.tables.length ? 'No tables match' : 'No tables found') + '</div>'; return; }
        list.innerHTML = '';
        tables.forEach(function (t) {
            var div = document.createElement('div');
            div.className = 'gf-item' + (t === _gfState.activeTable ? ' gf-active' : '');
            div.dataset.table = t; div.textContent = t;
            div.addEventListener('click', function () { _gfSelectTable(t); });
            list.appendChild(div);
        });
    }

    function _gfSelectTable(tableName) {
        _gfState.activeTable = tableName;
        document.querySelectorAll('#gf-table-list .gf-item').forEach(function (el) { el.classList.toggle('gf-active', el.dataset.table === tableName); });
        var fs = document.getElementById('gf-fld-search'); if (fs) fs.value = '';
        _renderGfFields(tableName, '');
    }

    function _renderGfFields(tableName, q) {
        var list = document.getElementById('gf-field-list'); if (!list) return;
        if (!tableName) { list.innerHTML = '<div class="gf-empty">Select a table</div>'; return; }
        var allFields = _gfState.fields[tableName] || [];
        var fields = q ? allFields.filter(function (f) { return f.toLowerCase().indexOf(q.toLowerCase()) !== -1; }) : allFields;
        if (!fields.length) { list.innerHTML = '<div class="gf-empty">' + (allFields.length ? 'No match' : 'No fields found') + '</div>'; return; }
        list.innerHTML = '';
        fields.forEach(function (f) {
            var div = document.createElement('div');
            div.className = 'gf-field-item'; div.dataset.field = f; div.dataset.table = tableName; div.textContent = f;
            div.addEventListener('click', function () { _gfPickField(tableName, f); });
            list.appendChild(div);
        });
    }

    function _toSnakeCase(s) {
        if (!s) return '';
        if (/^[a-z0-9_]+$/.test(s)) return s;
        return s
            .replace(/([A-Z]+)([A-Z][a-z])/g, '$1_$2')
            .replace(/([a-z0-9])([A-Z])/g, '$1_$2')
            .toLowerCase();
    }

    

    function _gfPickField(tableName, fieldName) {
        _gfModal.close();
        if (typeof _gfState.callback === 'function') {
            var snakeKey = _toSnakeCase(fieldName);
            _gfState.callback(tableName, fieldName, snakeKey);
        }
    }

    /* ═════════════════════════════════════════════════════════════════
       1. FILTER MODAL
    ═════════════════════════════════════════════════════════════════ */
    /* ── Filter modal via UtilityModal engine ── */
    var _filterModal = new UtilityModal({
        id: 'rptf-filter',
        title: 'Filter',
        icon: '<polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"/>',
        tabs: [{ id: 'filter', label: '» Filter', icon: 'doc' }],
        toolbar: [
            { label: 'OK', icon: 'save', danger: false, onclick: function () { _applyFilter(); } },
            { label: 'Cancel', icon: 'close', danger: false, onclick: function () { _filterModal.close(); } },
            { label: 'Remove', icon: 'del', danger: true, onclick: function () { _removeSelectedFilterRow(); } },
            { label: 'Default', icon: 'refresh', danger: false, onclick: function () { _loadDefaultFilterRows(); } },
            { label: 'Menu', icon: 'doc', danger: false, onclick: function () { _toggleFilterMenu(); } },
        ],
        onBuild: function (modal) {
            /* Hide sidenav — single-pane modal */
            var nav = document.getElementById('rptf-filter-nav');
            if (nav) nav.style.cssText = 'display:none!important;width:0;overflow:hidden';

            var pane = modal.pane('filter');
            if (!pane) return;
            pane.style.padding = '10px 14px';
            pane.style.gap = '0';

            /* Header fields zone */
            var hdrFields = document.createElement('div');
            hdrFields.id = 'rptf-hdr-fields';
            hdrFields.className = 'rptf-hdr';
            pane.appendChild(hdrFields);



            /* Grid */
            var tblWrap = document.createElement('div');
            tblWrap.style.cssText = 'flex:1;min-height:120px;overflow-y:auto;' +
                'border:1px solid var(--color-border-light,#e0e0e0);border-radius:4px';
            tblWrap.innerHTML = [
                '<table style="width:100%;border-collapse:collapse;font-size:12px">',
                '<thead><tr style="background:var(--color-bg-tertiary,#f5f5f5)">',
                '<th style="width:30px;padding:6px 8px;border-bottom:2px solid var(--color-border-light,#ddd);',
                'font-size:11px;font-weight:700;color:var(--color-text-tertiary,#888);text-align:center">SN</th>',
                '<th style="padding:6px 8px;border-bottom:2px solid var(--color-border-light,#ddd);',
                'font-size:11px;font-weight:700;color:var(--color-text-tertiary,#888);text-align:left">Field Name</th>',
                '<th style="padding:6px 8px;border-bottom:2px solid var(--color-border-light,#ddd);',
                'font-size:11px;font-weight:700;color:var(--color-text-tertiary,#888);text-align:left">Value</th>',
                '<th style="width:90px;padding:6px 8px;border-bottom:2px solid var(--color-border-light,#ddd);',
                'font-size:11px;font-weight:700;color:var(--color-text-tertiary,#888);text-align:left">Operator</th>',
                '<th style="width:30px;padding:6px 8px;border-bottom:2px solid var(--color-border-light,#ddd)"></th>',
                '</tr></thead>',
                '<tbody id="rpt-filter-tbody"></tbody>',
                '</table>',
            ].join('');
            pane.appendChild(tblWrap);

            /* Menu dropdown element */
            var menuEl = document.createElement('div');
            menuEl.id = 'rpt-filter-menu';
            menuEl.style.cssText = 'position:fixed;background:var(--color-bg-card,#fff);' +
                'border:1px solid var(--color-border-light,#e0e0e0);border-radius:6px;' +
                'box-shadow:0 6px 20px rgba(0,0,0,.14);z-index:2000;min-width:160px;' +
                'padding:4px 0;display:none';
            menuEl.innerHTML = '<div class="rfm-item" onclick="rptOpenEditFilter()">Edit Filter</div>';
            document.body.appendChild(menuEl);

            document.addEventListener('click', function (e) {
                if (!e.target.classList.contains('rfr-inp')) _closeAllAutocomplete();
            });
        },
        onOpen: function (modal, ctx) {
            var reportId = ctx.reportId || '';
            modal.setSubtitle(reportId);
            _filterState.reportId = reportId;
            _filterState.loaded = false;

            var st = window.rptGetState ? window.rptGetState(reportId) : null;
            _filterState.filterRows = (st && st.modalFilters)
                ? JSON.parse(JSON.stringify(st.modalFilters)) : [];

            _buildHeaderFields(reportId);
            _loadFieldDefs(reportId, function () {
                _renderFilterRows();
            });
        },
    });


    var _reportExtraFields = {
        'emp-report': {
            mrName: 'EmployeeReport',
            showType: true,
            showStatus: true,
            typeOptions: [
                { value: '', label: 'All' },
                { value: 'id_expiry', label: 'ID Expiry' },
                { value: 'passport_expiry', label: 'Passport Expiry' },
                { value: 'medical_expiry', label: 'Medical Card Expiry' },
            ],
            statusOptions: [
                { value: '', label: 'All' },
                { value: 'active', label: 'Active' },
                { value: 'expired', label: 'Expired' },
            ],
        },
    };

    var _headerCache = { styles: {}, depts: null, period: null };

    function _fetchReportStyles(mrName, cb) {
        if (!mrName) { cb([]); return; }
        if (_headerCache.styles[mrName]) { cb(_headerCache.styles[mrName]); return; }
        fetch('/common/filter/report-styles/?mr_name=' + encodeURIComponent(mrName))
            .then(function (r) { return r.json(); })
            .then(function (d) { var s = (d.success && d.styles) ? d.styles : []; _headerCache.styles[mrName] = s; cb(s); })
            .catch(function () { cb([]); });
    }

    function _fetchDeptOptions(cb) {
        if (_headerCache.depts) { cb(_headerCache.depts); return; }
        fetch('/common/filter/dept-options/')
            .then(function (r) { return r.json(); })
            .then(function (d) { var o = (d.success && d.options) ? d.options : []; _headerCache.depts = o; cb(o); })
            .catch(function () { cb([]); });
    }

    function _fetchPeriodDates(cb) {
        if (_headerCache.period) { cb(_headerCache.period); return; }
        fetch('/common/filter/period-dates/')
            .then(function (r) { return r.json(); })
            .then(function (d) { var p = d.success ? { from: d.period_from || '', to: d.period_to || '' } : { from: '', to: '' }; _headerCache.period = p; cb(p); })
            .catch(function () { cb({ from: '', to: '' }); });
    }

    function _getFieldValues(reportId, fieldName) {
        if (!fieldName) return [];
        var st = window.rptGetState ? window.rptGetState(reportId) : null;
        if (!st || !st.allRows) return [];
        var seen = {}, vals = [];
        st.allRows.forEach(function (row) { var v = String(row[fieldName] || '').trim(); if (v && !seen[v]) { seen[v] = true; vals.push(v); } });
        vals.sort(function (a, b) { return a.toLowerCase() < b.toLowerCase() ? -1 : 1; });
        return vals;
    }

    var _foreignOptionsCache = {};

    function _fetchForeignOptions(def, cb) {
        var cacheKey = _filterState.reportId + '|' + def.FieldName;
        if (_foreignOptionsCache[cacheKey]) { cb(_foreignOptionsCache[cacheKey]); return; }
        fetch('/common/filter/foreign-options/?report=' + encodeURIComponent(_filterState.reportId) + '&field=' + encodeURIComponent(def.FieldName))
            .then(function (r) { return r.json(); })
            .then(function (d) { var opts = (d.success && d.options) ? d.options : []; _foreignOptionsCache[cacheKey] = opts; cb(opts); })
            .catch(function () { cb([]); });
    }

    function _closeAllAutocomplete() { document.querySelectorAll('.rfr-ac').forEach(function (el) { el.remove(); }); }

    function _buildAutocomplete(inp, values, idx) {
        _closeAllAutocomplete(); if (!values.length) return;
        var td = inp.parentNode; if (!td) return; td.style.position = 'relative';
        var ac = document.createElement('div'); ac.className = 'rfr-ac'; ac.id = 'rfr-ac-' + idx;
        var q = inp.value.toLowerCase();
        var filtered = q ? values.filter(function (v) { return v.toLowerCase().indexOf(q) !== -1; }) : values;
        if (!filtered.length) return;
        filtered.slice(0, 20).forEach(function (val) {
            var item = document.createElement('div'); item.className = 'rfr-ac-item';
            if (q) { var lo = val.toLowerCase(), pos = lo.indexOf(q); if (pos >= 0) { item.innerHTML = _esc(val.slice(0, pos)) + '<strong>' + _esc(val.slice(pos, pos + q.length)) + '</strong>' + _esc(val.slice(pos + q.length)); } else { item.textContent = val; } } else { item.textContent = val; }
            item.addEventListener('mousedown', function (e) { e.preventDefault(); inp.value = val; _closeAllAutocomplete(); if (_filterState.filterRows[idx] !== undefined) _filterState.filterRows[idx].value = val; });
            ac.appendChild(item);
        });
        td.appendChild(ac);
    }

    function _buildFKAutocomplete(displayInp, hiddenInp, options, idx) {
        _closeAllAutocomplete();
        var td = displayInp.parentNode; if (!td) return; td.style.position = 'relative';
        var q = displayInp.value.toLowerCase();
        var filtered = q ? options.filter(function (o) { return o.label.toLowerCase().indexOf(q) !== -1; }) : options;
        if (!filtered.length) return;
        var ac = document.createElement('div'); ac.className = 'rfr-ac'; ac.id = 'rfr-ac-' + idx;
        filtered.slice(0, 30).forEach(function (opt) {
            var item = document.createElement('div'); item.className = 'rfr-ac-item';
            if (q) { var lo = opt.label.toLowerCase(), pos = lo.indexOf(q); if (pos >= 0) { item.innerHTML = _esc(opt.label.slice(0, pos)) + '<strong>' + _esc(opt.label.slice(pos, pos + q.length)) + '</strong>' + _esc(opt.label.slice(pos + q.length)); } else { item.textContent = opt.label; } } else { item.textContent = opt.label; }
            item.addEventListener('mousedown', function (e) { e.preventDefault(); displayInp.value = opt.label; if (hiddenInp) hiddenInp.value = opt.value; if (_filterState.filterRows[idx] !== undefined) { _filterState.filterRows[idx].value = opt.value; _filterState.filterRows[idx].displayValue = opt.label; } _closeAllAutocomplete(); });
            ac.appendChild(item);
        });
        td.appendChild(ac);
    }

    function _buildHeaderFields(reportId) {
        var wrap = document.getElementById('rptf-hdr-fields'); if (!wrap) return;
        wrap.innerHTML = '<div style="font-size:11px;color:var(--color-text-tertiary,#aaa);padding:8px 0">Loading…</div>';
    //     var extra = _reportExtraFields[reportId] || {};
        var extra = _reportExtraFields[reportId] || (window._reportExtraFields && window._reportExtraFields[reportId]) || {};
        var cfg = window.rptGetConfig ? window.rptGetConfig(reportId) : null;
        var mrName = extra.mrName || (cfg && cfg.mrName) || '';
        var stylesLoaded = false, deptsLoaded = false, periodLoaded = false;
        var styles = [], depts = [], period = { from: '', to: '' };
        function _tryRender() { if (!stylesLoaded || !deptsLoaded || !periodLoaded) return; _renderHeaderFields(reportId, extra, styles, depts, period); }
        _fetchReportStyles(mrName, function (s) { styles = s; stylesLoaded = true; _tryRender(); });
        _fetchDeptOptions(function (d) { depts = d; deptsLoaded = true; _tryRender(); });
        _fetchPeriodDates(function (p) { period = p; periodLoaded = true; _tryRender(); });
    }

    function _renderHeaderFields(reportId, extra, styles, depts, period) {
        var wrap = document.getElementById('rptf-hdr-fields'); if (!wrap) return;
        var hv = _filterState.headerVals || {};

        var styleOpts = styles.map(function (s) {
            return '<option value="' + _esc(s) + '">' + _esc(s) + '</option>';
        }).join('');
        var deptOpts = '<option value="">All</option>' + depts.map(function (d) {
            return '<option value="' + _esc(d.value) + '">' + _esc(d.label) + '</option>';
        }).join('');

        /*
         * Layout — two fluid rows, each using CSS grid with auto-fill columns
         * so width is fully dynamic (no hardcoded px widths).
         *
         * Row 1: Report Style  |  Dept/Project
         * Row 2: Date From  |  Date To  |  Status (if showStatus)  |  Type (if showType)
         */

        /* ── Row 1 ── */
        var row1 = '<div class="rptf-hdr-row">'
            + '<div class="rptf-hdr-field">'
            + '<label>Report Style</label>'
            + '<select id="rptf-report-style"><option value="">-- Select --</option>' + styleOpts + '</select>'
            + '</div>'
            + '<div class="rptf-hdr-field">'
            + '<label>Dept / Project</label>'
            + '<select id="rptf-dept-project">' + deptOpts + '</select>'
            + '</div>'
            + '</div>';

        /* ── Row 2 ── */
        var row2Fields = [
            '<div class="rptf-hdr-field"><label>Date From</label><div id="rptf-date-from-wrap"></div></div>',
            '<div class="rptf-hdr-field"><label>Date To</label><div id="rptf-date-to-wrap"></div></div>',
        ];
        if (extra.showStatus) {
            row2Fields.push(
                '<div class="rptf-hdr-field"><label>Status</label>'
                + '<select id="rptf-status">'
                + (extra.statusOptions || []).map(function (o) {
                    return '<option value="' + _esc(o.value) + '">' + _esc(o.label) + '</option>';
                }).join('')
                + '</select></div>'
            );
        }
        if (extra.showType) {
            row2Fields.push(
                '<div class="rptf-hdr-field"><label>Type</label>'
                + '<select id="rptf-type">'
                + (extra.typeOptions || []).map(function (o) {
                    return '<option value="' + _esc(o.value) + '">' + _esc(o.label) + '</option>';
                }).join('')
                + '</select></div>'
            );
        }
        var row2 = '<div class="rptf-hdr-row">' + row2Fields.join('') + '</div>';

        wrap.innerHTML = row1 + row2;

        /* inject datepickers first (they create their own DOM inside the wrap divs) */
        _dpInject('rptf-date-from-wrap', 'rptf_date_from', hv.dateFrom || period.from || '');
        _dpInject('rptf-date-to-wrap', 'rptf_date_to', hv.dateTo || period.to || '');

        /* set select values before upgrading */
        _setVal('rptf-report-style', hv.reportStyle || '');
        _setVal('rptf-dept-project', hv.deptProject || '');
        if (extra.showStatus) _setVal('rptf-status', hv.status || '');
        if (extra.showType) _setVal('rptf-type', hv.type || '');

        /* upgrade selects once, after values set */
        _pfSelUpgradeAll(wrap);
    }

    function _setVal(id, val) { var el = document.getElementById(id); if (!el) return; el.value = val || ''; }
    function _getVal(id) { var el = document.getElementById(id); return el ? el.value : ''; }

    /**
     * _dpInject(wrapperId, fieldName, isoValue)
     * Renders the datepicker.html pattern into a container div entirely in JS,
     * matching the Django template output of datepicker.html v1.3.
     * fieldName  — used as the hidden input id/name and as the dp_ prefix base.
     * isoValue   — YYYY-MM-DD string (may be empty).
     */
    function _dpInject(wrapperId, fieldName, isoValue) {
        var wrap = document.getElementById(wrapperId);
        if (!wrap) { console.warn('[dpInject] wrapper not found:', wrapperId); return; }
        if (!wrap) return;
        var dpid = 'dp_' + fieldName;
        var display = '';
        if (isoValue && /^\d{4}-\d{2}-\d{2}$/.test(isoValue)) {
            var p = isoValue.split('-');
            display = p[2] + '-' + p[1] + '-' + p[0];   // DD-MM-YYYY
        }
        wrap.innerHTML = [
            '<input type="hidden" id="' + fieldName + '" name="' + fieldName + '" value="' + (isoValue || '') + '">',
            '<div class="dp-input-wrap" id="' + dpid + '_wrap" onclick="dpToggle(\'' + dpid + '\', event)">',
            '  <span class="dp-display' + (isoValue ? ' has-value' : '') + '" id="' + dpid + '_display">',
            '    ' + (display || 'Choose Date'),
            '  </span>',
            '  <svg class="dp-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">',
            '    <rect x="3" y="4" width="18" height="18" rx="3"/>',
            '    <path d="M16 2v4M8 2v4M3 10h18"/>',
            '    <path d="M8 14h.01M12 14h.01M16 14h.01M8 18h.01M12 18h.01" stroke-linecap="round"/>',
            '  </svg>',
            '</div>',
            '<div class="dp-calendar" id="' + dpid + '_cal"></div>',
        ].join('');
        /* register with the datepicker engine */
        if (typeof window.dpRegister === 'function') {
            window.dpRegister(dpid, isoValue || '');
        } else if (window._dpPickers) {
            _dpBootPicker(dpid, fieldName, isoValue || '');
        }
    }



    // ── ADD after the existing _filterModal declaration ──────────────────────────

var _entryFilterState = {
    reportId: '',
    filterRows: [],
    fieldDefs: [],
    loaded: false,
    headerVals: {},
    showMenu: false,          // ← NEW: set true to show Menu→Edit Filter button
};

var _entryFilterModal = new UtilityModal({
    id: 'rptf-entry-filter',
    title: 'Filter',
    icon: '<polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"/>',
    tabs: [{ id: 'filter', label: '» Filter', icon: 'doc' }],
    toolbar: [
        { label: 'OK',      icon: 'save',    danger: false, onclick: function () { _applyEntryFilter(); } },
        { label: 'Cancel',  icon: 'close',   danger: false, onclick: function () { _entryFilterModal.close(); } },
        { label: 'Remove',  icon: 'del',     danger: true,  onclick: function () { _removeSelectedEntryFilterRow(); } },
        { label: 'Default', icon: 'refresh', danger: false, onclick: function () { _loadDefaultEntryFilterRows(); } },
        { label: 'Menu',    icon: 'doc',     danger: false, id: 'rptf-entry-filter-menu-btn',
          onclick: function () { _toggleEntryFilterMenu(); } },
    ],
    onBuild: function (modal) {
        var nav = document.getElementById('rptf-entry-filter-nav');
        if (nav) nav.style.cssText = 'display:none!important;width:0;overflow:hidden';
        var pane = modal.pane('filter');
        if (!pane) return;
        pane.style.padding = '10px 14px';
        pane.style.gap = '0';
        var tblWrap = document.createElement('div');
        tblWrap.style.cssText = 'flex:1;min-height:120px;overflow-y:auto;' +
            'border:1px solid var(--color-border-light,#e0e0e0);border-radius:4px';
        tblWrap.innerHTML = [
            '<table style="width:100%;border-collapse:collapse;font-size:12px">',
            '<thead><tr style="background:var(--color-bg-tertiary,#f5f5f5)">',
            '<th style="width:30px;padding:6px 8px;border-bottom:2px solid var(--color-border-light,#ddd);font-size:11px;font-weight:700;color:var(--color-text-tertiary,#888);text-align:center">SN</th>',
            '<th style="padding:6px 8px;border-bottom:2px solid var(--color-border-light,#ddd);font-size:11px;font-weight:700;color:var(--color-text-tertiary,#888);text-align:left">Field Name</th>',
            '<th style="padding:6px 8px;border-bottom:2px solid var(--color-border-light,#ddd);font-size:11px;font-weight:700;color:var(--color-text-tertiary,#888);text-align:left">Value</th>',
            '<th style="width:90px;padding:6px 8px;border-bottom:2px solid var(--color-border-light,#ddd);font-size:11px;font-weight:700;color:var(--color-text-tertiary,#888);text-align:left">Operator</th>',
            '<th style="width:30px;padding:6px 8px;border-bottom:2px solid var(--color-border-light,#ddd)"></th>',
            '</tr></thead>',
            '<tbody id="rpt-entry-filter-tbody"></tbody>',
            '</table>',
        ].join('');
        pane.appendChild(tblWrap);
        document.addEventListener('click', function (e) {
            if (!e.target.classList.contains('rfr-inp')) _closeAllAutocomplete();
        });
    },
    onOpen: function (modal, ctx) {
        var reportId = ctx.reportId || '';
        modal.setSubtitle(reportId);
        _entryFilterState.reportId = reportId;
        _entryFilterState.loaded   = false;
        _entryFilterState.showMenu = !!(ctx.showMenu);
 
        /* Show or hide the Menu toolbar button based on showMenu flag */
        setTimeout(function () {
            var bd = document.getElementById('rptf-entry-filter-bd');
            if (bd) {
                bd.querySelectorAll('button').forEach(function (b) {
                    if ((b.textContent || '').trim() === 'Menu') {
                        b.style.display = _entryFilterState.showMenu ? '' : 'none';
                    }
                });
            }
        }, 0);
 
        var st = window.rptGetState ? window.rptGetState(reportId) : null;
        _entryFilterState.filterRows = (st && st.modalFilters)
            ? JSON.parse(JSON.stringify(st.modalFilters)) : [];
        _loadEntryFieldDefs(reportId, function () {
            _renderEntryFilterRows();
        });
    },
});

// ── Entry filter: field defs loader ─────────────────────────────────────────
function _loadEntryFieldDefs(reportId, cb) {
    var cfg = window.rptGetConfig ? window.rptGetConfig(reportId) : null;
    var url = (cfg && cfg.filterLoadUrl) ? cfg.filterLoadUrl : '/common/filter/load/';
    fetch(url + '?report=' + encodeURIComponent(reportId))
        .then(function (r) { return r.json(); })
        .then(function (d) {
            _entryFilterState.fieldDefs = (d.success && d.filters && d.filters.length)
                ? d.filters : _colsToFieldDefsFor(reportId);
            _entryFilterState.loaded = true;
            if (typeof cb === 'function') cb();
        })
        .catch(function () {
            _entryFilterState.fieldDefs = _colsToFieldDefsFor(reportId);
            _entryFilterState.loaded = true;
            if (typeof cb === 'function') cb();
        });
}

// same as _colsToFieldDefs but doesn't touch _filterState
function _colsToFieldDefsFor(reportId) {
    var cfg = window.rptGetConfig ? window.rptGetConfig(reportId) : null;
    return (cfg && cfg.cols ? cfg.cols : []).map(function (c) {
        return { FieldName: c.key, DisplayName: c.label, FieldType: 1, FilterSql: '', ColWidth: '', IDField: '', Default: 0, Operator: 0 };
    });
}

// ── Entry filter: render rows ────────────────────────────────────────────────
function _renderEntryFilterRows() {
    var tbody = document.getElementById('rpt-entry-filter-tbody'); if (!tbody) return;
    var defs = _entryFilterState.fieldDefs || [];
    if (!_entryFilterState.filterRows.length)
        _entryFilterState.filterRows = [{ field: '', value: '', operator: 0 }];
    tbody.innerHTML = _entryFilterState.filterRows.map(function (row, i) {
        var fieldOpts = '<option value="">-- Field --</option>' +
            defs.map(function (d) {
                var sel = d.FieldName === row.field ? ' selected' : '';
                return '<option value="' + _esc(d.FieldName) + '"' + sel + '>' +
                    _esc(d.DisplayName || d.FieldName) + '</option>';
            }).join('');
        var def = defs.find(function (d) { return d.FieldName === row.field; }) || null;
        var opSel = (i === 0)
            ? '<span style="font-size:11px;color:var(--color-text-tertiary,#888);padding:0 4px">—</span>'
            : '<select class="rfr-op rfr-sel">' +
              '<option value="0"' + (row.operator === 0 ? ' selected' : '') + '>AND</option>' +
              '<option value="1"' + (row.operator === 1 ? ' selected' : '') + '>OR</option></select>';
        var delBtn = '<button class="rfr-del-btn" type="button" ' +
            'onclick="event.stopPropagation();rptEntryFilterDeleteRow(' + i + ')" title="Delete row">✕</button>';
        return '<tr data-idx="' + i + '" style="cursor:pointer;border-bottom:1px solid var(--color-border-light,#eee)">' +
            '<td style="padding:5px 8px;text-align:center;color:var(--color-text-tertiary,#aaa);font-size:11px" onclick="rptFilterRowSelect(this.parentNode)">' + (i + 1) + '</td>' +
            '<td class="rfr-td-input" onclick="event.stopPropagation();rptFilterRowSelect(this.parentNode)">' +
                '<select class="rfr-field rfr-sel" onchange="rptEntryFilterFieldChange(' + i + ',this)">' + fieldOpts + '</select></td>' +
            '<td class="rfr-td-input" onclick="event.stopPropagation();rptFilterRowSelect(this.parentNode)" id="rfr-entry-val-td-' + i + '">' +
                _buildEntryValueInput(row, def, i) + '</td>' +
            '<td style="padding:4px 8px" onclick="event.stopPropagation();rptFilterRowSelect(this.parentNode)">' + opSel + '</td>' +
            '<td style="padding:4px 6px;text-align:center" onclick="event.stopPropagation()">' + delBtn + '</td>' +
            '</tr>';
    }).join('');
    _pfSelUpgradeAll(tbody);
    tbody.querySelectorAll('input[id^="rfr_date_"]').forEach(function (inp) {
        _dpBootPicker('dp_' + inp.id, inp.id, inp.value || '');
    });
    _attachEntryAutocompleteListeners();
}

// ── Entry filter: autocomplete ───────────────────────────────────────────────
function _attachEntryAutocompleteListeners() {
    var tbody = document.getElementById('rpt-entry-filter-tbody'); if (!tbody) return;
    tbody.querySelectorAll('tr[data-idx]').forEach(function (tr) {
        var idx        = parseInt(tr.dataset.idx, 10);
        var displayInp = tr.querySelector('input.rfr-display');
        var hiddenInp  = tr.querySelector('input.rfr-value');
        var isFK       = !!displayInp;
        var inp        = displayInp || hiddenInp;
        if (!inp) return;
        function _openAC() {
            var row       = _entryFilterState.filterRows[idx];
            var fieldName = row ? row.field : '';
            var def       = (_entryFilterState.fieldDefs || []).find(function (d) { return d.FieldName === fieldName; });
            var ft        = def ? parseInt(def.FieldType, 10) : 1;
            if (isFK && ft === 3 && def && (def.FilterSql || '').trim() && (def.IDField || '').trim()) {
                var cacheKey = _entryFilterState.reportId + '|' + def.FieldName;
                if (_foreignOptionsCache[cacheKey]) {
                    _buildFKAutocomplete(inp, hiddenInp, _foreignOptionsCache[cacheKey], idx);
                } else {
                    fetch('/common/filter/foreign-options/?report=' + encodeURIComponent(_entryFilterState.reportId) +
                          '&field=' + encodeURIComponent(def.FieldName))
                        .then(function (r) { return r.json(); })
                        .then(function (d) {
                            var opts = (d.success && d.options) ? d.options : [];
                            _foreignOptionsCache[cacheKey] = opts;
                            _buildFKAutocomplete(inp, hiddenInp, opts, idx);
                        })
                        .catch(function () { });
                }
            } else {
                _buildAutocomplete(inp, _getFieldValues(_entryFilterState.reportId, fieldName), idx);
            }
        }
        inp.addEventListener('focus', _openAC);
        inp.addEventListener('input', function () {
            _openAC();
            if (!isFK && _entryFilterState.filterRows[idx] !== undefined)
                _entryFilterState.filterRows[idx].value = inp.value;
        });
        inp.addEventListener('keydown', function (e) {
            var ac = document.getElementById('rfr-ac-' + idx);
if (!ac) { if (e.key === 'Enter') { e.preventDefault(); if (inp.value.trim()) rptEntryFilterAddRow(); } return; }
            var items     = ac.querySelectorAll('.rfr-ac-item');
            var active    = ac.querySelector('.rfr-ac-active');
            var activeIdx = -1;
            items.forEach(function (it, i) { if (it === active) activeIdx = i; });
            if (e.key === 'ArrowDown') {
                e.preventDefault();
                var next = activeIdx < items.length - 1 ? activeIdx + 1 : 0;
                items.forEach(function (it) { it.classList.remove('rfr-ac-active'); });
                items[next].classList.add('rfr-ac-active'); items[next].scrollIntoView({ block: 'nearest' });
            } else if (e.key === 'ArrowUp') {
                e.preventDefault();
                var prev = activeIdx > 0 ? activeIdx - 1 : items.length - 1;
                items.forEach(function (it) { it.classList.remove('rfr-ac-active'); });
                items[prev].classList.add('rfr-ac-active'); items[prev].scrollIntoView({ block: 'nearest' });
            } else if (e.key === 'Enter') {
                e.preventDefault();
                if (active) active.dispatchEvent(new MouseEvent('mousedown', { bubbles: true }));
                else { _closeAllAutocomplete(); if (inp.value.trim()) rptEntryFilterAddRow(); }
            } else if (e.key === 'Escape') { _closeAllAutocomplete(); }
        });
    });
}

// ── Entry filter: sync from DOM ──────────────────────────────────────────────
function _syncEntryFilterRowsFromDom() {
    var tbody = document.getElementById('rpt-entry-filter-tbody'); if (!tbody) return;
    tbody.querySelectorAll('tr[data-idx]').forEach(function (tr) {
        var i          = parseInt(tr.dataset.idx, 10);
        var sel        = tr.querySelector('select.rfr-field');
        var hiddenInp  = tr.querySelector('input.rfr-value');
        var fkIdInp    = tr.querySelector('input.rfr-fk-id');
        var fkSel      = tr.querySelector('select.rfr-fk-select');
        var fkSearch   = tr.querySelector('input.rfr-fk-search');
        var displayInp = tr.querySelector('input.rfr-display');
        var op         = tr.querySelector('select.rfr-op');

        if (_filterState.filterRows[i] === undefined) return;  // ← _filterState not _entryFilterState

        _filterState.filterRows[i].field    = sel ? sel.value : '';
        _filterState.filterRows[i].operator = op  ? parseInt(op.value, 10) : 0;

        var def = (_filterState.fieldDefs || []).find(function (d) {
            return d.FieldName === _filterState.filterRows[i].field;
        });
        var ft = def ? parseInt(def.FieldType, 10) : 1;

        if (ft === 6) {
            var dateHidden = document.getElementById('rfr_date_' + i);
            _filterState.filterRows[i].value = dateHidden ? dateHidden.value : '';
        } else if (ft === 3 && fkIdInp) {
            _filterState.filterRows[i].value        = fkIdInp.value;
            _filterState.filterRows[i].displayValue = fkSearch ? fkSearch.value : '';
        } else if (hiddenInp) {
            _filterState.filterRows[i].value = hiddenInp.value;
            if (displayInp) _filterState.filterRows[i].displayValue = displayInp.value;
        }
    });
}

// ── Entry filter: apply / helpers ────────────────────────────────────────────
function _applyEntryFilter() {
    _syncEntryFilterRowsFromDom();
    _closeAllAutocomplete();
    _logToTerminal(_entryFilterState.reportId, {}, _entryFilterState.filterRows);
    var fkCols = (_optState.cols || [])
        .filter(function (c) { return c.fieldType === 'fk' && c.fkTable && c.fkField; })
        .map(function (c) { return { key: c.key, fkTable: c.fkTable, fkIdField: c.fkIdField || '', fkField: c.fkField }; });
    if (typeof window.rptApplyReportFilter === 'function') {
        window.rptApplyReportFilter(_entryFilterState.reportId, {
            header: {},
            rows  : _entryFilterState.filterRows,
            fkCols: fkCols,
        });
    } else if (typeof rptApplyModalFilters === 'function') {
        rptApplyModalFilters(_entryFilterState.reportId, _entryFilterState.filterRows);
    }
    _entryFilterModal.close();
}

function _removeSelectedEntryFilterRow() {
    var tbody = document.getElementById('rpt-entry-filter-tbody'); if (!tbody) return;
    var sel = tbody.querySelector('tr.rfr-selected');
    if (!sel) { _toast('Select a row first', 'w'); return; }
    var idx = parseInt(sel.dataset.idx, 10);
    if (!isNaN(idx)) { _syncEntryFilterRowsFromDom(); _entryFilterState.filterRows.splice(idx, 1); }
    _closeAllAutocomplete(); _renderEntryFilterRows();
}

function _loadDefaultEntryFilterRows() {
    var defaults = (_entryFilterState.fieldDefs || []).filter(function (d) { return d.Default == 1; });
    _entryFilterState.filterRows = defaults.map(function (d) {
        return { field: d.FieldName, value: '', operator: parseInt(d.Operator, 10) || 0 };
    });
    if (!_entryFilterState.filterRows.length && _entryFilterState.fieldDefs.length)
        _entryFilterState.filterRows = [{ field: _entryFilterState.fieldDefs[0].FieldName, value: '', operator: 0 }];
    if (!_entryFilterState.filterRows.length)
        _entryFilterState.filterRows = [{ field: '', value: '', operator: 0 }];
    _renderEntryFilterRows();
}


function _toggleEntryFilterMenu() {
    var menuId = 'rpt-entry-filter-menu';
    var existing = document.getElementById(menuId);
    if (existing) { existing.remove(); return; }
 
    var menu = document.createElement('div');
    menu.id = menuId;
    menu.style.cssText = 'position:fixed;background:var(--color-bg-card,#fff);' +
        'border:1px solid var(--color-border-light,#e0e0e0);border-radius:6px;' +
        'box-shadow:0 6px 20px rgba(0,0,0,.14);z-index:10001;min-width:160px;' +
        'padding:4px 0;';
 
    var item = document.createElement('div');
    item.className = 'rfm-item';
    item.textContent = 'Edit Filter';
    item.style.cssText = 'padding:8px 14px;cursor:pointer;font-size:13px;' +
        'color:var(--color-text-primary,#111);';
    item.onmouseover = function () { item.style.background = 'var(--color-bg-hover,#f5f5f5)'; };
    item.onmouseout  = function () { item.style.background = ''; };
    item.onclick = function () {
        menu.remove();
        /* Open Edit Filter modal for the current entry-filter reportId */
        _efModal.open({ reportId: _entryFilterState.reportId });
        setTimeout(function () {
            var bd = document.getElementById('rpt-ef-modal-bd');
            if (bd) bd.style.zIndex = '2400';
        }, 0);
    };
    menu.appendChild(item);
    document.body.appendChild(menu);
 
    /* Position below the Menu button */
    var bd = document.getElementById('rptf-entry-filter-bd');
    var btn = null;
    if (bd) {
        bd.querySelectorAll('button').forEach(function (b) {
            if ((b.textContent || '').trim() === 'Menu') btn = b;
        });
    }
    if (btn) {
        var rect = btn.getBoundingClientRect();
        menu.style.top  = (rect.bottom + 4) + 'px';
        menu.style.left = rect.left + 'px';
    }
 
    setTimeout(function () {
        document.addEventListener('click', function _cm(e) {
            if (!menu.contains(e.target)) {
                menu.remove();
                document.removeEventListener('click', _cm);
            }
        });
    }, 10);
}

function _buildEntryValueInput(row, def, idx) {
    var ft = def ? parseInt(def.FieldType, 10) : 1;
 
    /* Only FieldType=3 (FK/select) gets the special dropdown treatment */
    if (ft !== 3) {
        return _buildValueInput(row, def, idx);
    }
 
    /* Build a wrapper that shows a search input + <select> */
    var val        = _esc(row.value || '');
    var displayVal = _esc(row.displayValue || '');
    var cacheKey   = _entryFilterState.reportId + '|' + (def ? def.FieldName : '');
 
    /*
     * Render the shell immediately with a loading placeholder.
     * The <select> options are filled async from the foreign-options endpoint.
     * Hidden input carries the ID value; visible <select> carries the label.
     */
    var html = '<div class="rfr-fk-wrap" style="display:flex;flex-direction:column;gap:2px;width:100%">'
        + '<input type="text" class="rfr-inp rfr-fk-search" placeholder="Search…"'
        +   ' autocomplete="off" value="' + displayVal + '"'
        +   ' style="margin-bottom:2px">'
        + '<select class="rfr-fk-select rfr-value"'
        +   ' data-idx="' + idx + '" data-field="' + _esc(def ? def.FieldName : '') + '"'
        +   ' style="width:100%">'
        + '<option value="">— Loading… —</option>'
        + '</select>'
        + '<input type="hidden" class="rfr-fk-id" value="' + val + '">'
        + '</div>';
 
    /* Async: fill the <select> once options are available */
    setTimeout(function () {
        var tbody = document.getElementById('rpt-entry-filter-tbody');
        if (!tbody) return;
        var tr = tbody.querySelector('tr[data-idx="' + idx + '"]');
        if (!tr) return;
        var sel    = tr.querySelector('select.rfr-fk-select');
        var hidden = tr.querySelector('input.rfr-fk-id');
        var search = tr.querySelector('input.rfr-fk-search');
        if (!sel) return;
 
        function _populate(options) {
            sel.innerHTML = '<option value="">— Select —</option>' +
                options.map(function (o) {
                    var selected = String(o.value) === String(row.value || '') ? ' selected' : '';
                    return '<option value="' + _esc(String(o.value)) + '"' + selected + '>'
                        + _esc(o.label) + '</option>';
                }).join('');
            _pfSelUpgrade(sel);
 
            /* Sync display input to selected label */
            if (row.value && !row.displayValue) {
                var matched = options.find(function (o) { return String(o.value) === String(row.value); });
                if (matched && search) search.value = matched.label;
            }
        }
 
        /* Use cache if available */
        if (_foreignOptionsCache[cacheKey]) {
            _populate(_foreignOptionsCache[cacheKey]);
        } else {
            fetch('/common/filter/foreign-options/?report='
                + encodeURIComponent(_entryFilterState.reportId)
                + '&field=' + encodeURIComponent(def ? def.FieldName : ''))
            .then(function (r) { return r.json(); })
            .then(function (d) {
                var opts = (d.success && d.options) ? d.options : [];
                _foreignOptionsCache[cacheKey] = opts;
                _populate(opts);
            })
            .catch(function () {
                if (sel) sel.innerHTML = '<option value="">— Error loading —</option>';
            });
        }
 
        /* Search input filters the <select> options */
        if (search) {
            search.addEventListener('input', function () {
                var q    = search.value.toLowerCase();
                var opts = _foreignOptionsCache[cacheKey] || [];
                sel.innerHTML = '<option value="">— Select —</option>' +
                    opts.filter(function (o) {
                        return !q || o.label.toLowerCase().indexOf(q) !== -1;
                    }).map(function (o) {
                        return '<option value="' + _esc(String(o.value)) + '">'
                            + _esc(o.label) + '</option>';
                    }).join('');
            });
        }
 
        /* When <select> changes, update the hidden id input + filterRows state */
        sel.addEventListener('change', function () {
            if (hidden) hidden.value = sel.value;
            /* Update display label in search input */
            var opts = _foreignOptionsCache[cacheKey] || [];
            var matched = opts.find(function (o) { return String(o.value) === sel.value; });
            if (search) search.value = matched ? matched.label : '';
            /* Sync into _entryFilterState */
            if (_entryFilterState.filterRows[idx] !== undefined) {
                _entryFilterState.filterRows[idx].value        = sel.value;
                _entryFilterState.filterRows[idx].displayValue = matched ? matched.label : sel.value;
            }
        });
 
    }, 0);
 
    return html;
}


// ── Entry filter: public row callbacks ───────────────────────────────────────
window.rptEntryFilterAddRow = function () {
    _syncEntryFilterRowsFromDom();
    _entryFilterState.filterRows.push({ field: '', value: '', operator: 0 });
    _renderEntryFilterRows();
    setTimeout(function () {
        var tbody = document.getElementById('rpt-entry-filter-tbody'); if (!tbody) return;
        var rows  = tbody.querySelectorAll('tr[data-idx]'); if (!rows.length) return;
        var wrap = rows[rows.length - 1].querySelector('.rfr-td-input .pf-sel-wrap');
        if (wrap) { wrap.click(); } else { var fsel = rows[rows.length - 1].querySelector('select.rfr-field'); if (fsel) fsel.focus(); }
        if (inp) inp.focus();
    }, 30);
};

window.rptEntryFilterDeleteRow = function (idx) {
    _syncEntryFilterRowsFromDom();
    _entryFilterState.filterRows.splice(idx, 1);
    _closeAllAutocomplete();
    _renderEntryFilterRows();
};

window.rptEntryFilterFieldChange = function (idx, sel) {
    _syncEntryFilterRowsFromDom();
    if (_entryFilterState.filterRows[idx]) {
        _entryFilterState.filterRows[idx].field = sel ? sel.value : '';
        _entryFilterState.filterRows[idx].value = '';
    }
    _renderEntryFilterRows();
    setTimeout(function () {
        var tbody = document.getElementById('rpt-entry-filter-tbody'); if (!tbody) return;
        var tr    = tbody.querySelector('tr[data-idx="' + idx + '"]');
        var inp   = tr ? tr.querySelector('input.rfr-value,select.rfr-value') : null;
        if (inp) inp.focus();
    }, 20);
};

// ── Entry filter: public open ─────────────────────────────────────────────────
window.rptOpenEntryFilter = function (reportId, options) {
    _entryFilterModal.open({
        reportId: reportId,
        showMenu: !!(options && options.showMenu),
    });
};



/* ══════════════════════════════════════════════════════════════════════════
   ENTRY FILTER — wire rpt_filter.js into the attendance table
══════════════════════════════════════════════════════════════════════════ */

/* Register a minimal rptGetConfig entry so rpt_filter.js can build field defs */
window._rptConfig = window._rptConfig || {};
window._rptConfig['att-entry'] = {
    cols: [
        { key: 'reg_no',      label: 'Emp ID'      },
        { key: 'emp_name',    label: 'Name'         },
        { key: 'designation', label: 'Designation'  },
        { key: 'department',  label: 'Department'   },
        { key: 'contact',     label: 'Contact'      },
        { key: 'shift_name',  label: 'Shift'        },
    ],
};

/* rptGetState / rptGetConfig expected by rpt_filter.js */
window.rptGetConfig = window.rptGetConfig || function (rid) {
    return (window._rptConfig || {})[rid] || null;
};
window.rptGetState = window.rptGetState || function (rid) {
    return window._rptState ? window._rptState[rid] : null;
};

/* rptApplyModalFilters — called by rpt_filter.js after OK */
window.rptApplyModalFilters = function (reportId, filterRows) {
    if (reportId !== 'att-entry') return;
    /* Re-filter _attAllRows using the filter rows */
    if (!filterRows || !filterRows.length) {
        _attComputeDisplay();
        return;
    }
    var filtered = _attAllRows.filter(function (r) {
        return filterRows.every(function (fr, i) {
            if (!fr.field || fr.value === '') return true;
            var rowVal = String(r[fr.field] || '').toLowerCase();
            var match  = rowVal.indexOf(String(fr.value).toLowerCase()) !== -1;
            /* OR operator: row passes if any OR row matches */
            if (i > 0 && fr.operator === 1) return true;
            return match;
        });
    });
    /* Override display rows directly */
    _attDisplayRows = filtered;
    _attPage = 1;
    document.getElementById('att-count').textContent =
        filtered.length + ' employee' + (filtered.length === 1 ? '' : 's');
    _attRenderPage();
};




    /**
     * Boot a single datepicker state entry — mirrors the init() loop in datepicker.js.
     * Only runs when dpRegister is not exposed by the library.
     */
    function _dpBootPicker(dpid, fieldName, isoValue) {
        /* _dpPickers is window._dpPickers = pickers (set in datepicker.js) */
        var registry = window._dpPickers;
        if (!registry) return;
        var selected = null;
        if (isoValue && /^\d{4}-\d{2}-\d{2}$/.test(isoValue)) {
            var parts = isoValue.split('-').map(Number);
            selected = new Date(parts[0], parts[1] - 1, parts[2]);
        }
        var now = selected || new Date();
        registry[dpid] = { month: now.getMonth(), year: now.getFullYear(), selected: selected };
    }

    /**
     * _dpGetValue(fieldName) — reads the hidden input value (YYYY-MM-DD).
     */
    function _dpGetValue(fieldName) {
        var el = document.getElementById(fieldName);
        return el ? el.value : '';
    }

    window.rptOpenFilterModal = function (reportId) {
        _filterModal.open({ reportId: reportId });
    };

    window.rptCloseFilterModal = function () {
        _closeAllAutocomplete();
        _filterModal.close();
    };

    window.rptFilterAddRow = function () {
        _syncFilterRowsFromDom();
        _filterState.filterRows.push({ field: '', value: '', operator: 0 });
        _renderFilterRows();
        setTimeout(function () {
            var tbody = document.getElementById('rpt-filter-tbody'); if (!tbody) return;
            var rows = tbody.querySelectorAll('tr[data-idx]'); if (!rows.length) return;
            var lastRow = rows[rows.length - 1];
            var wrap = lastRow.querySelector('.rfr-td-input .pf-sel-wrap');
if (wrap) { wrap.click(); } else { var fsel = lastRow.querySelector('select.rfr-field'); if (fsel) fsel.focus(); }
        }, 30);
    };

    window.rptFilterClearAll = function () {
        _filterState.filterRows = []; _closeAllAutocomplete(); _renderFilterRows();
        if (typeof rptApplyModalFilters === 'function') rptApplyModalFilters(_filterState.reportId, []);
    };

    window.rptFilterDeleteRow = function (idx) {
        _syncFilterRowsFromDom(); _filterState.filterRows.splice(idx, 1); _closeAllAutocomplete(); _renderFilterRows();
    };

    function _removeSelectedFilterRow() {
        var tbody = document.getElementById('rpt-filter-tbody'); if (!tbody) return;
        var sel = tbody.querySelector('tr.rfr-selected'); if (!sel) { _toast('Select a row first', 'w'); return; }
        var idx = parseInt(sel.dataset.idx, 10);
        if (!isNaN(idx)) { _syncFilterRowsFromDom(); _filterState.filterRows.splice(idx, 1); }
        _closeAllAutocomplete(); _renderFilterRows();
    }

    function _loadDefaultFilterRows() {
        var defaults = (_filterState.fieldDefs || []).filter(function (d) { return d.Default == 1; });
        _filterState.filterRows = defaults.map(function (d) { return { field: d.FieldName, value: '', operator: parseInt(d.Operator, 10) || 0 }; });
        if (!_filterState.filterRows.length && _filterState.fieldDefs.length) _filterState.filterRows = [{ field: _filterState.fieldDefs[0].FieldName, value: '', operator: 0 }];
        if (!_filterState.filterRows.length) _filterState.filterRows = [{ field: '', value: '', operator: 0 }];
        _renderFilterRows();
    }

    function _collectHeaderVals() {
        // var extra = _reportExtraFields[_filterState.reportId] || {};
        var extra = _reportExtraFields[_filterState.reportId] || (window._reportExtraFields && window._reportExtraFields[_filterState.reportId]) || {};
        var deptVal = _getVal('rptf-dept-project'), deptLabel = '';
        var deptSel = document.getElementById('rptf-dept-project');
        if (deptSel) { for (var i = 0; i < deptSel.options.length; i++) { if (deptSel.options[i].value === deptVal) { deptLabel = deptSel.options[i].text; break; } } }
        _filterState.headerVals = {
            reportStyle: _getVal('rptf-report-style'), deptProject: deptVal, deptProjectLabel: deptLabel,
            dateFrom: _dpGetValue('rptf_date_from'), dateTo: _dpGetValue('rptf_date_to'),
            type: extra.showType ? _getVal('rptf-type') : '',
            status: extra.showStatus ? _getVal('rptf-status') : '',
        };
    }

    function _applyFilter() {
        _syncFilterRowsFromDom(); _collectHeaderVals(); _closeAllAutocomplete();
        var styleName = _filterState.headerVals.reportStyle;
        if (styleName) {
            var cfg = window.rptGetConfig ? window.rptGetConfig(_filterState.reportId) : null;
            var mrName = (_reportExtraFields[_filterState.reportId] || {}).mrName || (cfg && cfg.mrName) || '';
            _loadStyleAndApply(styleName, _filterState.reportId, mrName, function () { _doApplyFilter(); });
        } else {
            _doApplyFilter();
        }
    }

    function _doApplyFilter() {
        _logToTerminal(_filterState.reportId, _filterState.headerVals, _filterState.filterRows);
        var fkCols = (_optState.cols || []).filter(function (c) { return c.fieldType === 'fk' && c.fkTable && c.fkField; }).map(function (c) { return { key: c.key, fkTable: c.fkTable, fkIdField: c.fkIdField || '', fkField: c.fkField }; });
        if (typeof window.rptApplyReportFilter === 'function') {
            window.rptApplyReportFilter(_filterState.reportId, { header: _filterState.headerVals, rows: _filterState.filterRows, fkCols: fkCols });
        } else {
            if (typeof rptApplyModalFilters === 'function') rptApplyModalFilters(_filterState.reportId, _filterState.filterRows);
        }
        // var pgToolbar = document.getElementById('pf-toolbar-' + _filterState.reportId);
        // if (pgToolbar) pgToolbar.style.display = 'flex';
        rptCloseFilterModal();
    }

    function _applyColsToRptConfig(reportId, allCols) {
        var cfg = window._rptConfig && window._rptConfig[reportId];
        if (!cfg) return;
        var visCols = allCols
            .filter(function (c) { return c.show !== false; })
            .map(function (c) {
                return {
                    key: _toSnakeCase(c.key) || c.key,
                    label: c.label,
                    show: true,
                    total: !!c.total,
                    wrap: !!c.wrap,
                    format: c.format || '',
                    bold: !!c.bold,
                    color: c.color || '',
                    textColor: c.textColor || '',
                    fkTable: c.fkTable || '',
                    fkField: c.fkField || '',
                    fieldType: c.fieldType || 'text',
                    type: c.type || 'text',
                };
            });
        cfg.cols = visCols;
        var theadCols = cfg.cols.filter(function (c) { return c.type !== 'photo'; });
        var listThead = document.querySelector('#rpt-list-tbl-' + reportId + ' thead');
        if (listThead) {
            listThead.innerHTML = '<tr>' +
                theadCols.map(function (c) {
                    return '<th data-col="' + _esc(c.key) + '" style="cursor:pointer">' + _esc(c.label) + '</th>';
                }).join('') +
                '<th style="width:60px"></th></tr>';
        }
        var gridThead = document.querySelector('#rpt-grid-tbl-' + reportId + ' thead');
        if (gridThead) {
            gridThead.innerHTML = '<tr>' +
                '<th style="width:44px"></th>' +
                theadCols.map(function (c) {
                    return '<th data-col="' + _esc(c.key) + '" style="cursor:pointer">' + _esc(c.label) + '</th>';
                }).join('') +
                '<th style="width:60px"></th></tr>';
        }
        if (typeof window.rptGoPage === 'function') {
            var st = window.rptGetState ? window.rptGetState(reportId) : null;
            if (st) window.rptGoPage(reportId, st.currentPage || 1);
        }
    }

    function _loadStyleAndApply(styleName, reportId, mrName, cb) {
        fetch('/common/report/load-style/?report_name=' + encodeURIComponent(styleName) +
            '&mr_name=' + encodeURIComponent(mrName))
            .then(function (r) { return r.json(); })
            .then(function (d) {
                if (d.success && d.cols && d.cols.length) {
                    var normCols = d.cols.map(function (c) {
                        return Object.assign({}, c, {
                            key: _toSnakeCase(c.key) || c.key,
                            textColor: c.textColor || c.TextColor || '',
                        });
                    });
                    _optState.reportId = reportId;
                    _optState.cols = normCols;
                    _reportViewState.cols = JSON.parse(JSON.stringify(normCols));
                    _applyColsToRptConfig(reportId, normCols);
                    _renderReportTable(reportId);
                    window.dispatchEvent(new CustomEvent('rpt:colsChanged', {
                        detail: { reportId: reportId, cols: JSON.parse(JSON.stringify(normCols)) }
                    }));
                }
                if (typeof cb === 'function') cb();
            })
            .catch(function () { if (typeof cb === 'function') cb(); });
    }

    function _loadFieldDefs(reportId, cb) {
        var cfg = window.rptGetConfig ? window.rptGetConfig(reportId) : null;
        var url = (cfg && cfg.filterLoadUrl) ? cfg.filterLoadUrl : '/common/filter/load/';
        fetch(url + '?report=' + encodeURIComponent(reportId))
            .then(function (r) { return r.json(); })
            .then(function (d) {
                _filterState.fieldDefs = (d.success && d.filters && d.filters.length) ? d.filters : _colsToFieldDefs(reportId);
                _filterState.loaded = true; if (typeof cb === 'function') cb();
            })
            .catch(function () { _filterState.fieldDefs = _colsToFieldDefs(reportId); _filterState.loaded = true; if (typeof cb === 'function') cb(); });
    }

    function _colsToFieldDefs(reportId) {
        var cfg = window.rptGetConfig ? window.rptGetConfig(reportId) : null;
        return (cfg && cfg.cols ? cfg.cols : []).map(function (c) {
            return { FieldName: c.key, DisplayName: c.label, FieldType: 1, FilterSql: '', ColWidth: '', IDField: '', Default: 0, Operator: 0 };
        });
    }

    function _renderFilterRows() {
        var tbody = document.getElementById('rpt-filter-tbody'); if (!tbody) return;
        var defs = _filterState.fieldDefs || [];
        if (!_filterState.filterRows.length) _filterState.filterRows = [{ field: '', value: '', operator: 0 }];
        var rows = _filterState.filterRows;
        tbody.innerHTML = rows.map(function (row, i) {
            var fieldOpts = '<option value="">-- Field --</option>' + defs.map(function (d) { var sel = d.FieldName === row.field ? ' selected' : ''; return '<option value="' + _esc(d.FieldName) + '"' + sel + '>' + _esc(d.DisplayName || d.FieldName) + '</option>'; }).join('');
            var def = defs.find(function (d) { return d.FieldName === row.field; }) || null;
            var opSel = (i === 0) ? '<span style="font-size:11px;color:var(--color-text-tertiary,#888);padding:0 4px">—</span>' : '<select class="rfr-op rfr-sel"><option value="0"' + (row.operator === 0 ? ' selected' : '') + '>AND</option><option value="1"' + (row.operator === 1 ? ' selected' : '') + '>OR</option></select>';
            var delBtn = '<button class="rfr-del-btn" type="button" onclick="event.stopPropagation();rptFilterDeleteRow(' + i + ')" title="Delete row">✕</button>';
            return '<tr data-idx="' + i + '" style="cursor:pointer;border-bottom:1px solid var(--color-border-light,#eee)">' +
                '<td style="padding:5px 8px;text-align:center;color:var(--color-text-tertiary,#aaa);font-size:11px" onclick="rptFilterRowSelect(this.parentNode)">' + (i + 1) + '</td>' +
                '<td class="rfr-td-input" onclick="event.stopPropagation();rptFilterRowSelect(this.parentNode)"><select class="rfr-field rfr-sel" onchange="rptFilterFieldChange(' + i + ',this)">' + fieldOpts + '</select></td>' +
                '<td class="rfr-td-input" onclick="event.stopPropagation();rptFilterRowSelect(this.parentNode)" id="rfr-val-td-' + i + '">' + _buildValueInput(row, def, i) + '</td>' +
                '<td style="padding:4px 8px" onclick="event.stopPropagation();rptFilterRowSelect(this.parentNode)">' + opSel + '</td>' +
                '<td style="padding:4px 6px;text-align:center" onclick="event.stopPropagation()">' + delBtn + '</td>' +
                '</tr>';
        }).join('');
        var tblWrap = document.getElementById('rpt-filter-tbody');
        if (tblWrap) {
            _pfSelUpgradeAll(tblWrap);
            /* boot any dp pickers injected into date rows */
            tblWrap.querySelectorAll('input[id^="rfr_date_"]').forEach(function (inp) {
                var fn = inp.id;                   // e.g. rfr_date_2
                var dpid = 'dp_' + fn;               // e.g. dp_rfr_date_2
                _dpBootPicker(dpid, fn, inp.value || '');
            });
        }
        _attachAutocompleteListeners();
    }

    function _attachAutocompleteListeners() {
        var tbody = document.getElementById('rpt-filter-tbody'); if (!tbody) return;
        tbody.querySelectorAll('tr[data-idx]').forEach(function (tr) {
            var idx = parseInt(tr.dataset.idx, 10);
            var displayInp = tr.querySelector('input.rfr-display');
            var hiddenInp = tr.querySelector('input.rfr-value');
            var isFK = !!displayInp;
            var inp = displayInp || hiddenInp;
            if (!inp) return;
            function _openAC() {
                var row = _filterState.filterRows[idx]; var fieldName = row ? row.field : '';
                var def = (_filterState.fieldDefs || []).find(function (d) { return d.FieldName === fieldName; });
                var ft = def ? parseInt(def.FieldType, 10) : 1;
                if (isFK && ft === 3 && def && (def.FilterSql || '').trim() && (def.IDField || '').trim()) {
                    _fetchForeignOptions(def, function (opts) { _buildFKAutocomplete(inp, hiddenInp, opts, idx); });
                } else {
                    _buildAutocomplete(inp, _getFieldValues(_filterState.reportId, fieldName), idx);
                }
            }
            inp.addEventListener('focus', _openAC);
            inp.addEventListener('input', function () { _openAC(); if (!isFK && _filterState.filterRows[idx] !== undefined) _filterState.filterRows[idx].value = inp.value; });
            inp.addEventListener('keydown', function (e) {
                var ac = document.getElementById('rfr-ac-' + idx);
if (!ac) { if (e.key === 'Enter') { e.preventDefault(); if (inp.value.trim()) rptFilterAddRow(); } return; }
                var items = ac.querySelectorAll('.rfr-ac-item'); var active = ac.querySelector('.rfr-ac-active'); var activeIdx = -1;
                items.forEach(function (it, i) { if (it === active) activeIdx = i; });
                if (e.key === 'ArrowDown') { e.preventDefault(); var next = activeIdx < items.length - 1 ? activeIdx + 1 : 0; items.forEach(function (it) { it.classList.remove('rfr-ac-active'); }); items[next].classList.add('rfr-ac-active'); items[next].scrollIntoView({ block: 'nearest' }); }
                else if (e.key === 'ArrowUp') { e.preventDefault(); var prev = activeIdx > 0 ? activeIdx - 1 : items.length - 1; items.forEach(function (it) { it.classList.remove('rfr-ac-active'); }); items[prev].classList.add('rfr-ac-active'); items[prev].scrollIntoView({ block: 'nearest' }); }
else if (e.key === 'Enter') { e.preventDefault(); if (active) { active.dispatchEvent(new MouseEvent('mousedown', { bubbles: true })); } else { _closeAllAutocomplete(); if (inp.value.trim()) rptFilterAddRow(); } }
                else if (e.key === 'Escape') { _closeAllAutocomplete(); }
            });
        });
    }

    function _buildValueInput(row, def, idx) {
        var ft = def ? parseInt(def.FieldType, 10) : 1;
        var val = _esc(row.value || ''); var displayVal = _esc(row.displayValue || '');
        var ev = 'rptFilterRowChanged(' + idx + ')';
        if (ft === 6) {
            /* render the full datepicker markup inline; value read from hidden input */
            var dpFN = 'rfr_date_' + idx;
            var dpId = 'dp_' + dpFN;
            var disp = '';
            var rawV = row ? (row.value || '') : '';
            if (rawV && /^\d{4}-\d{2}-\d{2}$/.test(rawV)) {
                var pp = rawV.split('-'); disp = pp[2] + '-' + pp[1] + '-' + pp[0];
            }
            return [
                '<input type="hidden" id="' + dpFN + '" name="' + dpFN + '" value="' + _esc(rawV) + '">',
                '<div class="dp-input-wrap" id="' + dpId + '_wrap" onclick="dpToggle(\'' + dpId + '\', event)">',
                '<span class="dp-display' + (rawV ? ' has-value' : '') + '" id="' + dpId + '_display">' + (disp || 'Choose Date') + '</span>',
                '<svg class="dp-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">',
                '<rect x="3" y="4" width="18" height="18" rx="3"/>',
                '<path d="M16 2v4M8 2v4M3 10h18"/>',
                '<path d="M8 14h.01M12 14h.01M16 14h.01M8 18h.01M12 18h.01" stroke-linecap="round"/>',
                '</svg></div>',
                '<div class="dp-calendar" id="' + dpId + '_cal"></div>',
            ].join('');
        }
        if (ft === 7) return '<input type="time" class="rfr-inp rfr-value" value="' + val + '" onchange="' + ev + '">';
        if (ft === 2) return '<input type="number" class="rfr-inp rfr-value" value="' + val + '" onchange="' + ev + '">';
        if (ft === 3) return '<input type="text" class="rfr-inp rfr-display" value="' + displayVal + '" placeholder="Type to search…" autocomplete="off"><input type="hidden" class="rfr-value" value="' + val + '">';
        return '<input type="text" class="rfr-inp rfr-value" value="' + val + '" placeholder="Type to search…" oninput="' + ev + '" autocomplete="off">';
    }

    window.rptFilterRowSelect = function (tr) {
        var tbody = document.getElementById('rpt-filter-tbody');
        if (tbody) tbody.querySelectorAll('tr').forEach(function (r) { r.classList.remove('rfr-selected'); });
        if (tr) tr.classList.add('rfr-selected');
    };
    window.rptFilterFieldChange = function (idx, sel) {
        _syncFilterRowsFromDom();
        if (_filterState.filterRows[idx]) { _filterState.filterRows[idx].field = sel ? sel.value : ''; _filterState.filterRows[idx].value = ''; }
        _renderFilterRows();
        setTimeout(function () {
            var tbody = document.getElementById('rpt-filter-tbody'); if (!tbody) return;
            var tr = tbody.querySelector('tr[data-idx="' + idx + '"]');
            var inp = tr ? tr.querySelector('input.rfr-value,select.rfr-value') : null;
            if (inp) inp.focus();
        }, 20);
    };
    window.rptFilterRowChanged = function (idx) {
        var tbody = document.getElementById('rpt-filter-tbody'); if (!tbody) return;
        var tr = tbody.querySelector('tr[data-idx="' + idx + '"]'); if (!tr) return;
        var inp = tr.querySelector('input.rfr-value,select.rfr-value');
        if (inp && _filterState.filterRows[idx] !== undefined) _filterState.filterRows[idx].value = inp.value;
    };

    function _syncFilterRowsFromDom() {
        var tbody = document.getElementById('rpt-filter-tbody'); if (!tbody) return;
        tbody.querySelectorAll('tr[data-idx]').forEach(function (tr) {
            var i = parseInt(tr.dataset.idx, 10);
            var sel        = tr.querySelector('select.rfr-field');
        var hiddenInp  = tr.querySelector('input.rfr-value');
        var fkIdInp    = tr.querySelector('input.rfr-fk-id');     /* ← NEW: FK select hidden id */
        var fkSel      = tr.querySelector('select.rfr-fk-select'); /* ← NEW: FK visible select  */
        var fkSearch   = tr.querySelector('input.rfr-fk-search');  /* ← NEW: FK search input    */
        var displayInp = tr.querySelector('input.rfr-display');
        var op         = tr.querySelector('select.rfr-op');
        if (_entryFilterState.filterRows[i] === undefined) return;
        _entryFilterState.filterRows[i].field    = sel ? sel.value : '';
        _entryFilterState.filterRows[i].operator = op  ? parseInt(op.value, 10) : 0;
        var def = (_entryFilterState.fieldDefs || []).find(function (d) {
            return d.FieldName === _entryFilterState.filterRows[i].field;
        });
        var ft = def ? parseInt(def.FieldType, 10) : 1;
        if (ft === 6) {
            var dateHidden = document.getElementById('rfr_date_' + i);
            _entryFilterState.filterRows[i].value = dateHidden ? dateHidden.value : '';
        } else if (ft === 3 && fkIdInp) {
            /* FK select: value = ID from hidden input, displayValue = label from search */
            _entryFilterState.filterRows[i].value        = fkIdInp.value;
            _entryFilterState.filterRows[i].displayValue = fkSearch ? fkSearch.value : '';
        } else if (hiddenInp) {
            _entryFilterState.filterRows[i].value = hiddenInp.value;
            if (displayInp) _entryFilterState.filterRows[i].displayValue = displayInp.value;
        }
        });
    }

    function _toggleFilterMenu() {
        var menu = document.getElementById('rpt-filter-menu');
        if (!menu) return;
        if (menu.style.display !== 'none') { menu.style.display = 'none'; return; }

        var bd = document.getElementById('rptf-filter-bd');
        var btn = null;
        if (bd) {
            bd.querySelectorAll('button').forEach(function (b) {
                if ((b.textContent || '').trim() === 'Menu') btn = b;
            });
        }
        if (btn) {
            var rect = btn.getBoundingClientRect();
            menu.style.top = (rect.bottom + 4) + 'px';
            menu.style.left = rect.left + 'px';
        }
        menu.style.zIndex = '10001';   // ← ensure it's set at open time too
        menu.style.display = 'block';
        setTimeout(function () {
            document.addEventListener('click', function _cm(e) {
                if (!menu.contains(e.target)) {
                    menu.style.display = 'none';
                    document.removeEventListener('click', _cm);
                }
            });
        }, 10);
    }

    /* ═════════════════════════════════════════════════════════════════
       2. REPORT VIEW (overlay)
    ═════════════════════════════════════════════════════════════════ */
    var _reportViewState = { reportId: '', allRows: [], cols: [], filteredRows: [] };

    window.rptShowReportView = function (reportId, rows, cols) {
        _reportViewState.reportId = reportId; _reportViewState.allRows = rows || []; _reportViewState.filteredRows = rows || [];
        if (!cols) { var cfg = window.rptGetConfig ? window.rptGetConfig(reportId) : null; cols = (cfg && cfg.cols) ? cfg.cols.map(function (c, i) { return { key: c.key, label: c.label, show: true, total: false, wrap: false, format: '', color: '', col: i + 1 }; }) : []; }
        _reportViewState.cols = cols;
        _optState.reportId = reportId;
        if (!_optState.cols.length || _optState.reportId !== reportId) _optState.cols = JSON.parse(JSON.stringify(cols));
        var containerId = 'rpt-report-view-' + reportId;
        var container = document.getElementById(containerId);
        if (!container) { container = document.createElement('div'); container.id = containerId; container.style.cssText = 'position:fixed;inset:0;z-index:900;background:var(--color-bg,#f5f5f5)'; document.body.appendChild(container); }
        container.innerHTML = _buildReportViewHtml(reportId);
        _renderReportTable(reportId);
    };

    window.rptCloseReportView = function (reportId) {
        var el = document.getElementById('rpt-report-view-' + (reportId || _reportViewState.reportId));
        if (el) el.remove();
    };

    function _buildReportViewHtml(reportId) {
        var icons = { Close: 'M18 6L6 18 M6 6L18 18', Save: 'M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z M17 21V13H7V21 M7 3V8H15', Print: 'M6 9L6 2L18 2L18 9 M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2 M6 14H18V22H6Z', Default: 'M23 4L23 10L17 10 M1 20L1 14L7 14 M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15', Total: 'M18 20L18 10 M12 20L12 4 M6 20L6 14', Options: 'M12 20h9 M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z', Refresh: 'M23 4L23 10L17 10 M1 20L1 14L7 14 M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15', Menu: 'M3 12L21 12 M3 6L21 6 M3 18L21 18' };
        function tbBtn(label, onclick) { return '<button class="rpt-tb-btn" onclick="' + onclick + '"><svg viewBox="0 0 24 24"><path d="' + (icons[label] || icons.Menu) + '"/></svg>' + label + '</button>'; }
        return ['<div class="rpt-report-page">', '<div class="rpt-report-toolbar">', tbBtn('Close', 'rptCloseReportView("' + reportId + '")'), tbBtn('Save', 'rptReportSave("' + reportId + '")'), '<div class="rpt-tb-sep"></div>', tbBtn('Print', 'rptReportPrint("' + reportId + '")'), tbBtn('Default', 'rptReportDefault("' + reportId + '")'), tbBtn('Total', 'rptReportTotal("' + reportId + '")'), tbBtn('Options', 'rptOpenReportOptions("' + reportId + '")'), '<div class="rpt-tb-sep"></div>', tbBtn('Refresh', 'rptReportRefresh("' + reportId + '")'), '<button class="rpt-tb-menu-arrow" onclick="rptReportMenu(this,\'' + reportId + '\')">▼</button>', '</div>', '<div class="rpt-report-body" id="rpt-report-body-' + reportId + '">', '<table class="rpt-report-tbl" id="rpt-report-tbl-' + reportId + '">', '<thead id="rpt-report-thead-' + reportId + '"></thead>', '<tbody id="rpt-report-tbody-' + reportId + '"></tbody>', '</table></div></div>'].join('');
    }

    var _reportSortCol = {};
    var _reportSortDir = {};

    function _renderReportTable(reportId) {
        var cols = (_optState.reportId === reportId && _optState.cols.length)
            ? _optState.cols.filter(function (c) { return c.show !== false; })
            : _reportViewState.cols.filter(function (c) { return c.show !== false; });
        var rows = _reportViewState.filteredRows.slice(); /* shallow copy for sort */

        /* ── Sort ── */
        var sCol = _reportSortCol[reportId];
        var sDir = _reportSortDir[reportId] || 'asc';
        if (sCol) {
            rows.sort(function (a, b) {
                var av = String(a[sCol] || '').toLowerCase();
                var bv = String(b[sCol] || '').toLowerCase();
                return (av < bv ? -1 : av > bv ? 1 : 0) * (sDir === 'asc' ? 1 : -1);
            });
        }

        /* ── Group by ── */
        var rptSt2    = window.rptGetState ? window.rptGetState(reportId) : null;
        var groupKeys2 = (rptSt2 && rptSt2.groupKeys && rptSt2.groupKeys.length)
            ? rptSt2.groupKeys
            : (rptSt2 && rptSt2.groupKey ? [rptSt2.groupKey] : []);
 
        /* Sort by composite group keys first */
        if (groupKeys2.length) {
            rows.sort(function (a, b) {
                for (var ki = 0; ki < groupKeys2.length; ki++) {
                    var k  = groupKeys2[ki];
                    var av = String(a[k] !== undefined && a[k] !== null ? a[k] : '').toLowerCase();
                    var bv = String(b[k] !== undefined && b[k] !== null ? b[k] : '').toLowerCase();
                    if (av < bv) return -1;
                    if (av > bv) return  1;
                }
                return 0;
            });
        }
 

        var thead = document.getElementById('rpt-report-thead-' + reportId);
        var tbody = document.getElementById('rpt-report-tbody-' + reportId);
        if (!thead || !tbody) return;

        /* thead with sort arrows */
        thead.innerHTML = '<tr><th class="rpt-report-sn" style="cursor:default">SINo</th>' +
            cols.map(function (c) {
                var arrow = '';
                if (sCol === c.key) arrow = sDir === 'asc' ? ' ▲' : ' ▼';
                return '<th data-col="' + _esc(c.key) + '" style="cursor:pointer;user-select:none">' +
                    _esc(c.label) + '<span style="font-size:10px;opacity:0.7">' + arrow + '</span></th>';
            }).join('') + '</tr>';

        /* bind sort click once per render */
        thead.onclick = function (e) {
            var th = e.target.closest('th[data-col]');
            if (!th) return;
            var col = th.dataset.col;
            _reportSortDir[reportId] = (_reportSortCol[reportId] === col && _reportSortDir[reportId] === 'asc') ? 'desc' : 'asc';
            _reportSortCol[reportId] = col;
            _renderReportTable(reportId);
        };

        if (!rows.length) {
            tbody.innerHTML = '<tr><td colspan="' + (cols.length + 1) +
                '" style="text-align:center;padding:24px;color:var(--color-text-tertiary,#aaa);font-size:13px">' +
                'No records found</td></tr>';
            return;
        }

        var html = '';
        var lastGroupVal = undefined;
        var sn = 0;

        rows.forEach(function (row) {
            /* ── group header ── */
            if (groupKey) {
                var gv = row[groupKey];
                if (gv === undefined || gv === null) gv = row[_toSnakeCase(groupKey)];
                if (gv === undefined || gv === null) gv = '';
                gv = String(gv);
                if (gv !== lastGroupVal) {
                    lastGroupVal = gv;
                    var groupLabel = '';
                    var groupCol = cols.find(function (c) { return c.key === groupKey; });
                    if (groupCol) groupLabel = groupCol.label + ': ';
                    html += '<tr style="background:var(--color-primary);color:--color-text-white">' +
                        '<td colspan="' + (cols.length + 1) + '" ' +
                        'style="padding:5px 10px;font-weight:700;font-size:12px;letter-spacing:0.3px">' +
                        _esc(groupLabel) + _esc(gv || '—') + '</td></tr>';
                }
            }

            sn++;
            html += '<tr><td class="rpt-report-sn" style="padding:6px 10px;text-align:center;' +
                'color:var(--color-text-tertiary,#999)">' + sn + '</td>' +
                cols.map(function (c) {
                    var v = row[c.key];
                    if (v === undefined || v === null) v = row[_toSnakeCase(c.key)];
                    if ((v === undefined || v === null) && c.key.indexOf('.') !== -1) {
                        var bare = c.key.split('.').pop();
                        v = row[bare] !== undefined ? row[bare] : row[_toSnakeCase(bare)];
                    }
                    if (v === undefined || v === null) v = '';
                    var style = 'padding:6px 10px' +
                        (c.wrap ? ';white-space:normal' : '') +
                        (c.bold ? ';font-weight:600' : '') +
                        (c.color ? ';background:' + c.color : '') +
                        (c.textColor ? ';color:' + c.textColor : '');
                    return '<td style="' + style + '">' + _esc(String(v)) + '</td>';
                }).join('') + '</tr>';
        });

        tbody.innerHTML = html;
    }

    window.rptReportSave = function (rid) {
        var cfg = window.rptGetConfig ? window.rptGetConfig(rid) : null;
        var extra = _reportExtraFields[rid] || {};
        var mrName = extra.mrName || (cfg && cfg.mrName) || '';
        _srModal.open({ reportId: rid, mrName: mrName });
    };

    window.rptReportPrint = function (rid) {
        if (typeof window.rptPrintReport === 'function') {
            window.rptPrintReport(rid);
        } else {
            window.print();
        }
    };
    window.rptReportDefault = function (rid) { _toast('Default settings applied', 's'); };
    window.rptReportTotal = function (rid) {
        var st = _reportViewState;
        var cols = (_optState.reportId === rid ? _optState.cols : st.cols).filter(function (c) { return c.show !== false && c.total; });
        if (!cols.length) { _toast('Mark columns as Total in Report Options first', 'w'); return; }
        var tbody = document.getElementById('rpt-report-tbody-' + rid); if (!tbody) return;
        var existing = tbody.querySelector('.rpt-total-row'); if (existing) { existing.remove(); return; }
        var allCols = (_optState.reportId === rid ? _optState.cols : st.cols).filter(function (c) { return c.show !== false; });
        var totalRow = '<tr class="rpt-total-row" style="font-weight:700;background:var(--color-primary-light,rgba(139,0,0,.08))"><td style="padding:6px 10px;text-align:center">Total</td>' + allCols.map(function (c) { if (!c.total) return '<td style="padding:6px 10px"></td>'; var sum = st.filteredRows.reduce(function (acc, row) { return acc + (parseFloat(row[c.key]) || 0); }, 0); return '<td style="padding:6px 10px;text-align:right">' + sum.toLocaleString() + '</td>'; }).join('') + '</tr>';
        tbody.insertAdjacentHTML('beforeend', totalRow);
    };
    window.rptReportRefresh = function (rid) { _renderReportTable(rid); _toast('Refreshed', 's'); };
    window.rptReportMenu = function (btn, rid) {
        window.pfOpenMenu && window.pfOpenMenu(btn, [
            { icon: 'Save', label: 'Save Report', fn: function () { rptReportSave(rid); } },
            { icon: 'Print', label: 'Print', fn: function () { rptReportPrint(rid); } },
            { sep: true },
            { icon: 'Filter', label: 'Filter', fn: function () { rptOpenFilterModal(rid); } },
        ]);
    };

    window.rptApplyReportFilter = function (reportId, params) {
        var rows = _reportViewState.allRows; var header = (params && params.header) || {}; var filterRows = (params && params.rows) || [];
        // var pgToolbar = document.getElementById('pf-toolbar-' + reportId); if (pgToolbar) pgToolbar.style.display = 'flex';
        if (header.type) { rows = rows.filter(function (r) { if (header.type === 'id_expiry') return r.rp_expiry; if (header.type === 'passport_expiry') return r.passport_expiry; if (header.type === 'medical_expiry') return r.medical_expiry; return true; }); }
        if (header.status) { rows = rows.filter(function (r) { var active = String(r.active || '').toLowerCase(); if (header.status === 'active') return active === 'active'; if (header.status === 'expired') return active !== 'active'; return true; }); }
        if (header.deptProject) { rows = rows.filter(function (r) { return String(r.department_id || '') === String(header.deptProject); }); }
        filterRows.forEach(function (fr, i) {
            if (!fr.field || (fr.value === '' && fr.value !== 0)) return;
            var fieldKey = fr.field.replace(/^[A-Za-z_]+\./, '').toLowerCase();
            var searchVal = String((fr.displayValue && fr.displayValue !== '') ? fr.displayValue : fr.value).toLowerCase();
            var filtered = rows.filter(function (r) { return String(r[fieldKey] || '').toLowerCase().indexOf(searchVal) !== -1; });
            if (i === 0 || fr.operator === 0) { rows = filtered; } else { rows = rows.concat(filtered.filter(function (r) { return rows.indexOf(r) === -1; })); }
        });
        _reportViewState.filteredRows = rows; _renderReportTable(reportId);
    };

    /* ═════════════════════════════════════════════════════════════════
       3. REPORT OPTIONS MODAL
    ═════════════════════════════════════════════════════════════════ */
    var _optModal = new UtilityModal({
        id: 'rpt-opt-modal', title: 'Report Options',
        icon: 'M12 20h9 M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z',
        tabs: [{ id: 'opts', label: '» Fields', icon: 'doc' }],
        toolbar: [
            { label: 'OK', icon: 'save', danger: false, onclick: function () { _optApply(); } },
            { label: 'Cancel', icon: 'close', danger: false, onclick: function () { _optModal.close(); } },
            { label: 'Add', icon: 'doc', danger: false, onclick: function () { rptEditReportField(null); } },
            { label: 'Edit', icon: 'doc', danger: false, onclick: function () { _optEdit(); } },
            { label: 'Delete', icon: 'del', danger: true, onclick: function () { _optDelete(); } },
            { label: 'Reset', icon: 'refresh', danger: false, onclick: function () { _optReset(); } },
        ],
        onBuild: function (modal) {
            var nav = document.getElementById('rpt-opt-modal-nav');
            if (nav) nav.style.cssText = 'display:none!important;width:0;overflow:hidden';
            var pane = modal.pane('opts'); if (!pane) return;
            pane.style.overflow = 'hidden'; pane.style.flexDirection = 'column'; pane.style.padding = '12px';
            var gfRow = document.createElement('div');
            gfRow.style.cssText = 'display:flex;align-items:center;gap:8px;margin-bottom:10px;flex-shrink:0';
            gfRow.innerHTML = '<span style="font-size:11.5px;color:var(--color-text-secondary,#666);width:120px;text-align:right;flex-shrink:0">Group Field Name</span><select id="rpt-opt-group-field" data-multi-check="1" data-no-upgrade="0" style="min-width:220px"></select>';
            pane.appendChild(gfRow);
            var layout = document.createElement('div'); layout.className = 'ropt-layout';
            var gridWrap = document.createElement('div'); gridWrap.className = 'ropt-grid-wrap';
            /* ── Color column added to thead ── */
            gridWrap.innerHTML = '<table class="ropt-grid"><thead><tr>' +
                '<th style="width:40px">Show</th><th>Display Name</th>' +
                '<th style="width:60px">Total</th><th style="width:60px">Wrap</th>' +
                '<th style="width:80px">Format</th>' +
                '<th style="width:44px">BG</th>' +
                '<th style="width:44px">FG</th>' +
                '<th style="width:50px">Col</th>' +
                '</tr></thead><tbody id="rpt-opt-tbody"></tbody></table>';
            layout.appendChild(gridWrap);
            var arrowPanel = document.createElement('div'); arrowPanel.className = 'ropt-arrow-panel';
            arrowPanel.innerHTML = '<button class="ropt-arrow-btn" id="ropt-btn-up" title="Move up"><svg viewBox="0 0 24 24"><polyline points="18 15 12 9 6 15"/></svg></button><button class="ropt-arrow-btn" id="ropt-btn-down" title="Move down"><svg viewBox="0 0 24 24"><polyline points="6 9 12 15 18 9"/></svg></button>';
            layout.appendChild(arrowPanel); pane.appendChild(layout);
            setTimeout(function () {
                var btnUp = document.getElementById('ropt-btn-up'); var btnDown = document.getElementById('ropt-btn-down');
                if (btnUp) btnUp.addEventListener('click', function () { rptOptFieldUp(); });
                if (btnDown) btnDown.addEventListener('click', function () { rptOptFieldDown(); });
                _pfSelUpgradeAll(pane);
            }, 0);
        },
        onOpen: function (modal, ctx) {
            _optState.reportId = ctx.reportId || _reportViewState.reportId;
            _optState.selected = null;
            var liveCfg = window._rptConfig && window._rptConfig[_optState.reportId];
            var prevCols = (_reportViewState.reportId === _optState.reportId && _reportViewState.cols.length)
                ? _reportViewState.cols : [];
            if (prevCols.length) {
                var prevMap = {};
                prevCols.forEach(function (c) { prevMap[c.key] = c; });
                _optState.cols = prevCols.map(function (c, i) {
                    var live = liveCfg && liveCfg.cols ? liveCfg.cols.find(function (lc) { return lc.key === c.key; }) : null;
                    return {
                        key: c.key,
                        label: (live && live.label) || c.label,
                        show: c.show !== false,
                        total: !!c.total,
                        wrap: !!c.wrap,
                        format: c.format || '',
                        color: c.color || (live && live.color) || '',
                        fkTable: c.fkTable || (live && live.fkTable) || '',
                        fkField: c.fkField || (live && live.fkField) || '',
                        fkIdField: c.fkIdField || (live && live.fkIdField) || '',
                        fieldType: c.fieldType || (live && live.fieldType) || 'text',
                        col: i + 1,
                        bold: !!(live && live.bold),
                        type: (live && live.type) || c.type || 'text',
                    };
                });
                if (liveCfg && liveCfg.cols) {
                    liveCfg.cols.forEach(function (lc) {
                        if (!prevMap[lc.key]) {
                            _optState.cols.push({
                                key: lc.key, label: lc.label, show: true,
                                total: false, wrap: false, format: '',
                                color: lc.color || '', fkTable: lc.fkTable || '',
                                fkField: lc.fkField || '', fieldType: lc.fieldType || 'text',
                                fkIdField: c.fkIdField || (live && live.fkIdField) || '',
                                col: _optState.cols.length + 1, bold: !!lc.bold, type: lc.type || 'text',
                            });
                        }
                    });
                }
            } else if (liveCfg && liveCfg.cols && liveCfg.cols.length) {
                _optState.cols = liveCfg.cols.map(function (c, i) {
                    return { key: c.key, label: c.label, show: true, total: false, wrap: false, format: '', color: c.color || '', fkTable: c.fkTable || '', fkField: c.fkField || '', fieldType: c.fieldType || 'text', col: i + 1, bold: !!c.bold, type: c.type || 'text' };
                });
            } else {
                _optState.cols = [];
            }
           /* snapshot original cols for Reset */
            var _cfgSnap = window._rptConfig && window._rptConfig[_optState.reportId];
            if (_cfgSnap && !_cfgSnap._originalCols) {
                _cfgSnap._originalCols = JSON.parse(JSON.stringify(_optState.cols));
            }
            _optRenderGrid();
            _optPopulateGroupField();
            setTimeout(function () {
                var pane = _optModal.pane('opts');
                if (pane) _pfSelUpgradeAll(pane);
            }, 0);
        },
    });

    window.rptOpenReportOptions = function (reportId) {
        _optModal.open({ reportId: reportId });
    };

    function _optPopulateGroupField() {
        var sel = document.getElementById('rpt-opt-group-field');
        if (!sel) return;
 
        /* Save currently selected keys before rebuild */
        var prevVals = (typeof window.pfSelGetValues === 'function')
            ? window.pfSelGetValues(sel)
            : [];
 
        /* Rebuild options — no blank "None" needed for multi-check */
        sel.innerHTML = _optState.cols.map(function (c) {
            return '<option value="' + _esc(c.key) + '">' + _esc(c.label) + '</option>';
        }).join('');
 
        /* ── Deselect ALL options BEFORE upgrade so widget starts empty ── */
        Array.prototype.forEach.call(sel.options, function (o) { o.selected = false; });
 
        /* Ensure multi-check attribute is set */
        sel.setAttribute('data-multi-check', '1');
        sel.multiple = true;
 
        /* Tear down any existing upgrade wrapper for clean re-upgrade */
        var existingWrap = sel._pfMchkWrap || sel.closest('.pf-mchk-wrap');
        if (existingWrap) {
            existingWrap.parentNode.insertBefore(sel, existingWrap);
            existingWrap.remove();
            delete sel._pfMchkWrap;
            sel.style.display = '';
            sel.removeAttribute('data-upgraded');
        }
 
        /* Re-upgrade as multi-check widget */
        if (typeof window.pfSelUpgradeOne === 'function') {
            window.pfSelUpgradeOne(sel);
        }
 
        /* Restore previously selected values (only if user had picked some) */
        if (prevVals.length && typeof window.pfSelSetValues === 'function') {
            window.pfSelSetValues(sel, prevVals);
        }
    }

    function _optRenderGrid() {
        var tbody = document.getElementById('rpt-opt-tbody'); if (!tbody) return;
        tbody.innerHTML = _optState.cols.map(function (col, i) {
            var selClass = (_optState.selected && _optState.selected.key === col.key) ? ' ropt-sel' : '';
            /* color swatch cell */
            /* bg color swatch */
            var colorBg  = col.color || '#e0e0e0';
            var colorCell = '<span class="ropt-color-swatch" data-idx="' + i + '" data-type="bg" ' +
                'style="display:inline-block;width:28px;height:16px;border-radius:3px;cursor:pointer;' +
                'border:1px solid var(--color-border-medium,#ccc);background:' + _esc(colorBg) + '" ' +
                'onclick="event.stopPropagation();rptOptOpenColorPicker(this,' + i + ',\'bg\')"></span>';
            /* text color swatch */
            var textColorBg = col.textColor || '#e0e0e0';
            var textColorCell = '<span class="ropt-color-swatch" data-idx="' + i + '" data-type="fg" ' +
                'style="display:inline-block;width:28px;height:16px;border-radius:3px;cursor:pointer;' +
                'border:1px solid var(--color-border-medium,#ccc);background:' + _esc(textColorBg) + '" ' +
                'onclick="event.stopPropagation();rptOptOpenColorPicker(this,' + i + ',\'fg\')"></span>';
            /* ── ONE closing </tr> only ── */
            return '<tr class="' + selClass + '" data-idx="' + i + '" onclick="rptOptRowClick(this,' + i + ')">' +
                '<td style="text-align:center"><input type="checkbox" class="ropt-chk"' + (col.show !== false ? ' checked' : '') + ' onchange="rptOptToggleShow(' + i + ',this)" onclick="event.stopPropagation()"></td>' +
                '<td>' + _esc(col.label) + '</td>' +
                '<td style="text-align:center"><input type="checkbox" class="ropt-chk"' + (col.total ? ' checked' : '') + ' onchange="rptOptToggleTotal(' + i + ',this)" onclick="event.stopPropagation()"></td>' +
                '<td style="text-align:center"><input type="checkbox" class="ropt-chk"' + (col.wrap ? ' checked' : '') + ' onchange="rptOptToggleWrap(' + i + ',this)" onclick="event.stopPropagation()"></td>' +
                '<td><input type="text" class="ropt-inp" value="' + _esc(col.format || '') + '" onchange="rptOptSetFormat(' + i + ',this)" onclick="event.stopPropagation()"></td>' +
                '<td style="text-align:center;padding:4px 8px">' + colorCell + '</td>' +
                '<td style="text-align:center;padding:4px 8px">' + textColorCell + '</td>' +
                '<td style="text-align:center">' + (i + 1) + '</td>' +
                '</tr>';
        }).join('');
    }

    window.rptOptRowClick = function (tr, idx) { var tbody = document.getElementById('rpt-opt-tbody'); if (tbody) tbody.querySelectorAll('tr').forEach(function (r) { r.classList.remove('ropt-sel'); }); tr.classList.add('ropt-sel'); _optState.selected = _optState.cols[idx] || null; };
    window.rptOptToggleShow = function (i, cb) { if (_optState.cols[i]) _optState.cols[i].show = cb.checked; };
    window.rptOptToggleTotal = function (i, cb) { if (_optState.cols[i]) _optState.cols[i].total = cb.checked; };
    window.rptOptToggleWrap = function (i, cb) { if (_optState.cols[i]) _optState.cols[i].wrap = cb.checked; };
    window.rptOptSetFormat = function (i, inp) { if (_optState.cols[i]) _optState.cols[i].format = inp.value; };

    window.rptOptFieldUp = function () {
        var sel = _optState.selected; if (!sel) { _toast('Select a row first', 'w'); return; }
        var idx = _optState.cols.indexOf(sel); if (idx <= 0) return;
        _optState.cols.splice(idx, 1); _optState.cols.splice(idx - 1, 0, sel);
        _optState.cols.forEach(function (c, i) { c.col = i + 1; }); _optRenderGrid();
        setTimeout(function () { var tbody = document.getElementById('rpt-opt-tbody'); if (!tbody) return; var tr = tbody.querySelector('tr[data-idx="' + (idx - 1) + '"]'); if (tr) { tr.classList.add('ropt-sel'); tr.scrollIntoView({ block: 'nearest' }); } }, 0);
    };
    window.rptOptFieldDown = function () {
        var sel = _optState.selected; if (!sel) { _toast('Select a row first', 'w'); return; }
        var idx = _optState.cols.indexOf(sel); if (idx < 0 || idx >= _optState.cols.length - 1) return;
        _optState.cols.splice(idx, 1); _optState.cols.splice(idx + 1, 0, sel);
        _optState.cols.forEach(function (c, i) { c.col = i + 1; }); _optRenderGrid();
        setTimeout(function () { var tbody = document.getElementById('rpt-opt-tbody'); if (!tbody) return; var tr = tbody.querySelector('tr[data-idx="' + (idx + 1) + '"]'); if (tr) { tr.classList.add('ropt-sel'); tr.scrollIntoView({ block: 'nearest' }); } }, 0);
    };

    function _optDelete() {
        if (!_optState.selected) { _toast('Select a row first', 'w'); return; }
        var idx = _optState.cols.indexOf(_optState.selected); if (idx >= 0) _optState.cols.splice(idx, 1);
        _optState.cols.forEach(function (c, i) { c.col = i + 1; }); _optState.selected = null;
        _optRenderGrid(); _optPopulateGroupField();
    }
    function _optEdit() { if (!_optState.selected) { _toast('Select a row first', 'w'); return; } rptEditReportField(_optState.selected); }

    function _optApply() {
        var reportId = _optState.reportId;
        _reportViewState.reportId = reportId;
        _reportViewState.cols = JSON.parse(JSON.stringify(_optState.cols));
        _applyColsToRptConfig(reportId, _optState.cols);

        /* store groupKey on state so rpt.js renderers can read it */
        var gfSel     = document.getElementById('rpt-opt-group-field');
        /* Read directly from native <select> selected options —
           works regardless of widget upgrade state */
        var groupKeys = [];
        if (gfSel) {
            var mchkWrap = gfSel._pfMchkWrap;
            if (mchkWrap && mchkWrap._pfList) {
                mchkWrap._pfList.querySelectorAll('.pf-mchk-item').forEach(function (item) {
                    var chk = item.querySelector('.pf-mchk-chk');
                    if (chk && chk.checked) groupKeys.push(item.getAttribute('data-val'));
                });
            }
            if (!groupKeys.length) {
                groupKeys = Array.prototype.filter.call(gfSel.options, function (o) {
                    return o.selected;
                }).map(function (o) { return o.value; });
            }
        }
        var groupKey  = groupKeys[0] || '';
 
        var st = window.rptGetState ? window.rptGetState(reportId) : null;
        if (st) {
            st.groupKey  = groupKey;
            st.groupKeys = groupKeys;
        }
 
        _renderReportTable(reportId);
        window.dispatchEvent(new CustomEvent('rpt:colsChanged', {
            detail: {
                reportId : reportId,
                cols     : JSON.parse(JSON.stringify(_optState.cols)),
                groupKey : groupKey,
                groupKeys: groupKeys
            }
        }));
 
        _optModal.close();
        _toast('Columns updated', 's');
    }

    function _optReset() {
        showConfirm('Reset all columns to defaults? Any added or edited columns will be lost.',
            function (confirmed) {
                if (!confirmed) return;
                var cfg = window.rptGetConfig ? window.rptGetConfig(_optState.reportId) : null;
                if (cfg && cfg._originalCols) {
                    _optState.cols = JSON.parse(JSON.stringify(cfg._originalCols));
                } else if (cfg && cfg.cols) {
                    _optState.cols = cfg.cols.map(function (c, i) {
                        return { key: c.key, label: c.label, show: true, total: false, wrap: false, format: '', color: '', textColor: '', col: i + 1, bold: !!c.bold, type: c.type || 'text' };
                    });
                }
                _reportViewState.cols = JSON.parse(JSON.stringify(_optState.cols));
                _optRenderGrid();
                _optPopulateGroupField();
                _toast('Reset to defaults', 's');
            },
            'warning', 'Reset Columns', 'Yes, Reset', 'Cancel');
    }

    /* ═════════════════════════════════════════════════════════════════
        4. ADD / EDIT REPORT FIELD MODAL  (uses UtilityModal engine)
     ═════════════════════════════════════════════════════════════════ */
    var _refModal = new UtilityModal({
        id: 'rptf-ref',
        title: 'Report Field',
        icon: 'M12 20h9 M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z',
        tabs: [{ id: 'rf', label: '» Field Details', icon: 'doc' }],
        toolbar: [
            { label: 'OK', icon: 'save', danger: false, onclick: function () { rptRefSaveField(); } },
            { label: 'Cancel', icon: 'close', danger: false, onclick: function () { _refModal.close(); } },
        ],
        onBuild: function (modal) {
            var nav = document.getElementById('rptf-ref-nav');
            if (nav) nav.style.cssText = 'display:none!important;width:0;overflow:hidden';
            var pane = modal.pane('rf'); if (!pane) return;
            pane.style.padding = '14px'; pane.style.gap = '8px';

            var ftOpts = [
                { value: 'text', label: 'Text' },
                { value: 'number', label: 'Number' },
                { value: 'date', label: 'Date' },
                { value: 'fk', label: 'Foreign Key' },
            ];
            var alignOpts = [
                { value: '0 Left', label: '0 Left' },
                { value: '1 Right', label: '1 Right' },
                { value: '2 Centre', label: '2 Centre' },
            ];

            pane.innerHTML = [
                UtilityModal.field('Field Name',
                    '<div style="flex:1;display:flex;gap:4px">' +
                    '<input type="text" id="ref-field-name" class="utm-inp" placeholder="e.g. emp_name">' +
                    '<button id="ref-browse-btn" class="utm-gbtn" style="white-space:nowrap">...</button>' +
                    '</div>'),
                UtilityModal.field('Display Name',
                    '<input type="text" id="ref-display-name" class="utm-inp" placeholder="Column header label">'),
                UtilityModal.field('Width',
                    '<input type="text" id="ref-width" class="utm-inp" placeholder="e.g. 120px or 15%">'),
                UtilityModal.field('Format',
                    '<input type="text" id="ref-format" class="utm-inp" placeholder="e.g. YYYY-MM-DD">'),
                UtilityModal.field('Field Type',
                    '<select id="ref-field-type" class="utm-sel">' +
                    ftOpts.map(function (o) {
                        return '<option value="' + o.value + '">' + o.label + '</option>';
                    }).join('') +
                    '</select>'),
                '<div id="ref-fk-wrap" style="display:none;flex-direction:column;gap:8px">',
                UtilityModal.field('FK Table',
                    '<select id="ref-fk-table" class="utm-sel"><option value="">-- Select --</option></select>'),
                UtilityModal.field('FK ID Field',
                    '<select id="ref-fk-id-field" class="utm-sel"><option value="">-- Select --</option></select>'),
                UtilityModal.field('FK Label Field',
                    '<select id="ref-fk-field" class="utm-sel"><option value="">-- Select --</option></select>'),
                '</div>',
                UtilityModal.field('Alignment',
                    UtilityModal.select('ref-align', alignOpts)),
                UtilityModal.field('Highlight Color',
                    '<div id="ref-color-wrap" style="flex:1;display:flex;flex-direction:row;align-items:center;gap:6px"></div>'),
            ].join('');

            /* Wire events after DOM is built */
            setTimeout(function () {
                var ftSel = document.getElementById('ref-field-type');
                if (ftSel) ftSel.addEventListener('change', window.rptRefFtChange);
                var browseBtn = document.getElementById('ref-browse-btn');
                if (browseBtn) browseBtn.addEventListener('click', window.rptRefBrowseField);
                var fkTbl = document.getElementById('ref-fk-table');
                if (fkTbl) fkTbl.addEventListener('change', window.rptRefFkTableChange);
                /* upgrade ALL selects in this pane with one call */
                _pfSelUpgradeAll(pane);
            }, 0);
        },
        onOpen: function (modal, ctx) {
            var col = ctx.col || null;
            var isNew = ctx.isNew !== false ? !col : false;
            modal.setSubtitle(isNew ? 'Add Field' : 'Edit Field');

            /* Populate fields */
            _refSet('ref-field-name', col && col.key || '');
            _refSet('ref-display-name', col && col.label || '');
            _refSet('ref-width', col && col.width || '');
            _refSet('ref-format', col && col.format || '');
            _refSet('ref-align', col && col.align || '0 Left');

            var curFT = (col && col.fieldType) || 'text';
            _refSet('ref-field-type', curFT);
            /* Sync the custom select UI — native .value= doesn't fire its internal update */
            if (typeof window.pfSelSetValue === 'function') {
                window.pfSelSetValue('ref-field-type', String(curFT));
            }

            var wrap = document.getElementById('ref-fk-wrap');
            if (wrap) wrap.style.display = curFT === 'fk' ? 'flex' : 'none';

            /* Color picker — replace each time */
            var colorWrap = document.getElementById('ref-color-wrap');
            if (colorWrap) {
                colorWrap.innerHTML = '';
                window._refColorPicker = _createColorPicker((col && col.color) || '');
                colorWrap.appendChild(window._refColorPicker.el);
            }

            if (curFT === 'fk') {
                setTimeout(function () {
                    _rptRefLoadFkTables(
                        col && col.fkTable || '',
                        col && col.fkIdField || '',
                        col && col.fkField || ''
                    );
                    /* upgrade FK selects after they are populated */
                    var pane = _refModal.pane('rf');
                    if (pane) _pfSelUpgradeAll(pane);
                }, 80);
            } else {
                setTimeout(function () {
                    var pane = _refModal.pane('rf');
                    if (pane) _pfSelUpgradeAll(pane);
                }, 0);
            }
        },
    });

    window.rptEditReportField = function (col) {
        _refModal.open({ col: col, isNew: !col });
    };

    window.rptRefBrowseField = function () {
        var reportId = _optState.reportId || _reportViewState.reportId;
        _openGetFields(reportId, function (tableName, fieldName, snakeKey) {
            var fnInp = document.getElementById('ref-field-name');
            var dnInp = document.getElementById('ref-display-name');
            var key = snakeKey || _toSnakeCase(fieldName);
            if (fnInp) fnInp.value = key;
            if (dnInp && !dnInp.value) dnInp.value = _toDisplayName(key);
        });
    };

    window.rptRefFtChange = function () {
        /* Custom select fires a real 'change' event on the underlying <select>,
           so sel.value is already correct here — just use it directly.        */
        var sel = document.getElementById('ref-field-type');
        var wrap = document.getElementById('ref-fk-wrap');
        if (!sel || !wrap) return;
        var v = sel.value;
        wrap.style.display = v === 'fk' ? 'flex' : 'none';
        if (v === 'fk') _rptRefLoadFkTables('', '', '');
    };

    function _rptRefLoadFkTables(savedTable, savedIdField, savedLabelField) {
        var reportId = _optState.reportId || _reportViewState.reportId;
        _fetchFieldsSchema(reportId, function (schema) {
            var tSel = document.getElementById('ref-fk-table');
            if (!tSel) return;
            tSel.innerHTML = '<option value="">-- Select --</option>' +
                schema.tables.map(function (t) {
                    return '<option value="' + _esc(t) + '"' + (t === savedTable ? ' selected' : '') + '>' + _esc(t) + '</option>';
                }).join('');
            /* upgrade the table select after options are ready */
            _pfSelUpgrade(tSel);
            if (savedTable) _rptRefLoadFkFields(savedTable, savedIdField, savedLabelField);
        });
    }

    window.rptRefFkTableChange = function () {
        var tSel = document.getElementById('ref-fk-table');
        if (tSel) _rptRefLoadFkFields(tSel.value, '', '');
    };

    function _rptRefLoadFkFields(tableName, savedIdField, savedLabelField) {
        var idSel = document.getElementById('ref-fk-id-field');
        var lblSel = document.getElementById('ref-fk-field');
        if (!tableName) {
            if (idSel) { idSel.innerHTML = '<option value="">-- Select --</option>'; _pfSelUpgrade(idSel); }
            if (lblSel) { lblSel.innerHTML = '<option value="">-- Select --</option>'; _pfSelUpgrade(lblSel); }
            return;
        }
        var reportId = _optState.reportId || _reportViewState.reportId;
        _fetchFieldsSchema(reportId, function (schema) {
            var fields = schema.fields[tableName] || [];
            var opts = '<option value="">-- Select --</option>' +
                fields.map(function (f) {
                    return '<option value="' + _esc(f) + '">' + _esc(f) + '</option>';
                }).join('');
            if (idSel) {
                idSel.innerHTML = opts;
                if (savedIdField) idSel.value = savedIdField;
                _pfSelUpgrade(idSel);
            }
            if (lblSel) {
                lblSel.innerHTML = opts;
                if (savedLabelField) lblSel.value = savedLabelField;
                _pfSelUpgrade(lblSel);
            }
        });
    }

    function _toDisplayName(s) {
    return s.replace(/_/g, ' ')
            .replace(/([a-z])([A-Z])/g, '$1 $2')
            .replace(/\b\w/g, function (c) { return c.toUpperCase(); }); // ← correct
}


    window.rptRefSaveField = function () {
        var col = _refModal.context().col;
        var isNew = !col;
        var key = (_refGet('ref-field-name') || '').trim();
        var label = (_refGet('ref-display-name') || '').trim();
        var width = (_refGet('ref-width') || '').trim();
        var format = (_refGet('ref-format') || '').trim();
        var ftSel = document.getElementById('ref-field-type');
        var fieldType = ftSel ? ftSel.value : 'text';
        var fkTable = fieldType === 'fk' ? (_refGet('ref-fk-table') || '') : '';
        var fkIdField = fieldType === 'fk' ? (_refGet('ref-fk-id-field') || '') : '';
        var fkField = fieldType === 'fk' ? (_refGet('ref-fk-field') || '') : '';
        var align = (_refGet('ref-align') || '0 Left');
        var color = (window._refColorPicker && typeof window._refColorPicker.getValue === 'function')
            ? window._refColorPicker.getValue() : '';

        if (!key) { _toast('Field Name is required', 'w'); return; }
        if (!label) label = _toDisplayName(key);

        var newCol = {
            key: key,
            label: label,
            show: true,
            total: false,
            wrap: false,
            format: format,
            width: width,
            fieldType: fieldType,
            fkTable: fkTable,
            fkIdField: fkIdField,
            fkField: fkField,
            align: align,
            color: color,
            col: _optState.cols.length + 1,
        };

        if (isNew) {
            _optState.cols.push(newCol);
        } else {
            var idx = _optState.cols.indexOf(col);
            if (idx >= 0) _optState.cols[idx] = Object.assign({}, _optState.cols[idx], newCol, { col: _optState.cols[idx].col });
        }

        _optRenderGrid();
        _optPopulateGroupField();
        _refModal.close();
        _toast('Field ' + (isNew ? 'added' : 'updated'), 's');
    };

    function _refSet(id, val) { var el = document.getElementById(id); if (!el) return; el.value = val || ''; }
    function _refGet(id) { var el = document.getElementById(id); return el ? el.value : ''; }


    /* ═════════════════════════════════════════════════════════════════
       5. SAVE REPORT STYLE MODAL
    ═════════════════════════════════════════════════════════════════ */
    var _srModal = new UtilityModal({
        id: 'rpt-sr-modal', title: 'Save Report',
        icon: 'M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z M17 21V13H7V21 M7 3V8H15',
        tabs: [{ id: 'sr', label: '» Styles', icon: 'doc' }],
        toolbar: [
            { label: 'OK', icon: 'save', danger: false, onclick: function () { _srSave(false); } },
            { label: 'Cancel', icon: 'close', danger: false, onclick: function () { _srModal.close(); } },
            { label: 'Delete', icon: 'del', danger: true, onclick: function () { _srDelete(); } },
        ],
        onBuild: function (modal) {
            var nav = document.getElementById('rpt-sr-modal-nav');
            if (nav) nav.style.cssText = 'display:none!important;width:0;overflow:hidden';
            var pane = modal.pane('sr'); if (!pane) return;
            var nameWrap = document.createElement('div');
            nameWrap.style.cssText = 'flex-shrink:0;margin-bottom:8px';
            nameWrap.innerHTML = '<input type="text" id="rpt-sr-name" class="sr-name-inp" placeholder="Report style name…">';
            pane.appendChild(nameWrap);
            var listWrap = document.createElement('div');
            listWrap.className = 'utm-grid-wrap'; listWrap.style.flex = '1';
            listWrap.innerHTML = '<table class="utm-grid"><thead><tr><th>Saved Styles</th></tr></thead><tbody id="rpt-sr-tbody"></tbody></table>';
            pane.appendChild(listWrap);
            setTimeout(function () {
                var inp = document.getElementById('rpt-sr-name');
                if (inp) inp.addEventListener('keydown', function (e) { if (e.key === 'Enter') { e.preventDefault(); _srSave(false); } });
            }, 0);
        },
        onOpen: function (modal, ctx) {
            _srState.reportId = ctx.reportId || _reportViewState.reportId;
            _srState.mrName = ctx.mrName || '';
            _srState.selected = null;
            var inp = document.getElementById('rpt-sr-name'); if (inp) inp.value = '';
            var tbody = document.getElementById('rpt-sr-tbody');
            if (tbody) tbody.innerHTML = '<tr><td style="padding:14px;text-align:center;color:var(--color-text-tertiary,#aaa);font-size:12px">Loading…</td></tr>';
            _srLoadStyles();
        },
    });

    function _srLoadStyles() {
        if (!_srState.mrName) { _srRenderList([]); return; }
        delete _headerCache.styles[_srState.mrName];
        fetch('/common/filter/report-styles/?mr_name=' + encodeURIComponent(_srState.mrName))
            .then(function (r) { return r.json(); })
            .then(function (d) { _srRenderList(d.success ? (d.styles || []) : []); })
            .catch(function () { _srRenderList([]); });
    }

    function _srRenderList(styles) {
        _srState.styles = styles;
        var tbody = document.getElementById('rpt-sr-tbody'); if (!tbody) return;
        if (!styles.length) { tbody.innerHTML = '<tr><td style="padding:20px;text-align:center;color:var(--color-text-tertiary,#aaa);font-size:12px">No saved styles</td></tr>'; return; }
        tbody.innerHTML = '';
        styles.forEach(function (name) {
            var tr = document.createElement('tr');
            tr.innerHTML = '<td style="padding:6px 10px;border-bottom:1px solid var(--color-border,#eee);cursor:pointer">' + _esc(name) + '</td>';
            tr.addEventListener('click', function () {
                tbody.querySelectorAll('tr').forEach(function (r) { r.classList.remove('selected'); });
                tr.classList.add('selected'); _srState.selected = name;
                var inp = document.getElementById('rpt-sr-name'); if (inp) inp.value = name;
            });
            tbody.appendChild(tr);
        });
    }

    function _srSave(overwrite) {
        var name = ((document.getElementById('rpt-sr-name') || {}).value || '').trim();
        if (!name) { _toast('Enter a style name', 'w'); return; }
        var cols = ((_optState.reportId === _srState.reportId && _optState.cols.length)
            ? _optState.cols : _reportViewState.cols)
            .filter(function (c) { return c.show !== false; });
        if (!cols.length) { _toast('No columns to save. Open Report Options first.', 'w'); return; }
        var details = cols.map(function (c, i) {
            var widthNum = parseFloat(String(c.width || '').replace(/[^0-9.]/g, '')) || 0;
            var alignNum = parseInt(String(c.align || '0'), 10) || 0;
            var dField = (String(c.dbField || '').toLowerCase() === 'yes') ? 1 : 0;
            return {
                ReportName: name,
                MRName: _srState.mrName,
                Section: c.key,
                FName: c.label,
                UFName: c.label,
                Width: widthNum,
                Index: i + 1,
                Alignment: alignNum,
                Show: c.show !== false ? 1 : 0,
                Heder: 0,
                Break: 0,
                UIndex: i + 1,
                UWidth: widthNum,
                MReport: 0,
                DField: dField,
                Font: 0,
                FieldType: c.fieldType || 1,
                FormatText: c.format || '',
                FontName: '',
                SYS_ITEM: 0,
                Color: c.color || '',
                FKTable: c.fkTable || '',
                FKIDField: c.fkIdField || '',
                FKField: c.fkField || '',
            };
        });
        fetch('/common/report/save-style/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': _csrf() },
            body: JSON.stringify({ report_name: name, mr_name: _srState.mrName, details: details, overwrite: overwrite }),
        })
            .then(function (r) { return r.json(); })
            .then(function (d) {
                if (d.success) {
                    _toast('Style "' + name + '" saved', 's');
                    delete _headerCache.styles[_srState.mrName];
                    _srModal.close();
                } else if (d.exists) {
                    showConfirm('"' + name + '" already exists. Overwrite it?',
                        function (ok) { if (ok) _srSave(true); },
                        'warning', 'Style Exists', 'Overwrite', 'Cancel');
                } else {
                    _toast(d.error || 'Save failed', 'e');
                }
            })
            .catch(function (e) { _toast('Network error: ' + e, 'e'); });
    }

    function _srDelete() {
        var name = _srState.selected; if (!name) { _toast('Select a style to delete', 'w'); return; }
        showConfirm('Delete style "' + name + '"? This cannot be undone.',
            function (confirmed) {
                if (!confirmed) return;
                fetch('/common/report/delete-style/', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': _csrf() },
                    body: JSON.stringify({ report_name: name, mr_name: _srState.mrName }),
                })
                    .then(function (r) { return r.json(); })
                    .then(function (d) {
                        if (d.success) {
                            _toast('Style deleted', 's');
                            delete _headerCache.styles[_srState.mrName];
                            _srState.selected = null;
                            var inp = document.getElementById('rpt-sr-name'); if (inp) inp.value = '';
                            _srLoadStyles();
                        } else { _toast(d.error || 'Delete failed', 'e'); }
                    })
                    .catch(function (e) { _toast('Network error: ' + e, 'e'); });
            },
            'danger', 'Delete Style', 'Yes, Delete', 'Cancel');
    }

    /* ═════════════════════════════════════════════════════════════════
       6. EDIT FILTER MODAL
    ═════════════════════════════════════════════════════════════════ */
    var FIELD_TYPES = [
        { value: 1, label: '1 Text' }, { value: 2, label: '2 Number' },
        { value: 3, label: '3 Foreign Field' }, { value: 6, label: '6 Date' }, { value: 7, label: '7 Time' },
    ];

    var _efModal = new UtilityModal({
        id: 'rpt-ef-modal', title: 'Edit Filter',
        icon: '<polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"/>',
        tabs: [{ id: 'ef', label: '» Filter Fields', icon: 'doc' }],
        toolbar: [
            { label: 'Close', icon: 'close', danger: false, onclick: function () { _efModal.close(); } },
            { label: 'Save', icon: 'save', danger: false, onclick: function () { _efSave(); } },
            { label: 'New', icon: 'doc', danger: false, onclick: function () { _efNew(); } },
            { label: 'Add', icon: 'doc', danger: false, onclick: function () { _efSave(); } },
            { label: 'Remove', icon: 'del', danger: true, onclick: function () { _efRemove(); } },
            { label: 'Default', icon: 'refresh', danger: false, onclick: function () { _efSetDefault(); } },
        ],
        onBuild: function (modal) {
            var pane = modal.pane('ef'); if (!pane) return;
            var rnRow = document.createElement('div');
            rnRow.id = 'rpt-ef-rn-row';
            rnRow.style.cssText = 'display:flex;align-items:center;gap:8px;flex-shrink:0;margin-bottom:8px;flex-wrap:wrap';
            rnRow.innerHTML = '<span style="font-size:11.5px;color:var(--color-text-secondary,#666);width:100px;flex-shrink:0;text-align:right">Report Name</span><select id="rpt-ef-rn-sel" class="utm-sel" style="max-width:180px" onchange="rptEfReportChange(this)"><option value="">— new report —</option></select><input id="rpt-ef-rn-inp" type="text" class="utm-inp" style="max-width:160px" placeholder="Type new / rename target"><button class="utm-gbtn" onclick="rptEfRename()" style="white-space:nowrap">Rename</button>';
            pane.appendChild(rnRow);
            var gridWrap = document.createElement('div'); gridWrap.style.cssText = 'flex-shrink:0;margin-bottom:10px';
            gridWrap.innerHTML = UtilityModal.grid('rpt-ef-tbody', [{ key: '_sn', label: 'SLNO', width: '50px' }, { key: 'FieldName', label: 'Field Name', width: '140px' }, { key: 'DisplayName', label: 'Display Name', width: '140px' }, { key: '_ftLabel', label: 'Field Type' }, { key: 'ColWidth', label: 'Col Width', width: '100px' }]);
            pane.appendChild(gridWrap);
            var detail = document.createElement('div');
            detail.id = 'rpt-ef-detail';
            detail.style.cssText = 'border-top:1px solid var(--color-border-light,#e0e0e0);padding-top:10px;display:flex;flex-direction:column;gap:6px;flex-shrink:0';
            var LW = '100px'; var ftOpts = FIELD_TYPES.map(function (t) { return { value: t.value, label: t.label }; });
            detail.innerHTML = ['<div style="display:flex;gap:12px;flex-wrap:wrap">', UtilityModal.field('Field Name', UtilityModal.input('rpt-ef-fn', 'text'), { labelWidth: LW }), UtilityModal.field('Field Type', UtilityModal.select('rpt-ef-ft', ftOpts), { labelWidth: LW }), UtilityModal.field('Col Width', UtilityModal.input('rpt-ef-cw', 'text', { placeholder: 'e.g. 3500,1500' }), { labelWidth: LW }), '</div>', '<div style="display:flex;gap:12px;flex-wrap:wrap">', UtilityModal.field('Display Name', UtilityModal.input('rpt-ef-dn', 'text'), { labelWidth: LW }), UtilityModal.field('ID Field', UtilityModal.input('rpt-ef-id', 'text'), { labelWidth: LW }), '</div>', UtilityModal.field('Filter SQL', UtilityModal.input('rpt-ef-sql', 'text', { placeholder: 'e.g. Description, Address1 From ChartofAccounts Where' }), { labelWidth: LW })].join('');
            pane.appendChild(detail);
            /* upgrade selects after DOM is built */
            setTimeout(function () { _pfSelUpgradeAll(pane); }, 0);
        },
        onOpen: function (modal, ctx) {
            _editState.reportId = ctx.reportId || ''; _editState.selected = null; _editState.isNew = true;
            modal.setSubtitle(ctx.reportId || ''); _efClearDetail();
            _efLoadReports(function () {
                _efLoadGridOnly();
                /* upgrade selects in the detail panel */
                var pane = _efModal.pane('ef');
                if (pane) _pfSelUpgradeAll(pane);
            });
        },
    });

    window.rptOpenEditFilter = function () { var menu = document.getElementById('rpt-filter-menu'); if (menu) menu.style.display = 'none'; _efModal.open({ reportId: _filterState.reportId }); };
    window.rptEfReportChange = function (sel) { var chosen = sel.value; _vEf('rpt-ef-rn-inp', chosen); if (chosen) { _editState.reportId = chosen; _efClearDetail(); _efLoadGridOnly(); } else { _editState.reportId = ''; _editState.rows = []; _editState.selected = null; _efRenderGrid(); _efClearDetail(); var inp = document.getElementById('rpt-ef-rn-inp'); if (inp) setTimeout(function () { inp.focus(); }, 50); } };
    window.rptEfRename = function () { var oldName = _editState.reportId; var newName = (_gEf('rpt-ef-rn-inp') || '').trim(); if (!oldName) { _toast('Select a report to rename first', 'w'); return; } if (!newName) { _toast('Type the new report name', 'w'); return; } if (newName === oldName) { _toast('Same name', 'w'); return; } var fd = new FormData(); fd.append('old_name', oldName); fd.append('new_name', newName); fetch('/common/filter/rename/', { method: 'POST', body: fd, headers: { 'X-CSRFToken': _csrf() } }).then(function (r) { return r.json(); }).then(function (d) { if (d.success) { _toast(d.message || 'Renamed', 's'); _editState.reportId = d.new_name; _efLoadReports(function () { _vEf('rpt-ef-rn-sel', d.new_name); _vEf('rpt-ef-rn-inp', d.new_name); _efLoadGridOnly(); }); if (_filterState.reportId === oldName) { _filterState.reportId = d.new_name; _filterState.loaded = false; } } else { _toast(d.error || 'Rename failed', 'e'); } }).catch(function (e) { _toast('Network error: ' + e, 'e'); }); };
    function _efLoadReports(cb) { fetch('/common/filter/reports/').then(function (r) { return r.json(); }).then(function (d) { _editState.reports = d.success ? (d.reports || []) : []; _efPopulateReportDropdown(); if (cb) cb(); }).catch(function () { _editState.reports = []; _efPopulateReportDropdown(); if (cb) cb(); }); }
    function _efPopulateReportDropdown() {
        var sel = document.getElementById('rpt-ef-rn-sel'); if (!sel) return;
        var current = _editState.reportId;
        sel.innerHTML = '<option value="">— new report —</option>' +
            _editState.reports.map(function (name) {
                return '<option value="' + _esc(name) + '"' + (name === current ? ' selected' : '') + '>' + _esc(name) + '</option>';
            }).join('');
        _pfSelUpgrade(sel);
        _vEf('rpt-ef-rn-inp', current);
    } function _efLoadGridOnly() { if (!_editState.reportId) { _editState.rows = []; _efRenderGrid(); return; } fetch('/common/filter/load/?report=' + encodeURIComponent(_editState.reportId)).then(function (r) { return r.json(); }).then(function (d) { _editState.rows = d.success ? (d.filters || []) : []; _efRenderGrid(); }).catch(function (e) { _toast('Load failed: ' + e, 'e'); }); }
    function _efLoad() { if (!_editState.reportId) { _editState.rows = []; _editState.selected = null; _editState.isNew = true; _efRenderGrid(); _efClearDetail(); return; } fetch('/common/filter/load/?report=' + encodeURIComponent(_editState.reportId)).then(function (r) { return r.json(); }).then(function (d) { _editState.rows = d.success ? (d.filters || []) : []; _editState.selected = null; _editState.isNew = true; _efRenderGrid(); _efClearDetail(); _efLoadReports(function () { _vEf('rpt-ef-rn-sel', _editState.reportId); _vEf('rpt-ef-rn-inp', _editState.reportId); }); }).catch(function (e) { _toast('Load failed: ' + e, 'e'); }); }
    function _efRenderGrid() { var rows = _editState.rows.map(function (r, i) { var t = FIELD_TYPES.find(function (x) { return x.value == r.FieldType; }); return Object.assign({}, r, { _sn: i + 1, _ftLabel: t ? t.label : String(r.FieldType) }); }); UtilityModal.renderGrid('rpt-ef-tbody', rows, [{ key: '_sn', label: 'SLNO' }, { key: 'FieldName', label: 'Field Name' }, { key: 'DisplayName', label: 'Display Name' }, { key: '_ftLabel', label: 'Field Type' }, { key: 'ColWidth', label: 'Col Width' }], function (row) { _editState.selected = row; _editState.isNew = false; _vEf('rpt-ef-fn', row.FieldName || ''); _vEf('rpt-ef-dn', row.DisplayName || ''); _vEf('rpt-ef-ft', row.FieldType || 1); _vEf('rpt-ef-cw', row.ColWidth || ''); _vEf('rpt-ef-id', row.IDField || ''); _vEf('rpt-ef-sql', row.FilterSql || ''); }); }
    function _efClearDetail() { ['rpt-ef-fn', 'rpt-ef-dn', 'rpt-ef-cw', 'rpt-ef-id', 'rpt-ef-sql'].forEach(function (id) { _vEf(id, ''); }); _vEf('rpt-ef-ft', 1); _editState.selected = null; _editState.isNew = true; }
    function _efNew() { _editState.selected = null; _editState.isNew = true; _efClearDetail(); var tbody = document.getElementById('rpt-ef-tbody'); if (tbody) tbody.querySelectorAll('tr').forEach(function (r) { r.classList.remove('selected'); }); var fn = document.getElementById('rpt-ef-fn'); if (fn) setTimeout(function () { fn.focus(); }, 30); }
    function _efSave() { var fieldName = (_gEf('rpt-ef-fn') || '').trim(); var displayName = (_gEf('rpt-ef-dn') || '').trim(); var fieldType = parseInt(_gEf('rpt-ef-ft') || '1', 10); var colWidth = (_gEf('rpt-ef-cw') || '').trim(); var idField = (_gEf('rpt-ef-id') || '').trim(); var filterSql = (_gEf('rpt-ef-sql') || '').trim(); if (!fieldName) { _toast('Field Name is required', 'w'); return; } if (!displayName) displayName = fieldName; var typedName = (_gEf('rpt-ef-rn-inp') || '').trim(); var reportId = typedName || _editState.reportId; if (!reportId) { _toast('Select or type a Report Name first', 'w'); return; } _editState.reportId = reportId; var fd = new FormData(); fd.append('report_name', reportId); fd.append('field_name', fieldName); fd.append('display_name', displayName); fd.append('field_type', fieldType); fd.append('col_width', colWidth); fd.append('id_field', idField); fd.append('filter_sql', filterSql); fd.append('is_default', 0); fd.append('operator', 0); fetch('/common/filter/save/', { method: 'POST', body: fd, headers: { 'X-CSRFToken': _csrf() } }).then(function (r) { return r.json(); }).then(function (d) { if (d.success) { _toast('Saved', 's'); _efLoad(); _filterState.loaded = false; _loadFieldDefs(_editState.reportId, function () { }); } else { _toast(d.error || 'Save failed', 'e'); } }).catch(function (e) { _toast('Network error: ' + e, 'e'); }); }
    function _efRemove() { if (!_editState.selected || !_editState.selected.FieldName) { _toast('Select a row to remove', 'w'); return; } var fd = new FormData(); fd.append('report_name', _editState.reportId); fd.append('field_name', _editState.selected.FieldName); fetch('/common/filter/delete/', { method: 'POST', body: fd, headers: { 'X-CSRFToken': _csrf() } }).then(function (r) { return r.json(); }).then(function (d) { if (d.success) { _toast('Removed', 's'); _efLoad(); _filterState.loaded = false; _loadFieldDefs(_editState.reportId, function () { }); } else { _toast(d.error || 'Delete failed', 'e'); } }).catch(function (e) { _toast('Network error: ' + e, 'e'); }); }
    function _efSetDefault() { if (!_editState.selected || !_editState.selected.FieldName) { _toast('Select a row first', 'w'); return; } var row = _editState.selected; var fd = new FormData(); fd.append('report_name', _editState.reportId); fd.append('field_name', row.FieldName); fd.append('display_name', row.DisplayName || row.FieldName); fd.append('field_type', row.FieldType || 1); fd.append('col_width', row.ColWidth || ''); fd.append('id_field', row.IDField || ''); fd.append('filter_sql', row.FilterSql || ''); fd.append('is_default', row.Default == 1 ? 0 : 1); fd.append('operator', row.Operator || 0); fetch('/common/filter/save/', { method: 'POST', body: fd, headers: { 'X-CSRFToken': _csrf() } }).then(function (r) { return r.json(); }).then(function (d) { if (d.success) { _toast('Default toggled', 's'); _efLoad(); } else { _toast(d.error || 'Failed', 'e'); } }); }

    function _vEf(id, val) {
        var el = document.getElementById(id);
        if (!el) return;
        if (el.tagName === 'SELECT') {
            el.value = String(val);
            /* keep custom select UI in sync if pfSel exposes a setter */
            if (typeof window.pfSelSetValue === 'function') window.pfSelSetValue(id, String(val));
            else if (window.pfSel && typeof window.pfSel.setValue === 'function') window.pfSel.setValue(id, String(val));
        } else {
            el.value = val || '';
        }
    }
    function _gEf(id) { var el = document.getElementById(id); return el ? el.value : ''; }

    global.rptOpenEditFilter = global.rptOpenEditFilter || function () { _efModal.open({ reportId: _filterState.reportId }); };

}(window));