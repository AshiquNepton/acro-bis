"""
common/views/profile_form_helpers.py   v3.0
──────────────────────────────────────────────────────────────────────
Helpers for building form_config — the single dict that controls
the entire profile-form engine (profile_form.html + profile_form.js).

Quick usage
───────────
    from common.views.profile_form_helpers import build_form_config, pf_employee

    def employee_form(request, employee_id=None):
        dd = _load_employee(employee_id) if employee_id else {}
        return render(request, 'hrms/employee/employee_form.html', {
            'form_config': _build_form_config(dd),  # your existing fn
        })

    # Or use a preset that wraps build_form_config():
        'form_config': pf_employee(dd)['base_config'],   # just the hero/bar parts
                                                         # then merge with your tabs


form_config schema
──────────────────
{
  'form_id'        : str,
  'title'          : str,

  # Sticky top bar buttons (order matters)
  'action_bar': [
    {'action': 'close',  'label': 'Close',  'onclick': 'myClose()'},
    {'action': 'new',    'label': 'New',    'onclick': 'pfActNew("my-form")'},
    {'action': 'save',   'label': 'Save',   'onclick': 'pfActSave("my-form")'},
    {'action': 'delete', 'label': 'Delete', 'onclick': 'pfActDelete("my-form")'},
    # Custom:
    {'action': 'custom', 'label': 'Print', 'icon': '🖨️', 'onclick': 'window.print()',
     'danger': False, 'primary': False, 'sep_before': False, 'sep_after': False},
  ],

  # Optional hero card — omit key entirely to hide
  'hero': {
    'show_avatar'    : True,
    'avatar_field'   : 'photo',       # name of <input type=file>; '' = no upload
    'avatar_url'     : '',            # pre-load in edit mode
    'hero_icon'      : '🗂',         # shown when show_avatar=False or no avatar_field
    'name_field'     : 'emp_name',
    'default_name'   : 'New Employee',
    'show_meta_rows' : True,
    'row1_field'     : 'designation',
    'row1_icon'      : '',            # SVG <path> etc.; '' = default briefcase
    'row2_field'     : 'email',
    'row2_icon'      : '',            # SVG <path> etc.; '' = default envelope
    'badge1_label'   : 'Active',      # '' / None = hide badge1
    'badge1_class'   : 'pf-badge-active',
    'badge2_field'   : 'department',  # '' / None = hide badge2
  },

  # Optional toolbar row — omit key to hide
  'toolbar': [
    {'label': 'Visa',  'icon': '🪪', 'onclick': 'erVisa()'},
    {'label': 'Print', 'icon': '🖨️', 'onclick': 'window.print()', 'sep_before': True},
    {'label': 'Menu',  'icon': '☰',  'onclick': 'erMenu(this)'},
  ],

  # Optional header fields strip — omit key to hide
  'header_fields': [ field_dict, ... ],

  # Sidenav
  'show_sidenav': True,   # default False

  # Tabs
  'tabs': [
    {
      'id'      : str,
      'label'   : str,
      'nav_icon': '<path .../>', # SVG for sidenav; '' = auto by position
      'tab_icon': '<path .../>', # SVG for tab strip; '' = no icon
      'columns' : [ [field_dict, ...], ... ],
    },
    ...
  ],
}
──────────────────────────────────────────────────────────────────────
"""

# ── Default action bar ──────────────────────────────────────────────

from common.theme_constants import tb

def default_action_bar(form_id, close_fn=None, new_fn=None, save_fn=None, delete_fn=None):
    """
    Returns the standard 4-button action bar config.
    Pass custom onclick strings to override per-form.
    """
    fid = form_id
    return [
        tb('Close',  close_fn or f"pfActClose('{fid}')",  danger=True),
        tb('Save',   save_fn or f"pfActSave('{fid}')"),
        tb('New',    new_fn or f"pfActNew('{fid}')"),
        tb('Delete', delete_fn or f"pfActDelete('{fid}')"),
    ]


# ── Hero config builder ─────────────────────────────────────────────

