/**
 * common/static/common/js/utilities_modal.js
 * ═══════════════════════════════════════════════════════════════════
 * BASE MODAL ENGINE
 * All ERP utility modals (Documents, Visa, Attachments, etc.)
 * are built on top of this engine.
 *
 * Inherits ALL styling from the active profile_form theme via
 * CSS variables — no hardcoded colours, zero extra CSS files needed.
 *
 * ── HOW TO CREATE A NEW MODAL ──────────────────────────────────────
 *
 *   var myModal = new UtilityModal({
 *
 *     id       : 'my-modal',          // unique ID
 *     title    : 'My Modal',          // header title
 *     subtitle : '',                  // dynamic subtitle (e.g. emp name)
 *     icon     : '<path .../>',       // SVG inner path for header icon
 *     width    : '780px',             // optional, default 780px
 *
 *     // Left sidenav tabs
 *     tabs: [
 *       { id: 'tab1', label: '» Tab One',   icon: '<path .../>' },
 *       { id: 'tab2', label: '» Tab Two',   icon: '<path .../>' },
 *     ],
 *
 *     // Header toolbar buttons
 *     toolbar: [
 *       { label: 'Save',   onclick: function() { myModal.save(); },   danger: false },
 *       { label: 'Delete', onclick: function() { myModal.delete(); }, danger: true  },
 *     ],
 *
 *     // Called once when modal DOM is first built
 *     // Use to inject pane content via modal.pane(tabId) element
 *     onBuild: function(modal) { },
 *
 *     // Called every time the modal is opened
 *     onOpen: function(modal, context) { },
 *
 *     // Called when a tab is switched
 *     onTabSwitch: function(modal, tabId) { },
 *   });
 *
 *   myModal.open({ regNo: '100', empName: 'John' });
 *   myModal.close();
 *   myModal.setSubtitle('John Doe — E100');
 *   myModal.pane('tab1')   // returns the pane DOM element for tab1
 *   myModal.activeTab()    // returns current active tab id
 *
 * ── BUILT-IN HELPERS ───────────────────────────────────────────────
 *
 *   UtilityModal.field(label, controlHtml, opts)
 *     → builds a label+input row div (matches profile_form label style)
 *     opts: { topAlign, fill, labelWidth }
 *
 *   UtilityModal.input(id, type, opts)
 *     → <input> html string
 *
 *   UtilityModal.select(id, options)
 *     → <select> html string, options = [{value, label}]
 *
 *   UtilityModal.textarea(id, rows)
 *     → <textarea> html string
 *
 *   UtilityModal.gridToolbar(buttons)
 *     → toolbar row above a grid
 *     buttons: [{label, onclick, primary, danger, icon}]
 *
 *   UtilityModal.grid(id, columns)
 *     → table html string
 *     columns: [{label, key, width}]
 *
 *   UtilityModal.renderGrid(tbodyId, rows, columns, onRowClick)
 *     → populates a grid tbody with data rows
 *
 *   UtilityModal.sectionHdr(label)
 *     → section divider div
 *
 * ═══════════════════════════════════════════════════════════════════
 */

