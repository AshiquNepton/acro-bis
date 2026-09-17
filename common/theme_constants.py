# common/theme_constants.py
# ─────────────────────────────────────────────────────────────────
# Standalone constants — safe to import from both mixins.py and
# settings.py with zero circular-import risk.
# ─────────────────────────────────────────────────────────────────

VALID_THEMES = frozenset({
    'red-white',
    'blue-white',
    'purple-white',
    'green-white',
    'teal-white',
    'dark',
})

DEFAULT_THEME = 'red-white'


# ─────────────────────────────────────────────────────────────────
# TOOLBAR SVG ICONS
# All use stroke="currentColor" / fill="currentColor" so they
# automatically inherit the active theme color.
# ─────────────────────────────────────────────────────────────────

_I = {
    # ── Universal actions ────────────────────────────────────────
    'Close': (
        '<line x1="18" y1="6" x2="6" y2="18"/>'
        '<line x1="6" y1="6" x2="18" y2="18"/>'
    ),
    'Save': (
        '<path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/>'
        '<polyline points="17 21 17 13 7 13 7 21"/>'
        '<polyline points="7 3 7 8 15 8"/>'
    ),
    'New': (
        '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>'
        '<polyline points="14 2 14 8 20 8"/>'
        '<line x1="12" y1="18" x2="12" y2="12"/>'
        '<line x1="9" y1="15" x2="15" y2="15"/>'
    ),
    'Delete': (
        '<polyline points="3 6 5 6 21 6"/>'
        '<path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/>'
        '<path d="M10 11v6"/><path d="M14 11v6"/>'
        '<path d="M9 6V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2"/>'
    ),
    'Print': (
        '<polyline points="6 9 6 2 18 2 18 9"/>'
        '<path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"/>'
        '<rect x="6" y="14" width="12" height="8"/>'
    ),
    'Search': (
        '<circle cx="11" cy="11" r="8"/>'
        '<line x1="21" y1="21" x2="16.65" y2="16.65"/>'
    ),
    'Refresh': (
        '<polyline points="23 4 23 10 17 10"/>'
        '<polyline points="1 20 1 14 7 14"/>'
        '<path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/>'
    ),
    'Export': (
        '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>'
        '<polyline points="17 8 12 3 7 8"/>'
        '<line x1="12" y1="3" x2="12" y2="15"/>'
    ),
    'Import': (
        '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>'
        '<polyline points="7 10 12 15 17 10"/>'
        '<line x1="12" y1="15" x2="12" y2="3"/>'
    ),
    'Copy': (
        '<rect x="9" y="9" width="13" height="13" rx="2" ry="2"/>'
        '<path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>'
    ),
    # ── Record actions ───────────────────────────────────────────
    'Add': (
        '<circle cx="12" cy="12" r="10"/>'
        '<line x1="12" y1="8" x2="12" y2="16"/>'
        '<line x1="8" y1="12" x2="16" y2="12"/>'
    ),
    'Remove': (
        '<circle cx="12" cy="12" r="10"/>'
        '<line x1="8" y1="12" x2="16" y2="12"/>'
    ),
    'Change': (
        '<path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>'
        '<path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>'
    ),
    'Edit': (
        '<path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>'
        '<path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>'
    ),
    'View': (
        '<path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>'
        '<circle cx="12" cy="12" r="3"/>'
    ),
    'Approve': '<polyline points="20 6 9 17 4 12"/>',
    'Reject': (
        '<circle cx="12" cy="12" r="10"/>'
        '<line x1="15" y1="9" x2="9" y2="15"/>'
        '<line x1="9" y1="9" x2="15" y2="15"/>'
    ),
    'Cancel': (
        '<circle cx="12" cy="12" r="10"/>'
        '<line x1="4.93" y1="4.93" x2="19.07" y2="19.07"/>'
    ),
    'Submit': (
        '<line x1="22" y1="2" x2="11" y2="13"/>'
        '<polygon points="22 2 15 22 11 13 2 9 22 2"/>'
    ),
    'Confirm': (
        '<polyline points="9 11 12 14 22 4"/>'
        '<path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/>'
    ),
    # ── Navigation ───────────────────────────────────────────────
    'Back': (
        '<line x1="19" y1="12" x2="5" y2="12"/>'
        '<polyline points="12 19 5 12 12 5"/>'
    ),
    'Forward': (
        '<line x1="5" y1="12" x2="19" y2="12"/>'
        '<polyline points="12 5 19 12 12 19"/>'
    ),
    'First': (
        '<polyline points="11 17 6 12 11 7"/>'
        '<polyline points="18 17 13 12 18 7"/>'
    ),
    'Last': (
        '<polyline points="13 17 18 12 13 7"/>'
        '<polyline points="6 17 11 12 6 7"/>'
    ),
    'Previous': (
        '<line x1="19" y1="12" x2="5" y2="12"/>'
        '<polyline points="12 19 5 12 12 5"/>'
    ),
    'Next': (
        '<line x1="5" y1="12" x2="19" y2="12"/>'
        '<polyline points="12 5 19 12 12 19"/>'
    ),
    # ── Settings / config ────────────────────────────────────────
    'Settings': (
        '<circle cx="12" cy="12" r="3"/>'
        '<path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06'
        'a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09'
        'A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83'
        'l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09'
        'A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83'
        'l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09'
        'a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83'
        'l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09'
        'a1.65 1.65 0 0 0-1.51 1z"/>'
    ),
    'Default': (
        '<circle cx="12" cy="12" r="3"/>'
        '<path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06'
        'a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09'
        'A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83'
        'l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09'
        'A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83'
        'l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09'
        'a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83'
        'l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09'
        'a1.65 1.65 0 0 0-1.51 1z"/>'
    ),
    'Design': (
        '<circle cx="13.5" cy="6.5" r="0.5" fill="currentColor"/>'
        '<circle cx="17.5" cy="10.5" r="0.5" fill="currentColor"/>'
        '<circle cx="8.5" cy="7.5" r="0.5" fill="currentColor"/>'
        '<circle cx="6.5" cy="12.5" r="0.5" fill="currentColor"/>'
        '<path d="M12 2C6.5 2 2 6.5 2 12s4.5 10 10 10c.926 0 1.648-.746 1.648-1.688 '
        '0-.437-.18-.835-.437-1.125-.29-.289-.438-.652-.438-1.125a1.64 1.64 0 0 1 '
        '1.668-1.668h1.996c3.051 0 5.555-2.503 5.555-5.554C21.965 6.012 17.461 2 12 2z"/>'
    ),
    'Theme': (
        '<circle cx="13.5" cy="6.5" r="0.5" fill="currentColor"/>'
        '<circle cx="17.5" cy="10.5" r="0.5" fill="currentColor"/>'
        '<circle cx="8.5" cy="7.5" r="0.5" fill="currentColor"/>'
        '<circle cx="6.5" cy="12.5" r="0.5" fill="currentColor"/>'
        '<path d="M12 2C6.5 2 2 6.5 2 12s4.5 10 10 10c.926 0 1.648-.746 1.648-1.688 '
        '0-.437-.18-.835-.437-1.125-.29-.289-.438-.652-.438-1.125a1.64 1.64 0 0 1 '
        '1.668-1.668h1.996c3.051 0 5.555-2.503 5.555-5.554C21.965 6.012 17.461 2 12 2z"/>'
    ),
    'Utilities': (
        '<path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77'
        'a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91'
        'a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/>'
    ),
    'Tools': (
        '<path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77'
        'a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91'
        'a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/>'
    ),
    # ── Domain-specific ──────────────────────────────────────────
    'Visa': (
        '<rect x="2" y="5" width="20" height="14" rx="2"/>'
        '<line x1="2" y1="10" x2="22" y2="10"/>'
        '<line x1="6" y1="15" x2="6.01" y2="15"/>'
        '<line x1="10" y1="15" x2="14" y2="15"/>'
    ),
    'Passport': (
        '<path d="M4 4a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v16a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V4z"/>'
        '<circle cx="12" cy="10" r="3"/>'
        '<path d="M7 20s.5-3 5-3 5 3 5 3"/>'
    ),
    'Ticket': (
        '<path d="M15 5v2"/><path d="M15 11v2"/><path d="M15 17v2"/>'
        '<path d="M5 5h14a2 2 0 0 1 2 2v3a2 2 0 0 0 0 4v3a2 2 0 0 1-2 2H5'
        'a2 2 0 0 1-2-2v-3a2 2 0 0 0 0-4V7a2 2 0 0 1 2-2z"/>'
    ),
    'Payslip': (
        '<line x1="12" y1="1" x2="12" y2="23"/>'
        '<path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>'
    ),
    'Payroll': (
        '<line x1="12" y1="1" x2="12" y2="23"/>'
        '<path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>'
    ),
    'Documents': (
        '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>'
        '<polyline points="14 2 14 8 20 8"/>'
        '<line x1="16" y1="13" x2="8" y2="13"/>'
        '<line x1="16" y1="17" x2="8" y2="17"/>'
    ),

    'Attendance': (
        '<rect x="3" y="4" width="18" height="18" rx="2" ry="2"/>'
        '<line x1="16" y1="2" x2="16" y2="6"/>'
        '<line x1="8" y1="2" x2="8" y2="6"/>'
        '<line x1="3" y1="10" x2="21" y2="10"/>'
        '<polyline points="9 16 11 18 15 14"/>'
    ),
    'Leave': (
        '<path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>'
        '<polyline points="9 22 9 12 15 12 15 22"/>'
    ),
    'Report': (
        '<line x1="18" y1="20" x2="18" y2="10"/>'
        '<line x1="12" y1="20" x2="12" y2="4"/>'
        '<line x1="6" y1="20" x2="6" y2="14"/>'
    ),
    'Dashboard': (
        '<rect x="3" y="3" width="7" height="7"/>'
        '<rect x="14" y="3" width="7" height="7"/>'
        '<rect x="14" y="14" width="7" height="7"/>'
        '<rect x="3" y="14" width="7" height="7"/>'
    ),
    'Employee': (
        '<path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>'
        '<circle cx="12" cy="7" r="4"/>'
    ),
    'Employees': (
        '<path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>'
        '<circle cx="9" cy="7" r="4"/>'
        '<path d="M23 21v-2a4 4 0 0 0-3-3.87"/>'
        '<path d="M16 3.13a4 4 0 0 1 0 7.75"/>'
    ),
    'Customer': (
        '<path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>'
        '<circle cx="12" cy="7" r="4"/>'
        '<polyline points="16 11 18 13 22 9"/>'
    ),
    'Supplier': (
        '<rect x="1" y="3" width="15" height="13" rx="2"/>'
        '<path d="M16 8h4l3 3v5h-7V8z"/>'
        '<circle cx="5.5" cy="18.5" r="2.5"/>'
        '<circle cx="18.5" cy="18.5" r="2.5"/>'
    ),
    'Invoice': (
        '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>'
        '<polyline points="14 2 14 8 20 8"/>'
        '<line x1="16" y1="13" x2="8" y2="13"/>'
        '<line x1="16" y1="17" x2="8" y2="17"/>'
    ),
    'Payment': (
        '<rect x="1" y="4" width="22" height="16" rx="2" ry="2"/>'
        '<line x1="1" y1="10" x2="23" y2="10"/>'
    ),
    'Stock': (
        '<path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8'
        'a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/>'
        '<polyline points="3.27 6.96 12 12.01 20.73 6.96"/>'
        '<line x1="12" y1="22.08" x2="12" y2="12"/>'
    ),
    'Menu': (
        '<line x1="3" y1="12" x2="21" y2="12"/>'
        '<line x1="3" y1="6" x2="21" y2="6"/>'
        '<line x1="3" y1="18" x2="21" y2="18"/>'
    ),
    'Filter': '<polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"/>',
    'Upload': (
        '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>'
        '<polyline points="17 8 12 3 7 8"/>'
        '<line x1="12" y1="3" x2="12" y2="15"/>'
    ),
    'Download': (
        '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>'
        '<polyline points="7 10 12 15 17 10"/>'
        '<line x1="12" y1="15" x2="12" y2="3"/>'
    ),
    'Attach': (
        '<path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19'
        'a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48"/>'
    ),
    'Note': (
        '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>'
        '<polyline points="14 2 14 8 20 8"/>'
        '<line x1="16" y1="13" x2="8" y2="13"/>'
        '<line x1="16" y1="17" x2="8" y2="17"/>'
    ),
    'History': (
        '<polyline points="12 8 12 12 14 14"/>'
        '<path d="M3.05 11a9 9 0 1 1 .5 4"/>'
        '<polyline points="3 16 3 11 8 11"/>'
    ),
    'Lock': (
        '<rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>'
        '<path d="M7 11V7a5 5 0 0 1 10 0v4"/>'
    ),
    'Unlock': (
        '<rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>'
        '<path d="M7 11V7a5 5 0 0 1 9.9-1"/>'
    ),
    'Email': (
        '<path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/>'
        '<polyline points="22,6 12,13 2,6"/>'
    ),
    'SMS': '<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>',
    'Logout': (
        '<path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>'
        '<polyline points="16 17 21 12 16 7"/>'
        '<line x1="21" y1="12" x2="9" y2="12"/>'
    ),


    # ── Separator marker (not an icon, used as menu divider) ─────
    'sep': '',
}