def build_hero_config(
    # Avatar
    show_avatar     = True,
    avatar_field    = '',       # '' = no upload (static icon)
    avatar_url      = '',       # pre-load image in edit mode
    hero_icon       = '🗂',    # shown when not show_avatar or no avatar_field

    # Name
    name_field      = '',
    default_name    = '',

    # Meta rows
    show_meta_rows  = True,
    row1_field      = '',
    row1_icon       = '',       # SVG inner HTML; '' = default briefcase icon
    row2_field      = '',
    row2_icon       = '',       # SVG inner HTML; '' = default envelope icon

    # Badges
    badge1_label    = 'Active',       # '' or None → hide
    badge1_class    = 'pf-badge-active',
    badge2_field    = '',             # '' or None → hide
):
    """
    Returns a hero config dict for use inside form_config['hero'].
    Pass None or omit 'hero' from form_config to hide the hero card entirely.
    """
    return {
        'show_avatar'   : show_avatar,
        'avatar_field'  : avatar_field,
        'avatar_url'    : avatar_url,
        'hero_icon'     : hero_icon,
        'name_field'    : name_field,
        'default_name'  : default_name,
        'show_meta_rows': show_meta_rows,
        'row1_field'    : row1_field,
        'row1_icon'     : row1_icon,
        'row2_field'    : row2_field,
        'row2_icon'     : row2_icon,
        'badge1_label'  : badge1_label,
        'badge1_class'  : badge1_class,
        'badge2_field'  : badge2_field,
    }


# ── Main form_config builder ────────────────────────────────────────

def build_form_config(
    form_id,
    title,
    tabs,
    action_bar       = None,   # list of btn dicts; None = auto default 4 buttons
    hero             = None,   # hero_config dict; None = no hero card
    toolbar          = None,   # list of btn dicts; None = no toolbar row
    header_fields    = None,   # list of field dicts; None = no header strip
    show_sidenav     = False,
    close_fn         = None,   # override onclick for Close
    new_fn           = None,   # override onclick for New
    save_fn          = None,   # override onclick for Save
    delete_fn        = None,   # override onclick for Delete
):
    """
    Build the complete form_config dict for the template engine.

    Parameters
    ----------
    form_id       : HTML id of the <form> element (must be unique per page)
    title         : Shown in the sticky action bar
    tabs          : List of tab dicts
    action_bar    : None → use default_action_bar(); [] → no bar buttons
    hero          : build_hero_config() dict or None
    toolbar       : List of toolbar button dicts or None
    header_fields : List of field dicts or None
    show_sidenav  : Show left sidenav (True/False)
    close_fn      : Custom onclick str for Close button
    new_fn        : Custom onclick str for New button
    save_fn       : Custom onclick str for Save button
    delete_fn     : Custom onclick str for Delete button
    """
    if action_bar is None:
        action_bar = default_action_bar(form_id, close_fn, new_fn, save_fn, delete_fn)

    final_toolbar = action_bar
    if toolbar:
        final_toolbar = final_toolbar + toolbar

    return {
        'form_id'       : form_id,
        'title'         : title,
        'hero'          : hero,            # None → template hides hero section
        'toolbar'       : final_toolbar,   # Merged default buttons + extra toolbar items
        'header_fields' : header_fields,   # None → template hides header strip
        'show_sidenav'  : show_sidenav,
        'tabs'          : tabs or [],
    }


# ═══════════════════════════════════════════════════════════════════
#  READY-MADE PRESETS
#  Each preset returns a complete form_config dict.
#  Merge with your tabs in the view:
#
#      cfg = pf_employee_config(dd)
#      cfg['tabs'] = _build_tabs(dd)
#      return render(request, template, {'form_config': cfg})
#
# ═══════════════════════════════════════════════════════════════════

def pf_employee_config(dd=None, form_id='emp-reg-form'):
    """
    Employee Registration
    - Clickable avatar upload
    - Shows designation (row1) + email (row2)
    - Active/Inactive badge
    - Dynamic department badge
    - Sidenav shown
    - Full action bar
    """
    dd        = dd or {}
    is_active = dd.get('active', True)

    hero = build_hero_config(
        show_avatar   = True,
        avatar_field  = 'photo',
        avatar_url    = dd.get('photo_url', ''),
        name_field    = 'emp_name',
        default_name  = dd.get('emp_name') or 'New Employee',
        show_meta_rows= True,
        row1_field    = 'designation',
        row2_field    = 'email',
        badge1_label  = 'Active' if is_active else 'Inactive',
        badge1_class  = 'pf-badge-active' if is_active else 'pf-badge-sub',
        badge2_field  = 'department',
    )

    return build_form_config(
        form_id      = form_id,
        title        = 'Employee Registration',
        tabs         = [],          # caller must fill tabs
        hero         = hero,
        show_sidenav = True,
    )


