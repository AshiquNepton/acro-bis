/**
 * common/static/common/js/documents_modal.js
 * FTP-only document modal — no database table.
 * Files stored at: /erp/{module}/{company_code}/{ref_id}/{group_id}/filename
 *
 * Requires: utilities_modal.js
 *
 * Setup in template:
 *   window.EDM_LOAD_URL   = "{% url 'common:load_docs' %}";
 *   window.EDM_SAVE_URL   = "{% url 'common:save_doc' %}";
 *   window.EDM_DELETE_URL = "{% url 'common:delete_doc' %}";
 *   window.EDM_SERVE_URL  = "{% url 'common:serve_doc' %}";
 *   window.EDM_DOC_GROUPS = {{ doc_group_options|safe }};
 *
 *   function erDocuments() {
 *     var regNo   = document.getElementById('id_reg_no').value.trim();
 *     var empName = document.getElementById('id_emp_name').value.trim();
 *     if (!regNo) { pfToast('Load an employee first', 'w'); return; }
 *     edmOpen('hrms', regNo, empName);
 *   }
 */

(function () {
    'use strict';

    var MAX_BYTES = 1048576; // 1 MB

    var _state = {
        module     : '',
        refId      : '',
        label      : '',
        selected   : null,   // { doc, file_path, size, group_id, group_label }
        pendingFile: null,
    };

    function _csrf() { var m=document.cookie.match(/csrftoken=([^;]+)/); return m?decodeURIComponent(m[1]):''; }
    function _toast(msg,type){ if(typeof window.pfToast==='function') window.pfToast(msg,type); }
    function _val(id){ var e=document.getElementById(id); return e?e.value:''; }
    function _set(id,v){ var e=document.getElementById(id); if(e) e.value=v||''; }
    function _fmt(b){ if(b<1024) return b+' B'; if(b<1048576) return (b/1024).toFixed(1)+' KB'; return (b/1048576).toFixed(2)+' MB'; }

    /* Grid columns — FTP file listing */
    var GRID_COLS = [
        {key:'_sn',         label:'SN',      width:'40px' },
        {key:'doc',         label:'Document'              },
        {key:'group_label', label:'Group',   width:'110px'},
        {key:'size',        label:'Size',    width:'80px' },
    ];

    var _modal = new UtilityModal({
        id   : 'edm',
        title: 'Attachments',
        icon : '<path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48"/>',
        width: '50%',

        tabs: [
            {id:'attach',  label:'» Attach Document',  icon:'attach'},
            {id:'details', label:'» Document Details', icon:'doc'   },
        ],

        toolbar: [
            {label:'Save',   icon:'save', danger:false, onclick:function(){edmSave();  }},
            {label:'Delete', icon:'del',  danger:true,  onclick:function(){edmDelete();}},
        ],

        onBuild: function(modal) {

            /* ── Tab 1: Attach Document ── */
            var p1 = modal.pane('attach');
            if (p1) {
                /* Group row (mandatory) */
                var topRow = document.createElement('div');
                topRow.style.cssText = 'display:flex;gap:8px;align-items:center;margin-bottom:6px;flex-shrink:0';
                topRow.innerHTML =
                    '<div style="display:flex;align-items:center;gap:6px;flex:0 0 260px">' +
                    '  <span class="utm-lbl" style="width:44px;flex-shrink:0">Group <span style="color:var(--color-danger,#dc2626)">*</span></span>' +
                    '  <select id="edm-group" class="utm-sel"></select>' +
                    '</div>';
                p1.appendChild(topRow);

                /* File info bar */
                var fb = document.createElement('div');
                fb.id = 'edm-fbar';
                fb.style.cssText = 'display:none;align-items:center;gap:8px;padding:4px 8px;'+
                    'background:var(--color-surface-alt,#f5f5f5);border:1px solid var(--color-border,#ddd);'+
                    'border-radius:3px;font-size:12px;margin-bottom:6px;flex-shrink:0';
                fb.innerHTML =
                    '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'+
                    '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>'+
                    '<polyline points="14 2 14 8 20 8"/></svg>'+
                    '<span id="edm-fname" style="flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap"></span>'+
                    '<span id="edm-fsize" style="color:var(--color-text-secondary,#888);white-space:nowrap;font-size:11px"></span>'+
                    '<button onclick="edmClearFile()" style="background:none;border:none;cursor:pointer;color:var(--color-danger,#dc2626);padding:0 3px;font-size:14px">✕</button>';
                p1.appendChild(fb);

                /* Toolbar */
                var tb = document.createElement('div');
                tb.style.flexShrink = '0';
                tb.innerHTML = UtilityModal.gridToolbar([
                    {label:'Refresh',     icon:'refresh', onclick:'edmRefresh()'               },
                    {label:'Remove',      icon:'remove',  onclick:'edmRemoveRow()', danger:true  },
                    {label:'Upload',      icon:'upload',  onclick:'edmUpload()',    primary:true },
                    {label:'Choose File', icon:'attach',  onclick:'edmChooseFile()'             },
                ]);
                p1.appendChild(tb);

                /* Hidden file input */
                var fi = document.createElement('input');
                fi.type = 'file'; fi.id = 'edm-file-attach'; fi.style.display = 'none';
                fi.addEventListener('change', function(){ edmFileChosen(fi); });
                p1.appendChild(fi);

                /* Grid */
                var gw = document.createElement('div');
                gw.style.cssText = 'flex:1;min-height:0;overflow:hidden;display:flex;flex-direction:column';
                gw.innerHTML = UtilityModal.grid('edm-tbody', GRID_COLS);
                p1.appendChild(gw);
            }

            /* ── Tab 2: Document Details ── */
            var p2 = modal.pane('details');
            if (p2) {
                p2.innerHTML = [
                    UtilityModal.field('Doc Delivered By',
                        UtilityModal.inputBrowse('edm-delivered','edm-file-delivered'),
                        {labelWidth:'120px'}),
                    UtilityModal.field('Doc Received By',
                        UtilityModal.inputBrowse('edm-received','edm-file-received'),
                        {labelWidth:'120px'}),
                    UtilityModal.field('Contact No',
                        '<input id="edm-contact" type="tel" class="utm-inp">',
                        {labelWidth:'120px'}),
                    UtilityModal.field('Date',
                        '<input id="edm-date" type="date" class="utm-inp utm-inp--date">',
                        {labelWidth:'120px'}),
                    UtilityModal.field('Notes',
                        UtilityModal.textarea('edm-notes', 3),
                        {labelWidth:'120px', topAlign:true}),
                    UtilityModal.sectionHdr('Details'),
                    UtilityModal.field('',
                        UtilityModal.textarea('edm-details', 4, true),
                        {labelWidth:'120px', topAlign:true, fill:true}),
                ].join('');
            }
        },

        onOpen: function(modal, ctx) {
            modal.setSubtitle(ctx.refId + (ctx.label ? '  —  ' + ctx.label : ''));
            _populateGroups();
            _clearForm();
            edmRefresh();
        },
    });

    /* ── Populate groups ── */
    function _populateGroups() {
        var sel = document.getElementById('edm-group');
        if (!sel) return;
        sel.innerHTML = '<option value="">Select Group *</option>';
        (window.EDM_DOC_GROUPS || []).forEach(function(g) {
            var o = document.createElement('option');
            o.value = g.value; o.textContent = g.label; sel.appendChild(o);
        });
    }

    function _clearForm() {
        _set('edm-group', '');
        _state.selected = null; _state.pendingFile = null;
        var fb = document.getElementById('edm-fbar'); if (fb) fb.style.display = 'none';
        var fi = document.getElementById('edm-file-attach'); if (fi) fi.value = '';
        var tb = document.getElementById('edm-tbody');
        if (tb) tb.querySelectorAll('tr').forEach(function(r){ r.classList.remove('selected'); });
    }

    /* ── Public API ── */
    window.edmOpen = function(module, refId, label) {
        _state.module = module||''; _state.refId = refId||''; _state.label = label||'';
        _modal.open({module:module, refId:refId, label:label});
    };
    window.edmClose = function(){ _modal.close(); };

    /* ── Refresh — loads FTP file list ── */
    window.edmRefresh = function() {
        var url = window.EDM_LOAD_URL;
        if (!url || !_state.module || !_state.refId) {
            UtilityModal.renderGrid('edm-tbody', [], GRID_COLS, null, null);
            return;
        }
        fetch(url + '?module=' + encodeURIComponent(_state.module) +
                    '&ref_id='  + encodeURIComponent(_state.refId))
            .then(function(r){ return r.json(); })
            .then(function(d){
                if (d.warning) _toast(d.warning, 'w');
                UtilityModal.renderGrid('edm-tbody', d.rows||[], GRID_COLS,
                    /* single click — select row */
                    function(row) {
                        _state.selected = row;
                        /* Switch to group matching this file */
                        _set('edm-group', String(row.group_id||''));
                    },
                    /* double click — open/download file */
                    function(row) {
                        if (!row.file_path) { _toast('No file path', 'w'); return; }
                        var su = window.EDM_SERVE_URL;
                        if (su) {
                            window.open(su + '?path=' + encodeURIComponent(row.file_path), '_blank');
                        } else {
                            _toast('File: ' + row.file_path, 'i');
                        }
                    }
                );
            })
            .catch(function(e){ _toast('Load failed: '+e, 'e'); });
    };

    /* ── File picker ── */
    window.edmChooseFile = function(){ var fi=document.getElementById('edm-file-attach'); if(fi) fi.click(); };

    window.edmClearFile = function(){
        _state.pendingFile = null;
        var fi=document.getElementById('edm-file-attach'); if(fi) fi.value='';
        var fb=document.getElementById('edm-fbar'); if(fb) fb.style.display='none';
    };

    window.edmFileChosen = function(input) {
        if (!input.files||!input.files[0]) return;
        var file = input.files[0];
        if (file.size > MAX_BYTES) {
            _toast('File too large: ' + _fmt(file.size) + ' — max 1 MB', 'e');
            input.value = ''; return;
        }
        _state.pendingFile = file;
        var fb=document.getElementById('edm-fbar');
        var fn=document.getElementById('edm-fname');
        var fs=document.getElementById('edm-fsize');
        if(fb) fb.style.display='flex';
        if(fn) fn.textContent=file.name;
        if(fs) fs.textContent=_fmt(file.size);
    };

    /* ── Upload ── */
    window.edmUpload = function(){
        if (!_state.pendingFile) { _toast('Choose a file first (max 1 MB)', 'w'); return; }
        edmSave();
    };

    /* ── Save — uploads file to FTP ── */
    window.edmSave = function() {
        var url = window.EDM_SAVE_URL;
        if (!url) { _toast('Save URL not configured', 'e'); return; }

        /* Group is mandatory */
        var groupId = _val('edm-group');
        if (!groupId) {
            _toast('Please select a Group', 'w');
            var gs = document.getElementById('edm-group');
            if (gs) {
                gs.style.borderColor = 'var(--color-danger,#dc2626)';
                setTimeout(function(){ gs.style.borderColor=''; }, 2000);
            }
            return;
        }

        /* File is mandatory for new upload */
        if (!_state.pendingFile) {
            _toast('Choose a file to upload', 'w'); return;
        }

        var fd = new FormData();
        fd.append('module',   _state.module);
        fd.append('ref_id',   _state.refId);
        fd.append('group_id', groupId);
        fd.append('doc_file', _state.pendingFile, _state.pendingFile.name);

        fetch(url, {method:'POST', body:fd, headers:{'X-CSRFToken':_csrf()}})
            .then(function(r){ return r.json(); })
            .then(function(d){
                if (d.success) {
                    _toast(d.message||'Uploaded', 's');
                    _state.pendingFile = null;
                    _clearForm();
                    edmRefresh();
                } else {
                    _toast(d.error||'Upload failed', 'e');
                }
            })
            .catch(function(){ _toast('Network error', 'e'); });
    };

    /* ── Remove selected file from FTP ── */
    window.edmRemoveRow = function() {
        if (!_state.selected || !_state.selected.file_path) {
            _toast('Select a file first', 'w'); return;
        }
        var url = window.EDM_DELETE_URL;
        if (!url) { _toast('Delete URL not configured', 'e'); return; }

        /* Remove from grid immediately */
        var tb = document.getElementById('edm-tbody');
        if (tb) { var s=tb.querySelector('tr.selected'); if(s) s.remove(); }

        var path = _state.selected.file_path;
        _state.selected = null;

        var fd = new FormData();
        fd.append('path', path);
        fetch(url, {method:'POST', body:fd, headers:{'X-CSRFToken':_csrf()}})
            .then(function(r){ return r.json(); })
            .then(function(d){
                if (d.success) { _toast('Removed', 's'); }
                else { _toast(d.error||'Remove failed', 'e'); edmRefresh(); }
            })
            .catch(function(){ edmRefresh(); });
    };

    /* ── Delete (header button with confirm) ── */
    window.edmDelete = function() {
        if (!_state.selected || !_state.selected.file_path) {
            _toast('Select a file to delete', 'w'); return;
        }
        function doDelete() {
            var fd = new FormData();
            fd.append('path', _state.selected.file_path);
            var url = window.EDM_DELETE_URL;
            fetch(url, {method:'POST', body:fd, headers:{'X-CSRFToken':_csrf()}})
                .then(function(r){ return r.json(); })
                .then(function(d){
                    if (d.success) { _toast('Deleted', 's'); _clearForm(); edmRefresh(); }
                    else { _toast(d.error||'Delete failed', 'e'); }
                })
                .catch(function(){ _toast('Network error', 'e'); });
        }
        if (typeof window.showConfirm === 'function') {
            window.showConfirm('Delete this file from FTP?', function(ok){ if(ok) doDelete(); },
                'danger', 'Delete File', 'Yes, Delete', 'Cancel');
        } else {
            if (confirm('Delete this file?')) doDelete();
        }
    };

}());