# Wrap each inner path string into a full ready-to-render SVG tag
TOOLBAR_ICONS = {
    label: (
        f'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" '
        f'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
        f'{paths}</svg>'
    )
    for label, paths in _I.items()
}


# ─────────────────────────────────────────────────────────────────
# tb() — build a toolbar button dict
#
# Parameters:
#   label      : str   — display text AND icon key in TOOLBAR_ICONS
#   onclick    : str   — JS expression e.g. 'erSave()'
#   danger     : bool  — red danger styling
#   sep_before : bool  — vertical separator before this button
#   sep_after  : bool  — vertical separator after this button
#   menu       : bool  — if True, button goes into Menu dropdown,
#                        NOT rendered in the main toolbar row
#   icon       : str   — override SVG (full <svg>…</svg> string)
#
# Usage:
#   from common.theme_constants import tb
#
#   'toolbar': [
#       tb('Close',     'erClose()',   danger=True),
#       tb('Save',      'erSave()'),
#       tb('New',       'erNew()'),
#       tb('Delete',    'erDelete()',  danger=True),
#       tb('Print',     'erPrint()',   menu=True),          # → Menu dropdown
#       tb('Change',    'erChange()',  menu=True),
#       tb('Default',   'erDefault()', menu=True),
#       tb('Visa',      'erVisa()',    menu=True),
#       tb('Utilities', 'erUtilities()', menu=True),
#       tb('sep',       '',            menu=True),           # divider in menu
#       tb('Design',    "openFormDesign('f','F')", menu=True),
#   ]
#
# The template renders only non-menu buttons in the toolbar strip.
# The Menu button is auto-injected and its onclick is built from
# all menu=True items — no manual erMenu() needed in the view.
# ─────────────────────────────────────────────────────────────────

def tb(label, onclick='', danger=False, sep_before=False, sep_after=False,
       menu=False, icon=None, extra_attrs=''):
    return {
        'label':       label,
        'icon':        icon if icon is not None else TOOLBAR_ICONS.get(label, TOOLBAR_ICONS['Menu']),
        'onclick':     onclick,
        'danger':      danger,
        'sep_before':  sep_before,
        'sep_after':   sep_after,
        'menu':        menu,            # True → goes into Menu dropdown, not toolbar
        'sep':         label == 'sep',  # True → render as divider in dropdown
        'extra_attrs': extra_attrs,     # raw HTML attribute string e.g. 'data-foo="bar"'
    }