def pf_company_config(dd=None, form_id='company-form'):
    """
    Company Registration
    - No hero card
    - No sidenav
    - Minimal toolbar
    """
    dd = dd or {}
    return build_form_config(
        form_id      = form_id,
        title        = 'Company Registration',
        tabs         = [],
        hero         = None,        # no hero card
        show_sidenav = False,
    )


def pf_customer_config(dd=None, form_id='customer-form'):
    """
    Customer Registration
    - Static icon (no avatar upload)
    - Shows contact person + email
    - Sub-badge = customer type
    """
    dd = dd or {}
    hero = build_hero_config(
        show_avatar   = True,
        avatar_field  = '',         # no upload — static icon
        hero_icon     = '👥',
        name_field    = 'customer_name',
        default_name  = dd.get('customer_name') or 'New Customer',
        show_meta_rows= True,
        row1_field    = 'cont_person',
        row2_field    = 'email',
        badge1_label  = 'Customer',
        badge1_class  = 'pf-badge-sub',
        badge2_field  = 'customer_type',
    )
    return build_form_config(
        form_id      = form_id,
        title        = 'Customer Registration',
        tabs         = [],
        hero         = hero,
        show_sidenav = True,
    )


def pf_vendor_config(dd=None, form_id='vendor-form'):
    """
    Vendor Registration
    - Static icon (no upload)
    - Shows contact + email
    - Sub-badge = vendor category
    """
    dd = dd or {}
    hero = build_hero_config(
        show_avatar   = True,
        avatar_field  = '',
        hero_icon     = '🏭',
        name_field    = 'vendor_name',
        default_name  = dd.get('vendor_name') or 'New Vendor',
        show_meta_rows= True,
        row1_field    = 'cont_person',
        row2_field    = 'email',
        badge1_label  = 'Vendor',
        badge1_class  = 'pf-badge-sub',
        badge2_field  = 'vendor_category',
    )
    return build_form_config(
        form_id      = form_id,
        title        = 'Vendor Registration',
        tabs         = [],
        hero         = hero,
        show_sidenav = True,
    )


def pf_leave_config(dd=None, form_id='leave-form'):
    """
    Leave Application
    - No avatar
    - Row1 = leave type, Row2 = from date
    - Badge = status (Pending/Approved/Rejected)
    - Sub-badge = department
    """
    dd       = dd or {}
    status   = dd.get('status', 'Pending')
    badge_map = {
        'Approved': 'pf-badge-active',
        'Rejected': 'pf-badge-danger',
    }

    hero = build_hero_config(
        show_avatar   = False,
        hero_icon     = '📋',
        name_field    = 'emp_name',
        default_name  = dd.get('emp_name') or 'New Leave Application',
        show_meta_rows= True,
        row1_field    = 'leave_type',
        row1_icon     = (
            '<rect x="3" y="4" width="18" height="18" rx="2"/>'
            '<line x1="16" y1="2" x2="16" y2="6"/>'
            '<line x1="8" y1="2" x2="8" y2="6"/>'
            '<line x1="3" y1="10" x2="21" y2="10"/>'
        ),
        row2_field    = 'date_from',
        badge1_label  = status,
        badge1_class  = badge_map.get(status, 'pf-badge-warning'),
        badge2_field  = 'department',
    )
    return build_form_config(
        form_id      = form_id,
        title        = 'Leave Application',
        tabs         = [],
        hero         = hero,
        show_sidenav = False,
    )


# ── Convenience: build a toolbar button dict ────────────────────────

def tb_btn(label, icon, onclick, danger=False, sep_before=False, sep_after=False):
    """Shorthand for a toolbar button dict."""
    return {
        'label'     : label,
        'icon'      : icon,
        'onclick'   : onclick,
        'danger'    : danger,
        'sep_before': sep_before,
        'sep_after' : sep_after,
    }


# ── Convenience: build a field dict ────────────────────────────────

def field(name, label, ftype='1', **kwargs):
    """
    Shorthand for a field dict.

    field('emp_name', 'Employee Name')
    field('dept', 'Department', '3', options=dept_options, required=True)
    field('photo', 'Photo', 'photo')
    field('hdr', 'Personal Info', 'section_hdr')
    """
    d = {'name': name, 'label': label, 'type': ftype}
    d.update(kwargs)
    return d
