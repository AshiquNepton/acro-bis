/*
════════════════════════════════════════════════════════════════════
  common/static/common/js/rpt_print.js   v2.2

  CHANGES from v2.1:
  - Removed "New" and "Default" toolbar buttons from print dialog
  - OK button now prints DIRECTLY (no browser dialog re-open)
  - All selects use custom pf-sel-wrap (no native <select> visible)
  - Sidebar now has nav items: "Settings" and "Page Setup"
    Clicking either swaps the right-panel content
  - Header image: browse button opens company folder browser
    (calls /api/company-images/ endpoint) + manual path input
  - Company folder browser: grid of images, click to select
════════════════════════════════════════════════════════════════════
*/
(function (global) {
    'use strict';

    /* ── tiny helpers ── */
    function _esc(s) {
        return String(s || '')
            .replace(/&/g, '&amp;').replace(/</g, '&lt;')
            .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
    }
    function _toast(msg, type) {
        if (typeof global.pfToast === 'function') global.pfToast(msg, type);
        else console.log('[rpt_print]', type, msg);
    }
    function _ls(key, val) {
        try {
            if (val === undefined) return localStorage.getItem(key);
            if (val === null) { localStorage.removeItem(key); }
            else { localStorage.setItem(key, typeof val === 'string' ? val : JSON.stringify(val)); }
        } catch (e) { }
    }
    function _lsJson(key) {
        try { var v = localStorage.getItem(key); return v ? JSON.parse(v) : null; } catch (e) { return null; }
    }
    function _getCols(reportId) {
        var st = global.rptGetState ? global.rptGetState(reportId) : null;
        if (st && st.cols && st.cols.length) return st.cols;
        var cfg = global.rptGetConfig ? global.rptGetConfig(reportId) : null;
        return (cfg && cfg.cols) ? cfg.cols : [];
    }

    /* ── Company image browser API endpoint (configure as needed) ── */
    var _FTP_BROWSE_URL = (function () {
    var m = document.querySelector('meta[name="ftp-browse-url"]');
    return m ? m.content : '/common/ftp/browse/';
}());
var _COMPANY_FOLDER = (function () {
    var m = document.querySelector('meta[name="company-folder"]');
    return m ? m.content : '';
}());


    /* ══════════════════════════════════════════════════════════════
       A. LAST-USED STYLE MEMORY
    ══════════════════════════════════════════════════════════════ */

    global.rptRememberStyle = function (reportId, styleName) {
        if (!styleName) return;
        _ls('rpt_last_style_' + reportId, styleName);
        _ls('rpt_last_style_global', styleName);
    };

    global.rptGetLastStyle = function (reportId) {
        return _ls('rpt_last_style_' + reportId) || '';
    };

    (function _patchFilterStyle() {
        var _origApply = global.rptApplyReportFilter;
        global.rptApplyReportFilter = function (reportId, params) {
            try {
                var hv = params && params.header;
                if (hv && hv.reportStyle) {
                    global.rptRememberStyle(reportId, hv.reportStyle);
                }
            } catch (e) { }
            if (typeof _origApply === 'function') _origApply.apply(this, arguments);
        };
    })();


    /* ══════════════════════════════════════════════════════════════
       B. DEFAULT FIELDS
    ══════════════════════════════════════════════════════════════ */

    global.rptSaveDefaultFields = function (reportId) {
        var cols = _getCols(reportId);
        if (!cols.length) { _toast('No columns to save as default', 'w'); return; }
        _ls('rpt_def_cols_' + reportId, JSON.stringify(cols));
        _toast('Default column layout saved', 's');
    };

    global.rptLoadDefaultFields = function (reportId) {
        var saved = _lsJson('rpt_def_cols_' + reportId);
        if (!saved || !saved.length) {
            var cfg = global.rptGetConfig ? global.rptGetConfig(reportId) : null;
            if (cfg && cfg.cols && cfg.cols.length) {
                saved = cfg.cols;
            } else {
                _toast('No default saved for this report yet', 'w');
                return;
            }
        }
        if (global._rptConfig && global._rptConfig[reportId]) {
            global._rptConfig[reportId].cols = JSON.parse(JSON.stringify(saved));
        }
        if (typeof global.rptGoPage === 'function') {
            var st = global.rptGetState ? global.rptGetState(reportId) : null;
            global.rptGoPage(reportId, (st && st.currentPage) || 1);
        }
        _toast('Default field layout restored', 's');
    };


    /* ══════════════════════════════════════════════════════════════
       C. REPORT DESIGN MODE
    ══════════════════════════════════════════════════════════════ */

    var _designState = {
        reportId: '',
        cols: [],
        active: false,
        dragIdx: -1,
        dragStartX: 0,
        dragStartW: 0,
    };

    global.rptDesignReport = function (reportId) {
        if (_designState.active) { _designExit(); return; }

        var containerId = 'rpt-report-view-' + reportId;
        var container = document.getElementById(containerId);
        if (!container) {
            containerId = 'rpt-main-' + reportId;
            container = document.getElementById(containerId);
        }
        if (!container) {
            _toast('Open the report view first', 'w');
            return;
        }

        _designState.reportId = reportId;
        _designState.active = true;

        var cols = _getCols(reportId);
        _designState.cols = cols.map(function (c) {
            var saved = (_lsJson('rpt_col_widths_' + reportId) || {})[c.key];
            return {
                key: c.key,
                label: c.label,
                width: saved || c.width || 120,
                minWidth: 40,
                show: c.show !== false,
            };
        }).filter(function (c) { return c.show; });

        _designBuild(container, reportId);
        _designApplyWidths(reportId);
    };

    function _designBuild(container, reportId) {
        var bar = document.createElement('div');
        bar.id = 'rpt-design-bar-' + reportId;
        bar.className = 'rpt-design-bar';

        var barL = document.createElement('div');
        barL.className = 'rpt-design-bar-l';
        barL.innerHTML =
            '<div class="rpt-design-bar-ico">' +
            '<svg viewBox="0 0 24 24"><line x1="3" y1="6" x2="21" y2="6"/>' +
            '<line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="18" x2="21" y2="18"/></svg>' +
            '</div>' +
            '<div>' +
            '<div class="rpt-design-bar-title">Report Design</div>' +
            '<div class="rpt-design-bar-sub" id="rpt-design-info-' + reportId + '">Drag column edges to resize</div>' +
            '</div>';

        var barR = document.createElement('div');
        barR.className = 'rpt-design-bar-r';

        var saveBtn = document.createElement('button');
        saveBtn.className = 'utm-hbtn utm-hbtn--normal';
        saveBtn.title = 'Save column widths';
        saveBtn.innerHTML =
            '<svg viewBox="0 0 24 24"><path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/>' +
            '<polyline points="17 21 17 13 7 13 7 21"/><polyline points="7 3 7 8 15 8"/></svg>' +
            'Save Widths';
        saveBtn.addEventListener('click', function () { global.rptDesignSave(reportId); });

        var resetBtn = document.createElement('button');
        resetBtn.className = 'utm-hbtn utm-hbtn--normal';
        resetBtn.title = 'Reset column widths';
        resetBtn.innerHTML =
            '<svg viewBox="0 0 24 24"><polyline points="1 4 1 10 7 10"/>' +
            '<path d="M3.51 15a9 9 0 1 0 .49-5"/></svg>' +
            'Reset';
        resetBtn.addEventListener('click', function () { global.rptDesignReset(reportId); });

        var exitBtn = document.createElement('button');
        exitBtn.className = 'utm-hbtn utm-hbtn--danger';
        exitBtn.title = 'Exit design mode';
        exitBtn.innerHTML =
            '<svg viewBox="0 0 24 24"><line x1="18" y1="6" x2="6" y2="18"/>' +
            '<line x1="6" y1="6" x2="18" y2="18"/></svg>' +
            'Exit Design';
        exitBtn.addEventListener('click', function () { global.rptDesignExit(reportId); });

        barR.appendChild(saveBtn);
        barR.appendChild(resetBtn);
        barR.appendChild(exitBtn);

        bar.appendChild(barL);
        bar.appendChild(barR);

        container.insertBefore(bar, container.firstChild);

        var rulerWrap = document.createElement('div');
        rulerWrap.id = 'rpt-design-ruler-wrap-' + reportId;
        rulerWrap.className = 'rpt-design-ruler-wrap';
        rulerWrap.style.cssText = 'overflow-x:auto;overflow-y:hidden;';

        var ruler = document.createElement('div');
        ruler.id = 'rpt-design-ruler-' + reportId;
        ruler.className = 'rpt-design-ruler';
        ruler.style.cssText = 'display:flex;align-items:stretch;';
        rulerWrap.appendChild(ruler);

        bar.parentNode.insertBefore(rulerWrap, bar.nextSibling);

        _designRenderRuler(reportId);

        var tbl = document.getElementById('rpt-report-tbl-' + reportId);
        if (tbl) tbl.classList.add('design-active');

        var body = document.getElementById('rpt-report-body-' + reportId);
        if (body) {
            body.addEventListener('scroll', function () {
                rulerWrap.scrollLeft = body.scrollLeft;
            });
            rulerWrap.addEventListener('scroll', function () {
                body.scrollLeft = rulerWrap.scrollLeft;
            });
        }
    }

    function _designRenderRuler(reportId) {
        var ruler = document.getElementById('rpt-design-ruler-' + reportId);
        if (!ruler) return;
        ruler.innerHTML = '';

        _designState.cols.forEach(function (col, idx) {
            var cell = document.createElement('div');
            cell.className = 'rpt-ruler-col';
            cell.style.cssText = 'width:' + col.width + 'px;min-width:' + col.minWidth + 'px;position:relative;flex-shrink:0;box-sizing:border-box;';
            cell.dataset.idx = idx;

            var lbl = document.createElement('div');
            lbl.className = 'rpt-ruler-col-lbl';
            lbl.textContent = col.label;
            cell.appendChild(lbl);

            var wlbl = document.createElement('div');
            wlbl.className = 'rpt-ruler-col-width';
            wlbl.id = 'rpt-ruler-w-' + reportId + '-' + idx;
            wlbl.textContent = col.width + 'px';
            cell.appendChild(wlbl);

            if (idx < _designState.cols.length - 1) {
                var handle = document.createElement('div');
                handle.className = 'rpt-col-resize-handle';
                handle.dataset.idx = idx;
                handle.title = 'Drag to resize';
                handle.addEventListener('mousedown', function (e) { _designDragStart(e, idx, reportId); });
                cell.appendChild(handle);
            }

            ruler.appendChild(cell);
        });
    }

    function _designDragStart(e, idx, reportId) {
        e.preventDefault();
        _designState.dragIdx = idx;
        _designState.dragStartX = e.clientX;
        _designState.dragStartW = _designState.cols[idx].width;

        var tip = document.createElement('div');
        tip.className = 'rpt-width-tip';
        tip.id = 'rpt-width-tip';
        tip.textContent = _designState.dragStartW + 'px';
        document.body.appendChild(tip);
        tip.style.left = (e.clientX + 12) + 'px';
        tip.style.top = (e.clientY - 8) + 'px';

        var handle = e.currentTarget;
        handle.classList.add('dragging');

        function _move(ev) {
            var dx = ev.clientX - _designState.dragStartX;
            var newW = Math.max(_designState.cols[idx].minWidth, _designState.dragStartW + dx);
            _designState.cols[idx].width = Math.round(newW);

            var ruler = document.getElementById('rpt-design-ruler-' + reportId);
            if (ruler) {
                var cells = ruler.querySelectorAll('.rpt-ruler-col');
                if (cells[idx]) cells[idx].style.width = newW + 'px';
            }
            var wlbl = document.getElementById('rpt-ruler-w-' + reportId + '-' + idx);
            if (wlbl) wlbl.textContent = Math.round(newW) + 'px';

            if (tip) {
                tip.textContent = Math.round(newW) + 'px';
                tip.style.left = (ev.clientX + 12) + 'px';
                tip.style.top = (ev.clientY - 8) + 'px';
            }

            _designApplyWidths(reportId);

            var info = document.getElementById('rpt-design-info-' + reportId);
            if (info) info.textContent = '"' + _designState.cols[idx].label + '" → ' + Math.round(newW) + 'px';
        }

        function _up() {
            handle.classList.remove('dragging');
            var tip2 = document.getElementById('rpt-width-tip');
            if (tip2) tip2.remove();
            document.removeEventListener('mousemove', _move);
            document.removeEventListener('mouseup', _up);
            _designState.dragIdx = -1;
        }

        document.addEventListener('mousemove', _move);
        document.addEventListener('mouseup', _up);
    }

    function _designApplyWidths(reportId) {
        var tbl = document.getElementById('rpt-report-tbl-' + reportId);
        if (!tbl) return;
        var cg = tbl.querySelector('colgroup');
        if (!cg) {
            cg = document.createElement('colgroup');
            tbl.insertBefore(cg, tbl.firstChild);
        }
        cg.innerHTML = '';
        var snCol = document.createElement('col');
        snCol.style.width = '36px';
        cg.appendChild(snCol);
        _designState.cols.forEach(function (c) {
            var col = document.createElement('col');
            col.style.width = c.width + 'px';
            cg.appendChild(col);
        });
    }

    global.rptDesignSave = function (reportId) {
        var widths = {};
        _designState.cols.forEach(function (c) { widths[c.key] = c.width; });
        _ls('rpt_col_widths_' + reportId, JSON.stringify(widths));

        /* Update live config so next render uses new widths */
        var cfg = global.rptGetConfig ? global.rptGetConfig(reportId) : null;
        if (cfg && cfg.cols) {
            cfg.cols.forEach(function (c) {
                if (widths[c.key]) c.width = widths[c.key];
            });
        }

        /* Re-render the current page immediately — no refresh needed */
        if (typeof global.rptGoPage === 'function') {
            var st = global.rptGetState ? global.rptGetState(reportId) : null;
            global.rptGoPage(reportId, (st && st.currentPage) || 1);
        }

        _toast('Column widths saved', 's');
    };

    global.rptDesignReset = function (reportId) {
        _ls('rpt_col_widths_' + reportId, null);
        _designState.cols.forEach(function (dc) { dc.width = 120; });
        _designRenderRuler(reportId);
        _designApplyWidths(reportId);
        _toast('Widths reset', 's');
    };

    global.rptDesignExit = function (reportId) { _designExit(reportId); };

    function _designExit(reportId) {
        var rid = reportId || _designState.reportId;
        var bar = document.getElementById('rpt-design-bar-' + rid);
        if (bar) bar.remove();
        var ruler = document.getElementById('rpt-design-ruler-wrap-' + rid);
        if (ruler) ruler.remove();
        var tbl = document.getElementById('rpt-report-tbl-' + rid);
        if (tbl) tbl.classList.remove('design-active');
        _designState.active = false;
        _designState.reportId = '';
    }


    /* ══════════════════════════════════════════════════════════════
       D. REPORT PRINT DIALOG  — built with UtilityModal engine
       Sidebar nav: Settings | Page Setup
       Tab: Heading & Footer
    ══════════════════════════════════════════════════════════════ */

    var _DEFAULT_PRINT_CFG = {
        printStyle: 'Graphics',
        orientation: 'Portrait',
        printer: '',
        pageEjectAfter: false,
        print: 'All',
        newPage: true,
        autoFit: true,
        printModel: 'Separate Page',
        verticalLines: false,
        horizontalLines: false,
        printHeading: 'Header Logo',
        lineStyle: 'Dot',
        noCopies: 1,
        dateTime: true,
        startingPageNo: 1,
        pageWidth: 131,
        topMargin: 1,
        leftMargin: 1,
        reportHeading: '',
        reportFooter: false,
        reportFooterText: '',
        headerImagePath: '',
    };

    var _printRid = '';

    function _getPrintCfg(reportId) {
        var saved = _lsJson('rpt_print_cfg_' + reportId);
        var cfg = Object.assign({}, _DEFAULT_PRINT_CFG, saved || {});
        if (!cfg.reportHeading) {
            var ctx = global.rptGetConfig ? global.rptGetConfig(reportId) : null;
            cfg.reportHeading = (ctx && ctx.title) ? ctx.title : (reportId || '');
        }
        return cfg;
    }

    function _savePrintCfg(reportId, cfg) {
        _ls('rpt_print_cfg_' + reportId, JSON.stringify(cfg));
    }

    /* ══════════════════════════════════════════════════════════════
       D1. CUSTOM pf-sel-wrap BUILDER
       Builds the same searchable dropdown used by pf_select.js
       but inline via innerHTML (no native <select> upgrade pass needed).
    ══════════════════════════════════════════════════════════════ */

    function _buildPfSel(id, opts, currentVal) {
        var options = opts.map(function (o) {
            var val = typeof o === 'object' ? o.value : o;
            var lbl = typeof o === 'object' ? o.label : o;
            return { value: val, label: lbl };
        });
        var currentLabel = '';
        options.forEach(function (o) { if (o.value === currentVal) currentLabel = o.label; });
        if (!currentLabel && options.length) currentLabel = options[0].label;

        var optionsHtml = options.map(function (o) {
            return '<option value="' + _esc(o.value) + '"' + (o.value === currentVal ? ' selected' : '') + '>' + _esc(o.label) + '</option>';
        }).join('');

        return '<div class="pf-sel-wrap rpt-pd-pf-sel" data-name="' + id + '">' +
            '<div class="pf-sel-trigger" tabindex="0">' +
            '<span class="pf-sel-val">' + _esc(currentLabel) + '</span>' +
            '<span class="pf-sel-arr">▾</span>' +
            '</div>' +
            '<div class="pf-sel-popup">' +
            '<input class="pf-sel-search" type="text" placeholder="Search…" autocomplete="off">' +
            '<div class="pf-sel-list">' +
            options.map(function (o) {
                return '<div class="pf-sel-opt' + (o.value === currentVal ? ' selected' : '') + '" data-val="' + _esc(o.value) + '">' + _esc(o.label) + '</div>';
            }).join('') +
            '</div>' +
            '</div>' +
            '<select id="' + id + '" name="' + id + '" style="display:none" data-upgraded="1">' + optionsHtml + '</select>' +
            '</div>';
    }

    function _wirePfSel(wrapEl) {
        var trigger   = wrapEl.querySelector('.pf-sel-trigger');
        var popup     = wrapEl.querySelector('.pf-sel-popup');
        var search    = wrapEl.querySelector('.pf-sel-search');
        var list      = wrapEl.querySelector('.pf-sel-list');
        var valSpan   = wrapEl.querySelector('.pf-sel-val');
        var nativeSel = wrapEl.querySelector('select');

        if (!trigger || !popup) return;

        wrapEl._pfNative  = nativeSel;
        wrapEl._pfValSpan = valSpan;
        wrapEl._pfList    = list;
        wrapEl._pfSearch  = search;
        if (nativeSel) nativeSel._pfWrap = wrapEl;

        trigger.addEventListener('click', function (e) {
            e.stopPropagation();
            var isOpen = popup.classList.contains('open');
            _closePfSelAll();
            if (!isOpen) _openPfSel(wrapEl, popup, search);
        });

        trigger.addEventListener('keydown', function (e) {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                if (popup.classList.contains('open')) _closePfSel(wrapEl, popup);
                else _openPfSel(wrapEl, popup, search);
            }
            if (e.key === 'Escape') _closePfSel(wrapEl, popup);
        });

        if (search) {
            search.addEventListener('input', function (e) {
                e.stopPropagation();
                var q = search.value.toLowerCase().trim();
                var items = list.querySelectorAll('.pf-sel-opt:not(.pf-sel-no-match-msg)');
                var any = false;
                items.forEach(function (item) {
                    var match = !q || item.textContent.toLowerCase().indexOf(q) !== -1;
                    item.style.display = match ? '' : 'none';
                    if (match) any = true;
                });
                var nm = list.querySelector('.pf-sel-no-match-msg');
                if (!any) {
                    if (!nm) {
                        nm = document.createElement('div');
                        nm.className = 'pf-sel-opt pf-sel-no-match pf-sel-no-match-msg';
                        nm.textContent = 'No match';
                        list.appendChild(nm);
                    }
                } else if (nm) nm.remove();
            });
            search.addEventListener('click', function (e) { e.stopPropagation(); });
        }

        if (list) {
            list.addEventListener('click', function (e) {
                var item = e.target.closest('.pf-sel-opt');
                if (!item || item.classList.contains('pf-sel-no-match')) return;
                var val = item.getAttribute('data-val');
                valSpan.textContent = item.textContent;
                list.querySelectorAll('.pf-sel-opt').forEach(function (o) { o.classList.remove('selected'); });
                item.classList.add('selected');
                if (nativeSel) {
                    nativeSel.value = val;
                    nativeSel.dispatchEvent(new Event('change', { bubbles: true }));
                }
                _closePfSel(wrapEl, popup);
                trigger.focus();
            });
        }
    }

    function _openPfSel(wrap, popup, search) {
        popup.classList.add('open');
        wrap.querySelector('.pf-sel-trigger').classList.add('open');
        if (search) { search.value = ''; search.focus(); }
        popup.querySelectorAll('.pf-sel-opt').forEach(function (o) { o.style.display = ''; });
        var nm = popup.querySelector('.pf-sel-no-match-msg');
        if (nm) nm.remove();
        var rect = wrap.getBoundingClientRect();
        var below = window.innerHeight - rect.bottom;
        if (below < 220 && rect.top > 220) {
            popup.style.bottom = 'calc(100% + 3px)'; popup.style.top = 'auto';
        } else {
            popup.style.top = 'calc(100% + 3px)'; popup.style.bottom = 'auto';
        }
    }
    function _closePfSel(wrap, popup) {
        popup.classList.remove('open');
        var t = wrap.querySelector('.pf-sel-trigger');
        if (t) t.classList.remove('open');
    }
    function _closePfSelAll() {
        document.querySelectorAll('.rpt-pd-pf-sel .pf-sel-popup.open').forEach(function (p) {
            p.classList.remove('open');
            var w = p.closest('.pf-sel-wrap');
            if (w) { var t = w.querySelector('.pf-sel-trigger'); if (t) t.classList.remove('open'); }
        });
    }
    document.addEventListener('click', function (e) {
        if (!e.target.closest('.rpt-pd-pf-sel')) _closePfSelAll();
    });

    function _pfSelVal(id) {
        var el = document.getElementById(id);
        return el ? el.value : '';
    }
    function _pfSelSet(id, val) {
        var sel = document.getElementById(id);
        if (!sel) return;
        var wrap = sel._pfWrap || sel.closest('.pf-sel-wrap');
        if (!wrap) { sel.value = String(val); return; }
        var strVal = String(val !== null && val !== undefined ? val : '');
        var list = wrap._pfList || wrap.querySelector('.pf-sel-list');
        var valSpan = wrap._pfValSpan || wrap.querySelector('.pf-sel-val');
        var item = null;
        if (list) {
            list.querySelectorAll('.pf-sel-opt').forEach(function (o) {
                if (o.getAttribute('data-val') === strVal) item = o;
            });
            if (item) {
                list.querySelectorAll('.pf-sel-opt').forEach(function (o) { o.classList.remove('selected'); });
                item.classList.add('selected');
                if (valSpan) valSpan.textContent = item.textContent;
            }
        }
        sel.value = strVal;
    }

    function _wireAllPfSels(container) {
        container.querySelectorAll('.rpt-pd-pf-sel').forEach(function (wrap) {
            _wirePfSel(wrap);
        });
    }


    /* ══════════════════════════════════════════════════════════════
       D2. HTML BUILDER HELPERS
    ══════════════════════════════════════════════════════════════ */

    function _pInp(id, w, type) {
        return '<input id="' + id + '" class="utm-inp rpt-pd-inp" type="' + (type || 'text') + '" style="width:' + (w || '80px') + '">';
    }
    function _pChk(id) { return '<input type="checkbox" id="' + id + '" class="rpt-pchk">'; }
    function _pRow(fields) {
        return '<div class="rpt-pd-row">' +
            fields.map(function (f) {
                return '<div class="rpt-pd-cell' + (f.full ? ' rpt-pd-cell--full' : '') + '">' +
                    (f.lbl ? '<div class="rpt-pd-lbl">' + f.lbl + '</div>' : '') +
                    '<div class="rpt-pd-ctl">' + f.ctl + '</div>' +
                    '</div>';
            }).join('') +
            '</div>';
    }


    /* ══════════════════════════════════════════════════════════════
       D3. SETTINGS PANEL CONTENT (main left area)
    ══════════════════════════════════════════════════════════════ */

    function _buildSettingsContent(cfg) {
        return [
            _pRow([
                { lbl: 'Print Style', ctl: _buildPfSel('rpt-pd-style', ['Graphics', 'Text', 'HTML'], cfg.printStyle) },
                { lbl: 'Orientation', ctl: _buildPfSel('rpt-pd-orient', ['Portrait', 'Landscape'], cfg.orientation) },
            ]),
            _pRow([
                { lbl: 'Printer', ctl: _buildPfSel('rpt-pd-printer', ['Default Printer', 'PDF Printer', 'AnyDesk Printer', 'Microsoft Print to PDF'], cfg.printer), full: true },
            ]),
            '<div class="rpt-pd-divider"></div>',
            _pRow([
                { lbl: '', ctl: _pChk('rpt-pd-page-eject') + '<span class="rpt-plbl">Page Eject After</span>' },
                { lbl: 'Print', ctl: _buildPfSel('rpt-pd-print', ['All', 'Selection', 'Pages'], cfg.print) +
    '<div id="rpt-pd-pages-row" style="display:' + (cfg.print === 'Pages' ? 'flex' : 'none') + ';gap:4px;align-items:center;margin-top:4px">' +
    '<input id="rpt-pd-page-from" class="utm-inp rpt-pd-inp" type="number" min="1" placeholder="From" style="width:60px">' +
    '<span style="font-size:11px;color:var(--color-text-tertiary)">to</span>' +
    '<input id="rpt-pd-page-to" class="utm-inp rpt-pd-inp" type="number" min="1" placeholder="To" style="width:60px">' +
    '</div>'
},
            ]),
            _pRow([
                { lbl: '', ctl: _pChk('rpt-pd-newpage') + '<span class="rpt-plbl">New Page</span>&nbsp;&nbsp;' + _pChk('rpt-pd-autofit') + '<span class="rpt-plbl">Auto Fit</span>' },
                { lbl: 'Print Model', ctl: _buildPfSel('rpt-pd-model', ['Separate Page', 'Continuous', 'Booklet'], cfg.printModel) },
            ]),
            _pRow([
                { lbl: '', ctl: _pChk('rpt-pd-vlines') + '<span class="rpt-plbl">Vertical Lines</span>' },
                { lbl: 'Print Heading', ctl: _buildPfSel('rpt-pd-heading', ['Header Logo', 'Header Text', 'No Header'], cfg.printHeading) },
            ]),
            _pRow([
                { lbl: '', ctl: _pChk('rpt-pd-hlines') + '<span class="rpt-plbl">Horizontal Lines</span>' },
                { lbl: '', ctl: '' },
            ]),
        ].join('');
    }


    /* ══════════════════════════════════════════════════════════════
       D4. PAGE SETUP PANEL CONTENT (swaps into main area)
    ══════════════════════════════════════════════════════════════ */

    function _buildPageSetupContent(cfg) {
        return [
            _pRow([
                { lbl: 'Page Width', ctl: _pInp('rpt-pd-pgwidth', '100%', 'number') },
                { lbl: 'Orientation', ctl: _buildPfSel('rpt-pd-orient-ps', ['Portrait', 'Landscape'], cfg.orientation) },
            ]),
            '<div class="rpt-pd-divider"></div>',
            '<div class="rpt-ps-section-title">Margins</div>',
            _pRow([
                { lbl: 'Top Margin (cm)', ctl: _pInp('rpt-pd-topmgn', '100%', 'number') },
                { lbl: 'Left Margin (cm)', ctl: _pInp('rpt-pd-leftmgn', '100%', 'number') },
            ]),
            '<div class="rpt-pd-divider"></div>',
            '<div class="rpt-ps-section-title">Print Options</div>',
            _pRow([
                { lbl: 'Line Style', ctl: _buildPfSel('rpt-pd-linstyle', ['Dot', 'Solid', 'Dashed'], cfg.lineStyle) },
                { lbl: 'No of Copies', ctl: _pInp('rpt-pd-copies', '100%', 'number') },
            ]),
            _pRow([
                { lbl: 'Starting Page No', ctl: _pInp('rpt-pd-startpg', '100%', 'number') },
                {
                    lbl: '', ctl: '<div style="display:flex;align-items:center;gap:6px;margin-top:18px">' +
                        _pChk('rpt-pd-datetime') +
                        '<label for="rpt-pd-datetime" class="rpt-plbl" style="cursor:pointer">Include Date / Time</label>' +
                        '</div>'
                },
            ]),
        ].join('');
    }


    /* ══════════════════════════════════════════════════════════════
       D5. HEADING & FOOTER TAB CONTENT
    ══════════════════════════════════════════════════════════════ */

    function _buildHeadingPane(cfg) {
        var imgRowVisible = cfg.printHeading === 'Header Logo';
        return [
            /* Header image path — shown only when Header Logo is selected */
            '<div id="rpt-pd-header-img-row" class="rpt-pd-header-img-row" style="' + (imgRowVisible ? '' : 'display:none') + '">' +
            _pRow([{
                lbl: 'Header Image Path',
                ctl: '<div style="display:flex;gap:6px;align-items:center;flex:1">' +
                    '<input id="rpt-pd-header-img-path" class="utm-inp rpt-pd-inp" type="text" placeholder="/media/headers/logo.png" style="flex:1">' +
                    '<button type="button" class="utm-hbtn utm-hbtn--normal" onclick="rptPreviewHeaderImg()" title="Preview image">' +
                    '<svg viewBox="0 0 24 24" style="width:13px;height:13px;stroke:currentColor;fill:none;stroke-width:2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>' +
                    'Preview</button>' +
                    '<button type="button" class="utm-hbtn utm-hbtn--normal" onclick="rptBrowseCompanyImages()" title="Browse company images">' +
                    '<svg viewBox="0 0 24 24" style="width:13px;height:13px;stroke:currentColor;fill:none;stroke-width:2"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/></svg>' +
                    'Browse</button>' +
                    '</div>',
                full: true,
            }]) +
            '<div id="rpt-pd-header-img-preview" class="rpt-pd-img-preview-wrap" style="display:none">' +
            '<img id="rpt-pd-header-img-el" src="" alt="Header preview" style="max-height:80px;max-width:100%;border-radius:4px;border:1px solid var(--color-border-light,#e0e0e0)">' +
            '</div>' +
            '</div>',
            _pRow([{
                lbl: 'Report Heading',
                ctl: '<textarea id="rpt-pd-rpt-heading" class="utm-ta rpt-pd-ta" style="height:64px"></textarea>',
                full: true,
            }]),
            _pRow([{
                lbl: '',
                ctl: _pChk('rpt-pd-footer-chk') + '<span class="rpt-plbl">Report Footer</span>',
                full: true,
            }]),
            _pRow([{
                lbl: 'Footer Text',
                ctl: '<textarea id="rpt-pd-footer-txt" class="utm-ta rpt-pd-ta" style="height:48px" placeholder="Footer text…"></textarea>',
                full: true,
            }]),
        ].join('');
    }
    
   

    function _fillSettingsFields(cfg) {
        _pfSelSet('rpt-pd-style',    cfg.printStyle);
        _pfSelSet('rpt-pd-orient',   cfg.orientation);
        _pfSelSet('rpt-pd-printer',  cfg.printer);
        _pfSelSet('rpt-pd-print',    cfg.print);
        _pfSelSet('rpt-pd-model',    cfg.printModel);
        _pfSelSet('rpt-pd-heading',  cfg.printHeading);

        function _setC(id, val) { var el = document.getElementById(id); if (el) el.checked = !!val; }
        _setC('rpt-pd-page-eject', cfg.pageEjectAfter);
        _setC('rpt-pd-newpage',    cfg.newPage);
        _setC('rpt-pd-autofit',    cfg.autoFit);
        _setC('rpt-pd-vlines',     cfg.verticalLines);
        _setC('rpt-pd-hlines',     cfg.horizontalLines);
    }

    function _fillPageSetupFields(cfg) {
        function _setV(id, val) { var el = document.getElementById(id); if (el) el.value = String(val !== null && val !== undefined ? val : ''); }
        _pfSelSet('rpt-pd-linstyle',  cfg.lineStyle);
        _pfSelSet('rpt-pd-orient-ps', cfg.orientation);
        _setV('rpt-pd-copies',  cfg.noCopies);
        _setV('rpt-pd-startpg', cfg.startingPageNo);
        _setV('rpt-pd-pgwidth', cfg.pageWidth);
        _setV('rpt-pd-topmgn',  cfg.topMargin);
        _setV('rpt-pd-leftmgn', cfg.leftMargin);
        function _setC(id, val) { var el = document.getElementById(id); if (el) el.checked = !!val; }
        _setC('rpt-pd-datetime', cfg.dateTime);
    }


    /* ══════════════════════════════════════════════════════════════
       D8. HEADING CHANGE HANDLER
    ══════════════════════════════════════════════════════════════ */

    function _bindHeadingChange() {
        var sel = document.getElementById('rpt-pd-heading');
        if (!sel) return;
        function _toggle() {
            var row = document.getElementById('rpt-pd-header-img-row');
            if (!row) return;
            row.style.display = (sel.value === 'Header Logo') ? '' : 'none';
        }
        sel.addEventListener('change', _toggle);
        _toggle();
    }


    /* ══════════════════════════════════════════════════════════════
       D9. COMPANY IMAGE BROWSER
    ══════════════════════════════════════════════════════════════ */

    global.rptBrowseCompanyImages = function () {
        /* Remove existing browser if open */
        var existing = document.getElementById('rpt-img-browser-overlay');
        if (existing) { existing.remove(); return; }

        var overlay = document.createElement('div');
        overlay.id = 'rpt-img-browser-overlay';
        overlay.className = 'rpt-img-browser-overlay';
        overlay.innerHTML = [
            '<div class="rpt-img-browser-modal">',
            '<div class="rpt-img-browser-header">',
            '<div class="rpt-img-browser-title">',
            '<svg viewBox="0 0 24 24" style="width:15px;height:15px;stroke:currentColor;fill:none;stroke-width:2"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/></svg>',
            'Company Images',
            '</div>',
            '<button class="rpt-img-browser-close" onclick="document.getElementById(\'rpt-img-browser-overlay\').remove()">✕</button>',
            '</div>',
            '<div class="rpt-img-browser-search-bar" style="flex-direction:column;align-items:stretch;gap:6px">',
            '<div id="rpt-img-browser-breadcrumb" style="font-size:11.5px;color:var(--color-text-secondary,#666);padding:2px 0;min-height:18px"></div>',
            '<input id="rpt-img-browser-search" class="utm-inp" type="text" placeholder="Search files…" style="flex:1" oninput="rptImgBrowserFilter(this.value)">',
            '</div>',
            '<div class="rpt-img-browser-body" id="rpt-img-browser-body">',
            '<div class="rpt-img-browser-loading">',
            '<svg viewBox="0 0 24 24" style="width:24px;height:24px;stroke:var(--color-primary,#8b0000);fill:none;stroke-width:2;animation:rpt-spin 1s linear infinite"><path d="M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0z" stroke-opacity=".2"/><path d="M12 3a9 9 0 0 1 9 9"/></svg>',
            '<span>Loading images…</span>',
            '</div>',
            '</div>',
            '<div class="rpt-img-browser-footer">',
            '<div id="rpt-img-browser-selected-path" class="rpt-img-browser-sel-path">No image selected</div>',
            '<div style="display:flex;gap:6px">',
            '<button class="utm-hbtn utm-hbtn--normal" onclick="rptImgBrowserConfirm()">Select</button>',
            '<button class="utm-hbtn utm-hbtn--danger" onclick="document.getElementById(\'rpt-img-browser-overlay\').remove()">Cancel</button>',
            '</div>',
            '</div>',
            '</div>',
        ].join('');

        document.body.appendChild(overlay);

        /* Click outside to close */
        overlay.addEventListener('click', function (e) {
            if (e.target === overlay) overlay.remove();
        });

        /* Load images from API */
        _imgBrowserSelected = '';
        _ftpBrowse('');
    };

    var _imgBrowserSelected = '';

    var _ftpCurrentPath = '';

function _ftpBrowse(path) {
    _ftpCurrentPath = path || '';
    var body = document.getElementById('rpt-img-browser-body');
    if (!body) return;

    // Show spinner
    body.innerHTML =
        '<div class="rpt-img-browser-loading">' +
        '<svg viewBox="0 0 24 24" style="width:24px;height:24px;stroke:var(--color-primary,#8b0000);fill:none;stroke-width:2;animation:rpt-spin 1s linear infinite">' +
        '<path d="M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0z" stroke-opacity=".2"/>' +
        '<path d="M12 3a9 9 0 0 1 9 9"/></svg>' +
        '<span>Loading…</span></div>';

    _renderBreadcrumb(path);

    var url = _FTP_BROWSE_URL + '?path=' + encodeURIComponent(path || '');
    fetch(url, { credentials: 'same-origin' })
        .then(function (r) {
            if (!r.ok) throw new Error('HTTP ' + r.status);
            return r.json();
        })
        .then(function (data) {
            if (data.error) throw new Error(data.error);
            _renderFtpGrid(data);
        })
        .catch(function (err) {
            if (!body) return;
            body.innerHTML =
                '<div class="rpt-img-browser-empty">' +
                '<svg viewBox="0 0 24 24" style="width:32px;height:32px;stroke:#ccc;fill:none;stroke-width:1.5">' +
                '<path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>' +
                '<line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>' +
                '<div>Could not load FTP folder.<br><small style="color:#aaa">' + _esc(err.message) + '</small></div>' +
                '</div>';
        });
}

function _renderBreadcrumb(path) {
    var bar = document.getElementById('rpt-img-browser-breadcrumb');
    if (!bar) return;
    var parts = (path || '').split('/').filter(Boolean);
    var html = '<span class="rpt-ftp-crumb" data-path="" style="cursor:pointer">🏠 Root</span>';
    var built = '';
    parts.forEach(function (p, i) {
        built += (built ? '/' : '') + p;
        var bPath = built;
        html += ' <span style="opacity:.4">›</span> ' +
            '<span class="rpt-ftp-crumb" data-path="' + _esc(bPath) + '" style="cursor:pointer">' + _esc(p) + '</span>';
    });
    bar.innerHTML = html;
    bar.querySelectorAll('.rpt-ftp-crumb').forEach(function (el) {
        el.addEventListener('click', function () {
            _ftpBrowse(el.getAttribute('data-path'));
        });
    });
}

function _renderFtpGrid(data) {
    var body = document.getElementById('rpt-img-browser-body');
    if (!body) return;

    var folders = data.folders || [];
    var files   = data.files   || [];

    if (!folders.length && !files.length) {
        body.innerHTML =
            '<div class="rpt-img-browser-empty">' +
            '<svg viewBox="0 0 24 24" style="width:32px;height:32px;stroke:#ccc;fill:none;stroke-width:1.5">' +
            '<rect x="3" y="3" width="18" height="18" rx="2"/>' +
            '<circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/></svg>' +
            '<div>This folder is empty.</div></div>';
        return;
    }

    var html = '<div class="rpt-img-browser-grid" id="rpt-img-browser-grid">';

    // Folders first
    folders.forEach(function (name) {
        var childPath = (data.path ? data.path + '/' : '') + name;
        html +=
            '<div class="rpt-img-browser-item rpt-img-browser-item--folder" ' +
            'data-path="' + _esc(childPath) + '" data-type="folder" ' +
            'onclick="rptFtpOpenFolder(this)">' +
            '<div class="rpt-img-browser-thumb" style="background:#fffbf0">' +
            '<svg viewBox="0 0 24 24" style="width:36px;height:36px;stroke:#f59e0b;fill:#fef3c7;stroke-width:1.5">' +
            '<path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/></svg>' +
            '</div>' +
            '<div class="rpt-img-browser-item-name" title="' + _esc(name) + '">' + _esc(name) + '</div>' +
            '</div>';
    });

    // Files
    files.forEach(function (f) {
        var isPdf = f.type === 'pdf';
        var thumb = isPdf
            ? '<svg viewBox="0 0 24 24" style="width:32px;height:32px;stroke:#dc2626;fill:#fee2e2;stroke-width:1.5"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>'
            : '<img src="' + _esc('/common/ftp/serve/?path=' + encodeURIComponent(f.path)) + '" ' +
              'alt="' + _esc(f.name) + '" loading="lazy" style="max-width:100%;max-height:100%;object-fit:contain" ' +
              'onerror="this.parentNode.innerHTML=\'<div class=\\\"rpt-img-no-thumb\\\">?</div>\'">';

        html +=
            '<div class="rpt-img-browser-item' + (isPdf ? ' rpt-img-browser-item--pdf' : '') + '" ' +
            'data-path="' + _esc(f.path) + '" data-type="' + _esc(f.type) + '" ' +
            'onclick="rptImgBrowserSelect(this)">' +
            '<div class="rpt-img-browser-thumb">' + thumb + '</div>' +
            '<div class="rpt-img-browser-item-name" title="' + _esc(f.name) + '">' + _esc(f.name) + '</div>' +
            '</div>';
    });

    html += '</div>';
    body.innerHTML = html;
}

global.rptFtpOpenFolder = function (el) {
    _ftpBrowse(el.getAttribute('data-path'));
};

    function _renderImgBrowserGrid(images) {
        var body = document.getElementById('rpt-img-browser-body');
        if (!body) return;

        if (!images || !images.length) {
            body.innerHTML = '<div class="rpt-img-browser-empty">' +
                '<svg viewBox="0 0 24 24" style="width:32px;height:32px;stroke:#ccc;fill:none;stroke-width:1.5"><rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/></svg>' +
                '<div>No images found in company folder.</div>' +
                '</div>';
            return;
        }

        var gridHtml = '<div class="rpt-img-browser-grid" id="rpt-img-browser-grid">' +
            images.map(function (img, idx) {
                var thumbSrc = img.thumb || img.url || img.path || '';
                var name = img.name || img.path || ('Image ' + (idx + 1));
                return '<div class="rpt-img-browser-item" data-idx="' + idx + '" data-path="' + _esc(img.path || img.url || '') + '" onclick="rptImgBrowserSelect(this)">' +
                    '<div class="rpt-img-browser-thumb">' +
                    '<img src="' + _esc(thumbSrc) + '" alt="' + _esc(name) + '" loading="lazy" ' +
                    'onerror="this.parentNode.innerHTML=\'<div class=\\\"rpt-img-no-thumb\\\">?</div>\'">' +
                    '</div>' +
                    '<div class="rpt-img-browser-item-name" title="' + _esc(name) + '">' + _esc(name) + '</div>' +
                    '</div>';
            }).join('') +
            '</div>';

        body.innerHTML = gridHtml;
    }

    global.rptImgBrowserFilter = function (query) {
        var q = (query || '').toLowerCase().trim();
        var items = document.querySelectorAll('.rpt-img-browser-item');
        items.forEach(function (item) {
            var name = (item.querySelector('.rpt-img-browser-item-name') || {}).textContent || '';
            item.style.display = (!q || name.toLowerCase().indexOf(q) !== -1) ? '' : 'none';
        });
    };

    global.rptImgBrowserSelect = function (el) {
        document.querySelectorAll('.rpt-img-browser-item').forEach(function (i) {
            i.classList.remove('selected');
        });
        el.classList.add('selected');
        _imgBrowserSelected = el.getAttribute('data-path') || '';
        var selEl = document.getElementById('rpt-img-browser-selected-path');
        if (selEl) selEl.textContent = _imgBrowserSelected || 'No image selected';
    };

    global.rptImgBrowserConfirm = function () {
        if (!_imgBrowserSelected) {
            _toast('Please select an image first', 'w');
            return;
        }
        var pathInp = document.getElementById('rpt-pd-header-img-path');
        if (pathInp) {
            pathInp.value = _imgBrowserSelected;
            /* Trigger preview automatically */
            global.rptPreviewHeaderImg();
        }
        var overlay = document.getElementById('rpt-img-browser-overlay');
        if (overlay) overlay.remove();
        _imgBrowserSelected = '';
    };

    global.rptImgBrowserManualEntry = function () {
        /* Closes browser and focuses the path input */
        var overlay = document.getElementById('rpt-img-browser-overlay');
        if (overlay) overlay.remove();
        var inp = document.getElementById('rpt-pd-header-img-path');
        if (inp) { inp.focus(); inp.select(); }
    };


    /* ══════════════════════════════════════════════════════════════
       D10. PREVIEW HEADER IMAGE
    ══════════════════════════════════════════════════════════════ */

    global.rptPreviewHeaderImg = function () {
        var inp = document.getElementById('rpt-pd-header-img-path');
        var wrap = document.getElementById('rpt-pd-header-img-preview');
        var img = document.getElementById('rpt-pd-header-img-el');
        if (!inp || !wrap || !img) return;
        var path = (inp.value || '').trim();
        if (!path) { _toast('Enter an image path first', 'w'); return; }
        img.src = path;
        wrap.style.display = 'block';
        img.onerror = function () { _toast('Image not found at path: ' + path, 'w'); wrap.style.display = 'none'; };
        img.onload = function () { wrap.style.display = 'block'; };
    };


    /* ══════════════════════════════════════════════════════════════
       D11. UTILITY MODAL INSTANCE
       Toolbar: OK | Preview | Menu | Cancel  (New + Default removed)
    ══════════════════════════════════════════════════════════════ */

    var _printModal = new UtilityModal({
        id: 'rpt-print-modal',
        title: 'ReportPrint',
        icon: '<polyline points="6 9 6 2 18 2 18 9"/><path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"/><rect x="6" y="14" width="12" height="8"/>',
        tabs: [
    { id: 'settings',  label: '» Settings',         icon: 'doc' },
    { id: 'pagesetup', label: '» Page Setup',        icon: 'doc' },
    { id: 'heading',   label: '» Heading / Footer',  icon: 'doc' },
],
        toolbar: [
            {
                label: 'OK', icon: 'save', danger: false,
                onclick: function () { _printDo(_printRid, false); },
            },
            {
                label: 'Preview', icon: 'browse', danger: false,
                onclick: function () { _printDo(_printRid, true); },
            },
            {
                label: 'Menu', icon: 'doc', danger: false,
                onclick: function () { _printMenu(_printRid); },
            },
            {
                label: 'Cancel', icon: 'close', danger: true,
                onclick: function () { _printModal.close(); },
            },
        ],
        onBuild: function (modal) {
            var cfg = _getPrintCfg(_printRid);
            var settingsPane  = modal.pane('settings');
            var pageSetupPane = modal.pane('pagesetup');
            var headingPane   = modal.pane('heading');

            if (settingsPane) {
                settingsPane.style.padding = '12px 16px';
                settingsPane.innerHTML = _buildSettingsContent(cfg);
                _wireAllPfSels(settingsPane);
                /* Show/hide page range inputs when Print select changes */
                var printSel = document.getElementById('rpt-pd-print');
                if (printSel) {
                    printSel.addEventListener('change', function () {
                        var row = document.getElementById('rpt-pd-pages-row');
                        if (row) row.style.display = printSel.value === 'Pages' ? 'flex' : 'none';
                    });
                }
            }

            if (pageSetupPane) {
                pageSetupPane.style.padding = '12px 16px';
                pageSetupPane.innerHTML = _buildPageSetupContent(cfg);
                _wireAllPfSels(pageSetupPane);
            }

            if (headingPane) {
                headingPane.style.padding = '12px 16px';
                headingPane.style.gap = '6px';
                headingPane.innerHTML = _buildHeadingPane(cfg);
                _wireAllPfSels(headingPane);
                _bindHeadingChange();
            }
        },
        onOpen: function (modal, ctx) {
            _printRid = ctx.reportId || '';
            modal.setSubtitle(ctx.reportId || '');
            _fillPrintForm(_getPrintCfg(_printRid));
        },
    });


    /* ══════════════════════════════════════════════════════════════
       D12. COLLECT / FILL FORM VALUES
    ══════════════════════════════════════════════════════════════ */

    function _collectPrintCfg() {
        function _chk(id) { var el = document.getElementById(id); return el ? el.checked : false; }
        function _val(id) { var el = document.getElementById(id); return el ? el.value : ''; }

        /* Orientation: could be on settings panel OR page setup panel */
        var orientation = _pfSelVal('rpt-pd-orient') || _pfSelVal('rpt-pd-orient-ps') || _val('rpt-pd-orient') || _val('rpt-pd-orient-ps');

        return {
            printStyle:       _pfSelVal('rpt-pd-style')    || _val('rpt-pd-style'),
            orientation:      orientation,
            printer:          _pfSelVal('rpt-pd-printer')  || _val('rpt-pd-printer'),
            pageEjectAfter:   _chk('rpt-pd-page-eject'),
            print:      _pfSelVal('rpt-pd-print') || _val('rpt-pd-print'),
            pageFrom:   parseInt(_val('rpt-pd-page-from') || '1',  10) || 1,
            pageTo:     parseInt(_val('rpt-pd-page-to')   || '999', 10) || 999,
            newPage:          _chk('rpt-pd-newpage'),
            autoFit:          _chk('rpt-pd-autofit'),
            printModel:       _pfSelVal('rpt-pd-model')    || _val('rpt-pd-model'),
            verticalLines:    _chk('rpt-pd-vlines'),
            horizontalLines:  _chk('rpt-pd-hlines'),
            printHeading:     _pfSelVal('rpt-pd-heading')  || _val('rpt-pd-heading'),
            lineStyle:        _pfSelVal('rpt-pd-linstyle') || _val('rpt-pd-linstyle'),
            noCopies:         parseInt(_val('rpt-pd-copies')  || '1', 10),
            dateTime:         _chk('rpt-pd-datetime'),
            startingPageNo:   parseInt(_val('rpt-pd-startpg') || '1', 10),
            pageWidth:        parseFloat(_val('rpt-pd-pgwidth') || '131'),
            topMargin:        parseFloat(_val('rpt-pd-topmgn')  || '1'),
            leftMargin:       parseFloat(_val('rpt-pd-leftmgn') || '1'),
            reportHeading:    _val('rpt-pd-rpt-heading'),
            reportFooter:     _chk('rpt-pd-footer-chk'),
            reportFooterText: _val('rpt-pd-footer-txt'),
            headerImagePath:  _val('rpt-pd-header-img-path'),
        };
    }

    function _fillPrintForm(cfg) {
        function _setV(id, val) { var el = document.getElementById(id); if (el) el.value = String(val !== null && val !== undefined ? val : ''); }
        function _setC(id, val) { var el = document.getElementById(id); if (el) el.checked = !!val; }

        /* Settings panel selects */
        _pfSelSet('rpt-pd-style',    cfg.printStyle);
        _pfSelSet('rpt-pd-orient',   cfg.orientation);
        _pfSelSet('rpt-pd-printer',  cfg.printer);
        _pfSelSet('rpt-pd-print',    cfg.print);
        _pfSelSet('rpt-pd-model',    cfg.printModel);
        _pfSelSet('rpt-pd-heading',  cfg.printHeading);

        /* Page setup panel selects (if currently visible) */
        _pfSelSet('rpt-pd-linstyle',  cfg.lineStyle);
        _pfSelSet('rpt-pd-orient-ps', cfg.orientation);

        /* Checkboxes */
        _setC('rpt-pd-page-eject', cfg.pageEjectAfter);
        _setC('rpt-pd-newpage',    cfg.newPage);
        _setC('rpt-pd-autofit',    cfg.autoFit);
        _setC('rpt-pd-vlines',     cfg.verticalLines);
        _setC('rpt-pd-hlines',     cfg.horizontalLines);
        _setC('rpt-pd-datetime',   cfg.dateTime);
        _setC('rpt-pd-footer-chk', cfg.reportFooter);

        /* Text inputs */
        _setV('rpt-pd-copies',          cfg.noCopies);
        _setV('rpt-pd-startpg',         cfg.startingPageNo);
        _setV('rpt-pd-pgwidth',         cfg.pageWidth);
        _setV('rpt-pd-topmgn',          cfg.topMargin);
        _setV('rpt-pd-leftmgn',         cfg.leftMargin);
        _setV('rpt-pd-rpt-heading',     cfg.reportHeading);
        _setV('rpt-pd-footer-txt',      cfg.reportFooterText);
    _setV('rpt-pd-header-img-path', cfg.headerImagePath || '');

    _fillPageSetupFields(cfg);
    _bindHeadingChange();
}

    global.rptPrintReport = function (reportId) {
        _printModal.open({ reportId: reportId });
    };


    /* ══════════════════════════════════════════════════════════════
       D13. PRINT MENU
    ══════════════════════════════════════════════════════════════ */

    function _printMenu(reportId) {
        var menuEl = document.getElementById('rpt-print-dropdown-menu');
        if (menuEl) { menuEl.remove(); return; }

        var menu = document.createElement('div');
        menu.id = 'rpt-print-dropdown-menu';
        menu.style.cssText =
            'position:fixed;background:var(--color-bg-card,#fff);' +
            'border:1px solid var(--color-border-light,#ddd);border-radius:6px;' +
            'box-shadow:0 6px 20px rgba(0,0,0,.14);z-index:10002;min-width:200px;padding:4px 0;';

        var items = [
            {
                label: 'Print',
                fn: function () {
                    var cfg = _collectPrintCfg();
                    _savePrintCfg(reportId, cfg);
                    _printModal.close();
                    setTimeout(function () { global.rptPrintReport(reportId); }, 150);
                },
            },
            {
                label: 'Save Print Config',
                fn: function () { _savePrintCfg(reportId, _collectPrintCfg()); _toast('Print config saved', 's'); },
            },
            {
                label: 'Save as Default',
                fn: function () {
                    _savePrintCfg(reportId, _collectPrintCfg());
                    global.rptSaveDefaultFields(reportId);
                },
            },
            { sep: true },
            {
                label: 'Save to PDF',
                fn: function () { _printModal.close(); global.rptSaveToPdf(reportId); },
            },
            {
                label: 'Export as HTML',
                fn: function () { _printModal.close(); _exportHtml(reportId); },
            },
        ];

        items.forEach(function (item) {
            if (item.sep) {
                var s = document.createElement('hr');
                s.style.cssText = 'margin:4px 0;border:none;border-top:1px solid var(--color-border-light,#eee)';
                menu.appendChild(s);
                return;
            }
            var div = document.createElement('div');
            div.style.cssText =
                'padding:7px 16px;font-size:12.5px;color:var(--color-text-secondary,#555);cursor:pointer;' +
                'font-family:DM Sans,Segoe UI,sans-serif;';
            div.textContent = item.label;
            div.addEventListener('mouseenter', function () {
                div.style.background = 'var(--color-hover-primary,#f0f4ff)';
                div.style.color = 'var(--color-primary,#6366f1)';
            });
            div.addEventListener('mouseleave', function () {
                div.style.background = ''; div.style.color = '';
            });
            div.addEventListener('click', function () { menu.remove(); item.fn(); });
            menu.appendChild(div);
        });

        var bd = document.getElementById('rpt-print-modal-bd');
        var menuBtn = null;
        if (bd) {
            bd.querySelectorAll('.utm-hbtn').forEach(function (b) {
                if ((b.textContent || '').trim().indexOf('Menu') !== -1) menuBtn = b;
            });
        }
        if (menuBtn) {
            var rect = menuBtn.getBoundingClientRect();
            menu.style.top  = (rect.bottom + 4) + 'px';
            menu.style.left = rect.left + 'px';
        } else {
            menu.style.top  = '120px';
            menu.style.left = '50%';
        }

        document.body.appendChild(menu);
        setTimeout(function () {
            document.addEventListener('click', function _cm(ev) {
                if (!menu.contains(ev.target)) {
                    menu.remove();
                    document.removeEventListener('click', _cm);
                }
            });
        }, 10);
    }


    /* ══════════════════════════════════════════════════════════════
    D14. ACTUAL PRINT / PREVIEW EXECUTION
    ══════════════════════════════════════════════════════════════ */

    function _printDo(reportId, preview) {
        /* Collect form values */
        var cfg = _collectPrintCfg();
        _savePrintCfg(reportId, cfg);

        /* Get rows and cols */
        var st   = global.rptGetState  ? global.rptGetState(reportId)  : null;
        var allRows = (st && st.filteredRows) ? st.filteredRows
                    : (st && st.allRows)      ? st.allRows : [];
        var cols = _getCols(reportId).filter(function (c) {
            return c.show !== false && c.type !== 'photo';
        });

        /* Determine which rows to print based on cfg.print */
        var rowsPerPage = 50;
        var printRows;

        if (cfg.print === 'Pages') {
            var fromRow = ((cfg.pageFrom || 1) - 1) * rowsPerPage;
            var toRow   =  (cfg.pageTo   || 999)    * rowsPerPage;
            printRows = allRows.slice(fromRow, toRow);
        } else {
            /* 'All' and 'Selection' (selection not yet implemented) */
            printRows = allRows;
        }

        _printModal.close();

        if (preview) {
            _showPreview(reportId, cfg, printRows, cols);
        } else {
            _execPrint(reportId, cfg, printRows, cols);
        }
    }

    function _execPrint(reportId, cfg, printRows, cols) {
        var b          = _buildPrintHtml(reportId, cfg, printRows, cols);
        var headerHtml = _buildHeaderHtml(cfg);

        /* Remove existing frame */
        var existing = document.getElementById('rpt-printable-frame');
        if (existing) existing.remove();

        /* @page orientation + margins */
        var styleId = 'rpt-print-page-style';
        var es = document.getElementById(styleId);
        if (es) es.remove();
        var topMm  = ((cfg.topMargin  || 1) * 10) + 'mm';
        var leftMm = ((cfg.leftMargin || 1) * 10) + 'mm';
        var style  = document.createElement('style');
        style.id   = styleId;
        style.textContent = [
            '@media print {',
            '  @page { size: ' + (cfg.orientation || 'Portrait') + '; ',
            '          margin: ' + topMm + ' ' + leftMm + ' ' + topMm + ' ' + leftMm + '; }',
            '  body > *:not(#rpt-printable-frame) { display: none !important; }',
            '  #rpt-printable-frame { display: block !important; position: static !important; }',
            '}',
        ].join('\n');
        document.head.appendChild(style);

        /* Line classes */
        var lineClass = 'rpt-print-lines-' + (cfg.lineStyle || 'solid').toLowerCase();
        if (!cfg.verticalLines)   lineClass += ' rpt-print-novlines';
        if (!cfg.horizontalLines) lineClass += ' rpt-print-nohlines';

        /* Footer */
        var footerHtml = '';
        if (cfg.reportFooter && cfg.reportFooterText) {
            footerHtml += '<div class="rpt-print-footer-bar">'
                + '<span>' + _esc(cfg.reportFooterText) + '</span><span></span></div>';
        }
        if (cfg.dateTime) {
            var now = new Date();
            footerHtml += '<div class="rpt-print-footer-bar">'
                + '<span></span><span>'
                + now.toLocaleDateString() + ' ' + now.toLocaleTimeString()
                + '</span></div>';
        }

        /* Copies — each copy is one full table, separated by page break */
        var copies    = Math.max(1, parseInt(cfg.noCopies, 10) || 1);
        var colsToShow = cols.filter(function (c) { return c.show !== false; });

        function _buildAllRows() {
            return printRows.map(function (row, i) {
                return '<tr><td style="text-align:center;width:32px">' + (i + 1) + '</td>'
                    + colsToShow.map(function (c) {
                        var v = row[c.key];
                        if (v === undefined || v === null) v = row[c.key.toLowerCase()] || '';
                        return '<td>' + _esc(String(v)) + '</td>';
                    }).join('') + '</tr>';
            }).join('');
        }

        function _buildOneCopy(isLast) {
            return '<div' + (!isLast ? ' style="page-break-after:always"' : '') + '>'
                + headerHtml
                + '<table class="rpt-print-tbl" style="table-layout:fixed;width:100%;border-collapse:collapse">'
                + b.colgroup
                + '<thead>' + b.thead + '</thead>'
                + '<tbody>' + _buildAllRows() + '</tbody>'
                + '</table>'
                + footerHtml
                + '</div>';
        }

        var allCopies = '';
        for (var c = 0; c < copies; c++) {
            allCopies += _buildOneCopy(c === copies - 1);
        }

        var frame = document.createElement('div');
        frame.id        = 'rpt-printable-frame';
        frame.className = lineClass;
        /* NOT display:none — must be rendered for browser to paginate correctly.
        Hidden off-screen instead so it doesn't flash on screen. */
        frame.style.cssText = 'position:absolute;left:-9999px;top:0;width:210mm;background:#fff;';
        frame.innerHTML = allCopies;
        document.body.appendChild(frame);

        setTimeout(function () {
            window.print();
            setTimeout(function () {
                var f = document.getElementById('rpt-printable-frame');
                if (f) f.remove();
                var s = document.getElementById(styleId);
                if (s) s.remove();
            }, 2000);
        }, 150);
    }
    function _buildPrintHtml(reportId, cfg, rows, cols) {
        var lineClass = '';
        if (!cfg.verticalLines)   lineClass += ' rpt-print-novlines';
        if (!cfg.horizontalLines) lineClass += ' rpt-print-nohlines';
        if (cfg.lineStyle === 'Dot')    lineClass += ' rpt-preview-table--dot-lines';
        if (cfg.lineStyle === 'Dashed') lineClass += ' rpt-preview-table--dash-lines';

        var now = new Date();
        var dateStr = now.toLocaleDateString() + ' ' + now.toLocaleTimeString();

        var colsToShow = cols.filter(function (c) { return c.show !== false; });
        var savedWidths = _lsJson('rpt_col_widths_' + reportId) || {};

        var colgroup = '<colgroup>'
            + '<col style="width:32px">'
            + colsToShow.map(function (c) {
                var w = savedWidths[c.key] || c.width;
                return '<col' + (w ? ' style="width:' + w + 'px"' : '') + '>';
            }).join('')
            + '</colgroup>';

        var thead = '<tr>'
            + '<th style="width:32px;text-align:center">#</th>'
            + colsToShow.map(function (c) {
                return '<th>' + _esc(c.label) + '</th>';
            }).join('')
            + '</tr>';

        var tbody = rows.map(function (row, i) {
            return '<tr><td style="text-align:center">' + (i + 1) + '</td>' +
                colsToShow.map(function (c) {
                    var v = row[c.key];
                    if (v === undefined || v === null) v = row[c.key.toLowerCase()] || '';
                    return '<td>' + _esc(String(v)) + '</td>';
                }).join('') + '</tr>';
        }).join('');

        return { lineClass: lineClass, colgroup: colgroup, thead: thead, tbody: tbody, dateStr: dateStr };
    }

    function _buildHeaderHtml(cfg) {
        if (cfg.printHeading === 'Header Logo' && cfg.headerImagePath) {
            return '<div class="rpt-preview-heading rpt-preview-heading--logo">' +
                '<img src="' + _esc(cfg.headerImagePath) + '" alt="Header" ' +
                'style="max-height:72px;max-width:100%;object-fit:contain">' +
                '</div>';
        }
        if (cfg.printHeading !== 'No Header' && cfg.reportHeading) {
            return '<div class="rpt-preview-heading">' + _esc(cfg.reportHeading) + '</div>';
        }
        return '';
    }

    function _showPreview(reportId, cfg, rows, cols) {
        var b = _buildPrintHtml(reportId, cfg, rows, cols);
        var isLandscape = cfg.orientation === 'Landscape';
        var headerHtml = _buildHeaderHtml(cfg);

        var overlay = document.createElement('div');
        overlay.className = 'rpt-preview-overlay';
        overlay.id = 'rpt-preview-' + reportId;
        overlay.innerHTML = [
            '<div class="rpt-preview-toolbar">',
            '<div class="rpt-preview-toolbar-title">',
            '<svg viewBox="0 0 24 24" style="width:16px;height:16px;stroke:currentColor;fill:none;stroke-width:2;stroke-linecap:round;stroke-linejoin:round"><rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/></svg>',
            'Print Preview — ' + _esc(cfg.reportHeading || reportId),
            '</div>',
            '<button class="rpt-preview-btn rpt-preview-btn--primary" onclick="rptPreviewPrint(\'' + reportId + '\')">',
            '<svg viewBox="0 0 24 24" style="width:14px;height:14px;stroke:currentColor;fill:none;stroke-width:2;stroke-linecap:round;stroke-linejoin:round"><polyline points="6 9 6 2 18 2 18 9"/><path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"/><rect x="6" y="14" width="12" height="8"/></svg>',
            ' Print</button>',
            '<button class="rpt-preview-btn" onclick="rptSaveToPdf(\'' + reportId + '\')">',
            '<svg viewBox="0 0 24 24" style="width:14px;height:14px;stroke:currentColor;fill:none;stroke-width:2;stroke-linecap:round;stroke-linejoin:round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>',
            ' Save PDF</button>',
            '<button class="rpt-preview-btn" onclick="document.getElementById(\'rpt-preview-' + reportId + '\').remove()">✕ Close</button>',
            '</div>',
            '<div class="rpt-preview-scroller">',
            '<div class="rpt-preview-page ' + (isLandscape ? 'rpt-preview-page--landscape' : 'rpt-preview-page--portrait') + '" ',
            'style="padding:' + (cfg.topMargin * 10) + 'px ' + (cfg.leftMargin * 10) + 'px 40px;">',
            headerHtml,
            '<table class="rpt-preview-table' + b.lineClass + '" style="table-layout:fixed;width:100%">',
            b.colgroup,
            '<thead>' + b.thead + '</thead>',

            '<tbody>' + b.tbody + '</tbody>',
            '</table>',
            cfg.reportFooter && cfg.reportFooterText ? ('<div class="rpt-preview-footer">' + _esc(cfg.reportFooterText) + '</div>') : '',
            cfg.dateTime ? ('<div class="rpt-preview-footer"><span></span><span>' + b.dateStr + '</span></div>') : '',
            '</div>',
            '</div>',
        ].join('');

        document.body.appendChild(overlay);
        overlay._printData = { cfg: cfg, rows: rows, cols: cols, reportId: reportId };
    }

    global.rptPreviewPrint = function (reportId) {
        var overlay = document.getElementById('rpt-preview-' + reportId);
        var data = overlay && overlay._printData;
        if (!data) return;
        overlay.remove();
        _execPrint(data.reportId, data.cfg, data.rows, data.cols);
    };


    function _doPrint(reportId, cfg, rows, cols) {
    var b = _buildPrintHtml(reportId, cfg, rows, cols);
    var headerHtml = _buildHeaderHtml(cfg);

    var existing = document.getElementById('rpt-printable-frame');
    if (existing) existing.remove();

    var copies = Math.max(1, parseInt(cfg.noCopies, 10) || 1);

    /* orientation @page rule */
    var styleId = 'rpt-print-page-style';
    var existingStyle = document.getElementById(styleId);
    if (existingStyle) existingStyle.remove();
    var style = document.createElement('style');
    style.id = styleId;
    style.textContent = '@media print { @page { size: ' + cfg.orientation + '; } }';
    document.head.appendChild(style);

    /* CSS custom properties for margins */
    document.documentElement.style.setProperty(
        '--rpt-top-margin',  (cfg.topMargin  || 1) * 10 + 'mm');
    document.documentElement.style.setProperty(
        '--rpt-left-margin', (cfg.leftMargin || 1) * 10 + 'mm');

    var lineClass = 'rpt-print-lines-' + (cfg.lineStyle || 'solid').toLowerCase();
    if (!cfg.verticalLines)   lineClass += ' rpt-print-novlines';
    if (!cfg.horizontalLines) lineClass += ' rpt-print-nohlines';

    /* Build one copy block — browser repeats across pages naturally */
    var footerHtml = '';
    if (cfg.dateTime) {
        footerHtml += '<div class="rpt-print-footer-bar">'
            + '<span></span><span>' + b.dateStr + '</span></div>';
    }
    if (cfg.reportFooter && cfg.reportFooterText) {
        footerHtml += '<div class="rpt-print-footer-bar">'
            + '<span>' + _esc(cfg.reportFooterText) + '</span></div>';
    }

    /* One <div> per copy, page-break-after:always on all but last */
    var pageHtml = '';
    for (var c = 0; c < copies; c++) {
        pageHtml += '<div style="padding:'
            + (cfg.topMargin || 1) * 10 + 'px '
            + (cfg.leftMargin || 1) * 10 + 'px 40px;">'
            + headerHtml
            + '<table class="rpt-print-tbl" style="table-layout:fixed;width:100%">'
            + b.colgroup
            + '<thead>' + b.thead + '</thead>'
            + '<tbody>' + b.tbody + '</tbody>'
            + '</table>'
            + footerHtml
            + '</div>';
    }

    var frame = document.createElement('div');
    frame.id = 'rpt-printable-frame';
    frame.className = lineClass;
    frame.style.cssText = 'display:none';
    frame.innerHTML = pageHtml;
    document.body.appendChild(frame);

    setTimeout(function () {
        window.print();
        setTimeout(function () {
            var f = document.getElementById('rpt-printable-frame');
            if (f) f.remove();
            var s = document.getElementById(styleId);
            if (s) s.remove();
        }, 1500);
    }, 100);
}


    /* ══════════════════════════════════════════════════════════════
       E. SAVE TO PDF
    ══════════════════════════════════════════════════════════════ */

    global.rptSaveToPdf = function (reportId) {
        var prev = document.getElementById('rpt-preview-' + reportId);
        if (prev) prev.remove();

        var cfg  = _getPrintCfg(reportId);
        var st   = global.rptGetState ? global.rptGetState(reportId) : null;
        var rows = (st && st.filteredRows) ? st.filteredRows
                : (st && st.allRows)      ? st.allRows : [];
        var cols = _getCols(reportId).filter(function (c) {
            return c.show !== false && c.type !== 'photo';
        });

        var overlay = document.createElement('div');
        overlay.style.cssText =
            'position:fixed;inset:0;background:rgba(0,0,0,.65);z-index:9000;' +
            'display:flex;align-items:center;justify-content:center;';
        overlay.innerHTML = '<div style="background:var(--color-bg-card,#fff);border-radius:10px;' +
            'padding:32px 40px;max-width:400px;text-align:center;box-shadow:0 8px 32px rgba(0,0,0,.35);' +
            'font-family:DM Sans,sans-serif;">' +
            '<h3 style="margin:0 0 8px;font-size:16px">Save as PDF</h3>' +
            '<p style="margin:0 0 16px;font-size:13px;line-height:1.5">Set <strong>Destination</strong> ' +
            'to <strong>"Save as PDF"</strong> and click Save.</p>' +
            '<p style="font-size:11px;color:#888">Opening print dialog in 1 second…</p></div>';
        document.body.appendChild(overlay);

        setTimeout(function () {
            overlay.remove();
            _execPrint(reportId, cfg, rows, cols);
        }, 1200);
    };


    /* ══════════════════════════════════════════════════════════════
       F. HTML EXPORT
    ══════════════════════════════════════════════════════════════ */

    function _exportHtml(reportId) {
        var cfg = _getPrintCfg(reportId);
        var st = global.rptGetState ? global.rptGetState(reportId) : null;
        var rows = (st && st.filteredRows) ? st.filteredRows : ((st && st.allRows) ? st.allRows : []);
        var cols = _getCols(reportId).filter(function (c) { return c.show !== false && c.type !== 'photo'; });
        var b = _buildPrintHtml(reportId, cfg, rows, cols);
        var headerHtml = _buildHeaderHtml(cfg);

        var html = '<!DOCTYPE html><html><head><meta charset="UTF-8"><title>' + _esc(cfg.reportHeading || reportId) + '</title>' +
            '<style>body{font-family:Calibri,sans-serif;font-size:12px;margin:20px}' +
            'table{width:100%;border-collapse:collapse}th,td{border:1px solid #999;padding:4px 8px;text-align:left}' +
            'th{background:#e0e0e0;font-weight:700}tr:nth-child(even)td{background:#f9f9f9}</style></head><body>' +
            (headerHtml || (cfg.reportHeading ? '<h2 style="text-align:center;border-bottom:2px solid #000;padding-bottom:6px">' + _esc(cfg.reportHeading) + '</h2>' : '')) +
            '<table><thead>' + b.thead + '</thead><tbody>' + b.tbody + '</tbody></table>' +
            (cfg.dateTime ? '<p style="text-align:right;font-size:10px;color:#888">' + b.dateStr + '</p>' : '') +
            '</body></html>';

        var blob = new Blob([html], { type: 'text/html' });
        var a = document.createElement('a');
        a.href = URL.createObjectURL(blob);
        a.download = (reportId || 'report') + '.html';
        a.click();
        setTimeout(function () { URL.revokeObjectURL(a.href); }, 1000);
    }


    /* ══════════════════════════════════════════════════════════════
       G. AUTO-LOAD LAST STYLE ON FILTER MODAL OPEN
    ══════════════════════════════════════════════════════════════ */
    (function _patchFilterOpen() {
        var _orig = global.rptOpenFilterModal;
        global.rptOpenFilterModal = function (reportId) {
            if (typeof _orig === 'function') _orig.call(this, reportId);
            setTimeout(function () {
                var styleSel = document.getElementById('rptf-report-style');
                if (styleSel) {
                    var last = global.rptGetLastStyle(reportId);
                    if (last) {
                        for (var i = 0; i < styleSel.options.length; i++) {
                            if (styleSel.options[i].value === last) {
                                styleSel.value = last;
                                if (typeof global.pfSelSetValue === 'function') {
                                    global.pfSelSetValue('rptf-report-style', last);
                                }
                                break;
                            }
                        }
                    }
                }
            }, 350);
        };
    })();


    /* ══════════════════════════════════════════════════════════════
       H. PATCH "Default" BUTTON IN REPORT VIEW TOOLBAR
    ══════════════════════════════════════════════════════════════ */
    (function _patchDefault() {
        global.rptReportDefault = function (reportId) {
            global.rptLoadDefaultFields(reportId);
        };
    })();


    /* ══════════════════════════════════════════════════════════════
       I. PATCH REPORT VIEW TOOLBAR
    ══════════════════════════════════════════════════════════════ */
    (function _patchReportPrint() {
        global.rptReportPrint = function (reportId) {
            global.rptPrintReport(reportId);
        };
    })();

    (function _patchReportView() {
        var _origShow = global.rptShowReportView;
        global.rptShowReportView = function (reportId, rows, cols) {
            if (typeof _origShow === 'function') _origShow.apply(this, arguments);
            setTimeout(function () {
                var toolbar = document.querySelector('#rpt-report-view-' + reportId + ' .rpt-report-toolbar');
                if (!toolbar) return;
                if (toolbar.querySelector('[data-design-btn]')) return;

                var designBtn = document.createElement('button');
                designBtn.className = 'rpt-tb-btn';
                designBtn.setAttribute('data-design-btn', '1');
                designBtn.title = 'Report Design';
                designBtn.innerHTML =
                    '<svg viewBox="0 0 24 24"><line x1="3" y1="12" x2="21" y2="12"/>' +
                    '<line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="18" x2="21" y2="18"/></svg>' +
                    'Report Design';
                designBtn.onclick = function () { global.rptDesignReport(reportId); };

                var sep = document.createElement('div');
                sep.className = 'rpt-tb-sep';

                var savePdfBtn = document.createElement('button');
                savePdfBtn.className = 'rpt-tb-btn';
                savePdfBtn.title = 'Save to PDF';
                savePdfBtn.innerHTML =
                    '<svg viewBox="0 0 24 24"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>' +
                    '<polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/>' +
                    '<line x1="16" y1="17" x2="8" y2="17"/></svg>Save PDF';
                savePdfBtn.onclick = function () { global.rptSaveToPdf(reportId); };

                var menuArrow = toolbar.querySelector('.rpt-tb-menu-arrow');
                if (menuArrow) {
                    toolbar.insertBefore(savePdfBtn, menuArrow);
                    toolbar.insertBefore(sep.cloneNode(), menuArrow);
                    toolbar.insertBefore(designBtn, menuArrow);
                    toolbar.insertBefore(sep, menuArrow);
                } else {
                    toolbar.appendChild(sep);
                    toolbar.appendChild(designBtn);
                    toolbar.appendChild(sep.cloneNode());
                    toolbar.appendChild(savePdfBtn);
                }
            }, 80);
        };
    })();

})(window);