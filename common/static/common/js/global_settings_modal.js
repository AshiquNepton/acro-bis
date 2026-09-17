/**
 * common/static/common/js/global_settings_modal.js
 * ═══════════════════════════════════════════════════════════════════
 *  Global Settings Modal  —  Python-dict-driven via window._gsConfig
 *
 *  PATCH CHANGES
 *  ─────────────
 *  1. "Save Settings" button moved into the UtilityModal header toolbar
 *     (utm-hbtn style — matches the blue-bar Load/X button style).
 *  2. Settings tab has a new "Employee Report Logo" <select> field
 *     (name: 'employee_report_logo') whose options are the four image-slot
 *     keys loaded from the server.  Saved to ChartOfCode as
 *       Category=OrgOptions  Code=employee_report_logo  TypeCode=value.
 *  3. Per-pane sticky footer removed; status text moves to a small
 *     <span> injected next to the Save button in the header.
 *
 *  DEPENDS ON (load in this order in base.html):
 *    1. utilities_modal.js
 *    2. profile_form.js   ← provides window.PF_ICONS, window.pfToast,
 *                            window.showConfirm
 *    3. global_settings_modal.js   ← this file
 * ═══════════════════════════════════════════════════════════════════
 */

(function (global) {
    'use strict';

    /* ── Guard ───────────────────────────────────────────────────────────── */
    if (typeof global.UtilityModal === 'undefined') {
        console.error('[GlobalSettings] UtilityModal not found — load utilities_modal.js first.');
        global.openGlobalSettings = function () {
            console.error('openGlobalSettings: UtilityModal not available.');
        };
        global.globalSettingsModal = { open: global.openGlobalSettings };
        return;
    }

    /* ══════════════════════════════════════════════════════════════════════
       ICON HELPERS
    ══════════════════════════════════════════════════════════════════════ */
    function _icon(name) {
        return (global.PF_ICONS || {})[name] || '';
    }
    function _iconPaths(name) {
        var full = _icon(name);
        return full.replace(/<svg[^>]*>/i, '').replace(/<\/svg>/i, '');
    }

    /* ── CSRF ────────────────────────────────────────────────────────────── */
    function _csrf() {
        var m = document.cookie.match(/csrftoken=([^;]+)/);
        return m ? decodeURIComponent(m[1]) : '';
    }

    /* ── Toast ───────────────────────────────────────────────────────────── */
    function _toast(msg, type) {
        if (typeof global.pfToast === 'function') global.pfToast(msg, type);
        else console.info('[GS toast]', type, msg);
    }

    /* ── Confirm ─────────────────────────────────────────────────────────── */
    function _confirm(message, callback, type, title, okText, cancelText) {
        if (typeof global.showConfirm === 'function') {
            global.showConfirm(message, callback, type || 'danger', title, okText, cancelText);
        } else {
            callback(global.confirm(message));
        }
    }

    /* ══════════════════════════════════════════════════════════════════════
       RUNTIME STATE
    ══════════════════════════════════════════════════════════════════════ */
    var _imagePaths = {};   // { key: ftp_path }
    var _modal      = null;

    /* ══════════════════════════════════════════════════════════════════════
       IMAGE SLOT DEFINITIONS  (mirrors IMAGE_TYPES in global_settings.py)
       Used to populate the employee_report_logo <select>.
    ══════════════════════════════════════════════════════════════════════ */
    var IMAGE_SLOT_OPTIONS = [
        { value: '',                label: '— None —'           },
        { value: 'header_full_logo', label: 'Header Full Logo'  },
        { value: 'header_side_logo', label: 'Header Side Logo'  },
        { value: 'footer_full_logo', label: 'Footer Full Logo'  },
        { value: 'footer_side_logo', label: 'Footer Side Logo'  },
    ];

    /* ══════════════════════════════════════════════════════════════════════
       CONFIG ACCESSOR
    ══════════════════════════════════════════════════════════════════════ */
    function _cfg() {
        return global._gsConfig || { tabs: [] };
    }

    /**
     * Return the augmented tabs array.
     * The 'employee_report_logo' select is injected here so the Python
     * _build_gs_config() dict stays minimal — it only needs to declare
     * the field with type:'select' and an empty options list; we fill
     * the options from IMAGE_SLOT_OPTIONS at build time.
     */
    function _effectiveTabs() {
        var tabs = (_cfg().tabs || []).map(function (tab) {
            if (tab.id !== 'settings') return tab;

            /* Clone the tab shallowly, then clone fields array */
            var clone  = {};
            for (var k in tab) { if (tab.hasOwnProperty(k)) clone[k] = tab[k]; }

            var fields = (tab.fields || []).slice();

            /* Inject employee_report_logo if not already present */
            var alreadyHas = fields.some(function (f) { return f.name === 'employee_report_logo'; });
            if (!alreadyHas) {
                fields.push({
                    name    : 'employee_report_logo',
                    label   : 'Employee Report Logo',
                    type    : 'select',
                    value   : '',
                    options : IMAGE_SLOT_OPTIONS,
                });
            }

            clone.fields = fields;
            return clone;
        });
        return tabs;
    }

    /* ══════════════════════════════════════════════════════════════════════
       MODAL FACTORY  —  built lazily on first open
    ══════════════════════════════════════════════════════════════════════ */
    function _buildModal() {
        if (_modal) return _modal;

        var cfg     = _cfg();
        var tabs    = _effectiveTabs();
        var utmTabs = tabs.map(function (tab) {
            return { id: tab.id, label: tab.label, icon: _iconPaths(tab.icon) };
        });

        /* ── Header toolbar ─────────────────────────────────────────────── */
        /* We need one Save button that always saves the currently-active
           settings tab.  Images tab has no Save (uploads are instant).
           The status span is rendered as a plain DOM element appended to
           the header right-side after the modal is built — see _afterBuild. */
        var toolbar = [
            {
                label  : 'Save',
                icon   : 'save',          /* UtilityModal built-in icon key */
                danger : false,
                onclick: function () { _saveActiveTab(); },
            },
        ];

        _modal = new UtilityModal({
            id      : 'gs-modal',
            title   : cfg.title    || 'Global Settings',
            subtitle: cfg.subtitle || '',
            icon    : _iconPaths('Settings'),
            tabs    : utmTabs,
            toolbar : toolbar,

            onBuild     : function (modal) { _buildAllPanes(modal, tabs); _afterBuild(modal); },
            onOpen      : function ()      { _onModalOpen(tabs); },
            onTabSwitch : function (modal, tabId) { _onTabSwitch(tabId); },
        });

        return _modal;
    }

    /* ── After the DOM is built, hide Save on the images tab ─────────────── */
    function _afterBuild(modal) {
        /* The Save button is the first utm-hbtn--normal in the header.
           We toggle its visibility via _onTabSwitch. */
        _onTabSwitch(modal.activeTab());
    }

    function _onTabSwitch(tabId) {
        var saveBtn    = _getSaveBtn();
        var statusSpan = document.getElementById('gs-hdr-status');
        if (!saveBtn) return;
        var isImages = (tabId === 'images');
        saveBtn.style.display    = isImages ? 'none' : '';
        if (statusSpan) statusSpan.style.display = isImages ? 'none' : '';
    }

    function _getSaveBtn() {
        /* The Save button is built by UtilityModal from the toolbar config.
           It's the only utm-hbtn--normal in the gs-modal header. */
        var hdr = document.querySelector('#gs-modal-bd .utm-hdr-r');
        if (!hdr) return null;
        return hdr.querySelector('.utm-hbtn--normal');
    }

    /* ── Save whichever settings tab is active ───────────────────────────── */
    function _saveActiveTab() {
        var tabId = _modal ? _modal.activeTab() : 'settings';
        var tabs  = _effectiveTabs();
        for (var i = 0; i < tabs.length; i++) {
            if (tabs[i].id === tabId && tabs[i].fields && tabs[i].fields.length) {
                _saveSettings(tabs[i].fields, tabId);
                return;
            }
        }
    }

    /* ══════════════════════════════════════════════════════════════════════
       ON OPEN — reload settings and images from server every time
    ══════════════════════════════════════════════════════════════════════ */
    function _onModalOpen(tabs) {
        (tabs || []).forEach(function (tab) {
            if (tab.type === 'images') {
                _loadImages(tab.slots || []);
            } else if (tab.fields && tab.fields.length) {
                _loadSettings(tab.fields);
            }
        });
    }

    /* ══════════════════════════════════════════════════════════════════════
       PANE BUILDERS
    ══════════════════════════════════════════════════════════════════════ */
    function _buildAllPanes(modal, tabs) {
        (tabs || []).forEach(function (tab) {
            if (tab.type === 'images') {
                _buildImagesPane(modal, tab);
            } else {
                _buildFieldsPane(modal, tab);
            }
        });
    }

    /* ── Fields pane (no footer — Save is in the header toolbar) ─────────── */
    function _buildFieldsPane(modal, tab) {
        var pane = modal.pane(tab.id);
        if (!pane) return;

        var wrap = document.createElement('div');
        wrap.style.cssText = 'padding:20px 24px;display:flex;flex-direction:column;gap:0;overflow-y:auto;height:100%;box-sizing:border-box;';

        if (tab.section_label) {
            var sec = document.createElement('div');
            sec.className = 'utm-sec';
            sec.style.cssText = 'margin-bottom:12px;';
            sec.textContent = tab.section_label;
            wrap.appendChild(sec);
        }

        (tab.fields || []).forEach(function (field) {
            wrap.appendChild(_buildField(field));
        });

        pane.appendChild(wrap);
    }

    /* ── Single pf-field row ─────────────────────────────────────────────── */
    function _buildField(field) {
        var div = document.createElement('div');
        div.className = 'pf-field';

        var lbl = document.createElement('label');
        lbl.className = 'pf-field-lbl';
        lbl.setAttribute('for', 'gs-f-' + field.name);
        lbl.textContent = field.label || field.name;
        if (field.required) {
            var req = document.createElement('span');
            req.className = 'req';
            req.textContent = ' *';
            lbl.appendChild(req);
        }
        div.appendChild(lbl);

        var ctl = document.createElement('div');
        ctl.className = 'pf-field-ctl';
        ctl.appendChild(_buildControl(field));

        if (field.unit) {
            var unit = document.createElement('span');
            unit.style.cssText = 'font-size:11px;color:var(--color-text-tertiary);margin-top:2px;';
            unit.textContent = field.unit;
            ctl.appendChild(unit);
        }
        div.appendChild(ctl);
        return div;
    }

    /* ── Control builder ─────────────────────────────────────────────────── */
    function _buildControl(field) {
        var type = String(field.type || 'text');
        var val  = field.value !== undefined ? String(field.value) : '';
        var id   = 'gs-f-' + field.name;

        if (type === '3' || type === 'select') {
            var sel = document.createElement('select');
            sel.id = id; sel.name = field.name;
            if (field.required) sel.required = true;
            (field.options || []).forEach(function (opt) {
                var o = document.createElement('option');
                o.value = opt.value; o.textContent = opt.label;
                if (String(opt.value) === val) o.selected = true;
                sel.appendChild(o);
            });
            return sel;
        }

        if (type === '5' || type === 'textarea') {
            var ta = document.createElement('textarea');
            ta.id = id; ta.name = field.name; ta.rows = field.rows || 3;
            ta.textContent = val;
            if (field.placeholder) ta.placeholder = field.placeholder;
            if (field.required)    ta.required    = true;
            return ta;
        }

        if (type === '10' || type === 'checkbox') {
            var cbWrap = document.createElement('div');
            cbWrap.className = 'pf-check-wrap';
            var cb = document.createElement('input');
            cb.type = 'checkbox'; cb.id = id; cb.name = field.name;
            cb.checked = !!field.value;
            cbWrap.appendChild(cb);
            if (field.checkbox_label) {
                var cbl = document.createElement('label');
                cbl.className = 'pf-check-lbl';
                cbl.setAttribute('for', id);
                cbl.textContent = field.checkbox_label;
                cbWrap.appendChild(cbl);
            }
            return cbWrap;
        }

        if (type === '2' || type === 'number') {
            var numInp = document.createElement('input');
            numInp.type = 'number'; numInp.id = id; numInp.name = field.name;
            numInp.value = val;
            if (field.step  !== undefined) numInp.step  = field.step;
            if (field.min   !== undefined) numInp.min   = field.min;
            if (field.max   !== undefined) numInp.max   = field.max;
            if (field.required)    numInp.required    = true;
            if (field.readonly)    numInp.readOnly    = true;
            if (field.placeholder) numInp.placeholder = field.placeholder;
            return numInp;
        }

        if (type === '17' || type === 'readonly') {
            var roInp = document.createElement('input');
            roInp.type = 'text'; roInp.id = id; roInp.name = field.name;
            roInp.value = val; roInp.readOnly = true;
            return roInp;
        }

        if (type === '18' || type === 'hidden') {
            var hidInp = document.createElement('input');
            hidInp.type = 'hidden'; hidInp.id = id; hidInp.name = field.name;
            hidInp.value = val;
            return hidInp;
        }

        if (type === '12' || type === 'password') {
            var pwInp = document.createElement('input');
            pwInp.type = 'password'; pwInp.id = id; pwInp.name = field.name;
            if (field.placeholder) pwInp.placeholder = field.placeholder;
            if (field.required)    pwInp.required    = true;
            return pwInp;
        }

        /* Default: text / email / tel */
        var textType = 'text';
        if (type === '13' || type === 'email') textType = 'email';
        if (type === '14' || type === 'tel')   textType = 'tel';

        var txtInp = document.createElement('input');
        txtInp.type  = textType; txtInp.id = id; txtInp.name = field.name;
        txtInp.value = val;
        if (field.placeholder) txtInp.placeholder = field.placeholder;
        if (field.required)    txtInp.required    = true;
        if (field.readonly)    txtInp.readOnly    = true;
        if (field.maxlength)   txtInp.maxLength   = field.maxlength;
        return txtInp;
    }

    /* ══════════════════════════════════════════════════════════════════════
       IMAGES PANE
    ══════════════════════════════════════════════════════════════════════ */
    function _buildImagesPane(modal, tab) {
        var pane = modal.pane(tab.id);
        if (!pane) return;

        var wrap = document.createElement('div');
        wrap.style.cssText =
            'padding:20px 24px;display:flex;flex-direction:column;gap:0;' +
            'overflow-y:auto;height:100%;box-sizing:border-box;';

        (tab.slots || []).forEach(function (slot) {
            wrap.appendChild(_buildImageRow(slot));
        });
        pane.appendChild(wrap);
    }

    function _buildImageRow(slot) {
        var key = slot.key;

        var field = document.createElement('div');
        field.className     = 'pf-field';
        field.id            = 'gs-img-field-' + key;
        field.style.cssText = 'position:relative;';

        var lbl = document.createElement('label');
        lbl.className   = 'pf-field-lbl';
        lbl.textContent = slot.label || key;
        field.appendChild(lbl);

        var ctl = document.createElement('div');
        ctl.className     = 'pf-field-ctl';
        ctl.style.cssText = 'display:flex;flex-direction:column;gap:6px;';

        var row = document.createElement('div');
        row.style.cssText = 'display:flex;align-items:center;gap:8px;';

        /* Thumbnail */
        var thumb = document.createElement('div');
        thumb.id            = 'gs-thumb-' + key;
        thumb.style.cssText =
            'width:52px;height:40px;border:1px solid var(--color-border,#e2e8f0);' +
            'border-radius:4px;background:var(--color-bg,#f8fafc);flex-shrink:0;' +
            'display:flex;align-items:center;justify-content:center;overflow:hidden;cursor:pointer;';
        thumb.title = 'Click to browse';
        thumb.innerHTML =
            '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor"' +
            ' stroke-width="1.5" id="gs-thumb-ph-' + key + '">' +
            '<rect x="3" y="3" width="18" height="18" rx="2"/>' +
            '<circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/></svg>' +
            '<img id="gs-thumb-img-' + key + '" src="" alt=""' +
            ' style="display:none;width:100%;height:100%;object-fit:contain;">';
        thumb.addEventListener('click', (function (k) {
            return function () { _pickFile(k); };
        }(key)));
        row.appendChild(thumb);

        /* Filename (read-only) */
        var inputWrap = document.createElement('div');
        inputWrap.style.cssText = 'flex:1;';
        var fnInp = document.createElement('input');
        fnInp.type        = 'text';
        fnInp.id          = 'gs-inp-' + key;
        fnInp.readOnly    = true;
        fnInp.placeholder = 'No image selected';
        fnInp.style.cssText = 'width:100%;cursor:pointer;';
        fnInp.addEventListener('click', (function (k) {
            return function () { _pickFile(k); };
        }(key)));
        inputWrap.appendChild(fnInp);
        row.appendChild(inputWrap);

        /* Browse button */
        var browseBtn = document.createElement('button');
        browseBtn.type      = 'button';
        browseBtn.id        = 'gs-browse-' + key;
        browseBtn.className = 'utm-hbtn utm-hbtn--normal';
        browseBtn.style.cssText = 'font-size:12px;white-space:nowrap;';
        browseBtn.innerHTML = _icon('Upload') + ' Browse';
        browseBtn.addEventListener('click', (function (k) {
            return function () { _pickFile(k); };
        }(key)));
        row.appendChild(browseBtn);

        /* Remove button */
        var rmBtn = document.createElement('button');
        rmBtn.type      = 'button';
        rmBtn.id        = 'gs-rm-' + key;
        rmBtn.className = 'utm-hbtn utm-hbtn--danger';
        rmBtn.style.cssText = 'font-size:12px;display:none;white-space:nowrap;';
        rmBtn.innerHTML = _icon('Delete') + ' Remove';
        rmBtn.addEventListener('click', (function (k) {
            return function () { _confirmRemove(k); };
        }(key)));
        row.appendChild(rmBtn);

        ctl.appendChild(row);

        /* Hint text */
        if (slot.hint) {
            var hint = document.createElement('div');
            hint.style.cssText = 'font-size:11px;color:var(--color-text-tertiary,#94a3b8);line-height:1.4;';
            hint.textContent = slot.hint;
            ctl.appendChild(hint);
        }

        /* Hidden file input */
        var fileInp = document.createElement('input');
        fileInp.type    = 'file';
        fileInp.id      = 'gs-file-' + key;
        fileInp.accept  = '.jpg,.jpeg,.png,.gif,.webp,.svg,.bmp';
        fileInp.style.display = 'none';
        fileInp.addEventListener('change', (function (k, inp) {
            return function () { _onFilePicked(k, inp); };
        }(key, fileInp)));
        ctl.appendChild(fileInp);

        field.appendChild(ctl);
        return field;
    }

    /* ══════════════════════════════════════════════════════════════════════
       SETTINGS LOAD
    ══════════════════════════════════════════════════════════════════════ */
    function _loadSettings(fields) {
        if (!fields || !fields.length) return;

        fetch('/common/gs/settings/load/', {
            headers: { 'X-Requested-With': 'XMLHttpRequest' }
        })
        .then(function (r) {
            if (!r.ok) throw new Error('HTTP ' + r.status);
            return r.json();
        })
        .then(function (d) {
            if (!d.success) { console.warn('[GS] settings load:', d.error); return; }
            var settings = d.settings || {};
            fields.forEach(function (field) {
                var inp = document.getElementById('gs-f-' + field.name);
                if (!inp) return;
                var val = settings[field.name];
                if (val === undefined || val === null) return;
                if (inp.type === 'checkbox') {
                    inp.checked = (val === 'true' || val === '1' || val === 'on');
                } else {
                    inp.value = val;
                }
            });
        })
        .catch(function (err) {
            console.error('[GS] settings load:', err);
        });
    }

    /* ══════════════════════════════════════════════════════════════════════
       SETTINGS SAVE
       Status text is shown in the header via a small injected span
       (#gs-hdr-status) placed to the left of the Save button.
    ══════════════════════════════════════════════════════════════════════ */
    function _ensureStatusSpan() {
        var existing = document.getElementById('gs-hdr-status');
        if (existing) return existing;

        var hdrR = document.querySelector('#gs-modal-bd .utm-hdr-r');
        if (!hdrR) return null;

        var span = document.createElement('span');
        span.id = 'gs-hdr-status';
        span.style.cssText =
            'font-size:11px;color:rgba(255,255,255,.75);margin-right:4px;' +
            'white-space:nowrap;align-self:center;';
        /* Insert before the first child (before Save btn) */
        hdrR.insertBefore(span, hdrR.firstChild);
        return span;
    }

    function _saveSettings(fields, tabId) {
        if (!fields || !fields.length) return;

        var saveBtn    = _getSaveBtn();
        var statusSpan = _ensureStatusSpan();

        if (saveBtn)    { saveBtn.disabled = true; saveBtn.textContent = 'Saving…'; }
        if (statusSpan) statusSpan.textContent = '';

        var fd = new FormData();
        fd.append('csrfmiddlewaretoken', _csrf());
        fields.forEach(function (field) {
            var inp = document.getElementById('gs-f-' + field.name);
            if (!inp) return;
            fd.append(
                field.name,
                inp.type === 'checkbox' ? (inp.checked ? 'true' : 'false') : inp.value
            );
        });

        fetch('/common/gs/settings/save/', {
            method : 'POST',
            body   : fd,
            headers: { 'X-Requested-With': 'XMLHttpRequest' },
        })
        .then(function (r) {
            if (!r.ok) throw new Error('HTTP ' + r.status);
            return r.json();
        })
        .then(function (d) {
            if (saveBtn) {
                saveBtn.disabled = false;
                saveBtn.innerHTML = _icon('Save') + ' Save';
            }
            if (d.success) {
                var now = new Date();
                var ts  = now.getHours() + ':' +
                          String(now.getMinutes()).padStart(2, '0') + ':' +
                          String(now.getSeconds()).padStart(2, '0');
                if (statusSpan) statusSpan.textContent = 'Saved ' + ts;
                _toast('Settings saved', 's');
            } else {
                if (statusSpan) statusSpan.textContent = 'Save failed';
                _toast(d.error || 'Could not save settings', 'e');
            }
        })
        .catch(function (err) {
            if (saveBtn) {
                saveBtn.disabled = false;
                saveBtn.innerHTML = _icon('Save') + ' Save';
            }
            if (statusSpan) statusSpan.textContent = 'Network error';
            console.error('[GS] save:', err);
            _toast('Network error saving settings', 'e');
        });
    }

    /* ══════════════════════════════════════════════════════════════════════
       IMAGE LOAD
    ══════════════════════════════════════════════════════════════════════ */
    function _loadImages(slots) {
        _setAllImagesBusy(slots, true, 'Loading…');

        fetch('/common/gs/images/load/', {
            headers: { 'X-Requested-With': 'XMLHttpRequest' }
        })
        .then(function (r) {
            if (!r.ok) throw new Error('HTTP ' + r.status);
            return r.json();
        })
        .then(function (d) {
            _setAllImagesBusy(slots, false);
            if (!d.success) { _toast(d.error || 'Could not load images', 'e'); return; }
            _imagePaths = d.images || {};
            var urls = d.serve_urls || {};
            slots.forEach(function (s) {
                _applyPreview(s.key, urls[s.key] || '', _imagePaths[s.key] || '');
            });
        })
        .catch(function (err) {
            _setAllImagesBusy(slots, false);
            console.error('[GS] image load:', err);
            _toast('Network error loading images', 'e');
        });
    }

    /* ══════════════════════════════════════════════════════════════════════
       FILE PICK & UPLOAD
    ══════════════════════════════════════════════════════════════════════ */
    function _pickFile(key) {
        var fi = document.getElementById('gs-file-' + key);
        if (fi) fi.click();
    }

    function _onFilePicked(key, inp) {
        if (!inp.files || !inp.files[0]) return;
        var file   = inp.files[0];
        var reader = new FileReader();
        reader.onload = function (e) { _applyPreview(key, e.target.result, ''); };
        reader.readAsDataURL(file);
        _doUpload(key, file);
        inp.value = '';
    }

    function _doUpload(key, file) {
        _setFieldBusy(key, true, 'Uploading…');

        var fd = new FormData();
        fd.append('image_type', key);
        fd.append('image_file', file, file.name);
        fd.append('csrfmiddlewaretoken', _csrf());

        fetch('/common/gs/images/upload/', {
            method : 'POST',
            body   : fd,
            headers: { 'X-Requested-With': 'XMLHttpRequest' },
        })
        .then(function (r) {
            if (!r.ok) throw new Error('HTTP ' + r.status);
            return r.json();
        })
        .then(function (d) {
            _setFieldBusy(key, false);
            if (d.success) {
                _imagePaths[key] = d.ftp_path;
                _applyPreview(key, d.serve_url, d.ftp_path);
                _toast(d.filename + ' uploaded', 's');
            } else {
                _revertPreview(key);
                _toast(d.error || 'Upload failed', 'e');
            }
        })
        .catch(function (err) {
            _setFieldBusy(key, false);
            _revertPreview(key);
            console.error('[GS] upload:', err);
            _toast('Network error during upload', 'e');
        });
    }

    function _revertPreview(key) {
        var existing = _imagePaths[key];
        _applyPreview(
            key,
            existing ? '/common/gs/images/serve/?path=' + encodeURIComponent(existing) : '',
            existing || ''
        );
    }

    /* ══════════════════════════════════════════════════════════════════════
       REMOVE
    ══════════════════════════════════════════════════════════════════════ */
    function _confirmRemove(key) {
        if (!_imagePaths[key]) { _toast('No image to remove', 'w'); return; }
        _confirm(
            'Remove this image? This cannot be undone.',
            function (ok) { if (ok) _doRemove(key); },
            'danger', 'Remove Image', 'Yes, Remove', 'Cancel'
        );
    }

    function _doRemove(key) {
        _setFieldBusy(key, true, 'Removing…');

        var fd = new FormData();
        fd.append('image_type', key);
        fd.append('csrfmiddlewaretoken', _csrf());

        fetch('/common/gs/images/delete/', {
            method : 'POST',
            body   : fd,
            headers: { 'X-Requested-With': 'XMLHttpRequest' },
        })
        .then(function (r) {
            if (!r.ok) throw new Error('HTTP ' + r.status);
            return r.json();
        })
        .then(function (d) {
            _setFieldBusy(key, false);
            if (d.success) {
                _imagePaths[key] = '';
                _applyPreview(key, '', '');
                _toast('Image removed', 's');
            } else {
                _toast(d.error || 'Could not remove image', 'e');
            }
        })
        .catch(function (err) {
            _setFieldBusy(key, false);
            console.error('[GS] remove:', err);
            _toast('Network error during remove', 'e');
        });
    }

    /* ══════════════════════════════════════════════════════════════════════
       UI HELPERS
    ══════════════════════════════════════════════════════════════════════ */
    function _applyPreview(key, src, ftpPath) {
        var img    = document.getElementById('gs-thumb-img-' + key);
        var ph     = document.getElementById('gs-thumb-ph-'  + key);
        var txtInp = document.getElementById('gs-inp-'       + key);
        var rmBtn  = document.getElementById('gs-rm-'        + key);
        if (!img) return;

        if (src) {
            img.src = src; img.style.display = 'block';
            if (ph)     ph.style.display    = 'none';
            if (rmBtn)  rmBtn.style.display = '';
            if (txtInp) txtInp.value = (ftpPath || src).split('/').pop() || src;
        } else {
            img.src = ''; img.style.display = 'none';
            if (ph)     ph.style.display    = '';
            if (rmBtn)  rmBtn.style.display = 'none';
            if (txtInp) txtInp.value        = '';
        }
    }

    function _setFieldBusy(key, busy, msg) {
        var field  = document.getElementById('gs-img-field-' + key);
        var browse = document.getElementById('gs-browse-'    + key);
        var rmBtn  = document.getElementById('gs-rm-'        + key);
        if (!field) return;

        var ov = field.querySelector('.gs-row-ov');
        if (busy) {
            if (!ov) {
                ov = document.createElement('div');
                ov.className = 'gs-row-ov';
                ov.style.cssText =
                    'position:absolute;inset:0;border-radius:4px;z-index:10;' +
                    'background:rgba(255,255,255,.85);display:flex;align-items:center;' +
                    'gap:7px;font-size:12px;color:var(--color-text-secondary,#64748b);padding:0 12px;';
                ov.innerHTML =
                    '<svg viewBox="0 0 24 24" width="13" height="13" fill="none"' +
                    ' stroke="currentColor" stroke-width="2"' +
                    ' style="animation:utm-spin 1s linear infinite;flex-shrink:0;">' +
                    '<path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83' +
                    'M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/></svg>' +
                    '<span></span>';
                field.appendChild(ov);
            }
            ov.querySelector('span').textContent = msg || 'Please wait…';
            if (browse) browse.disabled = true;
            if (rmBtn)  rmBtn.disabled  = true;
        } else {
            if (ov) ov.remove();
            if (browse) browse.disabled = false;
            if (rmBtn)  rmBtn.disabled  = false;
        }
    }

    function _setAllImagesBusy(slots, busy, msg) {
        (slots || []).forEach(function (s) { _setFieldBusy(s.key, busy, msg); });
    }

    /* ══════════════════════════════════════════════════════════════════════
       PUBLIC EXPORTS
    ══════════════════════════════════════════════════════════════════════ */
    global.openGlobalSettings = function () { _buildModal().open(); };

    global.globalSettingsModal = {
        open : function () { _buildModal().open();  },
        close: function () { if (_modal) _modal.close(); },
    };

}(window));