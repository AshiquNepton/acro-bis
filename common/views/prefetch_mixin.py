# common/views/prefetch_mixin.py
"""
PrefetchMixin — builds window.PAGE_PREFETCH for any Django view.

Usage in a view:
    from common.views.prefetch_mixin import build_prefetch_urls
    ctx['prefetch_urls'] = build_prefetch_urls(request, 'laundry:order_form', order_id='123')

Or use the per-app helpers at the bottom of this file which know which
URLs each page needs.

The template renders it as:
    <script>window.PAGE_PREFETCH = {{ prefetch_urls_json }};</script>

in common/base.html inside {% block extra_head %}.
"""

import json
from django.urls import reverse


# ── Generic builder ───────────────────────────────────────────────────────────

def _safe_reverse(viewname, kwargs=None, args=None):
    """Reverse a URL silently — returns None on NoReverseMatch."""
    try:
        return reverse(viewname, kwargs=kwargs, args=args)
    except Exception:
        return None


def build_prefetch_json(urls):
    """
    Given a list of URL strings (some may be None — filtered out),
    return a JSON-safe string for injection into the template.
    """
    clean = [u for u in (urls or []) if u]
    return json.dumps(clean)


# ── Per-page prefetch builders ────────────────────────────────────────────────

def prefetch_employee_form(employee_id=None, next_reg_no=None):
    """Stub — HRMS is standalone; no prefetch URLs available here."""
    return []


def prefetch_employee_list():
    """Employee list / report page — no dynamic prefetch needed."""
    return []


def prefetch_attendance_form():
    """Attendance entry — no prefetch."""
    return []


def prefetch_leave_application(app_id=None):
    """Stub — HRMS is standalone."""
    return []


def prefetch_request_application(app_id=None):
    """Stub — HRMS is standalone."""
    return []


def prefetch_todo(task_id=None):
    """Stub — HRMS is standalone."""
    return []


def prefetch_shift_form(shift_id=None):
    """Stub — HRMS is standalone."""
    return []


def prefetch_payroll_form():
    return []


def prefetch_attendance_location_form(loc_id=None):
    """Stub — HRMS is standalone."""
    return []


# ── Master dispatcher ─────────────────────────────────────────────────────────

def get_prefetch_urls(page_name, **kwargs):
    """
    Central dispatcher.  Call this from any view's context builder:

        ctx['prefetch_urls_json'] = get_prefetch_json(
            'employee_form', employee_id=employee_id
        )

    Supported page_name values:
        employee_form, employee_list,
        attendance_form, attendance_location_form,
        leave_application, request_application,
        todo, shift_form, payroll_form
    """
    dispatch = {
        'employee_form'            : lambda: prefetch_employee_form(
                                         kwargs.get('employee_id'),
                                         kwargs.get('next_reg_no'),
                                     ),
        'employee_list'            : prefetch_employee_list,
        'attendance_form'          : prefetch_attendance_form,
        'attendance_location_form' : lambda: prefetch_attendance_location_form(
                                         kwargs.get('loc_id')
                                     ),
        'leave_application'        : lambda: prefetch_leave_application(
                                         kwargs.get('app_id')
                                     ),
        'request_application'      : lambda: prefetch_request_application(
                                         kwargs.get('app_id')
                                     ),
        'todo'                     : lambda: prefetch_todo(kwargs.get('task_id')),
        'shift_form'               : lambda: prefetch_shift_form(kwargs.get('shift_id')),
        'payroll_form'             : prefetch_payroll_form,
    }

    builder = dispatch.get(page_name)
    if not builder:
        return []
    return builder()


def get_prefetch_json(page_name, **kwargs):
    """Convenience wrapper — returns a JSON string ready for template injection."""
    return build_prefetch_json(get_prefetch_urls(page_name, **kwargs))