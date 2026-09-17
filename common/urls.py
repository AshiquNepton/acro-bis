# common/urls.py
from django.urls import path
from common.views import auth, dashboard, customers, masters, settings, company_info
from common.views import filter_views
from common.views.form_design import form_design_delete, load_form_design, reset_form_design, save_form_design
from common.views.ftp_browse import ftp_browse
from common.views.group_setup import group_setup, group_setup_load, group_setup_save, group_setup_delete
from common.views.department import (
    check_duplicate_department, department_form, get_next_dept_id, lookup_department, search_department,
    save_department, get_department, delete_department, list_departments,
)
from common.views.import_excel import import_excel_process, import_excel_view, import_template_download
from common.views.settings import theme_settings, save_theme
from common.views.documents import load_docs, save_doc, delete_doc, serve_doc
from common.views.filter_views import (
    filter_dept_options, filter_load, filter_log, filter_period_dates,
    filter_report_styles, filter_save, filter_delete, filter_reset,
    filter_reports, filter_rename, filter_foreign_options,
)
from common.views.report_style_views import (
    report_save_style, report_load_style, report_delete_style,
)
from common.views.global_settings import (
    gs_config,
    gs_load_settings,
    gs_save_settings,
    gs_load_images,
    gs_upload_image,
    gs_delete_image,
    gs_serve_image,
)

app_name = 'common'

urlpatterns = [
    # ── Authentication ────────────────────────────────────────────────────────
    path('',        auth.login_view,  name='login'),
    path('logout/', auth.logout_view, name='logout'),

    # ── Dashboard ─────────────────────────────────────────────────────────────
    path('dashboard/', dashboard.dashboard_view, name='dashboard'),
    path('home/',      settings.home,            name='home'),

    # ── Customer ──────────────────────────────────────────────────────────────
    path('customer/',               customers.customer_form,   name='customer'),
    path('customer/lookup/',        customers.lookup_customer, name='lookup_customer'),
    path('customer/save_customer/', customers.save_customer,   name='save_customer'),

    # ── Company ───────────────────────────────────────────────────────────────
    path('company/',                         company_info.company_form,           name='company_form'),
    path('company/lookup/',                  company_info.lookup_company,         name='lookup_company'),
    path('company/search/name/',             company_info.search_company_by_name, name='search_company_name'),
    path('company/save/',                    company_info.save_company,           name='save_company'),
    path('company/get/<int:company_id>/',    company_info.get_company,            name='get_company'),
    path('company/delete/<int:company_id>/', company_info.delete_company,         name='delete_company'),

    # ── Department / Job ──────────────────────────────────────────────────────
    path('department/',                      department_form,             name='department_form'),
    path('department/lookup/',               lookup_department,           name='lookup_department'),
    path('department/search/',               search_department,           name='search_department'),
    path('department/save/',                 save_department,             name='save_department'),
    path('department/get/<int:firm_id>/',    get_department,              name='get_department'),
    path('department/delete/<int:firm_id>/', delete_department,           name='delete_department'),
    path('department/list/',                 list_departments,            name='list_departments'),
    path('department/next-id/',              get_next_dept_id,            name='get_next_dept_id'),
    path('department/check-duplicate/',      check_duplicate_department,  name='check_duplicate_department'),

    # ── Settings ──────────────────────────────────────────────────────────────
    path('settings/database/', settings.database_config, name='database_config'),
    path('settings/theme/',    theme_settings,            name='theme_settings'),
    path('save-theme/',        save_theme,                name='save_theme'),

    # ── Form Design ───────────────────────────────────────────────────────────
    path('form-design/load/',   load_form_design,   name='form_design_load'),
    path('form-design/save/',   save_form_design,   name='form_design_save'),
    path('form-design/reset/',  reset_form_design,  name='form_design_reset'),
    path('form-design/delete/', form_design_delete, name='form_design_delete'),

    # ── Group Setup ───────────────────────────────────────────────────────────
    path('group-setup/',        group_setup,        name='group_setup'),
    path('group-setup/load/',   group_setup_load,   name='group_setup_load'),
    path('group-setup/save/',   group_setup_save,   name='group_setup_save'),
    path('group-setup/delete/', group_setup_delete, name='group_setup_delete'),

    # ── Documents ─────────────────────────────────────────────────────────────
    path('docs/load/',   load_docs,  name='load_docs'),
    path('docs/save/',   save_doc,   name='save_doc'),
    path('docs/delete/', delete_doc, name='delete_doc'),
    path('docs/serve/',  serve_doc,  name='serve_doc'),

    # ── Filter (shared across all modules) ────────────────────────────────────
    path('filter/load/',            filter_load,            name='filter_load'),
    path('filter/save/',            filter_save,            name='filter_save'),
    path('filter/delete/',          filter_delete,          name='filter_delete'),
    path('filter/reset/',           filter_reset,           name='filter_reset'),
    path('filter/reports/',         filter_reports,         name='filter_reports'),
    path('filter/rename/',          filter_rename,          name='filter_rename'),
    path('filter/report-styles/',   filter_report_styles,   name='filter_report_styles'),
    path('filter/dept-options/',    filter_dept_options,    name='filter_dept_options'),
    path('filter/period-dates/',    filter_period_dates,    name='filter_period_dates'),
    path('filter/log/',             filter_log,             name='filter_log'),
    path('filter/foreign-options/', filter_foreign_options, name='filter_foreign_options'),

    # ── Report Styles ─────────────────────────────────────────────────────────
    path('report/save-style/',   report_save_style,   name='report_save_style'),
    path('report/load-style/',   report_load_style,   name='report_load_style'),
    path('report/delete-style/', report_delete_style, name='report_delete_style'),

    # ── FTP Browse ────────────────────────────────────────────────────────────
    path('ftp/browse/', ftp_browse, name='ftp_browse'),

    # ── Import ────────────────────────────────────────────────────────────────
    path('import/',           import_excel_view,       name='import_excel_view'),
    path('import/process/',   import_excel_process,    name='import_excel_process'),
    path('import/template/',  import_template_download, name='import_template_download'),

    # ── Global Settings ───────────────────────────────────────────────────────
    path('gs/config/',          gs_config,          name='gs_config'),
    path('gs/settings/load/',   gs_load_settings,   name='gs_load_settings'),
    path('gs/settings/save/',   gs_save_settings,   name='gs_save_settings'),
    path('gs/images/load/',     gs_load_images,     name='gs_load_images'),
    path('gs/images/upload/',   gs_upload_image,    name='gs_upload_image'),
    path('gs/images/delete/',   gs_delete_image,    name='gs_delete_image'),
    path('gs/images/serve/',    gs_serve_image,     name='gs_serve_image'),
]