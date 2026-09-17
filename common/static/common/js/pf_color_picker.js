/**
 * pf_color_picker.js
 * common/static/common/js/pf_color_picker.js
 * ─────────────────────────────────────────────────────────────────
 * Reusable inline color-picker widget.
 * Icons are taken from PF_ICONS (profile_form.js) when available.
 *
 * Load order in base template:
 *   1. profile_form.js   ← defines PF_ICONS (via pfOpenMenu exposure)
 *   2. pf_color_picker.js
 *   3. rpt_filter.js
 *
 * API:
 *   var picker = PfColorPicker.create({ value, onChange });
 *   picker.el          → HTMLElement  (append wherever needed)
 *   picker.getValue()  → '#rrggbb' | ''
 *   picker.setValue(hex)
 *   picker.clear()
 *
 * Options:
 *   value    {string}   Initial hex color e.g. '#ffccaa', or '' for none.
 *   onChange {function} Called with (hex|'') on every change.
 * ─────────────────────────────────────────────────────────────────
 */
(function (global) {
    'use strict';

    /* ── icon helper ─────────────────────────────────────────────
       Tries PF_ICONS['Remove'] first (profile_form.js must be loaded).
       Falls back to an inline SVG × so the widget never breaks.
    ──────────────────────────────────────────────────────────────*/
    function _icon(key, fallbackPaths) {
        /* PF_ICONS is exposed on window via pfOpenMenu in profile_form.js */
        if (global.PF_ICONS && global.PF_ICONS[key]) {
            return global.PF_ICONS[key];
        }
        /* inline fallback */
        return (
            '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" ' +
            'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">' +
            fallbackPaths + '</svg>'
        );
    }

    /* ── inject shared styles once ───────────────────────────────── */
    function _injectStyles() {
        if (document.getElementById('pf-color-picker-styles')) return;
        var s = document.createElement('style');
        s.id = 'pf-color-picker-styles';
        s.textContent =
            /* root */
            '.pfcp-wrap{display:flex;align-items:center;gap:6px;flex:1}' +

            /* native <input type=color> */
            '.pfcp-input{width:36px;height:28px;padding:1px 2px;cursor:pointer;' +
            'border:1px solid var(--color-border-medium,#ccc);border-radius:3px;' +
            'background:var(--color-form-input-bg,#fff);flex-shrink:0}' +
            '.pfcp-input::-webkit-color-swatch-wrapper{padding:0}' +
            '.pfcp-input::-webkit-color-swatch{border:none;border-radius:2px}' +
            '.pfcp-input::-moz-color-swatch{border:none;border-radius:2px}' +

            /* preview swatch */
            '.pfcp-swatch{display:inline-block;width:52px;height:22px;border-radius:3px;' +
            'border:1px solid var(--color-border-medium,#ccc);flex-shrink:0;background:transparent}' +

            /* hex label */
            '.pfcp-label{font-size:11px;min-width:60px;font-family:inherit;' +
            'color:var(--color-text-secondary,#666)}' +
            '.pfcp-label.pfcp-none{color:var(--color-text-tertiary,#aaa);font-style:italic}' +

            /* Remove button — icon-only, matches toolbar ghost style */
            '.pfcp-clear{display:inline-flex;align-items:center;justify-content:center;' +
            'width:28px;height:28px;padding:0;cursor:pointer;font-family:inherit;' +
            'border:1px solid var(--color-border-medium,#ccc);border-radius:3px;' +
            'background:var(--color-surface,#fff);color:var(--color-danger,#dc2626);' +
            'transition:background .12s,border-color .12s;flex-shrink:0}' +
            '.pfcp-clear svg{width:14px;height:14px;stroke:var(--color-danger,#dc2626);' +
            'stroke-width:2;fill:none;stroke-linecap:round;stroke-linejoin:round}' +
            '.pfcp-clear:hover{background:rgba(220,38,38,.08);' +
            'border-color:var(--color-danger,#dc2626)}' +

            '.rptf-hdr-field .dp-input-wrap{width:100%;box-sizing:border-box;display:flex;' +
            'align-items:center;justify-content:space-between;cursor:pointer;' +
            'padding:4px 8px;border:1px solid var(--color-border-medium,#ccc);border-radius:3px;' +
            'background:var(--color-form-input-bg,#fff);font-size:12px;' +
            'color:var(--color-form-input-text,#222);min-height:28px}' +
            '.rptf-hdr-field .dp-input-wrap:hover{border-color:var(--color-primary,#8b0000)}' +
            '.rptf-hdr-field{position:relative}' +
            '.rptf-hdr-field .dp-calendar{position:fixed!important;z-index:9999!important}';
            'align-items:center;justify-content:space-between;cursor:pointer;',
            'padding:4px 8px;border:1px solid var(--color-border-medium,#ccc);border-radius:3px;',
            'background:var(--color-form-input-bg,#fff);font-size:12px;',
            'color:var(--color-form-input-text,#222);min-height:28px}',
            '.rptf-hdr-field .dp-input-wrap:hover{border-color:var(--color-primary,#8b0000)}',
            '.rptf-hdr-field{position:relative}',
            /* calendar must escape modal overflow clipping */
            '.rptf-hdr-field .dp-calendar{position:fixed!important;z-index:9999!important}',

        document.head.appendChild(s);
    }

    /* ── build one widget instance ───────────────────────────────── */
    function create(opts) {
        opts = opts || {};
        var _hex    = _normalise(opts.value);
        var _active = !!_hex;
        var onChange = typeof opts.onChange === 'function' ? opts.onChange : null;

        /* root */
        var wrap = document.createElement('div');
        wrap.className = 'pfcp-wrap';

        /* native color input */
        var input = document.createElement('input');
        input.type      = 'color';
        input.className = 'pfcp-input';
        input.value     = _hex || '#ffffff';
        input.title     = 'Pick highlight color';

        /* preview swatch */
        var swatch = document.createElement('span');
        swatch.className = 'pfcp-swatch';

        /* hex label */
        var label = document.createElement('span');
        label.className = 'pfcp-label';

        /* Remove button — uses Remove icon from PF_ICONS */
        var clearBtn = document.createElement('button');
        clearBtn.type      = 'button';
        clearBtn.className = 'pfcp-clear';
        clearBtn.title     = 'Remove color';
        clearBtn.innerHTML = _icon(
            'Remove',
            /* fallback: simple × paths */
            '<line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>'
        );

        wrap.appendChild(input);
        wrap.appendChild(swatch);
        wrap.appendChild(label);
        wrap.appendChild(clearBtn);

        /* ── render state ── */
        function _render() {
            if (_active && _hex) {
                swatch.style.background = _hex;
                label.textContent       = _hex;
                label.classList.remove('pfcp-none');
            } else {
                swatch.style.background = 'transparent';
                label.textContent       = 'None';
                label.classList.add('pfcp-none');
            }
        }

        /* ── events ── */
        input.addEventListener('input', function () {
            _hex = input.value; _active = true;
            _render();
            if (onChange) onChange(_hex);
        });
        /* fallback for browsers that only fire 'change' on color inputs */
        input.addEventListener('change', function () {
            _hex = input.value; _active = true;
            _render();
            if (onChange) onChange(_hex);
        });
        clearBtn.addEventListener('click', function () {
            _active = false; _hex = '';
            _render();
            if (onChange) onChange('');
        });

        _render();

        /* ── public API ── */
        return {
            el: wrap,
            getValue: function ()    { return _active ? _hex : ''; },
            setValue: function (hex) {
                var h = _normalise(hex);
                _hex = h; _active = !!h;
                if (h) input.value = h;
                _render();
            },
            clear: function () {
                _active = false; _hex = '';
                _render();
            },
        };
    }

    /* ── helpers ── */
    function _normalise(hex) {
        if (!hex || typeof hex !== 'string') return '';
        var h = hex.trim();
        if (/^#[0-9a-fA-F]{3}$/.test(h)) {
            h = '#' + h[1] + h[1] + h[2] + h[2] + h[3] + h[3];
        }
        return /^#[0-9a-fA-F]{6}$/.test(h) ? h.toLowerCase() : '';
    }

    /* ── export ── */
    global.PfColorPicker = { create: create };

}(window));