/**
 * ════════════════════════════════════════════════════════════════════
 *  common/static/common/js/rpt.js   v3.0
 *
 *  Changes from v2.0:
 *  - Removed left filter panel logic entirely
 *  - Search: supports per-field searching via rpt-search-field-btn dropdown
 *  - Pagination: arrow-only compact style, hidden when all fits on one page
 *  - Filter modal: see rpt_filter.js (loaded separately)
 * ════════════════════════════════════════════════════════════════════
 */

(function () {
    'use strict';

    var _state = {};

    /* ── Init ──────────────────────────────────────────────────── */
    window.rptInit = function (id) {
        var cfg  = (window._rptConfig || {})[id];
        var rows = (window._rptRows   || {})[id] || [];
        if (!cfg) return;

        _state[id] = {
            allRows      : rows,
            filteredRows : rows,
            currentPage  : 1,
            activeFilters: {},   // field → value (from left panel — kept for filter modal)
            modalFilters : [],   // [{field, value, operator}] from filter modal
            sortCol      : null,
            sortDir      : 'asc',
            view         : cfg.defaultView || 'tiles',
            searchTimer  : null,
            searchField  : '',   // '' = all fields
        };

        _bindSearch(id, cfg);
        _bindSort(id, cfg);
        _bindSearchDropClose(id);
        _render(id, cfg);
    };

    window.rptSetRows = function (id, rows) {
        var cfg = (window._rptConfig || {})[id];
        if (!cfg || !_state[id]) return;
        _state[id].allRows       = rows || [];
        _state[id].filteredRows  = rows || [];
        _state[id].currentPage   = 1;
        _state[id].activeFilters = {};
        _state[id].modalFilters  = [];
        _render(id, cfg);
    };

    /* ── Switch view ───────────────────────────────────────────── */
    window.rptSetView = function (id, view, btnEl) {
        var cfg = (window._rptConfig || {})[id];
        if (!cfg || !_state[id]) return;
        _state[id].view = view;
        var container = document.getElementById('rpt-views-' + id);
        if (container) container.querySelectorAll('.rpt-view-btn').forEach(function (b) { b.classList.remove('active'); });
        if (btnEl) btnEl.classList.add('active');
        var page = document.getElementById('rpt-' + id);
        if (page) page.querySelectorAll('.rpt-view').forEach(function (v) { v.classList.remove('active'); });
        var target = document.getElementById('rpt-' + view + '-' + id);
        if (target) target.classList.add('active');
        _render(id, cfg);
    };

    /* ── Search field selector ─────────────────────────────────── */
    window.rptToggleSearchDrop = function (id) {
        var drop = document.getElementById('rpt-search-drop-' + id);
        if (!drop) return;
        var visible = drop.style.display !== 'none';
        // Close all other dropdowns
        document.querySelectorAll('.rpt-search-drop').forEach(function (d) { d.style.display = 'none'; });
        drop.style.display = visible ? 'none' : 'block';
    };

    window.rptSetSearchField = function (id, fieldKey, fieldLabel, el) {
        var cfg = (window._rptConfig || {})[id];
        if (!cfg || !_state[id]) return;
        _state[id].searchField = fieldKey;

        // Update button label
        var lbl = document.getElementById('rpt-search-field-label-' + id);
        if (lbl) lbl.textContent = fieldLabel || 'All';

        // Update active class in dropdown
        var drop = document.getElementById('rpt-search-drop-' + id);
        if (drop) drop.querySelectorAll('.rpt-search-drop-item').forEach(function (it) {
            it.classList.toggle('active', it === el);
        });

        // Close dropdown
        drop.style.display = 'none';

        // Re-run search with new field
        var input = document.getElementById('rpt-search-' + id);
        var q = input ? input.value.trim() : '';
        _localSearch(id, cfg, q);
    };

    function _bindSearchDropClose(id) {
        document.addEventListener('click', function (e) {
            var wrap = document.getElementById('rpt-search-wrap-' + id);
            var drop = document.getElementById('rpt-search-drop-' + id);
            if (wrap && drop && !wrap.contains(e.target)) {
                drop.style.display = 'none';
            }
        });
    }

    /* ── Search ────────────────────────────────────────────────── */
    function _bindSearch(id, cfg) {
        var input = document.getElementById('rpt-search-' + id);
        if (!input) return;
        input.addEventListener('input', function () {
            clearTimeout(_state[id].searchTimer);
            var q = input.value.trim();
            _state[id].searchTimer = setTimeout(function () {
                var field = _state[id].searchField || '';
                if (cfg.searchUrl && q.length > 0 && !field) {
                    _ajaxSearch(id, cfg, q);
                } else {
                    _localSearch(id, cfg, q);
                }
            }, 300);
        });
    }

    function _localSearch(id, cfg, q) {
        var st    = _state[id];
        var field = st.searchField || '';
        // Start from modal-filtered rows if active, else all
        var base  = _getModalFilteredRows(id);

        if (!q) {
            st.filteredRows = base;
        } else {
            var ql = q.toLowerCase();
            if (field) {
                st.filteredRows = base.filter(function (row) {
                    var v = row[field];
                    return v && String(v).toLowerCase().indexOf(ql) !== -1;
                });
            } else {
                st.filteredRows = base.filter(function (row) {
                    return Object.values(row).some(function (v) {
                        return v && String(v).toLowerCase().indexOf(ql) !== -1;
                    });
                });
            }
        }
        st.currentPage = 1;
        _render(id, cfg);
    }

    function _ajaxSearch(id, cfg, q) {
        fetch(cfg.searchUrl + '?q=' + encodeURIComponent(q))
            .then(function (r) { return r.json(); })
            .then(function (d) {
                if (d.success) { _state[id].filteredRows = d.results || []; _state[id].currentPage = 1; _render(id, cfg); }
            })
            .catch(function () { _localSearch(id, cfg, q); });
    }

    /* ── Modal filter rows application ─────────────────────────── */
    function _getModalFilteredRows(id) {
        var st = _state[id];
        var filters = (st.modalFilters || []).filter(function (f) {
            return f.field && (f.value !== '' && f.value !== undefined && f.value !== null);
        });
        if (!filters.length) return st.allRows;

        return st.allRows.filter(function (row) {
            var result = true;
            filters.forEach(function (f, i) {
                var rowVal = String(row[f.field] || '').toLowerCase();
                var fVal   = String(f.value || '').toLowerCase();
                var match  = rowVal.indexOf(fVal) !== -1;
                if (i === 0) {
                    result = match;
                } else {
                    if (f.operator === 1) { result = result || match; }  // OR
                    else                  { result = result && match; }  // AND
                }
            });
            return result;
        });
    }

    /* ── Apply modal filters (called from rpt_filter.js) ──────── */
    window.rptApplyModalFilters = function (id, filterRows) {
        var cfg = (window._rptConfig || {})[id];
        if (!cfg || !_state[id]) return;
        _state[id].modalFilters = filterRows || [];
        _state[id].currentPage  = 1;

        var hasFilters = filterRows && filterRows.some(function (f) {
            return f.field && f.value !== '' && f.value !== undefined;
        });

        var badge = document.getElementById('rpt-filter-active-' + id);
        var btn   = document.getElementById('rpt-filter-btn-' + id);
        if (badge) badge.style.display = hasFilters ? 'inline-flex' : 'none';
        if (btn)   btn.classList.toggle('rpt-filter-btn--active', hasFilters);

        // Re-run current search against new modal-filtered base
        var input = document.getElementById('rpt-search-' + id);
        var q = input ? input.value.trim() : '';
        _localSearch(id, cfg, q);
    };

    window.rptClearFilter = function (id) {
        rptApplyModalFilters(id, []);
    };

    /* ── Sort ──────────────────────────────────────────────────── */
    function _bindSort(id, cfg) {
        ['rpt-list-tbl-' + id, 'rpt-grid-tbl-' + id].forEach(function (tid) {
            var tbl = document.getElementById(tid);
            if (!tbl) return;
            tbl.querySelector('thead').addEventListener('click', function (e) {
                var th = e.target.closest('th[data-col]');
                if (!th) return;
                var col = th.dataset.col;
                var st  = _state[id];
                st.sortDir = (st.sortCol === col && st.sortDir === 'asc') ? 'desc' : 'asc';
                st.sortCol = col;
                st.filteredRows.sort(function (a, b) {
                    var av = String(a[col] || '').toLowerCase();
                    var bv = String(b[col] || '').toLowerCase();
                    return (av < bv ? -1 : av > bv ? 1 : 0) * (st.sortDir === 'asc' ? 1 : -1);
                });
                st.currentPage = 1;
                _render(id, cfg);
            });
        });
    }

    function _updateSortArrows(id, tblId, visCols, offset) {
        var tbl = document.getElementById(tblId);
        if (!tbl) return;
        var st = _state[id];
        tbl.querySelectorAll('thead th[data-col]').forEach(function (th) {
            var arrow = th.querySelector('.rpt-sort-arrow');
            if (!arrow) {
                arrow = document.createElement('span');
                arrow.className = 'rpt-sort-arrow';
                arrow.style.cssText = 'font-size:10px;opacity:0.7;margin-left:3px';
                th.appendChild(arrow);
            }
            if (th.dataset.col === st.sortCol) {
                arrow.textContent = st.sortDir === 'asc' ? ' ▲' : ' ▼';
            } else {
                arrow.textContent = '';
            }
        });
    }

    /* ── Master render ─────────────────────────────────────────── */
    function _render(id, cfg) {
        var st   = _state[id];
        var rows = _paginate(st.filteredRows, st.currentPage, cfg.pageSize || 24);
        var countEl = document.getElementById('rpt-count-' + id);
        if (countEl) countEl.textContent = st.filteredRows.length + ' record' + (st.filteredRows.length !== 1 ? 's' : '');
        if      (st.view === 'tiles') _renderTiles(id, cfg, rows);
        else if (st.view === 'list')  _renderList(id, cfg, rows);
        else if (st.view === 'grid')  _renderGrid(id, cfg, rows);
        _renderPagination(id, cfg);
    }

    function _calcPageSize(rid) {
        var main = document.getElementById('rpt-main-' + rid);
        if (!main) return 24;
        var mainH     = main.clientHeight;
        var statsbar  = document.getElementById('rpt-stats-' + rid);
        var pager     = document.getElementById('rpt-pager-' + rid);
        var statsH    = statsbar ? statsbar.offsetHeight : 36;
        var pagerH    = pager    ? pager.offsetHeight    : 44;
        var theadEl   = main.querySelector('thead');
        var theadH    = theadEl  ? theadEl.offsetHeight  : 36;
        var available = mainH - statsH - pagerH - theadH - 4; /* 4px buffer */
        var rowH      = 38; /* matches td padding: 9px top + 9px bottom + ~20px content */
        return Math.max(10, Math.floor(available / rowH));
    }

    /* ── TILES ─────────────────────────────────────────────────── */
    function _renderTiles(id, cfg, rows) {
    var container = document.getElementById('rpt-tiles-body-' + id);
    if (!container) return;
    if (!rows.length) { container.innerHTML = _emptyHtml(); return; }
    var t = cfg.tile || {};

    container.innerHTML = rows.map(function (row) {
        var pk    = row[t.pkField || 'id'] || '';
        var url   = t.clickUrl ? t.clickUrl.replace('{id}', encodeURIComponent(pk)) : '#';
        var photo = row[t.photoField || 'photo'] || '';
        var name  = _esc(row[t.titleField || 'name'] || '—');
        var desig = _esc(row[t.sub1Field || ''] || '');
        var dept  = _esc(row['department'] || row[t.sub2Field || ''] || '');
        var email = row['email'] || '';
        var mobile= row['mobile'] || '';

        // Photo column
        var photoHtml;
        if (photo) {
            var src = (cfg.serveUrl || '/common/docs/serve/') + '?path=' + encodeURIComponent(photo);
            photoHtml = '<div class="rpt-tile-photo" style="background-image:url(\'' + _esc(src) + '\')">'
                      + '<img src="' + _esc(src) + '" alt="" style="display:none" '
                      + 'onerror="var p=this.parentNode;if(p){p.style.backgroundImage=\'\';p.classList.add(\'rpt-tile-photo--nophoto\');}">'
                      + '</div>';
        } else {
            photoHtml = '<div class="rpt-tile-photo rpt-tile-photo--nophoto"></div>';
        }

        // Badge
        var badgeHtml = '';
        (t.badges || []).forEach(function (key) {
            var val = row[key];
            if (val) badgeHtml += _badgeHtml(val);
        });

        // Meta rows (email, mobile)
        var metaHtml = '';
        if (email) {
            metaHtml += '<div class="rpt-tile-meta-row">'
                      + '<svg class="rpt-tile-meta-icon" viewBox="0 0 24 24"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/></svg>'
                      + '<a href="mailto:' + _esc(email) + '" onclick="event.stopPropagation()">' + _esc(email) + '</a>'
                      + '</div>';
        }
        if (mobile) {
            metaHtml += '<div class="rpt-tile-meta-row">'
                      + '<svg class="rpt-tile-meta-icon" viewBox="0 0 24 24"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07A19.5 19.5 0 0 1 4.69 12 19.79 19.79 0 0 1 1.61 3.4 2 2 0 0 1 3.6 1.22h3a2 2 0 0 1 2 1.72c.127.96.361 1.903.7 2.81a2 2 0 0 1-.45 2.11L7.91 8.91A16 16 0 0 0 14 14.91l.9-.9a2 2 0 0 1 2.11-.45c.907.339 1.85.573 2.81.7A2 2 0 0 1 22 16.92z"/></svg>'
                      + '<a href="tel:' + _esc(mobile) + '" onclick="event.stopPropagation()">' + _esc(mobile) + '</a>'
                      + '</div>';
        }

        return '<div class="rpt-tile" onclick="window.location.href=\'' + _esc(url) + '\'">'
             +   photoHtml
             +   '<div class="rpt-tile-body">'
             +     '<div class="rpt-tile-name">' + name + '</div>'
             +     (desig ? '<div class="rpt-tile-desig">' + desig + '</div>' : '')
             +     (dept  ? '<div class="rpt-tile-dept">'  + dept  + '</div>' : '')
             +     (metaHtml ? '<div class="rpt-tile-meta">' + metaHtml + '</div>' : '')
             +     (badgeHtml ? '<div class="rpt-tile-footer"><div class="rpt-tile-badges">' + badgeHtml + '</div></div>' : '')
             +   '</div>'
             + '</div>';
    }).join('');
}

    function _iconBtn(href, svgHtml, label, title) {
        var isAction = href !== '#';
        var tag = isAction ? 'a href="' + href + '"' : 'span';
        var endTag = isAction ? 'a' : 'span';
        return '<' + tag + ' class="rpt-tile-icon-btn" title="' + title + '" onclick="event.stopPropagation()">'
             +   svgHtml
             + '</' + endTag + '>';
    }

    /* ── LIST ──────────────────────────────────────────────────────────── */
    function _renderList(id, cfg, rows) {
        var tbody = document.getElementById('rpt-list-body-' + id);
        if (!tbody) return;
        var visCols = (cfg.cols || []).filter(function (c) { return c.type !== 'photo'; });
        if (!rows.length) {
            tbody.innerHTML = '<tr><td colspan="' + (visCols.length + 1) + '" style="padding:40px;text-align:center;color:var(--color-text-tertiary);font-style:italic">No records found.</td></tr>';
            return;
        }
       var st = _state[id] || {};
        var groupKeys = (st.groupKeys && st.groupKeys.length) ? st.groupKeys : (st.groupKey ? [st.groupKey] : []);
 
        /* Sort rows by composite group key combination before rendering */
        if (groupKeys.length) {
            rows = rows.slice().sort(function (a, b) {
                for (var ki = 0; ki < groupKeys.length; ki++) {
                    var k  = groupKeys[ki];
                    var av = String(a[k] !== undefined && a[k] !== null ? a[k] : '').toLowerCase();
                    var bv = String(b[k] !== undefined && b[k] !== null ? b[k] : '').toLowerCase();
                    if (av < bv) return -1;
                    if (av > bv) return  1;
                }
                return 0;
            });
        }
 
        var lastGroupVal;
        var html = '';
        rows.forEach(function (row) {
            /* group header */
            if (groupKeys.length) {
                var gStr = groupKeys.map(function (k) {
                    var gCol = visCols.find(function (c) { return c.key === k; });
                    var lbl  = gCol ? gCol.label : (k.charAt(0).toUpperCase() + k.slice(1).replace(/_/g, ' '));
                    var gv   = String(row[k] !== undefined && row[k] !== null ? row[k] : '');
                    return _esc(lbl) + ': ' + _esc(gv || '—');
                }).join(' | ');
                if (gStr !== lastGroupVal) {
                    lastGroupVal = gStr;
                    html += '<tr style="background:var(--color-primary,#8b0000);color:#fff;pointer-events:none">' +
                        '<td colspan="' + (visCols.length + 1) + '" ' +
                        'style="padding:5px 10px;font-weight:700;font-size:12px">' +
                        gStr + '</td></tr>';
                }
            }
 
            var url = _getUrl(row, cfg);
            var cells = visCols.map(function (col) {
                var styles = [];
                if (col.color) styles.push('background:' + col.color);
                if (col.textColor) styles.push('color:' + col.textColor);
                var styleAttr = styles.length ? ' style="' + styles.join(';') + '"' : '';
                return '<td' + (col.bold ? ' class="rpt-cell-bold"' : '') + styleAttr + '>' + _cellHtml(row[col.key], col) + '</td>';
            }).join('');
            html += '<tr onclick="window.location.href=\'' + _esc(url) + '\'">' + cells + '</tr>';
        });
        tbody.innerHTML = html;
        var tbl = document.getElementById('rpt-list-tbl-' + id);
        if (tbl) {
            /* Apply saved column widths via colgroup */
            var savedWidths = {};
            try { savedWidths = JSON.parse(localStorage.getItem('rpt_col_widths_' + id) || '{}'); } catch(e) {}
            var cg = tbl.querySelector('colgroup');
            if (!cg) { cg = document.createElement('colgroup'); tbl.insertBefore(cg, tbl.firstChild); }
            cg.innerHTML = '';
            visCols.forEach(function (col) {
                var c = document.createElement('col');
                var w = savedWidths[col.key] || col.width;
                if (w) c.style.width = w + 'px';
                cg.appendChild(c);
            });
            /* action column — no fixed width */
            cg.appendChild(document.createElement('col'));

            tbl.querySelectorAll('thead th').forEach(function (th, i) {
                if (visCols[i]) { th.dataset.col = visCols[i].key; th.style.cursor = 'pointer'; }
            });
            _updateSortArrows(id, 'rpt-list-tbl-' + id, visCols, 0);
        }
    }

    /* ── GRID ──────────────────────────────────────────────────── */
    /* ── GRID ──────────────────────────────────────────────────────────── */
    function _renderGrid(id, cfg, rows) {
        var tbody = document.getElementById('rpt-grid-body-' + id);
        if (!tbody) return;
        var t       = cfg.tile || {};
        var visCols = (cfg.cols || []).filter(function (c) { return c.type !== 'photo'; });
        if (!rows.length) {
            tbody.innerHTML = '<tr><td colspan="' + (visCols.length + 2) + '" style="padding:40px;text-align:center;color:var(--color-text-tertiary);font-style:italic">No records found.</td></tr>';
            return;
        }
        var st = _state[id] || {};
        var groupKeys = (st.groupKeys && st.groupKeys.length) ? st.groupKeys : (st.groupKey ? [st.groupKey] : []);
 
        /* Sort rows by composite group key combination before rendering */
        if (groupKeys.length) {
            rows = rows.slice().sort(function (a, b) {
                for (var ki = 0; ki < groupKeys.length; ki++) {
                    var k  = groupKeys[ki];
                    var av = String(a[k] !== undefined && a[k] !== null ? a[k] : '').toLowerCase();
                    var bv = String(b[k] !== undefined && b[k] !== null ? b[k] : '').toLowerCase();
                    if (av < bv) return -1;
                    if (av > bv) return  1;
                }
                return 0;
            });
        }
 
        var lastGroupVal;
        var html = '';
        rows.forEach(function (row) {
            /* group header */
            if (groupKeys.length) {
                var gStr = groupKeys.map(function (k) {
                    var gCol = visCols.find(function (c) { return c.key === k; });
                    var lbl  = gCol ? gCol.label : (k.charAt(0).toUpperCase() + k.slice(1).replace(/_/g, ' '));
                    var gv   = String(row[k] !== undefined && row[k] !== null ? row[k] : '');
                    return _esc(lbl) + ': ' + _esc(gv || '—');
                }).join(' | ');
                if (gStr !== lastGroupVal) {
                    lastGroupVal = gStr;
                    html += '<tr style="background:var(--color-primary,#8b0000);color:#fff;pointer-events:none">' +
                        '<td colspan="' + (visCols.length + 2) + '" ' +
                        'style="padding:5px 10px;font-weight:700;font-size:12px">' +
                        gStr + '</td></tr>';
                }
            }
 
            var url   = _getUrl(row, cfg);
            var photo = row[t.photoField || 'photo'] || '';
            var avatarHtml;
            if (photo) {
                var src = (cfg.serveUrl || '/common/docs/serve/') + '?path=' + encodeURIComponent(photo);
                avatarHtml = '<div class="rpt-grid-avatar">'
                           + '<img src="' + _esc(src) + '" alt="" style="display:none" '
                           + 'onload="this.style.display=\'block\';var s=this.nextElementSibling;if(s)s.style.display=\'none\';" '
                           + 'onerror="this.style.display=\'none\';var s=this.nextElementSibling;if(s)s.style.display=\'flex\';">'
                           + '<svg style="display:flex" viewBox="0 0 24 24"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>'
                           + '</div>';
            } else {
                avatarHtml = '<div class="rpt-grid-avatar"><svg viewBox="0 0 24 24"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg></div>';
            }
            var cells = visCols.map(function (col) {
                var styles = [];
                if (col.color) styles.push('background:' + col.color);
                if (col.textColor) styles.push('color:' + col.textColor);
                var styleAttr = styles.length ? ' style="' + styles.join(';') + '"' : '';
                return '<td' + (col.bold ? ' class="rpt-cell-bold"' : '') + styleAttr + '>' + _cellHtml(row[col.key], col) + '</td>';
            }).join('');
            html += '<tr onclick="window.location.href=\'' + _esc(url) + '\'">'
                 + '<td>' + avatarHtml + '</td>' + cells + '</tr>';
        });
        tbody.innerHTML = html;
        var tbl = document.getElementById('rpt-grid-tbl-' + id);
        if (tbl) {
            var savedWidths = {};
            try { savedWidths = JSON.parse(localStorage.getItem('rpt_col_widths_' + id) || '{}'); } catch(e) {}
            var cg = tbl.querySelector('colgroup');
            if (!cg) { cg = document.createElement('colgroup'); tbl.insertBefore(cg, tbl.firstChild); }
            cg.innerHTML = '';
            /* avatar column */
            var avatarCol = document.createElement('col');
            avatarCol.style.width = '44px';
            cg.appendChild(avatarCol);
            visCols.forEach(function (col) {
                var c = document.createElement('col');
                var w = savedWidths[col.key] || col.width;
                if (w) c.style.width = w + 'px';
                cg.appendChild(c);
            });
            cg.appendChild(document.createElement('col'));

            tbl.querySelectorAll('thead th').forEach(function (th, i) {
                if (i > 0 && visCols[i - 1]) { th.dataset.col = visCols[i - 1].key; th.style.cursor = 'pointer'; }
            });
            _updateSortArrows(id, 'rpt-grid-tbl-' + id, visCols, 1);
        }
    }

    /* ── Pagination — arrow-only compact, hidden if 1 page ─────── */
    function _renderPagination(id, cfg) {
        var st    = _state[id];
        var total = st.filteredRows.length;
        var ps    = cfg.pageSize || 24;
        var pages = Math.ceil(total / ps);
        var pager = document.getElementById('rpt-pager-' + id);
        if (!pager) return;

        // Hide completely if everything fits on one page
        if (pages <= 1) { pager.innerHTML = ''; pager.style.display = 'none'; return; }
        pager.style.display = 'flex';

        var cp   = st.currentPage;
        var html = '';

        // Prev arrow
        html += '<button type="button" class="rpt-page-arrow" '
              + (cp > 1 ? 'onclick="rptGoPage(\'' + id + '\',' + (cp-1) + ')"' : 'disabled')
              + ' title="Previous">'
              + '<svg viewBox="0 0 24 24"><polyline points="15 18 9 12 15 6"/></svg>'
              + '</button>';

        // Page numbers — compact: show first, last, current±1, ellipsis
        for (var i = 1; i <= pages; i++) {
            if (i === 1 || i === pages || (i >= cp - 1 && i <= cp + 1)) {
                html += '<button type="button" class="rpt-page-btn' + (i === cp ? ' active' : '') + '" '
                      + 'onclick="rptGoPage(\'' + id + '\',' + i + ')">' + i + '</button>';
            } else if (i === cp - 2 || i === cp + 2) {
                html += '<span class="rpt-page-ellipsis">…</span>';
            }
        }

        // Next arrow
        html += '<button type="button" class="rpt-page-arrow" '
              + (cp < pages ? 'onclick="rptGoPage(\'' + id + '\',' + (cp+1) + ')"' : 'disabled')
              + ' title="Next">'
              + '<svg viewBox="0 0 24 24"><polyline points="9 18 15 12 9 6"/></svg>'
              + '</button>';

        // Info
        html += '<span class="rpt-page-info">'
              + ((cp-1)*ps+1) + '–' + Math.min(cp*ps, total) + ' / ' + total
              + '</span>';

        pager.innerHTML = html;
    }

    window.rptGoPage = function (id, page) {
        var cfg = (window._rptConfig || {})[id];
        if (!cfg || !_state[id]) return;
        _state[id].currentPage = page;
        _render(id, cfg);
        var main = document.getElementById('rpt-main-' + id);
        if (main) main.scrollTop = 0;
    };

    /* ── Expose state getter for filter modal ───────────────────── */
    window.rptGetState = function (id) { return _state[id] || null; };
    window.rptGetConfig = function (id) { return (window._rptConfig || {})[id] || null; };

    /* ── SVG icons ─────────────────────────────────────────────── */
    function _svgEmail() {
        return '<svg viewBox="0 0 24 24"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/></svg>';
    }
    function _svgPhone() {
        return '<svg viewBox="0 0 24 24"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07A19.5 19.5 0 0 1 4.69 12 19.79 19.79 0 0 1 1.61 3.4 2 2 0 0 1 3.6 1.22h3a2 2 0 0 1 2 1.72c.127.96.361 1.903.7 2.81a2 2 0 0 1-.45 2.11L7.91 8.91A16 16 0 0 0 14 14.91l.9-.9a2 2 0 0 1 2.11-.45c.907.339 1.85.573 2.81.7A2 2 0 0 1 22 16.92z"/></svg>';
    }
    function _svgPhone2() {
        return '<svg viewBox="0 0 24 24"><rect x="5" y="2" width="14" height="20" rx="2" ry="2"/><line x1="12" y1="18" x2="12.01" y2="18"/></svg>';
    }
    function _svgPerson() {
        return '<svg viewBox="0 0 24 24"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>';
    }

    /* ── Helpers ───────────────────────────────────────────────── */
    function _paginate(rows, page, size) { return rows.slice((page-1)*size, page*size); }

    function _getPk(row, cfg) {
        var t = cfg.tile || {};
        return row[t.pkField || 'id'] || row['reg_no'] || row['id'] || '';
    }
    function _getUrl(row, cfg) {
        var t = cfg.tile || {};
        if (!t.clickUrl) return '#';
        return t.clickUrl.replace('{id}', encodeURIComponent(_getPk(row, cfg)));
    }

    function _cellHtml(val, col) {
        if (val === null || val === undefined || val === '') return '<span class="rpt-cell-muted">—</span>';
        var type = col.type || 'text';
        if (type === 'badge')  return _badgeHtml(val);
        if (type === 'email')  return '<a href="mailto:' + _esc(val) + '" onclick="event.stopPropagation()" style="color:var(--color-primary)">' + _esc(val) + '</a>';
        if (type === 'tel')    return '<a href="tel:' + _esc(val) + '" onclick="event.stopPropagation()">' + _esc(val) + '</a>';
        return _esc(val);
    }

    function _badgeHtml(val) {
        if (!val && val !== 0) return '';
        var cls = 'rpt-badge rpt-badge--' + String(val).toLowerCase().replace(/\s+/g, '-');
        return '<span class="' + cls + '">' + _esc(val) + '</span>';
    }

    function _emptyHtml() {
        return '<div class="rpt-empty" style="grid-column:1/-1">'
             + '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><line x1="8" y1="15" x2="16" y2="15"/>'
             + '<line x1="9" y1="9" x2="9.01" y2="9"/><line x1="15" y1="9" x2="15.01" y2="9"/></svg>'
             + '<span>No records found</span></div>';
    }

    function _esc(s) {
        return String(s || '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/'/g,'&#39;');
    }

}());