(function (global) {
    'use strict';

    /* ── Inject base styles once ─────────────────────────────────────────── */
    function _injectBaseStyles() {}

    /* ── SVG icon builder ────────────────────────────────────────────────── */
    function _svg(paths, w) {
        w = w || 12;
        return '<svg viewBox="0 0 24 24" width="' + w + '" height="' + w + '" fill="none" ' +
               'stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">' +
               paths + '</svg>';
    }

    /* ── Default icons ───────────────────────────────────────────────────── */
    var ICONS = {
        attach  : '<path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48"/>',
        doc     : '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/>',
        save    : '<path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/><polyline points="17 21 17 13 7 13 7 21"/><polyline points="7 3 7 8 15 8"/>',
        del     : '<polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/>',
        close   : '<line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>',
        refresh : '<polyline points="23 4 23 10 17 10"/><polyline points="1 20 1 14 7 14"/><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/>',
        upload  : '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/>',
        browse  : '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/>',
        remove  : '<circle cx="12" cy="12" r="10"/><line x1="8" y1="12" x2="16" y2="12"/>',
        print   : '<polyline points="6 9 6 2 18 2 18 9"/><path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"/><rect x="6" y="14" width="12" height="8"/>',
    };

    /* ══════════════════════════════════════════════════════════════════════
       UtilityModal CLASS
    ══════════════════════════════════════════════════════════════════════ */
    function UtilityModal(cfg) {
        this._cfg      = cfg || {};
        this._el       = null;   // backdrop element
        this._built    = false;
        this._context  = null;   // current open context
        this._activeTab = cfg.tabs && cfg.tabs[0] ? cfg.tabs[0].id : '';
    }

    /* ── Build DOM ──────────────────────────────────────────────────────── */
    UtilityModal.prototype._build = function () {
        if (this._built) return;
        this._built = true;

        var cfg  = this._cfg;
        var self = this;

        /* Backdrop */
        var bd = document.createElement('div');
        bd.id        = cfg.id + '-bd';
        bd.className = 'utm-bd';
        bd.style.display = 'none';
        bd.addEventListener('click', function (e) {
            if (e.target === bd) self.close();
        });
        this._el = bd;

        /* Modal */
        var modal = document.createElement('div');
        modal.className = 'utm-modal';
        modal.style.width    = '50%';
        modal.style.minWidth = '400px';
        modal.style.height   = '50vh';
        modal.style.minHeight = '320px';
        modal.setAttribute('role', 'dialog');
        modal.setAttribute('aria-modal', 'true');

        /* Header */
        var hdr = document.createElement('div');
        hdr.className = 'utm-hdr';

        var hdrL = document.createElement('div');
        hdrL.className = 'utm-hdr-l';
        hdrL.innerHTML =
            '<div class="utm-hdr-ico">' +
            _svg(cfg.icon || ICONS.doc, 14) + '</div>' +
            '<div>' +
            '<div class="utm-hdr-title">' + (cfg.title || 'Utilities') + '</div>' +
            '<div class="utm-hdr-sub" id="' + cfg.id + '-sub">' + (cfg.subtitle || '') + '</div>' +
            '</div>';

        var hdrR = document.createElement('div');
        hdrR.className = 'utm-hdr-r';

        /* Toolbar buttons */
        (cfg.toolbar || []).forEach(function (btn) {
            var b = document.createElement('button');
            b.className = 'utm-hbtn utm-hbtn--' + (btn.danger ? 'danger' : 'normal');
            b.innerHTML = (btn.icon ? _svg(ICONS[btn.icon] || btn.icon) : '') + btn.label;
            b.addEventListener('click', btn.onclick || function(){});
            hdrR.appendChild(b);
        });

        /* Close button always last */
        var closeBtn = document.createElement('button');
        closeBtn.className = 'utm-hbtn utm-hbtn--close';
        closeBtn.title     = 'Close';
        closeBtn.innerHTML = _svg(ICONS.close, 14);
        closeBtn.addEventListener('click', function () { self.close(); });
        hdrR.appendChild(closeBtn);

        hdr.appendChild(hdrL);
        hdr.appendChild(hdrR);
        modal.appendChild(hdr);

        /* Body */
        var body = document.createElement('div');
        body.className = 'utm-body';

        /* Sidenav */
        var nav = document.createElement('nav');
        nav.className = 'utm-nav';
        nav.id = cfg.id + '-nav';

        (cfg.tabs || []).forEach(function (tab, i) {
            var item = document.createElement('div');
            item.className  = 'utm-nav-item' + (i === 0 ? ' active' : '');
            item.dataset.tab = tab.id;
            item.innerHTML  = _svg(ICONS[tab.icon] || tab.icon || ICONS.doc, 13) + tab.label;
            item.addEventListener('click', function () { self.switchTab(tab.id); });
            nav.appendChild(item);
        });
        body.appendChild(nav);

        /* Content */
        var content = document.createElement('div');
        content.className = 'utm-content';
        content.id = cfg.id + '-content';

        (cfg.tabs || []).forEach(function (tab, i) {
            var pane = document.createElement('div');
            pane.className = 'utm-pane' + (i === 0 ? ' active' : '');
            pane.id = cfg.id + '-pane-' + tab.id;
            content.appendChild(pane);
        });
        body.appendChild(content);
        modal.appendChild(body);
        bd.appendChild(modal);
        document.body.appendChild(bd);

        /* Let caller build pane content */
        if (typeof cfg.onBuild === 'function') cfg.onBuild(this);
    };

    /* ── Public methods ─────────────────────────────────────────────────── */

    UtilityModal.prototype.open = function (context) {
        this._build();
        this._context = context || {};
        this._el.style.display = 'flex';
        /* Reset to first tab */
        if (this._cfg.tabs && this._cfg.tabs[0]) {
            this.switchTab(this._cfg.tabs[0].id);
        }
        if (typeof this._cfg.onOpen === 'function') {
            this._cfg.onOpen(this, this._context);
        }
    };

    UtilityModal.prototype.close = function () {
        if (this._el) this._el.style.display = 'none';
        if (typeof this._cfg.onClose === 'function') this._cfg.onClose(this);
    };

    UtilityModal.prototype.switchTab = function (tabId) {
        this._activeTab = tabId;
        var id = this._cfg.id;

        /* Nav items */
        var nav = document.getElementById(id + '-nav');
        if (nav) {
            nav.querySelectorAll('.utm-nav-item').forEach(function (n) {
                n.classList.toggle('active', n.dataset.tab === tabId);
            });
        }

        /* Panes */
        var content = document.getElementById(id + '-content');
        if (content) {
            content.querySelectorAll('.utm-pane').forEach(function (p) {
                p.classList.toggle('active', p.id === id + '-pane-' + tabId);
            });
        }

        if (typeof this._cfg.onTabSwitch === 'function') {
            this._cfg.onTabSwitch(this, tabId);
        }
    };

    UtilityModal.prototype.pane = function (tabId) {
        return document.getElementById(this._cfg.id + '-pane-' + tabId);
    };

    UtilityModal.prototype.activeTab = function () {
        return this._activeTab;
    };

    UtilityModal.prototype.setSubtitle = function (text) {
        var el = document.getElementById(this._cfg.id + '-sub');
        if (el) el.textContent = text || '';
    };

    UtilityModal.prototype.context = function () {
        return this._context || {};
    };

    /* ══════════════════════════════════════════════════════════════════════
       STATIC BUILDER HELPERS  (UtilityModal.field, .input, etc.)
    ══════════════════════════════════════════════════════════════════════ */

    /**
     * Build a label + control row.
     * opts: { topAlign, fill, labelWidth, hasBrowse, browseFileId, browseTargetId }
     */
    UtilityModal.field = function (label, controlHtml, opts) {
        opts = opts || {};
        var lblStyle = opts.labelWidth ? 'style="width:' + opts.labelWidth + '"' : '';
        var browse = '';
        if (opts.hasBrowse && opts.browseFileId && opts.browseTargetId) {
            browse =
                '<button class="pf-browse-btn" type="button" ' +
                'onclick="document.getElementById(\'' + opts.browseFileId + '\').click()" title="Browse">' +
                'Browse…</button>' +
                '<input type="file" id="' + opts.browseFileId + '" style="display:none" ' +
                'onchange="window._utmBrowsePicked(\'' + opts.browseTargetId + '\',this)">';
        }
        return '<div class="pf-field">' +
               '<div class="pf-field-lbl" ' + lblStyle + '>' + label + '</div>' +
               '<div class="pf-field-ctl">' + controlHtml + browse + '</div>' +
               '</div>';
    };

    /** Plain input */
    UtilityModal.input = function (id, type, opts) {
        opts = opts || {};
        var cls  = 'utm-inp' + (opts.cls ? ' ' + opts.cls : '');
        var attr = 'id="' + id + '" type="' + (type || 'text') + '" class="' + cls + '"';
        if (opts.readonly)     attr += ' readonly';
        if (opts.placeholder)  attr += ' placeholder="' + opts.placeholder + '"';
        if (opts.value)        attr += ' value="' + opts.value + '"';
        return '<input ' + attr + '>';
    };

    /** Select */
    UtilityModal.select = function (id, options) {
        var opts = (options || []).map(function (o) {
            return '<option value="' + o.value + '">' + o.label + '</option>';
        }).join('');
        return '<select id="' + id + '" class="utm-sel">' + opts + '</select>';
    };

    /** Textarea */
    UtilityModal.textarea = function (id, rows, fillHeight) {
        var style = fillHeight ? ' style="flex:1;resize:none;min-height:60px"' : '';
        return '<textarea id="' + id + '" class="utm-ta" rows="' + (rows || 3) + '"' + style + '></textarea>';
    };

    /** Input group with browse button */
    UtilityModal.inputBrowse = function (inputId, fileId) {
    return '<div style="display:flex;flex:1">' +
           '<input id="' + inputId + '" type="text" class="utm-inp" ' +
           'style="border-radius:3px 0 0 3px;border-right:none">' +
           '<button class="utm-browse-pf" type="button" ' +
           'onclick="document.getElementById(\'' + fileId + '\').click()" title="Browse">' +
           'Browse…</button></div>' +
           '<input type="file" id="' + fileId + '" style="display:none" ' +
           'onchange="window._utmBrowsePicked(\'' + inputId + '\',this)">';
    };

    /** Section header divider */
    UtilityModal.sectionHdr = function (label) {
        return '<div class="utm-sec">' + label + '</div>';
    };

    /** Grid toolbar */
    UtilityModal.gridToolbar = function (buttons) {
        var btns = (buttons || []).map(function (b) {
            var cls = 'utm-gbtn' +
                (b.primary ? ' utm-gbtn--primary' : '') +
                (b.danger  ? ' utm-gbtn--danger'  : '');
            var ico = b.icon ? _svg(ICONS[b.icon] || b.icon, 12) : '';
            return '<button class="' + cls + '" onclick="' + b.onclick + '">' +
                   ico + b.label + '</button>';
        }).join('');
        return '<div class="utm-gtbar">' + btns + '</div>';
    };

    /** Grid table */
    UtilityModal.grid = function (id, columns) {
        var heads = (columns || []).map(function (c) {
            var w = c.width ? ' style="width:' + c.width + '"' : '';
            return '<th' + w + '>' + c.label + '</th>';
        }).join('');
        return '<div class="utm-grid-wrap">' +
               '<table class="utm-grid"><thead><tr>' + heads + '</tr></thead>' +
               '<tbody id="' + id + '"></tbody></table>' +
               '<div class="utm-empty" id="' + id + '-empty" style="display:none">No records</div>' +
               '</div>';
    };

    /** Render rows into a grid tbody */
    UtilityModal.renderGrid = function (tbodyId, rows, columns, onRowClick, onRowDblClick) {
        var tbody = document.getElementById(tbodyId);
        var empty = document.getElementById(tbodyId + '-empty');
        if (!tbody) return;
        tbody.innerHTML = '';

        if (!rows || !rows.length) {
            if (empty) empty.style.display = 'block';
            return;
        }
        if (empty) empty.style.display = 'none';

        rows.forEach(function (row, i) {
            var tr = document.createElement('tr');
            tr.style.cursor = 'pointer';
            tr.innerHTML = (columns || []).map(function (c) {
                var val = c.key === '_sn' ? (i + 1) : (row[c.key] || '');
                return '<td>' + String(val).replace(/&/g,'&amp;').replace(/</g,'&lt;') + '</td>';
            }).join('');
            tr.addEventListener('click', function () {
                tbody.querySelectorAll('tr').forEach(function (r) { r.classList.remove('selected'); });
                tr.classList.add('selected');
                if (typeof onRowClick === 'function') onRowClick(row, tr);
            });
            /* Double-click — open file or custom action */
            tr.addEventListener('dblclick', function () {
                if (typeof onRowDblClick === 'function') onRowDblClick(row, tr);
            });
            tbody.appendChild(tr);
        });
    };

    /* ── Global browse picker helper ─────────────────────────────────────── */
    window._utmBrowsePicked = function (targetId, input) {
        if (!input.files || !input.files[0]) return;
        var el = document.getElementById(targetId);
        if (el) el.value = input.files[0].name;
    };

    /* ── Export ─────────────────────────────────────────────────────────── */
    global.UtilityModal = UtilityModal;
    _injectBaseStyles();

}(window));