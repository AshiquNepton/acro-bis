import json
from django.shortcuts import redirect, render
from django.urls import reverse

from common.views.import_excel import (
    build_import_form_config,
    get_import_types,
    import_template_download,
    import_excel_process
)
from inventory.views.import_config import register_inventory_imports

def import_excel_page(request):
    if not request.session.get('is_authenticated'):
        return redirect('common:login')

    # Register all types (idempotent)
    register_inventory_imports()

    types = get_import_types()
    import_types = [{'key': k, 'label': v['label']} for k, v in types.items()]

    ctx = {
        'module_name': 'Inventory',
        'page_title': 'Import from Excel',
        'form_config': build_import_form_config(import_types),
        'import_types': import_types,
        'columns_config': json.dumps({k: v['columns'] for k, v in types.items()}),

        # Absolute URLs — avoids broken relative paths when JS fetch() is called
        'process_url': reverse('inventory:import_process'),
        'template_url': reverse('inventory:import_template'),

        # Extends inventory chrome
        'base_template': 'inventory/base.html',
    }
    return render(request, 'common/masters/import_excel.html', ctx)
