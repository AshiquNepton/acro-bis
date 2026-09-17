/* common/static/common/js/group_setup.js */
(function () {
    'use strict';

    var DEL_ICON = (
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" ' +
        'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">' +
        '<polyline points="3 6 5 6 21 6"/>' +
        '<path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/>' +
        '<path d="M10 11v6"/><path d="M14 11v6"/>' +
        '<path d="M9 6V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2"/>' +
        '</svg>'
    );

    var catId   = '';
    var rows    = [];
    var tempId  = -1;
    var _dirty  = false;   // tracks any edit, add, delete

    /* ── Init ──────────────────────────────────────────────── */
    document.addEventListener('DOMContentLoaded', function () {
        var first = document.querySelector('.gs-cat-item.active');
        if (first) { catId = first.dataset.id; gsLoad(); }
        document.addEventListener('keydown', function (e) {
            if ((e.ctrlKey || e.metaKey) && e.key === 's') {
                e.preventDefault(); gsSave();
            }
        });
    });

    /* ── Category select ───────────────────────────────────── */
    window.gsSelectCat = function (el, id) {
        document.querySelectorAll('.gs-cat-item').forEach(function (e) {
            e.classList.remove('active');
        });
        el.classList.add('active');
        catId = id;

        // Clear grid instantly for a snappier feel
        rows = [];
        gsRender(false);

        gsLoad();
    };

    /* ── Load ──────────────────────────────────────────────── */
    function gsLoad(focusNew) {
        gsStatus('');
        fetch(window.GS.loadUrl + '?category=' + encodeURIComponent(catId))
            .then(function (r) { return r.json(); })
            .then(function (d) {
                rows = (d.success ? d.rows : []).map(function (r) {
                    return {
                        id: r.id, description: r.description,
                        code: r.code || '', is_new: false, is_deleted: false,
                        orig_desc: r.description, orig_code: r.code || ''
                    };
                });
                _dirty = false;
                gsRender(focusNew);
                gsStatus('Ready');
            })
            .catch(function () { rows = []; gsRender(focusNew); gsStatus('Load error'); });
    }

    /* ── Render ────────────────────────────────────────────── */
    function gsRender(focusNew) {
        var body    = document.getElementById('gs-grid-body');
        var visible = rows.filter(function (r) { return !r.is_deleted; });
        body.innerHTML = '';
        
        var last = visible[visible.length - 1];
        if (!last || last.description.trim()) {
            rows.push({ id: tempId--, description: '', code: '', is_new: true, is_deleted: false, orig_desc: '', orig_code: '' });
            visible = rows.filter(function (r) { return !r.is_deleted; });
        }

        visible.forEach(function (row, idx) {
            body.appendChild(makeRow(row, idx + 1));
        });
        gsUpdateCount();

        if (focusNew) {
            var all = document.querySelectorAll('.gs-grid-row');
            var lastEl = all[all.length - 1];
            if (lastEl) {
                var inp = lastEl.querySelectorAll('.gs-inp')[0];
                if (inp) {
                    inp.focus();
                    inp.scrollIntoView({ block: 'nearest' });
                }
            }
        }
    }

    function makeRow(row, sl) {
        var div = document.createElement('div');
        div.className = 'gs-grid-row' + (row.is_new ? ' gs-new' : '');
        div.dataset.id = row.id;
        div.innerHTML =
            '<div class="gs-cell gs-cell-sl">' + sl + '</div>' +
            '<div class="gs-cell" style="padding:0;">' +
                '<input class="gs-inp" type="text" value="' + _e(row.description) + '" ' +
                'placeholder="Description…" ' +
                'onchange="gsUpdate(' + row.id + ',\'description\',this.value)" ' +
                'onkeydown="gsKey(event,' + row.id + ',\'desc\')">' +
            '</div>' +
            '<div class="gs-cell" style="padding:0;">' +
                '<input class="gs-inp" type="text" value="' + _e(row.code) + '" ' +
                'placeholder="" ' +
                'onchange="gsUpdate(' + row.id + ',\'code\',this.value)" ' +
                'onkeydown="gsKey(event,' + row.id + ',\'code\')">' +
            '</div>' +
            '<div class="gs-cell gs-cell-del">' +
                '<button class="gs-del-btn" onclick="gsDelRow(' + row.id + ')" title="Delete">' +
                    DEL_ICON +
                '</button>' +
            '</div>';
        div.addEventListener('mousedown', function () {
            document.querySelectorAll('.gs-grid-row').forEach(function (r) {
                r.classList.remove('gs-sel');
            });
            div.classList.add('gs-sel');
        });
        return div;
    }

    /* ── Enter key navigation ──────────────────────────────── */
    window.gsKey = function (e, id, field) {
        if (e.key !== 'Enter') return;
        e.preventDefault();

        // Flush current input value into rows array first
        var inp = e.target;
        var val = inp.value;
        gsUpdate(id, field === 'desc' ? 'description' : 'code', val);

        var visible = rows.filter(function (r) { return !r.is_deleted; });
        var idx     = visible.findIndex(function (r) { return r.id === id; });
        var rowEls  = document.querySelectorAll('.gs-grid-row');

        if (field === 'desc') {
            // ── Duplicate check on description field ─────────
            var typedDesc = inp.value.trim().toLowerCase();
            if (typedDesc) {
                var dupIdx = visible.findIndex(function (r, i) {
                    return i !== idx &&
                           r.description.trim().toLowerCase() === typedDesc;
                });
                if (dupIdx !== -1) {
                    // Jump to the duplicate row, highlight it, focus its desc input
                    gsStatus('Duplicate — jumping to existing row');
                    
                    inp.value = '';
                    gsUpdate(id, 'description', '');

                    var dupEl = rowEls[dupIdx];
                    if (dupEl) {
                        document.querySelectorAll('.gs-grid-row').forEach(function (r) {
                            r.classList.remove('gs-sel');
                        });
                        dupEl.classList.add('gs-sel');
                        dupEl.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
                        var dupInp = dupEl.querySelectorAll('.gs-inp')[0];
                        if (dupInp) {
                            dupInp.focus();
                            dupInp.select();
                            // Flash highlight
                            dupEl.style.transition = 'outline 0s';
                            dupEl.style.outline = '2px solid var(--color-primary)';
                            setTimeout(function () {
                                dupEl.style.outline = '';
                            }, 1200);
                        }
                    }
                    return;   // ← stop here
                }
            }
            if (typedDesc) {
                gsSave(true);
            } else {
                // No duplicate — move to code cell
                if (rowEls[idx]) {
                    var codeInp = rowEls[idx].querySelectorAll('.gs-inp')[1];
                    if (codeInp) codeInp.focus();
                }
            }
        } else {
            // Code field Enter → save and advance
            gsSave(true);
        }
    };

    /* ── Update ────────────────────────────────────────────── */
    window.gsUpdate = function (id, field, val) {
        var row = rows.find(function (r) { return r.id === id; });
        if (row && row[field] !== val) { 
            row[field] = val; 
            _dirty = true; 
        }
    };

    /* ── Add / Remove ──────────────────────────────────────── */
    window.gsAdd = function () { gsAddBlank(); };

    function gsAddBlank() {
        var visible = rows.filter(function (r) { return !r.is_deleted; });
        var last    = visible[visible.length - 1];
        if (last && !last.description.trim()) return;
        rows.push({ id: tempId--, description: '', code: '', is_new: true, is_deleted: false, orig_desc: '', orig_code: '' });
        _dirty = true;
        gsRender(true);
    }

    window.gsRemove = function () {
        var sel = document.querySelector('.gs-grid-row.gs-sel');
        if (!sel) { showToast('Click a row first.', 'warning'); return; }
        gsDelRow(parseInt(sel.dataset.id));
    };

    window.gsDelRow = function (id) {
        var row = rows.find(function (r) { return r.id === id; });
        if (!row) return;
        if (row.is_new) {
            rows = rows.filter(function (r) { return r.id !== id; });
            gsRender();
        } else {
            showConfirm('Remove this row?', function (ok) {
                if (!ok) return;
                row.is_deleted = true;
                gsSave(false);
            }, 'danger', 'Remove Row', 'Yes, Remove', 'Cancel');
        }
    };

    window.gsChange = function () {
        var sel = document.querySelector('.gs-grid-row.gs-sel');
        if (!sel) { showToast('Click a row first.', 'warning'); return; }
        sel.querySelectorAll('.gs-inp')[0].focus();
    };

    /* ── Save ──────────────────────────────────────────────── */
    window.gsSave = function (focusNew) {
        // Flush DOM values first
        document.querySelectorAll('.gs-grid-row').forEach(function (el) {
            var id  = parseInt(el.dataset.id);
            var inp = el.querySelectorAll('.gs-inp');
            if (inp[0]) gsUpdate(id, 'description', inp[0].value);
            if (inp[1]) gsUpdate(id, 'code',        inp[1].value);
        });

        // ── Mandatory Description Check ──
        var missingDesc = false;
        rows.forEach(function (r) {
            if (!r.is_deleted && !r.description.trim() && r.code.trim()) {
                missingDesc = true;
            }
        });
        if (missingDesc) {
            gsStatus('Missing Description');
            showToast('Description is required when a code is entered.', 'warning');
            return;
        }

        // ── Global duplicate check ──
        var dupError = false;
        var visible = rows.filter(function (r) { return !r.is_deleted && r.description.trim(); });
        var descMap = {};
        for (var i = 0; i < visible.length; i++) {
            var d = visible[i].description.trim().toLowerCase();
            if (descMap[d]) {
                dupError = true;
                break;
            }
            descMap[d] = true;
        }

        if (dupError) {
            gsStatus('Duplicate found');
            showToast('Duplicate description found. Please remove or fix it before saving.', 'warning');
            return;
        }

        var toSave = rows.filter(function (r) {
            if (r.is_deleted) return false;
            if (!r.description.trim()) return false;
            if (r.is_saving) return false; // Prevent duplicate in-flight saves
            if (r.is_new) return true;
            return r.description !== r.orig_desc || r.code !== r.orig_code;
        }).map(function (r) {
            r.is_saving = true;
            return {
                id:          r.is_new ? null : r.id,
                temp_id:     r.id,
                description: r.description.trim(),
                code:        r.code.trim(),
            };
        });

        var toDelete = rows.filter(function (r) {
            return r.is_deleted && !r.is_new && !r.is_saving;
        }).map(function (r) {
            r.is_saving = true;
            return r.id; 
        });

        if (toSave.length === 0 && toDelete.length === 0) {
            _dirty = false;
            if (focusNew) gsRender(true);
            return;
        }

        var payload = {
            category:  catId,
            to_save:   toSave,
            to_delete: toDelete,
        };

        // OPTIMISTIC UI: Instantly render the grid state before the network request
        // so the user experiences absolutely zero lag for both saves and deletes.
        gsRender(focusNew === true);

        var actionText = (toSave.length === 0 && toDelete.length > 0) ? 'Removing…' : 'Saving…';
        gsStatus(actionText);
        fetch(window.GS.saveUrl, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': _csrf() },
            body: JSON.stringify(payload),
        })
        .then(function (r) { return r.json(); })
        .then(function (d) {
            // Clear in-flight flags
            toSave.forEach(function (ts) {
                var local = rows.find(function (r) { return r.id === ts.temp_id; });
                if (local) local.is_saving = false;
            });
            toDelete.forEach(function (td) {
                var local = rows.find(function (r) { return r.id === td; });
                if (local) local.is_saving = false;
            });

            if (d.success) {
                if (d.rows) {
                    // Silently sync server IDs into our local rows without rebuilding the DOM
                    d.rows.forEach(function (srv) {
                        var local = rows.find(function (r) {
                            return r.id === srv.id || r.description.toLowerCase() === srv.description.toLowerCase();
                        });
                        if (local) {
                            var oldId = local.id;
                            local.id = srv.id;
                            local.is_new = false;
                            local.orig_desc = srv.description;
                            local.orig_code = srv.code || '';
                            
                            // If this was a new row that just got a real ID, update its DOM elements
                            if (oldId !== srv.id) {
                                var rowEl = document.querySelector('.gs-grid-row[data-id="' + oldId + '"]');
                                if (rowEl) {
                                    rowEl.dataset.id = srv.id;
                                    var descInp = rowEl.querySelectorAll('.gs-inp')[0];
                                    var codeInp = rowEl.querySelectorAll('.gs-inp')[1];
                                    var delBtn  = rowEl.querySelector('.gs-del-btn');
                                    if (descInp) {
                                        descInp.setAttribute('onchange', 'gsUpdate(' + srv.id + ',\'description\',this.value)');
                                        descInp.setAttribute('onkeydown', 'gsKey(event,' + srv.id + ',\'desc\')');
                                    }
                                    if (codeInp) {
                                        codeInp.setAttribute('onchange', 'gsUpdate(' + srv.id + ',\'code\',this.value)');
                                        codeInp.setAttribute('onkeydown', 'gsKey(event,' + srv.id + ',\'code\')');
                                    }
                                    if (delBtn) {
                                        delBtn.setAttribute('onclick', 'gsDelRow(' + srv.id + ')');
                                    }
                                    rowEl.classList.remove('gs-new');
                                }
                            }
                        }
                    });
                }
                
                // Cleanup deleted rows from memory
                rows = rows.filter(function (r) { return !r.is_deleted; });
                
                _dirty = false;
                
                var statusMsg = 'Saved ✓';
                var toastMsg = 'Records saved successfully.';
                if (toSave.length === 0 && toDelete.length > 0) {
                    statusMsg = 'Removed ✓';
                    toastMsg = 'Record(s) removed successfully.';
                } else if (toSave.length > 0 && toDelete.length > 0) {
                    toastMsg = 'Records saved and removed successfully.';
                }
                
                gsStatus(statusMsg);
                showToast(toastMsg, 'success');
            } else {
                gsStatus('Operation failed');
                showToast(d.error || 'Operation failed.', 'error');
            }
        })
        .catch(function () {
            // Clear in-flight flags
            toSave.forEach(function (ts) {
                var local = rows.find(function (r) { return r.id === ts.temp_id; });
                if (local) local.is_saving = false;
            });
            toDelete.forEach(function (td) {
                var local = rows.find(function (r) { return r.id === td; });
                if (local) local.is_saving = false;
            });
            gsStatus('Network error');
            showToast('Network error — please try again.', 'error');
        });
    };

    window.gsClose = function () {
        if (!_dirty) { history.back(); return; }
        showConfirm(
            'You have unsaved changes. Are you sure you want to close?',
            function (ok) { if (ok) history.back(); },
            'warning', 'Unsaved Changes', 'Yes, Close', 'Cancel'
        );
    };

    /* ── Helpers ───────────────────────────────────────────── */
    function gsUpdateCount() {
        var n = rows.filter(function (r) {
            return !r.is_deleted && r.description.trim();
        }).length;
        var el = document.getElementById('gs-row-count');
        if (el) el.textContent = n + ' records';
    }

    function gsStatus(msg) {
        var el = document.getElementById('gs-status-msg');
        if (el) el.textContent = msg;
        // Auto-reset status after 3s if it's not "Ready"
        if (msg !== 'Ready') {
            clearTimeout(gsStatus._t);
            gsStatus._t = setTimeout(function () { gsStatus('Ready'); }, 3000);
        }
    }

    function _csrf() {
        return (document.cookie.match(/csrftoken=([^;]+)/) || [])[1] || '';
    }

    function _e(s) {
        return String(s || '')
            .replace(/&/g, '&amp;')
            .replace(/"/g, '&quot;')
            .replace(/</g, '&lt;');
    }

}());