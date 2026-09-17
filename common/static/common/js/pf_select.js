/**
 * ================================================================
 *  common/static/common/js/pf_select.js   v1.4
 *
 *  v1.4 changes:
 *  ⑦ SEARCH-ONLY vs SEARCH+ADD split:
 *     • By default (type '3') — no "Add: …" row ever appears.
 *     • If the native <select> has data-allow-add="1" (type '19')
 *       — the existing "Add custom value" behaviour is preserved.
 *     The flag is read once at upgrade time and stored on the wrap
 *     so the inner search listener can check it cheaply.
 *
 *  v1.3 fixes (retained):
 *  ⑥ Removed accidental form.reset() / pf:reset dispatch.
 *
 *  v1.2 (retained):
 *  ④ Keyboard navigation
 *  ⑤ "Add custom value" (now gated by data-allow-add="1")
 *
 *  v1.1 (retained):
 *  ① pfSelSetValue accepts raw <select>
 *  ② _upgrade() stores sel._pfWrap back-reference
 *  ③ pfSelSetValue graceful fallback before upgrade
 * ================================================================
 */

(function () {
    'use strict';

    /* ── Init on DOM ready ─────────────────────────────────── */
    document.addEventListener('DOMContentLoaded', function () {
        _upgradeAll();
    });

    window.pfSelUpgradeAll = _upgradeAll;
    window.pfSelUpgradeOne = function (el) {
        if (!el || el.tagName !== 'SELECT') return;
        if (el.closest('.pf-sel-wrap') || el.closest('.pf-mchk-wrap')) return;
        if (el.getAttribute('data-no-upgrade') === '1') return;
        if (el.getAttribute('data-multi-check') === '1') {
            _upgradeMulti(el);
        } else {
            _upgrade(el);
        }
    };

    function _upgradeAll() {
        document.querySelectorAll(
            '.pf-field-ctl select, .pf-hf-ctl select'
        ).forEach(function (sel) {
            if (sel.closest('.pf-sel-wrap') || sel.closest('.pf-mchk-wrap')) return;
            if (sel.getAttribute('data-no-upgrade') === '1') return;
            if (sel.getAttribute('data-multi-check') === '1') {
                _upgradeMulti(sel);
            } else {
                _upgrade(sel);
            }
        });
    }

    // function _upgradeMulti(sel) {
    //     var name    = sel.name || sel.id || '';
    //     var options = Array.prototype.slice.call(sel.options);
    //     /* Collect pre-selected values from the native <select> */
    //     var selected = options.filter(function (o) { return o.selected; })
    //                           .map(function (o) { return o.value; });
 
    //     /* Wrapper */
    //     var wrap = document.createElement('div');
    //     wrap.className = 'pf-mchk-wrap';
    //     wrap.setAttribute('data-name', name);
 
    //     /* Trigger */
    //     var trigger = document.createElement('div');
    //     trigger.className = 'pf-sel-trigger pf-mchk-trigger';
    //     trigger.tabIndex  = 0;
    //     trigger.setAttribute('role', 'combobox');
    //     trigger.setAttribute('aria-haspopup', 'listbox');
    //     trigger.setAttribute('aria-expanded', 'false');
    //     trigger.setAttribute('aria-multiselectable', 'true');
 
    //     var valSpan = document.createElement('span');
    //     valSpan.className = 'pf-sel-val';
 
    //     var arrSpan = document.createElement('span');
    //     arrSpan.className   = 'pf-sel-arr';
    //     arrSpan.textContent = '▾';
 
    //     trigger.appendChild(valSpan);
    //     trigger.appendChild(arrSpan);
 
    //     /* Popup */
    //     var popup = document.createElement('div');
    //     popup.className = 'pf-sel-popup pf-mchk-popup';
    //     popup.setAttribute('role', 'listbox');
 
    //     var search = document.createElement('input');
    //     search.className    = 'pf-sel-search';
    //     search.type         = 'text';
    //     search.placeholder  = 'Search…';
    //     search.autocomplete = 'off';
 
    //     /* Clear-all link */
    //     var clearBar = document.createElement('div');
    //     clearBar.className = 'pf-mchk-clear-bar';
    //     clearBar.innerHTML = '<span class="pf-mchk-clear-link">Clear all</span>';
 
    //     var list = document.createElement('div');
    //     list.className = 'pf-sel-list pf-mchk-list';
 
    //     options.forEach(function (opt) {
    //         if (opt.value === '') return; /* skip blank placeholder */
    //         var item = document.createElement('div');
    //         item.className = 'pf-sel-opt pf-mchk-item';
    //         item.setAttribute('data-val', opt.value);
    //         item.setAttribute('role', 'option');
 
    //         var chk = document.createElement('input');
    //         chk.type      = 'checkbox';
    //         chk.className = 'pf-mchk-chk';
    //         chk.tabIndex  = -1;
    //         chk.checked   = selected.indexOf(opt.value) !== -1;
 
    //         var lbl = document.createElement('span');
    //         lbl.className   = 'pf-mchk-lbl';
    //         lbl.textContent = opt.text;
 
    //         item.appendChild(chk);
    //         item.appendChild(lbl);
    //         list.appendChild(item);
    //     });
 
    //     popup.appendChild(search);
    //     popup.appendChild(clearBar);
    //     popup.appendChild(list);
 
    //     sel.style.display = 'none';
    //     sel.setAttribute('data-upgraded', '1');
    //     sel.multiple = true; /* ensure native select supports multi */
 
    //     sel.parentNode.insertBefore(wrap, sel);
    //     wrap.appendChild(trigger);
    //     wrap.appendChild(popup);
    //     wrap.appendChild(sel);
 
    //     /* Back-references */
    //     sel._pfMchkWrap  = wrap;
    //     wrap._pfNative   = sel;
    //     wrap._pfValSpan  = valSpan;
    //     wrap._pfList     = list;
    //     wrap._pfSearch   = search;
 
    //     /* ── Internal helpers ── */
    //     function _selectedVals() {
    //         return Array.prototype.slice.call(
    //             list.querySelectorAll('.pf-mchk-item')
    //         ).filter(function (i) {
    //             return i.querySelector('.pf-mchk-chk').checked;
    //         }).map(function (i) {
    //             return i.getAttribute('data-val');
    //         });
    //     }
 
    //     function _updateTrigger() {
    //         var vals   = _selectedVals();
    //         var labels = vals.map(function (v) {
    //             var item = list.querySelector('.pf-mchk-item[data-val="' + v + '"]');
    //             return item ? item.querySelector('.pf-mchk-lbl').textContent : v;
    //         });
    //         valSpan.textContent = labels.length
    //             ? labels.join(', ')
    //             : (options[0] ? '' : '');
    //     }
 
    //     function _syncNative() {
    //         var vals = _selectedVals();
    //         Array.prototype.forEach.call(sel.options, function (o) {
    //             o.selected = vals.indexOf(o.value) !== -1;
    //         });
    //         sel.dispatchEvent(new CustomEvent('change', {
    //             bubbles: true,
    //             detail: { values: vals }
    //         }));
    //     }
 
    //     function _toggle(item) {
    //         var chk = item.querySelector('.pf-mchk-chk');
    //         chk.checked = !chk.checked;
    //         item.classList.toggle('pf-mchk-checked', chk.checked);
    //         _updateTrigger();
    //         _syncNative();
    //     }
 
    //     /* ── Initial render ── */
    //     list.querySelectorAll('.pf-mchk-item').forEach(function (item) {
    //         var v = item.getAttribute('data-val');
    //         item.classList.toggle('pf-mchk-checked', selected.indexOf(v) !== -1);
    //     });
    //     _updateTrigger();
 
    //     /* ── Trigger: click ── */
    //     trigger.addEventListener('click', function (e) {
    //         e.stopPropagation();
    //         var isOpen = popup.classList.contains('open');
    //         _closeAllMulti();
    //         _closeAll();
    //         if (!isOpen) _openMultiPopup(wrap, popup, search, trigger);
    //     });
 
    //     /* ── Trigger: keyboard ── */
    //     trigger.addEventListener('keydown', function (e) {
    //         if (e.key === 'Escape') { _closeMultiPopup(wrap, popup, trigger); return; }
    //         if (e.key === 'Tab') { _closeMultiPopup(wrap, popup, trigger); return; }
    //         if ((e.key === 'Enter' || e.key === ' ') && !popup.classList.contains('open')) {
    //             e.preventDefault();
    //             _openMultiPopup(wrap, popup, search, trigger);
    //         }
    //     });
 
    //     /* ── Search ── */
    //     search.addEventListener('input', function (e) {
    //         e.stopPropagation();
    //         var q = search.value.toLowerCase().trim();
    //         list.querySelectorAll('.pf-mchk-item').forEach(function (item) {
    //             var lbl = item.querySelector('.pf-mchk-lbl').textContent.toLowerCase();
    //             item.style.display = (!q || lbl.indexOf(q) !== -1) ? '' : 'none';
    //         });
    //     });
    //     search.addEventListener('click', function (e) { e.stopPropagation(); });
    //     search.addEventListener('keydown', function (e) {
    //         if (e.key === 'Escape') { e.preventDefault(); _closeMultiPopup(wrap, popup, trigger); }
    //         if (e.key === 'Tab')    { _closeMultiPopup(wrap, popup, trigger); }
    //     });
 
    //     /* ── List: click ── */
    //     list.addEventListener('click', function (e) {
    //         var item = e.target.closest('.pf-mchk-item');
    //         if (!item) return;
    //         e.stopPropagation();
    //         /* If user clicked the checkbox itself, let it toggle naturally,
    //            then sync; otherwise manually toggle */
    //         if (e.target.classList.contains('pf-mchk-chk')) {
    //             item.classList.toggle('pf-mchk-checked', e.target.checked);
    //             _updateTrigger();
    //             _syncNative();
    //         } else {
    //             _toggle(item);
    //         }
    //     });
 
    //     /* ── Clear-all ── */
    //     clearBar.addEventListener('click', function (e) {
    //         e.stopPropagation();
    //         list.querySelectorAll('.pf-mchk-item').forEach(function (item) {
    //             item.querySelector('.pf-mchk-chk').checked = false;
    //             item.classList.remove('pf-mchk-checked');
    //         });
    //         _updateTrigger();
    //         _syncNative();
    //     });
 
    //     /* ── Reset ── */
    //     function _resetMulti() {
    //         list.querySelectorAll('.pf-mchk-item').forEach(function (item) {
    //             item.querySelector('.pf-mchk-chk').checked = false;
    //             item.classList.remove('pf-mchk-checked');
    //         });
    //         _updateTrigger();
    //         search.value = '';
    //         list.querySelectorAll('.pf-mchk-item').forEach(function (i) { i.style.display = ''; });
    //         _closeMultiPopup(wrap, popup, trigger);
    //     }
 
    //     var form = sel.closest('form');
    //     if (form) {
    //         form.addEventListener('reset',    _resetMulti);
    //         form.addEventListener('pf:reset', _resetMulti);
    //     }
    //     wrap.addEventListener('pf:reset', _resetMulti);
    // }


    function _upgradeMulti(sel) {
        var name    = sel.name || sel.id || '';
        var options = Array.prototype.slice.call(sel.options);
        /* Collect pre-selected values from the native <select> */
         var selected = options.filter(function (o) { return o.selected && o.getAttribute('selected') !== null; })
                              .map(function (o) { return o.value; });
 
        /* Wrapper */
        var wrap = document.createElement('div');
        wrap.className = 'pf-mchk-wrap';
        wrap.setAttribute('data-name', name);
 
        /* Trigger */
        var trigger = document.createElement('div');
        trigger.className = 'pf-sel-trigger pf-mchk-trigger';
        trigger.tabIndex  = 0;
        trigger.setAttribute('role', 'combobox');
        trigger.setAttribute('aria-haspopup', 'listbox');
        trigger.setAttribute('aria-expanded', 'false');
        trigger.setAttribute('aria-multiselectable', 'true');
 
        var valSpan = document.createElement('span');
        valSpan.className = 'pf-sel-val';
 
        var arrSpan = document.createElement('span');
        arrSpan.className   = 'pf-sel-arr';
        arrSpan.textContent = '▾';
 
        trigger.appendChild(valSpan);
        trigger.appendChild(arrSpan);
 
        /* Popup */
        var popup = document.createElement('div');
        popup.className = 'pf-mchk-popup';
        popup.setAttribute('role', 'listbox');
 
        var search = document.createElement('input');
        search.className    = 'pf-sel-search';
        search.type         = 'text';
        search.placeholder  = 'Search…';
        search.autocomplete = 'off';
 
        /* Clear-all link */
        var clearBar = document.createElement('div');
        clearBar.className = 'pf-mchk-clear-bar';
        clearBar.innerHTML = '<span class="pf-mchk-clear-link">Clear all</span>';
 
        var list = document.createElement('div');
        list.className = 'pf-sel-list pf-mchk-list';
 
        options.forEach(function (opt) {
            if (opt.value === '') return; /* skip blank placeholder */
            var item = document.createElement('div');
            item.className = 'pf-sel-opt pf-mchk-item';
            item.setAttribute('data-val', opt.value);
            item.setAttribute('role', 'option');
 
            var chk = document.createElement('input');
            chk.type      = 'checkbox';
            chk.className = 'pf-mchk-chk';
            chk.tabIndex  = -1;
            chk.checked   = selected.indexOf(opt.value) !== -1;
 
            var lbl = document.createElement('span');
            lbl.className   = 'pf-mchk-lbl';
            lbl.textContent = opt.text;
 
            item.appendChild(chk);
            item.appendChild(lbl);
            list.appendChild(item);
        });
 
        popup.appendChild(search);
        popup.appendChild(clearBar);
        popup.appendChild(list);
 
        sel.style.display = 'none';
        sel.setAttribute('data-upgraded', '1');
        sel.multiple = true; /* ensure native select supports multi */
 
        sel.parentNode.insertBefore(wrap, sel);
        wrap.appendChild(trigger);
        wrap.appendChild(popup);
        wrap.appendChild(sel);
 
        /* Back-references */
        sel._pfMchkWrap  = wrap;
        wrap._pfNative   = sel;
        wrap._pfValSpan  = valSpan;
        wrap._pfList     = list;
        wrap._pfSearch   = search;
        popup._pfWrap    = wrap;
 
        /* ── Internal helpers ── */
        function _selectedVals() {
            return Array.prototype.slice.call(
                list.querySelectorAll('.pf-mchk-item')
            ).filter(function (i) {
                return i.querySelector('.pf-mchk-chk').checked;
            }).map(function (i) {
                return i.getAttribute('data-val');
            });
        }
 
        function _updateTrigger() {
            var vals   = _selectedVals();
            var labels = vals.map(function (v) {
                var item = list.querySelector('.pf-mchk-item[data-val="' + v + '"]');
                return item ? item.querySelector('.pf-mchk-lbl').textContent : v;
            });
            valSpan.textContent = labels.length
                ? labels.join(', ')
                : (options[0] ? '' : '');
        }
 
        function _syncNative() {
            var vals = _selectedVals();
            Array.prototype.forEach.call(sel.options, function (o) {
                o.selected = vals.indexOf(o.value) !== -1;
            });
            sel.dispatchEvent(new CustomEvent('change', {
                bubbles: true,
                detail: { values: vals }
            }));
        }
 
        function _toggle(item) {
            var chk = item.querySelector('.pf-mchk-chk');
            chk.checked = !chk.checked;
            item.classList.toggle('pf-mchk-checked', chk.checked);
            _updateTrigger();
            _syncNative();
        }
 
        /* ── Initial render ── */
        list.querySelectorAll('.pf-mchk-item').forEach(function (item) {
            var v = item.getAttribute('data-val');
            item.classList.toggle('pf-mchk-checked', selected.indexOf(v) !== -1);
        });
        _updateTrigger();
 
        /* ── Trigger: click ── */
        trigger.addEventListener('click', function (e) {
            e.stopPropagation();
            var isOpen = popup.classList.contains('open');
            _closeAllMulti();
            _closeAll();
            if (!isOpen) _openMultiPopup(wrap, popup, search, trigger);
        });
 
        /* ── Trigger: keyboard ── */
        trigger.addEventListener('keydown', function (e) {
            if (e.key === 'Escape') { _closeMultiPopup(wrap, popup, trigger); return; }
            if (e.key === 'Tab') { _closeMultiPopup(wrap, popup, trigger); return; }
            if ((e.key === 'Enter' || e.key === ' ') && !popup.classList.contains('open')) {
                e.preventDefault();
                _openMultiPopup(wrap, popup, search, trigger);
            }
        });
 
        /* ── Search ── */
        search.addEventListener('input', function (e) {
            e.stopPropagation();
            var q = search.value.toLowerCase().trim();
            list.querySelectorAll('.pf-mchk-item').forEach(function (item) {
                var lbl = item.querySelector('.pf-mchk-lbl').textContent.toLowerCase();
                item.style.display = (!q || lbl.indexOf(q) !== -1) ? '' : 'none';
            });
        });
        search.addEventListener('click', function (e) { e.stopPropagation(); });
        search.addEventListener('keydown', function (e) {
            if (e.key === 'Escape') { e.preventDefault(); _closeMultiPopup(wrap, popup, trigger); }
            if (e.key === 'Tab')    { _closeMultiPopup(wrap, popup, trigger); }
        });
 
        /* ── List: click ── */
        list.addEventListener('click', function (e) {
            var item = e.target.closest('.pf-mchk-item');
            if (!item) return;
            e.stopPropagation();
            /* If user clicked the checkbox itself, let it toggle naturally,
               then sync; otherwise manually toggle */
            if (e.target.classList.contains('pf-mchk-chk')) {
                item.classList.toggle('pf-mchk-checked', e.target.checked);
                _updateTrigger();
                _syncNative();
            } else {
                _toggle(item);
            }
        });
 
        /* ── Clear-all ── */
        clearBar.addEventListener('click', function (e) {
            e.stopPropagation();
            list.querySelectorAll('.pf-mchk-item').forEach(function (item) {
                item.querySelector('.pf-mchk-chk').checked = false;
                item.classList.remove('pf-mchk-checked');
            });
            _updateTrigger();
            _syncNative();
        });
 
        /* ── Reset ── */
        function _resetMulti() {
            list.querySelectorAll('.pf-mchk-item').forEach(function (item) {
                item.querySelector('.pf-mchk-chk').checked = false;
                item.classList.remove('pf-mchk-checked');
            });
            _updateTrigger();
            search.value = '';
            list.querySelectorAll('.pf-mchk-item').forEach(function (i) { i.style.display = ''; });
            _closeMultiPopup(wrap, popup, trigger);
        }
 
        var form = sel.closest('form');
        if (form) {
            form.addEventListener('reset',    _resetMulti);
            form.addEventListener('pf:reset', _resetMulti);
        }

        function _repositionPopup() {
            if (!popup.classList.contains('open')) return;
            var rect2   = trigger.getBoundingClientRect();
            var scrollX = window.pageXOffset || document.documentElement.scrollLeft;
            var scrollY = window.pageYOffset || document.documentElement.scrollTop;
            var below2  = window.innerHeight - rect2.bottom;
            popup.style.left  = (rect2.left + scrollX) + 'px';
            popup.style.width = rect2.width + 'px';
            if (below2 < 240 && rect2.top > 240) {
                var ph = popup.offsetHeight;
                popup.style.top    = (rect2.top + scrollY - ph - 3) + 'px';
                popup.style.bottom = 'auto';
            } else {
                popup.style.top    = (rect2.bottom + scrollY + 3) + 'px';
                popup.style.bottom = 'auto';
            }
        }

        window.addEventListener('scroll', _repositionPopup, true);
        window.addEventListener('resize', _repositionPopup);

        
        wrap.addEventListener('pf:reset', _resetMulti);
    }
 
 
    /* ── Multi open / close ────────────────────────────────── */
    function _openMultiPopup(wrap, popup, search, trigger) {
        if (popup.parentNode !== document.body) {
            document.body.appendChild(popup);
        }
 
        var trigRect = trigger ? trigger.getBoundingClientRect() : wrap.getBoundingClientRect();
        var wrapRect = wrap ? wrap.getBoundingClientRect() : trigRect;
        var scrollX  = window.pageXOffset || document.documentElement.scrollLeft;
        var scrollY  = window.pageYOffset || document.documentElement.scrollTop;
        var below    = window.innerHeight - trigRect.bottom;
        var popW     = trigRect.width;
 
        popup.style.position = 'absolute';
        popup.style.zIndex   = '9999';
        popup.style.left     = (wrapRect.left + scrollX) + 'px';
        popup.style.width    = popW + 'px';
        popup.style.right    = 'auto';
 
        if (below < 240 && trigRect.top > 240) {
            popup.style.top    = 'auto';
            popup.style.bottom = 'auto';
            popup.style.top    = (trigRect.top + scrollY - 4) + 'px';
        } else {
            popup.style.top    = (trigRect.bottom + scrollY + 3) + 'px';
            popup.style.bottom = 'auto';
        }
 
        popup.classList.add('open');
 
        if (below < 240 && trigRect.top > 240) {
            var ph = popup.offsetHeight;
            popup.style.top = (trigRect.top + scrollY - ph - 3) + 'px';
        }
 
        if (trigger) {
            trigger.classList.add('open');
            trigger.setAttribute('aria-expanded', 'true');
        }
 
        search.value = '';
        popup.querySelectorAll('.pf-mchk-item').forEach(function (i) {
            i.style.display = '';
        });
 
        search.focus();
    }

 
    function _closeMultiPopup(wrap, popup, trigger) {
        popup.classList.remove('open');
        /* Return popup to its wrap */
        if (wrap && popup.parentNode !== wrap) {
            wrap.appendChild(popup);
        }
        popup.style.top    = '';
        popup.style.bottom = '';
        popup.style.left   = '';
        popup.style.width  = '';
 
        var trig = trigger || (wrap && wrap.querySelector('.pf-mchk-trigger'));
        if (trig) {
            trig.classList.remove('open');
            trig.setAttribute('aria-expanded', 'false');
        }
    }


    function _repositionAllSelectPopups() {
    document.querySelectorAll('.pf-sel-popup.open').forEach(function (popup) {
        if (popup.classList.contains('pf-mchk-popup')) return; /* handled separately */
        var wrap = popup._pfWrap || popup.closest('.pf-sel-wrap');
        if (!wrap) return;
        var rect2   = wrap.getBoundingClientRect();
        var scrollX = window.pageXOffset || document.documentElement.scrollLeft;
        var scrollY = window.pageYOffset || document.documentElement.scrollTop;
        var below2  = window.innerHeight - rect2.bottom;
        popup.style.left  = (rect2.left + scrollX) + 'px';
        popup.style.width = rect2.width + 'px';
        if (below2 < 220 && rect2.top > 220) {
            var ph = popup.offsetHeight;
            popup.style.top    = (rect2.top + scrollY - ph - 3) + 'px';
            popup.style.bottom = 'auto';
        } else {
            popup.style.top    = (rect2.bottom + scrollY + 3) + 'px';
            popup.style.bottom = 'auto';
        }
    });
}
window.addEventListener('scroll', _repositionAllSelectPopups, true);
window.addEventListener('resize', _repositionAllSelectPopups);


 
    function _closeAllMulti() {
        document.querySelectorAll('.pf-mchk-popup.open').forEach(function (p) {
            /* popup may be body-mounted; find wrap via stored reference */
            var w = p._pfWrap || p.closest('.pf-mchk-wrap');
            var t = w ? w.querySelector('.pf-mchk-trigger') : null;
            _closeMultiPopup(w, p, t);
        });
    }

    /* ── Upgrade a single <select> ─────────────────────────── */
    function _upgrade(sel) {
        var name    = sel.name || sel.id || '';
        var options = Array.prototype.slice.call(sel.options);
        var current = sel.value;

        /* ── v1.4: read the allow-add flag ONCE at upgrade time ── */
        var allowAdd = sel.getAttribute('data-allow-add') === '1';

        /* Build wrapper */
        var wrap = document.createElement('div');
        wrap.className = 'pf-sel-wrap';
        wrap.setAttribute('data-name', name);
        /* Expose on the wrap so external code can query it */
        wrap._pfAllowAdd = allowAdd;

        /* Trigger */
        var trigger = document.createElement('div');
        trigger.className = 'pf-sel-trigger';
        trigger.tabIndex  = 0;
        trigger.setAttribute('role', 'combobox');
        trigger.setAttribute('aria-haspopup', 'listbox');
        trigger.setAttribute('aria-expanded', 'false');

        var valSpan = document.createElement('span');
        valSpan.className   = 'pf-sel-val';
        valSpan.textContent = _labelFor(options, current) || (options[0] ? options[0].text : '');

        var arrSpan = document.createElement('span');
        arrSpan.className   = 'pf-sel-arr';
        arrSpan.textContent = '▾';

        trigger.appendChild(valSpan);
        trigger.appendChild(arrSpan);

        /* Popup */
        var popup = document.createElement('div');
        popup.className = 'pf-sel-popup';
        popup.setAttribute('role', 'listbox');

        var search = document.createElement('input');
        search.className    = 'pf-sel-search';
        search.type         = 'text';
        search.placeholder  = 'Search…';
        search.autocomplete = 'off';
        search.setAttribute('aria-autocomplete', 'list');

        var list = document.createElement('div');
        list.className = 'pf-sel-list';

        options.forEach(function (opt) {
            var item = document.createElement('div');
            item.className   = 'pf-sel-opt';
            item.setAttribute('data-val', opt.value);
            item.setAttribute('role', 'option');
            item.textContent = opt.text;
            if (opt.value === current) {
                item.classList.add('selected');
                item.setAttribute('aria-selected', 'true');
            } else {
                item.setAttribute('aria-selected', 'false');
            }
            // ── NEW: mirror the native option's disabled state ──
            if (opt.disabled) {
                item.classList.add('pf-sel-disabled');
                item.setAttribute('aria-disabled', 'true');
            }
            list.appendChild(item);
        });

        popup.appendChild(search);
        popup.appendChild(list);

        sel.style.display = 'none';
        sel.setAttribute('data-upgraded', '1');

        sel.parentNode.insertBefore(wrap, sel);
        wrap.appendChild(trigger);
        wrap.appendChild(popup);
        wrap.appendChild(sel);

        sel._pfWrap     = wrap;
        wrap._pfNative  = sel;
        wrap._pfValSpan = valSpan;
        wrap._pfList    = list;
        wrap._pfSearch  = search;

        /* ── Snapshot original options for reset ── */
        var _originalValues = options.map(function (o) { return o.value; });

        function _resetToOriginal() {
            Array.prototype.slice.call(sel.options).forEach(function (o) {
                if (_originalValues.indexOf(o.value) === -1) o.remove();
            });
            list.querySelectorAll('.pf-sel-opt').forEach(function (item) {
                var v = item.getAttribute('data-val');
                if (_originalValues.indexOf(v) === -1) item.remove();
            });
            var resetVal = sel.value;
            list.querySelectorAll('.pf-sel-opt').forEach(function (item) {
                var match = item.getAttribute('data-val') === resetVal;
                item.classList.toggle('selected', match);
                item.classList.remove('pf-sel-highlighted');
                item.setAttribute('aria-selected', match ? 'true' : 'false');
            });
            valSpan.textContent = _labelFor(
                Array.prototype.slice.call(sel.options), resetVal
            ) || (sel.options[0] ? sel.options[0].text : '');
            search.value = '';
            _closePopup(wrap, popup, trigger);
        }

        var form = sel.closest('form');
        if (form) {
            form.addEventListener('reset',    _resetToOriginal);
            form.addEventListener('pf:reset', _resetToOriginal);
        }
        wrap.addEventListener('pf:reset', _resetToOriginal);

        /* ── Helpers ── */
        function _visibleItems() {
            return Array.prototype.filter.call(
                list.querySelectorAll('.pf-sel-opt'),
                function (o) {
                    return o.style.display !== 'none' &&
                           !o.classList.contains('pf-sel-no-match');
                }
            );
        }

        function _moveHighlight(direction) {
            var items = _visibleItems();
            if (!items.length) return;
            var cur = list.querySelector('.pf-sel-opt.pf-sel-highlighted');
            var idx = items.indexOf(cur);
            if (cur) cur.classList.remove('pf-sel-highlighted');
            if (idx === -1) {
                idx = direction > 0 ? 0 : items.length - 1;
            } else {
                idx = idx + direction;
                if (idx < 0)             idx = 0;
                if (idx >= items.length) idx = items.length - 1;
            }
            var target = items[idx];
            target.classList.add('pf-sel-highlighted');
            target.scrollIntoView({ block: 'nearest' });
        }

        function _confirmHighlighted() {
            var item = list.querySelector('.pf-sel-opt.pf-sel-highlighted');
            if (!item) {
                var visible = _visibleItems();
                if (visible.length === 1) item = visible[0];
            }
            if (!item) return;
            item.dispatchEvent(new MouseEvent('click', { bubbles: true }));
        }

        /* ── Trigger: click ── */
        trigger.addEventListener('click', function (e) {
            e.stopPropagation();
            var isOpen = popup.classList.contains('open');
            _closeAll();
            if (!isOpen) _openPopup(wrap, popup, search, trigger);
        });

        /* ── Trigger: keyboard ── */
        trigger.addEventListener('keydown', function (e) {
            var isOpen = popup.classList.contains('open');
            switch (e.key) {
                case 'Enter':
                case ' ':
                    e.preventDefault();
                    if (isOpen) { _confirmHighlighted(); }
                    else { _openPopup(wrap, popup, search, trigger); }
                    break;
                case 'ArrowDown':
                    e.preventDefault();
                    if (!isOpen) { _openPopup(wrap, popup, search, trigger); }
                    else { _moveHighlight(+1); }
                    break;
                case 'ArrowUp':
                    e.preventDefault();
                    if (!isOpen) { _openPopup(wrap, popup, search, trigger); }
                    else { _moveHighlight(-1); }
                    break;
                case 'Home':
                    if (isOpen) { e.preventDefault(); _moveHighlight(-Infinity); }
                    break;
                case 'End':
                    if (isOpen) { e.preventDefault(); _moveHighlight(+Infinity); }
                    break;
                case 'Escape':
                    if (isOpen) { e.preventDefault(); _closePopup(wrap, popup, trigger); }
                    break;
                case 'Tab':
                    if (isOpen) _closePopup(wrap, popup, trigger);
                    break;
                default:
                    if (!isOpen && e.key.length === 1 && !e.ctrlKey && !e.metaKey && !e.altKey) {
                        e.preventDefault();
                        _openPopup(wrap, popup, search, trigger);
                        search.value = e.key;
                        search.dispatchEvent(new Event('input'));
                    }
                    break;
            }
        });

        /* ── Search box: filter + highlight ── */
        search.addEventListener('input', function (e) {
            e.stopPropagation();
            var raw   = search.value.trim();
            var q     = raw.toLowerCase();
            var items = list.querySelectorAll('.pf-sel-opt:not(.pf-sel-no-match-msg)');
            var any   = false;

            items.forEach(function (item) {
                item.classList.remove('pf-sel-highlighted');
                var match = !q || item.textContent.toLowerCase().indexOf(q) !== -1;
                item.style.display = match ? '' : 'none';
                if (match) any = true;
            });

            var nm = list.querySelector('.pf-sel-no-match-msg');

            if (!any && q) {
                /* ── v1.4: only show "Add" row when allowAdd is true ── */
                if (allowAdd) {
                    if (!nm) {
                        nm = document.createElement('div');
                        nm.className = 'pf-sel-opt pf-sel-add-new pf-sel-no-match-msg';
                        nm.setAttribute('role', 'option');
                        list.appendChild(nm);
                    }
                    nm.textContent = raw;
                    nm.setAttribute('data-add-val', raw);
                    nm.classList.add('pf-sel-highlighted');
                } else {
                    /* Search-only: show "No match" message instead */
                    if (!nm) {
                        nm = document.createElement('div');
                        nm.className   = 'pf-sel-opt pf-sel-no-match pf-sel-no-match-msg';
                        nm.textContent = 'No match';
                        list.appendChild(nm);
                    }
                }
            } else if (!any) {
                if (!nm) {
                    nm = document.createElement('div');
                    nm.className   = 'pf-sel-opt pf-sel-no-match pf-sel-no-match-msg';
                    nm.textContent = 'No match';
                    list.appendChild(nm);
                }
            } else {
                if (nm) nm.remove();
                if (q) {
                    var first = _visibleItems()[0];
                    if (first) first.classList.add('pf-sel-highlighted');
                }
            }
        });

        /* ── Search box: arrow keys ── */
        search.addEventListener('keydown', function (e) {
            switch (e.key) {
                case 'ArrowDown':  e.preventDefault(); _moveHighlight(+1);        break;
                case 'ArrowUp':    e.preventDefault(); _moveHighlight(-1);        break;
                case 'Enter':      e.preventDefault(); _confirmHighlighted();     break;
                case 'Home':       e.preventDefault(); _moveHighlight(-Infinity); break;
                case 'End':        e.preventDefault(); _moveHighlight(+Infinity); break;
                case 'Escape':     e.preventDefault(); _closePopup(wrap, popup, trigger); break;
                case 'Tab':        _closePopup(wrap, popup, trigger); break;
            }
        });

        search.addEventListener('click', function (e) { e.stopPropagation(); });

        /* ── List: click to select ── */
        list.addEventListener('click', function (e) {
            var item = e.target.closest('.pf-sel-opt');
            if (!item || item.classList.contains('pf-sel-no-match')) return;
            if (item.classList.contains('pf-sel-disabled')) return; 

            /* ── Add custom value (only when allowAdd) ── */
            if (item.classList.contains('pf-sel-add-new')) {
                if (!allowAdd) return;   /* safety guard */

                var newVal   = item.getAttribute('data-add-val');
                var newLabel = newVal;

                var newOpt         = document.createElement('option');
                newOpt.value       = newVal;
                newOpt.textContent = newLabel;
                sel.appendChild(newOpt);

                var newItem = document.createElement('div');
                newItem.className = 'pf-sel-opt';
                newItem.setAttribute('data-val', newVal);
                newItem.setAttribute('role', 'option');
                newItem.textContent = newLabel;
                list.insertBefore(newItem, item);
                item.remove();

                list.querySelectorAll('.pf-sel-opt').forEach(function (o) {
                    o.classList.remove('selected', 'pf-sel-highlighted');
                    o.setAttribute('aria-selected', 'false');
                });
                newItem.classList.add('selected');
                newItem.setAttribute('aria-selected', 'true');
                valSpan.textContent = newLabel;
                sel.value = newVal;
                sel.dispatchEvent(new Event('change', { bubbles: true }));
                _closePopup(wrap, popup, trigger);
                return;
            }

            /* ── Normal option ── */
            var val   = item.getAttribute('data-val');
            var label = item.textContent;

            valSpan.textContent = label;
            list.querySelectorAll('.pf-sel-opt').forEach(function (o) {
                o.classList.remove('selected', 'pf-sel-highlighted');
                o.setAttribute('aria-selected', 'false');
            });
            item.classList.add('selected');
            item.setAttribute('aria-selected', 'true');
            sel.value = val;
            sel.dispatchEvent(new Event('change', { bubbles: true }));
            _closePopup(wrap, popup, trigger);
        });
    }

    /* ── Open / close ──────────────────────────────────────── */
    // NEW
function _openPopup(wrap, popup, search, trigger) {
    /* Portal to <body> so the popup escapes any ancestor stacking
       context (hero card, sticky tabs, etc.) — same fix already
       applied to the multi-check dropdown in _openMultiPopup(). */
    if (popup.parentNode !== document.body) {
        document.body.appendChild(popup);
    }
    popup._pfWrap = wrap;

    var rect    = wrap.getBoundingClientRect();
    var scrollX = window.pageXOffset || document.documentElement.scrollLeft;
    var scrollY = window.pageYOffset || document.documentElement.scrollTop;
    var below   = window.innerHeight - rect.bottom;

    popup.style.position = 'absolute';
    popup.style.zIndex   = '9999';
    popup.style.left     = (rect.left + scrollX) + 'px';
    popup.style.width    = rect.width + 'px';
    popup.style.right    = 'auto';

    if (below < 220 && rect.top > 220) {
        popup.style.top    = 'auto';
        popup.style.bottom = 'auto';
    } else {
        popup.style.top    = (rect.bottom + scrollY + 3) + 'px';
        popup.style.bottom = 'auto';
    }

    popup.classList.add('open');
    if (trigger) {
        trigger.classList.add('open');
        trigger.setAttribute('aria-expanded', 'true');
    }
    search.value = '';

    popup.querySelectorAll('.pf-sel-opt').forEach(function (o) {
        o.style.display = '';
        o.classList.remove('pf-sel-highlighted');
    });

    var nm = popup.querySelector('.pf-sel-no-match-msg');
    if (nm) nm.remove();

    /* Flip upward now that we know the popup's real height */
    if (below < 220 && rect.top > 220) {
        var ph = popup.offsetHeight;
        popup.style.top = (rect.top + scrollY - ph - 3) + 'px';
    }

    search.focus();
}
    // NEW
function _closePopup(wrap, popup, trigger) {
    popup.classList.remove('open');

    /* Return popup to its wrap so it's back in normal flow when closed */
    if (wrap && popup.parentNode !== wrap) {
        wrap.appendChild(popup);
    }
    popup.style.position = '';
    popup.style.top      = '';
    popup.style.bottom   = '';
    popup.style.left     = '';
    popup.style.width    = '';
    popup.style.zIndex   = '';

    popup.querySelectorAll('.pf-sel-highlighted').forEach(function (o) {
        o.classList.remove('pf-sel-highlighted');
    });
    var trig = trigger || (wrap && wrap.querySelector('.pf-sel-trigger'));
    if (trig) {
        trig.classList.remove('open');
        trig.setAttribute('aria-expanded', 'false');
    }
}

    function _closeAll() {
        document.querySelectorAll('.pf-sel-popup.open').forEach(function (p) {
            if (p.classList.contains('pf-mchk-popup')) return; /* handled by _closeAllMulti */
            var w = p.closest('.pf-sel-wrap') || p._pfWrap || null;
            var t = w ? w.querySelector('.pf-sel-trigger') : null;
            _closePopup(w, p, t);
        });
    }

    document.addEventListener('click', function (e) {
        if (!e.target.closest('.pf-sel-wrap') &&
            !e.target.closest('.pf-sel-popup'))   _closeAll();
        if (!e.target.closest('.pf-mchk-wrap') &&
            !e.target.closest('.pf-mchk-popup'))  _closeAllMulti();
    });

    /* ── Public API ────────────────────────────────────────── */
    window.pfSelSetValue = function (nameOrEl, value) {
        var wrap = null;
        if (typeof nameOrEl === 'string') {
            wrap = document.querySelector('.pf-sel-wrap[data-name="' + nameOrEl + '"]');
            if (!wrap) {
                var byName = document.querySelector('select[name="' + nameOrEl + '"]');
                if (byName && byName._pfWrap) wrap = byName._pfWrap;
            }
        } else if (nameOrEl && nameOrEl.tagName === 'SELECT') {
            wrap = nameOrEl._pfWrap || (nameOrEl.closest ? nameOrEl.closest('.pf-sel-wrap') : null);
        } else if (nameOrEl && nameOrEl.closest) {
            wrap = nameOrEl.closest('.pf-sel-wrap');
        }
        if (!wrap || !wrap._pfList) return;

        var strVal = String(value !== null && value !== undefined ? value : '');
        var item   = null;
        wrap._pfList.querySelectorAll('.pf-sel-opt').forEach(function (o) {
            if (o.getAttribute('data-val') === strVal) item = o;
        });
        if (item) {
            wrap._pfList.querySelectorAll('.pf-sel-opt').forEach(function (o) {
                o.classList.remove('selected', 'pf-sel-highlighted');
                o.setAttribute('aria-selected', 'false');
            });
            item.classList.add('selected');
            item.setAttribute('aria-selected', 'true');
            if (wrap._pfValSpan) wrap._pfValSpan.textContent = item.textContent;
            if (wrap._pfNative) {
                wrap._pfNative.value = strVal;
                wrap._pfNative.dispatchEvent(new Event('change', { bubbles: true }));
            }
        }
    };

    window.pfSelGetValue = function (name) {
        var wrap = document.querySelector('.pf-sel-wrap[data-name="' + name + '"]');
        return wrap && wrap._pfNative ? wrap._pfNative.value : '';
    };

    window.pfSelRefresh = function (name) {
        var wrap = document.querySelector('.pf-sel-wrap[data-name="' + name + '"]');
        if (!wrap || !wrap._pfNative) return;
        var sel = wrap._pfNative;
        sel.style.display = '';
        sel.removeAttribute('data-upgraded');
        delete sel._pfWrap;
        wrap.parentNode.insertBefore(sel, wrap);
        wrap.remove();
        _upgrade(sel);
    };

    window.pfSelGetValues = function (nameOrEl) {
        var wrap = null;
        if (typeof nameOrEl === 'string') {
            wrap = document.querySelector('.pf-mchk-wrap[data-name="' + nameOrEl + '"]');
        } else if (nameOrEl && nameOrEl._pfMchkWrap) {
            wrap = nameOrEl._pfMchkWrap;
        }
        if (!wrap || !wrap._pfNative) return [];
        return Array.prototype.filter.call(wrap._pfNative.options, function (o) {
            return o.selected;
        }).map(function (o) { return o.value; });
    };
 
    /* ── Multi-check: set checked values programmatically ── */
    window.pfSelSetValues = function (nameOrEl, valArr) {
        var wrap = null;
        if (typeof nameOrEl === 'string') {
            wrap = document.querySelector('.pf-mchk-wrap[data-name="' + nameOrEl + '"]');
        } else if (nameOrEl && nameOrEl._pfMchkWrap) {
            wrap = nameOrEl._pfMchkWrap;
        }
        if (!wrap || !wrap._pfList) return;
        var vals = valArr || [];
        wrap._pfList.querySelectorAll('.pf-mchk-item').forEach(function (item) {
            var v    = item.getAttribute('data-val');
            var chk  = item.querySelector('.pf-mchk-chk');
            var on   = vals.indexOf(v) !== -1;
            chk.checked = on;
            item.classList.toggle('pf-mchk-checked', on);
        });
        /* Sync native <select> */
        if (wrap._pfNative) {
            Array.prototype.forEach.call(wrap._pfNative.options, function (o) {
                o.selected = vals.indexOf(o.value) !== -1;
            });
        }
        /* Update trigger label */
        if (wrap._pfValSpan) {
            var labels = vals.map(function (v) {
                var item = wrap._pfList.querySelector('.pf-mchk-item[data-val="' + v + '"]');
                return item ? item.querySelector('.pf-mchk-lbl').textContent : v;
            });
            wrap._pfValSpan.textContent = labels.join(', ');
        }
    };
    

    /* ── Utils ─────────────────────────────────────────────── */
    function _labelFor(options, value) {
        for (var i = 0; i < options.length; i++) {
            if (options[i].value === value) return options[i].text;
        }
        return '';
    }

}());